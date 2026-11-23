"""T-426: adaptador SADEI Asturias 2023 (votos por concejo). Esperado: 78 concejos de Asturias (INE) y totales oficiales
de la fila ASTURIAS de la propia tabla SADEI (PSOE 195.999, PP 175.131, VOX 54.273)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import adaptador_sadei_asturias_2023 as a  # noqa: E402

F = ROOT / "fuentes/sadei_asturias_2023/190426_votos_2023.csv"


class SadeiAsturias2023(unittest.TestCase):
    def test_cuadre_y_concejos(self):
        with tempfile.TemporaryDirectory() as t:
            m = a.construir(F, Path(t))
        self.assertEqual(m["municipios"], 78)
        self.assertTrue(m["cuadra_con_total_oficial"])
        self.assertEqual(m["total_oficial"]["PSOE"], 195999)
        self.assertEqual(m["total_oficial"]["PP"], 175131)
        self.assertEqual(m["total_oficial"]["VOX"], 54273)
        self.assertEqual(m["votos_municipios"]["PSOE"] + m["votos_ausentes_no_repartidos"]["PSOE"], 195999)

    def test_huella_incorrecta_falla(self):
        with tempfile.TemporaryDirectory() as t:
            malo = Path(t) / "x.csv"
            malo.write_text("no")
            with self.assertRaises(ValueError):
                a.construir(malo, Path(t) / "o")


if __name__ == "__main__":
    unittest.main()
