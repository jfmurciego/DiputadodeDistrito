"""Contrato ligero de simbología funcional del visor territorial/electoral."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "visor" / "app.js"
INDEX = ROOT / "visor" / "index.html"


class ViewerLegendContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = APP.read_text(encoding="utf-8")
        cls.index = INDEX.read_text(encoding="utf-8")

    def test_territorial_uses_relative_deviation_and_five_diverging_bins(self):
        self.assertIn('p.kind==="territorial"', self.app)
        self.assertIn('["get","relative_deviation"]', self.app)
        for threshold in ("-0.10", "-0.05", "0.05", "0.10"):
            self.assertIn(threshold, self.app)
        self.assertIn("Equilibrio de población", self.app)

    def test_electoral_uses_dynamic_winner_party_legend(self):
        self.assertIn('p.kind==="electoral"', self.app)
        self.assertIn("function partyEntries(data)", self.app)
        self.assertIn('properties?.winner_party', self.app)
        self.assertIn('["get","winner_party"]', self.app)
        self.assertNotIn("const ARAGON_PARTIES", self.app)

    def test_legend_is_view_specific(self):
        self.assertIn('id="legend"', self.index)
        self.assertIn("function renderLegend(p,data)", self.app)
        self.assertIn('p.kind==="territorial"', self.app)
        self.assertIn("Partido más votado", self.app)
        self.assertIn("legend.replaceChildren()", self.app)

    def test_electoral_popup_reads_functional_fields(self):
        for field in ("winner_party", "winner_votes", "winner_share", "total_votes"):
            self.assertIn(field, self.app)
        self.assertIn("Porcentaje", self.app)
        self.assertIn("Votos del ganador", self.app)
        self.assertIn("Votos totales", self.app)

    def test_navigation_and_public_contracts_remain_without_internal_status_codes(self):
        for token in (
            "map.fitBounds",
            'resultSelect.addEventListener("change"',
            "maplibregl.Popup",
            "Territorial y censal",
            "Electoral · elecciones",
        ):
            self.assertIn(token, self.app)
        for internal in (
            "CERTIFIED_WITH_GOVERNED_EXCEPTIONS",
            "technical_status",
            "publication_status",
            "geometric_status",
        ):
            self.assertNotIn(internal, self.app)


if __name__ == "__main__":
    unittest.main()
