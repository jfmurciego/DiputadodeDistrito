#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from herramientas.validar_puerta_ejecucion import PASS_DECISIONS


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class RecoveryBlocked(ValueError):
    pass


def _json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _first(root: Path, name: str) -> Path | None:
    rows = sorted(root.rglob(name)) if root.exists() else []
    return rows[0] if rows else None


def _digest(value: object) -> str:
    return str(value or "").strip().removeprefix("sha256:").lower()


def _receipt(root: Path, territory_id: str, edition: str, kind: str) -> dict:
    path = (
        root
        / "territorios"
        / territory_id
        / "evidencia"
        / "catalogo"
        / f"{kind}_{edition}.json"
    )
    return _json(path)


def _phase(manifest: dict, prefix: str) -> dict:
    for row in manifest.get("phases") or []:
        if str(row.get("name") or "").startswith(prefix):
            return row
    return {}


def _registered_election(root: Path, territory_id: str) -> str | None:
    import yaml

    path = root / "configuracion" / "registro_electoral.yaml"
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    row = (data.get("territories") or {}).get(territory_id) or {}
    value = str(row.get("election_id") or "").strip()
    return value or None


def structural_candidates(*, root_dir: Path, territory_id: str, edition: str) -> list[dict]:
    root = root_dir.resolve()
    territorial = _receipt(root, territory_id, edition, "territorial_product")
    if not territorial:
        return []
    territorial_run = territorial.get("run_id")
    territorial_artifact = str(territorial.get("artifact_name") or "")
    current_electoral = _receipt(root, territory_id, edition, "electoral_product")
    current_electoral_run = current_electoral.get("run_id")

    manifest_dir = (
        root
        / "territorios"
        / territory_id
        / "evidencia"
        / "ejecuciones_completas"
    )
    rows: list[dict] = []
    if not manifest_dir.is_dir():
        return rows

    for path in sorted(manifest_dir.glob("*.json")):
        manifest = _json(path)
        if (
            manifest.get("status") != "FAILED"
            or str(manifest.get("territory_id") or "") != territory_id
            or str(manifest.get("edition") or "") != str(edition)
        ):
            continue
        run_id = manifest.get("workflow_run_id")
        if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
            continue
        source_sha = str(manifest.get("source_sha") or "").lower()
        if not HEX40.fullmatch(source_sha):
            continue
        phase02 = _phase(manifest, "02 ·")
        phase04 = _phase(manifest, "04 ·")
        if (
            phase04.get("executed") is not True
            or phase04.get("result") == "success"
            or phase02.get("run_id") != territorial_run
            or str(phase02.get("artifact") or "") != territorial_artifact
        ):
            continue
        if (
            isinstance(current_electoral_run, int)
            and not isinstance(current_electoral_run, bool)
            and run_id <= current_electoral_run
        ):
            continue
        rows.append(
            {
                "run_id": run_id,
                "source_commit": source_sha,
                "manifest_path": str(path.relative_to(root)),
                "territorial_run_id": territorial_run,
                "territorial_artifact_name": territorial_artifact,
            }
        )
    return rows


def scan(*, root_dir: Path, territory_id: str, edition: str) -> dict:
    rows = structural_candidates(
        root_dir=root_dir,
        territory_id=territory_id,
        edition=edition,
    )
    if not rows:
        return {
            "schema": "ddd.orphan-electoral-product-scan/1.0",
            "status": "NONE",
            "reason": "NO_PENDING_FAILED_INCORPORATION",
            "candidate_count": 0,
            "candidates": [],
        }
    if len(rows) != 1:
        raise RecoveryBlocked(
            "RECOVERY_CANDIDATE_AMBIGUOUS: "
            f"{territory_id}/{edition}: {len(rows)} manifiestos fallidos corresponden "
            "al producto territorial vigente"
        )
    return {
        "schema": "ddd.orphan-electoral-product-scan/1.0",
        "status": "CANDIDATE",
        "reason": None,
        "candidate_count": 1,
        "candidate": rows[0],
        "candidates": rows,
    }


def _artifact_rows(data: dict, name: str) -> list[dict]:
    return [
        row
        for row in (data.get("artifacts") or [])
        if str(row.get("name") or "") == name and row.get("expired") is not True
    ]


