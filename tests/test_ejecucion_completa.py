from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest
import yaml

from herramientas.resolver_ejecucion_completa import _run_from_artifact, build_plan
from herramientas.escribir_manifest_ejecucion_completa import optimization_lineage

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
ORCH = WF / "ejecucion-completa-proyecto.yml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def triggers(path: Path) -> dict:
    data = load(path)
    return data.get("on") or data.get(True) or {}


class FullProjectOrchestratorTests(unittest.TestCase):

    def test_newly_produced_artifacts_do_not_reuse_previous_digest(self):
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn(
            "needs.preparar_territorial.result != 'success' && needs.planificar.outputs.existing_territorial_source_digest || ''",
            orchestration,
        )
        self.assertIn(
            "needs.generar.result != 'success' && needs.planificar.outputs.existing_territorial_product_digest || ''",
            orchestration,
        )
        self.assertIn(
            "needs.preparar_electoral.result != 'success' && needs.planificar.outputs.existing_electoral_source_digest || ''",
            orchestration,
        )
        self.assertIn(
            "needs.incorporar.result != 'success' && needs.planificar.outputs.existing_electoral_product_digest || ''",
            orchestration,
        )
        self.assertNotIn("result == 'success' && '' || needs.planificar.outputs.existing_", orchestration)

    def test_run_id_se_extrae_del_nombre_real_del_artefacto(self):
        self.assertEqual(_run_from_artifact("ddd-state-123456-M06", 999999), 123456)
        self.assertEqual(_run_from_artifact("ddd-state-654321-M08", None), 654321)
        self.assertEqual(_run_from_artifact("ddd-source-package-galicia-2025-777777", 1), 777777)

    def test_orchestrator_exposes_only_functional_controls(self):
        data = load(ORCH)
        self.assertEqual(data["name"], "00 · Ejecución Completa del Proyecto")
        inputs = triggers(ORCH)["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs), ["territory_id", "data_edition", "execution_mode", "optimization_algorithm", "publication_mode", "publish_result"])
        self.assertEqual(
            inputs["execution_mode"]["options"],
            [
                "Reutilizar progreso existente",
                "Generar desde fuente territorial acreditada",
                "Ejecutar desde el principio",
            ],
        )
        self.assertEqual(inputs["optimization_algorithm"]["options"], ["Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"])
        self.assertEqual(inputs["publication_mode"]["options"], ["electoral", "territorial_only"])
        self.assertFalse(inputs["publish_result"]["default"])
        dumped = yaml.safe_dump(inputs, allow_unicode=True)
        for forbidden in ("checkpoint_run_id:", "from_stage:", "to_stage:", "product:"):
            self.assertNotIn(forbidden, dumped)

    def test_orchestrator_runs_safe_premerge_smoke_directly(self):
        t = triggers(ORCH)
        self.assertIn("workflow_call", t)
        self.assertIn("pull_request", t)
        call_inputs = t["workflow_call"]["inputs"]
        self.assertIn("source_ref", call_inputs)
        self.assertIn("persist_state", call_inputs)
        text = ORCH.read_text(encoding="utf-8")
        self.assertIn("github.event_name == 'pull_request' && 'Galicia'", text)
        self.assertIn("github.event_name == 'pull_request' && '2025'", text)
        self.assertIn("github.event_name == 'pull_request' && 'Reutilizar progreso existente'", text)
        self.assertIn("github.event_name == 'pull_request' && 'Canónico'", text)
        self.assertIn("inputs.publication_mode || 'electoral'", text)
        self.assertIn('if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]', text)
        self.assertIn("persist=false", text)
        self.assertIn("publish=false", text)
        self.assertIn('[[ "$persist" == "true" && "$GITHUB_REF_NAME" != "main" ]]', text)
        self.assertIn("La persistencia durable sólo está permitida desde main", text)

    def test_premerge_smoke_cannot_persist_catalog_state(self):
        for name in (
            "preparacion-fuentes.yml",
            "preparacion-resultados-electorales.yml",
            "_reutilizable-generacion-territorial.yml",
            "_reutilizable-incorporacion-electoral.yml",
        ):
            text = (WF / name).read_text(encoding="utf-8")
            self.assertIn("persist_state", text, name)
        self.assertIn("needs.resolver.outputs.persist_state", load(WF / "preparacion-fuentes.yml")["jobs"]["registrar"]["if"])
        self.assertIn("needs.resolver.outputs.persist_state", load(WF / "preparacion-resultados-electorales.yml")["jobs"]["registrar"]["if"])
        self.assertIn("inputs.persist_state", load(WF / "_reutilizable-generacion-territorial.yml")["jobs"]["registrar"]["if"])
        self.assertIn("inputs.persist_state", load(WF / "_reutilizable-incorporacion-electoral.yml")["jobs"]["registrar"]["if"])

    def test_orchestrator_false_persistence_is_respected_by_generation(self):
        orchestration=load(ORCH)
        generation=load(WF / "produccion-distritos.yml")
        generar=orchestration["jobs"]["generar"]["with"]
        self.assertEqual(
            generar["persist_state"],
            "${{ needs.planificar.outputs.persist_state == 'true' }}",
        )
        generation_triggers=triggers(WF / "produccion-distritos.yml")
        self.assertEqual(
            generation_triggers["workflow_call"]["inputs"]["invocation_context"]["default"],
            "reusable",
        )
        self.assertEqual(
            generation["jobs"]["ruta"]["with"]["persist_state"],
            "${{ inputs.invocation_context != 'reusable' || inputs.persist_state }}",
        )

    def test_manual_generation_does_not_require_gerrychain_contract(self):
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("gerrychain_entrypoint: ${{ inputs.gerrychain_entrypoint || '' }}", orchestration)
        self.assertIn("require_unique_hashes: ${{ inputs.require_unique_hashes == true }}", orchestration)
        dispatch_inputs = triggers(ORCH)["workflow_dispatch"]["inputs"]
        self.assertNotIn("gerrychain_entrypoint", dispatch_inputs)
        self.assertNotIn("require_unique_hashes", dispatch_inputs)

    def test_orchestrator_calls_business_phases_in_order(self):
        data = load(ORCH)
        jobs = data["jobs"]
        self.assertEqual(
            list(jobs),
            [
                "planificar",
                "detectar_recuperacion_electoral",
                "preparar_territorial",
                "puerta_01",
                "generar",
                "puerta_02",
                "preparar_electoral",
                "puerta_03",
                "incorporar",
                "recuperar_electoral",
                "puerta_04",
                "actualizar_estado",
                "publicar",
                "campaign_status",
                "manifestar",
            ],
        )
        self.assertEqual(jobs["preparar_territorial"]["uses"], "./.github/workflows/preparacion-fuentes.yml")
        self.assertEqual(jobs["generar"]["uses"], "./.github/workflows/produccion-distritos.yml")
        self.assertEqual(jobs["preparar_electoral"]["uses"], "./.github/workflows/preparacion-resultados-electorales.yml")
        self.assertEqual(jobs["incorporar"]["uses"], "./.github/workflows/incorporacion-resultados-electorales.yml")
        self.assertEqual(jobs["recuperar_electoral"]["uses"], "./.github/workflows/recuperar-producto-electoral-durable.yml")
        self.assertEqual(jobs["publicar"]["uses"], "./.github/workflows/desplegar-visor-publico.yml")

    def test_business_phases_are_reusable(self):
        for name in (
            "preparacion-fuentes.yml",
            "produccion-distritos.yml",
            "preparacion-resultados-electorales.yml",
            "incorporacion-resultados-electorales.yml",
            "desplegar-visor-publico.yml",
        ):
            self.assertIn("workflow_call", triggers(WF / name), name)

    def test_from_start_disables_checkpoint_and_prepared_package_reuse(self):
        generation = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        preparation = (WF / "preparacion-fuentes.yml").read_text(encoding="utf-8")
        self.assertIn('if [[ "$mode" == from_start ]]', generation)
        self.assertIn('echo "from_stage=M01"', generation)
        self.assertIn("reutilizar_si_ya_preparada", preparation)
        data = load(ORCH)
        expected = "${{ needs.planificar.outputs.execution_mode_internal != 'from_start' }}"
        self.assertEqual(data["jobs"]["preparar_territorial"]["with"]["reutilizar_si_ya_preparada"], expected)
        self.assertEqual(data["jobs"]["preparar_electoral"]["with"]["reutilizar_si_ya_preparada"], expected)
        self.assertEqual(
            data["jobs"]["generar"]["with"]["execution_mode"],
            "${{ needs.planificar.outputs.generation_execution_mode }}",
        )

    def test_current_run_artifacts_can_feed_next_phase(self):
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("source_package_run_id:", orchestration)
        self.assertIn("territorial_run_id:", orchestration)
        self.assertIn("electoral_package_run_id:", orchestration)
        self.assertIn("github.run_id", orchestration)
        self.assertIn("needs.puerta_01.outputs.run_id", orchestration)
        self.assertIn("needs.puerta_02.outputs.run_id", orchestration)
        self.assertIn("needs.puerta_03.outputs.run_id", orchestration)
        self.assertIn("needs.puerta_04.outputs.run_id", orchestration)
        generation = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        electoral = (WF / "incorporacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn("OVERRIDE_SOURCE_RUN_ID", generation)
        self.assertIn("OVERRIDE_RUN_ID", electoral)

    def test_validation_gates_block_following_phases(self):
        data = load(ORCH)
        jobs = data["jobs"]
        self.assertIn("needs.puerta_01.result == 'success'", jobs["generar"]["if"])
        self.assertIn("needs.puerta_02.result == 'success'", jobs["preparar_electoral"]["if"])
        self.assertIn("needs.puerta_03.result == 'success'", jobs["incorporar"]["if"])
        self.assertIn("needs.puerta_04.result == 'success'", jobs["actualizar_estado"]["if"])
        self.assertIn("needs.actualizar_estado.result == 'success'", jobs["publicar"]["if"])
        for name in ("puerta_01", "puerta_02", "puerta_03", "puerta_04"):
            self.assertEqual(jobs[name]["uses"], "./.github/workflows/_reutilizable-puerta-validacion.yml")

    def test_pull_request_smoke_stops_after_territorial_product_gate(self):
        data = load(ORCH)
        jobs = data["jobs"]
        puerta_03_if = jobs["puerta_03"]["if"]
        self.assertIn("github.event_name != 'pull_request'", puerta_03_if)
        self.assertIn("needs.puerta_03.result == 'success'", jobs["incorporar"]["if"])
        self.assertIn("needs.puerta_03.result == 'success'", jobs["puerta_04"]["if"])
        gate = (WF / "_reutilizable-puerta-validacion.yml").read_text(encoding="utf-8")
        self.assertIn('audit_name="ddd-audit-electoral-$resolved_run_id"', gate)
        self.assertNotIn('audit_name="ddd-audit-$resolved_run_id"\n              audit_name="ddd-audit-electoral-', gate)

    def test_validation_gate_contract_exposes_digest_and_spanish_decision(self):
        gate = (WF / "_reutilizable-puerta-validacion.yml").read_text(encoding="utf-8")
        validator = (ROOT / "herramientas/validar_puerta_ejecucion.py").read_text(encoding="utf-8")
        self.assertIn("artifact_digest", gate)
        self.assertIn("expected_digest", gate)
        self.assertIn("VALIDADO", validator)
        self.assertIn("BLOQUEADO", validator)
        self.assertNotIn("preflight", gate.lower())

    def test_operational_state_updates_readme_and_dashboard_before_publication(self):
        data = load(ORCH)
        jobs = data["jobs"]
        self.assertIn("actualizar_estado", jobs)
        self.assertIn("python -m herramientas.persistir_estado_operativo_compartido", ORCH.read_text(encoding="utf-8"))
        self.assertEqual(jobs["actualizar_estado"]["concurrency"]["group"], "ddd-shared-operational-state")
        self.assertFalse(jobs["actualizar_estado"]["concurrency"]["cancel-in-progress"])
        self.assertIn("actualizar_estado", jobs["publicar"]["needs"])
        generator = (ROOT / "herramientas/generar_estado_operativo.py").read_text(encoding="utf-8")
        self.assertIn("orchestracion/estado_operativo.json", generator)
        self.assertIn("publicado/dashboard/status.json", generator)
        self.assertIn("README.md", generator)

    def test_manifest_is_uploaded_and_durable_on_main(self):
        text = ORCH.read_text(encoding="utf-8")
        self.assertIn("ddd-full-run-manifest-${{ github.run_id }}", text)
        self.assertIn("retention-days: 90", text)
        self.assertIn("ejecuciones_completas/$GITHUB_RUN_ID.json", text)
        self.assertIn("github.ref_name == 'main'", text)

    def test_manifest_records_requested_and_effective_algorithm_after_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "OPTIMIZATION_EXECUTION.json"
            evidence.write_text(
                json.dumps({
                    "schema": "ddd.optimization-execution/1.0",
                    "requested_algorithm": "GerryChain 50",
                    "effective_algorithm": "Canónico",
                    "fallback": True,
                    "fallback_reason": "gerrychain_runtime_failure_after_valid_baseline",
                }),
                encoding="utf-8",
            )
            lineage = optimization_lineage(
                "GerryChain 50",
                generate_executed=True,
                generate_result="success",
                evidence_path=str(evidence),
            )
            self.assertEqual(lineage["optimization_algorithm_requested"], "GerryChain 50")
            self.assertEqual(lineage["optimization_algorithm_effective"], "Canónico")
            self.assertTrue(lineage["optimization_fallback"])
            self.assertEqual(
                lineage["optimization_fallback_reason"],
                "gerrychain_runtime_failure_after_valid_baseline",
            )

    def test_manifest_rejects_missing_effective_evidence_when_generation_ran(self):
        with self.assertRaises(ValueError):
            optimization_lineage(
                "GerryChain 25",
                generate_executed=True,
                generate_result="success",
                evidence_path=None,
            )

    def test_failed_generation_preserves_manifest_without_effective_evidence(self):
        lineage = optimization_lineage(
            "GerryChain 50",
            generate_executed=True,
            generate_result="failure",
            evidence_path=None,
        )
        self.assertIsNone(lineage["optimization_algorithm_effective"])
        self.assertFalse(lineage["optimization_fallback"])
        self.assertEqual(
            lineage["optimization_evidence_status"],
            "NOT_AVAILABLE_DUE_TO_GENERATION_FAILURE",
        )

    def test_reused_product_does_not_invent_effective_algorithm(self):
        lineage = optimization_lineage(
            "Canónico",
            generate_executed=False,
            generate_result="skipped",
            evidence_path=None,
        )
        self.assertIsNone(lineage["optimization_algorithm_effective"])
        self.assertEqual(lineage["optimization_evidence_status"], "REUSED_EXISTING_PRODUCT")

    def test_workflow_downloads_effective_optimization_evidence_for_manifest(self):
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("Recuperar evidencia de optimización efectiva", orchestration)
        self.assertIn("OPTIMIZATION_EXECUTION.json", orchestration)
        self.assertIn("--optimization-evidence", orchestration)
        self.assertIn('if [[ "$RUN_GEN" == "true" && "$GEN_RESULT" == "success" ]]', orchestration)
        self.assertIn("La generación completó correctamente pero no dejó evidencia de estrategia efectiva.", orchestration)

    def test_generation_success_recovers_optimization_evidence_even_if_gate_02_fails(self):
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn(
            "needs.planificar.outputs.run_generate == 'true' && needs.generar.result == 'success'",
            orchestration,
        )
        self.assertNotIn(
            "needs.planificar.outputs.run_generate == 'true' && needs.puerta_02.result == 'success'",
            orchestration,
        )
        self.assertIn("name: ${{ needs.puerta_02.outputs.artifact_name }}", orchestration)
        self.assertIn("run-id: ${{ github.run_id }}", orchestration)

    def test_manifest_cli_integrates_effective_optimization_evidence(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = root / "ddd-state" / "run"
            state.mkdir(parents=True)
            evidence = state / "OPTIMIZATION_EXECUTION.json"
            evidence.write_text(
                json.dumps({
                    "schema": "ddd.optimization-execution/1.0",
                    "requested_algorithm": "GerryChain 50",
                    "effective_algorithm": "Canónico",
                    "fallback": True,
                    "fallback_reason": "gerrychain_runtime_failure_after_valid_baseline",
                }),
                encoding="utf-8",
            )
            output = root / "manifest.json"
            cmd = [
                sys.executable,
                str(ROOT / "herramientas" / "escribir_manifest_ejecucion_completa.py"),
                "--territory-id", "demo",
                "--territory-name", "Demo",
                "--edition", "2025",
                "--execution-mode", "from_start",
                "--optimization-algorithm", "GerryChain 50",
                "--optimization-evidence", str(evidence),
                "--workflow-run-id", "123",
                "--source-sha", "a" * 40,
                "--publication-mode-requested", "territorial_only",
                "--publication-mode-effective", "territorial_only",
                "--publish-requested", "false",
                "--prepare-territorial-result", "success",
                "--generate-result", "success",
                "--prepare-electoral-result", "skipped",
                "--incorporate-result", "skipped",
                "--publish-result", "skipped",
                "--prepare-territorial-executed", "true",
                "--generate-executed", "true",
                "--prepare-electoral-executed", "false",
                "--incorporate-executed", "false",
                "--territorial-source-validation", "VALIDADO",
                "--territorial-product-validation", "VALIDADO",
                "--output", str(output),
            ]
            completed = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["optimization_algorithm_requested"], "GerryChain 50")
            self.assertEqual(manifest["optimization_algorithm_effective"], "Canónico")
            self.assertTrue(manifest["optimization_fallback"])
            self.assertEqual(manifest["optimization_evidence_status"], "VALID")
            self.assertEqual(manifest["publication_mode_requested"], "territorial_only")
            self.assertEqual(manifest["publication_mode_effective"], "territorial_only")
            self.assertFalse(manifest["publication_mode_scope_mismatch"])

    def test_manifest_marks_failed_electoral_preparation_as_explicit_block(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "manifest.json"
            cmd = [
                sys.executable,
                str(ROOT / "herramientas" / "escribir_manifest_ejecucion_completa.py"),
                "--territory-id", "extremadura",
                "--territory-name", "Extremadura",
                "--edition", "2025",
                "--execution-mode", "reuse",
                "--optimization-algorithm", "Canónico",
                "--workflow-run-id", "456",
                "--source-sha", "b" * 40,
                "--publication-mode-requested", "electoral",
                "--publication-mode-effective", "electoral",
                "--publish-requested", "false",
                "--prepare-territorial-result", "skipped",
                "--generate-result", "skipped",
                "--prepare-electoral-result", "failure",
                "--incorporate-result", "skipped",
                "--publish-result", "skipped",
                "--prepare-territorial-executed", "false",
                "--generate-executed", "false",
                "--prepare-electoral-executed", "true",
                "--incorporate-executed", "false",
                "--territorial-source-validation", "VALIDADO",
                "--territorial-product-validation", "VALIDADO",
                "--electoral-source-validation", "BLOQUEADO",
                "--electoral-product-validation", "BLOQUEADO",
                "--output", str(output),
            ]
            completed = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(manifest["publication_mode_requested"], "electoral")
            self.assertEqual(manifest["publication_mode_effective"], "electoral")
            self.assertFalse(manifest["publication_mode_scope_mismatch"])
            self.assertEqual(manifest["status"], "FAILED")
            self.assertIn("03 · Preparación de Resultados Electorales", manifest["failed_phases"])
            self.assertIn("03 · Preparación de Resultados Electorales", manifest["blocked_phases"])

    def test_manifest_treats_skipped_scheduled_phase_as_failure(self):
        writer=(ROOT/"herramientas/escribir_manifest_ejecucion_completa.py").read_text(encoding="utf-8")
        self.assertIn('p["executed"] and p["result"] != "success"',writer)

    def test_reuse_plan_reruns_generation_for_noncanonical_selected_algorithm(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract = root / "territorios/demo/config/demo_2025.yaml"
            contract.parent.mkdir(parents=True)
            contract.write_text(yaml.safe_dump({
                "meta": {"territory_id": "demo", "status": "generation_ready"},
                "territory_contract": {"status": "generation_ready"},
            }), encoding="utf-8")
            evidence = root / "evidence"
            evidence.mkdir()
            digest = "a" * 64
            (evidence / "territorial.json").write_text(json.dumps({"run_id": 101, "artifact_name": "m06", "artifact_sha256": digest, "decision": "PASS"}), encoding="utf-8")
            (evidence / "source.json").write_text(json.dumps({"run_id": 102, "artifact_name": "electoral-source", "artifact_sha256": digest}), encoding="utf-8")
            (evidence / "electoral.json").write_text(json.dumps({"run_id": 103, "artifact_name": "m08", "artifact_sha256": digest}), encoding="utf-8")
            catalog = root / "catalog.yaml"
            catalog.write_text(
                yaml.safe_dump(
                    {
                        "schema": "ddd-preparation-catalog/1.1",
                        "default_edition": "2025",
                        "territories": [
                            {
                                "territory_id": "demo",
                                "name": "Demo",
                                "editions": {
                                    "2025": {
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
                                    }
                                },
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            plan = build_plan(
                territory="Demo",
                edition="2025",
                execution_mode="reuse",
                catalog=catalog,
                root_dir=root,
                optimization_algorithm="GerryChain 50",
                force_selected_algorithm=True,
            )
            self.assertFalse(plan["run_prepare_territorial"])
            self.assertTrue(plan["run_generate"])
            self.assertFalse(plan["run_prepare_electoral"])
            self.assertTrue(plan["run_incorporate"])
            self.assertEqual(plan["optimization_algorithm"], "GerryChain 50")
            self.assertEqual(plan["existing"]["electoral_product"]["run_id"], 103)

    def test_reuse_reschedules_electoral_when_registered_election_changed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
                        "electoral_source_declaration": None,
                        "territorial_sources_prepared": False,
                        "territorial_contract_complete": True,
                        "territorial_product_available": False,
                        "electoral_source_prepared": True,
                        "electoral_product_available": False,
                        "territorial_certification": "NOT_CERTIFIED",
                        "production_authorization": "AUTHORIZED",
                        "last_valid_checkpoint": None,
                        "preparation_evidence": {},
                        "evidence": {"electoral_source": "evidence/source.json"},
                    }},
                }],
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")
            evidence = root / "evidence"
            evidence.mkdir()
            (evidence / "source.json").write_text(json.dumps({
                "schema": "ddd.catalog-evidence/1.0",
                "kind": "electoral_source",
                "territory_id": "demo",
                "edition": "2025",
                "run_id": 102,
                "artifact_name": "ddd-electoral-package-demo-2025-102",
                "artifact_sha256": "d" * 64,
                "source_commit": "1" * 40,
                "election_id": "demo_2024",
            }), encoding="utf-8")
            registry = root / "configuracion/registro_electoral.yaml"
            registry.parent.mkdir(parents=True)
            registry.write_text(yaml.safe_dump({
                "schema": "ddd-election-registry/1.0",
                "edition": "2025",
                "territories": {
                    "demo": {
                        "name": "Demo",
                        "election_id": "demo_2026",
                        "election_date": "2026-01-01",
                    }
                },
            }, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "CONTINUE_DURABLE_BLOCK.*electoral_source.*election_id",
            ):
                build_plan(
                    territory="Demo",
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=root,
                )

    def test_reuse_reschedules_phase_when_catalog_flag_lacks_durable_provenance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
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
                        "territorial_sources_prepared": False,
                        "territorial_contract_complete": True,
                        "territorial_product_available": False,
                        "electoral_source_prepared": True,
                        "electoral_product_available": False,
                        "territorial_certification": "NOT_CERTIFIED",
                        "production_authorization": "AUTHORIZED",
                        "last_valid_checkpoint": None,
                        "preparation_evidence": {},
                        "evidence": {},
                    }},
                }],
            }, allow_unicode=True, sort_keys=False), encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError,
                "CONTINUE_DURABLE_BLOCK.*DURABLE_ASSET_MISSING.*electoral_source",
            ):
                build_plan(
                    territory="Demo",
                    edition="2025",
                    execution_mode="reuse",
                    catalog=catalog,
                    root_dir=root,
                )

    def test_gerrychain_50_is_preserved_in_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            contract = root / "territorios/demo/config/demo_2025.yaml"
            contract.parent.mkdir(parents=True)
            contract.write_text(yaml.safe_dump({
                "meta": {"territory_id": "demo", "status": "generation_ready"},
                "territory_contract": {"status": "generation_ready"},
            }), encoding="utf-8")
            catalog = root / "catalog.yaml"
            catalog.write_text(
                yaml.safe_dump({
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
                }, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
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

    def test_catalog_source_mode_forces_new_generation_and_preserves_electoral_reuse(self):
        plan = build_plan(
            territory="Ceuta",
            edition="2025",
            execution_mode="catalog_source",
            catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
            root_dir=ROOT,
        )
        self.assertEqual(plan["execution_mode"], "catalog_source")
        self.assertEqual(plan["generation_execution_mode"], "from_start")
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertTrue(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])
        self.assertTrue(plan["existing"]["territorial_product"]["run_id"])
        self.assertEqual(plan["existing"]["territorial_source"]["decision"], "VALIDADO")
        self.assertEqual(plan["generation_gate"], {
            "allowed": True,
            "route": "accredited_source_recalculation",
        })
        self.assertEqual(
            plan["existing"]["territorial_source"]["artifact_name"],
            "ddd-source-package-ceuta-2025-36258940598",
        )

    def test_catalog_source_mode_prepares_electoral_only_when_missing(self):
        plan = build_plan(
            territory="Cantabria",
            edition="2025",
            execution_mode="catalog_source",
            catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
            root_dir=ROOT,
        )
        self.assertFalse(plan["run_prepare_territorial"])
        self.assertTrue(plan["run_generate"])
        self.assertTrue(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])

    def test_catalog_source_mode_blocks_invalid_catalog_accreditation_before_generation(self):
        original = load(ROOT / "configuracion/catalogo_preparacion.yaml")
        target = next(row for row in original["territories"] if row["territory_id"] == "cantabria")
        base_state = target["editions"]["2025"]
        mutations = {
            "missing_evidence": lambda state: state.pop("preparation_evidence", None),
            "run_artifact_mismatch": lambda state: state["preparation_evidence"].update(run_id=999),
            "invalid_digest": lambda state: state["preparation_evidence"].update(artifact_sha256="bad"),
            "missing_package_sha": lambda state: state["preparation_evidence"].pop("package_sha256", None),
            "wrong_provenance": lambda state: state.update(
                territorial_source_declaration="territorios/andalucia/config/fuentes_oficiales.yaml"
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as td:
                data = json.loads(json.dumps(original))
                row = next(r for r in data["territories"] if r["territory_id"] == "cantabria")
                state = row["editions"]["2025"]
                mutate(state)
                catalog = Path(td) / "catalog.yaml"
                catalog.write_text(
                    yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, "CATALOG_SOURCE_BLOCK"):
                    build_plan(
                        territory="Cantabria",
                        edition="2025",
                        execution_mode="catalog_source",
                        catalog=catalog,
                        root_dir=ROOT,
                    )
        self.assertTrue(base_state["preparation_evidence"]["package_sha256"])

    def test_catalog_source_mode_uses_existing_source_gate_and_never_old_m06(self):
        data = load(ORCH)
        jobs = data["jobs"]
        dispatch = triggers(ORCH)["workflow_dispatch"]["inputs"]
        self.assertNotIn("reuse_run_id", dispatch)
        self.assertNotIn("reuse_artifact_name", dispatch)
        self.assertNotIn("reuse_artifact_sha256", dispatch)
        self.assertNotIn("reuse_source_sha", dispatch)
        self.assertEqual(
            jobs["puerta_01"]["with"]["run_id"],
            "${{ needs.preparar_territorial.result == 'success' && github.run_id || needs.planificar.outputs.existing_territorial_source_run_id }}",
        )
        self.assertEqual(
            jobs["puerta_01"]["with"]["expected_digest"],
            "${{ needs.preparar_territorial.result != 'success' && needs.planificar.outputs.existing_territorial_source_digest || '' }}",
        )
        self.assertEqual(
            jobs["puerta_02"]["with"]["run_id"],
            "${{ needs.generar.result == 'success' && github.run_id || needs.planificar.outputs.existing_territorial_product_run_id }}",
        )
        self.assertEqual(
            jobs["incorporar"]["with"]["territorial_run_id"],
            "${{ needs.puerta_02.outputs.run_id }}",
        )
        self.assertEqual(
            jobs["preparar_electoral"]["with"]["reutilizar_si_ya_preparada"],
            "${{ needs.planificar.outputs.execution_mode_internal != 'from_start' }}",
        )
        gate = (ROOT / "herramientas/validar_puerta_ejecucion.py").read_text(encoding="utf-8")
        self.assertIn('phase == "territorial_source"', gate)
        self.assertIn("validate_prepared_package(", gate)
        generation = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        self.assertIn("SOURCE_RECALCULATION_PLANNED", generation)
        self.assertIn("source_recalculation_planned=", generation)

    def test_from_start_without_generation_contract_blocks_before_business_phases(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            catalog = root / "catalog.yaml"
            catalog.write_text(
                yaml.safe_dump(
                    {
                        "schema": "ddd-preparation-catalog/1.1",
                        "default_edition": "2025",
                        "territories": [
                            {
                                "territory_id": "demo",
                                "name": "Demo",
                                "editions": {
                                    "2025": {
                                        "territory_declared": True,
                                        "preparation_status": "PENDING_INCORPORATION",
                                        "contract_path": None,
                                        "territorial_source_declaration": None,
                                        "electoral_source_declaration": None,
                                        "territorial_contract_complete": False,
                                        "production_authorization": "NONE",
                                        "last_valid_checkpoint": None,
                                        "territorial_sources_prepared": False,
                                        "territorial_product_available": False,
                                        "electoral_source_prepared": False,
                                        "electoral_product_available": False,
                                        "territorial_certification": "NOT_CERTIFIED",
                                    }
                                },
                            }
                        ],
                    },
                    allow_unicode=True,
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "contrato territorial efectivo ausente"):
                build_plan(
                    territory="Demo",
                    edition="2025",
                    execution_mode="from_start",
                    catalog=catalog,
                    root_dir=root,
                )


class CastillaLaManchaReuseCurrentDurableInputsTests(unittest.TestCase):
    def test_plan_is_no_no_no_yes_and_uses_current_receipts(self):
        data = load(ROOT / "configuracion/catalogo_preparacion.yaml")
        row = next(r for r in data["territories"] if r["territory_id"] == "castilla_la_mancha")
        state = row["editions"]["2025"]

        territorial_path = ROOT / "territorios/castilla_la_mancha/evidencia/catalogo/territorial_product_2025.json"
        electoral_source_path = ROOT / "territorios/castilla_la_mancha/evidencia/catalogo/electoral_source_2025.json"
        territorial = json.loads(territorial_path.read_text(encoding="utf-8"))
        electoral_source = json.loads(electoral_source_path.read_text(encoding="utf-8"))

        self.assertEqual(territorial["territory_id"], "castilla_la_mancha")
        self.assertEqual(electoral_source["territory_id"], "castilla_la_mancha")
        self.assertEqual(str(territorial["edition"]), "2025")
        self.assertEqual(str(electoral_source["edition"]), "2025")
        self.assertRegex(str(territorial["artifact_sha256"]).removeprefix("sha256:"), r"^[0-9a-f]{64}$")
        self.assertRegex(str(electoral_source["artifact_sha256"]).removeprefix("sha256:"), r"^[0-9a-f]{64}$")

        # Escenario aislado: M06 y fuente electoral durables disponibles, sin M08.
        state["territorial_product_available"] = True
        state["electoral_source_prepared"] = True
        state["electoral_product_available"] = False
        state["territorial_certification"] = "PASS_WITH_GOVERNED_EXCEPTIONS"
        state["last_valid_checkpoint"] = {"run_id": int(territorial["run_id"]), "stage": "M06"}
        state["evidence"] = {
            "territorial_product": str(territorial_path.relative_to(ROOT)),
            "electoral_source": str(electoral_source_path.relative_to(ROOT)),
        }
        with tempfile.TemporaryDirectory() as td:
            catalog = Path(td) / "catalog.yaml"
            catalog.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            plan = build_plan(
                territory="Castilla-La Mancha",
                edition="2025",
                execution_mode="reuse",
                catalog=catalog,
                root_dir=ROOT,
            )

        self.assertFalse(plan["run_prepare_territorial"])
        self.assertFalse(plan["run_generate"])
        self.assertFalse(plan["run_prepare_electoral"])
        self.assertTrue(plan["run_incorporate"])
        self.assertEqual(plan["existing"]["territorial_product"]["run_id"], territorial["run_id"])
        self.assertEqual(plan["existing"]["territorial_product"]["artifact_name"], territorial["artifact_name"])
        self.assertEqual(plan["existing"]["territorial_product"]["artifact_sha256"], territorial["artifact_sha256"])
        self.assertEqual(plan["existing"]["electoral_source"]["run_id"], electoral_source["run_id"])
        self.assertEqual(plan["existing"]["electoral_source"]["artifact_name"], electoral_source["artifact_name"])
        self.assertEqual(plan["existing"]["electoral_source"]["artifact_sha256"], electoral_source["artifact_sha256"])


if __name__ == "__main__":
    unittest.main()
