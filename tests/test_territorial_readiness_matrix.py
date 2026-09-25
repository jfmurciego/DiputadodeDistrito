from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import yaml

from herramientas.resolver_ejecucion_completa import build_plan, generation_enablement

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"


class TerritorialReadinessMatrixRegression(unittest.TestCase):
    def test_catalog_matrix_is_collected_and_enforces_current_generation_gate(self):
        catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
        pass_ids = {
            "andalucia", "aragon", "principado_de_asturias", "cantabria",
            "castilla_la_mancha", "castilla_y_leon", "extremadura", "galicia",
            "comunidad_foral_de_navarra", "pais_vasco", "la_rioja",
        }
        blocked_ready_ids = {"cataluna", "comunidad_valenciana", "madrid"}
        pending_ids = {"illes_balears", "canarias", "region_de_murcia", "ceuta", "melilla"}
        seen = set()

        for row in catalog["territories"]:
            territory_id = row["territory_id"]
            state = row["editions"]["2025"]
            seen.add(territory_id)
            with self.subTest(territory=territory_id):
                if territory_id in pass_ids:
                    plan = build_plan(
                        territory=row["name"], edition="2025", execution_mode="reuse",
                        catalog=CATALOG, root_dir=ROOT, force_selected_algorithm=True,
                    )
                    self.assertTrue(plan["generation_gate"]["allowed"])
                    self.assertTrue(plan["run_generate"])
                elif territory_id in blocked_ready_ids:
                    with self.assertRaisesRegex(ValueError, "GENERATION_CONTRACT_BLOCK"):
                        build_plan(
                            territory=row["name"], edition="2025", execution_mode="reuse",
                            catalog=CATALOG, root_dir=ROOT, force_selected_algorithm=True,
                        )
                else:
                    self.assertIn(territory_id, pending_ids)
                    gate = generation_enablement(
                        root_dir=ROOT, contract_path=state.get("contract_path"),
                        territory_id=territory_id,
                    )
                    self.assertFalse(gate["allowed"])

        self.assertEqual(seen, pass_ids | blocked_ready_ids | pending_ids)
        self.assertEqual(len(seen), 19)

    def _complete_contract(self) -> dict:
        return {
            "meta": {
                "territory_id": "demo",
                "contract_level": "production_m01_m06",
                "production_authorization": "AUTHORIZED",
                "status": "generation_ready",
            },
            "territory_contract": {
                "status": "generation_ready",
                "k_districts": 3,
                "population_floor_ratio": 0.9,
                "population_cap_ratio": 1.1,
                "target_tolerance_ratio": 0.1,
            },
            "modulos": {
                "modulo_01_preparar_base_territorial": {"out_geojson": "base.geojson"},
                "modulo_02_construir_adyacencias": {"predicate": "rook", "working_crs": "EPSG:25830"},
                "modulo_03_construir_grafo": {"out_graph_json": "graph.json"},
                "modulo_04_generar_semillas": {
                    "k_districts": 3, "in_graph_json": "graph.json", "in_geojson": "base.geojson",
                    "out_geojson": "m04.geojson", "municipality_field": "CUMUN",
                },
                "modulo_05_optimizar_distritos": {
                    "in_graph_json": "graph.json", "in_geojson": "m04.geojson",
                    "out_geojson": "m05.geojson", "municipality_field": "CUMUN",
                },
                "modulo_06_consolidar_distritos": {
                    "in_geojson": "m05.geojson", "expected_districts": 3,
                    "municipality_field": "CUMUN",
                },
            },
            "validation": {
                "municipality_field": "CUMUN",
                "require_graph_contiguity": True,
                "require_municipality_discipline": True,
            },
        }

    def _gate(self, contract: dict, root: Path) -> dict:
        path = root / "contract.yaml"
        path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
        return generation_enablement(
            root_dir=root, contract_path="contract.yaml", territory_id="demo",
            require_source=True,
            preparation_evidence={
                "run_id": 123, "artifact_name": "ddd-source-package-demo-2025-123",
                "artifact_sha256": "a" * 64,
            },
        )

    def test_complete_contract_passes_single_capability_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            gate = self._gate(self._complete_contract(), Path(raw))
        self.assertTrue(gate["allowed"])
        self.assertEqual(gate["route"], "declared_generation_ready")

    def test_individual_capability_ablation_blocks_with_precise_reason(self):
        mutations = {
            "CAP_CONTRACT": lambda c: c["meta"].update(contract_level="experimental_m01_m06"),
            "CAP_K": lambda c: c["territory_contract"].pop("k_districts"),
            "CAP_POPULATION_LIMITS": lambda c: c["territory_contract"].pop("population_floor_ratio"),
            "CAP_ADMIN_POLICY": lambda c: c["validation"].update(require_municipality_discipline=False),
            "CAP_GRAPH": lambda c: c["validation"].update(require_graph_contiguity=False),
            "CAP_M04_INPUT": lambda c: c["modulos"]["modulo_04_generar_semillas"].update(in_geojson="other.geojson"),
            "CAP_GENERATION_CHAIN": lambda c: c["modulos"]["modulo_05_optimizar_distritos"].update(in_geojson="other.geojson"),
        }
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            for capability, mutate in mutations.items():
                with self.subTest(capability=capability):
                    contract = deepcopy(self._complete_contract())
                    mutate(contract)
                    gate = self._gate(contract, root)
                    self.assertFalse(gate["allowed"])
                    self.assertEqual(gate["capability"], capability)
                    self.assertTrue(gate["reason"].startswith(capability + ":"))

            contract = self._complete_contract()
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            gate = generation_enablement(
                root_dir=root, contract_path="contract.yaml", territory_id="demo",
                require_source=True, preparation_evidence={},
            )
            self.assertFalse(gate["allowed"])
            self.assertEqual(gate["capability"], "CAP_SOURCE")
            self.assertTrue(gate["reason"].startswith("CAP_SOURCE:"))

    def test_from_start_may_plan_source_acquisition_without_circular_block(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract = self._complete_contract()
            contract["meta"]["status"] = "production_ready_auto_materialized"
            contract["territory_contract"]["status"] = "topology_contract_candidate"
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(contract, sort_keys=False), encoding="utf-8")
            gate = generation_enablement(
                root_dir=root, contract_path="contract.yaml", territory_id="demo",
                require_source=True, source_acquisition_planned=True,
            )
            self.assertTrue(gate["allowed"])
            self.assertEqual(gate["route"], "planned_source_acquisition")


if __name__ == "__main__":
    unittest.main()
