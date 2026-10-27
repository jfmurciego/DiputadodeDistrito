"""DDD plan migration 1.0.0, 2026-10-11; local directed regression, new file."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "infraestructura/ordenes-manuales/migrar_plan.py"
spec = importlib.util.spec_from_file_location("ddd_plan_migration", MODULE)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)
BASE = MODULE.parent


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.authority = self.root / "instruction.txt"
        self.authority.write_text("Actual test instruction: reconcile a local isolated copy. No production.")
        self.catalog = json.loads((BASE / "catalogo.json").read_text())
        self.specs = {t["id"]: t for t in self.catalog["tasks"]}
        self.state = {"plan_id": "fixture", "tasks": []}
        for task in self.catalog["tasks"][:32]:
            self.state["tasks"].append(dict(task, status="PENDING", evidence=[]))
        self.task("F02")["status"] = "PASS"
        self.task("F02")["evidence"] = [{"closure": "CLOSED", "independent_review": "REVIEW_PASS",
                                       "decision": {"authorization": "Existing owner closure"}}]
        self.task("F09")["status"] = "PASS"
        self.events = [{"task_id": "F02", "status": "PENDING"},
                       {"task_id": "F09", "status": "PASS"}]
        self.write_source()

    def tearDown(self):
        self.tmp.cleanup()

    def task(self, task_id):
        return next(task for task in self.state["tasks"] if task["id"] == task_id)

    def write_source(self):
        (self.source / "plan.md").write_text("# Historical plan\n")
        (self.source / "estado.json").write_text(json.dumps(self.state))
        (self.source / "eventos.jsonl").write_bytes(b"".join(migration.canonical(e)+b"\n" for e in self.events))

    def run_migrate(self, **kw):
        return migration.migrate(self.source, kw.pop("catalog", BASE / "catalogo.json"),
                                 kw.pop("output", self.root / "candidate"),
                                 kw.pop("authority", self.authority), **kw)

    def test_more_than_32_preserve_pass_and_ledger_exact_prefix(self):
        before = {p.name: p.read_bytes() for p in self.source.iterdir()}
        report = self.run_migrate()
        self.assertEqual(report["tasks"], 58)
        self.assertEqual(report["added_tasks"], 26)
        self.assertEqual(report["formal_counts"], {"PASS": 2, "PENDING": 56})
        candidate = self.root / "candidate"
        self.assertTrue((candidate / "eventos.jsonl").read_bytes().startswith(before["eventos.jsonl"]))
        self.assertEqual(migration.digest(before["eventos.jsonl"]), report["ledger_prefix_sha256"])
        for p in self.source.iterdir():
            self.assertEqual(p.read_bytes(), before[p.name])
        state = migration.read_json(candidate / "estado.json")
        self.assertEqual(next(t for t in state["tasks"] if t["id"] == "F09")["status"], "PASS")
        f04 = next(t for t in state["tasks"] if t["id"] == "F04")
        self.assertEqual((f04["status"], f04["technical_status"]), ("PENDING", "WAIT_OWNER"))

    def test_successful_repeat_is_byte_identical(self):
        first = self.run_migrate()
        all_bytes = {str(p): p.read_bytes() for p in (self.root / "candidate").rglob("*") if p.is_file()}
        second = self.run_migrate()
        self.assertEqual(first, second)
        self.assertEqual(all_bytes, {str(p): p.read_bytes() for p in (self.root / "candidate").rglob("*") if p.is_file()})

    def test_tampered_output_refuses_idempotent_reuse(self):
        self.run_migrate()
        (self.root / "candidate" / "estado.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "TAMPERED"):
            self.run_migrate()

    def test_truncated_ledger_preserved_and_refused(self):
        path = self.source / "eventos.jsonl"
        data = path.read_bytes()+b'{"unfinished":'
        path.write_bytes(data)
        with self.assertRaisesRegex(ValueError, "LEDGER_TRUNCATED"):
            self.run_migrate()
        self.assertEqual(path.read_bytes(), data)
        self.assertFalse((self.root / "candidate").exists())

    def test_bad_ledger_json_preserved_and_refused(self):
        path = self.source / "eventos.jsonl"
        path.write_bytes(b"bad\n")
        with self.assertRaisesRegex(ValueError, "LEDGER_INVALID"):
            self.run_migrate()

    def test_no_actual_instruction_refuses(self):
        with self.assertRaisesRegex(ValueError, "AUTHORITY_REFERENCE_REQUIRED"):
            self.run_migrate(authority=None)

    def test_source_cannot_be_destination(self):
        with self.assertRaisesRegex(ValueError, "ISOLATED_OUTPUT_REQUIRED"):
            self.run_migrate(output=self.source)
        with self.assertRaisesRegex(ValueError, "ISOLATED_OUTPUT_REQUIRED"):
            self.run_migrate(output=self.source / "copy")

    def test_f02_missing_decision_refuses_reconciliation(self):
        self.task("F02")["evidence"] = []
        self.write_source()
        with self.assertRaisesRegex(ValueError, "F02_FORMAL_DECISION_MISSING"):
            self.run_migrate()

    def test_other_formal_conflict_refuses(self):
        self.task("F09")["status"] = "PENDING"
        self.write_source()
        with self.assertRaisesRegex(ValueError, "UNRESOLVED_FORMAL_CONTRADICTION"):
            self.run_migrate()

    def test_duplicates_alias_collision_unknown_dependency_and_cycles(self):
        for error, change in [
            ("DUPLICATE_ID", lambda c: c["tasks"].append(copy.deepcopy(c["tasks"][0]))),
            ("ALIAS_COLLISION", lambda c: c["tasks"][0].update(aliases=["N01"])),
            ("INVALID_DEPENDENCY", lambda c: c["tasks"][0].update(depends_on=["missing"])),
            ("DEPENDENCY_CYCLE", lambda c: c["tasks"][0].update(preparation_dependencies=["F02"]))]:
            candidate = copy.deepcopy(self.catalog)
            change(candidate)
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                migration.validate_catalog(candidate, BASE)

    def test_aliases_recent_distinct_from_original(self):
        self.assertEqual(self.specs["H-N-01"]["aliases"], ["N1"])
        self.assertEqual(self.specs["H-N-02"]["aliases"], ["N2"])
        self.assertIn("A2", self.specs["H-A-03"]["aliases"])
        self.assertEqual(self.specs["A02"]["aliases"], [])

    def test_gate_dependencies_and_dedup_do_not_close_tasks(self):
        self.assertEqual(self.specs["F06"]["preparation_dependencies"], ["F02"])
        self.assertEqual(self.specs["F06"]["depends_on"], ["F04"])
        for task_id in ("A05", "A06", "A08", "N03", "N04", "N05", "N07"):
            self.assertEqual(self.specs[task_id]["preparation_dependencies"], [])
        self.assertEqual(self.specs["N08"]["acceptance_dependencies"], ["N06", "N07"])
        self.run_migrate()
        index = migration.read_json(self.root / "candidate" / "indice.json")
        self.assertEqual(set(index["tables"]), set(migration.TABLES))
        overlap = [r for r in index["relations"] if r["relation"] == "overlaps_initiative"]
        self.assertEqual(len(overlap), 17)
        self.assertTrue(all(r["provenance"]["does_not_close_target"] for r in overlap))

    def test_every_transition_has_real_evidence_reference_no_forged_authority(self):
        self.run_migrate()
        events = migration.parse_ledger((self.root / "candidate" / "eventos.jsonl").read_bytes())[2:]
        for event in events:
            self.assertEqual(event["actor"], "Codex")
            self.assertNotIn("authority", event)
            self.assertEqual(event["authority_ref"]["sha256"], migration.digest(self.authority.read_bytes()))
            self.assertEqual(event["manifest_sha256"], migration.digest((BASE / "catalogo.json").read_bytes()))
        self.assertEqual(migration.replay_formal(events)["F02"], "PASS")

    def test_prompt_hash_and_path_guard_and_exact_long_bytes(self):
        migration.validate_catalog(self.catalog, BASE)
        for task in self.catalog["tasks"]:
            data = (BASE / task["prompt_file"]).read_bytes()
            self.assertGreater(len(data), 4000)
            self.assertEqual(migration.digest(data), task["prompt_sha256"])
        bad = copy.deepcopy(self.catalog)
        bad["tasks"][0]["prompt_sha256"] = "bad"
        with self.assertRaisesRegex(ValueError, "PROMPT_HASH_MISMATCH"):
            migration.validate_catalog(bad, BASE)
        bad["tasks"][0]["prompt_file"] = "../ddd.py"
        with self.assertRaisesRegex(ValueError, "PROMPT_MISSING"):
            migration.validate_catalog(bad, BASE)

    def test_negative_research_record_never_promotes(self):
        receipt = self.root / "negative.json"
        receipt.write_text('{"result":"NO_GO"}')
        evidence = self.root / "inventory.json"
        evidence.write_text(json.dumps({"items": [{"entity_type": "research_experiment",
            "file": migration.fingerprint(receipt), "work_items": ["H-A-04"],
            "result": "NO_GO", "investigation_closed_locally": True}]}))
        self.run_migrate(evidence_manifest=evidence)
        state = migration.read_json(self.root / "candidate" / "estado.json")
        self.assertEqual(next(t for t in state["tasks"] if t["id"] == "H-A-04")["status"], "PENDING")
        index = migration.read_json(self.root / "candidate" / "indice.json")
        self.assertEqual(index["tables"]["research_experiment"][0]["data"]["result"], "NO_GO")
        receipt.write_text("changed")
        with self.assertRaisesRegex(ValueError, "EVIDENCE_HASH_MISMATCH"):
            self.run_migrate(output=self.root / "other", evidence_manifest=evidence)

    def test_already_evidenced_requires_receipt_and_keeps_formal_pending(self):
        reviewed = self.root / "reviewed.txt"
        reviewed.write_text("Historic investigation reviewed on these exact bytes")
        evidence = self.root / "inventory.json"
        evidence.write_text(json.dumps({"items": [], "work_item_dispositions": {"H-A-07": {
            "technical_status": "ALREADY_EVIDENCED", "scope": "historical investigation only",
            "evidence_refs": [migration.fingerprint(reviewed)]}}}))
        self.run_migrate(evidence_manifest=evidence)
        state = migration.read_json(self.root / "candidate" / "estado.json")
        task = next(t for t in state["tasks"] if t["id"] == "H-A-07")
        self.assertEqual(task["status"], "PENDING")
        self.assertEqual(task["technical_status"], "ALREADY_EVIDENCED")
        self.assertEqual(task["inventory_receipt"]["sha256"], migration.digest(evidence.read_bytes()))
        reviewed.write_text("changed")
        with self.assertRaisesRegex(ValueError, "HISTORICAL_DISPOSITION_EVIDENCE_MISSING"):
            self.run_migrate(output=self.root / "other", evidence_manifest=evidence)

    def test_rollback_snapshot_reconstructs_old_ids_without_erasing_events(self):
        events = [{"task_id": "F09", "to": "PASS"}, {"task_id": "new", "to": "PENDING"},
                  {"event": "PLAN_INDEX_RECONCILIATION", "formal_snapshot": {"F09": "PASS"}}]
        self.assertEqual(migration.replay_formal(events), {"F09": "PASS"})
        self.assertEqual(len(events), 3)


if __name__ == "__main__":
    unittest.main()
