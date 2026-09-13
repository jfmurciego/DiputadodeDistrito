import json
import tempfile
import unittest
from pathlib import Path

from herramientas.auditar_sesgo_reparto_k import audit_territory, build_report


ROOT = Path(__file__).resolve().parents[1]


class RepartoKTest(unittest.TestCase):
    def test_known_adversarial_allocation(self):
        result = audit_territory(
            {
                "territory_id": "synthetic",
                "status": "test",
                "source": "fixture",
                "k_districts": 4,
                "provinces": {
                    "01": {"population": 300, "districts": 2},
                    "02": {"population": 100, "districts": 2},
                },
            }
        )
        by_code = {row["province_code"]: row for row in result["provinces"]}
        self.assertEqual(by_code["01"]["population_load_bias"], 0.5)
        self.assertEqual(by_code["02"]["population_load_bias"], -0.5)

    def test_governed_evidence_closes_c04(self):
        payload = json.loads(
            (ROOT / "configuracion/auditoria_reparto_k.json").read_text(encoding="utf-8")
        )
        report = build_report(payload)
        self.assertEqual(report["decision"], "CLOSED_MEASURED_AND_PUBLISHED")
        by_territory = {row["territory_id"]: row for row in report["territories"]}
        aragon = by_territory["aragon"]
        self.assertEqual(aragon["total_population"], 1364621)
        self.assertEqual(aragon["k_districts"], 67)
        teruel = next(row for row in aragon["provinces"] if row["province_code"] == "44")
        self.assertAlmostEqual(teruel["population_load_bias"], -0.045460032, places=9)

    def test_rejects_allocation_that_does_not_sum_to_k(self):
        with self.assertRaisesRegex(ValueError, "reparto suma"):
            audit_territory(
                {
                    "territory_id": "bad",
                    "status": "test",
                    "source": "fixture",
                    "k_districts": 3,
                    "provinces": {"01": {"population": 100, "districts": 2}},
                }
            )


if __name__ == "__main__":
    unittest.main()
