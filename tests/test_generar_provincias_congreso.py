"""Versión 1.0.0; 2026-10-31; candidato. Coherencia del alta de las provincias del Congreso.
Origen: nuevo, sin predecesor. Cada provincia dada de alta por generar_provincias_congreso.py debe estar
declarada igual en catálogo, política, matriz, registro, contrato Infoelectoral y contrato M01–M06.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from herramientas.catalogo_territorios import load_pilot_territories, selector_labels  # noqa: E402
from herramientas.generar_provincias_congreso import INSULAR, PROVINCES, provinces  # noqa: E402


def _load(rel: str) -> dict:
    return yaml.safe_load((ROOT / rel).read_text(encoding="utf-8")) or {}


class CongressProvincesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reparto = {p["territory_id"]: p for p in provinces(ROOT)}
        cls.pilots = {p["territory_id"]: p for p in load_pilot_territories()}

    def test_reparto_is_n06_and_every_peninsular_province_is_declared(self):
        self.assertEqual(52, len(self.reparto))
        self.assertEqual(407, sum(p["k"] for p in self.reparto.values()))
        expected = {tid for tid, p in self.reparto.items() if p["code"] not in INSULAR}
        self.assertEqual(expected, set(self.pilots))

    def test_number_and_plate_identify_each_province_once(self):
        plates = [plate for _, plate in PROVINCES.values()]
        self.assertEqual(len(plates), len(set(plates)))
        for tid, pilot in self.pilots.items():
            province = self.reparto[tid]
            self.assertEqual(f"C{province['code']}", pilot["pilot_code"])
            self.assertEqual([province["code"]], pilot["province_codes"])
            if tid != "congreso_huesca":
                self.assertEqual(province["plate"], pilot["plate_code"])

    def test_every_declaration_agrees_with_the_approved_k(self):
        policy = _load("configuracion/politica_generacion_territorial_2025.yaml")["territories"]
        matrix = {row["territory_id"]: row for row in _load("configuracion/preparacion_legislatura_vigente.yaml")["territories"]}
        registry = _load("configuracion/registro_electoral.yaml")["territories"]
        contracts = _load("configuracion/contratos_infoelectoral.yaml")["contracts"]
        labels = set(selector_labels())
        for tid, pilot in self.pilots.items():
            with self.subTest(territory=tid):
                k = self.reparto[tid]["k"]
                election_id = f"{tid}_2023-07-23"
                self.assertEqual(k, pilot["k_districts"])
                self.assertEqual(k, policy[tid]["k"])
                self.assertEqual(election_id, matrix[tid]["election_id"])
                self.assertEqual(election_id, registry[tid]["election_id"])
                self.assertEqual(self.reparto[tid]["code"], contracts[election_id]["province"])
                self.assertIn(pilot["name"], labels)
                contract = _load(f"territorios/{tid}/config/{tid}_2025.yaml")
                self.assertEqual(k, contract["validation"]["expected_districts"])
                self.assertEqual({self.reparto[tid]["code"]: k}, contract["validation"]["province_districts"])

    def test_spanish_toponyms_only(self):
        names = {name for name, _ in PROVINCES.values()}
        for foreign in ("Girona", "Lleida", "Ourense", "Gipuzkoa", "Bizkaia", "Araba", "A Coruña", "Illes Balears"):
            self.assertNotIn(foreign, names)


if __name__ == "__main__":
    unittest.main()
