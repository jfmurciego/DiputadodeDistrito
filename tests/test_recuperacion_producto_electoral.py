from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.persistir_producto_electoral_operacional import (
    ABSENT_FINGERPRINT,
    current_electoral_product_fingerprint,
    persist_electoral_product,
)
from tests.test_registro_producto_electoral_concurrencia import (
    SOURCE_COMMIT,
    clone,
    git,
    make_remote,
)


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "recuperar-producto-electoral-durable.yml"


class DurableElectoralProductRecoveryWorkflowTests(unittest.TestCase):
    def test_workflow_is_recovery_only_and_verifies_durable_identity(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        event = data.get("on") or data.get(True)
        self.assertEqual(set(event), {"workflow_dispatch"})

        for forbidden in (
            "ejecucion-completa-proyecto.yml",
            "_reutilizable-incorporacion-electoral.yml",
            "preparacion-fuentes.yml",
            "preparacion-resultados-electorales.yml",
            "desplegar-visor-publico.yml",
        ):
            self.assertNotIn(forbidden, text)

        self.assertIn('actions/runs/$SOURCE_RUN_ID', text)
        self.assertIn("head_sha", text)
        self.assertIn('canonical="ddd-state-$SOURCE_RUN_ID-M08"', text)
        self.assertIn("(.expired|not)", text)
        self.assertIn("Digest M08 distinto", text)
        self.assertIn('audit_name="ddd-audit-electoral-$SOURCE_RUN_ID"', text)
        self.assertIn(
            'report_name="ddd-electoral-application-report-$SOURCE_RUN_ID"',
            text,
        )
        self.assertIn("El reporte de incorporación no declara SUCCESS", text)
        self.assertIn("READY_PACKAGE", text)
        self.assertIn("_reutilizable-puerta-validacion.yml", text)
        self.assertIn("phase: electoral_product", text)
        self.assertIn("source_ref: ${{ inputs.source_commit }}", text)
        self.assertIn(
            "python -m herramientas.persistir_producto_electoral_operacional",
            text,
        )
        self.assertIn("--expected-previous-fingerprint", text)
        self.assertNotIn("git pull --rebase", text)

    def test_manual_recovery_requires_explicit_confirmation(self):
        data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        event = data.get("on") or data.get(True)
        confirm = event["workflow_dispatch"]["inputs"]["confirm_recovery"]
        self.assertEqual(confirm["type"], "boolean")
        self.assertFalse(confirm["default"])
        self.assertIn(
            "inputs.confirm_recovery",
            str(data["jobs"]["acreditar"]["if"]),
        )


@unittest.skipUnless(shutil.which("git"), "git executable required for recovery CAS tests")
class DurableElectoralProductRecoveryCasTests(unittest.TestCase):
    def test_identical_candidate_is_noop_without_new_commit(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            clone(remote, writer)

            candidate = dict(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
                run_id=401,
                artifact_name="ddd-state-401-M08",
                artifact_sha256="a" * 64,
                source_commit=SOURCE_COMMIT,
                target_branch="main",
            )
            first_sha = persist_electoral_product(**candidate)
            fingerprint = current_electoral_product_fingerprint(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
            )
            before_count = int(git(writer, "rev-list", "--count", "HEAD"))
            result = writer / "noop.json"

            second_sha = persist_electoral_product(
                **candidate,
                expected_previous_fingerprint=fingerprint,
                result_json=result,
            )

            self.assertEqual(second_sha, first_sha)
            self.assertEqual(int(git(writer, "rev-list", "--count", "HEAD")), before_count)
            payload = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "NO_OP")
            self.assertEqual(payload["head_sha"], first_sha)

    def test_unrelated_territory_change_is_rederived_and_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            other = base / "other"
            verify = base / "verify"
            clone(remote, writer)
            clone(remote, other)

            expected = current_electoral_product_fingerprint(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
            )
            self.assertEqual(expected, ABSENT_FINGERPRINT)

            def before_push(attempt: int) -> None:
                if attempt != 1:
                    return
                persist_electoral_product(
                    root_dir=other,
                    territory_id="beta",
                    edition="2025",
                    run_id=502,
                    artifact_name="ddd-state-502-M08",
                    artifact_sha256="b" * 64,
                    source_commit=SOURCE_COMMIT,
                    target_branch="main",
                )

            result = writer / "registered.json"
            persist_electoral_product(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
                run_id=501,
                artifact_name="ddd-state-501-M08",
                artifact_sha256="a" * 64,
                source_commit=SOURCE_COMMIT,
                target_branch="main",
                expected_previous_fingerprint=expected,
                result_json=result,
                before_push=before_push,
            )

            clone(remote, verify)
            alpha = json.loads(
                (
                    verify
                    / "territorios/alpha/evidencia/catalogo/electoral_product_2025.json"
                ).read_text(encoding="utf-8")
            )
            beta = json.loads(
                (
                    verify
                    / "territorios/beta/evidencia/catalogo/electoral_product_2025.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(alpha["run_id"], 501)
            self.assertEqual(beta["run_id"], 502)
            self.assertEqual(
                json.loads(result.read_text(encoding="utf-8"))["status"],
                "REGISTERED",
            )

    def test_same_territory_change_aborts_instead_of_overwriting(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            contender = base / "contender"
            verify = base / "verify"
            clone(remote, writer)
            clone(remote, contender)

            expected = current_electoral_product_fingerprint(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
            )
            self.assertEqual(expected, ABSENT_FINGERPRINT)

            def before_push(attempt: int) -> None:
                if attempt != 1:
                    return
                persist_electoral_product(
                    root_dir=contender,
                    territory_id="alpha",
                    edition="2025",
                    run_id=602,
                    artifact_name="ddd-state-602-M08",
                    artifact_sha256="c" * 64,
                    source_commit=SOURCE_COMMIT,
                    target_branch="main",
                )

            result = writer / "blocked.json"
            with self.assertRaisesRegex(
                RuntimeError,
                "ELECTORAL_PRODUCT_CONCURRENT_CHANGE",
            ):
                persist_electoral_product(
                    root_dir=writer,
                    territory_id="alpha",
                    edition="2025",
                    run_id=601,
                    artifact_name="ddd-state-601-M08",
                    artifact_sha256="d" * 64,
                    source_commit=SOURCE_COMMIT,
                    target_branch="main",
                    expected_previous_fingerprint=expected,
                    result_json=result,
                    before_push=before_push,
                )

            clone(remote, verify)
            receipt = json.loads(
                (
                    verify
                    / "territorios/alpha/evidencia/catalogo/electoral_product_2025.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(receipt["run_id"], 602)
            payload = json.loads(result.read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "CONCURRENT_PRODUCT_CHANGED")


if __name__ == "__main__":
    unittest.main()
