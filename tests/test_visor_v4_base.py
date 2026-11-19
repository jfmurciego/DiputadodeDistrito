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
            for ref in re.findall(r'(?:href|src)="([^"#:]+)(?:#([^"]*))?"', h):
                destino = (V4 / ref[0]).resolve()
                self.assertTrue(destino.exists(), f"{pag}: {ref[0]}")
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

    def test_lang_y_una_h1(self):
        for pag in PAGINAS:
            h = _txt(pag)
            self.assertIn('<html lang="es"', h, pag)
            self.assertEqual(len(re.findall(r"<h1[ >]", h)), 1, pag)


if __name__ == "__main__":
    unittest.main()
