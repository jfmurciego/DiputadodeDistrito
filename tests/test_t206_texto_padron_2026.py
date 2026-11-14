"""T-206 (D-69): el texto público del padrón 2026 está en la web (V2) y en el visor V3, palabra por palabra."""
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LITERAL = ("Los distritos de las generales de 2026 están trazados con el padrón y el seccionado de 2023; "
           "se actualizarán con el padrón de 2025.")


class TextoPadron2026(unittest.TestCase):
    def test_web_v2_ya_trae_la_nota_sin_duplicar(self):
        html = (RAIZ / "visor/v2/index.html").read_text(encoding="utf-8")
        js = (RAIZ / "visor/v2/v2.js").read_text(encoding="utf-8")
        self.assertEqual(js.count(LITERAL), 1)
        self.assertNotIn("padron2026", html + js)

    def test_visor_v3_lleva_el_literal(self):
        html = (RAIZ / "visor/v3/index.html").read_text(encoding="utf-8")
        self.assertIn('id="padron-note" class="election-note" hidden>' + LITERAL + "</p>", html)
        self.assertIn('startsWith("2026")', (RAIZ / "visor/v3/v3.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
