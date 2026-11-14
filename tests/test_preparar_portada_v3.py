"""Regresiones de la publicación y los contratos cartográficos de V3.
PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-12
ESTADO: candidato
CAMBIOS: pruebas de portada, familias electorales, seccionado y calendario.
MOTIVO: impedir falsas promesas de datos al incorporar el explorador V3.
ANTERIOR: ninguna (fichero nuevo)
"""
import json
import tempfile
import unittest
from pathlib import Path

from herramientas.preparar_portada_v2 import preparar_portada
from herramientas.preparar_portada_v3 import preparar_portada_v3

ROOT = Path(__file__).resolve().parents[1]
V3 = ROOT / "visor" / "v3"


class PortadaV3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        (self.site / "index.html").write_text(
            (ROOT / "visor" / "index.html").read_text(encoding="utf-8"), encoding="utf-8"
        )
        for name in ("v2/index.html", "v3/index.html", "v3/v3.js", "v3/v3.css",
                     "v3/calendario.json"):
            target = self.site / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("V3" if name.startswith("v3") else "V2", encoding="utf-8")

    def test_promocionar_v3_preserva_v1_v2_y_query_hash(self):
        preparar_portada(self.site)
        preparar_portada_v3(self.site)
        root = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn('url=v3/', root)
        self.assertIn('new URL("v3/" + window.location.search + window.location.hash', root)
        self.assertIn('href="v3/"', root)
        self.assertNotIn('url=v2/', root)
        self.assertTrue((self.site / "v1" / "index.html").exists())
        self.assertEqual((self.site / "v2" / "index.html").read_text(), "V2")
        self.assertEqual((self.site / "v3" / "index.html").read_text(), "V3")

    def test_falla_cerrado_si_falta_v3(self):
        preparar_portada(self.site)
        before = (self.site / "index.html").read_bytes()
        (self.site / "v3" / "v3.js").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "v3/v3.js"):
            preparar_portada_v3(self.site)
        self.assertEqual((self.site / "index.html").read_bytes(), before)

    def test_falla_cerrado_si_la_portada_no_es_v2(self):
        preparar_portada(self.site)
        (self.site / "index.html").write_text("<html>portada inesperada</html>", encoding="utf-8")
        before = (self.site / "index.html").read_bytes()
        with self.assertRaisesRegex(ValueError, "V2"):
            preparar_portada_v3(self.site)
        self.assertEqual((self.site / "index.html").read_bytes(), before)

    def test_workflow_copia_v3_y_promociona_despues_de_v2(self):
        wf = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        build = wf.index("- name: Construir sitio candidato completo")
        v2 = wf.index("- name: Portada pública V2 y conservación V1")
        v3 = wf.index("- name: Promocionar portada pública V3")
        valid = wf.index("- name: Validar sitio candidato completo")
        self.assertLess(build, v2)
        self.assertLess(v2, v3)
        self.assertLess(v3, valid)
        self.assertIn("cp visor/v3/index.html visor/v3/v3.css visor/v3/v3.js visor/v3/calendario.json", wf)
        self.assertIn("node --check /tmp/site-candidate/v3/v3.js", wf)
        self.assertEqual(wf.count("--site /tmp/site-candidate"), 1)

    def test_ui_v3_se_valida_en_runner_con_node(self):
        # El contenedor reproducible de la suite Python no incluye Node.
        # El guardián de CI ejecuta la prueba interactiva en ubuntu-24.04.
        workflow = (ROOT / ".github/workflows/pruebas-plataforma.yml").read_text(encoding="utf-8")
        self.assertIn("node --check visor/v3/v3.js", workflow)
        self.assertIn("node tests/test_visor_v3_ui.js", workflow)

    def test_paneles_y_selectores_completos(self):
        html = (V3 / "index.html").read_text(encoding="utf-8")
        for identifier in ('id="scope"', 'id="system"', 'id="view"',
                           'id="elections"', 'id="election-region"',
                           'id="level"', 'id="layer"', 'id="search"',
                           'id="map"', 'id="legend"'):
            self.assertIn(identifier, html)
        for option in ('data-value="nacional"', 'data-value="autonomico"',
                       'data-value="proporcional"', 'data-value="mayoritario"',
                       'data-value="territorial"', 'data-value="electoral"',
                       'value="seccion"'):
            self.assertIn(option, html)

    def test_paleta_electoral_inequivoca_y_capas_sin_inventos(self):
        js = (V3 / "v3.js").read_text(encoding="utf-8")
        for p, color in (('PP', '#1d6fb8'), ('PSOE', '#d32b2b'),
                         ('VOX', '#5fa335'), ('SUMAR', '#cf2a7b'),
                         ('PODEMOS', '#8750b5')):
            self.assertIn(p + ':"' + color + '"', js)
        self.assertIn('winnerOfDistrict', js)
        self.assertIn("No se atribuyen resultados electorales", (V3 / "index.html").read_text(encoding="utf-8"))
        self.assertIn('BASE.secciones+cod+".geojson"', js)
        self.assertIn('e.data.geojson.ruta', js)
        self.assertIn('product.viewer_path', js)

    def test_calendario_autonomico_procede_de_software_de_fuentes(self):
        calendar = json.loads((V3 / "calendario.json").read_text(encoding="utf-8"))
        self.assertIn("madrid", calendar)
        self.assertIn("galicia", calendar)
        # Nombres provinciales del INE simplificados (Asturias/Baleares/Navarra).
        js = (V3 / "v3.js").read_text(encoding="utf-8")
        for alias, territory in (
            ("Asturias", "principado_de_asturias"),
            ("Baleares", "illes_balears"),
            ("Navarra", "comunidad_foral_de_navarra"),
        ):
            self.assertIn(f'"{alias}":"{territory}"', js)
        for region, dates in calendar.items():
            for code, label in dates:
                self.assertRegex(code, r"^\d{6}$")
                self.assertTrue((ROOT / "datos/resultados/historico/autonomicas" / region / code).is_dir(),
                                f"No hay fuente histórica para {region}/{code}")


if __name__ == "__main__":
    unittest.main()
