import json
from pathlib import Path
import tempfile
import unittest

from herramientas.preparar_f10_auto_cards import materialize
from herramientas.validar_f10_auto_task import CARDS, EXPECTED, validate, validate_executor_summary


ROOT = Path(__file__).resolve().parents[1]


class F10AutoTaskCardsTests(unittest.TestCase):
    def test_all_four_cards_validate_real_pinned_evidence(self):
        for task_id, expected_gate in EXPECTED.items():
            with self.subTest(task=task_id):
                report = validate(ROOT, task_id)
                self.assertEqual("EVIDENCE_VERIFIED", report["technical_result"])
                self.assertEqual(expected_gate, report["underlying_electoral_gate"])
                self.assertGreaterEqual(report["acceptance_count"], 3)
                self.assertEqual(list(range(report["acceptance_count"])), report["acceptance_covered"])
                self.assertTrue(all(row["identity"] == "HASH_MATCH" for row in report["evidence"]))
                self.assertFalse(report["network"])
                self.assertFalse(report["production"])
                self.assertFalse(report["promotion"])
                if task_id == "F10-AND-CROSSWALK-2025-2026":
                    self.assertEqual(6044, report["recomputed_checks"][0]["expected_sections"])
                    self.assertEqual(4157539, report["recomputed_checks"][0]["official_candidate_votes"])
                if task_id == "F10-ARA-CROSSWALK-2025-2026":
                    self.assertEqual(608, report["recomputed_checks"][0]["result_only_votes"])
                if task_id == "F10-CYL-CROSSWALK-2025-2026":
                    self.assertEqual(15656, report["recomputed_checks"][0]["electoral_only_votes_sum"])
                if task_id == "F10-EXT-ELECTORAL-SOURCE":
                    self.assertEqual(2419, report["recomputed_checks"][0]["computed_delta"])

    def test_all_four_cards_are_direct_controller_extensions_and_read_only(self):
        catalog = json.loads((ROOT / CARDS).read_text())
        self.assertEqual(4, len(catalog["cards"]))
        for card in catalog["cards"]:
            task, spec = card["task"], card["spec"]
            self.assertEqual("fuentes-oficiales", task["front"])
            self.assertEqual("local_read_only", task["authority_class"])
            self.assertEqual("codex", task["execution"])
            self.assertEqual([], task["depends_on"])
            self.assertTrue(task["origin"].startswith("proposed_extension"))
            self.assertEqual("READ_ONLY", spec["work_class"])
            self.assertEqual([], spec["allowed_change_prefixes"])
            self.assertEqual([], spec["prepare_dependencies"])
            self.assertEqual(len(card["acceptance"]), len(spec["validators"][0]["covers"]))
            self.assertTrue(all(v["local_only"] for v in spec["validators"]))

    def test_executor_summary_must_cite_inputs_and_state_remaining_block(self):
        catalog = json.loads((ROOT / CARDS).read_text())
        card = next(row for row in catalog["cards"] if row["id"] == "F10-EXT-ELECTORAL-SOURCE")
        summary = {"task": card["id"], "status": "READY_FOR_REVIEW", "criteria_verified": card["acceptance"],
                   "evidence": [item["path"] for item in card["evidence"]], "tests": ["validator evidence hash"],
                   "limitations": ["fuente definitiva granular permanece BLOCKED"]}
        validate_executor_summary(card, card["id"], summary)
        summary["evidence"] = summary["evidence"][:-1]
        with self.assertRaisesRegex(ValueError, "no cubre criterios"):
            validate_executor_summary(card, card["id"], summary)

    def test_corrupt_hash_and_temporal_identity_fail_closed(self):
        original = json.loads((ROOT / CARDS).read_text())
        original["cards"][0]["evidence"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / CARDS
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, "Hash de evidencia distinto"):
                validate(ROOT, "F10-AND-CROSSWALK-2025-2026", target)

        original = json.loads((ROOT / CARDS).read_text())
        original["cards"][0]["evidence"][0]["json_equals"]["election_date"] = "2025-01-01"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / CARDS
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, "Identidad/valor distinto"):
                validate(ROOT, "F10-AND-CROSSWALK-2025-2026", target)

    def test_materializer_extends_existing_controller_without_touching_source_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            launcher, plan_source, output = base / "launcher", base / "plan", base / "materialized"
            launcher.mkdir(); plan_source.mkdir()
            task = {"id": "BASE", "front": "fuentes-oficiales", "title": "base", "depends_on": [],
                    "execution": "manual", "acceptance": ["preserve"]}
            (launcher / "catalogo.json").write_text(json.dumps({"tasks": [task], "worktrees": {}}))
            (launcher / "auto-policy.json").write_text(json.dumps({"tasks": {}, "authorized_classes": {
                "local_read_only": ["investigation", "diagnostics", "preserve_evidence"]}}))
            plan_state = {"plan_revision": "test", "tasks": [{"id": "BASE", "status": "PENDING",
                          "front": "fuentes-oficiales", "depends_on": [], "acceptance": ["preserve"],
                          "execution": "manual"}]}
            state_bytes = json.dumps(plan_state)
            (plan_source / "estado.json").write_text(state_bytes)
            (plan_source / "catalogo.json").write_text("{}")
            before = (plan_source / "estado.json").read_bytes()
            manifest = materialize(ROOT, launcher, plan_source, output)
            self.assertEqual(set(EXPECTED), set(manifest["task_ids"]))
            self.assertEqual(before, (plan_source / "estado.json").read_bytes())
            built_catalog = json.loads((output / "catalogo.json").read_text())
            built_plan = json.loads((output / "plan/estado.json").read_text())
            self.assertEqual(5, len(built_catalog["tasks"]))
            self.assertEqual(5, len(built_plan["tasks"]))
            self.assertTrue(all(card_id in built_catalog["tasks"][-1]["id"] or card_id in {
                row["id"] for row in built_catalog["tasks"]} for card_id in EXPECTED))
            self.assertFalse(manifest["network"])
            self.assertFalse(manifest["production"])


if __name__ == "__main__":
    unittest.main()
