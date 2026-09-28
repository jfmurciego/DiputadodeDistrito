from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.detectar_producto_electoral_huerfano import (
    RecoveryBlocked,
    scan,
    validate_candidate,
)
from herramientas.persistir_producto_electoral_operacional import (
    ABSENT_FINGERPRINT,
    persist_electoral_product,
    recovery_context_fingerprint,
)
from tests.test_registro_producto_electoral_concurrencia import (
    SOURCE_COMMIT,
    clone,
    git,
    make_remote,
)


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"
MANIFEST_WRITER = ROOT / "herramientas" / "escribir_manifest_ejecucion_completa.py"

TERRITORY = "demo"
EDITION = "2025"
TERRITORIAL_RUN = 100
ELECTORAL_SOURCE_RUN = 200
CANDIDATE_RUN = 300
CANDIDATE_SHA = "c" * 40
M08_DIGEST = "a" * 64


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_root(root: Path, *, registered_candidate: bool = False, ambiguous: bool = False) -> None:
    registry = root / "configuracion" / "registro_electoral.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-election-registry/1.0",
                "edition": EDITION,
                "territories": {
                    TERRITORY: {
                        "name": "Demo",
                        "election_id": "demo_election_2025",
                    }
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    base = root / "territorios" / TERRITORY / "evidencia" / "catalogo"
    write_json(
        base / f"territorial_product_{EDITION}.json",
        {
            "schema": "ddd.catalog-evidence/1.0",
            "kind": "territorial_product",
            "territory_id": TERRITORY,
            "edition": EDITION,
            "run_id": TERRITORIAL_RUN,
            "artifact_name": f"ddd-state-{TERRITORIAL_RUN}-M06",
            "artifact_sha256": "1" * 64,
            "source_commit": "1" * 40,
            "decision": "PASS",
            "stage": "M06",
        },
    )
    write_json(
        base / f"electoral_source_{EDITION}.json",
        {
            "schema": "ddd.catalog-evidence/1.0",
            "kind": "electoral_source",
            "territory_id": TERRITORY,
            "edition": EDITION,
            "run_id": ELECTORAL_SOURCE_RUN,
            "artifact_name": f"ddd-electoral-package-{TERRITORY}-{EDITION}-{ELECTORAL_SOURCE_RUN}",
            "artifact_sha256": "2" * 64,
            "source_commit": "2" * 40,
            "election_id": "demo_election_2025",
        },
    )
    electoral_run = CANDIDATE_RUN if registered_candidate else 50
    write_json(
        base / f"electoral_product_{EDITION}.json",
        {
            "schema": "ddd.catalog-evidence/1.0",
            "kind": "electoral_product",
            "territory_id": TERRITORY,
            "edition": EDITION,
            "run_id": electoral_run,
            "artifact_name": f"ddd-state-{electoral_run}-M08",
            "artifact_sha256": M08_DIGEST if registered_candidate else "3" * 64,
            "source_commit": CANDIDATE_SHA if registered_candidate else "3" * 40,
            "stage": "M08",
        },
    )

    manifests = root / "territorios" / TERRITORY / "evidencia" / "ejecuciones_completas"
    runs = [CANDIDATE_RUN, CANDIDATE_RUN + 1] if ambiguous else [CANDIDATE_RUN]
    for run_id in runs:
        write_json(
            manifests / f"{run_id}.json",
            {
                "schema": "ddd.full-run-manifest/2.1",
                "territory_id": TERRITORY,
                "edition": EDITION,
                "workflow_run_id": run_id,
                "source_sha": CANDIDATE_SHA if run_id == CANDIDATE_RUN else "d" * 40,
                "status": "FAILED",
                "phases": [
                    {
                        "name": "02 · Generación de Distritos Autonómicos",
                        "executed": False,
                        "result": "skipped",
                        "run_id": TERRITORIAL_RUN,
                        "artifact": f"ddd-state-{TERRITORIAL_RUN}-M06",
                    },
                    {
                        "name": "04 · Incorporación de Resultados Electorales",
                        "executed": True,
                        "result": "failure",
                    },
                ],
            },
        )


def write_evidence(
    root: Path,
    *,
    run_id: int = CANDIDATE_RUN,
    expired: bool = False,
    digest_initial: str = M08_DIGEST,
    digest_confirmed: str | None = None,
    territorial_run: int = TERRITORIAL_RUN,
    election_id: str = "demo_election_2025",
) -> Path:
    evidence = root / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    digest_confirmed = digest_initial if digest_confirmed is None else digest_confirmed
    write_json(
        evidence / "run.json",
        {"id": run_id, "status": "completed", "head_sha": CANDIDATE_SHA},
    )

    def artifacts(digest: str) -> dict:
        return {
            "artifacts": [
                {
                    "id": 1,
                    "name": f"ddd-state-{run_id}-M08",
                    "expired": expired,
                    "digest": f"sha256:{digest}",
                },
                {
                    "id": 2,
                    "name": f"ddd-audit-electoral-{run_id}",
                    "expired": False,
                    "digest": "sha256:" + "4" * 64,
                },
                {
                    "id": 3,
                    "name": f"ddd-electoral-application-report-{run_id}",
                    "expired": False,
                    "digest": "sha256:" + "5" * 64,
                },
            ]
        }

    write_json(evidence / "artifacts.initial.json", artifacts(digest_initial))
    write_json(evidence / "artifacts.confirm.json", artifacts(digest_confirmed))
    write_json(
        evidence / "audit" / "production_status.json",
        {
            "decision": "PASS_WITH_EXCEPTIONS",
            "territory_id": TERRITORY,
            "workflow_run_id": run_id,
            "source_territorial_run_id": territorial_run,
            "electoral_application": True,
        },
    )
    write_json(
        evidence / "report" / "report.json",
        {
            "status": "SUCCESS",
            "territory_id": TERRITORY,
            "workflow_run_id": run_id,
            "territorial_source_run_id": territorial_run,
            "electoral_package_run_id": ELECTORAL_SOURCE_RUN,
        },
    )
    write_json(
        evidence / "report" / "validacion_paquete_electoral.json",
        {
            "decision": "READY_PACKAGE",
            "territory_id": TERRITORY,
            "edition": EDITION,
            "election_id": election_id,
        },
    )
    return evidence


class OrphanM08DetectionTests(unittest.TestCase):
    def test_valid_candidate_is_deterministic_and_accredited(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            scan_result = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)
            self.assertEqual(scan_result["status"], "CANDIDATE")
            evidence = write_evidence(root)
            result = validate_candidate(
                root_dir=root,
                territory_id=TERRITORY,
                edition=EDITION,
                candidate=scan_result["candidate"],
                evidence_root=evidence,
            )
            self.assertEqual(result["status"], "VALID")
            self.assertEqual(result["source_run_id"], CANDIDATE_RUN)
            self.assertEqual(result["artifact_sha256"], M08_DIGEST)
            self.assertEqual(result["territorial_run_id"], TERRITORIAL_RUN)
            self.assertEqual(result["election_id"], "demo_election_2025")

    def test_absent_materialized_candidate_blocks_when_failed_lineage_exists(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            evidence = write_evidence(root)
            data = json.loads((evidence / "artifacts.initial.json").read_text(encoding="utf-8"))
            data["artifacts"] = [row for row in data["artifacts"] if not row["name"].endswith("-M08")]
            write_json(evidence / "artifacts.initial.json", data)
            write_json(evidence / "artifacts.confirm.json", data)
            with self.assertRaisesRegex(RecoveryBlocked, "RECOVERY_CANDIDATE_ZERO"):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=evidence,
                )

    def test_ambiguous_failed_lineage_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root, ambiguous=True)
            with self.assertRaisesRegex(RecoveryBlocked, "RECOVERY_CANDIDATE_AMBIGUOUS"):
                scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)

    def test_expired_m08_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            with self.assertRaisesRegex(RecoveryBlocked, "RECOVERY_CANDIDATE_ZERO"):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=write_evidence(root, expired=True),
                )

    def test_digest_change_between_reads_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            with self.assertRaisesRegex(RecoveryBlocked, "RECOVERY_DIGEST_MISMATCH"):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=write_evidence(
                        root,
                        digest_initial="a" * 64,
                        digest_confirmed="b" * 64,
                    ),
                )

    def test_incompatible_current_territorial_product_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            with self.assertRaisesRegex(
                RecoveryBlocked,
                "RECOVERY_TERRITORIAL_PRODUCT_INCOMPATIBLE",
            ):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=write_evidence(root, territorial_run=999),
                )

    def test_registered_candidate_is_idempotently_not_rediscovered(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root, registered_candidate=True)
            result = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)
            self.assertEqual(result["status"], "NONE")
            self.assertEqual(result["candidate_count"], 0)


