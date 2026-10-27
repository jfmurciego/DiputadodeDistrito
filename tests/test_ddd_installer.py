"""DDD installer 1.3.0 directed offline tests, 2026-10-11, new file.
Install tests mock approval checks in-process; none is a real Codex pilot.
"""
import contextlib
import fcntl
import importlib.util
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1] / "infraestructura/ordenes-manuales"
spec = importlib.util.spec_from_file_location("ddd_installer_test", BASE / "instalar_actualizacion.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.target = self.root / "launcher"
        self.target.mkdir()
        for name in installer.bundle_hashes():
            source = BASE / "legacy/1.2.0" / name
            if source.is_file():
                target = self.target / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        for name in ("parametros.json", "encargos.json", "auto-policy.json"):
            (self.target / name).write_text('{"existing":true}')
        (self.target / "historial.jsonl").write_text('{"result":"TIME_LIMIT"}\n')
        for folder in ("logs", "legacy"):
            (self.target / folder).mkdir()
            (self.target / folder / "old").write_text("preserve bytes")
        (self.target / "ddd.py").chmod(0o751)

    def tearDown(self):
        self.temp.cleanup()

    def contents(self):
        return {str(p.relative_to(self.target)): (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
                for p in self.target.rglob("*") if p.is_file()}

    def simulated_install(self, **kwargs):
        with patch.object(installer, "validate_gates", return_value={"mode": "SIMULATED_UNIT_TEST", "launch_authorized": False}), \
             patch.object(installer, "lock_paths", return_value=[]):
            return installer.install(self.target, None, **kwargs)

    def test_dry_run_no_writes_then_apply_without_gates_no_writes(self):
        before = self.contents()
        command = [sys.executable, str(BASE / "instalar_actualizacion.py"), "--target", str(self.target)]
        dry = subprocess.run(command + ["--dry-run"], capture_output=True, text=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(json.loads(dry.stdout)["apply"], "NO_READY")
        self.assertEqual(before, self.contents())
        apply = subprocess.run(command + ["--apply"], capture_output=True, text=True)
        self.assertEqual(apply.returncode, 2)
        self.assertIn("REAL", apply.stderr)
        self.assertEqual(before, self.contents())
        self.assertFalse((self.root / "launcher-backups").exists())

    def test_external_backup_bytes_modes_protected_and_rollback(self):
        before = self.contents()
        result = self.simulated_install()
        backup = Path(result["backup"])
        self.assertFalse(backup.is_relative_to(self.target))
        report = installer.jsonread(backup / "manifest.json")
        for name, rec in report["files"].items():
            if rec["existed"]:
                self.assertEqual(installer.file_record(backup / name), {k: rec[k] for k in ("sha256", "mode")})
        for name in ("historial.jsonl", "auto-policy.json", "logs/old", "legacy/old"):
            self.assertEqual(before[name], self.contents()[name])
        with patch.object(installer, "lock_paths", return_value=[]):
            rolled = installer.rollback(self.target, backup)
        self.assertEqual(rolled["status"], "ROLLED_BACK")
        self.assertEqual(before, self.contents())

    def test_replacements_failure_restores_all_previous_bytes_and_modes(self):
        before = self.contents()
        original = installer.replace_bytes
        attempts = []
        def fail_once(path, data, mode):
            if path.parent.resolve() == self.target.resolve() and path.name == "ddd_auto.py" and not attempts:
                attempts.append(True)
                raise OSError("simulated disk error")
            return original(path, data, mode)
        with patch.object(installer, "replace_bytes", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "disk error"):
                self.simulated_install()
        self.assertEqual(before, self.contents())
        report = next((self.root / "launcher-backups").glob("*/manifest.json"))
        self.assertEqual(installer.jsonread(report)["status"], "ROLLED_BACK_ON_ERROR")

    def test_predecessor_dirty_rejected_and_legacy_1_0_supported(self):
        (self.target / "ddd_auto.py").write_text("changed")
        with self.assertRaisesRegex(RuntimeError, "INSTALLED_BYTES_CHANGED"):
            installer.check_predecessor(self.target, installer.bundle_hashes())
        old = self.root / "old"
        old.mkdir()
        shutil.copy2(BASE / "legacy/1.0.0/ddd.py", old / "ddd.py")
        self.assertEqual(installer.check_predecessor(old, installer.bundle_hashes()), "1.0.0")

    def test_existing_legacy_lock_blocks_and_preserves_lock_bytes(self):
        path = self.target / ".manual-distritos-autonomicos.lock"
        path.write_text("original lock bytes")
        command = [sys.executable, str(BASE / "instalar_actualizacion.py"), "--target", str(self.target), "--dry-run"]
        with path.open("rb") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertIn("ACTIVE_CONTROLLER_LOCK", result.stdout)
        self.assertEqual(path.read_text(), "original lock bytes")

    def test_running_plan_refuses_before_backup(self):
        plan = self.root / "plan"
        plan.mkdir()
        (plan / "estado.json").write_text('{"tasks":[{"id":"A-OPT-02","status":"RUNNING"}]}')
        with self.assertRaisesRegex(RuntimeError, "NO_HOT_MIGRATION"):
            self.simulated_install(plan_target=plan)
        self.assertFalse((self.root / "launcher-backups").exists())

    def test_simulated_pilot_cannot_satisfy_production_gate(self):
        evidence = self.root / "evidence"
        evidence.write_text("Explicitly simulated fixture")
        ref = {"path": str(evidence), "sha256": installer.digest(evidence)}
        gate = self.root / "gate.json"
        gate.write_text(json.dumps({"schema": "ddd.install-gates/1.0", "technical_review": {
            "verdict": "GO", "mode": "SEPARATE_READ_ONLY_SESSION", "evidence": ref,
            "bundle_hashes": installer.bundle_hashes()}, "real_pilot": {"mode": "SIMULATED", "result": "PASS"}}))
        with self.assertRaisesRegex(RuntimeError, "real Codex"):
            installer.validate_gates(gate, installer.bundle_hashes())

    def test_rollback_refuses_overwriting_new_work(self):
        result = self.simulated_install()
        (self.target / "ddd.py").write_text("new work after installation")
        with patch.object(installer, "lock_paths", return_value=[]), self.assertRaisesRegex(RuntimeError, "ROLLBACK_CHANGED_BYTES"):
            installer.rollback(self.target, Path(result["backup"]))
        self.assertEqual((self.target / "ddd.py").read_text(), "new work after installation")

    def test_manifest_traversal_is_refused(self):
        for name in ("../estado.json", "/absolute", "a/../estado.json", "a//estado.json"):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "UNSAFE_MANIFEST_PATH"):
                installer.validate_relative(name)

    def test_plan_rollback_never_removes_journalled_events(self):
        plan = self.root / "live-plan"
        plan.mkdir()
        (plan / "estado.json").write_text('{"tasks":[{"id":"F09","status":"PASS"}]}')
        original = b'{"task_id":"F09","status":"PASS"}\n'
        (plan / "eventos.jsonl").write_bytes(original)
        candidate = self.root / "candidate"
        candidate.mkdir()
        (candidate / "estado.json").write_text('{"tasks":[{"id":"F09","status":"PASS"},{"id":"new","status":"PENDING"}]}')
        proposed = original+b'{"event":"WORK_ITEM_IMPORTED","task_id":"new","to":"PENDING"}\n'
        (candidate / "eventos.jsonl").write_bytes(proposed)
        (candidate / "plan.md").write_text("# Candidate")
        (plan / "plan.md").write_text("# Original")
        outputs = {p.name: {"sha256": installer.digest(p)} for p in candidate.iterdir()}
        inputs = {p.name: {"sha256": installer.digest(p)} for p in plan.iterdir()}
        (candidate / "migration.json").write_text(json.dumps({"outputs": outputs, "inputs": inputs}))
        result = self.simulated_install(candidate_plan=candidate, plan_target=plan)
        self.assertEqual((plan / "eventos.jsonl").read_bytes(), proposed)
        with patch.object(installer, "lock_paths", return_value=[]):
            installer.rollback(self.target, Path(result["backup"]))
        final = (plan / "eventos.jsonl").read_bytes()
        self.assertTrue(final.startswith(proposed))
        event = json.loads(final.splitlines()[-1])
        self.assertEqual(event["formal_snapshot"], {"F09": "PASS"})
        self.assertEqual(installer.jsonread(plan / "estado.json")["tasks"], [{"id": "F09", "status": "PASS"}])


if __name__ == "__main__":
    unittest.main()
