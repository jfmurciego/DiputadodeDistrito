from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.registro_publicaciones_visor import make_candidate
from herramientas.resolver_ejecucion_completa import (
    build_plan, apply_explicit_territorial_source, generation_enablement,
)
from herramientas.gestor_campana import (
    CONFIRMATION,
    aggregate,
    assert_productive_launch,
    build_matrix,
    sha256,
    validate_manifest,
    validate_portfolio_contract,
    validate_portfolio_bundle,
    validate_portfolio_artifact_identity,
    portfolio_artifact_name,
    campaign_strategy,
    validate_reuse_metadata,
    validate_campaign_summary_for_promotion,
    release_identity,
    publication_matrix,
    package_campaign_gallery,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "configuracion/campanas/campana_cinco_territorios_v1.json"
WORKFLOW = ROOT / ".github/workflows/gestor-campanas.yml"
ORCH = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"


class CampaignManagerTests(unittest.TestCase):
    def manifest_copy(self) -> dict:
        return json.loads(MANIFEST.read_text(encoding="utf-8"))

    def write_manifest(self, data: dict, root: Path) -> Path:
        path = root / "manifest.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_manifest_is_strict_five_territory_contract(self):
        data = validate_manifest(MANIFEST)
        self.assertEqual(data["entrypoint"], "gerrychain_50")
        self.assertTrue(data["require_unique_hashes"])
        self.assertEqual(data["candidate_count"], 50)
        self.assertFalse(data["fail_fast"])
        self.assertEqual(data["max_parallel"], 5)
        self.assertFalse(data["retry_failed"])
        for row in data["territories"]:
            reuse = row["reuse"]
            self.assertEqual(reuse["checkpoint_stage"], "SOURCE_PACKAGE")
            self.assertEqual(len(reuse["source_sha"]), 40)
            self.assertEqual(len(reuse["artifact_sha256"]), 64)
            self.assertEqual(len(reuse["m01_artifact_sha256"]), 64)
            self.assertEqual(reuse["expected_certification"], "READY")

    def test_missing_or_wrong_entrypoint_is_rejected(self):
        for value in (None, "generic", "gerrychain"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as raw:
                data = self.manifest_copy()
                if value is None:
                    data.pop("entrypoint")
                else:
                    data["entrypoint"] = value
                with self.assertRaisesRegex(ValueError, "entrypoint"):
                    validate_manifest(self.write_manifest(data, Path(raw)))

    def test_unique_hashes_disabled_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            data = self.manifest_copy()
            data["require_unique_hashes"] = False
            with self.assertRaisesRegex(ValueError, "require_unique_hashes"):
                validate_manifest(self.write_manifest(data, Path(raw)))

    def test_campaign_strategy_selects_canonical_and_gerry_variants(self):
        expected = {
            "Canónico": ("Canónico", "", 0, False),
            "GerryChain": ("GerryChain", "", 1, False),
            "GerryChain 25": ("GerryChain 25", "", 25, False),
            "GerryChain 50": ("GerryChain 50", "gerrychain_50", 50, True),
        }
        for name, contract in expected.items():
            selected = campaign_strategy(name)
            self.assertEqual(
                (
                    selected["optimization_algorithm"],
                    selected["entrypoint"],
                    selected["candidate_count"],
                    selected["require_unique_hashes"],
                ),
                contract,
            )

    def test_matrix_propagates_strict_contract_and_fixed_reuse(self):
        source_sha = "a" * 40
        rows = build_matrix(
            MANIFEST,
            source_sha=source_sha,
            campaign_instance="campaign-123-1",
            confirmation=CONFIRMATION,
        )["include"]
        self.assertEqual(len(rows), 5)
        self.assertEqual(len({row["namespace"] for row in rows}), 5)
        self.assertEqual(len({row["artifact_namespace"] for row in rows}), 5)
        digest = sha256(MANIFEST)
        for row in rows:
            self.assertEqual(row["source_sha"], source_sha)
            self.assertEqual(row["manifest_sha256"], digest)
            self.assertEqual(row["entrypoint"], "gerrychain_50")
            self.assertTrue(row["require_unique_hashes"])
            self.assertEqual(row["candidate_count"], 50)
            self.assertGreater(row["reuse_run_id"], 0)
            self.assertEqual(len(row["reuse_artifact_sha256"]), 64)
            self.assertEqual(len(row["reuse_source_sha"]), 40)

    def test_matrix_overrides_execution_strategy_without_weakening_manifest_reuse(self):
        for strategy in ("Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"):
            rows = build_matrix(
                MANIFEST,
                source_sha="c" * 40,
                campaign_instance="campaign-strategy",
                confirmation=CONFIRMATION,
                strategy=strategy,
            )["include"]
            selected = campaign_strategy(strategy)
            for row in rows:
                self.assertEqual(row["optimization_algorithm"], selected["optimization_algorithm"])
                self.assertEqual(row["entrypoint"], selected["entrypoint"])
                self.assertEqual(row["candidate_count"], selected["candidate_count"])
                self.assertEqual(row["require_unique_hashes"], selected["require_unique_hashes"])
                self.assertGreater(row["reuse_run_id"], 0)

    def test_wrong_confirmation_is_rejected(self):
        with self.assertRaises(ValueError):
            build_matrix(
                MANIFEST,
                source_sha="a" * 40,
                campaign_instance="campaign-x",
                confirmation="NO",
            )

    def test_productive_pull_request_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "workflow_dispatch"):
            assert_productive_launch("pull_request", "main", CONFIRMATION)

    def test_checkpoint_digest_or_provenance_mismatch_is_rejected(self):
        reuse = self.manifest_copy()["territories"][0]["reuse"]
        ok = dict(
            run_head_sha=reuse["source_sha"],
            artifact_name=reuse["artifact_name"],
            artifact_digest="sha256:" + reuse["artifact_sha256"],
            m01_artifact_name=reuse["m01_artifact_name"],
            m01_artifact_digest="sha256:" + reuse["m01_artifact_sha256"],
        )
        validate_reuse_metadata(reuse, **ok)
        bad = dict(ok)
        bad["run_head_sha"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "procedencia"):
            validate_reuse_metadata(reuse, **bad)
        bad = dict(ok)
        bad["artifact_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "Digest"):
            validate_reuse_metadata(reuse, **bad)

    def test_fifty_candidates_with_49_unique_hashes_is_invalid(self):
        candidates = [{"assignment_hash": f"{idx:064x}"} for idx in range(49)]
        candidates.append({"assignment_hash": candidates[0]["assignment_hash"]})
        result = validate_portfolio_contract(
            {"candidate_count": 50, "unique_candidate_count": 49, "candidates": candidates}
        )
        self.assertEqual(result["candidate_count_expected"], 50)
        self.assertEqual(result["candidate_count_valid"], 50)
        self.assertEqual(result["unique_candidate_hash_count"], 49)
        self.assertEqual(result["duplicate_candidate_hash_count"], 1)
        self.assertFalse(result["valid"])

    def test_valid_portfolio_requires_exactly_50_nonmissing_unique_hashes(self):
        candidates = [{"assignment_hash": f"{idx:064x}"} for idx in range(50)]
        result = validate_portfolio_contract(
            {"candidate_count": 50, "unique_candidate_count": 50, "candidates": candidates}
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["candidate_count_valid"], 50)
        self.assertEqual(result["unique_candidate_hash_count"], 50)
        self.assertEqual(result["missing_candidate_hash_count"], 0)
        self.assertEqual(result["duplicate_candidate_hash_count"], 0)

    def test_aggregate_rejects_any_non_strict_territorial_summary(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            rows = build_matrix(
                MANIFEST,
                source_sha="b" * 40,
                campaign_instance="campaign-x",
                confirmation=CONFIRMATION,
            )["include"]
            for row in rows:
                target = root / row["artifact_namespace"] / "summary"
                target.mkdir(parents=True)
                payload = {
                    **row,
                    "status": "PASS",
                    "candidate_count_expected": 50,
                    "candidate_count_valid": 50,
                    "unique_candidate_hash_count": 50,
                    "missing_candidate_hash_count": 0,
                    "duplicate_candidate_hash_count": 0,
                }
                if row["territory_id"] == "galicia":
                    payload["unique_candidate_hash_count"] = 49
                (target / "campaign_status.json").write_text(
                    json.dumps(payload), encoding="utf-8"
                )
            summary = aggregate(
                MANIFEST, root, campaign_instance="campaign-x", source_sha="b" * 40
            )
            self.assertEqual(summary["status"], "FAIL")
            self.assertEqual(summary["failed_territories"], ["galicia"])

    def test_pull_request_never_schedules_productive_campaign_or_pages(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("inputs.operacion == 'Ejecutar campaña'", manager)
        self.assertIn("github.event_name == 'pull_request'", manager)
        self.assertIn("publish_result: false", manager)
        self.assertIn("E2E sintético de campaña sin ejecutar territorios", manager)
        self.assertIn("github.event_name != 'pull_request'", orchestration)
        self.assertIn("publish=false", orchestration)
        self.assertIn("needs.planificar.outputs.run_prepare_territorial == 'true'", orchestration)
        self.assertIn("needs.planificar.outputs.run_generate == 'true'", orchestration)
        self.assertIn("needs.planificar.outputs.run_incorporate == 'true'", orchestration)
        self.assertNotIn("repository_dispatch", manager)
        self.assertNotIn("gh workflow run", manager)
        self.assertNotIn("rerun", manager.lower())
        self.assertNotIn("sleep ", manager)

    def test_contract_is_propagated_to_runtime_runner(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        production = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        reusable = (ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        for text in (manager, orchestration, production, reusable):
            self.assertIn("gerrychain_entrypoint", text)
            self.assertIn("require_unique_hashes", text)
        self.assertIn("DDD_GERRYCHAIN_ENTRYPOINT", reusable)
        self.assertIn("DDD_REQUIRE_UNIQUE_HASHES", reusable)
        self.assertIn('DDD_GERRYCHAIN_ENTRYPOINT:-}" == "gerrychain_50"', procedure)
        self.assertIn('DDD_REQUIRE_UNIQUE_HASHES:-}" == "true"', procedure)

    def test_no_implicit_latest_checkpoint_in_campaign_contract(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        orchestration = ORCH.read_text(encoding="utf-8")
        production = (ROOT / ".github/workflows/produccion-distritos.yml").read_text(encoding="utf-8")
        self.assertIn("reuse_run_id:", manager)
        self.assertIn("reuse_artifact_name:", manager)
        self.assertIn("reuse_artifact_sha256:", manager)
        self.assertIn("reuse_source_sha:", manager)
        self.assertIn("apply_explicit_territorial_source(", orchestration)
        self.assertIn('if [[ -n "$OVERRIDE_SOURCE_RUN_ID" || -n "$OVERRIDE_SOURCE_ARTIFACT_NAME" ]]', production)
        self.assertLess(production.index("se prohíbe sustituirlo por el catálogo"),
                        production.index('validate_candidate "$PREPARED_SOURCE_RUN_ID"'))

    def test_fixed_manifest_source_a_wins_over_live_catalog_b_for_three_strategies(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract = root / "territorios/principado_de_asturias/config/contract.yaml"
            contract.parent.mkdir(parents=True)
            contract.write_text(yaml.safe_dump({
                "meta": {"territory_id": "principado_de_asturias", "status": "generation_ready"},
                "territory_contract": {"status": "generation_ready"},
            }), encoding="utf-8")
            catalog = root / "catalog.yaml"
            catalog.write_text(yaml.safe_dump({
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [{
                    "territory_id": "principado_de_asturias",
                    "name": "Principado de Asturias",
                    "editions": {"2025": {
                        "territory_declared": True,
                        "preparation_status": "READY",
                        "contract_path": "territorios/principado_de_asturias/config/contract.yaml",
                        "territorial_source_declaration": "sources.yaml",
                        "electoral_source_declaration": None,
                        "territorial_contract_complete": True,
                        "territorial_sources_prepared": True,
                        "territorial_product_available": False,
                        "electoral_source_prepared": False,
                        "electoral_product_available": False,
                        "territorial_certification": "NOT_CERTIFIED",
                        "production_authorization": "AUTHORIZED",
                        "last_valid_checkpoint": None,
                        "preparation_evidence": {"run_id": 999999, "artifact_name": "source-B", "artifact_sha256": "b" * 64},
                    }},
                }],
            }, allow_unicode=True), encoding="utf-8")
            for strategy in ("Canónico", "GerryChain", "GerryChain 25"):
                with self.subTest(strategy=strategy):
                    row = build_matrix(MANIFEST, source_sha="c" * 40,
                                       campaign_instance="campaign-test", confirmation=CONFIRMATION,
                                       strategy=strategy)["include"][1]
                    self.assertNotEqual(row["reuse_run_id"], 999999)
                    plan = build_plan(territory="Principado de Asturias", edition="2025",
                                      execution_mode="reuse", catalog=catalog, root_dir=root,
                                      optimization_algorithm=strategy, force_selected_algorithm=True)
                    self.assertEqual(plan["existing"]["territorial_source"]["artifact_name"], "source-B")
                    apply_explicit_territorial_source(
                        plan, root_dir=root, reuse_run_id=str(row["reuse_run_id"]),
                        reuse_artifact_name=row["reuse_artifact_name"],
                        reuse_artifact_sha256=row["reuse_artifact_sha256"],
                        reuse_source_sha=row["reuse_source_sha"],
                    )
                    self.assertEqual(plan["existing"]["territorial_source"]["run_id"], row["reuse_run_id"])
                    self.assertEqual(plan["existing"]["territorial_source"]["artifact_name"], row["reuse_artifact_name"])
                    self.assertEqual(plan["existing"]["territorial_source"]["artifact_sha256"], row["reuse_artifact_sha256"])
                    self.assertEqual(plan["existing"]["territorial_source"]["source_commit"], row["reuse_source_sha"])
                    self.assertEqual(plan["execution_mode"], "from_start")
                    self.assertFalse(plan["run_prepare_territorial"])
                    self.assertTrue(plan["run_generate"])
            for mode in ("reuse", "from_start"):
                with self.subTest(manual_mode=mode):
                    manual = build_plan(territory="Principado de Asturias", edition="2025",
                                        execution_mode=mode, catalog=catalog, root_dir=root,
                                        force_selected_algorithm=True)
                    unchanged = json.loads(json.dumps(manual))
                    self.assertEqual(apply_explicit_territorial_source(manual), unchanged)
                    self.assertEqual(manual["existing"]["territorial_source"]["artifact_name"], "source-B")
                    self.assertEqual(manual["run_prepare_territorial"], mode == "from_start")

    def test_partial_fixed_source_blocks_and_manual_plan_keeps_catalog_behavior(self):
        plan = {"execution_mode": "reuse", "run_prepare_territorial": False,
                "run_generate": True, "existing": {"territorial_source": {"run_id": 999, "artifact_name": "source-B"}}}
        before = json.loads(json.dumps(plan))
        self.assertEqual(apply_explicit_territorial_source(plan), before)
        with self.assertRaisesRegex(ValueError, "Procedencia explícita incompleta"):
            apply_explicit_territorial_source(plan, reuse_run_id="123", reuse_artifact_name="source-A")
        self.assertEqual(plan, before)
        with self.assertRaisesRegex(ValueError, "Procedencia explícita incompleta"):
            apply_explicit_territorial_source(plan, campaign_instance="campaign-test")
        self.assertEqual(plan, before)

    def test_generation_gate_first_product_preflight_and_existing_routes(self):
        catalog_path = ROOT / "configuracion/catalogo_preparacion.yaml"
        catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
        rows = {row["territory_id"]: row["editions"]["2025"] for row in catalog["territories"]}

        for name, territory_id, route in (
            ("Galicia", "galicia", "certified_product_lineage"),
            ("Principado de Asturias", "principado_de_asturias", "linked_internal_partitioning"),
            ("Aragón", "aragon", "certified_product_lineage"),
            ("Castilla y León", "castilla_y_leon", "certified_product_lineage"),
            ("La Rioja", "la_rioja", "validated_pre_m04_topology"),
            ("Cantabria", "cantabria", "validated_pre_m04_topology"),
            ("Comunidad Foral de Navarra", "comunidad_foral_de_navarra", "validated_pre_m04_topology"),
            ("País Vasco", "pais_vasco", "validated_pre_m04_topology"),
        ):
            with self.subTest(territory=name):
                row = rows[territory_id]
                plan = build_plan(
                    territory=name,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog_path,
                    root_dir=ROOT,
                    force_selected_algorithm=True,
                )
                self.assertEqual(plan["generation_gate"], {"allowed": True, "route": route})
                self.assertTrue(plan["run_generate"])

                if route == "validated_pre_m04_topology":
                    self.assertFalse(row["territorial_product_available"])
                    self.assertEqual(row["territorial_certification"], "NOT_CERTIFIED")
                    evidence = plan["catalog_state"]["generation_preflight"]
                    self.assertEqual(evidence["decision"], "READY_FOR_FIRST_GENERATION")
                    source = evidence["source"]
                    apply_explicit_territorial_source(
                        plan,
                        root_dir=ROOT,
                        reuse_run_id=str(source["run_id"]),
                        reuse_artifact_name=source["artifact_name"],
                        reuse_artifact_sha256=source["artifact_sha256"],
                        reuse_source_sha=source["source_commit"],
                    )
                    self.assertEqual(
                        plan["existing"]["territorial_source"]["run_id"],
                        source["run_id"],
                    )

        for name, territory_id in (
            ("Andalucía", "andalucia"),
            ("Comunidad de Madrid", "madrid"),
            ("Comunidad Valenciana", "comunidad_valenciana"),
        ):
            with self.subTest(blocked=name):
                row = rows[territory_id]
                self.assertEqual(row["production_authorization"], "AUTHORIZED")
                self.assertFalse(row["territorial_product_available"])
                self.assertNotIn("generation_preflight", row.get("evidence") or {})
                with self.assertRaisesRegex(ValueError, "sin generación habilitada"):
                    build_plan(
                        territory=name,
                        edition="2025",
                        execution_mode="reuse",
                        catalog=catalog_path,
                        root_dir=ROOT,
                        force_selected_algorithm=True,
                    )

    def test_first_generation_preflight_is_fail_closed_and_bound_to_source(self):
        catalog_path = ROOT / "configuracion/catalogo_preparacion.yaml"
        catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
        rows = {row["territory_id"]: row["editions"]["2025"] for row in catalog["territories"]}
        row = rows["la_rioja"]
        evidence_path = ROOT / row["evidence"]["generation_preflight"]
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        good = generation_enablement(
            root_dir=ROOT,
            contract_path=row["contract_path"],
            territory_id="la_rioja",
            edition="2025",
            certified_product_ready=False,
            preparation_evidence=row["preparation_evidence"],
            generation_preflight=evidence,
        )
        self.assertEqual(good, {"allowed": True, "route": "validated_pre_m04_topology"})

        broken = json.loads(json.dumps(evidence))
        broken["graph"]["global_components"] = 2
        blocked = generation_enablement(
            root_dir=ROOT,
            contract_path=row["contract_path"],
            territory_id="la_rioja",
            edition="2025",
            certified_product_ready=False,
            preparation_evidence=row["preparation_evidence"],
            generation_preflight=broken,
        )
        self.assertFalse(blocked["allowed"])
        self.assertIn("única componente", blocked["reason"])

        plan = build_plan(
            territory="La Rioja",
            edition="2025",
            execution_mode="reuse",
            catalog=catalog_path,
            root_dir=ROOT,
            force_selected_algorithm=True,
        )
        source = evidence["source"]
        with self.assertRaisesRegex(ValueError, "no coincide con el preflight"):
            apply_explicit_territorial_source(
                plan,
                root_dir=ROOT,
                reuse_run_id=str(source["run_id"]),
                reuse_artifact_name=source["artifact_name"],
                reuse_artifact_sha256="0" * 64,
                reuse_source_sha=source["source_commit"],
            )

    def test_generation_enablement_does_not_treat_generation_ready_labels_as_authority(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            contract = {
                "meta": {
                    "territory_id": "synthetic",
                    "status": "generation_ready",
                    "contract_level": "production_m01_m06",
                },
                "territory_contract": {"status": "generation_ready", "k_districts": 1},
                "modulos": {
                    "modulo_04_generar_semillas": {},
                    "modulo_05_optimizar_distritos": {},
                    "modulo_06_consolidar_distritos": {},
                },
            }
            path = root / "contract.yaml"
            path.write_text(yaml.safe_dump(contract), encoding="utf-8")
            gate = generation_enablement(
                root_dir=root,
                contract_path="contract.yaml",
                territory_id="synthetic",
                certified_product_ready=False,
            )
            self.assertFalse(gate["allowed"])

    def test_generation_enablement_requires_matching_partition_links(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            path = root / "contract.yaml"
            for territory_id, alteration, break_contract in (
                ("principado_de_asturias", "partition field", lambda c: c["modulos"]["modulo_04_generar_semillas"].update(municipality_field="CUMUN")),
                ("principado_de_asturias", "partition input", lambda c: c["modulos"]["modulo_04_generar_semillas"].update(in_geojson="source-B")),
            ):
                with self.subTest(territory=territory_id, alteration=alteration):
                    original = ROOT / f"territorios/{territory_id}/config/{territory_id}_2025.yaml"
                    contract = yaml.safe_load(original.read_text(encoding="utf-8"))
                    break_contract(contract)
                    path.write_text(yaml.safe_dump(contract), encoding="utf-8")
                    gate = generation_enablement(
                        root_dir=root,
                        contract_path="contract.yaml",
                        territory_id=territory_id,
                    )
                    self.assertFalse(gate["allowed"])

    def _strict_status(self, row: dict, *, status: str = "PASS") -> dict:
        return {
            **row,
            "status": status,
            "entrypoint": "gerrychain_50",
            "require_unique_hashes": True,
            "candidate_count_expected": 50,
            "candidate_count_valid": 50,
            "unique_candidate_hash_count": 50,
            "missing_candidate_hash_count": 0,
            "duplicate_candidate_hash_count": 0,
        }

    def test_promotion_requires_five_pass_and_one_failure_blocks_it(self):
        rows = build_matrix(
            MANIFEST,
            source_sha="d" * 40,
            campaign_instance="campaign-five",
            confirmation=CONFIRMATION,
        )["include"]
        summary = {
            "status": "PASS",
            "territories": [self._strict_status(row) for row in rows],
        }
        self.assertEqual(len(validate_campaign_summary_for_promotion(summary)), 5)
        summary["territories"][3]["status"] = "FAIL"
        with self.assertRaisesRegex(ValueError, "no promocionable"):
            validate_campaign_summary_for_promotion(summary)

    def test_five_releases_namespaces_and_galleries_are_distinct(self):
        rows = build_matrix(
            MANIFEST,
            source_sha="e" * 40,
            campaign_instance="campaign-five",
            confirmation=CONFIRMATION,
        )["include"]
        releases = []
        for index, row in enumerate(rows, start=1):
            release = release_identity(
                campaign_instance="campaign-five",
                slot=row["slot"],
                territory_id=row["territory_id"],
                asset_sha256=f"{index:064x}",
            )
            release["namespace"] = row["namespace"]
            release["gallery"] = f"{row['territory_id']}/{release['release_tag']}"
            releases.append(release)
        matrix = publication_matrix(releases)["include"]
        self.assertEqual(len(matrix), 5)
        self.assertEqual(len({row["release_tag"] for row in matrix}), 5)
        self.assertEqual(len({row["namespace"] for row in matrix}), 5)
        self.assertEqual(len({row["gallery"] for row in matrix}), 5)

    def test_publishing_one_ensemble_preserves_existing_territories(self):
        def entry(territory: str, ensemble: str, asset_id: int) -> dict:
            return {
                "id": f"ensemble-{territory}-{ensemble}",
                "asset_type": "ensemble_archive",
                "source_type": "release_asset",
                "immutable_location": f"github-release-asset://jfmurciego/DiputadodeDistrito/{asset_id}",
                "repository": "jfmurciego/DiputadodeDistrito",
                "asset_id": asset_id,
                "asset_name": f"{ensemble}.zip",
                "release_tag": ensemble,
                "sha256": f"{asset_id:064x}"[-64:],
                "kind": "ensemble",
                "territory_id": territory,
                "territory_label": territory,
                "ensemble_id": ensemble,
                "candidate_count_expected": 50,
                "candidate_count_valid": 50,
                "publication_status": "PUBLICABLE",
            }

        first = entry("aragon", "ensemble-aragon", 1001)
        second = entry("galicia", "ensemble-galicia", 1002)
        base = {
            "schema": "ddd.viewer-publication-registry/2.0",
            "products": [],
            "ensembles": [first],
        }
        candidate = make_candidate(base, [second])
        self.assertEqual(
            {row["territory_id"] for row in candidate["ensembles"]},
            {"aragon", "galicia"},
        )

    def test_synthetic_gallery_packages_in_existing_ensemble_format(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            bundle = root / "bundle"
            candidate_dir = bundle / "candidates"
            summary_dir = bundle / "summary"
            gallery_dir = bundle / "gallery"
            candidate_dir.mkdir(parents=True)
            summary_dir.mkdir(parents=True)
            gallery_dir.mkdir(parents=True)
            gallery_dir.joinpath("index.html").write_text(
                "<!doctype html><title>synthetic</title>", encoding="utf-8"
            )
            candidates = []
            for index in range(1, 51):
                seed = 1000 + index
                name = f"candidate_{index:03d}_seed_{seed}.geojson.zip"
                geo = {
                    "type": "FeatureCollection",
                    "features": [{
                        "type": "Feature",
                        "properties": {"district_id": "1"},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[-3.0, 40.0], [-2.9, 40.0], [-2.9, 40.1], [-3.0, 40.0]]],
                        },
                    }],
                }
                candidate_path = candidate_dir / name
                with zipfile.ZipFile(candidate_path, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr("candidate.geojson", json.dumps(geo))
                candidates.append({
                    "index": index,
                    "seed": seed,
                    "assignment_hash": f"{index:064x}",
                    "geojson": name,
                    "sha256": sha256(candidate_path),
                })
            (candidate_dir / "portfolio.json").write_text(
                json.dumps({
                    "candidate_count": 50,
                    "unique_candidate_count": 50,
                    "candidates": candidates,
                }),
                encoding="utf-8",
            )
            (summary_dir / "campaign_status.json").write_text(
                json.dumps({
                    "campaign_instance": "campaign-synthetic",
                    "slot": "01",
                    "territory_id": "aragon",
                    "territory_name": "Aragón",
                    "status": "PASS",
                    "entrypoint": "gerrychain_50",
                    "require_unique_hashes": True,
                    "candidate_count_expected": 50,
                    "candidate_count_valid": 50,
                    "unique_candidate_hash_count": 50,
                    "missing_candidate_hash_count": 0,
                    "duplicate_candidate_hash_count": 0,
                }),
                encoding="utf-8",
            )
            output = root / "ensemble.zip"
            descriptor = package_campaign_gallery(
                bundle,
                output,
                campaign_instance="campaign-synthetic",
                expected_districts=1,
            )
            self.assertTrue(output.is_file())
            self.assertEqual(descriptor["candidate_count_valid"], 50)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("site/data/summary.json", names)
                self.assertIn("site/index.html", names)
                self.assertEqual(
                    len([name for name in names if name.startswith("site/assets/") and name.endswith(".geojson")]),
                    50,
                )
                summary = json.loads(archive.read("site/data/summary.json"))
                self.assertEqual(summary["territory_id"], "aragon")
                self.assertEqual(summary["candidate_count_valid"], 50)
                self.assertEqual(len(summary["candidates"]), 50)

    def _make_portfolio_bundle(self, root: Path, *, count: int = 50, duplicate_hash: bool = False) -> Path:
        candidate_dir = root / "portfolio"
        candidate_dir.mkdir(parents=True, exist_ok=True)
        candidates = []
        for index in range(1, count + 1):
            seed = 20260000 + index
            name = f"candidate_{index:03d}_seed_{seed}.geojson.zip"
            geo = {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"district_id": "1"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[-5.9, 43.1], [-5.8, 43.1], [-5.8, 43.2], [-5.9, 43.1]]],
                    },
                }],
            }
            path = candidate_dir / name
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("candidate.geojson", json.dumps(geo))
            assignment = f"{index:064x}"
            if duplicate_hash and index == count:
                assignment = f"{1:064x}"
            candidates.append({
                "index": index,
                "seed": seed,
                "assignment_hash": assignment,
                "geojson": name,
                "sha256": sha256(path),
            })
        (candidate_dir / "portfolio.json").write_text(
            json.dumps({
                "schema": "ddd.m05-gerrychain-portfolio/1.0",
                "candidate_count": count,
                "unique_candidate_count": len({row["assignment_hash"] for row in candidates}),
                "candidates": candidates,
            }),
            encoding="utf-8",
        )
        return candidate_dir

    def test_portfolio_artifact_identity_rejects_different_or_corrupt_source(self):
        metadata = {
            "id": 10765532132,
            "name": "ddd-state-35889595424-M05-campaign-35889595424-1--02--principado_de_asturias",
            "digest": "sha256:" + "a" * 64,
            "expired": False,
            "workflow_run": {
                "id": 35889595424,
                "head_sha": "b" * 40,
            },
        }
        validate_portfolio_artifact_identity(
            metadata,
            run_id=35889595424,
            artifact_id=10765532132,
            artifact_name=metadata["name"],
            artifact_sha256="a" * 64,
            source_sha="b" * 40,
        )
        wrong = dict(metadata)
        wrong["name"] = "ddd-state-35889595424-M06-wrong"
        with self.assertRaisesRegex(ValueError, "Identidad del portfolio histórico no coincide"):
            validate_portfolio_artifact_identity(
                wrong,
                run_id=35889595424,
                artifact_id=10765532132,
                artifact_name=metadata["name"],
                artifact_sha256="a" * 64,
                source_sha="b" * 40,
            )
        corrupt = dict(metadata)
        corrupt["digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "artifact_sha256"):
            validate_portfolio_artifact_identity(
                corrupt,
                run_id=35889595424,
                artifact_id=10765532132,
                artifact_name=metadata["name"],
                artifact_sha256="a" * 64,
                source_sha="b" * 40,
            )

    def test_historical_false_fail_is_avoided_by_reading_m05_portfolio_not_m06(self):
        namespace = "campaign-35889595424-1--02--principado_de_asturias"
        self.assertEqual(
            portfolio_artifact_name(35889595424, namespace),
            "ddd-state-35889595424-M05-campaign-35889595424-1--02--principado_de_asturias",
        )
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            m05 = self._make_portfolio_bundle(root / "m05")
            (root / "m06").mkdir()
            result = validate_portfolio_bundle(m05, expected_districts=1)
            self.assertTrue(result["valid"])
            self.assertEqual(result["verified_candidate_zip_count"], 50)
            self.assertFalse(any((root / "m06").rglob("portfolio.json")))

    def test_portfolio_bundle_blocks_incomplete_and_duplicate_hashes(self):
        with tempfile.TemporaryDirectory() as raw:
            incomplete = self._make_portfolio_bundle(Path(raw) / "incomplete", count=49)
            with self.assertRaisesRegex(ValueError, "portfolio GerryChain 50 inválido"):
                validate_portfolio_bundle(incomplete, expected_districts=1)
        with tempfile.TemporaryDirectory() as raw:
            duplicate = self._make_portfolio_bundle(Path(raw) / "duplicate", duplicate_hash=True)
            with self.assertRaisesRegex(ValueError, "portfolio GerryChain 50 inválido"):
                validate_portfolio_bundle(duplicate, expected_districts=1)

    def test_portfolio_bundle_blocks_zip_sha_mismatch(self):
        with tempfile.TemporaryDirectory() as raw:
            bundle = self._make_portfolio_bundle(Path(raw))
            portfolio_path = bundle / "portfolio.json"
            portfolio = json.loads(portfolio_path.read_text(encoding="utf-8"))
            portfolio["candidates"][0]["sha256"] = "0" * 64
            portfolio_path.write_text(json.dumps(portfolio), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 del ZIP no coincide"):
                validate_portfolio_bundle(bundle, expected_districts=1)

    def test_existing_campaign_manager_recovers_portfolio_without_recalculation(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("name: 0 · Gestor de Campañas", manager)
        self.assertIn("Recuperar portfolio existente", manager)
        self.assertIn("portfolio_artifact_id:", manager)
        self.assertIn("portfolio_artifact_sha256:", manager)
        self.assertIn("validate_portfolio_artifact_identity", manager)
        self.assertIn("validate_portfolio_bundle", manager)
        self.assertIn("resolver_release_asset.py release", manager)
        self.assertIn("uses: ./.github/workflows/_reutilizable-publicar-sitio.yml", manager)
        self.assertIn("ensemble_release_tag:", manager)
        recovery = manager[manager.index("  recuperar_portfolio:"):manager.index("  resumen:")]
        self.assertNotIn("ejecucion-completa-proyecto.yml", recovery)
        self.assertNotIn("produccion-distritos.yml", recovery)
        self.assertNotIn("actions/deploy-pages@", recovery)

    def test_publication_jobs_are_after_five_pass_and_skipped_on_pull_request(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        summary_pos = manager.index("  resumen:")
        promote_pos = manager.index("  promover_galerias:")
        publish_pos = manager.index("  publicar_galerias:")
        self.assertLess(summary_pos, promote_pos)
        self.assertLess(promote_pos, publish_pos)
        self.assertIn("needs: [preparar, resumen]", manager)
        self.assertIn("needs.resumen.result == 'success'", manager)
        self.assertIn("validate_campaign_summary_for_promotion", manager)
        self.assertIn("uses: ./.github/workflows/_reutilizable-publicar-sitio.yml", manager)
        self.assertIn("group: ddd-pages-prod", (ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml").read_text(encoding="utf-8"))
        self.assertNotIn("actions/deploy-pages@", manager)
        self.assertIn("github.event_name == 'workflow_dispatch'", manager)
        self.assertIn("test \"${{ needs.publicar_galerias.result }}\" = success", manager)

    def test_campaign_propagates_accredited_ensemble_sha_to_common_publisher(self):
        manager = WORKFLOW.read_text(encoding="utf-8")
        publisher = (
            ROOT / ".github/workflows/_reutilizable-publicar-sitio.yml"
        ).read_text(encoding="utf-8")
        self.assertIn('expected_sha="$(jq -r .sha256 "$descriptor")"', manager)
        self.assertIn("ensemble_sha256: ${{ matrix.sha256 }}", manager)
        self.assertIn("ensemble_sha256:", publisher)
        self.assertIn("ENSEMBLE_SHA256: ${{ inputs.ensemble_sha256 || '' }}", publisher)

    def test_workflows_parse(self):
        for path in (
            WORKFLOW,
            ORCH,
            ROOT / ".github/workflows/produccion-distritos.yml",
            ROOT / ".github/workflows/incorporacion-resultados-electorales.yml",
            ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml",
            ROOT / ".github/workflows/_reutilizable-incorporacion-electoral.yml",
            ROOT / ".github/workflows/_reutilizable-puerta-validacion.yml",
        ):
            parsed = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
            self.assertIsInstance(parsed, dict, path)


if __name__ == "__main__":
    unittest.main()
