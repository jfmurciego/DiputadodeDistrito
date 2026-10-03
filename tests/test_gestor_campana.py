from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

import yaml

from tests import _test_gestor_campana_core as _core
from tests._test_gestor_campana_core import *  # noqa: F401,F403

ROOT = _core.ROOT
build_plan = _core.build_plan
generation_enablement = _core.generation_enablement
apply_explicit_territorial_source = _core.apply_explicit_territorial_source


PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


def _durable_receipt(state: dict, territory_id: str, kind: str) -> dict:
    rel = (state.get("evidence") or {}).get(kind)
    self_path = ROOT / str(rel or "")
    assert rel and self_path.is_file(), f"falta receipt {kind} de {territory_id}"
    payload = json.loads(self_path.read_text(encoding="utf-8"))
    assert payload["territory_id"] == territory_id
    assert str(payload["edition"]) == "2025"
    assert re.fullmatch(r"[0-9a-f]{64}", str(payload["artifact_sha256"]).removeprefix("sha256:"))
    assert payload["run_id"]
    return payload


def _expected_current_generation_route(state: dict, territory_id: str) -> str:
    receipt = _durable_receipt(state, territory_id, "territorial_product")
    certified = bool(
        state.get("territorial_product_available")
        and state.get("territorial_certification") in PASS_CERTIFICATIONS
        and receipt.get("decision") in PASS_CERTIFICATIONS
    )
    if certified:
        return "certified_product_lineage"
    if (state.get("evidence") or {}).get("generation_preflight"):
        return "validated_pre_m04_topology"
    contract = yaml.safe_load((ROOT / state["contract_path"]).read_text(encoding="utf-8")) or {}
    if (contract.get("meta") or {}).get("status") == "generation_ready":
        return "declared_generation_ready"
    raise AssertionError(f"no se puede derivar ruta de generación vigente para {territory_id}")


def _test_generation_gate_real_territories_and_both_entry_paths(self):
    catalog_path = ROOT / "configuracion/catalogo_preparacion.yaml"
    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
    rows = {row["territory_id"]: row["editions"]["2025"] for row in catalog["territories"]}

    # Un producto ya certificado sigue siendo reutilizable sólo cuando su
    # lineage corresponde a la fuente territorial actualmente acreditada.
    for name, territory_id in (
        ("Galicia", "galicia"),
    ):
        with self.subTest(certified_reuse=territory_id):
            row = rows[territory_id]
            if not row.get("territorial_product_available"):
                continue
            plan = build_plan(
                territory=name,
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=ROOT,
                optimization_algorithm="Canónico",
                force_selected_algorithm=False,
            )
            self.assertFalse(plan["run_prepare_territorial"])
            self.assertFalse(plan["run_generate"])
            self.assertEqual(plan["generation_gate"], {"allowed": True, "route": "certified_product_lineage"})

    # Asturias acaba de acreditar una fuente territorial 2023 distinta de la que
    # produjo su producto histórico. El catálogo conserva ese producto como
    # evidencia histórica, pero la reutilización debe bloquearse por lineage.
    with self.assertRaisesRegex(ValueError, "DURABLE_LINEAGE_INCOMPATIBLE"):
        build_plan(
            territory="Principado de Asturias",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog_path,
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=False,
        )

    # En cambio, cualquier nueva generación sobre los paquetes históricos actuales
    # debe reacreditar la fuente: todavía carecen de compatibilidad+año completa.
    for name, territory_id in (
        ("Galicia", "galicia"),
        ("Principado de Asturias", "principado_de_asturias"),
        ("Aragón", "aragon"),
        ("Castilla y León", "castilla_y_leon"),
        ("Andalucía", "andalucia"),
        ("La Rioja", "la_rioja"),
        ("Cantabria", "cantabria"),
        ("Comunidad Foral de Navarra", "comunidad_foral_de_navarra"),
        ("País Vasco", "pais_vasco"),
        ("Comunidad de Madrid", "madrid"),
        ("Comunidad Valenciana", "comunidad_valenciana"),
        ("Cataluña", "cataluna"),
    ):
        with self.subTest(recompute=territory_id):
            plan = build_plan(
                territory=name,
                edition="2025",
                execution_mode="reuse",
                catalog=catalog_path,
                root_dir=ROOT,
                optimization_algorithm="GerryChain 50",
                force_selected_algorithm=True,
            )
            self.assertTrue(plan["run_prepare_territorial"])
            self.assertEqual(
                plan["generation_gate"],
                {"allowed": True, "route": "planned_pre_m04_accreditation"},
            )
            self.assertTrue(plan["pre_m04_accreditation_planned"])

            row = rows[territory_id]
            historical_preflight = (row.get("evidence") or {}).get("generation_preflight")
            if historical_preflight:
                evidence = json.loads((ROOT / historical_preflight).read_text(encoding="utf-8"))
                direct = generation_enablement(
                    root_dir=ROOT,
                    contract_path=row["contract_path"],
                    territory_id=territory_id,
                    certified_product_ready=False,
                    first_generation_evidence=evidence,
                    preparation_evidence=row.get("preparation_evidence") or {},
                    require_source=True,
                )
                self.assertFalse(direct["allowed"])
                self.assertIn(direct["capability"], {"CAP_SOURCE", "CAP_PRE_M04_EVIDENCE"})



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
        with self.assertRaisesRegex(ValueError, "CAP_SOURCE|CAP_PRE_M04_EVIDENCE"):
            build_plan(
                territory="Fixture", edition="2025", execution_mode="reuse",
                catalog=catalog, root_dir=root, force_selected_algorithm=True,
                explicit_territorial_source=source_a,
            )
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
        self.assertFalse(authorized["allowed"])
        self.assertEqual(authorized["capability"], "CAP_PRE_M04_EVIDENCE")
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
