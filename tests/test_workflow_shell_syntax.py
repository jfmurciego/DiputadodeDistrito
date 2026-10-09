from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
GH_EXPR = re.compile(r"\$\{\{.*?\}\}", re.DOTALL)


def _bash_n(script: str) -> subprocess.CompletedProcess[str]:
    sanitized = GH_EXPR.sub("GH_EXPR", script)
    return subprocess.run(
        ["bash", "-n"],
        input=sanitized,
        text=True,
        capture_output=True,
        check=False,
    )


class WorkflowShellSyntaxTests(unittest.TestCase):
    def test_all_active_bash_run_blocks_are_syntax_valid(self):
        checked = 0
        for workflow_path in sorted(WORKFLOWS.glob("*.yml")):
            workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8")) or {}
            for job_name, job in (workflow.get("jobs") or {}).items():
                if not isinstance(job, dict):
                    continue
                steps = job.get("steps") or []
                if not isinstance(steps, list):
                    continue
                for index, step in enumerate(steps):
                    if not isinstance(step, dict) or "run" not in step:
                        continue
                    shell = str(step.get("shell") or "bash").lower()
                    if "bash" not in shell:
                        continue
                    script = str(step["run"])
                    result = _bash_n(script)
                    checked += 1
                    with self.subTest(
                        workflow=workflow_path.name,
                        job=job_name,
                        step=step.get("name") or step.get("id") or index,
                    ):
                        self.assertEqual(
                            0,
                            result.returncode,
                            result.stderr,
                        )
        self.assertGreater(checked, 0)

    def test_02_prepared_source_selector_bash_block_is_syntax_valid(self):
        workflow = yaml.safe_load(
            (WORKFLOWS / "produccion-distritos.yml").read_text(encoding="utf-8")
        )
        steps = workflow["jobs"]["resolver_interfaz"]["steps"]
        step = next(
            item
            for item in steps
            if item.get("name") == "Resolver paquete territorial preparado"
        )
        script = str(step["run"])
        result = _bash_n(script)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("validate_candidate()", script)
        self.assertIn("seleccionar_paquete_fuentes", script)


if __name__ == "__main__":
    unittest.main()
