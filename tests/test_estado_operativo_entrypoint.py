from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"
MODULE = "herramientas.persistir_estado_operativo_compartido"


class SharedOperationalStateEntrypointTests(unittest.TestCase):
    def test_orchestrator_invokes_shared_state_persistence_as_module(self):
        workflow = ORCH.read_text(encoding="utf-8")
        self.assertIn(f"python -m {MODULE}", workflow)
        self.assertNotIn(
            "python herramientas/persistir_estado_operativo_compartido.py",
            workflow,
        )

    def test_module_entrypoint_imports_from_repository_root(self):
        result = subprocess.run(
            [sys.executable, "-m", MODULE, "--help"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
