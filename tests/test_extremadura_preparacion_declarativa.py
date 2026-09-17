from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_common_preparer():
    path = ROOT / "herramientas/preparar_unidades_internas.py"
    spec = importlib.util.spec_from_file_location("ddd_internal_units_preparer", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ExtremaduraDeclarativeReadiness(unittest.TestCase):
    def setUp(self):
        self.catalog = yaml.safe_load((ROOT / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))
        self.params_path = ROOT / "territorios/extremadura/config/extremadura_2025.yaml"
        self.params = yaml.safe_load(self.params_path.read_text(encoding="utf-8"))
        self.sources = yaml.safe_load((ROOT / "territorios/extremadura/config/fuentes_oficiales.yaml").read_text(encoding="utf-8"))
        self.readiness = yaml.safe_load((ROOT / "territorios/extremadura/config/preparacion_proceso_completo.yaml").read_text(encoding="utf-8"))
        self.election_block = json.loads((ROOT / "territorios/extremadura/config/elecciones/bloqueo_fuente_oficial_2025.json").read_text(encoding="utf-8"))

    def test_extremadura_is_recognized_without_execution(self):
        rows = {row["territory_id"]: row for row in self.catalog["territories"]}
        self.assertIn("extremadura", rows)
        row = rows["extremadura"]
        self.assertEqual(row["province_codes"], ["06", "10"])
        self.assertEqual(row["k_districts"], 65)
        self.assertEqual(row["k_source"], "norma")
        self.assertEqual(row["production_authorization"], "BLOCKED")
        self.assertEqual(self.params["meta"]["production_authorization"], "BLOCKED")
        self.assertTrue(self.readiness["execution_forbidden_in_this_package"])
        self.assertFalse(self.readiness["decision"]["may_execute_territory"])

    def test_common_population_profile_and_k_provenance(self):
        contract = self.params["territory_contract"]
        validation = self.params["validation"]
        self.assertEqual(contract["k_source"], "norma")
        self.assertIn("Ley 2/1987", contract["k_rationale"])
        self.assertEqual(contract["limits_profile"], "standard-1.0.0")
        expected = (0.80, 1.75, 0.12)
        self.assertEqual((contract["population_floor_ratio"], contract["population_cap_ratio"], contract["target_tolerance_ratio"]), expected)
        self.assertEqual((validation["population_floor_ratio"], validation["population_cap_ratio"], validation["target_tolerance_ratio"]), expected)

    def test_common_internal_units_step_is_configuration_driven(self):
        preparer = load_common_preparer()
        command = preparer.build_command(self.params_path, "synthetic-run")
        self.assertIsNotNone(command)
        joined = " ".join(command)
        self.assertIn("construir_unidades_internas_m04.py", joined)
        self.assertIn("M04_PARTITION_UNIT", joined)
        self.assertIn("extremadura_2025_m03_unidades_internas.geojson", joined)
        active = self.params_path.read_text(encoding="utf-8").lower()
        self.assertNotIn("c020", active)
        common_code = (ROOT / "herramientas/preparar_unidades_internas.py").read_text(encoding="utf-8").lower()
        for forbidden in ("extremadura", "badajoz", "cáceres", "caceres"):
            self.assertNotIn(forbidden, common_code)
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn("preparar_unidades_internas.py", procedure)

    def test_sources_and_m01_m03_are_prepared_by_configuration(self):
        self.assertEqual(self.sources["territory"]["id"], "extremadura")
        self.assertEqual([row["code"] for row in self.sources["territory"]["territorial_codes"]], ["06", "10"])
        steps = self.readiness["business_steps"]
        self.assertTrue(steps["official_sources"]["ready"])
        self.assertTrue(steps["territorial_base_and_population"]["ready"])
        self.assertTrue(steps["adjacency_and_graph"]["ready"])
        self.assertTrue(steps["internal_units_preparation"]["ready"])
        self.assertEqual(steps["territorial_base_and_population"]["facts"]["expected_sections"], 964)
        self.assertEqual(steps["territorial_base_and_population"]["facts"]["expected_population_2025"], 1053345)

    def test_electoral_contract_remains_fail_closed_without_public_official_granular_file(self):
        block = self.election_block
        self.assertEqual(block["status"], "BLOCKED_NO_PUBLIC_OFFICIAL_SECTION_FILE")
        self.assertEqual(block["decision"], "BLOCKED")
        self.assertFalse(block["contract_created"])
        self.assertFalse(block["party_dictionary_created"])
        self.assertFalse(block["reconciliation_created"])
        self.assertFalse(block["rtve_allowed_as_substitute"])
        self.assertEqual(block["press_repository"]["access"], "credentials_required")
        self.assertFalse((ROOT / "territorios/extremadura/config/elecciones/extremadura_asamblea_2025.json").exists())
        electoral = self.readiness["business_steps"]["electoral_results"]
        self.assertFalse(electoral["ready"])
        self.assertEqual(electoral["remaining_blocker"]["type"], "OFFICIAL_DISAGGREGATED_FILE_NOT_PUBLICLY_LOCATED")
        self.assertIn("RTVE", electoral["remaining_blocker"]["detail"])

    def test_remaining_blocks_are_explicit(self):
        steps = self.readiness["business_steps"]
        self.assertFalse(steps["district_creation_and_balance"]["ready"])
        self.assertTrue(steps["district_creation_and_balance"]["configuration_ready"])
        self.assertEqual(steps["district_creation_and_balance"]["remaining_blocker"]["type"], "EXECUTION_AND_CERTIFICATION_REQUIRED")
        self.assertFalse(steps["geographic_control"]["ready"])
        self.assertFalse(steps["maps_generation_and_publication"]["ready"])
        self.assertEqual(self.readiness["decision"]["readiness"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
