#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Callable

import yaml

from herramientas.catalogo_preparacion import CATALOG, validate_repository
from herramientas.promover_catalogo_operacional import promote


ABSENT_FINGERPRINT = "ABSENT"


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _normalise_digest(value: object) -> str:
    return str(value or "").strip().removeprefix("sha256:").lower()


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _normalise_identity(payload: dict | None) -> dict | None:
    if payload is None:
        return None
    return {
        "territory_id": str(payload.get("territory_id") or ""),
        "edition": str(payload.get("edition") or ""),
        "run_id": int(payload.get("run_id")) if str(payload.get("run_id") or "").isdigit() else None,
        "artifact_name": str(payload.get("artifact_name") or ""),
        "artifact_sha256": _normalise_digest(payload.get("artifact_sha256")),
        "source_commit": str(payload.get("source_commit") or "").lower(),
        "stage": str(payload.get("stage") or ""),
    }


def electoral_product_fingerprint(identity: dict | None) -> str:
    normalised = _normalise_identity(identity)
    if normalised is None:
        return ABSENT_FINGERPRINT
    raw = json.dumps(normalised, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _receipt_path(territory_id: str, edition: str) -> Path:
    return (
        Path("territorios")
        / territory_id
        / "evidencia"
        / "catalogo"
        / f"electoral_product_{edition}.json"
    )


def current_electoral_product_identity(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
) -> dict | None:
    root = root_dir.resolve()
    return _normalise_identity(_read_json(root / _receipt_path(territory_id, edition)))


def current_electoral_product_fingerprint(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
) -> str:
    return electoral_product_fingerprint(
        current_electoral_product_identity(
            root_dir=root_dir,
            territory_id=territory_id,
            edition=edition,
        )
    )


def _catalog_state(root: Path, territory_id: str, edition: str) -> dict:
    path = root / CATALOG
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    for row in data.get("territories") or []:
        if str(row.get("territory_id") or "") == territory_id:
            state = (row.get("editions") or {}).get(str(edition))
            return state if isinstance(state, dict) else {}
    return {}


def recovery_context_fingerprint(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
) -> str:
    root = root_dir.resolve()
    base = root / "territorios" / territory_id / "evidencia" / "catalogo"
    payload = {
        "territorial_product": _read_json(base / f"territorial_product_{edition}.json"),
        "electoral_source": _read_json(base / f"electoral_source_{edition}.json"),
        "electoral_product": _read_json(base / f"electoral_product_{edition}.json"),
        "catalog_state": _catalog_state(root, territory_id, edition),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def electoral_product_registration_accreditation(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    artifact_name: str,
    artifact_sha256: str,
    source_commit: str,
) -> dict:
    root = root_dir.resolve()
    receipt = root / _receipt_path(territory_id, edition)
    candidate = _candidate_identity(
        territory_id=territory_id,
        edition=edition,
        run_id=run_id,
        artifact_name=artifact_name,
        artifact_sha256=artifact_sha256,
        source_commit=source_commit,
    )
    current = current_electoral_product_identity(
        root_dir=root,
        territory_id=territory_id,
        edition=edition,
    )
    receipt_accredited = (
        electoral_product_fingerprint(current)
        == electoral_product_fingerprint(candidate)
    )
    catalog_accredited = _catalog_registration_matches(
        root=root,
        territory_id=territory_id,
        edition=edition,
        run_id=run_id,
        receipt=receipt,
    )
    return {
        "receipt_accredited": receipt_accredited,
        "catalog_accredited": catalog_accredited,
        "accredited": receipt_accredited and catalog_accredited,
    }


def _candidate_identity(
    *,
    territory_id: str,
    edition: str,
    run_id: int,
    artifact_name: str,
    artifact_sha256: str,
    source_commit: str,
) -> dict:
    return _normalise_identity(
        {
            "territory_id": territory_id,
            "edition": edition,
            "run_id": run_id,
            "artifact_name": artifact_name,
            "artifact_sha256": artifact_sha256,
            "source_commit": source_commit,
            "stage": "M08",
        }
    ) or {}


def _catalog_registration_matches(
    *,
    root: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    receipt: Path,
) -> bool:
    catalog_path = root / CATALOG
    if not catalog_path.is_file():
        return False
    try:
        data = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False
    state = None
    for row in data.get("territories") or []:
        if str(row.get("territory_id") or "") == territory_id:
            state = (row.get("editions") or {}).get(str(edition))
            break
    if not isinstance(state, dict):
        return False
    evidence = state.get("evidence") or {}
    checkpoint = state.get("last_valid_checkpoint") or {}
    try:
        expected_receipt = str(receipt.relative_to(root))
    except ValueError:
        return False
    return (
        state.get("electoral_product_available") is True
        and evidence.get("electoral_product") == expected_receipt
        and checkpoint.get("stage") == "M08"
        and int(checkpoint.get("run_id")) == int(run_id)
    )


def _write_result(path: Path | None, *, status: str, head_sha: str, attempt: int) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "ddd.electoral-product-persistence/1.0",
                "status": status,
                "head_sha": head_sha,
                "attempt": attempt,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def persist_electoral_product(
    *,
    root_dir: Path,
    territory_id: str,
    edition: str,
    run_id: int,
    artifact_name: str,
    artifact_sha256: str,
    source_commit: str,
    target_branch: str = "main",
    max_attempts: int = 4,
    before_push: Callable[[int], None] | None = None,
    expected_previous_fingerprint: str | None = None,
    expected_context_fingerprint: str | None = None,
    result_json: Path | None = None,
) -> str:
    """
    Persist one electoral-product registration without rebasing a stale catalog commit.

    The module is loaded before the mutable checkout is reset. On every attempt the
    repository tree is reset to the current remote target-branch HEAD, then promotion
    and validation are re-derived. A rejected push discards that derived commit.

    When expected_previous_fingerprint is supplied, it acts as a semantic CAS guard:
    unrelated changes to main are tolerated, but a different electoral product for
    the same territory aborts the recovery. An already registered identical candidate
    is an idempotent NO_OP.
    """
    root = root_dir.resolve()
    source_commit = source_commit.lower()
    artifact_sha256 = _normalise_digest(artifact_sha256)
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError(f"source_commit inválido: {source_commit!r}")
    if not re.fullmatch(r"[0-9a-f]{64}", artifact_sha256):
        raise ValueError(f"artifact_sha256 inválido: {artifact_sha256!r}")
    if expected_previous_fingerprint is not None:
        expected_previous_fingerprint = expected_previous_fingerprint.strip()
        if (
            expected_previous_fingerprint != ABSENT_FINGERPRINT
            and not re.fullmatch(r"[0-9a-f]{64}", expected_previous_fingerprint)
        ):
            raise ValueError(
                "expected_previous_fingerprint debe ser ABSENT o sha256 hexadecimal"
            )
    if expected_context_fingerprint is not None:
        expected_context_fingerprint = expected_context_fingerprint.strip()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_context_fingerprint):
            raise ValueError("expected_context_fingerprint debe ser sha256 hexadecimal")
    if max_attempts < 1:
        raise ValueError("max_attempts debe ser >= 1")

    receipt_rel = _receipt_path(territory_id, edition)
    receipt = root / receipt_rel
    candidate = _candidate_identity(
        territory_id=territory_id,
        edition=edition,
        run_id=run_id,
        artifact_name=artifact_name,
        artifact_sha256=artifact_sha256,
        source_commit=source_commit,
    )
    candidate_fingerprint = electoral_product_fingerprint(candidate)

    _git(root, "config", "user.name", "github-actions")
    _git(root, "config", "user.email", "github-actions@github.com")

    for attempt in range(1, max_attempts + 1):
        _git(root, "fetch", "origin", target_branch)
        _git(root, "reset", "--hard", f"origin/{target_branch}")
        current_head = _git(root, "rev-parse", "HEAD").stdout.strip()

        current_identity = current_electoral_product_identity(
            root_dir=root,
            territory_id=territory_id,
            edition=edition,
        )
        current_fingerprint = electoral_product_fingerprint(current_identity)

        if (
            current_fingerprint == candidate_fingerprint
            and _catalog_registration_matches(
                root=root,
                territory_id=territory_id,
                edition=edition,
                run_id=run_id,
                receipt=receipt,
            )
        ):
            validate_repository(root_dir=root)
            _write_result(
                result_json,
                status="NO_OP",
                head_sha=current_head,
                attempt=attempt,
            )
            return current_head

        if (
            expected_previous_fingerprint is not None
            and current_fingerprint != expected_previous_fingerprint
        ):
            _write_result(
                result_json,
                status="CONCURRENT_PRODUCT_CHANGED",
                head_sha=current_head,
                attempt=attempt,
            )
            raise RuntimeError(
                "ELECTORAL_PRODUCT_CONCURRENT_CHANGE: el producto electoral previo "
                f"de {territory_id}/{edition} cambió durante la recuperación "
                f"(esperado={expected_previous_fingerprint}, actual={current_fingerprint})"
            )

        if expected_context_fingerprint is not None:
            current_context = recovery_context_fingerprint(
                root_dir=root,
                territory_id=territory_id,
                edition=edition,
            )
            if current_context != expected_context_fingerprint:
                _write_result(
                    result_json,
                    status="RECOVERY_CONTEXT_CHANGED",
                    head_sha=current_head,
                    attempt=attempt,
                )
                raise RuntimeError(
                    "ELECTORAL_RECOVERY_CONTEXT_CHANGE: cambió el contexto durable "
                    f"de {territory_id}/{edition} durante la recuperación "
                    f"(esperado={expected_context_fingerprint}, actual={current_context})"
                )

        promote(
            root_dir=root,
            kind="electoral_product",
            territory_id=territory_id,
            edition=edition,
            run_id=run_id,
            artifact_name=artifact_name,
            artifact_sha256=artifact_sha256,
            source_commit=source_commit,
        )
        validate_repository(root_dir=root)

        _git(root, "add", CATALOG.as_posix(), receipt_rel.as_posix())
        if _git(root, "diff", "--cached", "--quiet", check=False).returncode == 0:
            current_head = _git(root, "rev-parse", "HEAD").stdout.strip()
            _write_result(
                result_json,
                status="NO_OP",
                head_sha=current_head,
                attempt=attempt,
            )
            return current_head

        _git(root, "commit", "-m", f"chore: registrar producto electoral de {territory_id}")
        if before_push is not None:
            before_push(attempt)

        pushed = _git(
            root,
            "push",
            "origin",
            f"HEAD:{target_branch}",
            check=False,
        )
        if pushed.returncode == 0:
            current_head = _git(root, "rev-parse", "HEAD").stdout.strip()
            _write_result(
                result_json,
                status="REGISTERED",
                head_sha=current_head,
                attempt=attempt,
            )
            return current_head

        if attempt == max_attempts:
            raise RuntimeError(
                "No se pudo registrar el producto electoral tras "
                f"{max_attempts} derivaciones desde el HEAD vigente: "
                + pushed.stderr.strip()
            )
        time.sleep(min(attempt * 0.2, 1.0))

    raise AssertionError("bucle de persistencia inalcanzable")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--run-id", required=True, type=int)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--artifact-sha256", required=True)
    ap.add_argument("--source-commit", required=True)
    ap.add_argument("--target-branch", default="main")
    ap.add_argument("--max-attempts", type=int, default=4)
    ap.add_argument("--expected-previous-fingerprint")
    ap.add_argument("--expected-context-fingerprint")
    ap.add_argument("--result-json", type=Path)
    args = ap.parse_args()
    sha = persist_electoral_product(
        root_dir=args.root_dir,
        territory_id=args.territory_id,
        edition=args.edition,
        run_id=args.run_id,
        artifact_name=args.artifact_name,
        artifact_sha256=args.artifact_sha256,
        source_commit=args.source_commit,
        target_branch=args.target_branch,
        max_attempts=args.max_attempts,
        expected_previous_fingerprint=args.expected_previous_fingerprint,
        expected_context_fingerprint=args.expected_context_fingerprint,
        result_json=args.result_json,
    )
    print(sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
