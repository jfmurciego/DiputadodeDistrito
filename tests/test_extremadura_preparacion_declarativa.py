from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ExtremaduraDeclarativeReadiness(unittest.TestCase):
    def setUp(self):
        self.catalog = yaml.safe_load((ROOT / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))
        self.params = yaml.safe_load((ROOT / "territorios/extremadura/config/extremadura_2025.yaml").read_text(encoding="utf-8"))
        self.sources = yaml.safe_load((ROOT / "territorios/extremadura/config/fuentes_oficiales.yaml").read_text(encoding="utf-8"))
        self.readiness = yaml.safe_load((ROOT / "territorios/extremadura/config/preparacion_proceso_completo.yaml").read_text(encoding="utf-8"))

    def test_extremadura_is_recognized_without_execution(self):
        rows = {row["territory_id"]: row for row in self.catalog["territories"]}
        self.assertIn("extremadura", rows)
        row = rows["extremadura"]
        self.assertEqual(row["province_codes"], ["06", "10"])
        self.assertEqual(row["k_districts"], 65)
        self.assertEqual(row["production_authorization"], "BLOCKED")
        self.assertEqual(self.params["meta"]["production_authorization"], "BLOCKED")
        self.assertTrue(self.readiness["execution_forbidden_in_this_package"])
        self.assertFalse(self.readiness["decision"]["may_execute_territory"])

    def test_sources_and_m01_m03_are_prepared_by_configuration(self):
        self.assertEqual(self.sources["territory"]["id"], "extremadura")
        self.assertEqual([row["code"] for row in self.sources["territory"]["territorial_codes"]], ["06", "10"])
        steps = self.readiness["business_steps"]
        self.assertTrue(steps["official_sources"]["ready"])
        self.assertTrue(steps["territorial_base_and_population"]["ready"])
        self.assertTrue(steps["adjacency_and_graph"]["ready"])
        self.assertEqual(steps["territorial_base_and_population"]["facts"]["expected_sections"], 964)
        self.assertEqual(steps["territorial_base_and_population"]["facts"]["expected_population_2025"], 1053345)
        policy = steps["adjacency_and_graph"]["topology_policy"]
        self.assertEqual(policy["topology_mode"], "land")
        self.assertGreater(policy["min_shared_border_m"], 0)
        self.assertEqual(len(policy["declared_bridges"]), 2)
        self.assertTrue(all(bridge.get("admin_scope") == "municipality:06044" for bridge in policy["declared_bridges"]))

    def test_remaining_blocks_are_explicit_and_fail_closed(self):
        steps = self.readiness["business_steps"]
        self.assertFalse(steps["district_creation_and_balance"]["ready"])
        self.assertEqual(steps["district_creation_and_balance"]["remaining_blocker"]["type"], "COMMON_CAPABILITY_REQUIRED")
        self.assertFalse(steps["geographic_control"]["ready"])
        self.assertEqual(steps["geographic_control"]["remaining_blocker"]["type"], "UPSTREAM_BLOCK")
        self.assertFalse(steps["electoral_results"]["ready"])
        self.assertEqual(steps["electoral_results"]["remaining_blocker"]["type"], "DATA_AND_CONTRACT_REQUIRED")
        self.assertFalse(steps["maps_generation_and_publication"]["ready"])
        self.assertTrue(steps["maps_generation_and_publication"]["common_capability_available"])
        self.assertEqual(self.readiness["decision"]["readiness"], "BLOCKED")

    def test_no_territorial_exception_is_smuggled_into_common_pipeline(self):
        block = self.readiness["business_steps"]["district_creation_and_balance"]["remaining_blocker"]
        self.assertEqual(block["capability"], "declarative_internal_partition_preprocessor")
        self.assertIn("no se incorpora una excepción territorial", block["detail"])
        electoral = self.readiness["business_steps"]["electoral_results"]["remaining_blocker"]["detail"]
        self.assertIn("No se inventa", electoral)


if __name__ == "__main__":
    unittest.main()
