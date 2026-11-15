"""T-338: el cargador de territorio_ids funciona en un proceso limpio (sin ddd_core.territorio_ids precargado)."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CODIGO = (
    "import sys, importlib.util, os;"
    "sys.path.insert(0, os.path.dirname(sys.argv[1]));"  # como `python herramientas/x.py`: solo la carpeta del script
    "assert 'ddd_core.territorio_ids' not in sys.modules;"
    "s=importlib.util.spec_from_file_location('m', sys.argv[1]);"
    "m=importlib.util.module_from_spec(s); s.loader.exec_module(m);"
    "ti=m._territorio_ids_t220(); assert ti is not None;"
    "assert m.mismo_territorio('nac35','nac35') is True;"
    "assert m.mismo_territorio('nac35','nac36') is False;"
    "print('OK')"
)


class CargadorTerritorioIds(unittest.TestCase):
    def _limpio(self, rel):
        r = subprocess.run([sys.executable, "-c", CODIGO, str(ROOT / rel)], cwd=ROOT,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("OK", r.stdout)

    def test_validar_fuentes_reanudacion_proceso_limpio(self):
        self._limpio("herramientas/validar_fuentes_reanudacion.py")

    def test_promover_catalogo_operacional_proceso_limpio(self):
        self._limpio("herramientas/promover_catalogo_operacional.py")

    def test_validar_fuentes_reanudacion_por_ruta_como_workflow(self):
        # Se invoca por ruta; con un params inexistente debe fallar por el params, no por el cargador.
        r = subprocess.run([sys.executable, "herramientas/validar_fuentes_reanudacion.py",
                            "--params", "no_existe.yaml", "--package", "no_existe", "--root-dir", "."],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertNotIn("NoneType", r.stderr)
        self.assertNotIn("has no attribute '__dict__'", r.stderr)


if __name__ == "__main__":
    unittest.main()
