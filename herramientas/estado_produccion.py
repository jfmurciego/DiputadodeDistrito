#!/usr/bin/env python3
"""Construye un estado durable de producción separando ejecución, población y geometría."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

# Permite ejecutar este entrypoint directamente (`python herramientas/estado_produccion.py`)
# desde la raíz del repositorio, igual que hace GitHub Actions. Python sitúa
# `herramientas/` en sys.path en ese modo, no la raíz que contiene ddd_core/.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ddd_core.config import load_params_yaml

TARGET_MET = "TARGET_MET"
TARGET_IMPROVED_NOT_MET = "TARGET_IMPROVED_NOT_MET"
TARGET_NOT_MET = "TARGET_NOT_MET"
HARD_BLOCK = "HARD_BLOCK"
GEOMETRIC_PASS = {"PASS", "PASS_WITH_EXCEPTIONS"}
CAUSAL_TYPES = {"ATOMIC_MULTIPART", "GOVERNED_BRIDGE"}
POPULATION_REPAIR = "POPULATION_REPAIR"
SWAP_POLISH = "SWAP_POLISH"
BASE_M05 = "BASE_M05"


def _m05_report_path(params: Path, run_id: str | None = None) -> Path:
    cfg = load_params_yaml(str(params))
    s5 = (cfg.get("modulos", {}) or {}).get("modulo_05_optimizar_distritos") or cfg.get("step5_optimize_swaps") or {}
    value = s5.get("out_report")
    if not value:
        raise ValueError("M05 no declara out_report")
    meta = cfg.get("meta") or {}
    return Path(str(value).format(
        year=meta.get("year"),
        run_name=meta.get("run_name"),
        run_id=run_id or "",
    ))


def _objective_pair(container: dict, *, before_key: str, after_key: str, indexes: tuple[int, int, int]):
    before = container.get(before_key)
    after = container.get(after_key)
    needed = max(indexes) + 1
    if not isinstance(before, (list, tuple)) or not isinstance(after, (list, tuple)):
        return None
    if len(before) < needed or len(after) < needed:
        return None
    try:
        values_before = [float(before[i]) for i in indexes]
        values_after = [float(after[i]) for i in indexes]
    except (TypeError, ValueError, OverflowError):
        return None
    if not all(math.isfinite(v) and v >= 0 for v in values_before + values_after):
        return None
    hard_before, outliers_before, max_before = values_before
    hard_after, outliers_after, max_after = values_after
    if any(not float(v).is_integer() for v in (hard_before, outliers_before, hard_after, outliers_after)):
        return None
    return {
        "hard_before": int(hard_before),
        "outliers_before": int(outliers_before),
        "max_before": float(max_before),
        "hard_after": int(hard_after),
        "outliers_after": int(outliers_after),
        "max_after": float(max_after),
    }


def _repair_result(repair) -> str:
    if not isinstance(repair, dict):
        return "NOT_APPLICABLE"
    if not bool(repair.get("enabled", False)):
        return "DISABLED"
    return str(repair.get("result") or "UNKNOWN")


def _population_failure(*, status: str, path: str | None, error: str | None) -> dict:
    return {
        "population_outcome": "failure",
        "population_decision": HARD_BLOCK,
        "population_evidence_source": None,
        "population_evidence_status": status,
        "population_evidence_path": path,
        "population_evidence_error": error,
        "population_repair_result": "NOT_VERIFIABLE",
        "population_outliers_before": None,
        "population_outliers_after": None,
        "population_max_deviation_before": None,
        "population_max_deviation_after": None,
        "population_termination_reason": None,
        "population_baseline_restored": False,
        "population_hard_constraints_before": None,
        "population_hard_constraints_after": None,
    }


def population_dimension(m05_report: dict) -> dict:
    """Normaliza evidencia poblacional M05 sin modificar ni reinterpretar el algoritmo."""
    repair = m05_report.get("population_repair")
    repair_result = _repair_result(repair)
    selected = None
    source = None

    if isinstance(repair, dict) and bool(repair.get("enabled", False)):
        selected = _objective_pair(
            repair,
            before_key="objective_before",
            after_key="objective_after",
            indexes=(0, 1, 2),
        )
        if selected is not None:
            source = POPULATION_REPAIR

    if selected is None:
        swap = m05_report.get("swap_polish")
        if isinstance(swap, dict):
            selected = _objective_pair(
                swap,
                before_key="objective_start",
                after_key="objective_final",
                indexes=(0, 2, 3),
            )
            if selected is not None:
                source = SWAP_POLISH

    if selected is None:
        selected = _objective_pair(
            m05_report,
            before_key="objective_start",
            after_key="objective_final",
            indexes=(0, 2, 3),
        )
        if selected is not None:
            source = BASE_M05

    if selected is None:
        return _population_failure(status="INVALID_CONTENT", path=None, error="M05 no contiene objetivos poblacionales verificables") | {
            "population_repair_result": repair_result,
        }

    hard_before = selected["hard_before"]
    outliers_before = selected["outliers_before"]
    max_before = selected["max_before"]
    hard_after = selected["hard_after"]
    outliers_after = selected["outliers_after"]
    max_after = selected["max_after"]

    if hard_after != 0:
        decision = HARD_BLOCK
    elif outliers_after == 0:
        decision = TARGET_MET
    elif outliers_after < outliers_before or max_after < max_before:
        decision = TARGET_IMPROVED_NOT_MET
    else:
        decision = TARGET_NOT_MET

    return {
        "population_outcome": "success",
        "population_decision": decision,
        "population_evidence_source": source,
        "population_evidence_status": "VALID",
        "population_evidence_path": None,
        "population_evidence_error": None,
        "population_repair_result": repair_result,
        "population_outliers_before": outliers_before,
        "population_outliers_after": outliers_after,
        "population_max_deviation_before": max_before,
        "population_max_deviation_after": max_after,
        "population_termination_reason": repair.get("termination_reason") if source == POPULATION_REPAIR and isinstance(repair, dict) else None,
        "population_baseline_restored": bool(repair.get("baseline_restored", False)) if source == POPULATION_REPAIR and isinstance(repair, dict) else False,
        "population_hard_constraints_before": hard_before,
        "population_hard_constraints_after": hard_after,
    }


def _load_population_evidence(params: Path, run_id: str) -> dict:
    try:
        report_path = _m05_report_path(params, run_id)
    except Exception as exc:
        return _population_failure(status="UNDECLARED", path=None, error=f"{type(exc).__name__}: {exc}")

    path_text = report_path.as_posix()
    try:
        raw = report_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        return _population_failure(status="MISSING", path=path_text, error=f"{type(exc).__name__}: {exc}")
    except OSError as exc:
        return _population_failure(status="UNREADABLE", path=path_text, error=f"{type(exc).__name__}: {exc}")

    try:
        report = json.loads(raw)
    except json.JSONDecodeError as exc:
        return _population_failure(status="INVALID_JSON", path=path_text, error=f"{type(exc).__name__}: {exc}")
    if not isinstance(report, dict):
        return _population_failure(status="INVALID_CONTENT", path=path_text, error="M05 debe ser un objeto JSON")

    result = population_dimension(report)
    result["population_evidence_path"] = path_text
    if result["population_outcome"] == "success":
        result["population_evidence_status"] = "VALID"
        result["population_evidence_error"] = None
    elif not result.get("population_evidence_error"):
        result["population_evidence_error"] = "M05 no contiene objetivos poblacionales verificables"
    return result


def geometric_exceptions_causally_governed(audit: dict) -> bool:
    if audit.get("decision") == "PASS":
        return not audit.get("blocked_districts") and not audit.get("policy_mismatches") and not audit.get("contract_blockers")
    if audit.get("decision") != "PASS_WITH_EXCEPTIONS":
        return False
    if audit.get("blocked_districts") or audit.get("policy_mismatches") or audit.get("contract_blockers"):
        return False
    districts = audit.get("districts")
    if not isinstance(districts, list):
        return False
    exception_rows = [row for row in districts if row.get("decision") == "PASS_WITH_EXCEPTIONS"]
    if int(audit.get("governed_exceptions", -1)) != len(exception_rows):
        return False
    for row in exception_rows:
        causes = row.get("causal_exceptions")
        if not isinstance(causes, list) or not causes or row.get("unexplained_components") not in ([], None):
            return False
        for cause in causes:
            if cause.get("type") not in CAUSAL_TYPES:
                return False
            if not cause.get("components") or len(cause.get("components") or []) < 2:
                return False
            if cause.get("type") == "ATOMIC_MULTIPART":
                if not cause.get("sections"):
                    return False
            elif len(cause.get("endpoints") or []) != 2 or not cause.get("contract_sha256") or not cause.get("source"):
                return False
    return True


def certification_gate(*, execution_outcome: str, population: dict, geometric_outcome: str, geometric_decision: str, geometric_audit: dict) -> tuple[str, str | None]:
    if execution_outcome != "success":
        return "BLOCK", "EXECUTION_FAILED"
    if population.get("population_outcome") != "success":
        evidence_status = population.get("population_evidence_status")
        if evidence_status == "MISSING":
            return "BLOCK", "M05_POPULATION_EVIDENCE_MISSING"
        if evidence_status == "UNDECLARED":
            return "BLOCK", "M05_POPULATION_EVIDENCE_UNDECLARED"
        return "BLOCK", "M05_POPULATION_EVIDENCE_INVALID"
    if population.get("population_decision") == HARD_BLOCK:
        return "BLOCK", "POPULATION_HARD_BLOCK"
    if population.get("population_decision") != TARGET_MET:
        return "BLOCK", "POPULATION_TARGET_NOT_MET"
    if population.get("population_hard_constraints_after") != 0 or population.get("population_outliers_after") != 0:
        return "BLOCK", "POPULATION_TARGET_NOT_MET"
    if geometric_outcome != "success" or geometric_decision not in GEOMETRIC_PASS:
        return "BLOCK", "GEOMETRIC_BLOCK"
    if geometric_decision == "PASS_WITH_EXCEPTIONS" and not geometric_exceptions_causally_governed(geometric_audit):
        return "BLOCK", "GEOMETRIC_EXCEPTION_NOT_PROVEN"
    return geometric_decision, None


def build_production_status(*, territory_id: str, params: str, run_id: str, from_stage: str, to_stage: str, execution_outcome: str, geometric_outcome: str, geometric_decision: str, m05_report: dict | None, geometric_audit: dict, population_evidence: dict | None = None) -> dict:
    population = population_evidence if population_evidence is not None else population_dimension(m05_report or {})
    decision, block_cause = certification_gate(
        execution_outcome=execution_outcome,
        population=population,
        geometric_outcome=geometric_outcome,
        geometric_decision=geometric_decision,
        geometric_audit=geometric_audit,
    )
    payload = {
        "schema": "ddd.production-status/1.2",
        "decision": decision,
        "territory_id": territory_id,
        "params": params,
        "run_id": run_id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "execution_outcome": execution_outcome,
        "geometric_outcome": geometric_outcome,
        "geometric_decision": geometric_decision,
        **population,
        "scope_through_stage": "M06",
    }
    if block_cause:
        payload["block_cause"] = block_cause
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _block_causes(payload: dict) -> dict:
    return {
        "schema": "ddd.production-block-causes/1.0",
        "decision": payload.get("decision"),
        "block_cause": payload.get("block_cause"),
        "population_evidence_status": payload.get("population_evidence_status"),
        "population_evidence_path": payload.get("population_evidence_path"),
        "population_evidence_error": payload.get("population_evidence_error"),
        "population_decision": payload.get("population_decision"),
        "geometric_decision": payload.get("geometric_decision"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--territory-id", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--from-stage", required=True)
    parser.add_argument("--to-stage", required=True)
    parser.add_argument("--execution-outcome", default="success")
    parser.add_argument("--geometric-outcome", required=True)
    parser.add_argument("--geometric-decision", required=True)
    parser.add_argument("--geometric-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    geometric_audit = json.loads(args.geometric_audit.read_text(encoding="utf-8"))
    if not isinstance(geometric_audit, dict):
        raise ValueError("La auditoría geométrica no es un objeto JSON")

    population = _load_population_evidence(args.params, args.run_id)
    payload = build_production_status(
        territory_id=args.territory_id,
        params=str(args.params),
        run_id=args.run_id,
        from_stage=args.from_stage,
        to_stage=args.to_stage,
        execution_outcome=args.execution_outcome,
        geometric_outcome=args.geometric_outcome,
        geometric_decision=args.geometric_decision,
        m05_report=None,
        geometric_audit=geometric_audit,
        population_evidence=population,
    )
    _write_json(args.output, payload)
    _write_json(args.output.parent / "block_causes.json", _block_causes(payload))
    print(payload["decision"])
    if payload.get("block_cause"):
        print(payload["block_cause"])


if __name__ == "__main__":
    main()
