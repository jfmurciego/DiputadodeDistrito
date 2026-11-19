"""Mapa V4 con doble vuelta (T-413): pruebas JS, tokens de contraste y datos de ejemplo sin cambios respecto de la herramienta."""
import csv, re, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MAPA = RAIZ / "visor/v4/mapa"


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def _cr(a, b):
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + .05) / (y + .05)


class MapaV4(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "sin node")
    def test_js(self):
        r = subprocess.run(["node", str(RAIZ / "tests/test_visor_v4_mapa.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_contraste_tokens_claro_y_oscuro(self):
        css = (MAPA / "mapa.css").read_text(encoding="utf-8")
        claro = dict(re.findall(r"--(izq|nac|pat|sin|bg):(#[0-9a-f]{6})", css.split("@media")[0]))
        oscuro = dict(re.findall(r"--(izq|nac|pat|sin|bg):(#[0-9a-f]{6})", css.split("@media")[1].split("}")[0]))
        for tema in (claro, oscuro):
            self.assertEqual(len(tema), 5)
            for k in ("izq", "nac", "pat", "sin"):
                self.assertGreaterEqual(_cr(tema[k], tema["bg"]), 4.5, k)

    def test_ejemplos_coinciden_con_la_herramienta(self):
        with tempfile.TemporaryDirectory() as d:
            sal, det = Path(d) / "r.csv", Path(d) / "d.csv"
            subprocess.run([sys.executable, str(RAIZ / "herramientas/doble_vuelta.py"), "--votos", str(MAPA / "ejemplo/votos.csv"),
                            "--bloques", str(RAIZ / "configuracion/bloques_partidos_2026-11-17.csv"), "--eleccion", "2023-07",
                            "--salida", str(sal), "--detalle", str(det)], check=True, capture_output=True)
            self.assertEqual(sal.read_bytes(), (MAPA / "ejemplo/resultados_doble_vuelta.csv").read_bytes())
            self.assertEqual(det.read_bytes(), (MAPA / "ejemplo/detalle.csv").read_bytes())

    def test_sin_enlaces_a_v3_ni_externos(self):
        for f in ("index.html", "mapa.js", "dv.js"):
            t = (MAPA / f).read_text(encoding="utf-8")
            self.assertNotIn("/v3/", t)
            self.assertIsNone(re.search(r"(src|href)=\"https?://", t), f)


if __name__ == "__main__":
    unittest.main()
