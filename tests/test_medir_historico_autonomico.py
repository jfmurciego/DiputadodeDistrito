import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import medir_historico_autonomico as m  # noqa: E402


class Cobertura(unittest.TestCase):
    def test_cifras(self):
        f = m.medir()
        self.assertEqual(len(f), 75)  # calendario #568: 79 elecciones, 4 previas a 2011 fuera de alcance
        cuadran = [x for x in f if x["estado"] == "COMPLETA_Y_CUADRA"]
        self.assertGreaterEqual(len(cuadran), 42)
        self.assertEqual([x for x in f if x["estado"] == "EN_REPO_NO_CUADRA"], [])
        # Cantabria 2023 es la única con dato por sección del Observatorio (índice): a mano
        c = {x["eleccion"] for x in f if x["comunidad"] == "cantabria" and x["seccion_en_observatorio"] == "si"}
        self.assertEqual(c, {"202305"})


if __name__ == "__main__":
    unittest.main()
