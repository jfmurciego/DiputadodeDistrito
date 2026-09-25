from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from herramientas.persistir_estado_operativo_compartido import persist_shared_state


class SharedOperationalStateConcurrencyTests(unittest.TestCase):
    def test_two_concurrent_promotions_recalculate_after_push_collision_and_preserve_both_products(self):
        with tempfile.TemporaryDirectory() as td:
            worktree = Path(td) / "asturias"
            worktree.mkdir()

            asturias = "ddd-state-36136837323-M08"
            castilla_la_mancha = "ddd-state-36136811938-M06"
            remote = {
                "version": 1,
                "head": "base",
                "products": {
                    "principado_de_asturias": asturias,
                },
            }
            local = {
                "base_version": 0,
                "head": "base",
                "snapshot": {},
            }
            generated_states: list[dict[str, str]] = []
            failed_pushes = 0
            castilla_registered = False

            def completed(args, rc=0, stdout="", stderr=""):
                return subprocess.CompletedProcess(
                    args=list(args),
                    returncode=rc,
                    stdout=stdout,
                    stderr=stderr,
                )

            def fake_git(root: Path, *args: str, check: bool = True):
                nonlocal failed_pushes
                self.assertEqual(root, worktree)
                command = args[0]
                if command in ("config", "fetch", "add"):
                    return completed(args)
                if command == "reset":
                    local["base_version"] = remote["version"]
                    local["head"] = remote["head"]
                    return completed(args)
                if command == "diff":
                    return completed(args, rc=1)
                if command == "commit":
                    local["head"] = f"asturias-from-v{local['base_version']}"
                    return completed(args)
                if command == "rev-parse":
                    return completed(args, stdout=local["head"] + "\n")
                if command == "push":
                    if local["base_version"] != remote["version"]:
                        failed_pushes += 1
                        return completed(
                            args,
                            rc=1,
                            stderr="remote rejected: stale shared-state snapshot",
                        )
                    remote["version"] += 1
                    remote["head"] = local["head"]
                    return completed(args)
                raise AssertionError(f"comando git no simulado: {args}")

            def fake_regenerate(root: Path, edition: str, *, sync_dashboard_assets: bool):
                self.assertEqual(root, worktree)
                self.assertEqual(edition, "2025")
                local["snapshot"] = dict(remote["products"])
                generated_states.append(dict(local["snapshot"]))

            def before_push(attempt: int):
                nonlocal castilla_registered
                if attempt == 1:
                    self.assertEqual(
                        generated_states,
                        [{"principado_de_asturias": asturias}],
                    )
                    # Mientras Asturias conserva un snapshot derivado de v1,
                    # Castilla-La Mancha registra su producto durable y avanza main.
                    remote["products"]["castilla_la_mancha"] = castilla_la_mancha
                    remote["version"] += 1
                    remote["head"] = "castilla-la-mancha-registration"
                    castilla_registered = True

            with (
                patch(
                    "herramientas.persistir_estado_operativo_compartido._git",
                    side_effect=fake_git,
                ),
                patch(
                    "herramientas.persistir_estado_operativo_compartido._regenerate",
                    side_effect=fake_regenerate,
                ),
                patch(
                    "herramientas.persistir_estado_operativo_compartido.time.sleep",
                    return_value=None,
                ),
            ):
                sha = persist_shared_state(
                    root_dir=worktree,
                    edition="2025",
                    target_branch="main",
                    sync_dashboard_assets=True,
                    max_attempts=4,
                    before_push=before_push,
                )

            self.assertTrue(castilla_registered)
            self.assertEqual(failed_pushes, 1)
            self.assertEqual(
                generated_states,
                [
                    {"principado_de_asturias": asturias},
                    {
                        "principado_de_asturias": asturias,
                        "castilla_la_mancha": castilla_la_mancha,
                    },
                ],
            )
            self.assertEqual(
                local["snapshot"],
                {
                    "principado_de_asturias": asturias,
                    "castilla_la_mancha": castilla_la_mancha,
                },
            )
            self.assertEqual(remote["version"], 3)
            self.assertEqual(sha, "asturias-from-v2")


if __name__ == "__main__":
    unittest.main()
