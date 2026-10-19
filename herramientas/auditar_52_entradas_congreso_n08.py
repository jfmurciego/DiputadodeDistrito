"""Read-only full 52-origin-unit N08 audit against the immutable manifesto trust anchor.

This is a national *input check*, NOT district production, administrative source
accreditation, geometry remediation or a proof of feasible 407 districts.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ddd_core.congreso_contract import CONGRESS_CODES
from ddd_core.congreso_readiness import provincial_preflight, national_readiness, execution_authorization

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
PRODUCT = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
EXPECTED = {
    "07": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
    "09": "PHYSICAL_COMPONENTS_EXCEED_K",
    "17": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
    "34": "PHYSICAL_COMPONENTS_EXCEED_K",
    "36": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
}

def collect():
    contract = json.loads(CONTRACT.read_bytes())
    if contract["accreditation"]["generation_authorized"] is not False:
        raise ValueError("NATIONAL_PRODUCTION_MUST_REMAIN_DISABLED")
    national = national_readiness(contract)
    if national["generation_authorized"] is not False:
        raise ValueError("NATIONAL_READINESS_MUST_NOT_AUTHORIZE_PRODUCTION")
    provincial = []
    for code in CONGRESS_CODES:
        item = provincial_preflight(contract, PRODUCT, code)
        execution = execution_authorization(item, national)
        if (item["input_status"] != "PASS_INPUTS_ONLY" or
            item["generation_authorized"] is not False or
            item["structural_feasibility_proven"] is not False or
            execution["status"] != "DENIED" or
            execution["districts_generated"] != 0):
            raise ValueError("N08_PROVINCIAL_GATE_UNEXPECTED:" + code)
        if code in EXPECTED and (
            item["structural_necessary_condition"] or
            item["structural_necessary_reason"] != EXPECTED[code]):
            raise ValueError("N08_DISCONTINUITY_REGRESSION:" + code)
        provincial.append({
            "CPRO": code,
            "sections": item["sections"],
            "population": item["population"],
            "quota_K": item["k"],
            "edges": item["edges"],
            "input_status": item["input_status"],
            "structural_necessary_condition": item["structural_necessary_condition"],
            "structural_necessary_reason": item["structural_necessary_reason"],
            "territorial_cautions": item["territorial_cautions"],
            "generation_authorized": False,
            "production_districts_generated": 0,
        })
    if len(provincial) != 52 or len({r["CPRO"] for r in provincial}) != 52:
        raise ValueError("NATIONAL_52_UNITS_NOT_COMPLETE")
    if sum(x["sections"] for x in provincial) != 36554:
        raise ValueError("NATIONAL_CUSEC_SUM_WRONG")
    if sum(x["population"] for x in provincial) != 49128297:
        raise ValueError("NATIONAL_POPULATION_SUM_WRONG")
    if sum(x["quota_K"] for x in provincial) != 407:
        raise ValueError("NATIONAL_K_SUM_WRONG")
    return {
        "schema": "ddd.n08.52-cpro-input-audit/1.0",
        "source": "N08 original INE 2025 hash-pinned input product",
        "source_contract": str(CONTRACT.relative_to(ROOT)),
        "original_n08_manifest": str((PRODUCT / "manifest.json").relative_to(ROOT)),
        "checks": {
            "origin_units_checked": 52,
            "sections_2025": 36554,
            "population_2025": 49128297,
            "approved_k_total": 407,
            "input_checks_passed": 52,
            "strict_connected_population_impossibility_count":
                sum(not x["structural_necessary_condition"] for x in provincial),
            "known_strict_impossibilities": sorted(EXPECTED),
            "all_production_execution_denied": True,
            "administrative_boundaries_2025_crossvalidated": False,
            "individual_exceptions_approved": False,
            "district_partitions_generated": 0,
            "full_national_feasibility_proven": False,
        },
        "provinces": provincial,
        "generation_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Hash-pinned N08 52/52 input diagnostic, NEVER production")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = collect()
    if args.output is not None:
        if args.output.exists():
            raise FileExistsError("52_AUDIT_OUTPUT_ALREADY_EXISTS")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as file:
            json.dump(report, file, ensure_ascii=False, sort_keys=True, indent=2)
            file.write("\n")
    print("DDD_N08_52_INPUT_AUDIT " + json.dumps(report["checks"], sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
