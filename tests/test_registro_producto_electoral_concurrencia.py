from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

import yaml

from herramientas.persistir_producto_electoral_operacional import persist_electoral_product


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "_reutilizable-incorporacion-electoral.yml"
SOURCE_COMMIT = "36efca2ee7a025dee93f179d3b9caa2799eada4b"


def git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return completed.stdout.strip()


def territory_state(tid: str, name: str) -> dict:
    return {
        "territory_id": tid,
        "name": name,
        "editions": {
            "2025": {
                "territory_declared": True,
                "preparation_status": "READY",
                "contract_path": f"territorios/{tid}/config/{tid}_2025.yaml",
                "territorial_source_declaration": f"territorios/{tid}/config/fuentes.yaml",
                "electoral_source_declaration": f"territorios/{tid}/config/elecciones/vigente.yaml",
                "territorial_sources_prepared": True,
                "territorial_contract_complete": True,
                "territorial_product_available": True,
                "electoral_source_prepared": True,
                "electoral_product_available": False,
                "territorial_certification": "PASS",
                "production_authorization": "AUTHORIZED",
                "last_valid_checkpoint": {"run_id": 10, "stage": "M06"},
                "evidence": {
                    "territorial_product": f"territorios/{tid}/evidencia/catalogo/territorial_product_2025.json",
                    "electoral_source": f"territorios/{tid}/evidencia/catalogo/electoral_source_2025.json",
                },
            }
        },
    }


