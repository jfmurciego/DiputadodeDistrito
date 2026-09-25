from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

import tests.test_ejecucion_completa as _full
from herramientas.resolver_ejecucion_completa import build_plan


def _write_contract(root: Path) -> None:
    path = root / "territorios/demo/config/demo_2025.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({
        "meta": {"territory_id": "demo", "status": "generation_ready", "contract_level": "production_m01_m06"},
        "territory_contract": {"status": "generation_ready", "k_districts": 45, "population_floor_ratio": 0.8, "population_cap_ratio": 1.75, "target_tolerance_ratio": 0.12},
        "modulos": {
            "modulo_01_preparar_base_territorial": {"out_geojson": "source.geojson"},
            "modulo_02_construir_adyacencias": {"out_edges_jsonl": "edges.jsonl"},
            "modulo_03_construir_grafo": {"out_graph_json": "graph.json"},
            "modulo_04_generar_semillas": {"in_graph_json": "graph.json", "in_geojson": "source.geojson", "out_geojson": "seeds.geojson", "municipality_field": "CUMUN", "k_districts": 45},
            "modulo_05_optimizar_distritos": {"in_graph_json": "graph.json", "in_geojson": "seeds.geojson", "out_geojson": "optimized.geojson", "municipality_field": "CUMUN"},
            "modulo_06_consolidar_distritos": {"in_geojson": "optimized.geojson", "municipality_field": "CUMUN", "expected_districts": 45},
        },
        "validation": {"municipality_field": "CUMUN", "require_municipality_discipline": True, "require_graph_contiguity": True},
    }, allow_unicode=True), encoding="utf-8")


def _catalog(root: Path, *, digest: str, with_evidence: bool) -> Path:
    evidence = {}
    if with_evidence:
        edir = root / "evidence"
        edir.mkdir()
        (edir / "territorial.json").write_text(json.dumps({"run_id": 101, "artifact_name": "m06", "artifact_sha256": digest, "decision": "PASS"}), encoding="utf-8")
        (edir / "source.json").write_text(json.dumps({"run_id": 102, "artifact_name": "electoral-source", "artifact_sha256": digest}), encoding="utf-8")
        (edir / "electoral.json").write_text(json.dumps({"run_id": 103, "artifact_name": "m08", "artifact_sha256": digest}), encoding="utf-8")
        evidence = {"territorial_product": "evidence/territorial.json", "electoral_source": "evidence/source.json", "electoral_product": "evidence/electoral.json"}
    catalog = root / "catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "schema": "ddd-preparation-catalog/1.1", "default_edition": "2025",
        "territories": [{"territory_id": "demo", "name": "Demo", "editions": {"2025": {
            "territory_declared": True, "preparation_status": "READY", "contract_path": "territorios/demo/config/demo_2025.yaml",
            "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml", "electoral_source_declaration": "territorios/demo/config/elecciones/vigente.yaml",
            "territorial_contract_complete": True, "production_authorization": "AUTHORIZED", "last_valid_checkpoint": {"run_id": 101 if with_evidence else 10, "stage": "M06"},
            "territorial_sources_prepared": True, "territorial_product_available": True, "electoral_source_prepared": True, "electoral_product_available": True,
            "territorial_certification": "PASS_WITH_GOVERNED_EXCEPTIONS" if with_evidence else "PASS",
            "preparation_evidence": {"run_id": 100 if with_evidence else 9, "artifact_name": "source-package" if with_evidence else "source", "artifact_sha256": digest}, "evidence": evidence,
        }}}],
    }, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return catalog


def _test_reuse_plan_reruns_generation_for_selected_algorithm(self):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); _write_contract(root); catalog = _catalog(root, digest="a" * 64, with_evidence=True)
        plan = build_plan(territory="Demo", edition="2025", execution_mode="reuse", catalog=catalog, root_dir=root, force_selected_algorithm=True)
        self.assertFalse(plan["run_prepare_territorial"]); self.assertTrue(plan["run_generate"]); self.assertFalse(plan["run_prepare_electoral"]); self.assertTrue(plan["run_incorporate"])
        self.assertEqual(plan["optimization_algorithm"], "Canónico"); self.assertEqual(plan["existing"]["electoral_product"]["run_id"], 103)


def _test_gerrychain_50_is_preserved_in_plan(self):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td); _write_contract(root); catalog = _catalog(root, digest="c" * 64, with_evidence=False)
        plan = build_plan(territory="Demo", edition="2025", execution_mode="reuse", catalog=catalog, root_dir=root, optimization_algorithm="GerryChain 50")
        self.assertEqual(plan["optimization_algorithm"], "GerryChain 50"); self.assertTrue(plan["run_generate"]); self.assertTrue(plan["run_incorporate"])


_full.FullProjectOrchestratorTests.test_reuse_plan_reruns_generation_for_selected_algorithm = _test_reuse_plan_reruns_generation_for_selected_algorithm
_full.FullProjectOrchestratorTests.test_gerrychain_50_is_preserved_in_plan = _test_gerrychain_50_is_preserved_in_plan


class IntegrationPatchDiscovery(_full.unittest.TestCase):
    def test_140_fixtures_keep_138_structural_gate(self):
        self.assertIs(_full.FullProjectOrchestratorTests.test_reuse_plan_reruns_generation_for_selected_algorithm, _test_reuse_plan_reruns_generation_for_selected_algorithm)
        self.assertIs(_full.FullProjectOrchestratorTests.test_gerrychain_50_is_preserved_in_plan, _test_gerrychain_50_is_preserved_in_plan)
