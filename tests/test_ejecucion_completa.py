from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

from tests import _test_ejecucion_completa_core as _core
from tests._test_ejecucion_completa_core import *  # noqa: F401,F403

build_plan = _core.build_plan


def _write_complete_demo_contract(root: Path) -> None:
    contract = root / "territorios/demo/config/demo_2025.yaml"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(yaml.safe_dump({
        "meta": {
            "territory_id": "demo",
            "status": "generation_ready",
            "contract_level": "production_m01_m06",
            "production_authorization": "AUTHORIZED",
        },
        "territory_contract": {
            "status": "generation_ready",
            "k_districts": 10,
            "population_floor_ratio": 0.8,
            "population_cap_ratio": 1.75,
            "target_tolerance_ratio": 0.12,
        },
        "modulos": {
            "modulo_01_preparar_base_territorial": {"out_geojson": "source.geojson"},
            "modulo_02_construir_adyacencias": {"out_edges_jsonl": "edges.jsonl"},
            "modulo_03_construir_grafo": {"out_graph_json": "graph.json"},
            "modulo_04_generar_semillas": {
                "in_graph_json": "graph.json",
                "in_geojson": "source.geojson",
                "out_geojson": "seeds.geojson",
                "municipality_field": "CUMUN",
                "k_districts": 10,
            },
            "modulo_05_optimizar_distritos": {
                "in_graph_json": "graph.json",
                "in_geojson": "seeds.geojson",
                "out_geojson": "optimized.geojson",
                "municipality_field": "CUMUN",
            },
            "modulo_06_consolidar_distritos": {
                "in_geojson": "optimized.geojson",
                "municipality_field": "CUMUN",
                "expected_districts": 10,
            },
        },
        "validation": {
            "municipality_field": "CUMUN",
            "require_municipality_discipline": True,
            "require_graph_contiguity": True,
        },
    }, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _test_reuse_plan_reruns_generation_for_selected_algorithm(self):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_complete_demo_contract(root)
        evidence = root / "evidence"
        evidence.mkdir()
        digest = "a" * 64
        (evidence / "territorial.json").write_text(json.dumps({"run_id": 101, "artifact_name": "m06", "artifact_sha256": digest, "decision": "PASS"}), encoding="utf-8")
        (evidence / "source.json").write_text(json.dumps({"run_id": 102, "artifact_name": "electoral-source", "artifact_sha256": digest}), encoding="utf-8")
        (evidence / "electoral.json").write_text(json.dumps({"run_id": 103, "artifact_name": "m08", "artifact_sha256": digest}), encoding="utf-8")
        catalog = root / "catalog.yaml"
        catalog.write_text(yaml.safe_dump({
            "schema": "ddd-preparation-catalog/1.1",
            "default_edition": "2025",
            "territories": [{
                "territory_id": "demo",
                "name": "Demo",
                "editions": {"2025": {
                    "territory_declared": True,
                    "preparation_status": "READY",
                    "contract_path": "territorios/demo/config/demo_2025.yaml",
                    "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
                    "electoral_source_declaration": "territorios/demo/config/elecciones/vigente.yaml",
                    "territorial_contract_complete": True,
                    "production_authorization": "AUTHORIZED",
                    "last_valid_checkpoint": {"run_id": 101, "stage": "M06"},
                    "territorial_sources_prepared": True,
                    "territorial_product_available": True,
                    "electoral_source_prepared": True,
                    "electoral_product_available": True,
                    "territorial_certification": "PASS_WITH_GOVERNED_EXCEPTIONS",
                    "preparation_evidence": {"run_id": 100, "artifact_name": "source-package", "artifact_sha256": digest},
                    "evidence": {
                        "territorial_product": "evidence/territorial.json",
                        "electoral_source": "evidence/source.json",
                        "electoral_product": "evidence/electoral.json",
                    },
                }},
            }],
        }, allow_unicode=True, sort_keys=False), encoding="utf-8")
        plan = build_plan(
            territory="Demo",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog,
            root_dir=root,
            force_selected_algorithm=True,
        )
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertTrue(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])
        self.assertEqual(plan["optimization_algorithm"], "Canónico")
        self.assertEqual(plan["existing"]["electoral_product"]["run_id"], 103)


def _test_gerrychain_50_is_preserved_in_plan(self):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_complete_demo_contract(root)
        catalog = root / "catalog.yaml"
        catalog.write_text(yaml.safe_dump({
            "schema": "ddd-preparation-catalog/1.1",
            "default_edition": "2025",
            "territories": [{
                "territory_id": "demo",
                "name": "Demo",
                "editions": {"2025": {
                    "territory_declared": True,
                    "preparation_status": "READY",
                    "contract_path": "territorios/demo/config/demo_2025.yaml",
                    "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
                    "electoral_source_declaration": "territorios/demo/config/elecciones/vigente.yaml",
                    "territorial_contract_complete": True,
                    "territorial_sources_prepared": True,
                    "territorial_product_available": True,
                    "electoral_source_prepared": True,
                    "electoral_product_available": True,
                    "territorial_certification": "PASS",
                    "production_authorization": "AUTHORIZED",
                    "last_valid_checkpoint": {"run_id": 10, "stage": "M06"},
                    "preparation_evidence": {"run_id": 9, "artifact_name": "source", "artifact_sha256": "c" * 64},
                }},
            }],
        }, allow_unicode=True, sort_keys=False), encoding="utf-8")
        plan = build_plan(
            territory="Demo",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog,
            root_dir=root,
            optimization_algorithm="GerryChain 50",
        )
        self.assertEqual(plan["optimization_algorithm"], "GerryChain 50")
        self.assertTrue(plan["run_generate"])
        self.assertTrue(plan["run_incorporate"])


_core.FullProjectOrchestratorTests.test_reuse_plan_reruns_generation_for_selected_algorithm = (
    _test_reuse_plan_reruns_generation_for_selected_algorithm
)
_core.FullProjectOrchestratorTests.test_gerrychain_50_is_preserved_in_plan = _test_gerrychain_50_is_preserved_in_plan
FullProjectOrchestratorTests = _core.FullProjectOrchestratorTests
