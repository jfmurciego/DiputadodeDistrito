from __future__ import annotations

import importlib.util
import json
import re
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
        self.readiness_path = ROOT / "territorios/extremadura/config/preparacion_proceso_completo.yaml"
        self.readiness = yaml.safe_load(self.readiness_path.read_text(encoding="utf-8"))
        self.election_block = json.loads((ROOT / "territorios/extremadura/config/elecciones/bloqueo_fuente_oficial_2025.json").read_text(encoding="utf-8"))
        self.election_sources = yaml.safe_load((ROOT / "territorios/extremadura/config/elecciones/fuentes_oficiales_2025.yaml").read_text(encoding="utf-8"))

    def test_extremadura_is_recognized_without_execution(self):
        rows = {row["territory_id"]: row for row in self.catalog["territories"]}
        self.assertIn("extremadura", rows)
        row = rows["extremadura"]
        self.assertEqual(row["province_codes"], ["06", "10"])
        self.assertEqual(row["k_districts"], 65)
        self.assertEqual(row["k_source"], "norma")
        self.assertEqual(row["production_authorization"], "AUTHORIZED")
        self.assertEqual(row["status"], "generation_ready")
        self.assertEqual(self.params["meta"]["production_authorization"], "AUTHORIZED")
        self.assertEqual(self.params["meta"]["status"], "generation_ready")
        self.assertFalse(self.readiness["execution_forbidden_in_this_package"])
        self.assertTrue(self.readiness["decision"]["may_execute_territory"])

    def test_common_population_profile_and_k_provenance(self):
        contract = self.params["territory_contract"]
        validation = self.params["validation"]
        self.assertEqual(contract["k_source"], "norma")
        self.assertIn("Ley 2 de 1987", contract["k_rationale"])
        self.assertEqual(contract["limits_profile"], "standard-1.0.0")
        expected = (0.80, 1.75, 0.12)
        self.assertEqual((contract["population_floor_ratio"], contract["population_cap_ratio"], contract["target_tolerance_ratio"]), expected)
        self.assertEqual((validation["population_floor_ratio"], validation["population_cap_ratio"], validation["target_tolerance_ratio"]), expected)

    def test_common_internal_units_step_is_configuration_driven_and_visible(self):
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
        self.assertNotIn("preparar_unidades_internas.py", procedure)
        workflow = (ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("name: Preparar unidades internas", workflow)
        self.assertIn("ddd-internal-units-${{ github.run_id }}", workflow)
        self.assertIn("PREVIOUS_STAGE: M03U", workflow)

    def test_sources_and_m01_m03_are_prepared_by_configuration(self):
        self.assertEqual(self.sources["territory"]["id"], "extremadura")
        self.assertEqual([row["code"] for row in self.sources["territory"]["territorial_codes"]], ["06", "10"])
        steps = self.readiness["business_steps"]
        self.assertTrue(steps["official_sources"]["ready"])
        self.assertTrue(steps["territorial_base_and_population"]["ready"])
        self.assertTrue(steps["adjacency_and_graph"]["ready"])
        self.assertTrue(steps["internal_units_preparation"]["ready"])
        self.assertEqual(steps["internal_units_preparation"]["execution"], "visible_github_actions_job")
        self.assertEqual(steps["territorial_base_and_population"]["facts"]["expected_sections"], 964)
        self.assertEqual(steps["territorial_base_and_population"]["facts"]["expected_population_2025"], 1053345)

    def test_electoral_source_is_automatic_and_fail_closed(self):
        block = self.election_block
        self.assertEqual(block["decision"], "BLOCKED")
        self.assertFalse(block["rtve_allowed_as_substitute"])
        self.assertEqual(block["press_repository"]["access"], "credentials_required")
        self.assertFalse((ROOT / "territorios/extremadura/config/elecciones/extremadura_asamblea_2025.json").exists())
        self.assertEqual(self.params["meta"]["electoral_sources_declaration"], "territorios/extremadura/config/elecciones/fuentes_oficiales_2025.yaml")
        self.assertEqual(self.election_sources["minimum_resolution"], "section")
        forbidden = " ".join(str(x).lower() for x in self.election_sources["forbidden_substitutes"])
        self.assertIn("rtve", forbidden)
        urls = " ".join(str(s["url"]).lower() for s in self.election_sources["sources"])
        self.assertNotIn("rtve", urls)
        electoral = self.readiness["business_steps"]["electoral_results"]
        self.assertFalse(electoral["ready"])
        self.assertTrue(electoral["automated_check"])
        workflow = (ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("name: Fuente electoral oficial", workflow)
        self.assertIn("validar_paquete_electoral.py", workflow)
        self.assertIn("electoral_package_run_id", workflow)
        self.assertIn("ddd-electoral-source-${{ github.run_id }}", workflow)

    def test_active_titles_and_statuses_use_preparacion(self):
        params_text = self.params_path.read_text(encoding="utf-8")
        readiness_text = self.readiness_path.read_text(encoding="utf-8")
        catalogue_text = (ROOT / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8")
        for text in (params_text, readiness_text, catalogue_text):
            title = re.search(r"(?mi)^#\s*NOMBRE(?: DE VERSIÓN)?:\s*(.+)$", text)
            if title:
                self.assertIn("Preparación de Extremadura", title.group(1))
                self.assertNotIn("preindustrial", title.group(1).lower())
        self.assertEqual(self.params["meta"]["status"], "generation_ready")
        row = next(row for row in self.catalog["territories"] if row["territory_id"] == "extremadura")
        self.assertEqual(row["status"], "generation_ready")

    def test_remaining_blocks_are_explicit(self):
        steps = self.readiness["business_steps"]
        self.assertTrue(steps["district_creation_and_balance"]["ready"])
        self.assertTrue(steps["district_creation_and_balance"]["configuration_ready"])
        self.assertIsNone(steps["district_creation_and_balance"]["remaining_blocker"])
        self.assertFalse(steps["geographic_control"]["ready"])
        self.assertFalse(steps["maps_generation_and_publication"]["ready"])
        self.assertEqual(self.readiness["decision"]["readiness"], "READY_FOR_GENERATION")


if __name__ == "__main__":
    unittest.main()
