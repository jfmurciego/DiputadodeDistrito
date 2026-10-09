import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "EJECUCIONES" / "2026-09-18_CYL_M05_FOCAL_LOCAL.json"
CHECKER = ROOT / "herramientas" / "verificar_evidencia_m05_real.py"


class M05RealReproducibilityEvidence(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_evidence_is_bound_to_real_checkpoint_and_production_entrypoint(self):
        self.assertEqual(self.m["validated_source_head"], "d05741ab239b0a5f05455ba642ae702830fec775")
        self.assertEqual(self.m["input"]["origin_run_id"], 35319351944)
        self.assertEqual(self.m["input"]["artifact_name"], "ddd-state-35319351944-M06")
        self.assertEqual(self.m["input"]["artifact_sha256"], "ce0f198fc09a34877853bc0df8a3728be15d842fe2b0ba128ed869f8d5b20944")
        self.assertEqual(self.m["command"]["entrypoint"], "modulos/05_optimizar_distritos.py")
        self.assertEqual(self.m["command"]["argv"][1], "modulos/05_optimizar_distritos.py")
        blobs = {row["path"]: row["git_blob_sha1"] for row in self.m["source_integrity"]["operational_files"]}
        self.assertEqual(blobs["ddd_core/m05_population_repair.py"], "235260463214673c5ef84ca59017d55a102799a2")
        self.assertEqual(blobs["modulos/05_optimizar_distritos.py"], "649b1dad6cbab1fbb553d87322754fca1d102842")

    def test_real_population_progression_and_invariants_are_explicit(self):
        p = self.m["observed_state_progression"]
        self.assertEqual(p["primary_repair_outliers"], 3)
        self.assertEqual(set(p["primary_three_outliers"]), {"1", "46", "51"})
        self.assertEqual(p["focal_repair_outliers"], 0)
        for run in ("run1", "run2"):
            v = self.m["validation"][run]
            self.assertEqual(v["districts"], 82)
            self.assertEqual(v["sections"], 3506)
            self.assertEqual(v["unique_sections"], 3506)
            self.assertEqual(v["lost_sections"], 0)
            self.assertEqual(v["duplicated_sections"], 0)
            self.assertEqual(v["population_total"], 2401221)
            self.assertEqual(v["outliers_after"], 0)
            self.assertEqual(v["disconnected_districts"], 0)
            self.assertEqual(v["multi_province_districts"], 0)
            self.assertEqual(v["municipality_contract_violations"], 0)

    def test_two_real_runs_are_functionally_identical(self):
        d = self.m["determinism"]
        for key in ("canonical_assignment_equal", "inner_geojson_equal", "functional_report_equal", "populations_equal", "repairs_equal", "states_equal", "termination_equal"):
            self.assertTrue(d[key], key)
        self.assertEqual(self.m["runs"]["run1"]["canonical_assignment_sha256"], self.m["runs"]["run2"]["canonical_assignment_sha256"])
        self.assertEqual(self.m["runs"]["run1"]["functional_report_sha256"], self.m["runs"]["run2"]["functional_report_sha256"])
        self.assertEqual(self.m["certification"]["production_certification_gate"], "PASS_WITH_EXCEPTIONS")
        self.assertIsNone(self.m["certification"]["block_cause"])

    def test_checker_validates_evidence_without_reimplementing_repair(self):
        text = CHECKER.read_text(encoding="utf-8")
        self.assertNotIn("from ddd_core.m05_population_repair", text)
        self.assertNotIn("def repair(", text)
        self.assertNotIn("def _focal", text)
        self.assertIn("canonical_assignment", text)
        self.assertIn("functional_report_hash", text)
        self.assertIn("operational_files", text)


if __name__ == "__main__":
    unittest.main()
