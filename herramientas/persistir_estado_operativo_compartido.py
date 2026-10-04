#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from herramientas.generar_estado_operativo import build, update_readme, write_state

SHARED_PATHS = (
    "README.md",
    "orchestracion/estado_operativo.json",
    "publicado/dashboard/status.json",
)


@dataclass(frozen=True)
class PersistenceResult:
    head_sha: str
    attempt: int
    changed: bool


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def persist_rederived_tree(
    *,
    root_dir: Path,
    target_branch: str,
    paths: Iterable[str],
    commit_message: str,
    apply: Callable[[Path, int], None],
    validate: Callable[[Path], None] | None = None,
    max_attempts: int = 4,
    before_push: Callable[[int], None] | None = None,
    exhausted_message: str | None = None,
) -> PersistenceResult:
    """Persist a semantic operation by re-deriving it from current remote HEAD.

    The operation callback is executed again after every rejected push. No local
    commit is rebased or conflict-resolved textually: each retry discards the
    stale tree, reloads the remote target branch and reapplies the operation.
    """
    root = root_dir.resolve()
    tracked_paths = tuple(dict.fromkeys(str(path) for path in paths))
    if not tracked_paths:
        raise ValueError("paths no puede estar vacío")
    if max_attempts < 1:
        raise ValueError("max_attempts debe ser >= 1")

    _git(root, "config", "user.name", "github-actions")
    _git(root, "config", "user.email", "github-actions@github.com")

    for attempt in range(1, max_attempts + 1):
        _git(root, "fetch", "origin", target_branch)
        _git(root, "reset", "--hard", f"origin/{target_branch}")

        apply(root, attempt)
        if validate is not None:
            validate(root)

        _git(root, "add", *tracked_paths)
        if _git(root, "diff", "--cached", "--quiet", check=False).returncode == 0:
            validated_head = _git(root, "rev-parse", "HEAD").stdout.strip()
            if before_push is not None:
                before_push(attempt)
            remote = _git(
                root,
                "ls-remote",
                "--exit-code",
                "origin",
                f"refs/heads/{target_branch}",
                check=False,
            )
            remote_head = (
                remote.stdout.split()[0]
                if remote.returncode == 0 and remote.stdout.strip()
                else ""
            )
            if remote_head == validated_head:
                return PersistenceResult(
                    head_sha=validated_head,
                    attempt=attempt,
                    changed=False,
                )
            if attempt == max_attempts:
                prefix = exhausted_message or (
                    "No se pudo persistir la operación semántica tras "
                    f"{max_attempts} derivaciones desde el HEAD vigente"
                )
                raise RuntimeError(
                    f"{prefix}: el remoto avanzó durante la validación NO_OP "
                    f"(validado={validated_head}, remoto={remote_head or 'desconocido'})"
                )
            time.sleep(min(attempt * 0.2, 1.0))
            continue

        _git(root, "commit", "-m", commit_message)
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
            return PersistenceResult(
                head_sha=_git(root, "rev-parse", "HEAD").stdout.strip(),
                attempt=attempt,
                changed=True,
            )

        if attempt == max_attempts:
            prefix = exhausted_message or (
                "No se pudo persistir la operación semántica tras "
                f"{max_attempts} derivaciones desde el HEAD vigente"
            )
            raise RuntimeError(f"{prefix}: {pushed.stderr.strip()}")
        time.sleep(min(attempt * 0.2, 1.0))

    raise AssertionError("bucle de persistencia inalcanzable")


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
    paths = list(SHARED_PATHS)
    if sync_dashboard_assets:
        paths.append("publicado/dashboard")

    result = persist_rederived_tree(
        root_dir=root_dir,
        target_branch=target_branch,
        paths=paths,
        commit_message="chore: sincronizar estado operativo compartido",
        apply=lambda root, _attempt: _regenerate(
            root,
            edition,
            sync_dashboard_assets=sync_dashboard_assets,
        ),
        max_attempts=max_attempts,
        before_push=before_push,
        exhausted_message=(
            "No se pudo persistir el estado operativo compartido tras "
            f"{max_attempts} regeneraciones desde el HEAD vigente"
        ),
    )
    return result.head_sha


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
