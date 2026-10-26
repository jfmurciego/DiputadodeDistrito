#!/usr/bin/env python3
"""Produce four *analytical candidate* CUSEC district assignments for León.

Never modifies contracts, runs M04-M06, publishes a map or grants production
authorization. Output is a reproducible, source-bound pilot artifact only.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from ddd_core.congreso_constructive_witness import evaluate_unit
from ddd_core.congreso_bounded_tree_search import search_tree_partition
from herramientas.diagnosticar_factibilidad_congreso_k_multiple import _node_ordering

CPRO = "24"
K = 4
ORDERS = ("cusec", "degree_desc", "population_desc", "hash_order",
          "degree_asc", "population_asc", "degree_pop_asc",
          "degree_pop_desc", "hash_seed_1", "hash_seed_2")


def produce(root: Path, output: Path) -> dict:
    preflight = root / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013" / "PREFLIGHT_CPRO24"
    product = root / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
    contract = root / "territorios/congreso/contrato_congreso_2026.json"
    unit_path = product / "unidades/24.json.gz"
    bound = evaluate_unit(
        preflight_path=preflight / "PREFLIGHT.json",
        checkpoint_path=preflight / "CHECKPOINT.json",
        unit_path=unit_path,
        product_manifest_path=product / "manifest.json",
        contract_path=contract,
    )
    if bound["errors"]:
        raise ValueError("PREFLIGHT_BLOCKED: " + repr(bound["errors"]))
    config = json.loads(contract.read_text(encoding="utf-8"))
    if config["accreditation"]["generation_authorized"] is not False:
        raise ValueError("NATIONAL_GENERATION_GATE_CHANGED")
    quotas = {row["code"]: row["k"] for row in config["quotas_by_origin_unit"]}
    if quotas[CPRO] != K:
        raise ValueError("UNEXPECTED_LEON_QUOTA")
    with gzip.open(unit_path, "rt", encoding="utf-8") as stream:
        unit = json.load(stream)
    nodes = unit["nodes"]
    ids = [node["CUSEC"] for node in nodes]
    if len(set(ids)) != len(ids) or any(node["CPRO"] != CPRO for node in nodes):
        raise ValueError("CUSEC_COVERAGE_INVALID")
    weights = {node["CUSEC"]: node["POB_2025"] for node in nodes}
    municipalities = {node["CUSEC"]: node["CUMUN"] for node in nodes}
    adjacency = {node: set() for node in ids}
    for edge in unit["edges"]:
        if (edge.get("kind") == "linear" and edge.get("edge_type") == "geometric"
                and isinstance(edge.get("shared_border_m"), (int, float))
                and not isinstance(edge["shared_border_m"], bool)
                and edge["shared_border_m"] > 0):
            adjacency[edge["u"]].add(edge["v"])
            adjacency[edge["v"]].add(edge["u"])
    pop = sum(weights.values())
    floor = (17 * pop + 20 * K - 1) // (20 * K)
    cap = (23 * pop) // (20 * K)
    attempts = []
    for order in ORDERS:
        result = search_tree_partition(
            ids, adjacency, weights, k=K, floor=floor, cap=cap,
            node_order=_node_ordering(order, ids, adjacency, weights),
            max_states=5_000, max_transitions=30_000, return_groups=True,
        )
        attempts.append({"order": order, "status": result.status,
                         "input_sha256": result.input_sha256})
        if result.status != "TREE_WITNESS_FOUND_CONDITIONAL":
            continue
        groups = result.groups
        if len(groups) != K or sorted(n for g in groups for n in g) != sorted(ids):
            raise ValueError("INVALID_CANDIDATE_COVERAGE")
        assignment = {n: i for i, group in enumerate(groups, 1) for n in group}
        by_municipality = {}
        for node in ids:
            by_municipality.setdefault(municipalities[node], set()).add(assignment[node])
        split_municipalities = sorted(m for m, ds in by_municipality.items() if len(ds) > 1)
        districts = [
            {"id": f"LEON-{i:02d}", "population": sum(weights[n] for n in group),
             "cusecs": list(group)}
            for i, group in enumerate(groups, 1)
        ]
        report = {
            "schema": "ddd.congress-leon-analytical-candidate/1.0",
            "cpro": CPRO, "k": K, "population": pop,
            "floor": floor, "cap": cap, "districts": districts,
            "witness_sha256": result.witness_sha256,
            "input_sha256": result.input_sha256, "selected_order": order,
            "municipalities_split": split_municipalities,
            "municipal_policy_certified": False,
            "external_boundaries_accredited": False,
            "generation_authorized": False, "product_certification": "NOT_PERFORMED",
            "publication_authorized": False,
            "pilot_only": True, "attempts": attempts,
            "source_binding": bound["input_sha256"],
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
        return report
    raise RuntimeError("NO_CONDITIONAL_WITNESS_IN_DECLARED_ORDERS: " + repr(attempts))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = produce(args.root, args.output)
    print(json.dumps({"cpro": report["cpro"], "district_count": len(report["districts"]),
                      "populations": [row["population"] for row in report["districts"]],
                      "municipalities_split": len(report["municipalities_split"]),
                      "candidate_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      "certified": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
