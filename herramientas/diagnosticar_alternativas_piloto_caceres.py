#!/usr/bin/env python3
"""Run a finite, deterministic alternate-tree diagnostic for Cáceres.

This is an analytical search only. It preserves the N08 contract and never
certifies or authorizes a territorial product.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from ddd_core.congreso_bounded_tree_search import search_tree_partition
from ddd_core.congreso_pilot_adapter import consolidate_avoidable_splits, groups, split_inventory
from herramientas.diagnosticar_factibilidad_congreso_k_multiple import _node_ordering
from herramientas.generar_piloto_congreso_leon import (
    MAX_STATES, MAX_TRANSITIONS, ORDERS, _load_bound_inputs, produce,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diagnose(root: Path, candidate_output: Path, report_output: Path) -> dict:
    unit, contract, bound, units, graph, k, population, floor, cap = _load_bound_inputs(root, "10")
    ids = sorted(units)
    weights = {u: units[u]["population"] for u in ids}
    orders = []
    total_states = total_transitions = 0
    for order in ORDERS:
        result = search_tree_partition(
            ids, graph, weights, k=k, floor=floor, cap=cap,
            node_order=_node_ordering(order, ids, graph, weights),
            max_states=MAX_STATES, max_transitions=MAX_TRANSITIONS,
            return_groups=True,
        )
        total_states += result.explored_states
        total_transitions += result.explored_transitions
        row = {
            "order": order, "status": result.status,
            "states": result.explored_states, "transitions": result.explored_transitions,
            "input_sha256": result.input_sha256, "witness_sha256": result.witness_sha256,
        }
        if result.status == "TREE_WITNESS_FOUND_CONDITIONAL":
            state = {u: f"CPRO10-{index:02d}" for index, members in enumerate(result.groups, 1)
                     for u in members}
            repair = consolidate_avoidable_splits(
                state, units, graph, floor=floor, cap=cap, max_trials=30000,
            )
            final_state = repair["state"]
            district_populations = {
                district: sum(units[u]["population"] for u in members)
                for district, members in groups(final_state).items()
            }
            row.update({
                "post_repair_split_cumun": [x["CUMUN"] for x in split_inventory(final_state, units)],
                "post_repair_split_count": len(split_inventory(final_state, units)),
                "post_repair_district_populations": dict(sorted(district_populations.items())),
                "repair_trials": repair["trials"], "repair_moves": repair["moves"],
                "repair_validation_valid": repair["validation"].get("valid") is True,
            })
        orders.append(row)

    candidate_output.parent.mkdir(parents=True, exist_ok=True)
    selected = produce(root, candidate_output, cpro="10", repair=True, order="degree_asc")
    candidate = selected["candidate"]
    report = {
        "schema": "ddd.caceres.n08.alternate-tree-search/1.0",
        "scope": "Bounded analytical search; no global optimality or infeasibility claim",
        "source_binding": bound["input_sha256"],
        "cpro": "10", "sections": len(units), "population": population,
        "k": k, "floor": floor, "cap": cap,
        "search": {
            "orders": list(ORDERS), "per_order_max_states": MAX_STATES,
            "per_order_max_transitions": MAX_TRANSITIONS,
            "repair_max_trials_per_witness": 30000,
            "total_states": total_states, "total_transitions": total_transitions,
            "zero_split_witness_found": any(
                row.get("post_repair_split_count") == 0 for row in orders
            ),
            "results": orders,
        },
        "candidate_for_physical_review": {
            "order": candidate["selected_order"],
            "candidate_sha256": _sha(candidate_output),
            "assignment_witness_sha256": candidate["witness_sha256"],
            "municipalities_split": candidate["municipalities_split"],
            "municipal_policy_certified": candidate["municipal_policy_certified"],
            "generation_authorized": candidate["generation_authorized"],
            "product_certification": candidate["product_certification"],
        },
        "global_minimality_proven": False,
        "generation_authorized": False,
        "product_certification": "NOT_PERFORMED",
    }
    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                             encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--candidate-output", type=Path, required=True)
    parser.add_argument("--report-output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.root, args.candidate_output, args.report_output)
    print(json.dumps({
        "orders": len(result["search"]["results"]),
        "conditional_witnesses": sum(x["status"] == "TREE_WITNESS_FOUND_CONDITIONAL"
                                      for x in result["search"]["results"]),
        "zero_split_witness_found": result["search"]["zero_split_witness_found"],
        "candidate_sha256": result["candidate_for_physical_review"]["candidate_sha256"],
        "generation_authorized": result["generation_authorized"],
        "product_certification": result["product_certification"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
