"""T-426: adaptador CREM Murcia 2023 (votos por sección). Valores esperados: fila «Región de Murcia» oficial del propio CREM
(sec54.xls, PP 293.051, PSOE 175.505, VOX 121.321) y composición M06; no se recalculan con el código del adaptador."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import adaptador_crem_murcia_2023 as a  # noqa: E402

F = ROOT / "fuentes/crem_murcia_2023"


class CremMurcia2023(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.man = a.construir(F / "sec54.xls", F / "sec55.xls", Path(cls.tmp.name))
        with (Path(cls.tmp.name) / "secciones.csv").open(encoding="utf-8") as f:
            cls.filas = list(csv.DictReader(f))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_secciones_igual_composicion(self):
        with (ROOT / "datos/composicion/region_de_murcia.csv").open(encoding="utf-8") as f:
            comp = {r["seccion"] for r in csv.DictReader(f)}
        self.assertEqual({r["section_id"] for r in self.filas}, comp)

    def test_cuadre_con_total_regional_oficial_sin_cera(self):
        oficial = {"PP": 293051, "PSOE": 175505, "VOX": 121321}
        for p, tot in oficial.items():
            suma = self.man["votos_por_partido"][p]
            self.assertLessEqual(suma, tot)
            self.assertLess(tot - suma, 1000)  # la diferencia es el voto C.E.R.A., declarado fuera de las secciones
        self.assertEqual(self.man["votos_a_candidaturas"] + self.man["cera_votos_a_candidaturas_excluidos"], 676554)

    def test_huella_incorrecta_falla(self):
        with tempfile.TemporaryDirectory() as t:
            malo = Path(t) / "x.xls"
            malo.write_bytes(b"no")
            with self.assertRaises(ValueError):
                a.construir(malo, F / "sec55.xls", Path(t) / "o")


if __name__ == "__main__":
    unittest.main()
