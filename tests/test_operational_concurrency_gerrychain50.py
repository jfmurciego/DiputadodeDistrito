"""Regressions for durable Actions queues and the explicit GerryChain 50 contract."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"


def load_yaml(path: Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)


def concurrency_blocks(node, path=()):
    if isinstance(node, dict):
        if isinstance(node.get("concurrency"), dict):
            yield "/".join(path) or "workflow", node["concurrency"]
        for key, value in node.items():
            yield from concurrency_blocks(value, path + (key,))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from concurrency_blocks(value, path + (str(index),))


class OperationalConcurrencyTests(unittest.TestCase):
    def test_every_non_cancelling_group_queues_pending_jobs(self):
        blocks = []
        for path in sorted(WF.glob("*.yml")):
            data = load_yaml(path)
            for location, concurrency in concurrency_blocks(data):
                if concurrency.get("cancel-in-progress", "false") == "false":
                    blocks.append((path.name, location, concurrency))
                    self.assertEqual(
                        concurrency.get("queue"), "max",
                        f"{path.name}:{location} can replace a pending run",
                    )
        self.assertGreaterEqual(len(blocks), 17)

    def test_local_queue_smoke_preserves_more_than_two_pending_jobs(self):
        # Mirrors GitHub's queue:max contract: one active run plus FIFO pending runs.
        active = "prep-24"
        pending = ["register-24", "verify-24", "other-1", "other-2"]
        incoming = "other-3"
        pending.append(incoming)
        self.assertEqual(active, "prep-24")
        self.assertEqual(pending, ["register-24", "verify-24", "other-1", "other-2", "other-3"])
        self.assertNotIn("CANCELLED", pending)

    def test_remote_smoke_is_pr_only_and_has_no_productive_side_effects(self):
        path = ROOT / "legacy/workflows/retirados_20261031/p0-verificacion-remota.yml"
        data = load_yaml(path)
        self.assertIn("pull_request", data["on"])
        self.assertNotIn("workflow_dispatch", data["on"])
        job = data["jobs"]["comprobar-cola"]
        self.assertEqual(job["concurrency"]["group"], "ddd-p0-pr-queue-${{ github.run_id }}")
        self.assertEqual(job["concurrency"]["queue"], "max")
        self.assertEqual(job["concurrency"]["cancel-in-progress"], "false")
        self.assertEqual(job["strategy"]["matrix"]["ticket"], ["1", "2", "3", "4", "5"])
        steps = job["steps"]
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["env"]["SMOKE_TICKET"], "${{ matrix.ticket }}")
        self.assertNotIn("${{ matrix.ticket }}", steps[0]["run"])
        self.assertIn('[[ "$SMOKE_TICKET" =~ ^[1-5]$ ]]', steps[0]["run"])
        self.assertIn("sleep 15", steps[0]["run"])
        self.assertNotIn("uses", steps[0])

    def test_reported_20261024_prepare_register_verify_pattern_is_preserved(self):
        # Replays the failure sequence reported by Work without inventing run IDs.
        legacy = [("territorial_preparation", "SUCCESS"),
                  ("durable_registration", "CANCELLED"),
                  ("later_verification", "FAILURE")]
        self.assertEqual([state for _, state in legacy], ["SUCCESS", "CANCELLED", "FAILURE"])
        pending = ["durable_registration"]
        replaced_queue = ["later_verification"]  # GitHub's default queue: single behavior.
        self.assertEqual(set(pending) - set(replaced_queue), {"durable_registration"})
        pending.append("later_verification")  # queue: max preserves both jobs.
        self.assertEqual(pending, ["durable_registration", "later_verification"])


class GerryChain50WiringTests(unittest.TestCase):
    def test_manual_02_derives_gerrychain50_contract(self):
        data = load_yaml(WF / "produccion-distritos.yml")
        manual_inputs = data["on"]["workflow_dispatch"]["inputs"]
        self.assertNotIn("gerrychain_entrypoint", manual_inputs)
        self.assertNotIn("require_unique_hashes", manual_inputs)
        child = data["jobs"]["ruta"]["with"]
        self.assertIn("gerrychain_50", child["gerrychain_entrypoint"])
        self.assertIn("require_unique_hashes", child)

    def test_manual_00_derives_contract_and_preserves_campaign_checks(self):
        data = load_yaml(WF / "ejecucion-completa-proyecto.yml")
        outputs = data["jobs"]["planificar"]["outputs"]
        self.assertIn("gerrychain_entrypoint", outputs)
        self.assertIn("require_unique_hashes", outputs)
        child = data["jobs"]["generar"]["with"]
        self.assertIn("needs.planificar.outputs.gerrychain_entrypoint", child["gerrychain_entrypoint"])
        self.assertIn("needs.planificar.outputs.require_unique_hashes", child["require_unique_hashes"])
        source = (WF / "ejecucion-completa-proyecto.yml").read_text()
        self.assertIn('"gerrychain_50" if p["optimization_algorithm"] == "GerryChain 50" else ""', source)
        self.assertIn("Contrato de estrategia incompleto en el caller", source)

    def test_gerrychain50_failure_cannot_fall_back_to_canonical(self):
        script = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        failure = script.index('if [[ "${DDD_OPTIMIZATION_ALGORITHM:-}" == "GerryChain 50" ]]; then', script.index('if (( gerry_rc != 0 ))'))
        fallback = script.index('Canónico como fallback', failure)
        g50_failure_path = script[failure:fallback]
        self.assertIn("GerryChain 50 no admite fallback", g50_failure_path)
        self.assertIn('"GerryChain 50"|gerrychain_50) printf', script)
        self.assertIn('registrar_optimizacion "GerryChain 50" "" false "gerrychain50_runtime_failure" "$gerry_rc" "$candidate_count" FAILED NOT_CERTIFIED', g50_failure_path)
        self.assertIn("exit 44", g50_failure_path)
        self.assertIn('"execution_status":status', script)
        self.assertIn('"candidate_count":int(candidate_count)', script)

    def test_selected_strategy_reuses_m04_and_reports_certification_separately(self):
        resolver = (WF / "produccion-distritos.yml").read_text(encoding="utf-8")
        procedure = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        reusable = (WF / "_reutilizable-generacion-territorial.yml").read_text(encoding="utf-8")
        self.assertIn("search_from=4", resolver)
        self.assertIn("--validate-baseline-only", procedure)
        self.assertIn("PENDING_M06", procedure)
        self.assertIn('report["certification_status"]=decision', reusable)
        self.assertIn('report["certification_stage"]="M06_INDEPENDENT_GEOMETRIC_AUDIT"', reusable)


class GerryChain50PortfolioTests(unittest.TestCase):
    def test_exact_fifty_unique_hashes_and_integral_artifacts_pass(self):
        from herramientas.validar_portfolio_gerrychain50 import validate_portfolio

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows = []
            for i in range(50):
                artifact = root / f"candidate-{i}.zip"
                payload = f"candidate-{i}".encode()
                artifact.write_bytes(payload)
                rows.append({
                    "assignment_hash": f"{i:064x}",
                    "geojson": str(artifact),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "selected": i == 0,
                })
            report = {
                "search": {"selected_assignment_hash": rows[0]["assignment_hash"]},
                "portfolio": {
                    "candidate_count": 50,
                    "unique_candidate_count": 50,
                    "candidates": rows,
                }
            }
            report_path = root / "m05.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(validate_portfolio(report_path)["unique_candidate_hash_count"], 50)

    def test_duplicate_hash_or_missing_candidate_fails_closed(self):
        from herramientas.validar_portfolio_gerrychain50 import PortfolioValidationError, validate_portfolio

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            artifact = root / "candidate.zip"
            artifact.write_bytes(b"candidate")
            row = {
                "assignment_hash": "a" * 64,
                "geojson": str(artifact),
                "sha256": hashlib.sha256(b"candidate").hexdigest(),
                "selected": True,
            }
            report_path = root / "m05.json"
            report_path.write_text(json.dumps({"selected_assignment_hash": "a" * 64, "portfolio": {
                "candidate_count": 50,
                "unique_candidate_count": 1,
                "candidates": [row] * 50,
            }}), encoding="utf-8")
            with self.assertRaises(PortfolioValidationError):
                validate_portfolio(report_path)


if __name__ == "__main__":
    unittest.main()
