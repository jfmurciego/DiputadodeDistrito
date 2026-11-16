"""T-333: datos de ensayo por mesa con claves de sección 2026 (reparto desde 2023): marcados ENSAYO, con sha256, no confundibles con oficiales."""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import adaptador_minsait_csv as adaptador
from herramientas import generar_datos_ensayo_congreso as gen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / gen.MANIFEST
ZIP_OFICIAL_SHA = "e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8"
TABLA_SHA = "d57d5fcfd80372b4842edc914bd43f89a655c91f996d4bd8bbceb5fd6fbfb35e"
# Literales independientes: votos a candidaturas del ZIP oficial Infoelectoral 2023 por provincia (contratos_infoelectoral.yaml,
# verificados el 30-10-2026): el reparto a claves 2026 los conserva. Secciones 2026 «partida» de la tabla por provincia.
VOTOS = {"nac22": 117735, "nac42": 49823, "nac52": 26925}
PARTIDAS = {"nac22": ["2221301002"], "nac42": [], "nac52": ["5200108002"]}  # Soria no tiene ninguna partida en la tabla


def _m07():
    spec = importlib.util.spec_from_file_location("ddd_m07_t333", ROOT / "modulos/07_agregar_resultados_electorales.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _escribir(path: Path, filas: list[dict], campos=gen.fim.OUTPUT_FIELDS) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def _fila(prov, muni, dist, sec, mesa, partido, votos, ccaa="02"):
    return {"codigo_ccaa": ccaa, "codigo_provincia": prov, "codigo_municipio": muni, "codigo_distrito": dist,
            "codigo_seccion": sec, "codigo_mesa": mesa, "partido": partido, "votos": str(votos)}


class Manifest(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_marcado_como_ensayo_no_oficial(self):
        m = self.m
        self.assertIs(m["rehearsal"], True)
        self.assertIs(m["official"], False)
        self.assertEqual(m["status"], "PROVISIONAL")
        self.assertEqual(m["mark"], gen.MARCA)
        self.assertIn("ENSAYO", m["warning"])
        self.assertEqual(m["derived_from"]["sha256"], ZIP_OFICIAL_SHA)
        self.assertEqual(m["equivalence_table"]["sha256"], TABLA_SHA)
        self.assertIn("sin documento", m["feed_format"])
        self.assertIn("Operador", m["operator_check"])

    def test_ficheros_con_nombre_ensayo_sha256_y_totales(self):
        self.assertEqual(set(self.m["files"]), set(VOTOS))
        for tid, f in self.m["files"].items():
            self.assertRegex(f["file"], r"^ensayo_congreso_[a-z]+_2026-11-29\.csv$")
            self.assertRegex(f["sha256"], r"^[0-9a-f]{64}$")
            self.assertNotEqual(f["sha256"], ZIP_OFICIAL_SHA)
            self.assertEqual(f["candidate_votes"], VOTOS[tid])
            self.assertEqual(f["partida_sections"], PARTIDAS[tid])
            self.assertEqual(f["sections_by_type"]["partida"], len(PARTIDAS[tid]))

    def test_cada_provincia_tiene_partida_o_lo_declara(self):
        con = [t for t, f in self.m["files"].items() if f["partida_sections"]]
        sin = [t for t, f in self.m["files"].items() if not f["partida_sections"]]
        self.assertEqual(sorted(con), ["nac22", "nac52"])
        self.assertEqual(sin, ["nac42"])  # declarado: la tabla no trae secciones partidas en Soria

    def test_cuadra_con_los_contratos_de_ensayo_si_estan(self):
        # Con #800 (T-332) fusionada, expected del contrato = totales del MANIFEST y la huella es la del MANIFEST (T-391: sin pendientes).
        contratos = (yaml.safe_load((ROOT / "configuracion/contratos_minsait_provisionales.yaml").read_text(encoding="utf-8")) or {})["contracts"]
        for tid, f in self.m["files"].items():
            c = contratos.get(f["election_id_ensayo"])
            if c is None:
                continue
            self.assertEqual(c["source_sha256"], f["sha256"])
            self.assertEqual(c["source_url"].rsplit("/", 1)[1], f["file"])
            self.assertEqual((c["expected"]["sections"], c["expected"]["polling_stations"], c["expected"]["candidate_votes"]),
                             (f["sections"], f["polling_stations"], f["candidate_votes"]))


class Reparto(unittest.TestCase):
    def test_reparto_entero_resto_al_mayor_peso(self):
        r = gen._repartir
        self.assertEqual(r(10, [("a", 600000, "x"), ("b", 400000, "x")]), [("a", 6), ("b", 4)])
        self.assertEqual(r(7, [("a", 500000, "x"), ("b", 500000, "x")]), [("a", 4), ("b", 3)])  # resto al primero (mayor peso/clave menor)
        self.assertEqual(r(5, [("a", 1, "x")]), [("a", 5)])
        self.assertEqual(r(0, [("a", 3, "x"), ("b", 1, "x")]), [("a", 0), ("b", 0)])

    def test_tabla_con_sha_distinto_se_rechaza(self):
        with tempfile.TemporaryDirectory() as tmp:
            falsa = Path(tmp) / "t.csv"
            falsa.write_text("seccion_2026,seccion_2023,tipo,peso_area,peso_poblacion\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                gen.cargar_tabla(falsa)

    def _tabla(self):
        return gen.cargar_tabla(ROOT / gen.EQUIVALENCIA)

    def test_huesca_la_partida_recibe_los_votos_de_sus_dos_secciones_2023(self):
        # 2221301002 (2026, «partida») = partes de 2221301002 y 2221301003 (2023): en el fixture lleva los votos de ambas.
        with tempfile.TemporaryDirectory() as tmp:
            entrada, salida = Path(tmp) / "in.csv", Path(tmp) / "out.csv"
            _escribir(entrada, [_fila("22", "213", "01", "002", "A", "PP", 100), _fila("22", "213", "01", "003", "A", "PP", 40),
                                _fila("22", "001", "01", "001", "U", "PP", 7)])
            res = gen.repartir_claves_2026(entrada, salida, self._tabla())
            with salida.open(encoding="utf-8", newline="") as fh:
                filas = list(csv.DictReader(fh))
            texto = salida.read_text(encoding="utf-8")
        self.assertEqual(res["partida_sections"], ["2221301002"])
        self.assertEqual(res["candidate_votes"], 147)
        por_seccion = {f["codigo_provincia"] + f["codigo_municipio"] + f["codigo_distrito"] + f["codigo_seccion"]: int(f["votos"]) for f in filas}
        self.assertEqual(por_seccion, {"2221301002": 140, "2200101001": 7})
        self.assertEqual({f["ensayo"] for f in filas}, {gen.MARCA})
        self.assertNotIn("\r", texto)

    def test_cabecera_inesperada_falla(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada = Path(tmp) / "in.csv"
            _escribir(entrada, [{"a": "1"}], campos=("a",))
            with self.assertRaises(ValueError):
                gen.repartir_claves_2026(entrada, Path(tmp) / "out.csv", self._tabla())


class SalidaM07(unittest.TestCase):
    """La sección partida del fixture llega ENTERA al distrito de más población con el tipo correcto (M07 7.4.0, apply_section_equivalence)."""

    def setUp(self):
        import pandas as pd
        self.pd = pd
        self.m07 = _m07()
        record = {"path": gen.EQUIVALENCIA.as_posix(), "sha256": TABLA_SHA, "source_column": "seccion_2026",
                  "target_column": "seccion_2023", "decision": "D-65"}
        self.tabla, _ = self.m07.load_section_equivalence(record, project_root=ROOT)

    def _aplicar(self, votos: dict[str, int], distritos: dict[str, str]):
        pd = self.pd
        sp = pd.DataFrame([{"cusec": s, "party": "PP", "votes": v} for s, v in votos.items()])
        gdf = pd.DataFrame({"cusec": list(distritos), "distrito": list(distritos.values())})
        return self.m07.apply_section_equivalence(sp, gdf, section_field="cusec", district_field="distrito", table=self.tabla)

    def test_huesca_partida_entera_al_distrito_de_mas_poblacion(self):
        # 2221301002: 72,6115 % de la población en 2221301002 y 27,3885 % en 2221301003 (tabla). Cada una en un distrito.
        out, ev = self._aplicar({"2221301002": 140, "2200101001": 7}, {"2221301002": "D1", "2221301003": "D2", "2200101001": "D1"})
        self.assertEqual(ev["by_class"]["partida"], {"sections": 1, "votes": 140})
        self.assertEqual(ev["votes_assigned_by_majority_across_districts"], 140)
        a = ev["majority_assignments"][0]
        self.assertEqual((a["source"], a["target"], a["district"], a["votes"]), ("2221301002", "2221301002", "D1", 140))
        self.assertEqual(dict(zip(out["cusec"], out["votes"])), {"2221301002": 140, "2200101001": 7})

    def test_melilla_el_destino_es_el_de_mayor_poblacion(self):
        # 5200108002: 45,9709 % en 5200108001 y 54,0291 % en 5200108002; con cada una en su distrito gana la 002.
        out, ev = self._aplicar({"5200108002": 90}, {"5200108001": "D1", "5200108002": "D2"})
        a = ev["majority_assignments"][0]
        self.assertEqual((a["target"], a["district"], a["votes"]), ("5200108002", "D2", 90))
        self.assertEqual(ev["by_class"]["partida"]["sections"], 1)
        self.assertEqual(int(out["votes"].sum()), 90)

    def test_clases_1a1_y_contenida_del_fixture_de_soria(self):
        out, ev = self._aplicar({"4209501002": 10, "4217302015": 5, "4209501001": 3},
                                {"4209501001": "D1", "4217302007": "D1"})
        self.assertEqual(ev["by_class"]["1:1"]["sections"], 1)
        self.assertEqual(ev["by_class"]["contenida"]["sections"], 2)  # 4217302015 y 4209501001 (tabla)
        self.assertEqual(ev["by_class"]["partida"]["sections"], 0)
        self.assertEqual(dict(zip(out["cusec"], out["votes"])), {"4209501001": 13, "4217302007": 5})


class PaqueteDelAdaptador(unittest.TestCase):
    def test_el_adaptador_lo_acepta_y_el_paquete_lleva_marcas_de_ensayo_y_no_es_elegible(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada, salida, paquete = Path(tmp) / "in.csv", Path(tmp) / "ensayo_x.csv", Path(tmp) / "pkg"
            _escribir(entrada, [_fila("42", "095", "01", "001", "U", "PSOE", 57, "08"), _fila("42", "095", "01", "001", "U", "PP", 43, "08")])
            res = gen.repartir_claves_2026(entrada, salida, gen.cargar_tabla(ROOT / gen.EQUIVALENCIA))
            self.assertEqual(res["candidate_votes"], 100)
            adaptador.build(
                salida, paquete, territory_id="nac42", election_id="congreso_soria_2026-11-29", election_date="2026-11-29",
                edition="2025", expected_sha256=gen.sha256(salida), expected_ccaa="08", expected_provinces=1,
                expected_sections=res["sections"], expected_polling_stations=res["polling_stations"], expected_candidate_votes=100,
                source_url="x", publisher="ENSAYO", source_status="PROVISIONAL", definitive_reference_publisher="r",
                definitive_reference_url="u", definitive_candidate_votes=100, expected_delta_definitive_minus_provisional=0,
                source_class="rehearsal", adapter_label="minsait_provisional/ensayo/1.0",
                section_equivalence=ROOT / gen.EQUIVALENCIA,
            )
            manifest = json.loads((paquete / "manifest.json").read_text(encoding="utf-8"))
        self.assertIs(manifest["production_eligible"], False)
        self.assertEqual(manifest["source_status"], "PROVISIONAL")
        self.assertEqual(manifest["selected_source"]["source_class"], "rehearsal")
        self.assertIn("ensayo", manifest["adapter"])
        self.assertTrue(manifest["election_id"].endswith("_2026-11-29"))


@unittest.skipUnless(os.environ.get("DDD_ZIP_INFOELECTORAL_2023"), "ZIP oficial no disponible (DDD_ZIP_INFOELECTORAL_2023)")
class RegeneracionDesdeElZipOficial(unittest.TestCase):
    """Lo ejecuta el Operador antes de subir: los sha256 del MANIFEST solo se confrontan aquí."""

    def test_regenerar_da_el_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            nuevo = gen.generar(Path(os.environ["DDD_ZIP_INFOELECTORAL_2023"]), Path(tmp), ROOT)
        self.assertEqual(nuevo, json.loads(MANIFEST.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
