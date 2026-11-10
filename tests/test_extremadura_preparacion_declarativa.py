from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
from tests._estados_vivos import ESTADOS_PREPARADO  # noqa: E402


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
        self.assertIn(row["status"], ESTADOS_PREPARADO)
        self.assertEqual(self.params["meta"]["production_authorization"], "AUTHORIZED")
        self.assertIn(self.params["meta"]["status"], ESTADOS_PREPARADO)
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


    def test_m02_uses_original_administrative_fields_before_internal_partitioning(self):
        m02 = (ROOT / "modulos/02_construir_adyacencias.py").read_text(encoding="utf-8")
        self.assertIn('validation.get("municipality_field", "CUMUN")', m02)
        self.assertEqual(self.params["validation"]["municipality_field"], "CUMUN")
        self.assertEqual(self.params["modulos"]["modulo_04_generar_semillas"]["municipality_field"], "M04_PARTITION_UNIT")
        self.assertNotIn("require_zero_outside_tolerance_after_m05", self.params["validation"])

    def test_validator_applies_discipline_to_declared_internal_units(self):
        validator = (ROOT / "herramientas/validar_ejecucion.py").read_text(encoding="utf-8")
        self.assertIn("municipality_discipline_field", validator)
        self.assertIn("connected_internal_units", validator)
        self.assertIn("partition_unit_field", validator)

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


    def test_active_titles_and_statuses_use_preparacion(self):
        params_text = self.params_path.read_text(encoding="utf-8")
        readiness_text = self.readiness_path.read_text(encoding="utf-8")
        catalogue_text = (ROOT / "configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8")
        for text in (params_text, readiness_text, catalogue_text):
            title = re.search(r"(?mi)^#\s*NOMBRE(?: DE VERSIÓN)?:\s*(.+)$", text)
            if title:
                self.assertIn("Preparación de Extremadura", title.group(1))
                self.assertNotIn("preindustrial", title.group(1).lower())
        self.assertIn(self.params["meta"]["status"], ESTADOS_PREPARADO)
        row = next(row for row in self.catalog["territories"] if row["territory_id"] == "extremadura")
        self.assertIn(row["status"], ESTADOS_PREPARADO)

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
