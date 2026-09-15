"""Contrato ligero de simbología y popup del visor M06/M08."""
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

    def test_m06_uses_relative_deviation_and_five_diverging_bins(self):
        self.assertIn('spec.kind==="canonical_m06"', self.app)
        self.assertIn('["get","relative_deviation"]', self.app)
        for threshold in ("-0.10", "-0.05", "0.05", "0.10"):
            self.assertIn(threshold, self.app)
        self.assertIn("Desviación respecto a la población objetivo", self.app)

    def test_m08_uses_dynamic_winner_party_legend(self):
        self.assertIn('spec.kind==="canonical_m08"', self.app)
        self.assertIn("function partyEntries(data)", self.app)
        self.assertIn('properties?.winner_party', self.app)
        self.assertIn('["get","winner_party"]', self.app)
        self.assertNotIn('const ARAGON_PARTIES', self.app)
        self.assertNotIn('["PP","PSOE"]', self.app)

    def test_legend_is_result_specific(self):
        self.assertIn('id="legend"', self.index)
        self.assertIn("function renderLegend(spec,data)", self.app)
        self.assertIn('if(spec.kind==="canonical_m06")', self.app)
        self.assertIn('else if(spec.kind==="canonical_m08")', self.app)
        self.assertIn("legend.replaceChildren();legend.hidden=true", self.app)

    def test_m08_popup_reads_four_electoral_fields(self):
        for field in ("winner_party", "winner_votes", "winner_share", "total_votes"):
            self.assertIn(f'["{field}"]', self.app)
        self.assertIn("minimumFractionDigits:2", self.app)
        self.assertIn("maximumFractionDigits:2", self.app)

    def test_existing_status_and_navigation_contracts_remain(self):
        for token in (
            "map.fitBounds",
            "CERTIFIED_WITH_GOVERNED_EXCEPTIONS",
            'spec.publication_status||"BLOCKED"',
            'resultSelect.addEventListener("change"',
            "maplibregl.Popup",
        ):
            self.assertIn(token, self.app)


if __name__ == "__main__":
    unittest.main()
