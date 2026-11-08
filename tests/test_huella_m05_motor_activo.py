"""T-108: la huella M05 cubre todos los ficheros del motor activo (imports reales desde el punto de entrada)."""
import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path

from herramientas.huella_checkpoint_m05 import ENGINE_FILES, ENTRY

ROOT = Path(__file__).resolve().parents[1]

SONDA = r"""
import importlib.util, json, sys
from pathlib import Path
root = Path(sys.argv[1]).resolve(); sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("m05_entry", root / sys.argv[2])
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod._load_base()
files = {str(Path(mod.BASE_ENGINE).resolve().relative_to(root))}
for m in list(sys.modules.values()):
    f = getattr(m, "__file__", None)
    if f and Path(f).resolve().is_relative_to(root / "ddd_core"):
        files.add(Path(f).resolve().relative_to(root).as_posix())
print(json.dumps(sorted(files)))
"""


class HuellaMotorActivoTests(unittest.TestCase):
    def test_motor_activo_en_huella(self):
        out = subprocess.run([sys.executable, "-c", SONDA, str(ROOT), ENTRY], capture_output=True, text=True,
                             check=True, cwd=ROOT).stdout
        import json
        cargados = set(json.loads(out)) - {"ddd_core/__init__.py"}
        faltan = sorted(cargados - set(ENGINE_FILES))
        self.assertEqual(faltan, [], f"ficheros del motor M05 activo fuera de la huella: {faltan}")

    def test_motor_base_activo_y_no_el_inactivo(self):
        spec = importlib.util.spec_from_file_location("m05_entry_t108", ROOT / ENTRY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        base = Path(mod.BASE_ENGINE).resolve().relative_to(ROOT).as_posix()
        self.assertIn(base, ENGINE_FILES)
        self.assertNotIn("ddd_core/m05_opt_engine_v740.py", ENGINE_FILES)


if __name__ == "__main__":
    unittest.main()
