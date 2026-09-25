from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.preflight_preparacion_fuente import preflight
from herramientas.evaluar_persistencia_preparacion import resolve_persist_state, terminal_decision

ROOT = Path(__file__).resolve().parents[1]
WF01 = ROOT / ".github" / "workflows" / "preparacion-fuentes.yml"
WF03 = ROOT / ".github" / "workflows" / "preparacion-resultados-electorales.yml"
WF00 = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"


def write_catalog(root: Path, state: dict):
    path = root / "configuracion" / "catalogo_preparacion.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [
                    {
                        "territory_id": "demo",
                        "name": "Demo",
                        "editions": {"2025": state},
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


class CommonPreparationPreflightTests(unittest.TestCase):
    def test_territorial_registered_source_requires_complete_registry_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = "a" * 64
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": False,
                    "preparation_evidence": {
                        "run_id": 123,
                        "artifact_name": "ddd-source-package-demo-2025-123",
                        "artifact_sha256": digest,
                    },
                },
            )
            result = preflight(root, "territorial", "Demo", "2025")
            self.assertTrue(result["registered"])
            self.assertEqual(result["run_id"], 123)
            self.assertEqual(result["artifact_sha256"], digest)

    def test_territorial_prepared_without_registry_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": False,
                },
            )
            with self.assertRaisesRegex(ValueError, "sin preparation_evidence"):
                preflight(root, "territorial", "Demo", "2025")

    def test_electoral_registered_source_requires_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt = root / "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                json.dumps(
                    {
                        "schema": "ddd.catalog-evidence/1.0",
                        "kind": "electoral_source",
                        "territory_id": "demo",
                        "edition": "2025",
                        "run_id": 456,
                        "artifact_name": "ddd-electoral-package-demo-2025-456",
                        "artifact_sha256": "b" * 64,
                        "election_id": "demo_2024",
                    }
                ),
                encoding="utf-8",
            )
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": True,
                    "evidence": {
                        "electoral_source": "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
                    },
                },
            )
            result = preflight(root, "electoral", "demo", "2025")
            self.assertTrue(result["registered"])
            self.assertEqual(result["run_id"], 456)
            self.assertEqual(result["election_id"], "demo_2024")

    def test_electoral_prepared_with_missing_receipt_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": True,
                    "evidence": {
                        "electoral_source": "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
                    },
                },
            )
            with self.assertRaisesRegex(ValueError, "registro electoral inexistente"):
                preflight(root, "electoral", "Demo", "2025")

    def test_unprepared_source_has_no_fabricated_registered_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": False,
                    "electoral_source_prepared": False,
                },
            )
            self.assertFalse(preflight(root, "territorial", "Demo", "2025")["registered"])
            self.assertFalse(preflight(root, "electoral", "Demo", "2025")["registered"])

    def test_00_passes_same_edition_into_03(self):
        data = yaml.safe_load(WF00.read_text(encoding="utf-8"))
        self.assertEqual(
            data["jobs"]["preparar_electoral"]["with"]["data_edition"],
            "${{ needs.planificar.outputs.edition }}",
        )

    def test_01_reuse_path_skips_all_acquisition_steps(self):
        data = yaml.safe_load(WF01.read_text(encoding="utf-8"))
        steps = data["jobs"]["territoriales"]["steps"]
        gated = [
            next(step for step in steps if str(step.get("uses", "")).startswith("docker/setup-buildx-action@")),
            next(step for step in steps if str(step.get("uses", "")).startswith("docker/build-push-action@")),
            next(step for step in steps if step.get("id") == "mode"),
            next(step for step in steps if step.get("name") == "Adquirir y congelar fuentes"),
        ]
        for step in gated:
            self.assertIn("reused_candidate != 'true'", step["if"])

    def test_persistence_matrix_manual_and_reusable_is_common_to_01_and_03(self):
        # workflow_dispatch no declara persist_state: ausencia => persistencia obligatoria.
        self.assertTrue(resolve_persist_state(None))
        self.assertTrue(resolve_persist_state("null"))

        # workflow_call conserva exactamente el booleano recibido.
        self.assertTrue(resolve_persist_state(True))
        self.assertFalse(resolve_persist_state(False))

        # Manual exitoso: el registro es obligatorio para terminar SUCCESS.
        self.assertEqual(
            terminal_decision(
                preparation_result="success",
                registration_result="success",
                persist_state=resolve_persist_state(None),
            )["status"],
            "SUCCESS",
        )
        for registration_result in ("skipped", "failure"):
            self.assertEqual(
                terminal_decision(
                    preparation_result="success",
                    registration_result=registration_result,
                    persist_state=resolve_persist_state(None),
                )["status"],
                "FAILURE",
            )

        # Reutilizable persistente: misma obligación; persist_state=false permite omitir.
        self.assertEqual(
            terminal_decision(
                preparation_result="success",
                registration_result="success",
                persist_state=True,
            )["status"],
            "SUCCESS",
        )
        self.assertEqual(
            terminal_decision(
                preparation_result="success",
                registration_result="skipped",
                persist_state=True,
            )["status"],
            "FAILURE",
        )
        self.assertEqual(
            terminal_decision(
                preparation_result="success",
                registration_result="skipped",
                persist_state=False,
            )["status"],
            "SUCCESS",
        )

    def test_both_workflows_resolve_persistence_before_registration_and_gate_terminal_result(self):
        for path, preparation_job in ((WF01, "territoriales"), (WF03, "electorales")):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            trigger = data.get("on") or data.get(True)
            self.assertNotIn("persist_state", trigger["workflow_dispatch"]["inputs"])
            self.assertIn("persist_state", trigger["workflow_call"]["inputs"])
            self.assertTrue(trigger["workflow_call"]["inputs"]["persist_state"]["default"])

            resolver = data["jobs"]["resolver"]
            self.assertEqual(resolver["outputs"]["persist_state"], "${{ steps.resolve.outputs.persist_state }}")
            resolve_step = next(step for step in resolver["steps"] if step.get("id") == "resolve")
            self.assertEqual(resolve_step["env"]["PERSIST_INPUT"], "${{ toJSON(inputs.persist_state) }}")
            self.assertIn("evaluar_persistencia_preparacion.py resolve", resolve_step["run"])

            registrar = data["jobs"]["registrar"]
            self.assertIn("needs.resolver.outputs.persist_state == 'true'", registrar["if"])

            terminal = data["jobs"]["resultado"]
            self.assertEqual(terminal["if"], "${{ always() }}")
            self.assertIn("registrar", terminal["needs"])
            terminal_step = next(
                step for step in terminal["steps"]
                if step.get("name") == "Exigir registro cuando la persistencia es obligatoria"
            )
            self.assertEqual(
                terminal_step["env"]["PREPARATION_RESULT"],
                f"${{{{ needs.{preparation_job}.result }}}}",
            )
            self.assertEqual(
                terminal_step["env"]["REGISTRATION_RESULT"],
                "${{ needs.registrar.result }}",
            )
            self.assertIn("evaluar_persistencia_preparacion.py terminal", terminal_step["run"])

    def test_registration_verifies_current_durable_identity_for_new_and_reused_package(self):
        for path in (WF01, WF03):
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            registrar = data["jobs"]["registrar"]
            registration_step = next(
                step for step in registrar["steps"]
                if str(step.get("name", "")).startswith("Registrar ")
            )
            script = registration_step["run"]
            self.assertIn("preflight_preparacion_fuente.py", script)
            self.assertIn('== "$GITHUB_RUN_ID"', script)
            self.assertIn("artifact_sha256", script)
            self.assertNotIn("git diff --cached --quiet && exit 0", script)

    def test_03_reuse_path_feeds_downloaded_package_into_reuse_engine(self):
        data = yaml.safe_load(WF03.read_text(encoding="utf-8"))
        steps = data["jobs"]["electorales"]["steps"]
        previous = next(step for step in steps if step.get("id") == "previous")
        prepare = next(step for step in steps if step.get("id") == "prepare")
        self.assertIn("REGISTERED_ARTIFACT_SHA256", previous["run"])
        self.assertIn("--previous-package .ddd-electoral-previous", prepare["run"])
        self.assertIn("--previous-run-id", prepare["run"])
        self.assertIn("--previous-artifact-name", prepare["run"])


if __name__ == "__main__":
    unittest.main()