def write_fixture(root: Path) -> None:
    territories = [("alpha", "Alpha"), ("beta", "Beta")]
    (root / "configuracion").mkdir(parents=True)
    master = {
        "territories": [
            {"territory_id": tid, "name": name}
            for tid, name in territories
        ]
    }
    (root / "configuracion/catalogo_territorios_espana_2025.yaml").write_text(
        yaml.safe_dump(master, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    catalog = {
        "schema": "ddd-preparation-catalog/1.1",
        "default_edition": "2025",
        "territories": [territory_state(tid, name) for tid, name in territories],
    }
    (root / "configuracion/catalogo_preparacion.yaml").write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    for tid, name in territories:
        config = root / f"territorios/{tid}/config"
        evidence = root / f"territorios/{tid}/evidencia/catalogo"
        (config / "elecciones").mkdir(parents=True)
        evidence.mkdir(parents=True)
        (config / f"{tid}_2025.yaml").write_text(
            yaml.safe_dump(
                {
                    "meta": {
                        "territory_id": tid,
                        "year": 2025,
                        "contract_level": "production_m01_m06",
                        "production_authorization": "AUTHORIZED",
                    }
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (config / "fuentes.yaml").write_text(
            yaml.safe_dump(
                {"territory": {"id": tid, "edition": "2025"}},
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        (config / "elecciones/vigente.yaml").write_text(
            yaml.safe_dump({"territory_id": tid, "election_id": f"{tid}_2025"}),
            encoding="utf-8",
        )
        (evidence / "territorial_product_2025.json").write_text(
            json.dumps({"durable": True}) + "\n",
            encoding="utf-8",
        )
        (evidence / "electoral_source_2025.json").write_text(
            json.dumps(
                {
                    "schema": "ddd.catalog-evidence/1.0",
                    "kind": "electoral_source",
                    "territory_id": tid,
                    "territory_name": name,
                    "edition": "2025",
                    "run_id": 20,
                    "artifact_name": f"ddd-electoral-package-{tid}-2025-20",
                    "artifact_sha256": "1" * 64,
                    "election_id": f"{tid}_2025",
                    "declaration": f"territorios/{tid}/config/elecciones/vigente.yaml",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


def make_remote(base: Path) -> Path:
    seed = base / "seed"
    remote = base / "remote.git"
    seed.mkdir()
    write_fixture(seed)
    git(seed, "init", "-b", "main")
    git(seed, "config", "user.name", "test")
    git(seed, "config", "user.email", "test@example.invalid")
    git(seed, "add", ".")
    git(seed, "commit", "-m", "base")
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, stdout=subprocess.PIPE)
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    subprocess.run(
        ["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True,
    )
    return remote


def clone(remote: Path, destination: Path) -> None:
    subprocess.run(
        ["git", "clone", "--branch", "main", str(remote), str(destination)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ElectoralProductConcurrentRegistrationTests(unittest.TestCase):
    def test_workflow_keeps_source_checkout_but_rederives_mutation_from_main(self):
        data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        register = data["jobs"]["registrar"]
        checkout = register["steps"][0]
        self.assertEqual(
            checkout["with"]["ref"],
            "${{ inputs.source_ref || github.ref_name }}",
        )
        run = next(
            step["run"]
            for step in register["steps"]
            if step.get("name") == "Registrar disponibilidad del producto electoral"
        )
        self.assertIn('source_commit="$(git rev-parse HEAD)"', run)
        self.assertIn(
            "python -m herramientas.persistir_producto_electoral_operacional",
            run,
        )
        self.assertIn("--target-branch main", run)
        self.assertNotIn("git pull --rebase", run)

    def run_two(
        self,
        remote: Path,
        first: tuple[str, int, str],
        second: tuple[str, int, str],
    ) -> tuple[dict[str, str], Path]:
        writer_a = remote.parent / "writer-a"
        writer_b = remote.parent / "writer-b"
        verify = remote.parent / "verify"
        clone(remote, writer_a)
        clone(remote, writer_b)
        barrier = threading.Barrier(2)
        results: dict[str, str] = {}
        errors: list[BaseException] = []

        def worker(label: str, root: Path, spec: tuple[str, int, str]) -> None:
            territory_id, run_id, digest_char = spec

            def before_push(attempt: int) -> None:
                if attempt == 1:
                    barrier.wait(timeout=10)

            try:
                results[label] = persist_electoral_product(
                    root_dir=root,
                    territory_id=territory_id,
                    edition="2025",
                    run_id=run_id,
                    artifact_name=f"ddd-state-{run_id}-M08",
                    artifact_sha256=digest_char * 64,
                    source_commit=SOURCE_COMMIT,
                    target_branch="main",
                    max_attempts=4,
                    before_push=before_push,
                )
            except BaseException as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=("a", writer_a, first)),
            threading.Thread(target=worker, args=("b", writer_b, second)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)
        self.assertTrue(all(not thread.is_alive() for thread in threads))
        if errors:
            raise errors[0]

        clone(remote, verify)
        return results, verify

    @unittest.skipUnless(shutil.which("git"), "git executable required for real concurrent-push test")
    def test_two_concurrent_different_territories_preserve_both_registrations(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            results, verify = self.run_two(
                remote,
                ("alpha", 101, "a"),
                ("beta", 202, "b"),
            )

            self.assertEqual(set(results), {"a", "b"})
            catalog = yaml.safe_load(
                (verify / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
            )
            states = {
                row["territory_id"]: row["editions"]["2025"]
                for row in catalog["territories"]
            }
            for tid, run_id in (("alpha", 101), ("beta", 202)):
                self.assertTrue(states[tid]["electoral_product_available"])
                self.assertEqual(
                    states[tid]["last_valid_checkpoint"],
                    {"run_id": run_id, "stage": "M08"},
                )
                receipt = json.loads(
                    (
                        verify
                        / f"territorios/{tid}/evidencia/catalogo/electoral_product_2025.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(receipt["run_id"], run_id)
                self.assertEqual(receipt["source_commit"], SOURCE_COMMIT)

    @unittest.skipUnless(shutil.which("git"), "git executable required for real concurrent-push test")
    def test_two_concurrent_same_territory_rederive_from_new_head_without_rebase(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote = make_remote(base)
            results, verify = self.run_two(
                remote,
                ("alpha", 301, "c"),
                ("alpha", 302, "d"),
            )

            self.assertEqual(set(results), {"a", "b"})
            self.assertNotEqual(results["a"], results["b"])
            catalog = yaml.safe_load(
                (verify / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
            )
            alpha = next(
                row["editions"]["2025"]
                for row in catalog["territories"]
                if row["territory_id"] == "alpha"
            )
            receipt = json.loads(
                (
                    verify
                    / "territorios/alpha/evidencia/catalogo/electoral_product_2025.json"
                ).read_text(encoding="utf-8")
            )
            self.assertIn(receipt["run_id"], {301, 302})
            self.assertEqual(
                alpha["last_valid_checkpoint"],
                {"run_id": receipt["run_id"], "stage": "M08"},
            )
            self.assertTrue(alpha["electoral_product_available"])
            self.assertEqual(receipt["source_commit"], SOURCE_COMMIT)


if __name__ == "__main__":
    unittest.main()
