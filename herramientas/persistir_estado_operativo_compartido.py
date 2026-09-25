#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable

from herramientas.generar_estado_operativo import build, update_readme, write_state

SHARED_PATHS = (
    "README.md",
    "orchestracion/estado_operativo.json",
    "publicado/dashboard/status.json",
)


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def _regenerate(root: Path, edition: str, *, sync_dashboard_assets: bool) -> None:
    state = build(root, edition)
    write_state(
        state,
        root / "orchestracion/estado_operativo.json",
        root / "publicado/dashboard/status.json",
    )
    update_readme(root / "README.md", state)
    if sync_dashboard_assets:
        target = root / "publicado/dashboard"
        target.mkdir(parents=True, exist_ok=True)
        for name in ("index.html", "app.js", "styles.css"):
            shutil.copy2(root / "dashboard" / name, target / name)


def persist_shared_state(
    *,
    root_dir: Path,
    edition: str,
    target_branch: str = "main",
    sync_dashboard_assets: bool = False,
    max_attempts: int = 4,
    before_push: Callable[[int], None] | None = None,
) -> str:
    """
    Persist the repository-wide derived state without rebasing generated files.

    Each retry starts from the current remote HEAD and regenerates README/status
    from durable catalog/receipt identities. A rejected push therefore causes a
    fresh derivation, not a merge of stale snapshots.
    """
    root = root_dir.resolve()
    _git(root, "config", "user.name", "github-actions")
    _git(root, "config", "user.email", "github-actions@github.com")

    paths = list(SHARED_PATHS)
    if sync_dashboard_assets:
        paths.append("publicado/dashboard")

    for attempt in range(1, max_attempts + 1):
        _git(root, "fetch", "origin", target_branch)
        _git(root, "reset", "--hard", f"origin/{target_branch}")
        _regenerate(root, edition, sync_dashboard_assets=sync_dashboard_assets)

        _git(root, "add", *paths)
        if _git(root, "diff", "--cached", "--quiet", check=False).returncode == 0:
            return _git(root, "rev-parse", "HEAD").stdout.strip()

        _git(root, "commit", "-m", "chore: sincronizar estado operativo compartido")
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
                "No se pudo persistir el estado operativo compartido tras "
                f"{max_attempts} regeneraciones desde el HEAD vigente: "
                + pushed.stderr.strip()
            )
        time.sleep(min(attempt * 0.2, 1.0))

    raise AssertionError("bucle de persistencia inalcanzable")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--edition", default="2025")
    ap.add_argument("--target-branch", default="main")
    ap.add_argument("--sync-dashboard-assets", action="store_true")
    ap.add_argument("--max-attempts", type=int, default=4)
    args = ap.parse_args()
    sha = persist_shared_state(
        root_dir=args.root_dir,
        edition=args.edition,
        target_branch=args.target_branch,
        sync_dashboard_assets=args.sync_dashboard_assets,
        max_attempts=args.max_attempts,
    )
    print(sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
