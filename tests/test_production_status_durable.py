"""Regresiones sintéticas del estado durable de producción tras recuperar M06."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas" / "estado_produccion.py"
WORKFLOW = ROOT / ".github" / "workflows" / "producir-territorio-por-contrato.yml"


def governed_geometry() -> dict:
    return {
        "schema": "ddd.geometric-components-audit/2.0",
        "decision": "PASS_WITH_EXCEPTIONS",
        "governed_exceptions": 1,
        "blocked_districts": 0,
        "policy_mismatches": 0,
        "contract_blockers": [],
        "districts": [{
            "district_id": "fixture-01",
            "decision": "PASS_WITH_EXCEPTIONS",
            "unexplained_components": [],
            "causal_exceptions": [{
                "type": "GOVERNED_BRIDGE",
                "components": [1, 2],
                "endpoints": ["a", "b"],
                "contract_sha256": "c" * 64,
                "source": "contract:topology_bridges[0]",
            }],
        }],
    }


def partial_population() -> dict:
    return {
        "population_repair": {
            "enabled": True,
            "result": "IMPROVED_NOT_REPAIRED",
            "objective_before": [0, 4, 0.25, 1.0, 10],
            "objective_after": [0, 3, 0.20, 0.9, 9],
            "termination_reason": "CANDIDATE_BUDGET_EXHAUSTED",
            "baseline_restored": False,
        }
    }


class DurableProductionStatusTests(unittest.TestCase):
    def _fixture(self, tmp: Path) -> tuple[Path, Path, Path, Path]:
        run_name = "synthetic_checkpoint"
        evidence_dir = tmp / "preparacion" / run_name
        evidence_dir.mkdir(parents=True)
        report = evidence_dir / f"{run_name}_m05_informe.json"
        params = tmp / "territory.yaml"
        params.write_text(yaml.safe_dump({
            "meta": {"year": 2025, "run_name": run_name},
            "modulos": {
                "modulo_05_optimizar_distritos": {
                    "out_report": str(tmp / "preparacion" / "{run_name}" / "{run_name}_m05_informe.json")
                }
            },
        }), encoding="utf-8")
        geometry = tmp / "m06_contiguedad_geometrica.json"
        geometry.write_text(json.dumps(governed_geometry()), encoding="utf-8")
        audit_dir = tmp / ".ddd-audit"
        return params, report, geometry, audit_dir

    def _run(self, params: Path, geometry: Path, audit_dir: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([
            "python", str(SCRIPT),
            "--params", str(params),
            "--territory-id", "synthetic",
            "--run-id", "production-synthetic-checkpoint",
            "--from-stage", "M06",
            "--to-stage", "M08",
            "--execution-outcome", "success",
            "--geometric-outcome", "success",
            "--geometric-decision", "PASS_WITH_EXCEPTIONS",
            "--geometric-audit", str(geometry),
            "--output", str(audit_dir / "production_status.json"),
        ], cwd=ROOT, text=True, capture_output=True, check=False)

    def test_checkpoint_partial_population_records_block_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            params, report, geometry, audit_dir = self._fixture(tmp)
            report.write_text(json.dumps(partial_population()), encoding="utf-8")

            result = self._run(params, geometry, audit_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((audit_dir / "production_status.json").read_text(encoding="utf-8"))
            causes = json.loads((audit_dir / "block_causes.json").read_text(encoding="utf-8"))
            shutil.copy2(geometry, audit_dir / geometry.name)

            self.assertEqual(status["execution_outcome"], "success")
            self.assertEqual(status["geometric_decision"], "PASS_WITH_EXCEPTIONS")
            self.assertEqual(status["population_decision"], "TARGET_IMPROVED_NOT_MET")
            self.assertEqual(status["decision"], "BLOCK")
            self.assertEqual(status["block_cause"], "POPULATION_TARGET_NOT_MET")
            self.assertEqual(causes["block_cause"], "POPULATION_TARGET_NOT_MET")
            self.assertTrue((audit_dir / "production_status.json").is_file())
            self.assertTrue((audit_dir / "block_causes.json").is_file())
            self.assertTrue((audit_dir / geometry.name).is_file())

            workflow = WORKFLOW.read_text(encoding="utf-8")
            registration = workflow.split("      - name: Registrar estado verificable de producción", 1)[1].split("      - name: Aplicar puerta geométrica", 1)[0]
            self.assertIn('cp "$audit" .ddd-audit/', registration)
            self.assertIn("path: .ddd-audit", registration)
            m07 = workflow.split("  m07:\n", 1)[1].split("\n  m08:\n", 1)[0]
            self.assertIn("needs.auditoria.result == 'success'", m07)
            self.assertNotIn("population_decision", m07)
            self.assertNotIn("production_status", m07)

    def test_missing_or_damaged_population_is_closed_block_not_unknown(self):
        for mode in ("missing", "damaged"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as raw:
                tmp = Path(raw)
                params, report, geometry, audit_dir = self._fixture(tmp)
                if mode == "damaged":
                    report.write_text("{not-json", encoding="utf-8")

                result = self._run(params, geometry, audit_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                status = json.loads((audit_dir / "production_status.json").read_text(encoding="utf-8"))
                causes = json.loads((audit_dir / "block_causes.json").read_text(encoding="utf-8"))
                shutil.copy2(geometry, audit_dir / geometry.name)

                expected = "MISSING" if mode == "missing" else "INVALID_JSON"
                self.assertEqual(status["decision"], "BLOCK")
                self.assertEqual(status["population_outcome"], "failure")
                self.assertEqual(status["population_decision"], "HARD_BLOCK")
                self.assertEqual(status["population_evidence_status"], expected)
                self.assertEqual(status["block_cause"], "M05_POPULATION_EVIDENCE_MISSING")
                self.assertTrue(status["population_evidence_error"])
                self.assertEqual(causes["population_evidence_status"], expected)
                self.assertTrue((audit_dir / "production_status.json").is_file())
                self.assertTrue((audit_dir / "block_causes.json").is_file())
                self.assertTrue((audit_dir / geometry.name).is_file())
                self.assertNotIn("UNKNOWN", json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
