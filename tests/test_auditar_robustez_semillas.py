"""Pruebas ligeras de la evidencia C-01; no ejecutan el motor territorial."""
import unittest

from herramientas.auditar_robustez_semillas import decide, percentile, seed_list


class SeedRobustnessAudit(unittest.TestCase):
    def test_seed_list_includes_canonical_and_has_required_size(self):
        seeds = seed_list(50, 12345)
        self.assertEqual(len(seeds), 50)
        self.assertEqual(len(set(seeds)), 50)
        self.assertEqual(seeds[0], 12345)

    def test_percentile_uses_midrank_for_ties(self):
        self.assertEqual(percentile([1.0, 2.0, 2.0, 4.0], 2.0), 50.0)

    def test_decision_accepts_central_published_map(self):
        rows = [
            {
                "max_rel_dev": 0.08 + i / 10000,
                "pp_mean": 0.20 + i / 1000,
                "pp_min": 0.06 + i / 10000,
                "districts_outside_tolerance": 0,
            }
            for i in range(50)
        ]
        canonical = {
            **rows[24],
            "pp_below_015_ratio": 0.25,
        }
        self.assertEqual(decide(rows, canonical), ("PASS", []))

    def test_process_success_does_not_mean_technical_solution(self):
        rows = [
            {
                "max_rel_dev": 0.10 if i < 15 else 0.18,
                "districts_outside_tolerance": 0 if i < 15 else 1,
                "pp_mean": 0.23,
                "pp_min": 0.052,
            }
            for i in range(50)
        ]
        canonical = {**rows[0], "pp_below_015_ratio": 0.25}
        decision, reasons = decide(rows, canonical)
        self.assertEqual(decision, "FAIL")
        self.assertIn("menos del 95 %", reasons[0])


if __name__ == "__main__":
    unittest.main()
