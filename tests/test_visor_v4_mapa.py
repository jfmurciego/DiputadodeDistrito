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
        # tokens de bloque: fuente única visor/v4/tokens-bloques.css; fondo: mapa.css (claro #fffdf8, oscuro #14181a)
        tok = (MAPA.parent / "tokens-bloques.css").read_text(encoding="utf-8")
        css = (MAPA / "mapa.css").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"--(izq|nac|pat|sin)\s*:", css))  # sin definiciones duplicadas (solo se usan)
        claro = dict(re.findall(r"--(izq|nac|pat|sin):(#[0-9a-f]{6})", tok.split("@media")[0]))
        oscuro = dict(re.findall(r"--(izq|nac|pat|sin):(#[0-9a-f]{6})", tok.split("[data-theme=dark]{")[1]))
        fondos = {"claro": re.search(r"--bg:(#[0-9a-f]{6})", css.split("@media")[0]).group(1),
                  "oscuro": re.search(r"--bg:(#[0-9a-f]{6})", css.split("@media")[1].split("}")[0]).group(1)}
        self.assertEqual(fondos, {"claro": "#fffdf8", "oscuro": "#14181a"})
        for nombre, tema in (("claro", claro), ("oscuro", oscuro)):
            self.assertEqual(set(tema), {"izq", "nac", "pat", "sin"})
            for k, v in tema.items():
                self.assertGreaterEqual(_cr(v, fondos[nombre]), 4.5, f"{nombre} {k}")

    def test_pagina_real_lee_datos_y_enlaza_tokens(self):
        h = (MAPA / "index.html").read_text(encoding="utf-8")
        for t in ("../tokens-bloques.css", "geo.js", "dv.js", "mapa.js", 'id="territorio"', 'id="mapa"', "Simulación sin valor oficial",
                  "mayoría aritmética", "irán a la segunda", "Así aseguramos que el ciudadano tenga la última palabra, no los partidos."):
            self.assertIn(t, h)
        js = (MAPA / "mapa.js").read_text(encoding="utf-8")
        self.assertIn('pedir("datos/INDEX.json")', js)
        self.assertIn("crypto.subtle", js)  # verifica el sha256 antes de mostrar nada

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
