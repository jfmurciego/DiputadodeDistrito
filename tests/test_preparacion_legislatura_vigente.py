from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas.identidad_fuentes_legislatura import (
    electoral_identity,
    geometric_reuse_compatible,
    territorial_identity,
)
from herramientas.promover_catalogo_tras_preparacion import promote as promote_territorial
from herramientas.registrar_par_fuentes_legislatura import (
    PAIR_SCHEMA,
    PreparedSourcePairBlock,
    build_pair,
)
from herramientas.resolver_fuentes_territorio import build_declaration
from herramientas.resolver_preparacion_legislatura import resolve, validate_matrix

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-legislatura-vigente.yml"
MATRIX = ROOT / "configuracion/preparacion_legislatura_vigente.yaml"
REGISTRY = ROOT / "configuracion/registro_electoral.yaml"
TEMPORAL = ROOT / "configuracion/evidencia_disponibilidad_fuentes_territoriales_2026-09-30.json"
CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"


class CurrentLegislaturePreparationTests(unittest.TestCase):
    def test_matrix_has_exactly_19_current_elections(self):
        rows = validate_matrix(ROOT)
        registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["territories"]
        self.assertEqual(len(rows), 19)
        self.assertEqual({r["territory_id"] for r in rows}, set(registry))
        for row in rows:
            registered = registry[row["territory_id"]]
            self.assertEqual(row["election_id"], registered["election_id"])
            self.assertEqual(str(row["election_date"]), str(registered["election_date"]))

    def test_2023_and_2024_require_contemporary_population_and_sectioning(self):
        for row in validate_matrix(ROOT):
            election_year = int(str(row["election_date"])[:4])
            if election_year not in {2023, 2024}:
                continue
            territorial = row["territorial"]
            with self.subTest(territory=row["territory_id"]):
                self.assertEqual(territorial["population_required_year"], election_year)
                self.assertEqual(territorial["population_selected_year"], election_year)
                self.assertEqual(territorial["section_required_year"], election_year)
                self.assertEqual(territorial["section_selected_year"], election_year)
                self.assertEqual(territorial["population_lag_years"], 0)
                self.assertEqual(territorial["section_lag_years"], 0)

    def test_2026_uses_population_2025_but_sectioning_2026(self):
        rows = [
            r for r in validate_matrix(ROOT)
            if str(r["election_date"]).startswith("2026-")
        ]
        self.assertEqual(
            {r["territory_id"] for r in rows},
            {"andalucia", "aragon", "castilla_y_leon"},
        )
        for row in rows:
            territorial = row["territorial"]
            with self.subTest(territory=row["territory_id"]):
                self.assertEqual(territorial["population_required_year"], 2026)
                self.assertEqual(territorial["population_selected_year"], 2025)
                self.assertEqual(territorial["population_lag_years"], 1)
                self.assertEqual(territorial["population_reference_date"], "2025-01-01")
                self.assertEqual(territorial["section_required_year"], 2026)
                self.assertEqual(territorial["section_selected_year"], 2026)
                self.assertEqual(territorial["section_lag_years"], 0)
                self.assertEqual(territorial["section_reference_label"], "Secciones_2026")
                self.assertEqual(
                    territorial["temporal_evidence"],
                    "configuracion/evidencia_disponibilidad_fuentes_territoriales_2026-09-30.json",
                )

    def test_temporal_evidence_preserves_query_response_date_and_digest(self):
        evidence = json.loads(TEMPORAL.read_text(encoding="utf-8"))
        self.assertEqual(evidence["provider"], "Instituto Nacional de Estadística")
        self.assertTrue(evidence["checked_at"])
        population = evidence["checks"]["population_by_section"]
        sections = evidence["checks"]["census_sections"]
        for item in (population, sections):
            self.assertTrue(item["query"].startswith("https://"))
            self.assertTrue(item["preserved_response"])
            self.assertEqual(
                item["response_sha256"],
                hashlib.sha256(item["preserved_response"].encode("utf-8")).hexdigest(),
            )
        self.assertNotIn(2026, population["available_years"])
        self.assertEqual(population["latest_available_year"], 2025)
        self.assertIn(2026, sections["available_years"])
        self.assertEqual(sections["latest_available_year"], 2026)

    def test_temporal_substitution_without_preserved_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            shutil.copy2(MATRIX, root / "configuracion/preparacion_legislatura_vigente.yaml")
            shutil.copy2(REGISTRY, root / "configuracion/registro_electoral.yaml")
            with self.assertRaisesRegex(ValueError, "TEMPORAL_EVIDENCE_MISSING"):
                validate_matrix(root)

    def test_temporal_response_digest_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            shutil.copy2(MATRIX, root / "configuracion/preparacion_legislatura_vigente.yaml")
            shutil.copy2(REGISTRY, root / "configuracion/registro_electoral.yaml")
            evidence = json.loads(TEMPORAL.read_text(encoding="utf-8"))
            evidence["checks"]["population_by_section"]["preserved_response"] += " alterado"
            target = root / "configuracion/evidencia_disponibilidad_fuentes_territoriales_2026-09-30.json"
            target.write_text(json.dumps(evidence), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "TEMPORAL_EVIDENCE_DIGEST_MISMATCH"):
                validate_matrix(root)

    def test_extremadura_2025_is_exact_but_electoral_stays_provisional(self):
        plan = resolve(ROOT, "Extremadura")["plans"][0]
        self.assertEqual(plan["population_year_selected"], 2025)
        self.assertEqual(plan["section_year_selected"], 2025)
        self.assertEqual(plan["territorial_action"], "ACQUIRE")
        self.assertEqual(plan["territorial_reason"], "TERRITORIAL_COMPATIBILITY_REPORT_MISSING")
        self.assertEqual(plan["electoral_action"], "BLOCKED_PROVISIONAL")
        self.assertEqual(plan["definitive_gap"]["source_candidate_votes"], 522418)
        self.assertEqual(plan["definitive_gap"]["definitive_candidate_votes"], 524837)
        self.assertEqual(plan["definitive_gap"]["gap_candidate_votes"], 2419)

    def test_andalucia_preserves_provisional_gap_and_requires_2026_sectioning(self):
        plan = resolve(ROOT, "Andalucía")["plans"][0]
        self.assertEqual(plan["population_year_selected"], 2025)
        self.assertEqual(plan["section_year_selected"], 2026)
        self.assertEqual(plan["territorial_action"], "ACQUIRE")
        self.assertEqual(plan["electoral_action"], "BLOCKED_PROVISIONAL")
        self.assertEqual(plan["definitive_gap"]["source_candidate_votes"], 4128575)
        self.assertEqual(plan["definitive_gap"]["definitive_candidate_votes"], 4157539)
        self.assertEqual(plan["definitive_gap"]["gap_candidate_votes"], 28964)

    def test_aragon_source_receipt_is_repaired_without_reacquiring_historical_product(self):
        plan = resolve(ROOT, "Aragón")["plans"][0]
        candidate = plan["territorial_candidate"]
        self.assertEqual(candidate["run_id"], 35728613828)
        self.assertEqual(
            candidate["artifact_name"],
            "ddd-source-package-aragon-2025-35728613828",
        )
        self.assertEqual(
            candidate["artifact_sha256"],
            "df7222525fc43943859c41bc653e8b4ca320e9c47f602dc5cd6e8f93cfb0bec2",
        )
        self.assertEqual(candidate["reason"], "TERRITORIAL_COMPATIBILITY_REPORT_MISSING")
        self.assertEqual(plan["territorial_action"], "ACQUIRE")
        self.assertEqual(plan["electoral_action"], "REUSE")
        state = next(
            r for r in yaml.safe_load(CATALOG.read_text(encoding="utf-8"))["territories"]
            if r["territory_id"] == "aragon"
        )["editions"]["2025"]
        self.assertTrue(state["territorial_product_available"])
        self.assertEqual(state["last_valid_checkpoint"], {"run_id": 36321736287, "stage": "M06"})
        self.assertNotIn("stage", state["preparation_evidence"])

    def test_castilla_y_leon_source_receipt_is_repaired_without_erasing_historical_product(self):
        plan = resolve(ROOT, "Castilla y León")["plans"][0]
        candidate = plan["territorial_candidate"]
        self.assertEqual(candidate["run_id"], 35610439734)
        self.assertEqual(
            candidate["artifact_name"],
            "ddd-source-package-castilla_y_leon-2025-35610439734",
        )
        self.assertEqual(candidate["reason"], "TERRITORIAL_COMPATIBILITY_REPORT_MISSING")
        self.assertEqual(plan["territorial_action"], "ACQUIRE")
        self.assertEqual(plan["electoral_action"], "ACQUIRE")
        self.assertEqual(
            plan["electoral_candidate"]["reason"],
            "ELECTORAL_PACKAGE_IDENTITY_NOT_DURABLE",
        )
        state = next(
            r for r in yaml.safe_load(CATALOG.read_text(encoding="utf-8"))["territories"]
            if r["territory_id"] == "castilla_y_leon"
        )["editions"]["2025"]
        self.assertTrue(state["territorial_product_available"])
        self.assertEqual(state["last_valid_checkpoint"], {"run_id": 35889595424, "stage": "M06"})
        self.assertNotIn("stage", state["preparation_evidence"])

    def test_historical_product_source_lineage_preserves_direct_producer_observation(self):
        cases = {
            "aragon": (36321736287, 35728613828, "f13310ea23ab914d35ca2f08e05eb2d96820a702ca9d50e772a1e16ec99a7be2"),
            "castilla_y_leon": (35889595424, 35610439734, "37eecb1a37e7bde56246a04866b09056e73088c91064043604d9ba22bf015752"),
        }
        for territory, (product_run, source_run, package_sha) in cases.items():
            path = ROOT / f"territorios/{territory}/evidencia/linaje_producto_territorial/{product_run}.json"
            lineage = json.loads(path.read_text(encoding="utf-8"))
            observation = lineage["producer_observation"]
            with self.subTest(territory=territory):
                self.assertEqual(lineage["schema"], "ddd.territorial-product-source-lineage/1.0")
                self.assertEqual(observation["observed_source_package_run_id"], source_run)
                self.assertEqual(observation["observed_source_execution_package_sha256"], package_sha)
                self.assertEqual(
                    observation["response_sha256"],
                    hashlib.sha256(observation["preserved_response"].encode("utf-8")).hexdigest(),
                )

    def test_partial_acquisition_reuses_electoral_but_replaces_wrong_year_territorial(self):
        for territory in ("Comunidad de Madrid", "Galicia"):
            plan = resolve(ROOT, territory)["plans"][0]
            with self.subTest(territory=territory):
                self.assertEqual(plan["territorial_action"], "ACQUIRE")
                self.assertEqual(plan["electoral_action"], "REUSE")

    def test_both_sources_are_acquired_when_both_are_missing_or_wrong(self):
        plan = resolve(ROOT, "Canarias")["plans"][0]
        self.assertEqual(plan["territorial_action"], "ACQUIRE")
        self.assertEqual(plan["electoral_action"], "ACQUIRE")

    def test_population_and_section_years_are_separate_from_project_edition(self):
        declaration = build_declaration(
            "Aragón",
            2025,
            population_year=2025,
            section_year=2026,
        )
        territory = declaration["territory"]
        self.assertEqual(territory["edition"], 2025)
        self.assertEqual(territory["population_year"], 2025)
        self.assertEqual(territory["section_year"], 2026)
        self.assertNotIn("source_year", territory)
        self.assertEqual(
            declaration["source_bindings"]["secciones_censales"]["materialized_path"],
            "inputs/seccionado_2026.zip",
        )
        legacy_default = build_declaration("Comunidad de Madrid", 2025)
        self.assertEqual(legacy_default["territory"]["source_year"], 2025)

    def test_current_legislature_workflow_uses_codauto_labels_and_resolves_them(self):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        triggers = workflow.get("on") or workflow.get(True)
        options = triggers["workflow_dispatch"]["inputs"]["territory"]["options"]
        self.assertEqual(options[0], "Todos")
        self.assertEqual(options[1], "01 · Andalucía")
        self.assertEqual(options[7], "07 · Castilla y León")
        self.assertEqual(options[-1], "19 · Melilla")
        plain = resolve(ROOT, "Aragón")
        coded = resolve(ROOT, "02 · Aragón")
        self.assertEqual(coded, plain)

    def test_workflow_keeps_01_and_03_independent_and_never_runs_all_19(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("uses: ./.github/workflows/preparacion-fuentes.yml", workflow)
        self.assertIn("uses: ./.github/workflows/preparacion-resultados-electorales.yml", workflow)
        self.assertIn("prepare_one exige un territorio concreto", workflow)
        self.assertNotIn("ejecucion-completa-proyecto.yml", workflow)
        self.assertNotIn("_reutilizable-generacion-territorial.yml", workflow)
        self.assertNotIn("incorpor", workflow.lower())
        self.assertNotIn("publicar visor", workflow.lower())

    def test_workflow_requires_durable_pair_after_effective_preparations(self):
        data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        pair_job = data["jobs"]["registrar_par"]
        self.assertEqual(pair_job["needs"], ["planificar", "territorial", "electoral"])
        self.assertIn("needs.territorial.result != 'failure'", str(pair_job["if"]))
        self.assertIn("needs.electoral.result != 'failure'", str(pair_job["if"]))
        result_job = data["jobs"]["resultado"]
        self.assertIn("registrar_par", result_job["needs"])
        terminal = "\n".join(step.get("run", "") for step in result_job["steps"])
        self.assertIn("PAIR_RESULT", terminal)
        self.assertIn("Las preparaciones terminaron sin un par durable válido", terminal)

    def test_partial_preparation_cannot_materialize_pair(self):
        remote = {
            "schema": "ddd.prepared-source-pair-artifact-verification/1.0",
        }
        with self.assertRaisesRegex(PreparedSourcePairBlock, "fuente territorial efectiva no acreditada"):
            build_pair(root_dir=ROOT, territory="Canarias", remote_verification=remote)

    def test_territorial_identity_change_blocks_geometric_reuse(self):
        historical = territorial_identity(
            territory_id="demo",
            edition="2025",
            population_year=2025,
            section_year=2025,
            package_sha256="a" * 64,
        )
        current = territorial_identity(
            territory_id="demo",
            edition="2025",
            population_year=2025,
            section_year=2026,
            package_sha256="b" * 64,
        )
        self.assertFalse(
            geometric_reuse_compatible(
                product_territorial_identity_sha256=historical["territorial_identity_sha256"],
                current_territorial_identity_sha256=current["territorial_identity_sha256"],
            )
        )

    def test_electoral_only_change_preserves_geometric_compatibility(self):
        territorial = territorial_identity(
            territory_id="demo",
            edition="2025",
            population_year=2025,
            section_year=2025,
            package_sha256="a" * 64,
        )
        old_electoral = electoral_identity(
            territory_id="demo",
            edition="2025",
            election_id="demo_2023",
            election_date="2023-05-28",
            artifact_sha256="b" * 64,
        )
        new_electoral = electoral_identity(
            territory_id="demo",
            edition="2025",
            election_id="demo_2027",
            election_date="2027-05-28",
            artifact_sha256="c" * 64,
        )
        self.assertNotEqual(
            old_electoral["electoral_identity_sha256"],
            new_electoral["electoral_identity_sha256"],
        )
        self.assertTrue(
            geometric_reuse_compatible(
                product_territorial_identity_sha256=territorial["territorial_identity_sha256"],
                current_territorial_identity_sha256=territorial["territorial_identity_sha256"],
            )
        )

    def test_failed_source_promotion_preserves_previous_product_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            (root / "territorios/demo/config").mkdir(parents=True)
            product = root / "territorios/demo/evidencia/catalogo/territorial_product_2025.json"
            product.parent.mkdir(parents=True)
            product.write_text('{"schema":"ddd.catalog-evidence/1.0","kind":"territorial_product"}\n', encoding="utf-8")
            declaration = root / "territorios/demo/config/fuentes_oficiales.yaml"
            declaration.write_text(
                "territory:\n  id: demo\n  business_name: Demo\n  edition: 2025\n  source_year: 2025\n",
                encoding="utf-8",
            )
            catalog = {
                "schema": "ddd-preparation-catalog/1.1",
                "territories": [{
                    "territory_id": "demo",
                    "name": "Demo",
                    "editions": {"2025": {
                        "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
                        "territorial_sources_prepared": True,
                        "territorial_product_available": True,
                        "evidence": {"territorial_product": "territorios/demo/evidencia/catalogo/territorial_product_2025.json"},
                    }},
                }],
            }
            catalog_path = root / "configuracion/catalogo_preparacion.yaml"
            catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False), encoding="utf-8")
            before_product = product.read_bytes()
            before_catalog = catalog_path.read_bytes()
            invalid_package = root / "invalid-package"
            invalid_package.mkdir()
            with self.assertRaises(ValueError):
                promote_territorial(
                    root_dir=root,
                    territory_id="demo",
                    edition="2025",
                    package=invalid_package,
                    source_declaration=declaration,
                    run_id=999,
                    artifact_name="ddd-source-package-demo-2025-999",
                    artifact_sha256="d" * 64,
                    source_commit="e" * 40,
                )
            self.assertEqual(product.read_bytes(), before_product)
            self.assertEqual(catalog_path.read_bytes(), before_catalog)

    def test_synthetic_pair_contains_effective_receipts_and_separate_geometry_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir()
            temporal = root / "configuracion/temporal.json"
            temporal.write_text('{"ok":true}\n', encoding="utf-8")
            temporal_sha = hashlib.sha256(temporal.read_bytes()).hexdigest()
            (root / "configuracion/catalogo_preparacion.yaml").write_text(
                yaml.safe_dump({
                    "territories": [{
                        "territory_id": "demo",
                        "editions": {"2025": {
                            "territorial_product_available": False,
                            "evidence": {},
                        }},
                    }]
                }),
                encoding="utf-8",
            )
            compatibility_identity = "f" * 64
            territorial = territorial_identity(
                territory_id="demo",
                edition="2025",
                population_year=2025,
                section_year=2026,
                package_sha256="a" * 64,
                compatibility_identity_sha256=compatibility_identity,
            )
            synthetic_plan = {
                "plans": [{
                    "territory_id": "demo",
                    "name": "Demo",
                    "project_edition": "2025",
                    "election_id": "demo_2026",
                    "election_date": "2026-01-01",
                    "population_year_required": 2026,
                    "population_year_selected": 2025,
                    "population_reference_date": "2025-01-01",
                    "section_year_required": 2026,
                    "section_year_selected": 2026,
                    "section_reference_label": "Secciones_2026",
                    "temporal_evidence": {
                        "path": "configuracion/temporal.json",
                        "sha256": temporal_sha,
                        "provider": "INE",
                        "checked_at": "2026-09-30T10:51:00+02:00",
                    },
                    "territorial_action": "REUSE_TEMPORAL_SUBSTITUTION",
                    "electoral_action": "REUSE",
                    "territorial_candidate": {
                        "run_id": 10,
                        "artifact_name": "ddd-source-package-demo-2025-10",
                        "artifact_sha256": "b" * 64,
                        "package_sha256": "a" * 64,
                        "source_commit": "c" * 40,
                        "declaration": "territorios/demo/config/fuentes.yaml",
                        "receipt_path": "territorios/demo/evidencia/fuentes/receipt.json",
                        "territorial_identity_sha256": territorial["territorial_identity_sha256"],
                        "compatibility_report_member": "compatibilidad_poblacion_seccionado.json",
                        "compatibility_report_sha256": "e" * 64,
                        "compatibility_identity_sha256": compatibility_identity,
                    },
                    "electoral_candidate": {
                        "run_id": 20,
                        "artifact_name": "ddd-electoral-package-demo-2025-20",
                        "artifact_sha256": "d" * 64,
                        "source_commit": "e" * 40,
                        "receipt": "territorios/demo/evidencia/electoral/receipt.json",
                        "provenance_reference": "configuracion/registro_electoral.yaml",
                    },
                }]
            }
            remote = {
                "schema": "ddd.prepared-source-pair-artifact-verification/1.0",
                "territorial": {
                    "run_id": 10, "artifact_id": 101,
                    "artifact_name": "ddd-source-package-demo-2025-10",
                    "artifact_sha256": "b" * 64, "expired": False,
                },
                "electoral": {
                    "run_id": 20, "artifact_id": 202,
                    "artifact_name": "ddd-electoral-package-demo-2025-20",
                    "artifact_sha256": "d" * 64, "expired": False,
                },
            }
            with mock.patch(
                "herramientas.registrar_par_fuentes_legislatura.resolve",
                return_value=synthetic_plan,
            ):
                pair = build_pair(
                    root_dir=root,
                    territory="Demo",
                    remote_verification=remote,
                )
            self.assertEqual(pair["schema"], PAIR_SCHEMA)
            self.assertEqual(
                pair["geometric_compatibility_key"],
                territorial["territorial_identity_sha256"],
            )
            self.assertEqual(pair["references"]["population"]["year"], 2025)
            self.assertEqual(pair["references"]["sectioning"]["year"], 2026)
            self.assertEqual(pair["temporal_evidence"]["sha256"], temporal_sha)

    def test_plan_exposes_package_state_and_precise_reason_for_all_19(self):
        plans = resolve(ROOT, "Todos")["plans"]
        self.assertEqual(len(plans), 19)
        for plan in plans:
            with self.subTest(territory=plan["territory_id"]):
                self.assertIn(
                    plan["territorial_package_state"],
                    {"READY_REUSABLE", "ACQUIRE_REQUIRED"},
                )
                self.assertTrue(plan["territorial_reason"])
                self.assertIn(
                    plan["electoral_package_state"],
                    {"READY_REUSABLE", "ACQUIRE_REQUIRED", "BLOCKED_PROVISIONAL"},
                )
                self.assertTrue(plan["electoral_reason"])

    def test_remote_reuse_requires_complete_paginated_inventory(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("gh api --paginate --slurp", workflow)
        self.assertIn("total=\"$(jq -r '.total_count'", workflow)
        self.assertIn("received=\"$(jq -r '.artifacts|length'", workflow)
        self.assertIn("BLOCKED_DURABLE_INVENTORY", workflow)

    def test_matrix_does_not_invent_unknown_definitive_vote_gaps(self):
        matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
        for row in matrix["territories"]:
            electoral = row["electoral"]
            status = electoral.get("definitive_gap_status")
            if status in {"NOT_DECLARED", "NOT_EVALUATED"}:
                with self.subTest(territory=row["territory_id"]):
                    self.assertNotIn("gap_candidate_votes", electoral)
                    self.assertNotIn("definitive_candidate_votes", electoral)
                    self.assertNotIn("source_candidate_votes", electoral)


if __name__ == "__main__":
    unittest.main()
