from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modulos/07_agregar_resultados_electorales.py"
spec = importlib.util.spec_from_file_location("m07_agregar_resultados_electorales", MODULE)
m07 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m07)


class NoVoteRedistributionTests(unittest.TestCase):
    def test_population_weighted_split_is_reported_but_not_applied(self):
        section_party = pd.DataFrame(
            {"section": ["OLD"], "party": ["P"], "votes": [100]}
        )
        current = pd.DataFrame(
            {"section": ["NEW1", "NEW2"], "population": [900, 100]}
        )
        transformed, evidence = m07.apply_section_reconciliation(
            section_party,
            current,
            section_field="section",
            contract={
                "section_reconciliation": {
                    "splits": [
                        {
                            "source_section": "OLD",
                            "target_sections": ["NEW1", "NEW2"],
                            "weighting": "current_population",
                            "population_field": "population",
                        }
                    ]
                }
            },
        )
        self.assertEqual(transformed.to_dict("records"), [{"section": "OLD", "party": "P", "votes": 100}])
        self.assertEqual(evidence["votes_before"], 100)
        self.assertEqual(evidence["votes_after"], 100)
        self.assertEqual(
            evidence["splits_not_applied"][0]["reason"],
            "NO_VOTE_REDISTRIBUTION_BETWEEN_EDITIONS",
        )

    def test_proven_exact_one_to_one_alias_can_be_applied_without_changing_votes(self):
        section_party = pd.DataFrame(
            {"section": ["OLD"], "party": ["P"], "votes": [100]}
        )
        current = pd.DataFrame({"section": ["NEW"], "population": [1000]})
        transformed, evidence = m07.apply_section_reconciliation(
            section_party,
            current,
            section_field="section",
            contract={
                "section_reconciliation": {
                    "aliases": [
                        {
                            "from": "OLD",
                            "to": "NEW",
                            "method": "ine_geometry_exact_overlap_1_to_1",
                        }
                    ]
                }
            },
        )
        self.assertEqual(transformed.to_dict("records"), [{"section": "NEW", "party": "P", "votes": 100}])
        self.assertEqual(len(evidence["aliases_applied"]), 1)

    def test_non_exact_alias_is_not_used_to_force_year_concordance(self):
        section_party = pd.DataFrame(
            {"section": ["OLD"], "party": ["P"], "votes": [100]}
        )
        current = pd.DataFrame({"section": ["NEW"], "population": [1000]})
        transformed, evidence = m07.apply_section_reconciliation(
            section_party,
            current,
            section_field="section",
            contract={
                "section_reconciliation": {
                    "aliases": [
                        {"from": "OLD", "to": "NEW", "method": "heuristic"}
                    ]
                }
            },
        )
        self.assertEqual(transformed.iloc[0]["section"], "OLD")
        self.assertEqual(
            evidence["aliases_not_applied"][0]["reason"],
            "ALIAS_NOT_PROVEN_EXACT_1_TO_1",
        )


if __name__ == "__main__":
    unittest.main()
