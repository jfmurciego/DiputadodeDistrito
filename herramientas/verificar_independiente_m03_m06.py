#!/usr/bin/env python3
"""C-06 independent verifier: stdlib only, no producer or validator imports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, deque
from pathlib import Path


VERSION = "1.0.0"


def connected(nodes, adjacency):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    queue = deque(seen)
    while queue:
        node = queue.popleft()
        for neighbour in adjacency[node]:
            if neighbour in nodes and neighbour not in seen:
                seen.add(neighbour)
                queue.append(neighbour)
    return seen == nodes


def verify(root, spec):
    graph = json.loads((root / spec["graph"]).read_text(encoding="utf-8"))
    nodes = {str(row["id"]): int(row["pop"]) for row in graph["nodes"]}
    adjacency = {node: set() for node in nodes}
    for edge in graph["edges"]:
        left, right = str(edge["u"]), str(edge["v"])
        adjacency[left].add(right)
        adjacency[right].add(left)
    with (root / spec["composition"]).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    section_ids = [str(row["CUSEC_KEY"]) for row in rows]
    technical_failures = []
    if len(section_ids) != len(set(section_ids)):
        technical_failures.append("duplicate_sections")
    if set(section_ids) != set(nodes):
        technical_failures.append("section_universe_mismatch")
    pop_field = spec["population_field"]
    csv_population = {str(row["CUSEC_KEY"]): int(float(row[pop_field])) for row in rows}
    if csv_population != nodes:
        technical_failures.append("section_population_mismatch")

    districts = defaultdict(list)
    for row in rows:
        districts[int(row["district_id"])].append(row)
    if len(districts) != int(spec["expected_k"]):
        technical_failures.append("k_mismatch")
    total = sum(csv_population.values())
    if total != int(spec["expected_population"]):
        technical_failures.append("total_population_mismatch")
    target = total / int(spec["expected_k"])
    floor, cap = target * spec["floor_ratio"], target * spec["cap_ratio"]
    tolerance = target * spec["tolerance_ratio"]
    disconnected, province_crossings, hard, outside = [], [], [], []
    district_municipalities = {}
    for district, district_rows in sorted(districts.items()):
        ids = {str(row["CUSEC_KEY"]) for row in district_rows}
        population = sum(csv_population[node] for node in ids)
        provinces = {str(row["CPRO"]).zfill(2) for row in district_rows}
        district_municipalities[district] = {str(row["CUMUN"]) for row in district_rows}
        if not connected(ids, adjacency): disconnected.append(district)
        if len(provinces) != 1: province_crossings.append(district)
        if not floor <= population <= cap: hard.append(district)
        if abs(population - target) > tolerance + 1e-9: outside.append(district)

    municipality_rows = defaultdict(list)
    for row in rows: municipality_rows[str(row["CUMUN"])].append(row)
    atomicity_violations, mixed_violations = [], []
    atomicity_limit = target * spec["atomicity_ratio"]
    for municipality, items in municipality_rows.items():
        ids = {int(row["district_id"]) for row in items}
        population = sum(int(float(row[pop_field])) for row in items)
        if population <= atomicity_limit + 1e-9 and len(ids) > 1:
            atomicity_violations.append(municipality)
        mixed = sum(len(district_municipalities[district]) > 1 for district in ids)
        if len(ids) > 1 and mixed > 1:
            mixed_violations.append(municipality)
    technical_failures += [
        name for name, values in (
            ("disconnected_districts", disconnected),
            ("province_crossings", province_crossings),
            ("hard_population_violations", hard),
            ("municipality_atomicity_violations", atomicity_violations),
            ("municipality_mixed_district_violations", mixed_violations),
        ) if values
    ]
    decision = "BLOCKED_INDEPENDENT_VALIDATION" if technical_failures else "BLOCKED_TARGET_TOLERANCE" if outside else "PASS"
    verification_errors = [] if decision == spec["expected_decision"] else ["unexpected_decision"]
    return {"territory_id":spec["territory_id"],"decision":decision,"expected_decision":spec["expected_decision"],"sections":len(rows),"population":total,"districts":len(districts),"disconnected":disconnected,"province_crossings":province_crossings,"hard_population_violations":hard,"outside_target_tolerance":outside,"municipality_atomicity_violations":atomicity_violations,"municipality_mixed_district_violations":mixed_violations,"technical_failures":technical_failures,"verification_errors":verification_errors}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--config",type=Path,required=True);parser.add_argument("--output",type=Path,required=True);args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];payload=json.loads(args.config.read_text(encoding="utf-8"));results=[verify(root,spec) for spec in payload["territories"]]
    report={"schema_version":"1.0.0","tool_version":VERSION,"audit_finding":"C-06","independence":"stdlib_only_no_imports_from_modulos_ddd_core_or_existing_validator","territories":results,"decision":"PASS" if all(not row["verification_errors"] for row in results) else "FAIL"}
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps(report,ensure_ascii=False,indent=2))
    if report["decision"] != "PASS": raise SystemExit(1)


if __name__=="__main__": main()
