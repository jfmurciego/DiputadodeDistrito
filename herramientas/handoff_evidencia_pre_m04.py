#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class PreM04HandoffError(ValueError):
    pass


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise PreM04HandoffError(f"PRE_M04_HANDOFF_MISSING: no existe {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise PreM04HandoffError(f"PRE_M04_HANDOFF_INVALID_JSON: {path}") from exc
    if not isinstance(data, dict):
        raise PreM04HandoffError(f"PRE_M04_HANDOFF_INVALID_JSON: {path}")
    return data


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    if not path.is_file():
        raise PreM04HandoffError(f"PRE_M04_HANDOFF_MISSING: no existe {path}")
    return _sha256_bytes(path.read_bytes())


def _digest(value: object, *, label: str) -> str:
    text = str(value or "").removeprefix("sha256:").lower()
    if not HEX64.fullmatch(text):
        raise PreM04HandoffError(f"PRE_M04_HANDOFF_IDENTITY: digest inválido en {label}")
    return text


def validate_identity(
    payload: dict,
    *,
    territory_id: str,
    edition: str,
    run_id: int,
    source_commit: str,
) -> None:
    if payload.get("schema") != "ddd.catalog-evidence/1.0":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: schema inválido")
    if payload.get("kind") != "generation_preflight":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: kind inválido")
    if str(payload.get("territory_id") or "") != territory_id:
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: territorio no coincide")
    if str(payload.get("edition") or "") != str(edition):
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: edición no coincide")
    if payload.get("run_id") != run_id:
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: run_id no coincide")
    actual_commit = str(payload.get("source_commit") or "").lower()
    if not HEX40.fullmatch(actual_commit) or actual_commit != source_commit.lower():
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: source_commit no coincide")
    if payload.get("decision") != "READY_FOR_FIRST_GENERATION":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: decisión pre-M04 no acreditada")
    if payload.get("stage") != "M03U":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: stage distinto de M03U")

    _digest(payload.get("artifact_sha256"), label="M03U")
    source = payload.get("source") or {}
    graph = payload.get("graph") or {}
    partitioning = payload.get("partitioning") or {}
    _digest(source.get("artifact_sha256"), label="source.artifact")
    _digest(source.get("package_sha256"), label="source.package")
    _digest(graph.get("artifact_sha256"), label="graph")
    _digest(partitioning.get("job_artifact_sha256"), label="partitioning")

    if str(payload.get("artifact_name") or "") != f"ddd-state-{run_id}-M03U":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: artifact_name M03U no coincide")
    if str(graph.get("artifact_name") or "") != f"ddd-state-{run_id}-M03":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: artifact_name M03 no coincide")
    if str(partitioning.get("job_artifact_name") or "") != f"ddd-internal-units-{run_id}":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: artifact_name particionado no coincide")
    gate = payload.get("effective_gate") or {}
    if gate.get("allowed") is not True or gate.get("route") != "validated_pre_m04_topology":
        raise PreM04HandoffError("PRE_M04_HANDOFF_IDENTITY: puerta efectiva pre-M04 no acreditada")


def stage_handoff(
    *,
    persisted_evidence: Path,
    handoff: Path,
    metadata: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    source_commit: str,
) -> dict:
    payload = _load_json(persisted_evidence)
    validate_identity(
        payload,
        territory_id=territory_id,
        edition=edition,
        run_id=run_id,
        source_commit=source_commit,
    )
    original = persisted_evidence.read_bytes()
    digest = _sha256_bytes(original)
    handoff.parent.mkdir(parents=True, exist_ok=True)
    handoff.write_bytes(original)
    if handoff.read_bytes() != original:
        raise PreM04HandoffError("PRE_M04_HANDOFF_COPY_MISMATCH: copia de handoff no idéntica")

    meta = {
        "schema": "ddd.pre-m04-handoff/1.0",
        "territory_id": territory_id,
        "edition": str(edition),
        "run_id": run_id,
        "source_commit": source_commit.lower(),
        "evidence_sha256": digest,
        "persisted_evidence": persisted_evidence.as_posix(),
        "handoff": handoff.as_posix(),
    }
    metadata.parent.mkdir(parents=True, exist_ok=True)
    metadata.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta


def verify_handoff(
    *,
    persisted_evidence: Path,
    handoff: Path,
    metadata: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    source_commit: str,
) -> dict:
    meta = _load_json(metadata)
    if meta.get("schema") != "ddd.pre-m04-handoff/1.0":
        raise PreM04HandoffError("PRE_M04_HANDOFF_META: schema inválido")
    if (
        str(meta.get("territory_id") or "") != territory_id
        or str(meta.get("edition") or "") != str(edition)
        or meta.get("run_id") != run_id
        or str(meta.get("source_commit") or "").lower() != source_commit.lower()
    ):
        raise PreM04HandoffError("PRE_M04_HANDOFF_META: identidad no coincide")

    handoff_payload = _load_json(handoff)
    persisted_payload = _load_json(persisted_evidence)
    for payload in (handoff_payload, persisted_payload):
        validate_identity(
            payload,
            territory_id=territory_id,
            edition=edition,
            run_id=run_id,
            source_commit=source_commit,
        )

    expected = str(meta.get("evidence_sha256") or "").lower()
    if not HEX64.fullmatch(expected):
        raise PreM04HandoffError("PRE_M04_HANDOFF_META: digest ausente o inválido")
    handoff_digest = _sha256_file(handoff)
    persisted_digest = _sha256_file(persisted_evidence)
    if handoff_digest != expected:
        raise PreM04HandoffError("PRE_M04_HANDOFF_DIGEST_MISMATCH: handoff alterado")
    if persisted_digest != expected:
        raise PreM04HandoffError("PRE_M04_HANDOFF_DIGEST_MISMATCH: evidencia persistida alterada")
    if handoff.read_bytes() != persisted_evidence.read_bytes():
        raise PreM04HandoffError("PRE_M04_HANDOFF_BYTES_MISMATCH: handoff y persistencia difieren")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    for name in ("stage", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--persisted-evidence", type=Path, required=True)
        p.add_argument("--handoff", type=Path, required=True)
        p.add_argument("--metadata", type=Path, required=True)
        p.add_argument("--territory-id", required=True)
        p.add_argument("--edition", required=True)
        p.add_argument("--run-id", type=int, required=True)
        p.add_argument("--source-commit", required=True)
    ns = ap.parse_args()
    try:
        fn = stage_handoff if ns.command == "stage" else verify_handoff
        result = fn(
            persisted_evidence=ns.persisted_evidence,
            handoff=ns.handoff,
            metadata=ns.metadata,
            territory_id=ns.territory_id,
            edition=ns.edition,
            run_id=ns.run_id,
            source_commit=ns.source_commit,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except PreM04HandoffError as exc:
        print(f"::error::{exc}")
        return 57


if __name__ == "__main__":
    raise SystemExit(main())
