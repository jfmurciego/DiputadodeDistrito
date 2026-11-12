"""Pruebas aisladas de la portada V2 y conservación de V1."""
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin

from herramientas.preparar_portada_v2 import preparar_portada


class PrepararPortadaV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        (self.site / "v2").mkdir()
        (self.site / "v2" / "index.html").write_text("<!doctype html>V2", encoding="utf-8")
        (self.site / "index.html").write_text(
            '<!doctype html><html><head><link rel="stylesheet" href="styles.css"></head>'
            '<body><a href="dashboard/">Dashboard operativo</a>'
            '<script src="app.js"></script></body></html>', encoding="utf-8")

    def test_v2_portada_y_v1_conservada(self):
        preparar_portada(self.site)
        self.assertIn('url=v2/', (self.site / 'index.html').read_text())
        v1 = (self.site / 'v1' / 'index.html').read_text()
        self.assertIn('<base href="../">', v1)
        self.assertIn('src="app.js"', v1)
        self.assertIn('href="dashboard/"', v1)
        self.assertEqual((self.site / 'v2' / 'index.html').read_text(), '<!doctype html>V2')
        for base in ['https://diputadodedistrito.es/v1/',
                     'https://jfmurciego.github.io/DiputadodeDistrito/v1/']:
            self.assertTrue(urljoin(urljoin(base, '../'), 'app.js').endswith('/app.js'))

    def test_no_cambiar_sitio_incompleto(self):
        (self.site / 'v2' / 'index.html').unlink()
        original = (self.site / 'index.html').read_text()
        with self.assertRaises(FileNotFoundError):
            preparar_portada(self.site)
        self.assertEqual((self.site / 'index.html').read_text(), original)

    def test_rechazar_portada_inesperada(self):
        (self.site / 'index.html').write_text('<html><head></head></html>')
        with self.assertRaises(ValueError):
            preparar_portada(self.site)


if __name__ == '__main__':
    unittest.main()
