from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

import yaml

from herramientas.persistir_evidencia_pre_m04_operacional import (
    PreM04PersistenceConflict,
    persist_pre_m04_evidence,
)


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


def _state(tid: str, *, with_product: bool = False) -> dict:
    state = {
        "territory_declared": True,
        "preparation_status": "READY",
        "contract_path": f"territorios/{tid}/config/{tid}_2025.yaml",
        "territorial_source_declaration": f"territorios/{tid}/config/fuentes.yaml",
        "electoral_source_declaration": None,
        "territorial_sources_prepared": True,
        "territorial_contract_complete": True,
        "territorial_product_available": with_product,
        "electoral_source_prepared": False,
        "electoral_product_available": False,
        "territorial_certification": "PASS" if with_product else "NOT_CERTIFIED",
        "production_authorization": "AUTHORIZED",
        "last_valid_checkpoint": (
            {"run_id": 7, "stage": "M06"} if with_product else None
        ),
        "generation_enabled": False,
    }
    if with_product:
        state["evidence"] = {
            "territorial_product": (
                f"territorios/{tid}/evidencia/catalogo/territorial_product_2025.json"
            ),
            "territorial_product_source_lineage": (
                f"territorios/{tid}/evidencia/catalogo/"
                "territorial_product_source_lineage_2025.json"
            ),
        }
    return state


