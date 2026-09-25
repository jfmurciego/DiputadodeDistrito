from __future__ import annotations

import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from herramientas.persistir_estado_operativo_compartido import persist_shared_state


class SharedOperationalStateConcurrencyTests(unittest.TestCase):
    def test_two_concurrent_promotions_recalculate_after_push_collision_and_preserve_both_products(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            clone_a = root / "asturias"
            clone_b = root / "castilla_la_mancha"
            clone_a.mkdir()
            clone_b.mkdir()

            remote = {
                "version": 1,
                "head": "base",
                "products": {
                    "principado_de_asturias": "ddd-state-36136837323-M08",
                    "castilla_la_mancha": "ddd-state-36136811938-M06",
                },
            }
            local = {
                clone_a: {"base_version": 0, "head": "base", "snapshot": {}},
                clone_b: {"base_version": 0, "head": "base", "snapshot": {}},
            }
            state_lock = threading.Lock()
            first_push_barrier = threading.Barrier(2)
            failed_pushes = 0

            def completed(args, rc=0, stdout="", stderr=""):
                return subprocess.CompletedProcess(args=list(args), returncode=rc, stdout=stdout, stderr=stderr)

            def fake_git(worktree: Path, *args: str, check: bool = True):
                nonlocal failed_pushes
                with state_lock:
                    command = args[0]
                    if command == "config":
                        return completed(args)
                    if command == "fetch":
                        return completed(args)
                    if command == "reset":
                        local[worktree]["base_version"] = remote["version"]
                        local[worktree]["head"] = remote["head"]
                        return completed(args)
                    if command == "add":
                        return completed(args)
                    if command == "diff":
                        return completed(args, rc=1)
                    if command == "commit":
                        local[worktree]["head"] = (
                            f"{worktree.name}-from-v{local[worktree]['base_version']}"
                        )
                        return completed(args)
                    if command == "rev-parse":
                        return completed(args, stdout=local[worktree]["head"] + "\n")
                    if command == "push":
                        if local[worktree]["base_version"] != remote["version"]:
                            failed_pushes += 1
                            result = completed(
                                args,
                                rc=1,
                                stderr="remote rejected: stale shared-state snapshot",
                            )
                            if check:
                                raise subprocess.CalledProcessError(
                                    result.returncode, result.args, result.stdout, result.stderr
                                )
                            return result
                        remote["version"] += 1
                        remote["head"] = local[worktree]["head"]
                        return completed(args)
                raise AssertionError(f"comando git no simulado: {args}")

            def fake_regenerate(worktree: Path, edition: str, *, sync_dashboard_assets: bool):
                self.assertEqual(edition, "2025")
                with state_lock:
                    # La derivación siempre parte de las identidades durables del HEAD remoto
                    # que el intento acaba de adoptar mediante fetch/reset.
                    local[worktree]["snapshot"] = dict(remote["products"])

            def before_push(attempt: int):
                if attempt == 1:
                    first_push_barrier.wait(timeout=10)

            results: list[str] = []
            errors: list[BaseException] = []
            result_lock = threading.Lock()

            def worker(worktree: Path):
                try:
                    sha = persist_shared_state(
                        root_dir=worktree,
                        edition="2025",
                        target_branch="main",
                        sync_dashboard_assets=True,
                        max_attempts=4,
                        before_push=before_push,
                    )
                    with result_lock:
                        results.append(sha)
                except BaseException as exc:
                    with result_lock:
                        errors.append(exc)

            with (
                patch("herramientas.persistir_estado_operativo_compartido._git", side_effect=fake_git),
                patch("herramientas.persistir_estado_operativo_compartido._regenerate", side_effect=fake_regenerate),
                patch("herramientas.persistir_estado_operativo_compartido.time.sleep", return_value=None),
            ):
                t1 = threading.Thread(target=worker, args=(clone_a,))
                t2 = threading.Thread(target=worker, args=(clone_b,))
                t1.start()
                t2.start()
                t1.join(timeout=10)
                t2.join(timeout=10)

            self.assertFalse(t1.is_alive() or t2.is_alive())
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)
            self.assertEqual(failed_pushes, 1)
            self.assertEqual(remote["version"], 3)
            for worktree in (clone_a, clone_b):
                self.assertEqual(
                    local[worktree]["snapshot"],
                    {
                        "principado_de_asturias": "ddd-state-36136837323-M08",
                        "castilla_la_mancha": "ddd-state-36136811938-M06",
                    },
                )


if __name__ == "__main__":
    unittest.main()
