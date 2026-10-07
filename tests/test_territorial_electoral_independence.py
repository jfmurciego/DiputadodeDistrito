from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas.resolver_activos_durables import DurableAssetBlock
from herramientas.resolver_ejecucion_completa import (
    build_plan,
    classify_prepared_pair_failure,
    resolve_publication_mode,
    select_territorial_for_prepared_pair,
)

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
WRITER = ROOT / "herramientas/escribir_manifest_ejecucion_completa.py"


def manifest_cmd(output: Path, *, completion: str, prep_e_result: str = "skipped",
                 prep_e_executed: str = "false", electoral_source_validation: str = "",
                 classification_result: str = "success",
                 territorial_product_validation: str = "VALIDADO",
                 incorporate_executed: str = "false") -> list[str]:
    activation_by_completion = {
        "SKIPPED_SOURCE_UNAVAILABLE": "TERRITORIAL_READY_ELECTORAL_PENDING",
        "SKIPPED_ELECTORAL_SOURCE_INVALID": "TERRITORIAL_READY_ELECTORAL_INVALID",
        "SKIPPED_INCOMPATIBLE_PAIR": "TERRITORIAL_READY_PAIR_INCOMPATIBLE",
        "SKIPPED_NO_ACCREDITED_PAIR": "TERRITORIAL_READY_ELECTORAL_PENDING",
    }
    return [
        sys.executable,
        str(WRITER),
        "--territory-id", "demo",
        "--territory-name", "Demo",
        "--edition", "2025",
        "--execution-mode", "reuse",
        "--optimization-algorithm", "Canónico",
        "--workflow-run-id", "999",
        "--source-sha", "a" * 40,
        "--publication-mode-requested", "electoral",
        "--publication-mode-effective", "electoral",
        "--electoral-classification-result", classification_result,
        "--electoral-activation-status", activation_by_completion.get(
            completion,
            "TERRITORIAL_READY_ELECTORAL_PENDING" if completion.startswith("SKIPPED_") else "FULL_PAIR_READY",
        ),
        "--electoral-completion-status", completion,
        "--electoral-skip-reason", "fixture source gap" if completion.startswith("SKIPPED_") else "",
        "--publish-requested", "false",
        "--prepare-territorial-result", "skipped",
        "--generate-result", "skipped",
        "--prepare-electoral-result", prep_e_result,
        "--incorporate-result", "skipped",
        "--publish-result", "skipped",
        "--prepare-territorial-executed", "false",
        "--generate-executed", "false",
        "--prepare-electoral-executed", prep_e_executed,
        "--incorporate-executed", incorporate_executed,
        "--territorial-source-validation", "VALIDADO",
        "--territorial-product-validation", territorial_product_validation,
        "--electoral-source-validation", electoral_source_validation,
        "--output", str(output),
    ]


