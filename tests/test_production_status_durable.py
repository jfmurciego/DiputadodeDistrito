"""Regresiones sintéticas del estado durable de producción tras recuperar M06."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
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


def workflow_jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def evaluate_job_if(expression: str, context: dict[str, str]) -> bool:
    """Evalúa el subconjunto de sintaxis GitHub usado por auditoria/M07 contra un contexto sintético."""
    body = expression.strip()
    if body.startswith("${{") and body.endswith("}}"):
        body = body[3:-2].strip()
    replacements = {
        "always()": "True",
        "fromJSON(needs.resolve.outputs.from_num)": str(int(context["from_num"])),
        "fromJSON(needs.resolve.outputs.to_num)": str(int(context["to_num"])),
        "needs.resolve.result": repr(context["resolve_result"]),
        "needs.resolve.outputs.mode": repr(context["mode"]),
        "needs.m06.result": repr(context["m06_result"]),
        "needs.auditoria.result": repr(context["auditoria_result"]),
        "needs.electoral_source.result": repr(context.get("electoral_source_result", "success")),
        "needs.m07.result": repr(context.get("m07_result", "success")),
        "needs.m08.result": repr(context.get("m08_result", "success")),
        "inputs.publish_result": "True" if context.get("publish_result", "true") == "true" else "False",
        "inputs.checkpoint_run_id": repr(context.get("checkpoint_run_id", "")),
    }
    for token, value in replacements.items():
        body = body.replace(token, value)
    body = body.replace("&&", " and ").replace("||", " or ")
    body = body.replace(" true", " True").replace(" false", " False")
    return bool(eval(body, {"__builtins__": {}}, {}))


def archive_members(audit_dir: Path, tmp: Path) -> set[str]:
    archive = shutil.make_archive(str(tmp / "ddd-audit-synthetic"), "zip", root_dir=audit_dir)
    with zipfile.ZipFile(archive) as payload:
        return set(payload.namelist())


class DurableProductionStatusTests(unittest.TestCase):
    def _fixture(self, tmp: Path) -> tuple[Path, Path, Path, Path]:
        run_name = "synthetic_checkpoint"
        evidence_dir = tmp / "preparacion" / run_name
        evidence_dir.mkdir(parents=True)
        report = evidence_dir / f"{run_name}_m05_informe.json"
        params = tmp / "territory.yaml"
        params.write_text(yaml.safe_dump({
            "meta": {"year": 2025, "run_name": run_name},
            "validation": {"require_zero_outside_tolerance_after_m05": True},
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

    def _run(self, params: Path, geometry: Path, audit_dir: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(extra_env or {})
        previous_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(ROOT) if not previous_pythonpath else f"{ROOT}{os.pathsep}{previous_pythonpath}"
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
        ], cwd=ROOT, env=env, text=True, capture_output=True, check=False)

    def test_checkpoint_partial_population_blocks_m07_m08_and_publication(self):
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

            members = archive_members(audit_dir, tmp)
            self.assertIn("production_status.json", members)
            self.assertIn("block_causes.json", members)
            self.assertIn(geometry.name, members)

            jobs = workflow_jobs()
            upload_steps = [
                step for step in jobs["auditoria"]["steps"]
                if step.get("uses") == "actions/upload-artifact@v6"
            ]
            self.assertEqual(len(upload_steps), 1)
            self.assertEqual(upload_steps[0]["with"]["path"], ".ddd-audit")
            self.assertEqual(upload_steps[0]["with"]["if-no-files-found"], "error")

            gate_step = next(
                step for step in jobs["auditoria"]["steps"]
                if step.get("name") == "Aplicar puerta de certificación territorial"
            )
            self.assertIn(".ddd-audit/production_status.json", gate_step["run"])
            self.assertIn("PASS|PASS_WITH_EXCEPTIONS", gate_step["run"])
            self.assertNotIn("steps.geometric.outcome", gate_step["run"])

            gate_dir = tmp / "gate"
            (gate_dir / ".ddd-audit").mkdir(parents=True)
            gate_status = gate_dir / ".ddd-audit" / "production_status.json"
            gate_status.write_text(json.dumps(status), encoding="utf-8")
            bin_dir = gate_dir / "bin"
            bin_dir.mkdir()
            jq = bin_dir / "jq"
            jq.write_text(
                "#!/usr/bin/env python3\n"
                "import json, sys\n"
                "path = sys.argv[-1]\n"
                "data = json.load(open(path, encoding='utf-8'))\n"
                "print(data.get('decision') or 'UNKNOWN')\n",
                encoding="utf-8",
            )
            jq.chmod(0o755)
            gate_env = os.environ.copy()
            gate_env["PATH"] = f"{bin_dir}{os.pathsep}{gate_env.get('PATH', '')}"

            blocked = subprocess.run(
                ["bash", "-c", gate_step["run"]],
                cwd=gate_dir,
                env=gate_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("Certificación territorial bloqueada: BLOCK", blocked.stderr)

            checkpoint_context = {
                "resolve_result": "success",
                "mode": "execute",
                "from_num": "7",
                "to_num": "8",
                "m06_result": "skipped",
                "auditoria_result": "failure",
                "electoral_source_result": "skipped",
                "m07_result": "skipped",
                "m08_result": "skipped",
                "publish_result": "true",
                "checkpoint_run_id": "35319351944",
            }
            self.assertTrue(evaluate_job_if(jobs["auditoria"]["if"], checkpoint_context))
            self.assertFalse(evaluate_job_if(jobs["electoral_source"]["if"], checkpoint_context))
            self.assertFalse(evaluate_job_if(jobs["m07"]["if"], checkpoint_context))
            self.assertFalse(evaluate_job_if(jobs["m08"]["if"], checkpoint_context))
            self.assertFalse(evaluate_job_if(jobs["visor"]["if"], checkpoint_context))

            for accepted_decision in ("PASS", "PASS_WITH_EXCEPTIONS"):
                gate_status.write_text(json.dumps({"decision": accepted_decision}), encoding="utf-8")
                accepted = subprocess.run(
                    ["bash", "-c", gate_step["run"]],
                    cwd=gate_dir,
                    env=gate_env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(accepted.returncode, 0, accepted.stderr)

            state_step = next(step for step in jobs["auditoria"]["steps"] if step.get("name") == "Resolver checkpoint M06")
            self.assertIn('else state_run_id="$CHECKPOINT_RUN_ID"', state_step["run"])

    def test_partial_population_is_not_a_block_when_contract_does_not_require_target(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            params, report, geometry, audit_dir = self._fixture(tmp)
            cfg = yaml.safe_load(params.read_text(encoding="utf-8"))
            cfg["validation"]["require_zero_outside_tolerance_after_m05"] = False
            params.write_text(yaml.safe_dump(cfg), encoding="utf-8")
            report.write_text(json.dumps(partial_population()), encoding="utf-8")

            result = self._run(params, geometry, audit_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((audit_dir / "production_status.json").read_text(encoding="utf-8"))
            self.assertFalse(status["population_target_required"])
            self.assertEqual(status["population_decision"], "TARGET_IMPROVED_NOT_MET")
            self.assertEqual(status["population_hard_constraints_after"], 0)
            self.assertEqual(status["decision"], "PASS_WITH_EXCEPTIONS")
            self.assertNotIn("block_cause", status)

    def test_explicit_run_id_resolves_population_evidence_even_if_environment_says_local(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            params, _, geometry, audit_dir = self._fixture(tmp)
            params.write_text(yaml.safe_dump({
                "meta": {"year": 2025, "run_name": "synthetic_checkpoint"},
                "io": {"project_root": {"path": str(tmp)}},
                "modulos": {
                    "modulo_05_optimizar_distritos": {
                        "out_report": "ejecuciones/{run_id}/{run_name}_m05_informe.json"
                    }
                },
            }), encoding="utf-8")
            report = tmp / "ejecuciones" / "production-synthetic-checkpoint" / "synthetic_checkpoint_m05_informe.json"
            report.parent.mkdir(parents=True)
            report.write_text(json.dumps({
                "population_repair": {
                    "enabled": True,
                    "result": "REPAIRED",
                    "objective_before": [0, 3, 0.20, 1.0, 10],
                    "objective_after": [0, 0, 0.11, 0.7, 8],
                    "termination_reason": "QUEUE_EMPTY",
                    "baseline_restored": False,
                }
            }), encoding="utf-8")

            result = self._run(params, geometry, audit_dir, {"DDD_RUN_ID": "local"})
            self.assertEqual(result.returncode, 0, result.stderr)
            status = json.loads((audit_dir / "production_status.json").read_text(encoding="utf-8"))
            self.assertEqual(status["decision"], "PASS_WITH_EXCEPTIONS")
            self.assertEqual(status["population_decision"], "TARGET_MET")
            self.assertEqual(status["population_evidence_status"], "VALID")
            self.assertEqual(Path(status["population_evidence_path"]), report.resolve())
            self.assertNotIn("/ejecuciones/local/", status["population_evidence_path"])

    def test_missing_or_damaged_population_is_closed_block_not_unknown(self):
        expected_causes = {
            "missing": "M05_POPULATION_EVIDENCE_MISSING",
            "damaged": "M05_POPULATION_EVIDENCE_INVALID",
        }
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

                expected_status = "MISSING" if mode == "missing" else "INVALID_JSON"
                self.assertEqual(status["decision"], "BLOCK")
                self.assertEqual(status["population_outcome"], "failure")
                self.assertEqual(status["population_decision"], "HARD_BLOCK")
                self.assertEqual(status["population_evidence_status"], expected_status)
                self.assertEqual(status["block_cause"], expected_causes[mode])
                self.assertTrue(status["population_evidence_error"])
                self.assertEqual(causes["population_evidence_status"], expected_status)
                self.assertEqual(causes["block_cause"], expected_causes[mode])

                members = archive_members(audit_dir, tmp)
                self.assertIn("production_status.json", members)
                self.assertIn("block_causes.json", members)
                self.assertIn(geometry.name, members)
                self.assertNotIn("UNKNOWN", json.dumps(status, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
