from __future__ import annotations

import json
from pathlib import Path
from typing import Any


OBJECTIVES = (
    "population_max_deviation",
    "shape_penalty",
    "comarca_penalty",
    "corridor_count",
    "assignment_delta",
)


def _objective(report: dict[str, Any]) -> dict[str, float]:
    metrics = report["metrics"]
    return {
        "population_max_deviation": float(metrics["population"]["max_deviation"]),
        "shape_penalty": 1.0 - float(metrics["shape"]["polsby_popper_median"]),
        "comarca_penalty": 1.0 - float(metrics["comarca"]["retention_ratio"]),
        "corridor_count": float(len(metrics["shape"].get("corridor_alerts", []))),
        "assignment_delta": float(metrics.get("stability", {}).get("assignment_delta", 0.0)),
    }


def _dominates(left: dict[str, float], right: dict[str, float]) -> bool:
    return all(left[key] <= right[key] for key in OBJECTIVES) and any(
        left[key] < right[key] for key in OBJECTIVES
    )


def _find_reports(results_dir: str) -> dict[str, tuple[dict[str, Any], Path]]:
    reports: dict[str, tuple[dict[str, Any], Path]] = {}
    for path in sorted(Path(results_dir).rglob("report.json")):
        report = json.loads(path.read_text(encoding="utf-8"))
        candidate_id = report.get("candidate_id")
        if not candidate_id:
            raise ValueError(f"Informe sin candidate_id: {path}")
        if candidate_id in reports:
            raise ValueError(f"candidate_id duplicado: {candidate_id}")
        reports[candidate_id] = (report, path)
    return reports


def assemble(plan_path: str, results_dir: str, shortlist_size: int = 10) -> dict[str, Any]:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if plan.get("schema") != "ddd.ensemble-plan/1.0":
        raise ValueError("Plan de ensemble incompatible")
    expected = {item["candidate_id"]: item for item in plan["candidates"]}
    reports = _find_reports(results_dir)
    unknown = sorted(set(reports) - set(expected))
    if unknown:
        raise ValueError(f"Resultados no previstos: {', '.join(unknown)}")

    valid: list[dict[str, Any]] = []
    invalid: list[str] = []
    for candidate_id, (report, report_path) in reports.items():
        hard = report.get("hard_constraints", {})
        all_pass = hard is True or (isinstance(hard, dict) and hard.get("all_pass") is True)
        if not all_pass:
            invalid.append(candidate_id)
            continue
        objective = _objective(report)
        geojson_value = report.get("geojson")
        geojson_path = Path(geojson_value) if geojson_value else None
        if geojson_path is not None and not geojson_path.is_absolute():
            geojson_path = (report_path.parent / geojson_path).resolve()
        valid.append({
            "candidate_id": candidate_id,
            "profile": expected[candidate_id]["profile"],
            "seed": expected[candidate_id]["seed"],
            "parameters": expected[candidate_id]["parameters"],
            "metrics": report["metrics"],
            "fields": report.get("fields", {}),
            "objectives": objective,
            "report_path": str(report_path.resolve()),
            "geojson": str(geojson_path) if geojson_path is not None else None,
        })

    pareto_ids = {
        candidate["candidate_id"]
        for candidate in valid
        if not any(
            _dominates(other["objectives"], candidate["objectives"])
            for other in valid
            if other is not candidate
        )
    }

    def aggregate(candidate: dict[str, Any]) -> float:
        return sum(candidate["objectives"].values())

    shortlist: list[str] = []
    pool = [candidate for candidate in valid if candidate["candidate_id"] in pareto_ids] or valid
    for profile in plan["profiles"]:
        # La diversidad por familia es deliberada: si un perfil entero queda
        # dominado, conservamos su mejor representante para revisión de campo.
        options = [candidate for candidate in valid if candidate["profile"] == profile]
        if options:
            shortlist.append(min(options, key=aggregate)["candidate_id"])
    for candidate in sorted(pool, key=aggregate):
        if candidate["candidate_id"] not in shortlist:
            shortlist.append(candidate["candidate_id"])
        if len(shortlist) >= shortlist_size:
            break

    missing = sorted(set(expected) - set(reports))
    retry = sorted(set(missing) | set(invalid))
    retry_shards = []
    for shard in plan["shards"]:
        candidate_ids = [candidate_id for candidate_id in shard["candidate_ids"] if candidate_id in retry]
        if candidate_ids:
            retry_shards.append({**shard, "candidate_ids": candidate_ids})

    return {
        "schema": "ddd.ensemble-summary/1.0",
        "territory_id": plan["territory_id"],
        "prepared_bundle_id": plan["prepared_bundle_id"],
        "plan_sha256": plan["plan_sha256"],
        "candidate_count_expected": len(expected),
        "candidate_count_received": len(reports),
        "candidate_count_valid": len(valid),
        "complete": not retry,
        "missing_candidates": missing,
        "invalid_candidates": sorted(invalid),
        "retry_matrix": {"include": retry_shards},
        "pareto_candidates": sorted(pareto_ids),
        "shortlist": shortlist[:shortlist_size],
        "candidates": sorted(valid, key=lambda item: item["candidate_id"]),
        "selection_status": "PENDING_FIELD_REVIEW",
    }
