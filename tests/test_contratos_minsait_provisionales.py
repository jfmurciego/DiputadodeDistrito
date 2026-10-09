from __future__ import annotations

import unittest
from pathlib import Path

from herramientas.resolver_contrato_minsait_provisional import resolve

ROOT = Path(__file__).resolve().parents[1]


class MinsaitProvisionalContractsTests(unittest.TestCase):
    def test_andalucia_contract_is_governed_and_non_promotable(self):
        row = resolve(
            election_id="andalucia_parlamento_2026",
            territory_id="andalucia",
            election_date="2026-05-17",
            root_dir=ROOT,
        )
        self.assertEqual(row["expected"]["ccaa"], "01")
        self.assertEqual(row["expected"]["provinces"], 8)
        self.assertEqual(row["expected"]["sections"], 6044)
        self.assertEqual(row["expected"]["polling_stations"], 10403)
        self.assertEqual(row["expected"]["candidate_votes"], 4128575)
        self.assertFalse(row["production_eligible"])
        self.assertFalse(row["promotion_allowed"])

    def test_extremadura_contract_is_complete_and_reconciled_as_known_delta(self):
        row = resolve(
            election_id="extremadura_asamblea_2025-12-21",
            territory_id="extremadura",
            election_date="2025-12-21",
            root_dir=ROOT,
        )
        self.assertEqual(row["expected"], {
            "ccaa": "10",
            "provinces": 2,
            "sections": 966,
            "polling_stations": 1400,
            "candidate_votes": 522418,
        })
        self.assertEqual(row["canonical_codauto"], "11")
        self.assertEqual(row["reconciliation"]["status"], "KNOWN_PROVISIONAL_DELTA")
        self.assertEqual(row["reconciliation"]["definitive"]["candidate_votes"], 524837)
        self.assertEqual(row["reconciliation"]["delta_definitive_minus_provisional"], 2419)
        self.assertFalse(row["production_eligible"])
        self.assertFalse(row["promotion_allowed"])

    def test_contract_rejects_wrong_identity(self):
        with self.assertRaisesRegex(ValueError, "otro territorio"):
            resolve(
                election_id="extremadura_asamblea_2025-12-21",
                territory_id="andalucia",
                election_date="2025-12-21",
                root_dir=ROOT,
            )


if __name__ == "__main__":
    unittest.main()
