#!/usr/bin/env python3
"""
PROYECTO: Diputado de Distrito
PRUEBAS: Reconciliación electoral M07
VERSIÓN: 1.0.0
FECHA: 2026-09-13
QUÉ HACE: prueba el contrato de integridad incorporado por el Paquete A.
ESTADO: vigente — C-05/C-09
ANTERIOR: ninguno — prueba nueva.
"""
import unittest

import pandas as pd

from ddd_core.electoral_reconciliation import reconcile_sections


class ElectoralReconciliation(unittest.TestCase):
    def data(self):
        mapping = pd.DataFrame(
            {"section": ["A", "B", "C"], "district": [1, 1, 2]}
        )
        results = pd.DataFrame(
            {
                "section": ["A", "B", "X"],
                "party": ["P", "P", "P"],
                "votes": [10, 20, 7],
            }
        )
        return mapping, results

    def declared_policy(self, expected_votes=7):
        return {
            "allowed_result_only_sections": [
                {
                    "section_id": "X",
                    "expected_votes": expected_votes,
                    "reason": "cambio censal",
                }
            ],
            "allowed_map_only_sections": [
                {"section_id": "C", "reason": "sin resultados"}
            ],
        }

    def test_declared_mismatches_preserve_vote_identity(self):
        mapping, results = self.data()
        assigned, report = reconcile_sections(
            mapping,
            results,
            section_field="section",
            district_field="district",
            policy=self.declared_policy(),
        )

        self.assertEqual(report["status"], "PASS_WITH_DECLARED_EXCEPTIONS")
        self.assertEqual(
            (
                report["input_votes"],
                report["assigned_votes"],
                report["unassigned_votes"],
            ),
            (37, 30, 7),
        )
        self.assertEqual(int(assigned["votes"].sum()), 30)

    def test_empty_party_list_still_belongs_to_electoral_universe(self):
        mapping, results = self.data()
        _, report = reconcile_sections(
            mapping,
            results,
            section_field="section",
            district_field="district",
            policy={
                "allowed_result_only_sections": [
                    {
                        "section_id": "X",
                        "expected_votes": 7,
                        "reason": "cambio censal",
                    }
                ]
            },
            result_section_ids={"A", "B", "C", "X"},
        )

        self.assertEqual(report["map_only_sections"], [])
        self.assertEqual(report["status"], "PASS_WITH_DECLARED_EXCEPTIONS")

    def test_undeclared_mismatch_fails(self):
        mapping, results = self.data()
        _, report = reconcile_sections(
            mapping,
            results,
            section_field="section",
            district_field="district",
            policy={},
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(report["errors"])

    def test_changed_vote_count_invalidates_exception(self):
        mapping, results = self.data()
        _, report = reconcile_sections(
            mapping,
            results,
            section_field="section",
            district_field="district",
            policy=self.declared_policy(expected_votes=6),
        )
        self.assertEqual(report["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
