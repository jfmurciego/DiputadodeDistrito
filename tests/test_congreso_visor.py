"""Regression for analytical (non-certified) Congress viewer integration."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CongressViewerContractTests(unittest.TestCase):
    def test_both_provinces_auto_load_with_explicit_scope(self):
        html = (ROOT / "visor/congreso/index.html").read_text(encoding="utf-8")
        script = (ROOT / "visor/congreso/congreso.js").read_text(encoding="utf-8")
        for expected in ("value=\"24\"", "value=\"10\"", "PILOTO ANALÍTICO", "NO CERTIFICADO"):
            self.assertIn(expected, html)
        for expected in ('"24":{name:"León"', '"10":{name:"Cáceres"',
                         'fetch("data/"+cpro', 'municipios-divididos.geojson',
                         'NOT_CERTIFIED', "sourceDetails.textContent",
                         "detail.textContent"):
            self.assertIn(expected, script)
        self.assertNotIn('innerHTML=', script)

    def test_pages_copies_congress_route_outside_certified_registry(self):
        workflow = (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8")
        home = (ROOT / "visor/index.html").read_text(encoding="utf-8")
        self.assertIn('href="congreso/"', home)
        self.assertIn("mkdir -p /tmp/site-candidate/congreso/data", workflow)
        self.assertIn("cp visor/congreso/index.html visor/congreso/congreso.js visor/congreso/styles.css /tmp/site-candidate/congreso/", workflow)
        self.assertIn("congreso/data/24.geojson", workflow)
        self.assertIn("congreso/data/10.geojson", workflow)
        self.assertIn("congreso/data/10-municipios-divididos.geojson", workflow)
        self.assertNotIn("congreso/data", (ROOT / "orchestracion/publicaciones_visor.json").read_text(encoding="utf-8"))

    def test_pilot_preflight_packs_standalone_viewer_without_public_deploy(self):
        workflow = (ROOT / ".github/workflows/congreso-piloto-leon.yml").read_text(encoding="utf-8")
        self.assertIn("N08_STANDALONE_VIEWER_READY", workflow)
        self.assertIn("piloto-autonomo.html", workflow)
        self.assertIn("10-split", workflow)
        self.assertNotIn("actions/deploy-pages", workflow)


if __name__ == "__main__":
    unittest.main()
