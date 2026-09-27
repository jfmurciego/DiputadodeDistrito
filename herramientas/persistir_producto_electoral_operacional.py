#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import time
from pathlib import Path
from typing import Callable

from herramientas.catalogo_preparacion import CATALOG, validate_repository
from herramientas.promover_catalogo_operacional import promote


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
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
) -> str:
    """
    Persist one electoral-product registration without rebasing a stale catalog commit.

    This module is loaded from the source-pinned checkout.  On every attempt the
    mutable repository tree is reset to the current remote target-branch HEAD;
    promotion and validation are then re-derived with the already loaded source
    code.  A rejected push discards that derived commit and starts again from the
    newly fetched operational HEAD.
    """
    root = root_dir.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError(f"source_commit inválido: {source_commit!r}")
    if max_attempts < 1:
        raise ValueError("max_attempts debe ser >= 1")

    receipt = (
        Path("territorios")
        / territory_id
        / "evidencia"
        / "catalogo"
        / f"electoral_product_{edition}.json"
    )
    _git(root, "config", "user.name", "github-actions")
    _git(root, "config", "user.email", "github-actions@github.com")

    for attempt in range(1, max_attempts + 1):
        _git(root, "fetch", "origin", target_branch)
        _git(root, "reset", "--hard", f"origin/{target_branch}")

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

        _git(root, "add", CATALOG.as_posix(), receipt.as_posix())
        if _git(root, "diff", "--cached", "--quiet", check=False).returncode == 0:
            return _git(root, "rev-parse", "HEAD").stdout.strip()

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
            return _git(root, "rev-parse", "HEAD").stdout.strip()

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
    )
    print(sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
