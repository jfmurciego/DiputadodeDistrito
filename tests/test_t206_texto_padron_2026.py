"""T-206 (D-69): el texto público del padrón 2026 está en la web (V2) y en el visor V3, palabra por palabra."""
import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LITERAL = ("Los distritos de las generales de 2026 están trazados con el padrón y el seccionado de 2023; "
           "se actualizarán con el padrón de 2025.")


class TextoPadron2026(unittest.TestCase):
    def test_textos_web_lleva_el_literal(self):
        md = (RAIZ / "web" / "textos.md").read_text(encoding="utf-8")
        m = re.search(r"^## padron2026\n(?:<!--.*?-->\n)?(.*?)(?=\n## |\Z)", md, re.S | re.M)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1).strip(), LITERAL)

    def test_web_v2_tiene_el_hueco(self):
        self.assertIn('data-k="padron2026"', (RAIZ / "visor/v2/index.html").read_text(encoding="utf-8"))
        self.assertIn("padron2026:", (RAIZ / "visor/v2/v2.js").read_text(encoding="utf-8"))

    def test_visor_v3_lleva_el_literal(self):
        html = (RAIZ / "visor/v3/index.html").read_text(encoding="utf-8")
        self.assertIn(">" + LITERAL + "</p>", html)


if __name__ == "__main__":
    unittest.main()
