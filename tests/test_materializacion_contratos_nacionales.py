from pathlib import Path
import json
import tempfile
import unittest

import pandas as pd
import yaml

from herramientas.materializar_contrato_territorial import materialize
from herramientas.preparar_unidades_internas import main as prepare_internal_units_main

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "configuracion" / "politica_materializacion_territorial.yaml"
CATALOG = ROOT / "configuracion" / "catalogo_preparacion.yaml"


def population_package(root: Path, rows):
    package = root / "population"
    package.mkdir(parents=True, exist_ok=True)
    path = package / "padron.csv"
    pd.DataFrame(rows, columns=["CUSEC", "population"]).to_csv(path, index=False, sep=";")
    return package


class NationalGenerationMaterializationTests(unittest.TestCase):
    def test_every_non_insular_territory_materializes_without_manual_promotion(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id, entry in policy["territories"].items():
            if territory_id in {"illes_balears", "canarias"}:
                continue
            td = tempfile.TemporaryDirectory()
            try:
                root = Path(td.name)
                provinces = [str(p).zfill(2) for p in entry["province_codes"]]
                rows = [(f"{province}00101001", 100000 + index * 1000) for index, province in enumerate(provinces)]
                package = population_package(root, rows)
                result = materialize(root, territory_id, "2025", package)
                self.assertEqual(result["status"], "READY", territory_id)
                self.assertEqual(result["k"], int(entry["k"]), territory_id)
                cfg = yaml.safe_load((root / result["contract_path"]).read_text(encoding="utf-8"))
                self.assertEqual(cfg["meta"]["production_authorization"], "AUTHORIZED", territory_id)
                self.assertEqual(sum(cfg["validation"]["province_districts"].values()), int(entry["k"]), territory_id)
            finally:
                td.cleanup()

    def test_archipelagos_remain_without_electoral_readiness_in_live_catalog(self):
        catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
        rows = {row["territory_id"]: row for row in catalog["territories"]}
        for territory_id in ("illes_balears", "canarias"):
            state = rows[territory_id]["editions"]["2025"]
            self.assertEqual("READY", state["preparation_status"])
            self.assertTrue(state["territorial_sources_prepared"])
            self.assertTrue(state["territorial_contract_complete"])
            self.assertEqual("AUTHORIZED", state["production_authorization"])
            self.assertTrue(state["contract_path"])
            self.assertTrue(state["territorial_source_declaration"])
            self.assertFalse(state["electoral_source_prepared"])
            self.assertFalse(state["electoral_product_available"])
            self.assertIsNone(state["electoral_source_declaration"])

    def test_archipelago_policy_separates_institutional_k_from_ddd_apportionment(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id, expected_k in (("illes_balears", 59), ("canarias", 70)):
            entry = policy["territories"][territory_id]
            self.assertEqual(expected_k, entry["k"])
            self.assertEqual("norma", entry["k_source"])
            self.assertEqual("institutional_chamber_size_only", entry["k_reference_scope"])
            self.assertEqual("ddd_design_policy", entry["apportionment_source"])
            self.assertFalse(entry["legal_apportionment_reused"])
            self.assertIn("Contexto solamente", entry["legal_context"]["note"])
        self.assertEqual("island_components", policy["territories"]["illes_balears"]["partition_policy"]["mode"])
        self.assertEqual("island_components", policy["territories"]["canarias"]["partition_policy"]["mode"])

    def test_archipelago_registry_is_explicit_and_has_no_marine_edges(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id in ("illes_balears", "canarias"):
            registry_path = ROOT / policy["territories"][territory_id]["partition_policy"]["registry"]
            registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
            self.assertEqual("island_components", registry["partition_policy"])
            self.assertEqual([], registry["marine_bridges"])
            self.assertGreater(len(registry["components"]), 1)

    def test_hamilton_conserves_k(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id in ("illes_balears", "canarias"):
            entry = policy["territories"][territory_id]
            registry = yaml.safe_load((ROOT / entry["partition_policy"]["registry"]).read_text(encoding="utf-8"))
            total = sum(int(component["k"]) for component in registry["components"])
            self.assertEqual(int(entry["k"]), total)

    def test_ungoverned_archipelago_floor_exception_blocks(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        entry = policy["territories"]["illes_balears"]
        registry = yaml.safe_load((ROOT / entry["partition_policy"]["registry"]).read_text(encoding="utf-8"))
        governed = [c for c in registry["components"] if c.get("population_floor_exception")]
        self.assertTrue(governed)
        broken = json.loads(json.dumps(registry))
        target = next(c for c in broken["components"] if c.get("population_floor_exception"))
        target.pop("population_floor_exception", None)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "registry.yaml"
            path.write_text(yaml.safe_dump(broken, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.assertFalse(target.get("population_floor_exception"))

    def test_materializes_asturias_without_manual_contract_work(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        entry = policy["territories"]["principado_de_asturias"]
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows = [("3300101001", 100000)]
            package = population_package(root, rows)
            result = materialize(root, "principado_de_asturias", "2025", package)
            self.assertEqual("READY", result["status"])

    def test_materializes_balearic_archipelago_with_explicit_partition_exception(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        self.assertEqual("island_components", policy["territories"]["illes_balears"]["partition_policy"]["mode"])

    def test_materializes_canary_archipelago_without_marine_bridge(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        registry = yaml.safe_load((ROOT / policy["territories"]["canarias"]["partition_policy"]["registry"]).read_text(encoding="utf-8"))
        self.assertEqual([], registry["marine_bridges"])

    def test_population_parser_accepts_semicolon_official_subset(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = population_package(root, [("2800101001", 1000)])
            self.assertTrue((package / "padron.csv").exists())

    def test_r026_component_inventories_match_partition_registry_and_ddd_audit(self):
        policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
        for territory_id in ("illes_balears", "canarias"):
            registry = yaml.safe_load((ROOT / policy["territories"][territory_id]["partition_policy"]["registry"]).read_text(encoding="utf-8"))
            self.assertGreater(len(registry["components"]), 1)
