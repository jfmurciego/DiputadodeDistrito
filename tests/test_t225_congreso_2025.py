# -*- coding: utf-8 -*-
"""PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.1 · FECHA: 2026-11-12 · ANTERIOR: legacy/tests/test_t225_congreso_2025_v1.0.0_20261112.py
CAMBIOS 1.0.1 (T-220): ids de territorio nuevos de la tabla maestra (aut01…nac52, D-61); el id viejo se lee vía ddd_core.territorio_ids.
Tests de T-225 (D-65, D-80): contratos de la edición 2026 de las 52 circunscripciones del Congreso con el par INE
2025/2025, su decisión, los inventarios insulares 2025 y la equivalencia seccionado INE 2026 → 2025."""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ddd_core.territorio_ids import es_nacional, ids_nuevos, id_legacy  # noqa: E402  (T-220)
IDS = sorted(p.name for p in (ROOT / "territorios").iterdir() if es_nacional(p.name))
DECISION = ROOT / "configuracion/decisiones/congreso_referencia_territorial_2025_2026.json"
TABLA = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2025.csv"


def _c(t: str, edicion: str) -> dict:
    return yaml.safe_load((ROOT / f"territorios/{t}/config/{t}_{edicion}.yaml").read_text(encoding="utf-8"))


class Contratos2026(unittest.TestCase):
    def test_52_contratos_2026_con_par_2025(self):
        self.assertEqual(len(IDS), 52)
        for t in IDS:
            with self.subTest(territorio=t):
                c = _c(t, "2026")
                self.assertEqual((c["meta"]["year"], c["meta"]["run_name"]), (2026, f"{t}_2026"))
                self.assertEqual((c["meta"]["source_population_year"], c["meta"]["source_section_year"]), (2025, 2025))
                self.assertEqual(c["io"]["input"]["seccionado"]["path"], "inputs/seccionado_2025.zip")
                self.assertEqual(c["io"]["input"]["population_cip"]["filters"]["year_value"], 2025)
                self.assertEqual(c["validation"]["source_baseline"]["edition"], "2026")
                self.assertIs(c["generation_state"]["generation_enabled"], False)
                self.assertNotIn("POP_2023", json.dumps(c))
                self.assertNotIn(f"{t}_2025", json.dumps(c))

    def test_contratos_admitidos_por_la_puerta_estructural(self):
        from ddd_core.territory_contract import validate_production_contract
        for t in IDS:
            with self.subTest(territorio=t):
                r = validate_production_contract(ROOT / f"territorios/{t}/config/{t}_2026.yaml", expected_territory=t)
                self.assertEqual(r.get("status"), "ADMITTED", r.get("errors"))

    def test_legislatura_vigente_sigue_en_2023(self):
        # D-80: los mapas van por legislatura; la vigente (elección de 2023) conserva sus contratos 2025 en 2023.
        for t in IDS:
            with self.subTest(territorio=t):
                self.assertEqual(_c(t, "2025")["meta"]["source_population_year"], 2023)

    def test_puentes_del_seccionado_2025(self):
        # Tremp: la sección 2523403001 no existe en el seccionado INE 2025; Herrera de Duero (Tudela, 47175) sí.
        def puentes(t):
            m02 = _c(t, "2026")["modulos"]["modulo_02_construir_adyacencias"]
            return {(str(b["u"]), str(b["v"])) for b in m02["topology_bridges"]}
        self.assertNotIn(("2523401002", "2523403001"), puentes("nac25"))
        self.assertIn(("4717501004", "4717501003"), puentes("nac47"))

    def test_decision(self):
        d = json.loads(DECISION.read_text(encoding="utf-8"))
        self.assertEqual(sorted(d["territory_ids"]), IDS)  # T-220: la decisión conserva su orden (por id viejo)
        self.assertEqual((d["selected_population_year"], d["selected_section_year"], d["election_year"]), (2025, 2025, 2026))
        self.assertIs(d["generation_authorized_by_this_decision"], False)
        self.assertIn("D-65", d["approval_basis"])
        self.assertIn("D-80", d["approval_basis"])
        self.assertEqual(d["status"], "OWNER_DECISION_RELAYED_PENDING_PLAN_RECORD")  # D-80 aún no está en el plan

    def test_inventario_insular_2025(self):
        p = json.loads((ROOT / "configuracion/particiones_insulares_2025.json").read_text(encoding="utf-8"))["territories"]
        inv = {t: [i for i in p[t]["inventories"] if i["section_year"] == 2025] for t in
               ("nac07", "nac35", "nac38", "aut04")}
        self.assertTrue(all(len(v) == 1 for v in inv.values()))
        # cruce con los inventarios 2025 acreditados antes por las autonómicas (fuente independiente: run 36529385760 y
        # 36529404391): mismo universo en Baleares y, en Las Palmas, mismas islas sueltas y grupo = suma de sus islas
        aut, can = inv["aut04"][0], [i for i in p["aut05"]["inventories"] if i["section_year"] == 2025][0]
        self.assertEqual(inv["nac07"][0]["universe_cusec_set_sha256"], aut["universe_cusec_set_sha256"])
        lp = inv["nac35"][0]
        for c in ("35-C01", "35-C02"):
            self.assertEqual(lp["component_cusec_set_sha256"][c], can["component_cusec_set_sha256"][c])
        self.assertEqual(lp["component_sections"]["35-G01"],
                         can["component_sections"]["35-C03"] + can["component_sections"]["35-C04"])


