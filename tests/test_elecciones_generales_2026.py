"""Universo electoral de las generales 2026: coherencia con el RD 806/2026 (valores literales del BOE)."""
import csv, hashlib, unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
YAML = ROOT / "configuracion/elecciones_generales_2026.yaml"
CSV = ROOT / "configuracion/escanos_oficiales_congreso_2026.csv"


class UniversoGenerales2026(unittest.TestCase):
    def setUp(self):
        self.u = yaml.safe_load(YAML.read_text(encoding="utf-8"))
        lineas = [l for l in CSV.read_text(encoding="utf-8").splitlines() if not l.startswith("#")]
        self.csv = list(csv.DictReader(lineas))

    def test_total_y_circunscripciones(self):
        self.assertEqual(len(self.u["circunscripciones"]), 52)
        self.assertEqual(sum(c["escanos_2026"] for c in self.u["circunscripciones"]), 350)
        self.assertEqual(self.u["total_escanos"], 350)

    def test_cambios_respecto_a_2023(self):
        cambios = {c["territory_id"]: (c["escanos_2023"], c["escanos_2026"])
                   for c in self.u["circunscripciones"] if c["escanos_2023"] != c["escanos_2026"]}
        self.assertEqual(cambios, {"congreso_madrid": (37, 38), "congreso_cadiz": (9, 8)})

    def test_yaml_coincide_con_csv(self):
        por_cod = {r["codigo"]: int(r["escanos_2026"]) for r in self.csv}
        for c in self.u["circunscripciones"]:
            self.assertEqual(c["escanos_2026"], por_cod[c["codigo"]])

    def test_no_toca_k_de_ddd(self):
        for tid, k in (("congreso_madrid", 59), ("congreso_cadiz", 11)):
            txt = (ROOT / f"territorios/{tid}/config/{tid}_2025.yaml").read_text(encoding="utf-8")
            self.assertIn(f"k_districts: {k}", txt)


if __name__ == "__main__":
    unittest.main()
