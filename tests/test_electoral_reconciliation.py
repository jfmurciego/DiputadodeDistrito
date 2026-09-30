#!/usr/bin/env python3
import unittest

import pandas as pd

from ddd_core.electoral_reconciliation import reconcile_sections


class ElectoralReconciliation(unittest.TestCase):
    def mapping(self):
        return pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3900201001"],
                "district": [1, 1, 2],
                "population": [1000, 1200, 800],
            }
        )

    def test_incomplete_accepted_source_with_ddd_loss_within_1_5_percent_passes(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3999901001"],
                "party": ["P", "P", "P"],
                "votes": [600, 390, 10],
            }
        )
        assigned, report = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            definitive_candidate_votes=1100,
            policy={},
        )

        self.assertEqual(report["status"], "PASS_WITH_DECLARED_EXCEPTIONS")
        self.assertEqual(report["population_total"], 3000)
        self.assertEqual(report["source_votes"], 1000)
        self.assertEqual(report["incorporated_votes"], 990)
        self.assertEqual(report["ddd_unassigned_votes"], 10)
        self.assertAlmostEqual(report["ddd_loss_ratio"], 0.01)
        self.assertEqual(report["source_gap_to_definitive_votes"], 100)
        self.assertAlmostEqual(report["source_gap_to_definitive_ratio"], 100 / 1100)
        self.assertEqual(int(assigned["votes"].sum()), 990)
        self.assertEqual(
            report["unassigned_votes_breakdown"]["by_section"],
            [{"section_id": "3999901001", "votes": 10}],
        )
        self.assertEqual(
            report["unassigned_votes_breakdown"]["by_province"],
            [{"province_code": "39", "votes": 10}],
        )
        # El hueco de la fuente frente al definitivo no se suma a la pérdida DDD.
        self.assertEqual(
            report["source_gap_to_definitive_votes"] + report["ddd_unassigned_votes"],
            110,
        )
        self.assertEqual(report["unassigned_votes"], 10)

    def test_population_section_without_electoral_results_keeps_population_without_fabricated_votes(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002"],
                "party": ["P", "P"],
                "votes": [600, 400],
            }
        )
        _, report = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={},
        )

        self.assertEqual(report["status"], "PASS_WITH_DECLARED_EXCEPTIONS")
        self.assertEqual(report["source_votes"], 1000)
        self.assertEqual(report["incorporated_votes"], 1000)
        self.assertEqual(report["ddd_unassigned_votes"], 0)
        self.assertEqual(
            report["map_only_sections"],
            [{"section_id": "3900201001", "population": 800}],
        )

    def test_exactly_1_5_percent_is_accepted(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3999901001"],
                "party": ["P", "P", "P"],
                "votes": [600, 385, 15],
            }
        )
        _, report = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={},
        )
        self.assertEqual(report["source_votes"], 1000)
        self.assertEqual(report["ddd_unassigned_votes"], 15)
        self.assertEqual(report["status"], "PASS_WITH_DECLARED_EXCEPTIONS")
        self.assertEqual(report["ddd_loss_ratio"], 0.015)

    def test_one_vote_above_1_5_percent_is_rejected(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3999901001"],
                "party": ["P", "P", "P"],
                "votes": [600, 384, 16],
            }
        )
        _, report = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={},
        )
        self.assertEqual(report["source_votes"], 1000)
        self.assertEqual(report["ddd_unassigned_votes"], 16)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(
            any("por encima del margen" in error for error in report["errors"])
        )

    def test_ddd_loss_above_1_5_percent_blocks(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3999901001"],
                "party": ["P", "P", "P"],
                "votes": [600, 380, 20],
            }
        )
        _, report = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={},
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertAlmostEqual(report["ddd_loss_ratio"], 0.02)
        self.assertTrue(
            any("por encima del margen" in error for error in report["errors"])
        )

    def test_unmeasurable_ddd_loss_blocks_explicitly(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001"],
                "party": ["P"],
                "votes": [0],
            }
        )
        _, report = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={},
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIsNone(report["ddd_loss_ratio"])
        self.assertTrue(
            any("no se puede medir" in error for error in report["errors"])
        )

    def test_population_is_not_the_electoral_loss_denominator(self):
        mapping = self.mapping()
        mapping["population"] = [1000000, 1000000, 1000000]
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3999901001"],
                "party": ["P", "P", "P"],
                "votes": [600, 390, 10],
            }
        )
        _, report = reconcile_sections(
            mapping,
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={},
        )
        self.assertEqual(report["population_total"], 3000000)
        self.assertAlmostEqual(report["ddd_loss_ratio"], 10 / 1000)
        self.assertNotAlmostEqual(report["ddd_loss_ratio"], 10 / 3000000)

    def test_explicit_lower_budget_is_allowed_but_budget_above_1_5_is_not(self):
        results = pd.DataFrame(
            {
                "section": ["3900101001", "3900101002", "3999901001"],
                "party": ["P", "P", "P"],
                "votes": [600, 390, 10],
            }
        )
        _, strict = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={"max_ddd_loss_ratio": 0.005},
        )
        self.assertEqual(strict["status"], "FAIL")

        _, invalid = reconcile_sections(
            self.mapping(),
            results,
            section_field="section",
            district_field="district",
            population_field="population",
            policy={"max_ddd_loss_ratio": 0.02},
        )
        self.assertEqual(invalid["status"], "FAIL")
        self.assertTrue(
            any("máximo provisional" in error for error in invalid["errors"])
        )


if __name__ == "__main__":
    unittest.main()
