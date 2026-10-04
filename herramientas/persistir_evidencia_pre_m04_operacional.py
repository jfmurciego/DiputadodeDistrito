#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Callable

import yaml

from herramientas.catalogo_preparacion import CATALOG, MASTER, validate_repository
from herramientas.handoff_evidencia_pre_m04 import (
    PreM04HandoffError,
    validate_identity,
    verify_handoff,
)
from herramientas.materializar_evidencia_pre_m04 import register_evidence_path
from herramientas.persistir_estado_operativo_compartido import (
    PersistenceResult,
    persist_rederived_tree,
)

ABSENT_FINGERPRINT = "ABSENT"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class PreM04PersistenceConflict(RuntimeError):
    def __init__(self, status: str, message: str):
        super().__init__(message)
        self.status = status


def _json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON inválido: {path}")
    return data


def _yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML inválido: {path}")
    return data


def _stable_fingerprint(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _evidence_rel(territory_id: str, edition: str) -> Path:
    return (
        Path("territorios")
        / territory_id
        / "evidencia"
        / "catalogo"
        / f"generation_preflight_{edition}.json"
    )


def _evidence_fingerprint(root: Path, territory_id: str, edition: str) -> str:
    path = root / _evidence_rel(territory_id, edition)
    if not path.is_file():
        return ABSENT_FINGERPRINT
    try:
        return _stable_fingerprint(_json(path))
    except Exception:
        return "INVALID:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _catalog_state(root: Path, territory_id: str, edition: str) -> dict:
    catalog = _yaml(root / CATALOG)
    row = next(
        (
            row
            for row in catalog.get("territories") or []
            if str(row.get("territory_id") or "") == territory_id
        ),
        None,
    )
    if row is None:
        raise PreM04PersistenceConflict(
            "INCOMPATIBLE_CURRENT_STATE",
            f"PRE_M04_TERRITORY_MISSING: {territory_id} no existe en catálogo",
        )
    state = (row.get("editions") or {}).get(str(edition))
    if not isinstance(state, dict):
        raise PreM04PersistenceConflict(
            "INCOMPATIBLE_CURRENT_STATE",
            f"PRE_M04_EDITION_MISSING: {territory_id}/{edition} no existe en catálogo",
        )
    return copy.deepcopy(state)


def _master_row(root: Path, territory_id: str) -> dict:
    master = _yaml(root / MASTER)
    row = next(
        (
            row
            for row in master.get("territories") or []
            if str(row.get("territory_id") or "") == territory_id
        ),
        None,
    )
    if not isinstance(row, dict):
        raise PreM04PersistenceConflict(
            "INCOMPATIBLE_CURRENT_STATE",
            f"PRE_M04_MASTER_MISSING: {territory_id} no existe en catálogo maestro",
        )
    return copy.deepcopy(row)


def _contract(root: Path, contract_path: str) -> dict:
    path = root / contract_path
    if not path.is_file():
        raise PreM04PersistenceConflict(
            "INCOMPATIBLE_CURRENT_STATE",
            f"PRE_M04_CONTRACT_MISSING: no existe {contract_path}",
        )
    return copy.deepcopy(_yaml(path))


def _context_fingerprint(
    root: Path,
    *,
    territory_id: str,
    edition: str,
    contract_path: str,
) -> str:
    return _stable_fingerprint(
        {
            "catalog_state": _catalog_state(root, territory_id, edition),
            "master_row": _master_row(root, territory_id),
            "contract": _contract(root, contract_path),
            "generation_preflight_fingerprint": _evidence_fingerprint(
                root, territory_id, edition
            ),
        }
    )


def _protected_snapshot(
    root: Path,
    *,
    territory_id: str,
    edition: str,
    contract_path: str,
) -> dict:
    state = _catalog_state(root, territory_id, edition)
    state.pop("generation_enabled", None)
    evidence = copy.deepcopy(state.get("evidence") or {})
    evidence.pop("generation_preflight", None)
    if evidence:
        state["evidence"] = evidence
    else:
        state.pop("evidence", None)

    contract = _contract(root, contract_path)
    (contract.get("meta") or {}).pop("status", None)
    (contract.get("territory_contract") or {}).pop("status", None)
    generation = contract.get("generation_state")
    if isinstance(generation, dict):
        for key in (
            "generation_enabled",
            "pre_m04_run_id",
            "pre_m04_source_commit",
            "pre_m04_artifact_sha256",
        ):
            generation.pop(key, None)

    master = _master_row(root, territory_id)
    master.pop("status", None)

    return {
        "catalog_state": state,
        "contract": contract,
        "master_row": master,
    }


def _registration_matches(
    root: Path,
    *,
    territory_id: str,
    edition: str,
    contract_path: str,
    candidate: dict,
    candidate_fingerprint: str,
) -> bool:
    if _evidence_fingerprint(root, territory_id, edition) != candidate_fingerprint:
        return False
    state = _catalog_state(root, territory_id, edition)
    evidence = state.get("evidence") or {}
    if (
        state.get("generation_enabled") is not True
        or evidence.get("generation_preflight")
        != _evidence_rel(territory_id, edition).as_posix()
    ):
        return False

    contract = _contract(root, contract_path)
    generation = contract.get("generation_state") or {}
    if (
        generation.get("generation_enabled") is not True
        or int(generation.get("pre_m04_run_id") or 0) != int(candidate["run_id"])
        or str(generation.get("pre_m04_source_commit") or "").lower()
        != str(candidate["source_commit"]).lower()
        or str(generation.get("pre_m04_artifact_sha256") or "").removeprefix(
            "sha256:"
        )
        != str(candidate["artifact_sha256"]).removeprefix("sha256:")
    ):
        return False

    return str(_master_row(root, territory_id).get("status") or "") == "generation_ready"


def _write_result(
    path: Path | None,
    *,
    status: str,
    territory_id: str,
    edition: str,
    run_id: int,
    source_commit: str,
    candidate_fingerprint: str,
    head_sha: str,
    attempt: int,
    reason: str | None = None,
) -> None:
    if path is None:
        return
    payload = {
        "schema": "ddd.pre-m04-persistence/1.0",
        "status": status,
        "territory_id": territory_id,
        "edition": str(edition),
        "run_id": int(run_id),
        "source_commit": source_commit,
        "candidate_fingerprint": candidate_fingerprint,
        "head_sha": head_sha,
        "attempt": int(attempt),
    }
    if reason:
        payload["reason"] = reason
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def persist_pre_m04_evidence(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    contract_path: str,
    candidate_evidence: Path,
    source_commit: str,
    target_branch: str = "main",
    max_attempts: int = 4,
    result_json: Path | None = None,
    handoff: Path | None = None,
    handoff_metadata: Path | None = None,
    before_push: Callable[[int], None] | None = None,
) -> str:
    """Persist immutable pre-M04 evidence against a moving branch safely.

    Candidate evidence and the expected same-territory baseline are captured
    before the checkout is moved. Every retry then starts from the current
    remote HEAD and reapplies that already-frozen semantic operation using the
    code loaded by this process from the run's original source commit.
    """
    root = root_dir.resolve()
    source_commit = source_commit.lower()
    if not HEX40.fullmatch(source_commit):
        raise ValueError(f"source_commit inválido: {source_commit!r}")

    initial_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout.strip().lower()
    if initial_head != source_commit:
        raise ValueError(
            "PRE_M04_SOURCE_CHECKOUT_MISMATCH: el checkout del escritor "
            f"({initial_head}) no coincide con el source_commit del run "
            f"({source_commit})"
        )

    candidate_path = candidate_evidence
    if not candidate_path.is_absolute():
        candidate_path = root / candidate_path
    candidate_bytes = candidate_path.read_bytes()
    candidate = json.loads(candidate_bytes.decode("utf-8"))
    if not isinstance(candidate, dict):
        raise ValueError("candidate_evidence debe contener un objeto JSON")

    validate_identity(
        candidate,
        territory_id=territory_id,
        edition=str(edition),
        run_id=int(run_id),
        source_commit=source_commit,
    )
    candidate_fingerprint = _stable_fingerprint(candidate)

    if (handoff is None) != (handoff_metadata is None):
        raise ValueError("handoff y handoff_metadata deben suministrarse juntos")
    handoff_path = handoff
    metadata_path = handoff_metadata
    if handoff_path is not None and not handoff_path.is_absolute():
        handoff_path = root / handoff_path
    if metadata_path is not None and not metadata_path.is_absolute():
        metadata_path = root / metadata_path

    expected_previous_fingerprint = _evidence_fingerprint(
        root, territory_id, str(edition)
    )
    expected_context_fingerprint = _context_fingerprint(
        root,
        territory_id=territory_id,
        edition=str(edition),
        contract_path=contract_path,
    )
    expected_protected_snapshot = _protected_snapshot(
        root,
        territory_id=territory_id,
        edition=str(edition),
        contract_path=contract_path,
    )

    canonical_rel = _evidence_rel(territory_id, str(edition))
    last_attempt = 0
    last_head = ""

    def apply(current_root: Path, attempt: int) -> None:
        nonlocal last_attempt, last_head
        last_attempt = attempt
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=current_root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        last_head = completed.stdout.strip()

        current_protected_snapshot = _protected_snapshot(
            current_root,
            territory_id=territory_id,
            edition=str(edition),
            contract_path=contract_path,
        )
        if current_protected_snapshot != expected_protected_snapshot:
            raise PreM04PersistenceConflict(
                "INCOMPATIBLE_CURRENT_STATE",
                "PRE_M04_PROTECTED_CONTEXT_CHANGE: cambió el estado protegido "
                f"del mismo territorio {territory_id}/{edition} desde el "
                "source_commit del run",
            )

        if _registration_matches(
            current_root,
            territory_id=territory_id,
            edition=str(edition),
            contract_path=contract_path,
            candidate=candidate,
            candidate_fingerprint=candidate_fingerprint,
        ):
            return

        current_previous = _evidence_fingerprint(
            current_root, territory_id, str(edition)
        )
        if current_previous != expected_previous_fingerprint:
            raise PreM04PersistenceConflict(
                "CONCURRENT_PRE_M04_CHANGED",
                "PRE_M04_CONCURRENT_EVIDENCE_CHANGE: la evidencia pre-M04 de "
                f"{territory_id}/{edition} cambió desde la base del run "
                f"(esperado={expected_previous_fingerprint}, "
                f"actual={current_previous})",
            )

        current_context = _context_fingerprint(
            current_root,
            territory_id=territory_id,
            edition=str(edition),
            contract_path=contract_path,
        )
        if current_context != expected_context_fingerprint:
            raise PreM04PersistenceConflict(
                "INCOMPATIBLE_CURRENT_STATE",
                "PRE_M04_CONTEXT_CHANGE: cambió el estado durable del mismo "
                f"territorio {territory_id}/{edition} desde la base del run",
            )

        protected_before = current_protected_snapshot
        canonical = current_root / canonical_rel
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_bytes(candidate_bytes)
        try:
            register_evidence_path(
                root_dir=current_root,
                territory_id=territory_id,
                edition=str(edition),
                evidence_path=canonical_rel.as_posix(),
                contract_path=contract_path,
                evidence=candidate,
            )
        except ValueError as exc:
            raise PreM04PersistenceConflict(
                "INCOMPATIBLE_CURRENT_STATE",
                f"PRE_M04_CURRENT_STATE_REJECTED: {exc}",
            ) from exc

        protected_after = _protected_snapshot(
            current_root,
            territory_id=territory_id,
            edition=str(edition),
            contract_path=contract_path,
        )
        if protected_after != protected_before:
            raise PreM04PersistenceConflict(
                "PROTECTED_STATE_CHANGED",
                "PRE_M04_PROTECTED_STATE_CHANGED: la operación intentó alterar "
                "producto certificado, receipts, lineage o estado ajeno a la "
                "habilitación pre-M04",
            )

        errors = validate_repository(root_dir=current_root)
        if errors:
            raise PreM04PersistenceConflict(
                "INCOMPATIBLE_CURRENT_STATE",
                "PRE_M04_REPOSITORY_INVALID: " + "; ".join(errors[:8]),
            )

        if handoff_path is not None and metadata_path is not None:
            try:
                verify_handoff(
                    persisted_evidence=canonical,
                    handoff=handoff_path,
                    metadata=metadata_path,
                    territory_id=territory_id,
                    edition=str(edition),
                    run_id=int(run_id),
                    source_commit=source_commit,
                )
            except PreM04HandoffError as exc:
                raise PreM04PersistenceConflict(
                    "HANDOFF_MISMATCH",
                    f"PRE_M04_HANDOFF_REJECTED: {exc}",
                ) from exc

    paths = (
        CATALOG.as_posix(),
        MASTER.as_posix(),
        contract_path,
        canonical_rel.as_posix(),
    )
    try:
        result: PersistenceResult = persist_rederived_tree(
            root_dir=root,
            target_branch=target_branch,
            paths=paths,
            commit_message=f"chore: registrar evidencia pre-M04 de {territory_id}",
            apply=apply,
            max_attempts=max_attempts,
            before_push=before_push,
            exhausted_message=(
                "No se pudo registrar la evidencia pre-M04 tras "
                f"{max_attempts} derivaciones desde el HEAD vigente"
            ),
        )
    except PreM04PersistenceConflict as exc:
        _write_result(
            result_json,
            status=exc.status,
            territory_id=territory_id,
            edition=str(edition),
            run_id=run_id,
            source_commit=source_commit,
            candidate_fingerprint=candidate_fingerprint,
            head_sha=last_head,
            attempt=last_attempt,
            reason=str(exc),
        )
        raise
    except RuntimeError as exc:
        _write_result(
            result_json,
            status="PUSH_RETRY_EXHAUSTED",
            territory_id=territory_id,
            edition=str(edition),
            run_id=run_id,
            source_commit=source_commit,
            candidate_fingerprint=candidate_fingerprint,
            head_sha=last_head,
            attempt=last_attempt,
            reason=str(exc),
        )
        raise
    except Exception as exc:
        _write_result(
            result_json,
            status="PERSISTENCE_FAILED",
            territory_id=territory_id,
            edition=str(edition),
            run_id=run_id,
            source_commit=source_commit,
            candidate_fingerprint=candidate_fingerprint,
            head_sha=last_head,
            attempt=last_attempt,
            reason=f"{type(exc).__name__}: {exc}",
        )
        raise

    _write_result(
        result_json,
        status="REGISTERED" if result.changed else "NO_OP",
        territory_id=territory_id,
        edition=str(edition),
        run_id=run_id,
        source_commit=source_commit,
        candidate_fingerprint=candidate_fingerprint,
        head_sha=result.head_sha,
        attempt=result.attempt,
    )
    return result.head_sha


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--run-id", type=int, required=True)
    ap.add_argument("--contract-path", required=True)
    ap.add_argument("--candidate-evidence", type=Path, required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--target-branch", default="main")
    ap.add_argument("--max-attempts", type=int, default=4)
    ap.add_argument("--result-json", type=Path)
    ap.add_argument("--handoff", type=Path)
    ap.add_argument("--handoff-metadata", type=Path)
    args = ap.parse_args()

    try:
        sha = persist_pre_m04_evidence(
            root_dir=args.root_dir,
            territory_id=args.territory_id,
            edition=args.edition,
            run_id=args.run_id,
            contract_path=args.contract_path,
            candidate_evidence=args.candidate_evidence,
            source_commit=args.source_commit,
            target_branch=args.target_branch,
            max_attempts=args.max_attempts,
            result_json=args.result_json,
            handoff=args.handoff,
            handoff_metadata=args.handoff_metadata,
        )
    except PreM04PersistenceConflict as exc:
        print(f"::error::{exc}")
        return 59
    except RuntimeError as exc:
        print(f"::error::{exc}")
        return 54

    print(sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
