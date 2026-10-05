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
    resolve_candidates,
    scan,
    structural_candidates,
    validate_candidate,
)
from herramientas.persistir_producto_electoral_operacional import (
    ABSENT_FINGERPRINT,
    persist_electoral_product,
    recovery_context_fingerprint,
)
from herramientas.resolver_ejecucion_completa import build_plan
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
    decoy_count: int = 0,
    source_commit: str = CANDIDATE_SHA,
    evidence_dir: Path | None = None,
) -> Path:
    evidence = evidence_dir if evidence_dir is not None else root / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    digest_confirmed = digest_initial if digest_confirmed is None else digest_confirmed
    write_json(
        evidence / "run.json",
        {"id": run_id, "status": "completed", "head_sha": source_commit},
    )

    def artifacts(digest: str) -> dict:
        rows = [
            {
                "id": 1000 + i,
                "name": f"decoy-{i:03d}",
                "expired": False,
                "digest": "sha256:" + "6" * 64,
            }
            for i in range(decoy_count)
        ]
        rows.extend(
            [
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
        )
        return {"total_count": len(rows), "artifacts": rows}

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

    def test_absent_m08_allows_fresh_incorporation_after_failed_history(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            evidence = write_evidence(root)
            data = json.loads((evidence / "artifacts.initial.json").read_text(encoding="utf-8"))
            data["artifacts"] = [row for row in data["artifacts"] if not row["name"].endswith("-M08")]
            data["total_count"] = len(data["artifacts"])
            write_json(evidence / "artifacts.initial.json", data)
            write_json(evidence / "artifacts.confirm.json", data)
            result = validate_candidate(
                root_dir=root,
                territory_id=TERRITORY,
                edition=EDITION,
                candidate=candidate,
                evidence_root=evidence,
            )
            self.assertEqual(result["status"], "NO_RECOVERY")
            self.assertEqual(result["reason"], "M08_ABSENT")

    def test_m08_after_first_100_artifacts_is_found_from_complete_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            evidence = write_evidence(root, decoy_count=101)
            initial = json.loads((evidence / "artifacts.initial.json").read_text(encoding="utf-8"))
            self.assertGreater(initial["total_count"], 100)
            self.assertGreater(
                next(
                    i
                    for i, row in enumerate(initial["artifacts"])
                    if row["name"] == f"ddd-state-{CANDIDATE_RUN}-M08"
                ),
                99,
            )
            result = validate_candidate(
                root_dir=root,
                territory_id=TERRITORY,
                edition=EDITION,
                candidate=candidate,
                evidence_root=evidence,
            )
            self.assertEqual(result["status"], "VALID")

    def test_incomplete_artifact_inventory_blocks_absence_decision(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            evidence = write_evidence(root)
            for filename in ("artifacts.initial.json", "artifacts.confirm.json"):
                path = evidence / filename
                data = json.loads(path.read_text(encoding="utf-8"))
                data["artifacts"] = []
                data["total_count"] = 101
                write_json(path, data)
            with self.assertRaisesRegex(
                RecoveryBlocked,
                "RECOVERY_ARTIFACT_INVENTORY_INCOMPLETE",
            ):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=evidence,
                )

    def test_workflow_paginates_both_artifact_inventory_reads(self):
        jobs = yaml.safe_load(FULL.read_text(encoding="utf-8"))["jobs"]
        detect_step = next(
            step
            for step in jobs["detectar_recuperacion_electoral"]["steps"]
            if step.get("name") == "Resolver y acreditar candidato huérfano"
        )
        script = detect_step["run"]
        self.assertEqual(script.count("gh api --paginate --slurp"), 2)
        self.assertEqual(script.count("total_count:(.[0].total_count // 0)"), 2)
        self.assertIn("jq -c '.candidates[]'", script)
        self.assertIn("detectar_producto_electoral_huerfano resolve", script)
        self.assertIn('evidence=".ddd-orphan-recovery/evidence/$run_id"', script)

    def test_multiple_failed_manifests_are_not_products_until_accredited(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root, ambiguous=True)
            result = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)
            self.assertEqual(result["status"], "CANDIDATES")
            self.assertEqual(result["candidate_count"], 2)
            self.assertEqual(
                [row["run_id"] for row in result["candidates"]],
                [CANDIDATE_RUN, CANDIDATE_RUN + 1],
            )

    def test_m08_absence_barrier_retires_only_older_failed_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root, ambiguous=True)
            manifest_path = (
                root
                / "territorios"
                / TERRITORY
                / "evidencia"
                / "ejecuciones_completas"
                / f"{CANDIDATE_RUN + 1}.json"
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["execution_mode"] = "reuse"
            manifest["publication_mode_effective"] = "electoral"
            manifest["resumption"] = {
                "kind": "durable_electoral_product",
                "status": "NO_RECOVERY",
                "result": "skipped",
                "reason": "M08_ABSENT",
                "origin_run_id": None,
                "origin_manifest": None,
                "artifact": None,
                "artifact_digest": None,
                "source_commit": None,
                "registration_status": None,
                "receipt_accredited": False,
                "catalog_accredited": False,
            }
            write_json(manifest_path, manifest)

            result = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)
            self.assertEqual(result["status"], "CANDIDATE")
            self.assertEqual(result["candidate"]["run_id"], CANDIDATE_RUN + 1)
            self.assertEqual(result["absence_barrier_run_id"], CANDIDATE_RUN + 1)
            self.assertEqual(
                [row["run_id"] for row in result["retired_candidates"]],
                [CANDIDATE_RUN],
            )

    def _two_candidates_after_absence_barrier(self, root: Path) -> dict:
        write_root(root, ambiguous=True)
        manifests = (
            root
            / "territorios"
            / TERRITORY
            / "evidencia"
            / "ejecuciones_completas"
        )
        barrier_path = manifests / f"{CANDIDATE_RUN}.json"
        barrier = json.loads(barrier_path.read_text(encoding="utf-8"))
        barrier["execution_mode"] = "reuse"
        barrier["publication_mode_effective"] = "electoral"
        barrier["resumption"] = {
            "kind": "durable_electoral_product",
            "status": "NO_RECOVERY",
            "result": "skipped",
            "reason": "M08_ABSENT",
            "origin_run_id": None,
            "origin_manifest": None,
            "artifact": None,
            "artifact_digest": None,
            "source_commit": None,
            "registration_status": None,
            "receipt_accredited": False,
            "catalog_accredited": False,
        }
        write_json(barrier_path, barrier)
        result = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)
        self.assertEqual(result["status"], "CANDIDATES")
        self.assertEqual(result["candidate_count"], 2)
        return result

    def test_two_structural_candidates_without_m08_allow_fresh_incorporation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scan_result = self._two_candidates_after_absence_barrier(root)
            evidence_root = root / "multi-evidence"
            for candidate in scan_result["candidates"]:
                run_id = candidate["run_id"]
                evidence = write_evidence(
                    root,
                    run_id=run_id,
                    source_commit=candidate["source_commit"],
                    evidence_dir=evidence_root / str(run_id),
                )
                for filename in ("artifacts.initial.json", "artifacts.confirm.json"):
                    path = evidence / filename
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    payload["artifacts"] = [
                        row for row in payload["artifacts"]
                        if row["name"] != f"ddd-state-{run_id}-M08"
                    ]
                    payload["total_count"] = len(payload["artifacts"])
                    write_json(path, payload)
            resolved = resolve_candidates(
                root_dir=root,
                territory_id=TERRITORY,
                edition=EDITION,
                candidates=scan_result["candidates"],
                evidence_root=evidence_root,
            )
            self.assertEqual(resolved["status"], "NO_RECOVERY")
            self.assertEqual(resolved["reason"], "M08_ABSENT")
            self.assertEqual(
                resolved["absent_run_ids"],
                [CANDIDATE_RUN, CANDIDATE_RUN + 1],
            )

    def test_two_real_m08_products_after_barrier_still_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scan_result = self._two_candidates_after_absence_barrier(root)
            evidence_root = root / "multi-evidence"
            for index, candidate in enumerate(scan_result["candidates"]):
                write_evidence(
                    root,
                    run_id=candidate["run_id"],
                    source_commit=candidate["source_commit"],
                    digest_initial=("a" if index == 0 else "b") * 64,
                    evidence_dir=evidence_root / str(candidate["run_id"]),
                )
            with self.assertRaisesRegex(
                RecoveryBlocked,
                "RECOVERY_CANDIDATE_AMBIGUOUS.*productos M08 recuperables múltiples",
            ):
                resolve_candidates(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidates=scan_result["candidates"],
                    evidence_root=evidence_root,
                )

    def test_multiple_candidates_with_incompatible_lineage_still_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            scan_result = self._two_candidates_after_absence_barrier(root)
            evidence_root = root / "multi-evidence"
            first, second = scan_result["candidates"]
            first_evidence = write_evidence(
                root,
                run_id=first["run_id"],
                source_commit=first["source_commit"],
                evidence_dir=evidence_root / str(first["run_id"]),
            )
            for filename in ("artifacts.initial.json", "artifacts.confirm.json"):
                path = first_evidence / filename
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["artifacts"] = [
                    row for row in payload["artifacts"]
                    if row["name"] != f"ddd-state-{first['run_id']}-M08"
                ]
                payload["total_count"] = len(payload["artifacts"])
                write_json(path, payload)
            write_evidence(
                root,
                run_id=second["run_id"],
                source_commit=second["source_commit"],
                territorial_run=999,
                evidence_dir=evidence_root / str(second["run_id"]),
            )
            with self.assertRaisesRegex(
                RecoveryBlocked,
                "RECOVERY_TERRITORIAL_PRODUCT_INCOMPATIBLE",
            ):
                resolve_candidates(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidates=scan_result["candidates"],
                    evidence_root=evidence_root,
                )

    def test_expired_m08_blocks_with_specific_cause(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            with self.assertRaisesRegex(RecoveryBlocked, "RECOVERY_ARTIFACT_EXPIRED"):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=write_evidence(root, expired=True),
                )

    def test_duplicate_live_m08_blocks_as_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_root(root)
            candidate = scan(root_dir=root, territory_id=TERRITORY, edition=EDITION)["candidate"]
            evidence = write_evidence(root)
            for filename in ("artifacts.initial.json", "artifacts.confirm.json"):
                path = evidence / filename
                data = json.loads(path.read_text(encoding="utf-8"))
                m08 = next(row for row in data["artifacts"] if row["name"].endswith("-M08"))
                duplicate = dict(m08)
                duplicate["id"] = 99
                data["artifacts"].append(duplicate)
                data["total_count"] = len(data["artifacts"])
                write_json(path, data)
            with self.assertRaisesRegex(RecoveryBlocked, "RECOVERY_ARTIFACT_AMBIGUOUS"):
                validate_candidate(
                    root_dir=root,
                    territory_id=TERRITORY,
                    edition=EDITION,
                    candidate=candidate,
                    evidence_root=evidence,
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


class RealFreshIncorporationRegressionTests(unittest.TestCase):
    REAL_FAILURES = {
        "castilla_la_mancha": [36488755336],
        "ceuta": [36529371078, 36529371312],
    }

    def _assert_real_case(
        self,
        *,
        territory_name: str,
        territory_id: str,
        failed_candidate_run: int,
        persisted_false_runs: tuple[int, ...],
        expected_plan_block: str | None = None,
    ) -> None:
        if expected_plan_block is None:
            plan = build_plan(
                territory=territory_name,
                edition="2025",
                execution_mode="reuse",
                catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
                root_dir=ROOT,
                optimization_algorithm="Canónico",
                force_selected_algorithm=True,
            )
            self.assertFalse(plan["run_prepare_territorial"])
            self.assertFalse(plan["run_generate"])
            self.assertFalse(plan["run_prepare_electoral"])
            self.assertTrue(plan["run_incorporate"])
        else:
            with self.assertRaisesRegex(ValueError, expected_plan_block):
                build_plan(
                    territory=territory_name,
                    edition="2025",
                    execution_mode="reuse",
                    catalog=ROOT / "configuracion/catalogo_preparacion.yaml",
                    root_dir=ROOT,
                    optimization_algorithm="Canónico",
                    force_selected_algorithm=True,
                )

        scan_result = scan(
            root_dir=ROOT,
            territory_id=territory_id,
            edition="2025",
        )
        self.assertEqual(scan_result["status"], "CANDIDATE")
        self.assertEqual(scan_result["candidate_count"], 1)
        self.assertEqual(scan_result["candidate"]["run_id"], failed_candidate_run)
        for run_id in persisted_false_runs:
            self.assertNotIn(
                run_id,
                [row["run_id"] for row in scan_result["candidates"]],
            )

        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td)
            candidate = scan_result["candidate"]
            write_json(
                evidence / "run.json",
                {
                    "id": candidate["run_id"],
                    "status": "completed",
                    "head_sha": candidate["source_commit"],
                },
            )
            # Ausencia acreditada: dos lecturas independientes sin M08.
            write_json(evidence / "artifacts.initial.json", {"total_count": 0, "artifacts": []})
            write_json(evidence / "artifacts.confirm.json", {"total_count": 0, "artifacts": []})
            validation = validate_candidate(
                root_dir=ROOT,
                territory_id=territory_id,
                edition="2025",
                candidate=candidate,
                evidence_root=evidence,
            )
        self.assertEqual(validation["status"], "NO_RECOVERY")
        self.assertEqual(validation["reason"], "M08_ABSENT")

        jobs = yaml.safe_load(FULL.read_text(encoding="utf-8"))["jobs"]
        detect_step = next(
            step
            for step in jobs["detectar_recuperacion_electoral"]["steps"]
            if step.get("name") == "Resolver y acreditar candidato huérfano"
        )
        detect_script = detect_step["run"]
        self.assertIn('if [[ "$status" == NO_RECOVERY ]]', detect_script)
        self.assertIn('echo "recover=false"', detect_script)

        incorporate_if = str(jobs["incorporar"]["if"])
        self.assertIn("needs.planificar.outputs.run_incorporate == 'true'", incorporate_if)
        self.assertIn(
            "needs.detectar_recuperacion_electoral.result == 'success'",
            incorporate_if,
        )
        self.assertIn(
            "needs.detectar_recuperacion_electoral.outputs.recover != 'true'",
            incorporate_if,
        )

    def test_castilla_la_mancha_current_source_lineage_blocks_reuse(self):
        # El candidato M08 sigue siendo auditable, pero la fuente territorial
        # viva fue renovada después del producto M06 vigente. El planner debe
        # bloquear la reutilización del producto histórico hasta que exista un
        # lineage que acredite compatibilidad con la fuente territorial actual.
        result = scan(
            root_dir=ROOT,
            territory_id="castilla_la_mancha",
            edition="2025",
        )
        self.assertEqual(result["absence_barrier_run_id"], 36551586302)
        self.assertEqual(
            [row["run_id"] for row in result["retired_candidates"]],
            [36444657976],
        )
        self.assertEqual(
            [row["run_id"] for row in structural_candidates(
                root_dir=ROOT,
                territory_id="castilla_la_mancha",
                edition="2025",
            )],
            [36551586302],
        )

        self._assert_real_case(
            territory_name="Castilla-La Mancha",
            territory_id="castilla_la_mancha",
            failed_candidate_run=36551586302,
            persisted_false_runs=(36444657976, 36488755336),
            expected_plan_block=(
                r"CONTINUE_DURABLE_BLOCK: Castilla-La Mancha: "
                r"DURABLE_LINEAGE_INCOMPATIBLE: "
                r"territorial_source→territorial_product"
            ),
        )

    def test_baleares_36573474139_territorial_failure_never_becomes_m08_candidate(self):
        manifest_path = (
            ROOT
            / "territorios"
            / "illes_balears"
            / "evidencia"
            / "ejecuciones_completas"
            / "36573474139.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["status"], "FAILED")
        self.assertEqual(manifest["publication_mode_effective"], "territorial_only")

        phase02 = next(
            row
            for row in manifest["phases"]
            if row["name"].startswith("02 ·")
        )
        phase04 = next(
            row
            for row in manifest["phases"]
            if row["name"].startswith("04 ·")
        )
        self.assertTrue(phase02["executed"])
        self.assertEqual(phase02["result"], "failure")
        self.assertEqual(phase04["scope"], "OUT_OF_SCOPE")
        self.assertFalse(phase04["executed"])
        self.assertEqual(phase04["result"], "skipped")

        candidates = structural_candidates(
            root_dir=ROOT,
            territory_id="illes_balears",
            edition="2025",
        )
        self.assertNotIn(36573474139, [row["run_id"] for row in candidates])

    def test_ceuta_historical_candidates_survive_but_current_source_lineage_blocks_reuse(self):
        # Los candidatos históricos siguen siendo auditables, pero la fuente
        # territorial viva de Ceuta fue renovada después del producto M06
        # vigente. Continuar ese producto con la fuente nueva debe bloquearse
        # por linaje en vez de fingir que la ruta histórica sigue reutilizable.
        self._assert_real_case(
            territory_name="Ceuta",
            territory_id="ceuta",
            failed_candidate_run=36482903970,
            persisted_false_runs=(36529371312,),
            expected_plan_block=(
                r"CONTINUE_DURABLE_BLOCK: Ceuta: DURABLE_LINEAGE_INCOMPATIBLE: "
                r"territorial_source→territorial_product"
            ),
        )


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
        self.assertIn("needs.puerta_04.result == 'success'", publish_if)
        self.assertNotIn("NO_RECOVERY", publish_if)

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
