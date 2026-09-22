from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DECL = ROOT / "territorios/principado_de_asturias/config/elecciones/asturias_jgpa_2023_vigente.yaml"
CROSSWALK = ROOT / "territorios/principado_de_asturias/config/elecciones/asturias_2023_oviedo_special_crosswalk.json"


class AsturiasElectoralReconciliationTests(unittest.TestCase):
    def test_special_rows_are_governed_oviedo_rows_not_cera(self):
        data = json.loads(CROSSWALK.read_text(encoding="utf-8"))
        rows = data["rows"]
        self.assertEqual(data["schema"], "ddd-election-special-row-crosswalk/1.0")
        self.assertEqual(len(rows), 81)
        self.assertEqual([r["ordinal"] for r in rows], list(range(1, 82)))
        self.assertTrue(all(str(r["target_cusec"]).startswith("33044") for r in rows))
        self.assertTrue(all(str(r["target_cusec"])[5:7] in {"10","11","12","13","14","15","16"} for r in rows))
        self.assertTrue(all(r["special_code"] in {"-00", "-01"} for r in rows))
        self.assertTrue(all(0 <= int(r["census_delta"]) <= 8 for r in rows))
        self.assertEqual(sum(int(r["census_delta"]) for r in rows), 190)
        self.assertEqual(len({r["target_cusec"] for r in rows}), 51)
        self.assertTrue(all(str(r["target_cusec"])[:5] == "33044" for r in rows))
        self.assertTrue(all(str(r["target_cusec"])[5:7] in {"10","11","12","13","14","15","16"} for r in rows))

    def test_declared_official_totals_are_exact_and_cera_is_separate(self):
        cfg = yaml.safe_load(DECL.read_text(encoding="utf-8"))
        verification = cfg["verification"]
        party_totals = verification["official_party_totals"]
        self.assertEqual(sum(int(v) for v in party_totals.values()), 527500)
        self.assertEqual(int(verification["official_candidate_votes"]), 527500)
        self.assertEqual(int(verification["expected_cera_candidate_votes"]), 7034)
        cera = cfg["non_geocodable_vote_policy"]["CERA"]
        self.assertEqual(cera["action"], "exclude_from_geographic_district_allocation")
        self.assertEqual(cera["reporting"], "mandatory")

    def test_2023_to_2025_reconciliation_has_no_declared_map_only_escape(self):
        cfg = yaml.safe_load(DECL.read_text(encoding="utf-8"))
        aliases = cfg["section_reconciliation"]["aliases"]
        self.assertEqual(len(aliases), 8)
        self.assertTrue(all(a["method"] == "ine_geometry_exact_overlap_1_to_1" for a in aliases))
        splits = cfg["section_reconciliation"]["splits"]
        self.assertEqual(
            {s["source_section"] for s in splits},
            {"3302405021", "3302409001"},
        )
        self.assertEqual(cfg["reconciliation"]["allowed_result_only_sections"], [])
        self.assertEqual(cfg["reconciliation"]["allowed_map_only_sections"], [])

    def test_runtime_map_only_is_disabled_by_default(self):
        text = (ROOT / "herramientas/materializar_contrato_electoral_runtime.py").read_text(encoding="utf-8")
        self.assertIn('"allow_declared_map_only_districts": False', text)
        self.assertNotIn('"allow_declared_map_only_districts": True', text)


if __name__ == "__main__":
    unittest.main()
