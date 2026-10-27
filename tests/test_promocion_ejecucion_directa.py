"""Regresión: promover_catalogo_operacional.py ejecutado por ruta desde el workflow 02.

El paso "Registrar producto territorial certificado" invoca
`python herramientas/promover_catalogo_operacional.py` sin PYTHONPATH, de modo que
sys.path[0] es `herramientas/` y el paquete `herramientas` no es importable.
El 27-10-2026 los runs 40544326534, 40544333932 y 40544340229 fallaron así con
ModuleNotFoundError al importar manifest_sha256 dentro de promote().
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas" / "promover_catalogo_operacional.py"
WORKFLOW = ROOT / ".github" / "workflows" / "_reutilizable-generacion-territorial.yml"


class PromocionEjecucionDirectaTests(unittest.TestCase):
    def test_workflow_02_invoca_la_herramienta_por_ruta(self):
        self.assertIn("python herramientas/promover_catalogo_operacional.py", WORKFLOW.read_text(encoding="utf-8"))

    def test_ejecucion_directa_resuelve_manifest_sha256(self):
        code = (
            "import sys\n"
            f"sys.path[0] = {str(SCRIPT.parent)!r}\n"
            "import promover_catalogo_operacional as m\n"
            "import manifest_generacion_territorial as g\n"
            "assert m.promote.__globals__['manifest_sha256'] is g.manifest_sha256\n"
        )
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "herramientas",
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_sin_imports_de_paquete_fuera_del_bloque_con_respaldo(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        guarded = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Try) and any(
                    h.type is not None and "ModuleNotFoundError" in ast.unparse(h.type) for h in node.handlers):
                guarded.update(id(child) for stmt in node.body for child in ast.walk(stmt))
        unguarded = [node.lineno for node in ast.walk(tree)
                     if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("herramientas.")
                     and id(node) not in guarded]
        self.assertEqual(unguarded, [], "import de herramientas.* sin respaldo de ejecución directa")


if __name__ == "__main__":
    unittest.main()