@unittest.skipUnless(shutil.which("git"), "git executable required for semantic CAS test")
class OrphanM08RecoveryCollisionTests(unittest.TestCase):
    def test_same_territory_context_change_blocks_after_push_collision(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            writer = base / "writer"
            contender = base / "contender"
            clone(remote, writer)
            clone(remote, contender)

            expected_context = recovery_context_fingerprint(
                root_dir=writer,
                territory_id="alpha",
                edition="2025",
            )

            def before_push(attempt: int) -> None:
                if attempt != 1:
                    return
                path = contender / "territorios/alpha/evidencia/catalogo/electoral_source_2025.json"
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["concurrent_marker"] = "changed"
                write_json(path, payload)
                git(contender, "add", str(path.relative_to(contender)))
                git(contender, "config", "user.name", "test")
                git(contender, "config", "user.email", "test@example.invalid")
                git(contender, "commit", "-m", "concurrent same-territory context change")
                git(contender, "push", "origin", "HEAD:main")

            with self.assertRaisesRegex(RuntimeError, "ELECTORAL_RECOVERY_CONTEXT_CHANGE"):
                persist_electoral_product(
                    root_dir=writer,
                    territory_id="alpha",
                    edition="2025",
                    run_id=701,
                    artifact_name="ddd-state-701-M08",
                    artifact_sha256="7" * 64,
                    source_commit=SOURCE_COMMIT,
                    target_branch="main",
                    expected_previous_fingerprint=ABSENT_FINGERPRINT,
                    expected_context_fingerprint=expected_context,
                    before_push=before_push,
                )


class FullRunRecoveryContractTests(unittest.TestCase):
    def test_00_uses_internal_recovery_without_executing_04(self):
        text = FULL.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        jobs = data["jobs"]
        self.assertIn("detectar_recuperacion_electoral", jobs)
        self.assertEqual(
            jobs["recuperar_electoral"]["uses"],
            "./.github/workflows/recuperar-producto-electoral-durable.yml",
        )
        self.assertIn(
            "needs.detectar_recuperacion_electoral.outputs.recover != 'true'",
            str(jobs["incorporar"]["if"]),
        )
        self.assertIn(
            "needs.recuperar_electoral.outputs.source_run_id",
            yaml.safe_dump(jobs["puerta_04"], allow_unicode=True),
        )
        publish_if = str(jobs["publicar"]["if"])
        self.assertIn("needs.planificar.outputs.publish_result == 'true'", publish_if)

    def _manifest(self, *, catalog_ok: bool, receipt_ok: bool) -> dict:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "manifest.json"
            args = [
                sys.executable,
                str(MANIFEST_WRITER),
                "--territory-id", TERRITORY,
                "--territory-name", "Demo",
                "--edition", EDITION,
                "--execution-mode", "reuse",
                "--optimization-algorithm", "Canónico",
                "--workflow-run-id", "999",
                "--source-sha", "9" * 40,
                "--publication-mode-requested", "electoral",
                "--publication-mode-effective", "electoral",
                "--publish-requested", "false",
                "--prepare-territorial-result", "skipped",
                "--generate-result", "skipped",
                "--prepare-electoral-result", "skipped",
                "--incorporate-result", "skipped",
                "--publish-result", "skipped",
                "--prepare-territorial-executed", "false",
                "--generate-executed", "false",
                "--prepare-electoral-executed", "false",
                "--incorporate-executed", "false",
                "--territorial-source-validation", "VALIDADO",
                "--territorial-product-validation", "VALIDADO",
                "--electoral-source-validation", "VALIDADO",
                "--electoral-product-validation", "VALIDADO",
                "--electoral-recovery-status", "VALID",
                "--electoral-recovery-result", "success",
                "--electoral-recovery-source-run-id", str(CANDIDATE_RUN),
                "--electoral-recovery-artifact", f"ddd-state-{CANDIDATE_RUN}-M08",
                "--electoral-recovery-digest", M08_DIGEST,
                "--electoral-recovery-source-commit", CANDIDATE_SHA,
                "--electoral-recovery-origin-manifest",
                f"territorios/{TERRITORY}/evidencia/ejecuciones_completas/{CANDIDATE_RUN}.json",
                "--electoral-recovery-registration-status", "REGISTERED",
                "--electoral-recovery-receipt-accredited", str(receipt_ok).lower(),
                "--electoral-recovery-catalog-accredited", str(catalog_ok).lower(),
                "--output", str(out),
            ]
            completed = subprocess.run(
                args,
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            self.assertEqual(completed.returncode, 0)
            return json.loads(out.read_text(encoding="utf-8"))

    def test_new_run_records_resumption_and_complete_only_after_accreditation(self):
        manifest = self._manifest(catalog_ok=True, receipt_ok=True)
        self.assertEqual(manifest["status"], "SUCCESS")
        self.assertEqual(manifest["completion_status"], "COMPLETE")
        self.assertEqual(manifest["resumption"]["origin_run_id"], CANDIDATE_RUN)
        self.assertEqual(manifest["resumption"]["kind"], "durable_electoral_product")
        phase04 = next(p for p in manifest["phases"] if p["name"].startswith("04 ·"))
        self.assertFalse(phase04["executed"])
        self.assertEqual(phase04["result"], "skipped")

    def test_new_run_is_incomplete_when_catalog_is_not_accredited(self):
        manifest = self._manifest(catalog_ok=False, receipt_ok=True)
        self.assertEqual(manifest["status"], "FAILED")
        self.assertEqual(manifest["completion_status"], "INCOMPLETE")
        self.assertIn("Reanudación de producto electoral durable", manifest["failed_phases"])


if __name__ == "__main__":
    unittest.main()
