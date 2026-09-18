from pathlib import Path
import json
import unittest

import yaml

from ddd_core.electoral_contract import load_election_contract


ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml"
CONTRACT = ROOT / "territorios/castilla_y_leon/config/elecciones/castilla_y_leon_cortes_2026.json"
RECON = ROOT / "territorios/castilla_y_leon/evidencia/reconciliacion_secciones_2025_2026.json"


class CastillaLeonElectoral2026(unittest.TestCase):
    def test_m07_m08_are_declared_without_changing_m01_m06_inputs(self):
        cfg = yaml.safe_load(PARAMS.read_text(encoding="utf-8"))
        self.assertEqual(cfg["meta"]["contract_level"], "production_m01_m06")
        m07 = cfg["modulos"]["modulo_07_agregar_resultados_electorales"]
        m08 = cfg["modulos"]["modulo_08_integrar_resultados"]
        self.assertEqual(m07["election_contract"], "territorios/castilla_y_leon/config/elecciones/castilla_y_leon_cortes_2026.json")
        self.assertEqual(m07["section_id_field"], "CUSEC_KEY")
        self.assertEqual(m07["district_field"], "district_id")
        self.assertIn("m06_distritos.geojson.zip", m08["in_district_geojson"])

    def test_contract_and_frozen_source_are_verifiable(self):
        contract, dictionary = load_election_contract(
            CONTRACT,
            project_root=ROOT,
            expected_territory_id="castilla_y_leon",
        )
        self.assertEqual(contract["election_id"], "castilla_y_leon_cortes_2026-03-15")
        self.assertTrue(contract["boundary_independence"])
        self.assertEqual(len(contract["sources"]), 1)
        self.assertEqual(contract["sources"][0]["adapter"]["kind"], "long_csv")
        self.assertEqual(contract["reconciliation"]["policy"], "fail_unless_declared")

    def test_reconciliation_inventory_is_explicit(self):
        data = json.loads(RECON.read_text(encoding="utf-8"))
        self.assertEqual(data["electoral_sections"], 3528)
        self.assertEqual(data["m06_sections"], 3506)
        self.assertEqual(data["intersection"], 3504)
        self.assertEqual(len(data["electoral_only"]), 24)
        self.assertEqual(len(data["m06_only"]), 2)
        self.assertEqual(data["electoral_only_total_votes"], 15656)


if __name__ == "__main__":
    unittest.main()
