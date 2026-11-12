import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidencia/rescate_huecos_electorales_2026-10-02"


class ElectoralGapFillerRealEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.real = json.loads((EVIDENCE / "real_validation.json").read_text(encoding="utf-8"))
        self.full = json.loads((EVIDENCE / "extremadura_full_gap_fill_report.json").read_text(encoding="utf-8"))
        self.bad = json.loads((EVIDENCE / "extremadura_badajoz_gap_fill_report.json").read_text(encoding="utf-8"))
        self.cac = json.loads((EVIDENCE / "extremadura_caceres_gap_fill_report.json").read_text(encoding="utf-8"))

    def test_extremadura_gap_is_exactly_decomposed_without_overwriting_zeroes(self):
        gap = self.real["extremadura"]["gap_decomposition"]
        self.assertEqual(gap["badajoz_external"], 891)
        self.assertEqual(gap["caceres_external"], 994)
        self.assertEqual(gap["caceres_explicit_zero_conflicts"], 534)
        self.assertEqual(gap["total"], 2419)
        self.assertEqual(self.full["status"], "BLOCK")
        self.assertEqual(self.full["added_keys"], 0)
        self.assertEqual(self.full["blocked_units"], ["1004201001", "1012501001"])
        self.assertEqual(self.full["special_candidate_votes"], 1885)
        self.assertEqual(self.full["candidate_votes_with_special"], 524303)
        self.assertFalse(self.full["production_eligible"])

    def test_badajoz_reconciles_candidate_total_but_remains_inadmissible(self):
        src = self.real["extremadura"]["badajoz_fragment"]
        self.assertEqual(src["geographic_section_party_differences_vs_primary"], [])
        self.assertEqual(src["geographic_candidate_votes"], 325305)
        self.assertEqual(src["external_candidate_votes"], 891)
        self.assertEqual(src["total_candidate_votes"], 326196)
        self.assertEqual(src["accounting_bad_rows"], 15)
        self.assertNotEqual(
            src["ancillary_totals"],
            {k: src["official_totals"][k] for k in ("electors", "voters", "blank", "null")},
        )
        self.assertEqual(self.bad["status"], "BLOCK_ADMISSIBILITY")

    def test_caceres_definitive_copy_reconciles_but_conflicts_with_explicit_zeroes(self):
        src = self.real["extremadura"]["caceres_fragment"]
        self.assertEqual(src["accounting_bad_rows"], 0)
        self.assertEqual(src["total_candidate_votes"], 198641)
        self.assertEqual(src["official_totals"]["candidate_votes"], 198641)
        self.assertEqual(len(src["differences_vs_primary"]), 13)
        self.assertEqual(
            {x["cusec"] for x in src["differences_vs_primary"]},
            {"1004201001", "1012501001"},
        )
        self.assertTrue(all(x["primary"] == 0 for x in src["differences_vs_primary"]))
        self.assertEqual(self.cac["status"], "BLOCK")
        self.assertEqual(self.cac["geographic_candidate_votes"], 197113)
        self.assertEqual(self.cac["special_candidate_votes"], 994)

    def test_andalucia_does_not_claim_complete_from_unaccredited_opte_capacity(self):
        row = self.real["andalucia"]
        self.assertEqual(row["primary"]["sections"], 6044)
        self.assertEqual(row["primary"]["candidate_votes"], 4128575)
        self.assertEqual(row["official_candidate_votes"], 4157539)
        self.assertEqual(row["gap_candidate_votes"], 28964)
        self.assertEqual(row["opte_inventory"]["structured_rows_used"], 0)
        self.assertEqual(row["opte_inventory"]["status"], "SOURCE_DISCOVERY_ONLY")
        siel = row["official_siel_route"]
        self.assertEqual(siel["status"], "IMPLEMENTED_NOT_EXECUTED_IN_THIS_RESCUE")
        self.assertEqual(siel["expected_sections"], 6044)
        self.assertEqual(siel["official_candidate_votes"], 4157539)
        self.assertTrue((ROOT / siel["acquisition"]).is_file())
        self.assertTrue((ROOT / siel["adapter"]).is_file())
        self.assertTrue((ROOT / siel["manual"]).is_file())

    def test_cuenca_is_no_longer_a_current_gap_and_europe_2024_is_excluded(self):
        row = self.real["castilla_la_mancha"]
        self.assertEqual(row["election_id"], "castilla_la_mancha_cortes_2023")
        self.assertEqual(row["status"], "NO_CURRENT_GAP")
        self.assertEqual(row["cuenca_sections"], 196)
        self.assertFalse(row["european_2024_allowed"])


if __name__ == "__main__":
    unittest.main()