def validate_candidate(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    candidate: dict,
    evidence_root: Path,
) -> dict:
    root = root_dir.resolve()
    evidence = evidence_root.resolve()
    run_id = candidate.get("run_id")
    source_commit = str(candidate.get("source_commit") or "").lower()
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        raise RecoveryBlocked("RECOVERY_IDENTITY_CONTRADICTORY: run_id inválido")
    if not HEX40.fullmatch(source_commit):
        raise RecoveryBlocked("RECOVERY_IDENTITY_CONTRADICTORY: source_commit inválido")

    run = _json(evidence / "run.json")
    if (
        run.get("id") != run_id
        or str(run.get("status") or "") != "completed"
        or str(run.get("head_sha") or "").lower() != source_commit
    ):
        raise RecoveryBlocked(
            "RECOVERY_IDENTITY_CONTRADICTORY: run/head_sha no coincide con el manifiesto durable"
        )

    initial = _json(evidence / "artifacts.initial.json")
    confirmed = _json(evidence / "artifacts.confirm.json")
    m08_name = f"ddd-state-{run_id}-M08"
    audit_name = f"ddd-audit-electoral-{run_id}"
    report_name = f"ddd-electoral-application-report-{run_id}"

    for name, code in (
        (m08_name, "M08"),
        (audit_name, "AUDIT"),
        (report_name, "REPORT"),
    ):
        first = _artifact_rows(initial, name)
        second = _artifact_rows(confirmed, name)
        if len(first) != 1 or len(second) != 1:
            raise RecoveryBlocked(
                f"RECOVERY_CANDIDATE_ZERO: {code} ausente, expirado o no único para run {run_id}"
            )
        if first[0].get("id") != second[0].get("id"):
            raise RecoveryBlocked(
                f"RECOVERY_IDENTITY_CONTRADICTORY: {code} cambió durante la acreditación"
            )

    first_m08 = _artifact_rows(initial, m08_name)[0]
    second_m08 = _artifact_rows(confirmed, m08_name)[0]
    digest_initial = _digest(first_m08.get("digest"))
    digest_confirmed = _digest(second_m08.get("digest"))
    if not HEX64.fullmatch(digest_initial):
        raise RecoveryBlocked("RECOVERY_DIGEST_INVALID: M08 sin digest SHA-256 acreditable")
    if digest_initial != digest_confirmed:
        raise RecoveryBlocked(
            "RECOVERY_DIGEST_MISMATCH: el digest M08 cambió durante la acreditación"
        )

    territorial = _receipt(root, territory_id, edition, "territorial_product")
    electoral_source = _receipt(root, territory_id, edition, "electoral_source")
    if not territorial or not electoral_source:
        raise RecoveryBlocked(
            "RECOVERY_IDENTITY_CONTRADICTORY: faltan receipts territorial o electoral vigentes"
        )
    territorial_run = territorial.get("run_id")
    electoral_source_run = electoral_source.get("run_id")

    audit = _json(_first(evidence / "audit", "production_status.json") or Path())
    if (
        str(audit.get("territory_id") or "") != territory_id
        or audit.get("workflow_run_id") != run_id
        or audit.get("source_territorial_run_id") != territorial_run
        or audit.get("electoral_application") is not True
        or str(audit.get("decision") or "") not in PASS_DECISIONS
    ):
        raise RecoveryBlocked(
            "RECOVERY_TERRITORIAL_PRODUCT_INCOMPATIBLE: auditoría M08 no corresponde "
            "al producto territorial vigente"
        )

    report = _json(_first(evidence / "report", "report.json") or Path())
    if (
        report.get("status") != "SUCCESS"
        or str(report.get("territory_id") or "") != territory_id
        or report.get("workflow_run_id") != run_id
        or report.get("territorial_source_run_id") != territorial_run
        or report.get("electoral_package_run_id") != electoral_source_run
    ):
        raise RecoveryBlocked(
            "RECOVERY_REPORT_INVALID: el informe SUCCESS no enlaza producto territorial "
            "y paquete electoral vigentes"
        )

    validation = _json(
        _first(evidence / "report", "validacion_paquete_electoral.json") or Path()
    )
    registered_election = _registered_election(root, territory_id)
    source_election = str(electoral_source.get("election_id") or "") or None
    candidate_election = str(validation.get("election_id") or "") or None
    if (
        validation.get("decision") != "READY_PACKAGE"
        or str(validation.get("territory_id") or "") != territory_id
        or str(validation.get("edition") or "") != str(edition)
        or not registered_election
        or source_election != registered_election
        or candidate_election != registered_election
    ):
        raise RecoveryBlocked(
            "RECOVERY_ELECTION_IDENTITY_MISMATCH: elección del candidato no coincide "
            "con registro y fuente electoral vigentes"
        )

    return {
        "schema": "ddd.orphan-electoral-product-candidate/1.0",
        "status": "VALID",
        "territory_id": territory_id,
        "edition": str(edition),
        "source_run_id": run_id,
        "artifact_name": m08_name,
        "artifact_sha256": digest_initial,
        "source_commit": source_commit,
        "audit_artifact_name": audit_name,
        "report_artifact_name": report_name,
        "territorial_run_id": territorial_run,
        "territorial_artifact_name": territorial.get("artifact_name"),
        "electoral_source_run_id": electoral_source_run,
        "election_id": registered_election,
        "origin_manifest": candidate.get("manifest_path"),
    }


def _write(path: Path | None, payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path is None:
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("--root-dir", type=Path, default=Path("."))
    scan_p.add_argument("--territory-id", required=True)
    scan_p.add_argument("--edition", required=True)
    scan_p.add_argument("--output", type=Path)

    validate_p = sub.add_parser("validate")
    validate_p.add_argument("--root-dir", type=Path, default=Path("."))
    validate_p.add_argument("--territory-id", required=True)
    validate_p.add_argument("--edition", required=True)
    validate_p.add_argument("--candidate-json", type=Path, required=True)
    validate_p.add_argument("--evidence-root", type=Path, required=True)
    validate_p.add_argument("--output", type=Path)

    ns = ap.parse_args()
    try:
        if ns.command == "scan":
            payload = scan(
                root_dir=ns.root_dir,
                territory_id=ns.territory_id,
                edition=ns.edition,
            )
        else:
            candidate_payload = _json(ns.candidate_json)
            candidate = candidate_payload.get("candidate") or candidate_payload
            payload = validate_candidate(
                root_dir=ns.root_dir,
                territory_id=ns.territory_id,
                edition=ns.edition,
                candidate=candidate,
                evidence_root=ns.evidence_root,
            )
        _write(ns.output, payload)
        return 0
    except RecoveryBlocked as exc:
        payload = {
            "schema": "ddd.orphan-electoral-product-candidate/1.0",
            "status": "BLOCKED",
            "reason": str(exc),
        }
        _write(getattr(ns, "output", None), payload)
        print(f"::error::{exc}")
        return 46


if __name__ == "__main__":
    raise SystemExit(main())
