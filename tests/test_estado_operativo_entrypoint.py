from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = (
    ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml",
    ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml",
)
MODULE = "herramientas.persistir_estado_operativo_compartido"
LEGACY_CALL = "python herramientas/persistir_estado_operativo_compartido.py"
MODULE_CALL = f"python -m {MODULE}"


class SharedOperationalStateEntrypointTests(unittest.TestCase):
    def test_all_productive_callers_use_the_module_entrypoint(self):
        for workflow in WORKFLOWS:
            text = workflow.read_text(encoding="utf-8")
            self.assertIn(MODULE_CALL, text, workflow)
            self.assertNotIn(LEGACY_CALL, text, workflow)

    def test_workflow_cli_invocation_runs_from_checkout_root(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            fixture = tmp / "checkout"
            fixture.mkdir()
            (fixture / "configuracion").symlink_to(ROOT / "configuracion", target_is_directory=True)
            (fixture / "territorios").symlink_to(ROOT / "territorios", target_is_directory=True)
            shutil.copy2(ROOT / "README.md", fixture / "README.md")
            (fixture / "orchestracion").mkdir()
            (fixture / "publicado" / "dashboard").mkdir(parents=True)

            fake_bin = tmp / "bin"
            fake_bin.mkdir()
            fake_git = fake_bin / "git"
            fake_git.write_text(
                "#!/usr/bin/env sh\n"
                "if [ \"$1\" = \"rev-parse\" ]; then printf '%s\\n' workflow-fixture-head; fi\n"
                "if [ \"$1\" = \"ls-remote\" ]; then printf '%s\\t%s\\n' workflow-fixture-head refs/heads/main; fi\n"
                "exit 0\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)

            env = os.environ.copy()
            env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    MODULE,
                    "--root-dir",
                    str(fixture),
                    "--edition",
                    "2025",
                    "--target-branch",
                    "main",
                    "--max-attempts",
                    "1",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "workflow-fixture-head")
            self.assertNotIn("ModuleNotFoundError", result.stderr)
            self.assertTrue((fixture / "orchestracion" / "estado_operativo.json").is_file())
            self.assertTrue((fixture / "publicado" / "dashboard" / "status.json").is_file())


if __name__ == "__main__":
    unittest.main()
