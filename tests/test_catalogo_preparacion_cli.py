from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "preparacion-fuentes.yml"
SCRIPT = ROOT / "herramientas" / "catalogo_preparacion.py"


class CatalogoPreparacionCliRegression(unittest.TestCase):
    def test_validate_accepts_global_root_dir_before_subcommand(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--root-dir", ".", "validate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("OK", proc.stdout)

    def test_workflow_does_not_put_global_root_dir_after_validate(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "python herramientas/catalogo_preparacion.py --root-dir . validate",
            text,
        )
        self.assertNotIn(
            "python herramientas/catalogo_preparacion.py validate --root-dir .",
            text,
        )


if __name__ == "__main__":
    unittest.main()