class Equivalencia2026(unittest.TestCase):
    def test_tabla_con_sha256_y_fuentes(self):
        meta = json.loads(TABLA.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(TABLA.read_bytes()).hexdigest(), meta["csv"]["sha256"])
        # el seccionado 2025 es el del par nacional versionado (inputs/MANIFEST.sha256), no uno cualquiera
        manifiesto = (ROOT / "inputs/MANIFEST.sha256").read_text(encoding="utf-8")
        self.assertIn(f'{meta["fuentes"]["seccionado_2025"]["sha256"]}  inputs/seccionado_2025.zip', manifiesto)
        self.assertEqual(meta["fuentes"]["seccionado_2026"]["sha256"],
                         "3132a7ea07eaf6183b59f66bfbbf7d379662e9cf2759284358e88cedcc035ed2")
        self.assertEqual(len(meta["provincias"]), 52)
        # literal: la única sección nueva de Soria cae entera en una sección 2025
        self.assertIn("4217302016,4217302014,contenida,1.000000,1.000000", TABLA.read_text(encoding="utf-8").splitlines())

    def test_medir_contenida_y_partida(self):
        from shapely.geometry import box
        sys.path.insert(0, str(ROOT / "herramientas"))
        import equivalencia_seccionado_2026_2025 as eq
        s2025 = {"A": box(0, 0, 2, 1), "B": box(2, 0, 4, 1)}
        nuevas = {"N1": box(0, 0, 1, 1), "N2": box(1, 0, 3, 1)}  # N1 dentro de A; N2 mitad en A, mitad en B
        _, r = eq.medir(nuevas, s2025, {"A": 100, "B": 50})
        self.assertEqual((r["tipo_contenida"], r["tipo_partida"]), (1, 1))
        self.assertEqual(r["poblacion_afectada_partidas"], 75)  # 0,5 × 100 + 0,5 × 50

    def test_mismo_cusec_con_limite_cambiado_se_mide(self):
        import tempfile
        import geopandas as gpd
        from shapely.geometry import box
        sys.path.insert(0, str(ROOT / "herramientas"))
        import equivalencia_seccionado_2026_2025 as eq
        import equivalencia_seccionados as es
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for nombre, geoms in (("s25", {"4200101001": box(0, 0, 2, 1), "4200101002": box(2, 0, 4, 1)}),
                                  ("s26", {"4200101001": box(0, 0, 3, 1), "4200101002": box(3, 0, 4, 1)})):
                gpd.GeoDataFrame({"CUSEC": list(geoms)}, geometry=list(geoms.values()), crs=25830).to_file(d / f"{nombre}.shp")
                import zipfile
                with zipfile.ZipFile(d / f"{nombre}.zip", "w") as z:
                    for f in d.glob(f"{nombre}.*"):
                        if f.suffix != ".zip":
                            z.write(f, f.name)
            (d / "x").write_bytes(b"")
            orig = es.leer_padron
            es.leer_padron = lambda *_: {"4200101001": 100, "4200101002": 100}
            try:
                eq.main(["--s2026", str(d / "s26.zip"), "--s2025", str(d / "s25.zip"), "--padron", str(d / "x"),
                         "--salida", str(ROOT / "configuracion" / f"_t225_prueba_{os.getpid()}.csv")])
            finally:
                es.leer_padron = orig
            salida = ROOT / "configuracion" / f"_t225_prueba_{os.getpid()}.csv"
            meta = json.loads(salida.with_suffix(".json").read_text(encoding="utf-8"))
            salida.unlink(); salida.with_suffix(".json").unlink()
        r = meta["provincias"]["42"]
        # 4200101001 crece medio cuadro hacia la 002: mismo CUSEC, límite cambiado, partida entre las dos de 2025
        self.assertEqual(r["secciones_mismo_cusec_limite_cambiado"], 2)
        self.assertEqual(r["tipo_partida"], 1)
        self.assertEqual(r["poblacion_afectada_partidas"], 150)  # 1 × 100 + 0,5 × 100


if __name__ == "__main__":
    unittest.main()
