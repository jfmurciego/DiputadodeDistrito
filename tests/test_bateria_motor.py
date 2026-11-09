"""T-132: batería del motor (herramientas/bateria_motor.py)."""
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import bateria_motor as b

ROOT = Path(__file__).resolve().parents[1]


class BateriaMotor(unittest.TestCase):
    def test_territorios_son_52_congreso_y_19_comunidades(self):
        ts = b.territorios()
        self.assertEqual(len([t for t in ts if t.startswith("congreso_")]), 52)
        self.assertEqual(len([t for t in ts if not t.startswith("congreso_")]), 19)

    def test_reglas_salen_del_informe_de_validar_ejecucion(self):
        ok = {"estado": "PASS", "districts_found": 2, "failures": []}
        self.assertTrue(all(b._reglas(ok).values()))
        mal = {"estado": "FAIL", "districts_found": 3, "below_floor": [{"district_id": 1}],
               "graph_disconnected": [{"district_id": 2, "components": 2}],
               "municipality_violations": [{"municipality_id": "22125"}],
               "failures": ["distritos=3, esperados=2", "distritos bajo límite poblacional=1",
                            "distritos desconectados en grafo=1", "municipios con fragmentación inválida=1",
                            "algo nuevo"]}
        r = b._reglas(mal)
        self.assertEqual({k for k, v in r.items() if not v}, {"K", "poblacion", "contiguidad", "municipal", "otras"})
        self.assertTrue(r["provincia"] and r["atomicidad"])

    def test_versiones_del_motor_m05_existen(self):
        for v, p in b.M05_BASE.items():
            self.assertTrue(p.is_file(), v)

    def test_comparacion_con_publicado_ignora_etiquetas(self):
        with tempfile.TemporaryDirectory() as td:
            comp = Path(td) / "c.csv"
            pub = Path(ROOT / "datos" / "composicion" / "congreso_huesca.csv")
            filas = pub.read_text(encoding="utf-8").splitlines()[1:]
            # mismas particiones con etiquetas intercambiadas
            comp.write_text("CUSEC_KEY,district_id\n" + "\n".join(
                f"{s},{1 - int(d)}" for s, d, _ in (x.split(",") for x in filas)) + "\n", encoding="utf-8")
            r = b._comparar_publicado("congreso_huesca", comp)
            self.assertTrue(r["igual"])

    def test_declaracion_temporal_completa_anos_desde_contrato(self):
        nac = {n: {"sha256": "0" * 64} for n in ("65034_totales.csv.zip", "seccionado_2023.zip",
                                                  "seccionado_2024.zip", "seccionado_2025.zip")}
        for modo in ("ogc", "shapefile"):
            p = b._declaracion_temporal("comunidad_valenciana", nac, modo)
            try:
                d = yaml.safe_load(p.read_text(encoding="utf-8"))
            finally:
                p.unlink()
            self.assertEqual((d["territory"]["population_year"], d["territory"]["section_year"]), (2023, 2023))
            self.assertEqual(d["source_bindings"]["secciones_censales"]["materialized_path"], "inputs/seccionado_2023.zip")
            self.assertEqual("snapshot" in d["source_bindings"]["secciones_censales"], modo == "shapefile")


if __name__ == "__main__":
    unittest.main()
