from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

from tests import _test_gestor_campana_core as _core
from tests._test_gestor_campana_core import *  # noqa: F401,F403

ROOT = _core.ROOT
build_plan = _core.build_plan
generation_enablement = _core.generation_enablement
apply_explicit_territorial_source = _core.apply_explicit_territorial_source


def _test_generation_gate_real_territories_and_both_entry_paths(self):
    catalog_path = ROOT / "configuracion/catalogo_preparacion.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    rows = {row["territory_id"]: row["editions"]["2025"] for row in catalog["territories"]}

    for name, territory_id, route in (
        ("Galicia", "galicia", "certified_product_lineage"),
        ("Principado de Asturias", "principado_de_asturias", "certified_product_lineage"),
        ("Aragón", "aragon", "certified_product_lineage"),
        ("Castilla y León", "castilla_y_leon", "certified_product_lineage"),
        ("Andalucía", "andalucia", "declared_generation_ready"),
    ):
        with self.subTest(territory=name):
            plan = build_plan(
                territory=name, edition="2025", execution_mode="reuse",
                catalog=catalog_path, root_dir=ROOT, force_selected_algorithm=True,
            )
            self.assertEqual(plan["generation_gate"], {"allowed": True, "route": route})

    for name, territory_id in (
        ("La Rioja", "la_rioja"),
        ("Cantabria", "cantabria"),
        ("Comunidad Foral de Navarra", "comunidad_foral_de_navarra"),
        ("País Vasco", "pais_vasco"),
    ):
        with self.subTest(first_product=territory_id):
            row = rows[territory_id]
            self.assertFalse(row["territorial_product_available"])
            self.assertEqual(row["territorial_certification"], "NOT_CERTIFIED")
            evidence_path = row["evidence"]["generation_preflight"]
            evidence = json.loads((ROOT / evidence_path).read_text(encoding="utf-8"))
            bare_gate = generation_enablement(
                root_dir=ROOT, contract_path=row["contract_path"],
                territory_id=territory_id, certified_product_ready=False,
            )
            if territory_id == "cantabria":
                # #140 materializa Cantabria como contrato generation_ready. Esto es
                # capacidad estructural del contrato, no un efecto de AUTHORIZED.
                self.assertEqual(bare_gate, {"allowed": True, "route": "declared_generation_ready"})
            else:
                self.assertFalse(bare_gate["allowed"])
            plan = build_plan(
                territory=name, edition="2025", execution_mode="reuse",
                catalog=catalog_path, root_dir=ROOT, force_selected_algorithm=True,
            )
            self.assertEqual(plan["generation_gate"], {"allowed": True, "route": "validated_pre_m04_topology"})
            prep = row["preparation_evidence"]
            apply_explicit_territorial_source(
                plan, root_dir=ROOT, reuse_run_id=str(prep["run_id"]),
                reuse_artifact_name=prep["artifact_name"],
                reuse_artifact_sha256=prep["artifact_sha256"],
                reuse_source_sha=evidence["source_commit"],
            )
            self.assertTrue(plan["run_generate"])
            self.assertEqual(plan["existing"]["territorial_source"]["run_id"], prep["run_id"])

    for name, territory_id in (
        ("Comunidad de Madrid", "madrid"),
        ("Comunidad Valenciana", "comunidad_valenciana"),
        ("Cataluña", "cataluna"),
    ):
        with self.subTest(still_blocked=territory_id):
            row = rows[territory_id]
            self.assertFalse(row["territorial_product_available"])
            self.assertFalse((row.get("evidence") or {}).get("generation_preflight"))
            with self.assertRaisesRegex(ValueError, "GENERATION_CONTRACT_BLOCK"):
                build_plan(
                    territory=name, edition="2025", execution_mode="reuse",
                    catalog=catalog_path, root_dir=ROOT, force_selected_algorithm=True,
                )


