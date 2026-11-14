"""T-333: datos de ensayo por mesa (2023 reetiquetado): marcados como ENSAYO, con sha256 y nunca confundibles con oficiales."""
from __future__ import annotations

import csv
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from herramientas import adaptador_minsait_csv as adaptador
from herramientas import generar_datos_ensayo_congreso as gen

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / gen.MANIFEST
ZIP_OFICIAL_SHA = "e78fc231326a03cf67bbec87b7100ea0c8c46859daa1b2a631c06daaaf1717f8"
# Literales independientes: totales del ZIP oficial Infoelectoral 2023 por provincia (contratos_infoelectoral.yaml, 30-10-2026).
ESPERADO = {"nac22": (286, 403, 117735), "nac42": (216, 256, 49823), "nac52": (44, 87, 26925)}


def _escribir(path: Path, filas: list[dict], campos=gen.fim.OUTPUT_FIELDS) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


FILAS = [
    {"codigo_ccaa": "08", "codigo_provincia": "42", "codigo_municipio": "001", "codigo_distrito": "01", "codigo_seccion": "001",
     "codigo_mesa": "U", "partido": "PSOE", "votos": "57"},
    {"codigo_ccaa": "08", "codigo_provincia": "42", "codigo_municipio": "001", "codigo_distrito": "01", "codigo_seccion": "001",
     "codigo_mesa": "U", "partido": "PP", "votos": "43"},
]


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

    def test_ficheros_con_nombre_ensayo_y_sha256(self):
        self.assertEqual(set(self.m["files"]), set(ESPERADO))
        for tid, f in self.m["files"].items():
            self.assertRegex(f["file"], r"^ensayo_congreso_[a-z]+_2026-11-29\.csv$")
            self.assertRegex(f["sha256"], r"^[0-9a-f]{64}$")
            self.assertNotEqual(f["sha256"], ZIP_OFICIAL_SHA)
            self.assertTrue(f["election_id_ensayo"].endswith("_2026-11-29"))
            self.assertEqual((f["sections"], f["polling_stations"], f["candidate_votes"]), ESPERADO[tid])

    def test_cuadra_con_los_contratos_de_ensayo_si_estan(self):
        # Con #800 (T-332) fusionada, la huella del contrato es la del manifest (o PENDIENTE_T333 hasta que se rellene).
        import yaml
        contratos = (yaml.safe_load((ROOT / "configuracion/contratos_minsait_provisionales.yaml").read_text(encoding="utf-8")) or {})["contracts"]
        for tid, f in self.m["files"].items():
            c = contratos.get(f["election_id_ensayo"])
            if c is None:
                continue
            self.assertIn(c["source_sha256"], ("PENDIENTE_T333", f["sha256"]))
            self.assertEqual(c["source_url"].rsplit("/", 1)[1], f["file"])
            self.assertEqual((c["expected"]["sections"], c["expected"]["polling_stations"], c["expected"]["candidate_votes"]), ESPERADO[tid])


class Reetiquetado(unittest.TestCase):
    def test_cada_fila_lleva_la_marca_y_los_votos_no_cambian(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada, salida = Path(tmp) / "in.csv", Path(tmp) / "ensayo_x.csv"
            _escribir(entrada, FILAS)
            self.assertEqual(gen.reetiquetar(entrada, salida)["rows"], 2)
            filas = list(csv.DictReader(salida.open(encoding="utf-8", newline="")))
            self.assertEqual([f["ensayo"] for f in filas], [gen.MARCA] * 2)
            self.assertEqual([int(f["votos"]) for f in filas], [57, 43])
            self.assertNotIn("\r", salida.read_text(encoding="utf-8"))

    def test_cabecera_inesperada_falla(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada = Path(tmp) / "in.csv"
            _escribir(entrada, [{"a": "1"}], campos=("a",))
            with self.assertRaises(ValueError):
                gen.reetiquetar(entrada, Path(tmp) / "out.csv")

    def test_el_adaptador_lo_acepta_y_el_paquete_no_es_elegible(self):
        with tempfile.TemporaryDirectory() as tmp:
            entrada, salida, paquete = Path(tmp) / "in.csv", Path(tmp) / "ensayo_x.csv", Path(tmp) / "pkg"
            _escribir(entrada, FILAS)
            gen.reetiquetar(entrada, salida)
            adaptador.build(
                salida, paquete, territory_id="nac42", election_id="congreso_soria_2026-11-29", election_date="2026-11-29",
                edition="2025", expected_sha256=gen.sha256(salida), expected_ccaa="08", expected_provinces=1,
                expected_sections=1, expected_polling_stations=1, expected_candidate_votes=100,
                source_url="x", publisher="ENSAYO", source_status="PROVISIONAL", definitive_reference_publisher="r",
                definitive_reference_url="u", definitive_candidate_votes=100, expected_delta_definitive_minus_provisional=0,
                source_class="rehearsal", adapter_label="minsait_provisional/ensayo/1.0",
            )
            manifest = json.loads((paquete / "manifest.json").read_text(encoding="utf-8"))
            self.assertIs(manifest["production_eligible"], False)
            self.assertEqual(manifest["source_status"], "PROVISIONAL")


@unittest.skipUnless(os.environ.get("DDD_ZIP_INFOELECTORAL_2023"), "ZIP oficial no disponible (DDD_ZIP_INFOELECTORAL_2023)")
class RegeneracionDesdeElZipOficial(unittest.TestCase):
    def test_regenerar_da_los_sha256_del_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            nuevo = gen.generar(Path(os.environ["DDD_ZIP_INFOELECTORAL_2023"]), Path(tmp), ROOT)
        self.assertEqual(nuevo, json.loads(MANIFEST.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
