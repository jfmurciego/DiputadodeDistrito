"""Versión 1.0.0 — T-506: fotos de provincia en el panel de Explorar (V4), sin créditos en el panel y con página de créditos.
Fecha: 2026-11-26. Estado: candidato. Anterior: ninguna (fichero nuevo).
Esperados literales: 52 provincias INE 01-52; los ficheros y sha256 salen del catálogo real, no del código."""
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAL = ROOT / "visor" / "v2" / "galeria"
V4 = ROOT / "visor" / "v4" / "mapa"
PROV = ["%02d" % i for i in range(1, 53)]


class FotosProvincia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cat = json.loads((GAL / "catalogo.json").read_text(encoding="utf-8"))
        cls.por_id = {i["id"]: i for i in cls.cat["imagenes"]}
        cls.cred = (GAL / "creditos.html").read_text(encoding="utf-8")

    def test_52_provincias_con_foto_existente_y_sha256(self):
        self.assertEqual(len(PROV), 52)
        for c in PROV:
            img = self.por_id[self.cat["territorios"]["provincia:" + c]]
            f = GAL / img["archivo"]
            self.assertTrue(f.is_file(), f"falta la foto de la provincia {c}: {f}")
            self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(), img["sha256"], c)

    def test_creditos_tiene_entrada_de_las_52(self):
        for c in PROV:
            img = self.por_id[self.cat["territorios"]["provincia:" + c]]
            fila = next((r for r in self.cred.split("<tr>") if img["origen_url"] in r), None)
            self.assertIsNotNone(fila, f"créditos sin la foto de la provincia {c}")
            for campo in ("autor", "licencia", "licencia_url"):
                self.assertIn(img[campo].replace("&", "&amp;"), fila, f"{c}: falta {campo}")

    def test_panel_con_foto_sin_creditos_y_pie_enlaza_creditos(self):
        html = (V4 / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="territory-gallery"', html)
        self.assertIn('src="../v2/galeria/galeria.js"', html)
        panel = html[html.index('id="territory-gallery"'):html.index("</section>", html.index('id="territory-gallery"'))]
        self.assertNotRegex(panel, r"(?i)cr[eé]ditos|licencia|foto:")
        pie = html[html.index('<footer class="footer v4-footer"'):]  # el pie común no lleva enlaces: el de créditos va justo debajo
        self.assertRegex(pie, r'</footer>\s*<p[^>]*><a href="\.\./v2/galeria/creditos\.html">Créditos de las imágenes</a></p>')
        js = (V4 / "explorar.js").read_text(encoding="utf-8")
        self.assertRegex(js, r"DDDGaleria\.render\(.*sinCreditos:true")


if __name__ == "__main__":
    unittest.main()
