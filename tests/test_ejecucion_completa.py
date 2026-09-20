from __future__ import annotations

import json
import tempfile
from pathlib import Path
import unittest
import yaml

from herramientas.resolver_ejecucion_completa import build_plan

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
ORCH = WF / "ejecucion-completa-proyecto.yml"


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def triggers(path: Path) -> dict:
    data = load(path)
    return data.get("on") or data.get(True) or {}


class FullProjectOrchestratorTests(unittest.TestCase):
    def test_orchestrator_exposes_only_functional_controls(self):
        data = load(ORCH)
        self.assertEqual(data["name"], "00 · Ejecución Completa del Proyecto")
        inputs = triggers(ORCH)["workflow_dispatch"]["inputs"]
        self.assertEqual(list(inputs), ["territory_id", "data_edition", "execution_mode", "optimization_algorithm", "publish_result"])
        self.assertEqual(
            inputs["execution_mode"]["options"],
            ["Reutilizar progreso existente", "Ejecutar desde el principio"],
        )
        self.assertEqual(inputs["optimization_algorithm"]["options"], ["Canónico","GerryChain","GerryChain 25","GerryChain 50"])
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
        self.assertIn('if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]', text)
        self.assertIn("persist=false", text)
        self.assertIn("publish=false", text)

    def test_premerge_smoke_cannot_persist_catalog_state(self):
        for name in (
            "preparacion-fuentes.yml",
            "preparacion-resultados-electorales.yml",
            "_reutilizable-generacion-territorial.yml",
            "_reutilizable-incorporacion-electoral.yml",
        ):
            text = (WF / name).read_text(encoding="utf-8")
            self.assertIn("persist_state", text, name)
        self.assertIn("inputs.persist_state", load(WF / "preparacion-fuentes.yml")["jobs"]["registrar"]["if"])
        self.assertIn("inputs.persist_state", load(WF / "preparacion-resultados-electorales.yml")["jobs"]["registrar"]["if"])
        self.assertIn("inputs.persist_state", load(WF / "_reutilizable-generacion-territorial.yml")["jobs"]["registrar"]["if"])
        self.assertIn("inputs.persist_state", load(WF / "_reutilizable-incorporacion-electoral.yml")["jobs"]["registrar"]["if"])

    def test_orchestrator_calls_business_phases_in_order(self):
        data = load(ORCH)
        jobs = data["jobs"]
        self.assertEqual(
            list(jobs),
            [
                "planificar",
                "preparar_territorial",
                "validar_territorial",
                "generar",
                "validar_generacion",
                "preparar_electoral",
                "validar_electoral",
                "incorporar",
                "validar_producto",
                "actualizar_estado",
                "publicar",
                "manifestar",
            ],
        )
        self.assertEqual(jobs["preparar_territorial"]["uses"], "./.github/workflows/preparacion-fuentes.yml")
        self.assertEqual(jobs["generar"]["uses"], "./.github/workflows/produccion-distritos.yml")
        self.assertEqual(jobs["preparar_electoral"]["uses"], "./.github/workflows/preparacion-resultados-electorales.yml")
        self.assertEqual(jobs["incorporar"]["uses"], "./.github/workflows/incorporacion-resultados-electorales.yml")
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

    def test_from_start_disables_checkpoint_reuse_but_keeps_prepared_sources_reusable(self):
        generation = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        preparation = (WF / "preparacion-fuentes.yml").read_text(encoding="utf-8")
        self.assertIn('if [[ "$mode" == from_start ]]', generation)
        self.assertIn('echo "from_stage=M01"', generation)
        self.assertIn("reutilizar_si_ya_preparada", preparation)
        orchestrator = ORCH.read_text(encoding="utf-8")
        self.assertIn("reutilizar_si_ya_preparada: true", orchestrator)

    def test_current_run_artifacts_can_feed_next_phase(self):
        orchestration = ORCH.read_text(encoding="utf-8")
        self.assertIn("source_package_run_id:", orchestration)
        self.assertIn("territorial_run_id:", orchestration)
        self.assertIn("electoral_package_run_id:", orchestration)
        self.assertIn("github.run_id", orchestration)
        generation = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        electoral = (WF / "incorporacion-resultados-electorales.yml").read_text(encoding="utf-8")
        self.assertIn("OVERRIDE_SOURCE_RUN_ID", generation)
        self.assertIn("OVERRIDE_RUN_ID", electoral)

    def test_failed_or_unvalidated_phase_blocks_following_phases(self):
        data = load(ORCH)
        jobs = data["jobs"]
        self.assertIn("needs.validar_territorial.result == 'success'", jobs["generar"]["if"])
        self.assertIn("needs.validar_generacion.result == 'success'", jobs["preparar_electoral"]["if"])
        self.assertIn("needs.validar_electoral.result == 'success'", jobs["incorporar"]["if"])
        self.assertIn("needs.validar_producto.result == 'success'", jobs["publicar"]["if"])
        self.assertIn("needs.actualizar_estado.result == 'success'", jobs["publicar"]["if"])
        for name in ("validar_territorial", "validar_generacion", "validar_electoral", "validar_producto"):
            self.assertEqual(jobs[name]["uses"], "./.github/workflows/_reutilizable-puerta-validacion.yml")

    def test_operational_state_is_synchronized_before_publication(self):
        data = load(ORCH)
        jobs = data["jobs"]
        self.assertIn("actualizar_estado", jobs)
        self.assertIn("publicado/estado_operativo.json", ORCH.read_text(encoding="utf-8"))
        self.assertIn("README.md publicado/estado_operativo.json publicado/dashboard", ORCH.read_text(encoding="utf-8"))
        self.assertIn("actualizar_estado", jobs["publicar"]["needs"])

    def test_plan_propagates_durable_digests_to_validation_gates(self):
        text = ORCH.read_text(encoding="utf-8")
        for key in (
            "existing_territorial_source_digest",
            "existing_territorial_product_digest",
            "existing_electoral_source_digest",
            "existing_electoral_product_digest",
        ):
            self.assertIn(key, text)
        self.assertIn("expected_digest:", text)

    def test_manifest_is_uploaded_and_durable_on_main(self):
        text = ORCH.read_text(encoding="utf-8")
        self.assertIn("ddd-full-run-manifest-${{ github.run_id }}", text)
        self.assertIn("retention-days: 90", text)
        self.assertIn("ejecuciones_completas/$GITHUB_RUN_ID.json", text)
        self.assertIn("github.ref_name == 'main'", text)

    def test_manifest_treats_skipped_scheduled_phase_as_failure(self):
        writer=(ROOT/"herramientas/escribir_manifest_ejecucion_completa.py").read_text(encoding="utf-8")
        self.assertIn('p["executed"] and p["result"] != "success"',writer)

    def test_reuse_plan_preserves_complete_canonical_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = root / "evidence"
            evidence.mkdir()
            (evidence / "territorial.json").write_text(json.dumps({"run_id": 101, "artifact_name": "m06", "artifact_sha256": "a"*64, "decision": "PASS"}), encoding="utf-8")
            (evidence / "source.json").write_text(json.dumps({"run_id": 102, "artifact_name": "electoral-source", "artifact_sha256": "b"*64}), encoding="utf-8")
            (evidence / "electoral.json").write_text(json.dumps({"run_id": 103, "artifact_name": "m08", "artifact_sha256": "c"*64}), encoding="utf-8")
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
                                        "preparation_evidence": {"run_id": 100, "artifact_name": "source-package", "artifact_sha256": "d"*64},
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
            )
            self.assertFalse(plan["run_prepare_territorial"])
            self.assertFalse(plan["run_generate"])
            self.assertFalse(plan["run_prepare_electoral"])
            self.assertFalse(plan["run_incorporate"])
            self.assertEqual(plan["optimization_algorithm"], "Canónico")
            self.assertEqual(plan["existing"]["electoral_product"]["run_id"], 103)

    def test_reuse_reschedules_phase_when_catalog_flag_lacks_durable_provenance(self):
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
                                        "preparation_status": "READY",
                                        "contract_path": "territorios/demo/config/demo_2025.yaml",
                                        "territorial_source_declaration": "territorios/demo/config/fuentes_oficiales.yaml",
                                        "electoral_source_declaration": "territorios/demo/config/elecciones/vigente.yaml",
                                        "territorial_sources_prepared": True,
                                        "territorial_contract_complete": True,
                                        "territorial_product_available": True,
                                        "electoral_source_prepared": True,
                                        "electoral_product_available": False,
                                        "territorial_certification": "PASS_WITH_GOVERNED_EXCEPTIONS",
                                        "production_authorization": "AUTHORIZED",
                                        "last_valid_checkpoint": {"run_id": 500, "stage": "M06"},
                                        "preparation_evidence": {"run_id": 400, "artifact_name": "source-package"},
                                        "evidence": {},
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
            )
            self.assertFalse(plan["run_prepare_territorial"])
            self.assertTrue(plan["run_generate"])
            self.assertTrue(plan["run_prepare_electoral"])
            self.assertTrue(plan["run_incorporate"])
            self.assertEqual(plan["existing"]["territorial_product"]["run_id"], 500)

    def test_gerrychain_50_is_preserved_in_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            catalog=root/"catalog.yaml"
            catalog.write_text(yaml.safe_dump({
                "schema":"ddd-preparation-catalog/1.1",
                "default_edition":"2025",
                "territories":[{
                    "territory_id":"demo","name":"Demo","editions":{"2025":{
                        "territory_declared":True,"preparation_status":"READY",
                        "contract_path":"territorios/demo/config/demo_2025.yaml",
                        "territorial_source_declaration":"territorios/demo/config/fuentes_oficiales.yaml",
                        "electoral_source_declaration":"territorios/demo/config/elecciones/vigente.yaml",
                        "territorial_contract_complete":True,
                        "territorial_sources_prepared":True,
                        "territorial_product_available":True,
                        "electoral_source_prepared":True,
                        "electoral_product_available":True,
                        "territorial_certification":"PASS",
                        "production_authorization":"AUTHORIZED",
                        "last_valid_checkpoint":{"run_id":10,"stage":"M06"},
                        "preparation_evidence":{"run_id":9,"artifact_name":"source"}
                    }}
                }]
            },allow_unicode=True,sort_keys=False),encoding="utf-8")
            plan=build_plan(
                territory="Demo",edition="2025",execution_mode="reuse",
                catalog=catalog,root_dir=root,optimization_algorithm="GerryChain 50",
            )
            self.assertEqual(plan["optimization_algorithm"],"GerryChain 50")
            self.assertTrue(plan["run_generate"])
            self.assertTrue(plan["run_incorporate"])

    def test_from_start_runs_all_business_phases(self):
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
            plan = build_plan(
                territory="Demo",
                edition="2025",
                execution_mode="from_start",
                catalog=catalog,
                root_dir=root,
            )
            self.assertTrue(plan["run_prepare_territorial"])
            self.assertTrue(plan["run_generate"])
            self.assertTrue(plan["run_prepare_electoral"])
            self.assertTrue(plan["run_incorporate"])


if __name__ == "__main__":
    unittest.main()
