import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import cuadre_historico_espana as cu  # noqa: E402
import reagregacion_historico as rh  # noqa: E402


class Rotacion(unittest.TestCase):
    def test_ganador_homologado_suma_la_familia(self):
        hom = {("201111", "22", "PP-PAR"): "PP", ("201111", "22", "PP"): "PP", ("201111", "22", "PSOE"): "PSOE"}
        sin = set()
        # PP-PAR 40 + PP 30 = 70 > PSOE 60 (sin homologar el ganador sería PSOE... no: PP-PAR 40 < 60)
        g = rh.ganador_homologado({"PP-PAR": 40, "PP": 30, "PSOE": 60}, hom, "201111", "22", sin)
        self.assertEqual(g, "PP")
        g = rh.ganador_homologado({"XYZ": 5, "PSOE": 4}, hom, "201111", "22", sin)
        self.assertEqual((g, sin), ("XYZ", {("201111", "22", "XYZ")}))

    def test_escribir_rotacion_cuenta_cambios(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.csv"
            rh.escribir_rotacion(p, {"201111": {"0": "PP"}, "201512": {"0": "PSOE"}, "201606": {"0": "PSOE"}})
            self.assertEqual(p.read_text().splitlines(), ["district_id,201111,201512,201606,cambios", "0,PP,PSOE,PSOE,1"])

    def test_lector_infoelectoral(self):
        b = io.BytesIO()
        with zipfile.ZipFile(b, "w") as z:
            z.writestr("03022307.DAT", "02202307000002" + "PSOE".ljust(50) + "x\n")
            z.writestr("08022307.DAT", "02202307" + "1" + "01" + "04" + "9" + "000002" + "00093282" + "00002\n")
            z.writestr("10022307.DAT", "02202307" + "1" + "01" + "04" + "001" + "01" + "001" + " A" + "000002" + "0000100\n"
                       + "02202307" + "1" + "01" + "04" + "999" + "01" + "001" + " A" + "000002" + "0000007\n")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.zip"
            p.write_bytes(b.getvalue())
            r = cu.leer_infoelectoral(p)["04"]
        self.assertEqual((r["total_cand"], r["mesas_sin_cera"], r["cera"], dict(r["partidos"])),
                         (93282, 100, 7, {"PSOE": 93282}))


if __name__ == "__main__":
    unittest.main()