def write_fixture(root: Path, *, with_product: bool = False) -> None:
    (root / "configuracion").mkdir(parents=True)
    (root / "configuracion/catalogo_territorios_espana_2025.yaml").write_text(
        "territories:\n"
        "  - {territory_id: alpha, name: Alpha, status: source_prepared_pending_pre_m04}\n"
        "  - {territory_id: beta, name: Beta, status: source_prepared_pending_pre_m04}\n",
        encoding="utf-8",
    )
    catalog = {
        "schema": "ddd-preparation-catalog/1.1",
        "default_edition": "2025",
        "territories": [
            {
                "territory_id": "alpha",
                "name": "Alpha",
                "editions": {"2025": _state("alpha", with_product=with_product)},
            },
            {
                "territory_id": "beta",
                "name": "Beta",
                "editions": {"2025": _state("beta")},
            },
        ],
    }
    (root / "configuracion/catalogo_preparacion.yaml").write_text(
        yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    for tid in ("alpha", "beta"):
        config = root / f"territorios/{tid}/config"
        evidence = root / f"territorios/{tid}/evidencia/catalogo"
        config.mkdir(parents=True)
        evidence.mkdir(parents=True)
        (config / "fuentes.yaml").write_text(
            yaml.safe_dump({"territory": {"id": tid, "edition": "2025"}}),
            encoding="utf-8",
        )
        contract = {
            "meta": {
                "territory_id": tid,
                "year": 2025,
                "contract_level": "production_m01_m06",
                "production_authorization": "AUTHORIZED",
                "status": "source_prepared_pending_pre_m04",
            },
            "territory_contract": {
                "status": "source_prepared_pending_pre_m04",
            },
            "generation_state": {
                "source_prepared": True,
                "generation_enabled": False,
                "package_sha256": "b" * 64,
                "compatibility_identity_sha256": "c" * 64,
            },
            "validation": {
                "source_baseline": {
                    "package_sha256": "b" * 64,
                    "compatibility_identity_sha256": "c" * 64,
                    "population_year": 2023,
                    "section_year": 2023,
                }
            },
        }
        (config / f"{tid}_2025.yaml").write_text(
            yaml.safe_dump(contract, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

    if with_product:
        base = root / "territorios/alpha/evidencia/catalogo"
        (base / "territorial_product_2025.json").write_text(
            json.dumps({"schema": "ddd.catalog-evidence/1.0", "run_id": 7}) + "\n",
            encoding="utf-8",
        )
        (base / "territorial_product_source_lineage_2025.json").write_text(
            json.dumps(
                {
                    "schema": "ddd.territorial-product-source-lineage/1.0",
                    "territory_id": "alpha",
                    "edition": "2025",
                }
            )
            + "\n",
            encoding="utf-8",
        )


def make_remote(base: Path, *, with_product: bool = False) -> tuple[Path, str]:
    seed = base / "seed"
    remote = base / "remote.git"
    seed.mkdir()
    write_fixture(seed, with_product=with_product)
    git(seed, "init", "-b", "main")
    git(seed, "config", "user.name", "test")
    git(seed, "config", "user.email", "test@example.invalid")
    git(seed, "add", ".")
    git(seed, "commit", "-m", "base")
    base_sha = git(seed, "rev-parse", "HEAD")
    subprocess.run(
        ["git", "init", "--bare", str(remote)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    git(seed, "remote", "add", "origin", str(remote))
    git(seed, "push", "-u", "origin", "main")
    subprocess.run(
        ["git", "--git-dir", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True,
    )
    return remote, base_sha


def clone(remote: Path, destination: Path, *, source_sha: str | None = None) -> None:
    subprocess.run(
        ["git", "clone", "--branch", "main", str(remote), str(destination)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if source_sha is not None:
        git(destination, "checkout", "--detach", source_sha)


def candidate(path: Path, *, tid: str, run_id: int, source_commit: str, mark: str) -> Path:
    payload = {
        "schema": "ddd.catalog-evidence/1.0",
        "kind": "generation_preflight",
        "territory_id": tid,
        "territory_name": tid.title(),
        "edition": "2025",
        "run_id": run_id,
        "source_commit": source_commit,
        "artifact_name": f"ddd-state-{run_id}-M03U",
        "artifact_sha256": mark * 64,
        "decision": "READY_FOR_FIRST_GENERATION",
        "stage": "M03U",
        "source": {
            "artifact_name": f"ddd-source-package-{tid}-2025-{run_id}",
            "artifact_sha256": "a" * 64,
            "package_sha256": "b" * 64,
            "compatibility_identity_sha256": "c" * 64,
            "territorial_identity_sha256": "d" * 64,
            "population_year": 2023,
            "section_year": 2023,
        },
        "graph": {
            "artifact_name": f"ddd-state-{run_id}-M03",
            "artifact_sha256": "e" * 64,
        },
        "partitioning": {
            "job_artifact_name": f"ddd-internal-units-{run_id}",
            "job_artifact_sha256": "f" * 64,
            "status": "NOOP",
        },
        "effective_gate": {
            "allowed": True,
            "route": "validated_pre_m04_topology",
        },
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def persist(
    root: Path,
    candidate_path: Path,
    *,
    tid: str,
    run_id: int,
    source_sha: str,
    result_json: Path | None = None,
    max_attempts: int = 4,
    before_push=None,
) -> str:
    return persist_pre_m04_evidence(
        root_dir=root,
        territory_id=tid,
        edition="2025",
        run_id=run_id,
        contract_path=f"territorios/{tid}/config/{tid}_2025.yaml",
        candidate_evidence=candidate_path,
        source_commit=source_sha,
        target_branch="main",
        result_json=result_json,
        max_attempts=max_attempts,
        before_push=before_push,
    )


def state(root: Path, tid: str) -> dict:
    catalog = yaml.safe_load(
        (root / "configuracion/catalogo_preparacion.yaml").read_text(encoding="utf-8")
    )
    return next(
        row["editions"]["2025"]
        for row in catalog["territories"]
        if row["territory_id"] == tid
    )


@unittest.skipUnless(shutil.which("git"), "git executable required")
class PreM04SemanticPersistenceTests(unittest.TestCase):
    def test_two_writers_same_base_different_territories_preserve_both(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            writer_a = base / "writer-a"
            writer_b = base / "writer-b"
            clone(remote, writer_a, source_sha=source_sha)
            clone(remote, writer_b, source_sha=source_sha)
            ca = candidate(base / "alpha.json", tid="alpha", run_id=101, source_commit=source_sha, mark="1")
            cb = candidate(base / "beta.json", tid="beta", run_id=202, source_commit=source_sha, mark="2")
            barrier = threading.Barrier(2)
            errors: list[BaseException] = []

            def worker(root: Path, cand: Path, tid: str, run_id: int):
                try:
                    persist(
                        root,
                        cand,
                        tid=tid,
                        run_id=run_id,
                        source_sha=source_sha,
                        before_push=lambda attempt: barrier.wait(timeout=10)
                        if attempt == 1
                        else None,
                    )
                except BaseException as exc:
                    errors.append(exc)

            threads = [
                threading.Thread(target=worker, args=(writer_a, ca, "alpha", 101)),
                threading.Thread(target=worker, args=(writer_b, cb, "beta", 202)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])

            verify = base / "verify"
            clone(remote, verify)
            self.assertTrue(state(verify, "alpha")["generation_enabled"])
            self.assertTrue(state(verify, "beta")["generation_enabled"])
            self.assertEqual(
                json.loads(
                    (verify / "territorios/alpha/evidencia/catalogo/generation_preflight_2025.json").read_text()
                )["run_id"],
                101,
            )
            self.assertEqual(
                json.loads(
                    (verify / "territorios/beta/evidencia/catalogo/generation_preflight_2025.json").read_text()
                )["run_id"],
                202,
            )

    def test_branch_advance_rederives_operation_without_losing_remote_change(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            writer = base / "writer"
            contender = base / "contender"
            clone(remote, writer, source_sha=source_sha)
            clone(remote, contender)
            cand = candidate(base / "alpha.json", tid="alpha", run_id=303, source_commit=source_sha, mark="3")
            advanced = False

            def advance(attempt: int):
                nonlocal advanced
                if attempt != 1:
                    return
                (contender / "unrelated.txt").write_text("concurrent change\n")
                git(contender, "add", "unrelated.txt")
                git(contender, "config", "user.name", "test")
                git(contender, "config", "user.email", "test@example.invalid")
                git(contender, "commit", "-m", "unrelated concurrent change")
                git(contender, "push", "origin", "HEAD:main")
                advanced = True

            persist(
                writer,
                cand,
                tid="alpha",
                run_id=303,
                source_sha=source_sha,
                before_push=advance,
            )
            self.assertTrue(advanced)
            verify = base / "verify"
            clone(remote, verify)
            self.assertEqual((verify / "unrelated.txt").read_text(), "concurrent change\n")
            self.assertTrue(state(verify, "alpha")["generation_enabled"])

    def test_incompatible_same_territory_operations_conflict_explicitly(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            writer_a = base / "writer-a"
            writer_b = base / "writer-b"
            clone(remote, writer_a, source_sha=source_sha)
            clone(remote, writer_b, source_sha=source_sha)
            ca = candidate(base / "a.json", tid="alpha", run_id=401, source_commit=source_sha, mark="4")
            cb = candidate(base / "b.json", tid="alpha", run_id=402, source_commit=source_sha, mark="5")
            barrier = threading.Barrier(2)
            outcomes: list[str] = []

            def worker(root: Path, cand: Path, run_id: int):
                try:
                    persist(
                        root,
                        cand,
                        tid="alpha",
                        run_id=run_id,
                        source_sha=source_sha,
                        before_push=lambda attempt: barrier.wait(timeout=10)
                        if attempt == 1
                        else None,
                    )
                    outcomes.append("REGISTERED")
                except PreM04PersistenceConflict as exc:
                    outcomes.append(exc.status)

            threads = [
                threading.Thread(target=worker, args=(writer_a, ca, 401)),
                threading.Thread(target=worker, args=(writer_b, cb, 402)),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)
            self.assertCountEqual(outcomes, ["REGISTERED", "CONCURRENT_PRE_M04_CHANGED"])

    def test_same_operation_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            first = base / "first"
            clone(remote, first, source_sha=source_sha)
            cand = candidate(base / "alpha.json", tid="alpha", run_id=501, source_commit=source_sha, mark="6")
            persist(first, cand, tid="alpha", run_id=501, source_sha=source_sha)

            second = base / "second"
            clone(remote, second, source_sha=source_sha)
            result = base / "idempotent.json"
            before = git(second, "ls-remote", "origin", "refs/heads/main").split()[0]
            returned = persist(
                second,
                cand,
                tid="alpha",
                run_id=501,
                source_sha=source_sha,
                result_json=result,
            )
            after = git(second, "ls-remote", "origin", "refs/heads/main").split()[0]
            self.assertEqual(returned, before)
            self.assertEqual(after, before)
            self.assertEqual(json.loads(result.read_text())["status"], "NO_OP")

    def test_idempotent_registration_blocks_if_protected_same_territory_state_changed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            first = base / "first"
            clone(remote, first, source_sha=source_sha)
            cand = candidate(
                base / "alpha-protected.json",
                tid="alpha",
                run_id=551,
                source_commit=source_sha,
                mark="9",
            )
            persist(first, cand, tid="alpha", run_id=551, source_sha=source_sha)

            contender = base / "contender-protected"
            clone(remote, contender)
            catalog_path = contender / "configuracion/catalogo_preparacion.yaml"
            catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))
            alpha = next(
                row["editions"]["2025"]
                for row in catalog["territories"]
                if row["territory_id"] == "alpha"
            )
            alpha["last_valid_checkpoint"] = {"run_id": 99, "stage": "M06"}
            catalog_path.write_text(
                yaml.safe_dump(catalog, allow_unicode=True, sort_keys=False),
                encoding="utf-8",
            )
            git(contender, "config", "user.name", "test")
            git(contender, "config", "user.email", "test@example.invalid")
            git(contender, "add", "configuracion/catalogo_preparacion.yaml")
            git(contender, "commit", "-m", "advance protected alpha state")
            git(contender, "push", "origin", "HEAD:main")

            retry = base / "retry-protected"
            clone(remote, retry, source_sha=source_sha)
            result = base / "protected-conflict.json"
            with self.assertRaises(PreM04PersistenceConflict) as ctx:
                persist(
                    retry,
                    cand,
                    tid="alpha",
                    run_id=551,
                    source_sha=source_sha,
                    result_json=result,
                )
            self.assertEqual(ctx.exception.status, "INCOMPATIBLE_CURRENT_STATE")
            self.assertIn("PRE_M04_PROTECTED_CONTEXT_CHANGE", str(ctx.exception))
            diagnostic = json.loads(result.read_text())
            self.assertEqual(diagnostic["status"], "INCOMPATIBLE_CURRENT_STATE")

    def test_idempotent_noop_retries_if_remote_advances_before_return(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            first = base / "first-noop-race"
            clone(remote, first, source_sha=source_sha)
            cand = candidate(
                base / "alpha-noop-race.json",
                tid="alpha",
                run_id=552,
                source_commit=source_sha,
                mark="a",
            )
            persist(first, cand, tid="alpha", run_id=552, source_sha=source_sha)

            writer = base / "writer-noop-race"
            contender = base / "contender-noop-race"
            clone(remote, writer, source_sha=source_sha)
            clone(remote, contender)
            result = base / "noop-race.json"
            advanced_sha = ""

            def advance_once(attempt: int):
                nonlocal advanced_sha
                if attempt != 1:
                    return
                (contender / "unrelated-noop-race.txt").write_text(
                    "advanced during NO_OP validation\n",
                    encoding="utf-8",
                )
                git(contender, "config", "user.name", "test")
                git(contender, "config", "user.email", "test@example.invalid")
                git(contender, "add", "unrelated-noop-race.txt")
                git(contender, "commit", "-m", "advance remote during NO_OP")
                git(contender, "push", "origin", "HEAD:main")
                advanced_sha = git(contender, "rev-parse", "HEAD")

            returned = persist(
                writer,
                cand,
                tid="alpha",
                run_id=552,
                source_sha=source_sha,
                result_json=result,
                before_push=advance_once,
            )
            remote_head = git(
                writer, "ls-remote", "origin", "refs/heads/main"
            ).split()[0]
            diagnostic = json.loads(result.read_text())
            self.assertTrue(advanced_sha)
            self.assertEqual(returned, advanced_sha)
            self.assertEqual(returned, remote_head)
            self.assertEqual(diagnostic["status"], "NO_OP")
            self.assertEqual(diagnostic["attempt"], 2)

    def test_retry_exhaustion_records_diagnostic_and_does_not_register_success(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base)
            writer = base / "writer"
            contender = base / "contender"
            clone(remote, writer, source_sha=source_sha)
            clone(remote, contender)
            cand = candidate(base / "alpha.json", tid="alpha", run_id=601, source_commit=source_sha, mark="7")
            result = base / "failure.json"

            def advance_every_time(attempt: int):
                git(contender, "fetch", "origin", "main")
                git(contender, "reset", "--hard", "origin/main")
                path = contender / "race.txt"
                previous = path.read_text() if path.exists() else ""
                path.write_text(previous + f"{attempt}\n")
                git(contender, "add", "race.txt")
                git(contender, "config", "user.name", "test")
                git(contender, "config", "user.email", "test@example.invalid")
                git(contender, "commit", "-m", f"advance {attempt}")
                git(contender, "push", "origin", "HEAD:main")

            with self.assertRaisesRegex(RuntimeError, "No se pudo registrar la evidencia pre-M04"):
                persist(
                    writer,
                    cand,
                    tid="alpha",
                    run_id=601,
                    source_sha=source_sha,
                    result_json=result,
                    max_attempts=2,
                    before_push=advance_every_time,
                )

            diagnostic = json.loads(result.read_text())
            self.assertEqual(diagnostic["status"], "PUSH_RETRY_EXHAUSTED")
            verify = base / "verify"
            clone(remote, verify)
            self.assertFalse(state(verify, "alpha")["generation_enabled"])
            self.assertFalse(
                (
                    verify
                    / "territorios/alpha/evidencia/catalogo/generation_preflight_2025.json"
                ).exists()
            )

    def test_latest_certified_product_receipt_checkpoint_and_lineage_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            remote, source_sha = make_remote(base, with_product=True)
            writer = base / "writer"
            clone(remote, writer, source_sha=source_sha)
            cand = candidate(base / "alpha.json", tid="alpha", run_id=701, source_commit=source_sha, mark="8")
            persist(writer, cand, tid="alpha", run_id=701, source_sha=source_sha)

            verify = base / "verify"
            clone(remote, verify)
            alpha = state(verify, "alpha")
            self.assertTrue(alpha["territorial_product_available"])
            self.assertEqual(alpha["territorial_certification"], "PASS")
            self.assertEqual(alpha["last_valid_checkpoint"], {"run_id": 7, "stage": "M06"})
            self.assertEqual(
                alpha["evidence"]["territorial_product"],
                "territorios/alpha/evidencia/catalogo/territorial_product_2025.json",
            )
            self.assertEqual(
                alpha["evidence"]["territorial_product_source_lineage"],
                "territorios/alpha/evidencia/catalogo/territorial_product_source_lineage_2025.json",
            )
            self.assertTrue(
                (
                    verify
                    / "territorios/alpha/evidencia/catalogo/territorial_product_2025.json"
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main()
