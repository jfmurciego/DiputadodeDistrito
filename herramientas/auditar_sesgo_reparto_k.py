#!/usr/bin/env python3
"""Mide el sesgo poblacional previo a M04 introducido por repartir K."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


VERSION = "1.0.0"


def audit_territory(record: dict) -> dict:
    provinces = record["provinces"]
    total_population = sum(int(v["population"]) for v in provinces.values())
    total_districts = sum(int(v["districts"]) for v in provinces.values())
    expected_k = int(record["k_districts"])
    if total_population <= 0:
        raise ValueError(f"{record['territory_id']}: población no positiva")
    if total_districts != expected_k:
        raise ValueError(
            f"{record['territory_id']}: reparto suma {total_districts}, K={expected_k}"
        )

    territory_mean = total_population / expected_k
    rows = []
    for province_code, values in sorted(provinces.items()):
        population = int(values["population"])
        districts = int(values["districts"])
        if population <= 0 or districts <= 0:
            raise ValueError(f"{record['territory_id']}/{province_code}: dato no positivo")
        exact_quota = population * expected_k / total_population
        provincial_mean = population / districts
        rows.append(
            {
                "province_code": str(province_code).zfill(2),
                "population": population,
                "districts": districts,
                "exact_quota": round(exact_quota, 9),
                "quota_error_districts": round(districts - exact_quota, 9),
                "representation_ratio": round(districts / exact_quota, 9),
                "population_load_ratio": round(provincial_mean / territory_mean, 9),
                "population_load_bias": round(provincial_mean / territory_mean - 1, 9),
            }
        )

    worst = max(rows, key=lambda row: abs(row["population_load_bias"]))
    return {
        "territory_id": record["territory_id"],
        "status": record["status"],
        "source": record["source"],
        "k_districts": expected_k,
        "total_population": total_population,
        "territory_mean_population_per_district": round(territory_mean, 9),
        "maximum_absolute_population_load_bias": abs(worst["population_load_bias"]),
        "worst_province_code": worst["province_code"],
        "provinces": rows,
    }


def build_report(payload: dict) -> dict:
    territories = [audit_territory(record) for record in payload["territories"]]
    return {
        "schema_version": "1.0.0",
        "tool_version": VERSION,
        "audit_finding": "C-04",
        "metric_definition": (
            "population_load_bias = (province_population / province_districts) "
            "/ (territory_population / K) - 1"
        ),
        "interpretation": (
            "negative means fewer residents per representative than the territorial mean; "
            "positive means more residents per representative"
        ),
        "territories": territories,
        "decision": "CLOSED_MEASURED_AND_PUBLISHED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    report = build_report(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