def _write_structural_fixture(root: Path, *, b_sha: str = "b" * 64, authorization=..., broken_k: bool = False) -> Path:
    meta = {"territory_id": "fixture", "status": "generation_ready", "contract_level": "production_m01_m06"}
    if authorization is not ...:
        meta["production_authorization"] = authorization
    (root / "contract.yaml").write_text(yaml.safe_dump({
        "meta": meta,
        "territory_contract": {
            "status": "generation_ready", "k_districts": 45,
            "population_floor_ratio": 0.8, "population_cap_ratio": 1.75,
            "target_tolerance_ratio": 0.12,
        },
        "modulos": {
            "modulo_01_preparar_base_territorial": {"out_geojson": "source.geojson"},
            "modulo_02_construir_adyacencias": {"out_edges_jsonl": "edges.jsonl"},
            "modulo_03_construir_grafo": {"out_graph_json": "graph.json"},
            "modulo_04_generar_semillas": {"in_graph_json": "graph.json", "in_geojson": "source.geojson", "out_geojson": "seeds.geojson", "municipality_field": "CUMUN", "k_districts": 45},
            "modulo_05_optimizar_distritos": {"in_graph_json": "graph.json", "in_geojson": "seeds.geojson", "out_geojson": "optimized.geojson", "municipality_field": "CUMUN"},
            "modulo_06_consolidar_distritos": {"in_geojson": "optimized.geojson", "municipality_field": "CUMUN", "expected_districts": 44 if broken_k else 45},
        },
        "validation": {"municipality_field": "CUMUN", "require_municipality_discipline": True, "require_graph_contiguity": True},
    }, allow_unicode=True), encoding="utf-8")
    catalog = root / "catalog.yaml"
    catalog.write_text(yaml.safe_dump({
        "schema": "ddd-preparation-catalog/1.1", "default_edition": "2025",
        "territories": [{"territory_id": "fixture", "name": "Fixture", "editions": {"2025": {
            "territory_declared": True, "preparation_status": "READY", "contract_path": "contract.yaml",
            "territorial_source_declaration": "sources.yaml", "electoral_source_declaration": None,
            "territorial_contract_complete": True, "territorial_sources_prepared": True,
            "territorial_product_available": False, "electoral_source_prepared": False,
            "electoral_product_available": False, "territorial_certification": "NOT_CERTIFIED",
            "production_authorization": "AUTHORIZED", "last_valid_checkpoint": None,
            "preparation_evidence": {"run_id": 999999, "artifact_name": "source-B", "artifact_sha256": b_sha},
        }}}],
    }, allow_unicode=True), encoding="utf-8")
    return catalog


def _test_effective_manifest_source_precedes_catalog_provenance(self):
    source_a = {"run_id": 123456, "artifact_name": "source-A", "artifact_sha256": "a" * 64, "source_commit": "c" * 40}
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        catalog = _write_structural_fixture(root, b_sha="invalid-B")
        plan = build_plan(territory="Fixture", edition="2025", execution_mode="reuse", catalog=catalog, root_dir=root, force_selected_algorithm=True, explicit_territorial_source=source_a)
        self.assertEqual(plan["existing"]["territorial_source"]["artifact_name"], "source-A")
        self.assertEqual(plan["generation_gate"], {"allowed": True, "route": "declared_generation_ready"})
        self.assertFalse(plan["run_prepare_territorial"])
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        catalog = _write_structural_fixture(root)
        with self.assertRaisesRegex(ValueError, "CAP_SOURCE"):
            build_plan(territory="Fixture", edition="2025", execution_mode="reuse", catalog=catalog, root_dir=root, force_selected_algorithm=True, explicit_territorial_source={**source_a, "artifact_sha256": "invalid-A"})


def _test_authorization_is_neutral_but_explicit_block_is_not(self):
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        _write_structural_fixture(root, authorization="AUTHORIZED")
        authorized = generation_enablement(root_dir=root, contract_path="contract.yaml", territory_id="fixture")
        self.assertEqual(authorized, {"allowed": True, "route": "declared_generation_ready"})
        _write_structural_fixture(root, authorization=...)
        absent = generation_enablement(root_dir=root, contract_path="contract.yaml", territory_id="fixture")
        self.assertEqual(absent, authorized)
        _write_structural_fixture(root, authorization="BLOCKED")
        blocked = generation_enablement(root_dir=root, contract_path="contract.yaml", territory_id="fixture")
        self.assertFalse(blocked["allowed"])
        self.assertEqual(blocked["capability"], "CAP_CONTRACT")


def _test_explicit_source_never_repairs_missing_structural_capability(self):
    source_a = {"run_id": 123456, "artifact_name": "source-A", "artifact_sha256": "a" * 64, "source_commit": "c" * 40}
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        catalog = _write_structural_fixture(root, broken_k=True)
        with self.assertRaisesRegex(ValueError, "CAP_K"):
            build_plan(territory="Fixture", edition="2025", execution_mode="reuse", catalog=catalog, root_dir=root, force_selected_algorithm=True, explicit_territorial_source=source_a)


_core.CampaignManagerTests.test_generation_gate_real_territories_and_both_entry_paths = _test_generation_gate_real_territories_and_both_entry_paths
_core.CampaignManagerTests.test_effective_manifest_source_precedes_catalog_provenance = _test_effective_manifest_source_precedes_catalog_provenance
_core.CampaignManagerTests.test_authorization_is_neutral_but_explicit_block_is_not = _test_authorization_is_neutral_but_explicit_block_is_not
_core.CampaignManagerTests.test_explicit_source_never_repairs_missing_structural_capability = _test_explicit_source_never_repairs_missing_structural_capability
CampaignManagerTests = _core.CampaignManagerTests