class TerritorialElectoralIndependenceTests(unittest.TestCase):
    def test_r1_valid_territorial_missing_electoral_keeps_generation_and_delegates_to_03(self):
        plan = {
            "territory_id": "demo",
            "territory_name": "Demo",
            "edition": "2025",
            "contract_path": "demo.yaml",
            "run_prepare_territorial": False,
            "run_generate": True,
            "run_prepare_electoral": True,
            "run_incorporate": True,
            "existing": {"territorial_source": {"run_id": 101}},
        }
        current = {
            "plans": [{
                "electoral_action": "ACQUIRE",
                "electoral_admissibility": "NOT_ACCREDITED",
                "electoral_reason": "ELECTORAL_PACKAGE_MISSING",
            }]
        }
        with mock.patch(
            "herramientas.resolver_ejecucion_completa.resolve_current_legislature",
            return_value=current,
        ), mock.patch(
            "herramientas.resolver_eleccion_vigente.resolve",
            side_effect=AssertionError("03 debe conservar la autoridad de adquisición"),
        ) as premature_source_resolver:
            mode = resolve_publication_mode(plan, "electoral", root_dir=Path("."))
        premature_source_resolver.assert_not_called()

        self.assertEqual(mode, "electoral")
        self.assertTrue(plan["run_generate"])
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertTrue(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])
        self.assertEqual(plan["electoral_activation"]["execution"], "EXECUTE")
        self.assertEqual(plan["electoral_activation"]["completion_status"], "PENDING")

        workflow = yaml.load(ORCH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        source_gate = workflow["jobs"]["verificar_fuentes_preparadas"]
        self.assertIn("run_prepare_territorial == 'false'", source_gate["if"])
        gate_text = ORCH.read_text(encoding="utf-8").split(
            "  verificar_fuentes_preparadas:", 1
        )[1].split("  detectar_recuperacion_electoral:", 1)[0]
        self.assertIn("verify-territorial", gate_text)
        self.assertNotIn("verify_side electoral", gate_text)

    def test_r2_incompatible_pair_keeps_preferred_territorial_and_disables_electoral_jobs(self):
        preferred = {
            "territorial_identity_sha256": "a" * 64,
            "population_year": 2025,
            "section_year": 2026,
        }
        pair = {
            "territorial_source": {
                "territorial_identity_sha256": "b" * 64,
                "population_year": 2024,
                "section_year": 2026,
            }
        }
        temporal = {
            "plans": [{
                "population_year_selected": 2025,
                "section_year_selected": 2026,
            }]
        }
        with mock.patch(
            "herramientas.resolver_ejecucion_completa.resolve_current_legislature",
            return_value=temporal,
        ):
            selected = select_territorial_for_prepared_pair(
                {"territory_name": "Demo"},
                preferred_territorial=preferred,
                pair=pair,
                root_dir=Path("."),
            )
        self.assertEqual(selected["status"], "TERRITORIAL_READY_PAIR_INCOMPATIBLE")
        self.assertEqual(selected["selected_identity_sha256"], "a" * 64)

        workflow = yaml.load(ORCH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        self.assertIn(
            "needs.clasificar_electoral.outputs.execution == 'EXECUTE'",
            workflow["jobs"]["incorporar"]["if"],
        )
        self.assertIn(
            "needs.clasificar_electoral.outputs.execution == 'SKIP'",
            workflow["jobs"]["actualizar_estado"]["if"],
        )

    def test_r3_invalid_territorial_remains_fail_closed_before_generation(self):
        state = {
            "territory_id": "demo",
            "name": "Demo",
            "contract_path": "demo.yaml",
            "territorial_sources_prepared": True,
            "territorial_product_available": False,
            "electoral_source_prepared": True,
            "electoral_product_available": False,
            "territorial_certification": "NOT_CERTIFIED",
            "preparation_evidence": {
                "run_id": 101,
                "artifact_name": "ddd-source-package-demo-2025-101",
                "artifact_sha256": "a" * 64,
                "package_sha256": "b" * 64,
                "compatibility_identity_sha256": "c" * 64,
                "population_year": 2025,
                "section_year": 2026,
            },
            "evidence": {},
            "last_valid_checkpoint": None,
        }
        with mock.patch(
            "herramientas.resolver_ejecucion_completa._core.lookup",
            return_value=state,
        ), mock.patch(
            "herramientas.resolver_ejecucion_completa._core._registered_election_id",
            return_value=None,
        ), mock.patch(
            "herramientas.resolver_ejecucion_completa.validate_durable_assets",
            side_effect=DurableAssetBlock("DURABLE_ASSET_INVALID: territorial"),
        ):
            with self.assertRaisesRegex(ValueError, "CONTINUE_DURABLE_BLOCK"):
                build_plan(
                    territory="Demo",
                    edition="2025",
                    execution_mode="reuse",
                    catalog=Path("unused.yaml"),
                    root_dir=Path("."),
                )

    def test_r4_certified_m06_source_gap_is_successful_territorial_completion(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "manifest.json"
            completed = subprocess.run(
                manifest_cmd(output, completion="SKIPPED_SOURCE_UNAVAILABLE"),
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "SUCCESS")
        self.assertEqual(manifest["completion_status"], "TERRITORIAL_COMPLETE")
        self.assertEqual(manifest["territorial_status"], "CERTIFIED")
        self.assertEqual(manifest["electoral_status"], "SKIPPED_SOURCE_UNAVAILABLE")
        self.assertEqual(len(manifest["skipped_source_gap_phases"]), 2)

    def test_r3b_electoral_source_block_after_03_is_successful_territorial_completion(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "manifest.json"
            completed = subprocess.run(
                manifest_cmd(
                    output,
                    completion="SKIPPED_ELECTORAL_SOURCE_INVALID",
                    prep_e_result="success",
                    prep_e_executed="true",
                ),
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "SUCCESS")
        self.assertEqual(manifest["completion_status"], "TERRITORIAL_COMPLETE")
        self.assertEqual(manifest["territorial_status"], "CERTIFIED")
        self.assertEqual(
            manifest["electoral_status"],
            "SKIPPED_ELECTORAL_SOURCE_INVALID",
        )

    def test_r5_executed_electoral_failure_is_still_failed(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "manifest.json"
            completed = subprocess.run(
                manifest_cmd(
                    output,
                    completion="SKIPPED_ELECTORAL_SOURCE_INVALID",
                    prep_e_result="failure",
                    prep_e_executed="true",
                    electoral_source_validation="BLOQUEADO",
                ),
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "FAILED")
        self.assertIn(
            "03 · Preparación de Resultados Electorales",
            manifest["failed_phases"],
        )

    def test_r5b_corrupt_prepared_pair_is_technical_failure(self):
        with self.assertRaisesRegex(ValueError, "ELECTORAL_PAIR_TECHNICAL_BLOCK"):
            classify_prepared_pair_failure(
                "PREPARED_PAIR_BLOCK: receipt durable del par no disponible: evidence/pair.json"
            )
        gap = classify_prepared_pair_failure(
            "PREPARED_PAIR_BLOCK: falta evidence.prepared_source_pair para Demo edición 2025"
        )
        self.assertEqual(gap["completion_status"], "SKIPPED_NO_ACCREDITED_PAIR")

    def test_r6_electoral_scope_does_not_mutate_territorial_generation_contract(self):
        base = {
            "territory_id": "demo",
            "territory_name": "Demo",
            "edition": "2025",
            "contract_path": "territorios/demo/config/demo_2025.yaml",
            "generation_execution_mode": "reuse",
            "optimization_algorithm": "GerryChain 50",
            "run_prepare_territorial": False,
            "run_generate": True,
            "run_prepare_electoral": False,
            "run_incorporate": True,
            "population_year": 2025,
            "section_year": 2026,
            "existing": {
                "territorial_source": {
                    "run_id": 101,
                    "territorial_identity_sha256": "a" * 64,
                }
            },
        }
        territorial = copy.deepcopy(base)
        electoral = copy.deepcopy(base)
        resolve_publication_mode(territorial, "territorial_only", root_dir=Path("."))
        current = {
            "plans": [{
                "electoral_action": "REUSE",
                "electoral_admissibility": "ADMISSIBLE",
            }]
        }
        with mock.patch(
            "herramientas.resolver_ejecucion_completa.resolve_current_legislature",
            return_value=current,
        ):
            resolve_publication_mode(electoral, "electoral", root_dir=Path("."))

        for key in (
            "contract_path",
            "generation_execution_mode",
            "optimization_algorithm",
            "run_prepare_territorial",
            "run_generate",
            "population_year",
            "section_year",
        ):
            self.assertEqual(territorial[key], electoral[key])
        self.assertEqual(
            territorial["existing"]["territorial_source"],
            electoral["existing"]["territorial_source"],
        )

    def test_phase03_source_gap_mode_is_opt_in_and_00_classifies_it(self):
        prep = (ROOT / ".github/workflows/preparacion-resultados-electorales.yml").read_text(
            encoding="utf-8"
        )
        workflow = ORCH.read_text(encoding="utf-8")
        self.assertIn(
            "allow_source_gap_success: {required: false, type: boolean, default: false}",
            prep,
        )
        self.assertIn("electoral_outcome=SKIPPED_ELECTORAL_SOURCE_INVALID", prep)
        self.assertIn("needs.electorales.outputs.electoral_outcome == 'READY'", prep)
        self.assertIn("Fuente electoral no apta: terminal válido sin promoción ni registro.", prep)
        self.assertIn("allow_source_gap_success: true", workflow)
        self.assertIn("Clasificar resultado de la rama electoral", workflow)
        self.assertIn(
            "PREPARED_PAIR_SHA: ${{ needs.planificar.outputs.prepared_source_pair_sha256 }}",
            workflow,
        )
        self.assertIn(
            "no existe prepared_source_pair acreditado para la entrada electoral",
            workflow,
        )
        self.assertIn(
            'PREP_OUTCOME" == "SKIPPED_ELECTORAL_SOURCE_INVALID"',
            workflow,
        )
        self.assertIn(
            "03 falló técnicamente; no puede reclasificarse como source gap electoral",
            workflow,
        )
        self.assertIn(
            'production_eligible="${{ steps.policy.outputs.production_eligible }}"',
            prep,
        )
        self.assertIn(
            '[[ "$production_eligible" == "true" ]] && ready=true',
            prep,
        )
        self.assertIn(
            "fuente electoral no elegible para producción",
            prep,
        )
        self.assertIn(
            '[[ -z "$package_election_id" || "$package_election_id" == "$ELECTION_ID" ]]',
            prep,
        )
        self.assertIn(
            "Bloqueo electoral con identidad contradictoria",
            prep,
        )
        self.assertIn(
            "electoral:{run_id:$electoral_run_id,artifact:$electoral_artifact,execution:$electoral_execution,completion_status:$electoral_completion_status}",
            workflow,
        )
        self.assertIn(
            "RUN_PREP_E: ${{ needs.preparar_electoral.result != 'skipped' }}",
            workflow,
        )
        self.assertIn(
            "RUN_INC: ${{ needs.incorporar.result != 'skipped' }}",
            workflow,
        )

    def test_legislature_resolution_corruption_is_not_downgraded_to_source_gap(self):
        plan = {
            "territory_id": "demo",
            "territory_name": "Demo",
            "edition": "2025",
            "run_prepare_territorial": False,
            "run_generate": True,
            "run_prepare_electoral": True,
            "run_incorporate": True,
        }
        with mock.patch(
            "herramientas.resolver_ejecucion_completa.resolve_current_legislature",
            side_effect=ValueError("matriz electoral contradictoria"),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "ELECTORAL_ACTIVATION_TECHNICAL_BLOCK",
            ):
                resolve_publication_mode(plan, "electoral", root_dir=Path("."))

        self.assertTrue(plan["run_generate"])
        self.assertTrue(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])

    def test_unknown_skip_or_classifier_failure_cannot_yield_success_manifest(self):
        scenarios = (
            {
                "completion": "SKIPPED_TECHNICAL_FAILURE",
            },
            {
                "completion": "SKIPPED_SOURCE_UNAVAILABLE",
                "classification_result": "failure",
            },
            {
                "completion": "SKIPPED_SOURCE_UNAVAILABLE",
                "territorial_product_validation": "BLOQUEADO",
            },
            {
                "completion": "SKIPPED_SOURCE_UNAVAILABLE",
                "incorporate_executed": "true",
            },
        )
        for kwargs in scenarios:
            with self.subTest(**kwargs), tempfile.TemporaryDirectory() as td:
                output = Path(td) / "manifest.json"
                completed = subprocess.run(
                    manifest_cmd(output, **kwargs),
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                manifest = json.loads(output.read_text(encoding="utf-8"))
                self.assertEqual(manifest["status"], "FAILED")
                self.assertEqual(manifest["completion_status"], "INCOMPLETE")

    def test_same_material_pair_never_replaces_preferred_territorial_run(self):
        preferred = {
            "run_id": 101,
            "artifact_name": "ddd-source-package-demo-2025-101",
            "territorial_identity_sha256": "a" * 64,
            "population_year": 2025,
            "section_year": 2025,
        }
        pair = {
            "territorial_source": {
                "run_id": 202,
                "artifact_name": "ddd-source-package-demo-2025-202",
                "territorial_identity_sha256": "a" * 64,
                "population_year": 2025,
                "section_year": 2025,
            }
        }
        selected = select_territorial_for_prepared_pair(
            {"territory_name": "Demo"},
            preferred_territorial=preferred,
            pair=pair,
            root_dir=Path("."),
        )
        self.assertEqual(selected["status"], "FULL_PAIR_READY")
        self.assertEqual(selected["selected"]["run_id"], 101)
        self.assertEqual(
            selected["selection_reason"],
            "PREFERRED_TERRITORIAL_MATCHES_ACCREDITED_PAIR",
        )

    def test_r7_alternative_territorial_requires_temporal_admissibility_and_is_explicit(self):
        preferred = {
            "territorial_identity_sha256": "a" * 64,
            "population_year": 2025,
            "section_year": 2026,
        }
        pair = {
            "territorial_source": {
                "territorial_identity_sha256": "b" * 64,
                "population_year": 2025,
                "section_year": 2026,
            }
        }
        temporal = {
            "plans": [{
                "population_year_selected": 2025,
                "section_year_selected": 2026,
            }]
        }
        with mock.patch(
            "herramientas.resolver_ejecucion_completa.resolve_current_legislature",
            return_value=temporal,
        ):
            selected = select_territorial_for_prepared_pair(
                {"territory_name": "Demo"},
                preferred_territorial=preferred,
                pair=pair,
                root_dir=Path("."),
            )

        self.assertEqual(
            selected["status"],
            "TERRITORIAL_READY_PAIR_INCOMPATIBLE",
        )
        self.assertEqual(selected["preferred_identity_sha256"], "a" * 64)
        self.assertEqual(selected["selected_identity_sha256"], "a" * 64)
        self.assertTrue(selected["alternative_temporally_admissible"])
        self.assertEqual(
            selected["selection_reason"],
            "PAIR_ALTERNATIVE_NOT_AUTO_SELECTED_TO_PRESERVE_TERRITORIAL_INDEPENDENCE",
        )

        workflow = ORCH.read_text(encoding="utf-8")
        self.assertNotIn("reuse=pair_doc.get(\"geometric_reuse\")", workflow)
        self.assertNotIn("FULL_PAIR_READY_WITH_ALTERNATIVE_TERRITORIAL", workflow)
        source_gate = workflow.split(
            "  verificar_fuentes_preparadas:", 1
        )[1].split("  detectar_recuperacion_electoral:", 1)[0]
        self.assertIn("resolve-territorial", source_gate)
        self.assertNotIn("--root-dir . resolve \\", source_gate)


if __name__ == "__main__":
    unittest.main()
