from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

from herramientas.materializar_evidencia_pre_m04 import (
    build_generation_evaluation,
    register_evidence_path,
)
from herramientas.promover_catalogo_tras_preparacion import promote
from herramientas.resolver_ejecucion_completa import generation_ready_contract


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"


def _write_minimal_prepared_source(root: Path) -> Path:
    (root / "configuracion").mkdir(parents=True, exist_ok=True)
    contract = root / "territorios/demo/config/demo_2025.yaml"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(
        yaml.safe_dump(
            {
                "meta": {
                    "territory_id": "demo",
                    "status": "source_prepared_pending_pre_m04",
                },
                "territory_contract": {
                    "status": "source_prepared_pending_pre_m04",
                },
                "generation_state": {
                    "source_prepared": True,
                    "generation_enabled": False,
                    "package_sha256": "b" * 64,
                    "compatibility_identity_sha256": "c" * 64,
                },
                "validation": {
                    "source_baseline": {
                        "package_sha256": "b" * 64,
                        "compatibility_identity_sha256": "c" * 64,
                        "population_year": 2024,
                        "section_year": 2024,
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (root / "configuracion/catalogo_preparacion.yaml").write_text(
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
                                "electoral_source_declaration": None,
                                "territorial_sources_prepared": True,
                                "territorial_contract_complete": True,
                                "territorial_product_available": False,
                                "electoral_source_prepared": False,
                                "electoral_product_available": False,
                                "territorial_certification": "NOT_CERTIFIED",
                                "production_authorization": "AUTHORIZED",
                                "last_valid_checkpoint": None,
                                "generation_enabled": False,
                                "preparation_evidence": {
                                    "run_id": 123,
                                    "artifact_name": "ddd-source-package-demo-2025-123",
                                    "artifact_sha256": "a" * 64,
                                    "package_sha256": "b" * 64,
                                    "compatibility_identity_sha256": "c" * 64,
                                    "population_year": 2024,
                                    "section_year": 2024,
                                },
                                "evidence": {},
                            }
                        },
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (root / "configuracion/catalogo_territorios_espana_2025.yaml").write_text(
        "- {territory_id: demo, status: source_prepared_pending_pre_m04}\n",
        encoding="utf-8",
    )
    return contract


class GenerationEvaluationStateTests(unittest.TestCase):
    def test_pending_blocked_and_technical_error_are_durable_but_never_enable_generation(self):
        for status in ("PENDING", "BLOCKED", "ERROR_TECHNICAL"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                contract = _write_minimal_prepared_source(root)
                with mock.patch(
                    "herramientas.materializar_evidencia_pre_m04._git_head",
                    return_value="1" * 40,
                ):
                    evaluation = build_generation_evaluation(
                        root_dir=root,
                        territory_id="demo",
                        edition="2025",
                        run_id=999,
                        status=status,
                        stage="TEST",
                        reason=f"{status} fixture",
                    )

                self.assertEqual(evaluation["evaluation_status"], status)
                self.assertEqual(evaluation["run_id"], 999)
                self.assertEqual(evaluation["source"]["run_id"], 123)
                self.assertFalse(evaluation["effective_gate"]["allowed"])

                rel = "territorios/demo/evidencia/catalogo/generation_preflight_2025.json"
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                register_evidence_path(
                    root_dir=root,
                    territory_id="demo",
                    edition="2025",
                    evidence_path=rel,
                    contract_path="territorios/demo/config/demo_2025.yaml",
                    evidence=evaluation,
                )

                catalog = yaml.safe_load(
                    (root / "configuracion/catalogo_preparacion.yaml").read_text(
                        encoding="utf-8"
                    )
                )
                state = catalog["territories"][0]["editions"]["2025"]
                self.assertFalse(state["generation_enabled"])
                self.assertEqual(state["evidence"]["generation_preflight"], rel)

                effective = yaml.safe_load(contract.read_text(encoding="utf-8"))
                self.assertTrue(effective["generation_state"]["source_prepared"])
                self.assertFalse(effective["generation_state"]["generation_enabled"])
                self.assertEqual(
                    effective["meta"]["status"],
                    "source_prepared_pending_pre_m04",
                )
                master = (
                    root / "configuracion/catalogo_territorios_espana_2025.yaml"
                ).read_text(encoding="utf-8")
                self.assertIn("status: source_prepared_pending_pre_m04", master)
                self.assertNotIn("status: generation_ready", master)

    def test_package_accreditation_stops_before_catalog_mutation_when_source_validation_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configuracion").mkdir(parents=True)
            (root / "configuracion/catalogo_preparacion.yaml").write_text(
                yaml.safe_dump(
                    {
                        "territories": [
                            {
                                "territory_id": "demo",
                                "name": "Demo",
                                "editions": {"2025": {}},
                            }
                        ]
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            declaration = root / "sources.yaml"
            declaration.write_text(
                yaml.safe_dump(
                    {
                        "territory": {
                            "population_year": 2024,
                            "section_year": 2024,
                        }
                    }
                ),
                encoding="utf-8",
            )
            package = root / "package"
            package.mkdir()
            with mock.patch(
                "herramientas.promover_catalogo_tras_preparacion.validate_prepared_package",
                return_value=(False, ["fixture inválido"]),
            ), mock.patch(
                "herramientas.promover_catalogo_tras_preparacion._set_catalog_state"
            ) as mutate:
                with self.assertRaisesRegex(
                    ValueError,
                    "Paquete territorial no promovible",
                ):
                    promote(
                        root_dir=root,
                        territory_id="demo",
                        edition="2025",
                        package=package,
                        source_declaration=declaration,
                        run_id=1,
                        artifact_name="artifact",
                        artifact_sha256="a" * 64,
                    )
                mutate.assert_not_called()

    def test_validation_precedes_catalog_accreditation_in_source_promoter(self):
        body = inspect.getsource(promote)
        self.assertLess(
            body.index("validate_prepared_package"),
            body.index("_set_catalog_state"),
        )
        self.assertLess(
            body.index("validate_compatibility_package"),
            body.index("_set_catalog_state"),
        )
        self.assertIn("require_ready=True", body)


class WorkflowDecouplingTests(unittest.TestCase):
    def test_01_finishes_with_prepared_source_and_full_orchestrator_blocks_on_generation_evaluation(self):
        preparation = yaml.safe_load(
            (WF / "preparacion-fuentes.yml").read_text(encoding="utf-8")
        )
        full = yaml.safe_load(
            (WF / "ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
        )
        jobs = preparation["jobs"]
        self.assertNotIn("pre_m04", jobs)
        self.assertIn("generation_pending", jobs)
        self.assertIn("generation_pending", jobs["resultado"]["needs"])

        full_jobs = full["jobs"]
        self.assertLess(
            list(full_jobs).index("preparar_territorial"),
            list(full_jobs).index("acreditar_generacion"),
        )
        self.assertLess(
            list(full_jobs).index("acreditar_generacion"),
            list(full_jobs).index("generar"),
        )
        self.assertTrue(full_jobs["acreditar_generacion"]["with"]["preflight_only"])
        self.assertIn("acreditar_generacion", full_jobs["generar"]["needs"])
        self.assertIn(
            "needs.acreditar_generacion.result == 'success'",
            full_jobs["generar"]["if"],
        )

    def test_activation_can_register_pair_without_generation_becoming_ready(self):
        activation = yaml.safe_load(
            (WF / "preparacion-legislatura-vigente.yml").read_text(encoding="utf-8")
        )
        pair = activation["jobs"]["registrar_par"]
        self.assertEqual(pair["needs"], ["planificar", "territorial", "electoral"])
        self.assertNotIn("generation", pair["if"].lower())
        self.assertIn(
            "needs.planificar.outputs.electoral_action != 'BLOCKED_PROVISIONAL'",
            pair["if"],
        )
        closing = activation["jobs"]["resultado"]
        self.assertIn("registrar_par", closing["needs"])
        self.assertNotIn("gener", closing["if"].lower())

    def test_source_and_pair_writers_use_common_rederived_persistence_not_rebase(self):
        territorial = yaml.safe_load(
            (WF / "preparacion-fuentes.yml").read_text(encoding="utf-8")
        )
        electoral = yaml.safe_load(
            (WF / "preparacion-resultados-electorales.yml").read_text(
                encoding="utf-8"
            )
        )
        activation = yaml.safe_load(
            (WF / "preparacion-legislatura-vigente.yml").read_text(encoding="utf-8")
        )

        territorial_run = next(
            step["run"]
            for step in territorial["jobs"]["registrar"]["steps"]
            if step.get("name") == "Registrar preparación territorial"
        )
        electoral_run = next(
            step["run"]
            for step in electoral["jobs"]["registrar"]["steps"]
            if step.get("name") == "Registrar preparación electoral"
        )
        pair_run = next(
            step["run"]
            for step in activation["jobs"]["registrar_par"]["steps"]
            if step.get("name") == "Materializar receipt versionado del par"
        )
        for body in (territorial_run, electoral_run, pair_run):
            self.assertIn("--persist", body)
            self.assertNotIn("git pull --rebase", body)

        for module in (
            ROOT / "herramientas/promover_catalogo_tras_preparacion.py",
            ROOT / "herramientas/promover_catalogo_operacional.py",
            ROOT / "herramientas/registrar_par_fuentes_legislatura.py",
        ):
            self.assertIn(
                "persist_rederived_tree",
                module.read_text(encoding="utf-8"),
                module.name,
            )

    def test_current_canarias_and_cataluna_source_pairs_and_generation_gates_are_consistent(self):
        catalog = yaml.safe_load(
            (ROOT / "configuracion/catalogo_preparacion.yaml").read_text(
                encoding="utf-8"
            )
        )
        rows = {row["territory_id"]: row for row in catalog["territories"]}
        for territory_id in ("canarias", "cataluna"):
            with self.subTest(territory=territory_id):
                state = rows[territory_id]["editions"]["2025"]
                self.assertTrue(state["territorial_sources_prepared"])
                self.assertTrue(state["electoral_source_prepared"])
                ready = generation_ready_contract(root_dir=ROOT, state=state, territory_id=territory_id)
                self.assertEqual(bool(state["generation_enabled"]), ready["allowed"])
                evidence = state.get("evidence") or {}
                pair_rel = evidence.get("prepared_source_pair")
                self.assertTrue(pair_rel)
                pair = json.loads((ROOT / pair_rel).read_text(encoding="utf-8"))
                self.assertEqual(pair["schema"], "ddd.prepared-source-pair/1.0")
                self.assertEqual(pair["territory_id"], territory_id)
                self.assertEqual(str(pair["edition"]), "2025")
                prepared = state["preparation_evidence"]
                paired_source = pair["territorial_source"]
                # Una reacreditación puede producir un run nuevo con los mismos
                # datos territoriales. La identidad material, no el run_id,
                # es la invariancia del par de fuentes.
                for key in (
                    "package_sha256",
                    "territorial_identity_sha256",
                    "compatibility_identity_sha256",
                ):
                    self.assertEqual(paired_source[key], prepared[key])
                self.assertIn("electoral_source", pair)
                preflight_rel = evidence.get("generation_preflight")
                if preflight_rel:
                    preflight = json.loads(
                        (ROOT / preflight_rel).read_text(encoding="utf-8")
                    )
                    self.assertEqual(preflight["territory_id"], territory_id)
                    preflight_source = preflight.get("source") or {}
                    for key in (
                        "package_sha256",
                        "territorial_identity_sha256",
                        "compatibility_identity_sha256",
                    ):
                        self.assertEqual(preflight_source[key], prepared[key])
                    gate = preflight.get("effective_gate") or {}
                    self.assertEqual(ready["allowed"], gate.get("allowed", False))
                    if ready["allowed"]:
                        self.assertEqual(preflight.get("decision"), "READY_FOR_FIRST_GENERATION")
                    else:
                        self.assertNotEqual(preflight.get("decision"), "READY_FOR_FIRST_GENERATION")

    def test_provisional_electoral_source_does_not_form_productive_pair(self):
        text = (WF / "preparacion-legislatura-vigente.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("BLOCKED_PROVISIONAL", text)
        self.assertIn(
            "Fuente electoral provisional: queda explícitamente bloqueada para producción.",
            text,
        )


if __name__ == "__main__":
    unittest.main()
