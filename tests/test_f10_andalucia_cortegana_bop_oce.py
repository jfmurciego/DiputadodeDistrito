"""Safeguards: certified Cortegana election identity must never silently authorize geographic vote transfer."""
from __future__ import annotations
import json
from pathlib import Path
import unittest
FILE=(Path(__file__).resolve().parents[1]/
      "docs/AUDITORIAS/CIERRE_FUENTES_20261017/ANDALUCIA_CORTEGANA_BOP_OCE_2026_EVIDENCIA.json")
class CorteganaOfficialSourceContract(unittest.TestCase):
    def test_official_election_002_is_not_a_standalone_siel_section(self):
        x=json.loads(FILE.read_text(encoding="utf-8"))
        self.assertEqual(x["publication"]["raw_pdf_sha256"],
          "cdd97765f72121a31774d7c0c37f572399ba3c3dca767b44e42bdc4493497dfa")
        self.assertEqual(x["publication"]["github_actions_run"],39240781750)
        self.assertTrue(x["publication"]["raw_pdf_preserved"])
        e=x["locale"]
        self.assertEqual(e["effective_electoral_sections"],["001"])
        self.assertEqual([(t["subsection"],t["table"]) for t in e["polling_tables"]],
          [("01","A"),("02","B"),("03","C")])
        self.assertEqual(e["not_listed_as_independent_section"],"2102502002")
        s=x["siel"]
        self.assertTrue(s["electoral_universe_verified_against_bop"])
        self.assertEqual(s["observed_votes_to_candidacies"],658)
        self.assertEqual(s["observed_party_rows"],15)
        self.assertEqual(s["electoral_sections_national_autonomous"],6044)
        self.assertEqual(s["geographic_candidate_votes_official"],4136317)
        self.assertEqual(s["cera_candidate_votes_official"],21222)
        self.assertEqual(s["total_candidate_votes_official"],4157539)
        self.assertEqual(s["combined_source_verification"]["github_run_id"],39241450837)
        self.assertEqual(s["combined_source_verification"]["conclusion"],"SUCCESS")
        self.assertFalse(x["dictamen"]["generation_authorized"])
        self.assertEqual(x["dictamen"]["crosswalk_to_territorial_2025"],"BLOCKED_CROSSWALK_NOT_PROVEN")
        self.assertEqual(x["dictamen"]["mapping_votes_to_ine_2025"],"BLOCKED_NO_AUTHORISED_CROSSWALK")

