"""DDD regression 1.0.0, 2026-10-29: exención de suelo por municipio (Beniel, Murcia).

Solo el distrito que contiene un municipio declarado queda sin suelo; el resto conserva el suelo común.
"""
import unittest
from pathlib import Path

import yaml

from ddd_core.population_floor_exemptions import (
    exempt_municipalities, municipalities_touch_exempt, unit_municipality, units_touch_exempt,
)

ROOT = Path(__file__).resolve().parents[1]


class MunicipalFloorExemptionTests(unittest.TestCase):
    def test_unit_ids_carry_their_municipality(self):
        self.assertEqual("30010", unit_municipality("30:30010:M"))
        self.assertEqual("30030", unit_municipality("30:30030:U4"))
        self.assertIsNone(unit_municipality("suelto"))

    def test_only_districts_with_a_declared_municipality_are_exempt(self):
        exempt = {"30010"}
        self.assertTrue(units_touch_exempt(["30:30010:M", "30:30030:R"], exempt))
        self.assertFalse(units_touch_exempt(["30:30030:U1"], exempt))
        self.assertFalse(units_touch_exempt(["30:30010:M"], set()))
        self.assertTrue(municipalities_touch_exempt(["30030", "30010"], exempt))
        self.assertFalse(municipalities_touch_exempt(["30030"], exempt))

    def test_murcia_contract_declares_only_beniel(self):
        cfg = yaml.safe_load((ROOT / "territorios/region_de_murcia/config/region_de_murcia_2025.yaml").read_text(encoding="utf-8"))
        self.assertEqual({"30010"}, exempt_municipalities(cfg))
        self.assertEqual([], cfg["validation"]["population_floor_exempt_partitions"])

    def test_absent_key_means_no_exemption(self):
        self.assertEqual(set(), exempt_municipalities({"validation": {}}))
        self.assertEqual(set(), exempt_municipalities(None))


if __name__ == "__main__":
    unittest.main()
