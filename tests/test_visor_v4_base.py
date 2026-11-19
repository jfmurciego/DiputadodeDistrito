"""T-415 PR 1: base de visor/v4 (portada). Esperados literales, no recalculados."""
import hashlib
import json
import re
import unittest
from pathlib import Path

V4 = Path(__file__).resolve().parent.parent / "visor" / "v4"
PAGINAS = ["index.html", "comprender.html", "auditoria-registro.html"]
# sha256 de los WebP de la autora (final/SHA256SUMS y assets-manifest.json de la entrega)
SHA = {
    "congreso.webp": "ece374b9094acb48eb1ae0b1714440e4401a3154935bb444169bf211da8d13b6",
}


def _txt(p):
    return (V4 / p).read_text(encoding="utf-8")


class PortadaV4(unittest.TestCase):
    def test_enlaces_locales_y_anclas_resuelven(self):
        for pag in PAGINAS:
            h = _txt(pag)
            for ref in re.findall(r'(?:href|src)="([^"#:?]+)(?:[?#][^"]*)?"', h):
                destino = (V4 / ref).resolve()
                self.assertTrue(destino.exists(), f"{pag}: {ref}")
        for pag in PAGINAS:
            for r, a in re.findall(r'href="([^"#:]*)#([^"]+)"', _txt(pag)):
                self.assertIn(f'id="{a}"', _txt(r or pag), f"{pag}: ancla {a}")

    def test_explorar_va_al_mapa_v4_y_no_a_v3(self):
        for pag in PAGINAS:
            h = _txt(pag)
            self.assertNotIn("/v3/", h, pag)
            self.assertNotIn("diputadodedistrito.es", h, pag)
        self.assertIn('href="mapa/"', _txt("index.html"))

    def test_sin_nomenclatura_vieja(self):
        for pag in PAGINAS:
            self.assertIsNone(re.search(r"\bM0[1-8]\b", _txt(pag)), pag)

    def test_catalogo_doi_vacio(self):
        self.assertIn("window.DDD_MAPS = [];", _txt("catalogo-mapas.js"))

    def test_sin_recursos_externos_ni_rutas_privadas(self):
        malo = re.compile(r"/Users/|/home/|C:\\|chatgpt\.com|account_id|@[a-z0-9.-]+\.[a-z]{2,}", re.I)
        for f in PAGINAS + ["styles.css", "app.js", "catalogo-mapas.js", "assets-manifest.json", "NOTICE.md"]:
            self.assertIsNone(malo.search(_txt(f)), f)
        for pag in PAGINAS:
            for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', _txt(pag)):
                self.assertTrue(u.startswith(("https://orcid.org/", "https://www.linkedin.com/")), f"{pag}: {u}")
        self.assertNotRegex(_txt("styles.css"), r"url\(\s*['\"]?https?:|@import")

    def test_webp_coinciden_con_manifiesto(self):
        man = json.loads(_txt("assets-manifest.json"))
        self.assertEqual(len(man["assets"]), 3)
        for a in man["assets"]:
            h = hashlib.sha256((V4 / a["file"]).read_bytes()).hexdigest()
            self.assertEqual(h, a["sha256"], a["file"])
        h = hashlib.sha256((V4 / "assets/congreso.webp").read_bytes()).hexdigest()
        self.assertEqual(h, SHA["congreso.webp"])

    def test_video_configurable_y_vacio(self):
        cfg = json.loads(_txt("video.json"))
        self.assertEqual(set(cfg), {"base", "video", "poster", "subtitulos", "transcripcion"})
        self.assertTrue(cfg["base"].startswith("https://"))
        for k in ("video", "poster", "subtitulos", "transcripcion"):
            self.assertEqual(cfg[k], "", k)  # la ruta real la aporta el propietario
        # la URL del bucket solo vive en video.json, nunca fija en el código
        for f in PAGINAS + ["app.js", "styles.css"]:
            self.assertNotIn("r2.dev", _txt(f), f)
        h = _txt("index.html")
        self.assertRegex(h, r'<section[^>]*data-video[^>]*\bhidden\b')
        self.assertNotIn("<video", h)  # el reproductor no se carga hasta pulsar
        self.assertNotRegex(_txt("app.js"), r"autoplay")

    def test_doble_vuelta_en_comprender(self):
        h = _txt("comprender.html")
        self.assertIn('id="doble-vuelta"', h)
        for t in ("Izquierdas", "Nacionalistas", "Patriotas", "Simulación sin valor oficial", "mapa/?regla=tres"):
            self.assertIn(t, h)
        self.assertIn("tokens-bloques.css", h)

    def test_contraste_de_tokens_de_bloques(self):
        css = _txt("tokens-bloques.css")

        def lum(hexc):
            c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
            return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

        def ratio(a, b):
            la, lb = sorted((lum(a), lum(b)), reverse=True)
            return (la + 0.05) / (lb + 0.05)

        claro = dict(re.findall(r"--(izq|nac|pat|sin):(#[0-9a-f]{6})", css.split("@media")[0]))
        oscuro = dict(re.findall(r"--(izq|nac|pat|sin):(#[0-9a-f]{6})", css.split("[data-theme=dark]{")[1]))
        self.assertEqual(set(claro), {"izq", "nac", "pat", "sin"})
        self.assertEqual(set(oscuro), {"izq", "nac", "pat", "sin"})
        # texto/objetos: WCAG 2.1 ≥ 4,5 sobre #fffdf8 (claro) y sobre #14181a y #0b0d0e (oscuro)
        for k, v in claro.items():
            self.assertGreaterEqual(ratio(v, "#fffdf8"), 4.5, f"claro {k}")
        for k, v in oscuro.items():
            for fondo in ("#14181a", "#0b0d0e"):
                self.assertGreaterEqual(ratio(v, fondo), 4.5, f"oscuro {k} sobre {fondo}")
        # valores literales de T-413 §2 / D-172
        self.assertEqual((claro["izq"], oscuro["izq"]), ("#b3261e", "#ff8a80"))

    def test_lang_y_una_h1(self):
        for pag in PAGINAS:
            h = _txt(pag)
            self.assertIn('<html lang="es"', h, pag)
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, pag)


if __name__ == "__main__":
    unittest.main()
