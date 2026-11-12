"""Regresiones de la portada V2 y las rutas relativas de V1."""
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urljoin

from herramientas.preparar_portada_v2 import preparar_portada

ROOT = Path(__file__).resolve().parents[1]
ORIGEN_V1 = ROOT / "visor" / "index.html"


class PrepararPortadaV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        (self.site / "v2").mkdir()
        (self.site / "v2" / "index.html").write_text("<!doctype html>V2", encoding="utf-8")
        self.original = ORIGEN_V1.read_text(encoding="utf-8")
        (self.site / "index.html").write_text(self.original, encoding="utf-8")

    def test_v2_portada_y_v1_original_con_base(self):
        preparar_portada(self.site)
        portada = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn('url=v2/', portada)
        self.assertIn('window.location.replace(', portada)
        self.assertIn('window.location.search + window.location.hash', portada)
        self.assertIn('<a href="v2/">', portada)
        v1 = (self.site / "v1" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(v1.replace('<head>\n  <base href="../">', '<head>', 1), self.original)
        self.assertEqual((self.site / "v2" / "index.html").read_text(), "<!doctype html>V2")
        self.assertTrue((self.site / "v1" / "index.html").is_file())

    def test_rutas_de_v1_funcionan_en_dominio_y_pages(self):
        preparar_portada(self.site)
        v1 = (self.site / "v1" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<base href="../">', v1)
        for relative in ['styles.css', 'app.js', 'escenarios.js', 'dashboard/']:
            self.assertIn(relative, v1)
            for site_root in [
                "https://diputadodedistrito.es/",
                "https://jfmurciego.github.io/DiputadodeDistrito/",
            ]:
                v1_url = urljoin(site_root, "v1/")
                effective_base = urljoin(v1_url, "../")
                self.assertEqual(urljoin(effective_base, relative), urljoin(site_root, relative))

    def test_congreso_opt_in_sigue_accesible_desde_v1(self):
        orig = self.original.replace(
            '<a class="dashboard-link" href="dashboard/">Dashboard operativo</a>',
            '<a class="dashboard-link" href="dashboard/">Dashboard operativo</a>'
            ' <a class="dashboard-link" href="congreso/">Congreso piloto</a>', 1
        )
        (self.site / "index.html").write_text(orig, encoding="utf-8")
        preparar_portada(self.site)
        v1 = (self.site / "v1" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="congreso/"', v1)
        self.assertNotIn('href="congreso/"', (self.site / "index.html").read_text(encoding="utf-8"))

    def test_flujo_p50_promueve_v2_despues_del_opt_in_y_antes_de_validar(self):
        workflow = (ROOT / ".github" / "workflows" / "_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        congreso = workflow.index("- name: Preparar visor analítico Congreso opt-in")
        promocion = workflow.index("- name: Portada pública V2 y conservación V1")
        validacion = workflow.index("- name: Validar sitio candidato completo")
        self.assertLess(congreso, promocion)
        self.assertLess(promocion, validacion)
        self.assertEqual(workflow.count("python herramientas/preparar_portada_v2.py"), 1)
        self.assertIn("python herramientas/preparar_portada_v2.py --site=/tmp/site-candidate", workflow)
        self.assertEqual(workflow.count("--site /tmp/site-candidate"), 1)
        self.assertIn("grep -q 'url=v2/' /tmp/site-candidate/index.html", workflow)
        self.assertIn('test -s /tmp/site-candidate/v1/index.html', workflow)
        self.assertIn("grep -q 'href=\"congreso/\"' /tmp/site-candidate/v1/index.html", workflow)

    def test_no_cambiar_sitio_incompleto(self):
        (self.site / "v2" / "index.html").unlink()
        with self.assertRaises(FileNotFoundError):
            preparar_portada(self.site)
        self.assertEqual((self.site / "index.html").read_text(encoding="utf-8"), self.original)

    def test_rechazar_portada_inesperada(self):
        (self.site / "index.html").write_text("<html><head></head></html>", encoding="utf-8")
        with self.assertRaises(ValueError):
            preparar_portada(self.site)


if __name__ == "__main__":
    unittest.main()
