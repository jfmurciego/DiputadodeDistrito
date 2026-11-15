"""T-339: smoke de carga de TODOS los entrypoints que invocan procedimiento.sh y los workflows.

Cada ``python X.py`` / ``python -m X`` (lista derivada del repo) se ejecuta con ``--help`` en un subproceso limpio y
por ruta, como en CI, con el PYTHONPATH que fije su workflow. Solo falla por errores de carga (import, atributo,
nombre, sintaxis, sys.modules): es lo que T-338 (#808) no vio porque el proceso de test ya tenía módulos cargados.
"""
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FUENTES = [ROOT / "procedimiento.sh", *sorted((ROOT / ".github" / "workflows").glob("*.yml"))]
PATRON = re.compile(r"\bpython3? (?:-m ([A-Za-z_][\w.]*)|([\w./-]+\.py))")
# Módulos de la biblioteca estándar o de pip que los workflows invocan con -m: no son código del repo.
EXCLUIDOS = {"pip": "pip, no es código del repo", "py_compile": "stdlib", "unittest": "stdlib; ya es la propia suite"}
ERRORES_CARGA = re.compile(r"(ModuleNotFoundError|ImportError|AttributeError|NameError|SyntaxError|TypeError): ")


def entrypoints():
    """{ruta relativa del fichero: (argumentos de python, {fuentes que lo invocan})}"""
    res = {}
    for fuente in FUENTES:
        texto = fuente.read_text(encoding="utf-8", errors="replace")
        for modulo, ruta in PATRON.findall(texto):
            if modulo:
                if modulo in EXCLUIDOS:
                    continue
                fichero = modulo.replace(".", "/") + ".py"
                args = ["-m", modulo]
            else:
                fichero, args = ruta, [ruta]
            if not (ROOT / fichero).is_file():
                continue
            res.setdefault(fichero, (args, set()))[1].add(fuente)
    return res


def _entorno(fuentes):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONSTARTUP")}
    # Como el workflow: solo se añade PYTHONPATH si TODAS las fuentes que lo invocan lo fijan.
    if all("PYTHONPATH" in f.read_text(encoding="utf-8", errors="replace") for f in fuentes):
        env["PYTHONPATH"] = str(ROOT)
    return env


class SmokeEntrypoints(unittest.TestCase):
    def test_hay_entrypoints(self):
        self.assertGreater(len(entrypoints()), 50)

    def test_help_por_ruta_en_subproceso_limpio(self):
        fallos = []
        for fichero, (args, fuentes) in sorted(entrypoints().items()):
            r = subprocess.run([sys.executable, *args, "--help"], cwd=ROOT, env=_entorno(fuentes),
                               capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL)
            if "Traceback" in r.stderr and ERRORES_CARGA.search(r.stderr):
                fallos.append(f"{fichero}: {r.stderr.strip().splitlines()[-1][:200]}")
        self.assertEqual(fallos, [], "entrypoints que no cargan:\n" + "\n".join(fallos))

    def test_validar_fuentes_reanudacion_aut11_llega_a_la_puerta(self):
        # Como procedimiento.sh:85 con params reales y un paquete sin manifiesto: llega al cargador de ids y falla
        # por la puerta esperada, nunca por el cargador (T-338).
        import tempfile
        with tempfile.TemporaryDirectory() as paquete:
            r = subprocess.run([sys.executable, "herramientas/validar_fuentes_reanudacion.py",
                                "--params", "territorios/aut11/config/aut11_2025.yaml",
                                "--package", paquete, "--root-dir", "."],
                               cwd=ROOT, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("Fuentes BLOQUEADAS", r.stderr)
        self.assertNotIn("__dict__", r.stderr)


if __name__ == "__main__":
    unittest.main()
