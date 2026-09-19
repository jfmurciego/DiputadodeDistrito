from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "preparacion-fuentes.yml"
ELECTORAL_WORKFLOW = ROOT / ".github" / "workflows" / "preparacion-resultados-electorales.yml"
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


class PreparationEntrypointRegression(unittest.TestCase):
    def test_workflows_use_module_entrypoints(self):
        territorial = WORKFLOW.read_text(encoding="utf-8")
        electoral = ELECTORAL_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("-m herramientas.ejecutar_fuentes_workflow", territorial)
        self.assertNotIn("preparar_fuente_electoral", territorial)
        self.assertIn("python -m herramientas.preparar_fuente_electoral", electoral)
        self.assertNotIn("/app/herramientas/ejecutar_fuentes_workflow.py", territorial)
        self.assertNotIn("python herramientas/preparar_fuente_electoral.py", electoral)

    def test_module_entrypoints_import_cleanly(self):
        for module in (
            "herramientas.ejecutar_fuentes_workflow",
            "herramientas.preparar_fuente_electoral",
        ):
            proc = subprocess.run(
                [sys.executable, "-m", module, "--help"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"{module}: {proc.stderr}")


if __name__ == "__main__":
    unittest.main()
