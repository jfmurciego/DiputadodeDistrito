"""Read-only comprehensive audit of 52 national origin units."""
import unittest
from herramientas.auditar_52_entradas_congreso_n08 import collect

class TestNational52InputCoverage(unittest.TestCase):
    def test_hash_pinned_provinces_are_all_readable_but_no_districts_certified(self):
        result = collect()
        c = result["checks"]
        self.assertEqual(c["origin_units_checked"], 52)
        self.assertEqual(c["sections_2025"], 36554)
        self.assertEqual(c["population_2025"], 49128297)
        self.assertEqual(c["approved_k_total"], 407)
        self.assertEqual(c["input_checks_passed"], 52)
        self.assertFalse(c["administrative_boundaries_2025_crossvalidated"])
        self.assertFalse(c["individual_exceptions_approved"])
        self.assertFalse(c["full_national_feasibility_proven"])
        self.assertEqual(c["district_partitions_generated"], 0)
        self.assertTrue(c["all_production_execution_denied"])
        self.assertFalse(result["generation_authorized"])
        rows = result["provinces"]
        self.assertEqual([r["CPRO"] for r in rows], [f"{n:02d}" for n in range(1, 53)])
        self.assertTrue(all(r["input_status"] == "PASS_INPUTS_ONLY" for r in rows))

if __name__ == "__main__":
    unittest.main()
