from __future__ import annotations

import json
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

import yaml

from herramientas.persistir_estado_operativo_compartido import persist_shared_state
from herramientas.generar_estado_operativo import START, END


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def write_repo(root: Path) -> None:
    (root / "configuracion").mkdir(parents=True, exist_ok=True)
    (root / "dashboard").mkdir(parents=True, exist_ok=True)
    (root / "orchestracion").mkdir(parents=True, exist_ok=True)
    (root / "publicado/dashboard").mkdir(parents=True, exist_ok=True)

    digest_a = "a" * 64
    digest_b = "b" * 64
    catalog = {
        "schema": "ddd-preparation-catalog/1.1",
        "default_edition": "2025",
        "territories": [],
    }
    for tid, name, run_id, digest in (
        ("producto_a", "Producto A", 101, digest_a),
        ("producto_b", "Producto B", 202, digest_b),
    ):
        receipt = root / f"territorios/{tid}/evidencia/catalogo/territorial_product_2025.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps(
                {
                    "territory_id": tid,
                    "edition": "2025",
                    "run_id": run_id,
                    "artifact_name": f"ddd-state-{run_id}-M06",
                    "artifact_sha256": digest,
                    "decision": "PASS",
                }
            ),
            encoding="utf-8",
        )
        catalog["territories"].append(
            {
                "territory_id": tid,
                "name": name,
                "editions": {
                    "2025": {
                        "contract_path": f"territorios/{tid}/config/{tid}_2025.yaml",
                        "territorial_sources_prepared": True,
                        "territorial_product_available": True,
                        "electoral_source_prepared": False,
                        "electoral_product_available": False,
                        "territorial_certification": "PASS",
                        "production_authorization": "AUTHORIZED",
                        "preparation_evidence": {
                            "run_id": run_id - 1,
                            "artifact_name": f"ddd-source-package-{tid}-2025-{run_id - 1}",
                            "artifact_sha256": digest,
                        },
                        "evidence": {
                            "territorial_product": f"territorios/{tid}/evidencia/catalogo/territorial_product_2025.json"
                        },
                    }
                },
            }
        )

    (root / "configuracion/catalogo_preparacion.yaml").write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        f"# Demo\n\n{START}\nestado anterior\n{END}\n",
        encoding="utf-8",
    )
    for name in ("index.html", "app.js", "styles.css"):
        (root / "dashboard" / name).write_text(f"{name}\n", encoding="utf-8")


class SharedOperationalStateConcurrencyTests(unittest.TestCase):
    def test_two_concurrent_promotions_recalculate_after_push_collision_and_preserve_both_products(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            remote = td / "remote.git"
            seed = td / "seed"
            clone_a = td / "a"
            clone_b = td / "b"
            final = td / "final"

            run("git", "init", "--bare", str(remote), cwd=td)
            run("git", "clone", str(remote), str(seed), cwd=td)
            run("git", "checkout", "-b", "main", cwd=seed)
            run("git", "config", "user.name", "test", cwd=seed)
            run("git", "config", "user.email", "test@example.invalid", cwd=seed)
            write_repo(seed)
            run("git", "add", ".", cwd=seed)
            run("git", "commit", "-m", "seed durable products", cwd=seed)
            run("git", "push", "-u", "origin", "main", cwd=seed)
            run("git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main", cwd=td)

            run("git", "clone", str(remote), str(clone_a), cwd=td)
            run("git", "clone", str(remote), str(clone_b), cwd=td)

            barrier = threading.Barrier(2)
            results: list[str] = []
            errors: list[BaseException] = []
            lock = threading.Lock()

            def worker(root: Path) -> None:
                try:
                    sha = persist_shared_state(
                        root_dir=root,
                        edition="2025",
                        target_branch="main",
                        sync_dashboard_assets=True,
                        max_attempts=4,
                        before_push=lambda attempt: barrier.wait(timeout=10) if attempt == 1 else None,
                    )
                    with lock:
                        results.append(sha)
                except BaseException as exc:
                    with lock:
                        errors.append(exc)

            t1 = threading.Thread(target=worker, args=(clone_a,))
            t2 = threading.Thread(target=worker, args=(clone_b,))
            t1.start()
            t2.start()
            t1.join(timeout=30)
            t2.join(timeout=30)

            self.assertFalse(t1.is_alive() or t2.is_alive(), "las promociones concurrentes no terminaron")
            self.assertEqual(errors, [])
            self.assertEqual(len(results), 2)

            run("git", "clone", str(remote), str(final), cwd=td)
            state = json.loads(
                (final / "orchestracion/estado_operativo.json").read_text(encoding="utf-8")
            )
            by_id = {row["territory_id"]: row for row in state["territories"]}
            self.assertEqual(
                by_id["producto_a"]["phase_evidence"]["territorial_product"]["artifact_name"],
                "ddd-state-101-M06",
            )
            self.assertEqual(
                by_id["producto_b"]["phase_evidence"]["territorial_product"]["artifact_name"],
                "ddd-state-202-M06",
            )
            self.assertEqual(by_id["producto_a"]["g"], "green")
            self.assertEqual(by_id["producto_b"]["g"], "green")

            log = run(
                "git",
                "log",
                "--format=%s",
                "--all",
                cwd=final,
            ).stdout
            self.assertGreaterEqual(
                log.count("chore: sincronizar estado operativo compartido"),
                2,
            )


if __name__ == "__main__":
    unittest.main()
