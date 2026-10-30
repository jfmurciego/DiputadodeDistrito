"""Regresión funcional del diagnóstico tras un M05 GerryChain 50 fallido."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"


class GerryChainFailureDiagnosticContract(unittest.TestCase):
    def test_failure_diagnostic_reuses_run_directory_and_preserves_original_log(self):
        source = WF.read_text(encoding="utf-8")
        workflow = yaml.safe_load(source)
        diagnostic_steps = [
            step for step in workflow["jobs"]["m05"].get("steps", [])
            if step.get("name") == "Conservar fallo explícito de GerryChain 50"
        ]
        self.assertEqual(len(diagnostic_steps), 1)
        step = diagnostic_steps[0]
        script = step["run"]
        self.assertIn('python - "$RUNS_DIR"', script)
        self.assertNotIn('"$RUN_DIR"', script)
        self.assertIn('".ddd-logs/$STAGE.log"', script)
        self.assertIn("failure()", step["if"])

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "state" / "run"
            run_dir.mkdir(parents=True)
            metadata = {
                "schema": "ddd.optimization-execution/1.0",
                "execution_status": "FAILED",
                "error_code": "GERRYCHAIN50_ASSIGNMENT_HASHES_NOT_UNIQUE",
                "certification_status": "NOT_CERTIFIED",
            }
            (run_dir / "OPTIMIZATION_EXECUTION.json").write_text(
                json.dumps(metadata), encoding="utf-8"
            )
            logs = root / ".ddd-logs"
            logs.mkdir()
            original_error = b"PortfolioValidationError: GERRYCHAIN50_ASSIGNMENT_HASHES_NOT_UNIQUE\\n"
            (logs / "M05.log").write_bytes(original_error)
            env = dict(os.environ, RUNS_DIR=str(run_dir), STAGE="M05")
            result = subprocess.run(
                ["bash", "-e", "-c", script],
                cwd=root, env=env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output_dir = root / ".ddd-gerrychain50-diagnostic"
            report = json.loads(
                (output_dir / "optimization_execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual(report["error_code"], metadata["error_code"])
            self.assertEqual(report["certification_status"], "NOT_CERTIFIED")
            self.assertEqual((output_dir / "M05.log").read_bytes(), original_error)
            self.assertEqual(
                report["diagnostic_files"]["M05.log"],
                hashlib.sha256(original_error).hexdigest(),
            )

    def test_diagnostic_is_generated_when_metadata_is_missing(self):
        workflow = yaml.safe_load(WF.read_text(encoding="utf-8"))
        step = next(
            s for s in workflow["jobs"]["m05"].get("steps", [])
            if s.get("name") == "Conservar fallo explícito de GerryChain 50"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "state").mkdir()
            env = dict(os.environ, RUNS_DIR=str(root / "state"), STAGE="M05")
            result = subprocess.run(
                ["bash", "-e", "-c", step["run"]],
                cwd=root, env=env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(
                (root / ".ddd-gerrychain50-diagnostic/optimization_execution.json").read_text()
            )
            self.assertEqual(report["certification_status"], "NOT_CERTIFIED")
            self.assertEqual(report["execution_status"], "FAILED")
            self.assertEqual(report["diagnostic_files"], {})


if __name__ == "__main__":
    unittest.main()
