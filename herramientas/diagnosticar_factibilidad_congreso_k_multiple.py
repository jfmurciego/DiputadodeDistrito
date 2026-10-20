#!/usr/bin/env python3
"""Bounded Congress K>1 search over already-bound N08 inputs; never emits a partition.

Version: 1.2.0 (bounded alternative spanning-forest orders; 2026-10-20)
This tool does not invoke M04-M06, write assignments, certify products or open
production gates. A graph witness, if found, is conditional on CUSEC graph
semantics and does not resolve municipal policy, multipart topology, CNIG
boundary accreditation or named exceptions.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ddd_core.congreso_constructive_witness import evaluate_unit
from ddd_core.congreso_exact_feasibility import solve_bounded_connected_partition
from ddd_core.congreso_bounded_tree_search import search_tree_partition

FOREST_ORDERINGS = frozenset({
    "cusec", "degree_desc", "population_desc", "hash_order", "degree_asc",
    "population_asc", "degree_pop_asc", "degree_pop_desc", "hash_seed_1",
    "hash_seed_2",
})


def _node_ordering(name: str, nodes: Sequence[str], adjacency, weights) -> list[str]:
    degree = {node: len(adjacency[node]) for node in nodes}
    keys = {
        "cusec": lambda node: (node,),
        "degree_desc": lambda node: (-degree[node], node),
        "population_desc": lambda node: (-weights[node], node),
        "hash_order": lambda node: (hashlib.sha256(node.encode()).hexdigest(), node),
        "degree_asc": lambda node: (degree[node], node),
        "population_asc": lambda node: (weights[node], node),
        "degree_pop_asc": lambda node: (degree[node], weights[node], node),
        "degree_pop_desc": lambda node: (-degree[node], -weights[node], node),
        "hash_seed_1": lambda node: (hashlib.sha256(("nac1" + node).encode()).hexdigest(), node),
        "hash_seed_2": lambda node: (hashlib.sha256(("nac2" + node).encode()).hexdigest(), node),
    }
    if name not in keys:
        raise ValueError("UNKNOWN_FOREST_ORDERING:" + name)
    return sorted(nodes, key=keys[name])


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def diagnose_graph(
    nodes: Sequence[str], adjacency: Mapping[str, Sequence[str] | set[str]],
    weights: Mapping[str, int], *, k: int, floor: int, cap: int,
    physical_part_components: int, max_extra_groups: int = 512,
    max_states: int = 1, tree_max_states: int = 12_000,
    tree_max_transitions: int = 100_000,
    forest_orderings: Sequence[str] = ("cusec",),
) -> dict:
    """Probe a bounded exact search, returning status and digest only.

    Search group budget includes initial singleton vertices. The graph is the
    CUSEC section graph; part-component count above K is a conditional
    necessary-condition failure. Group assignments are never returned.
    """
    for name, value in (("k", k), ("floor", floor), ("cap", cap),
                        ("physical_part_components", physical_part_components),
                        ("max_extra_groups", max_extra_groups), ("max_states", max_states),
                        ("tree_max_states", tree_max_states),
                        ("tree_max_transitions", tree_max_transitions)):
        if type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    if (physical_part_components < 1 or max_extra_groups < 1 or max_states < 1
            or tree_max_states < 1 or tree_max_transitions < 1):
        raise ValueError("invalid component count or budget")
    if k <= 1:
        raise ValueError("K_MULTIPLE_REQUIRED")
    if (not forest_orderings or any(not isinstance(name, str) for name in forest_orderings)
            or len(set(forest_orderings)) != len(forest_orderings)
            or any(name not in FOREST_ORDERINGS for name in forest_orderings)):
        raise ValueError("FOREST_ORDERINGS_INVALID")
    if physical_part_components > k:
        return {
            "status": "NECESSARY_CONDITION_FAILED_CONDITIONAL",
            "condition": "PHYSICAL_PART_COMPONENTS_EXCEED_K",
            "input_sha256": None,
            "enumerated_groups": 0,
            "explored_states": 0,
            "search_exhaustive": False,
            "partition_emitted": False,
        }
    result = solve_bounded_connected_partition(
        nodes, adjacency, weights, k=k, floor=floor, cap=cap,
        max_groups=len(nodes) + max_extra_groups, max_states=max_states,
    )
    tree_result = None
    tree_attempts = []
    # Independently validate any in-memory witness, then discard its labels.
    witness_sha256 = None
    if result.status == "SOLUTION_FOUND":
        groups = [set(group) for group in result.groups]
        covered = [node for group in groups for node in group]
        if (len(groups) != k or len(covered) != len(nodes) or set(covered) != set(nodes)
                or any(not floor <= sum(weights[node] for node in group) <= cap for group in groups)):
            raise ValueError("WITNESS_PARTITION_INVARIANT_FAILED")
        for group in groups:
            reached = set()
            if group:
                stack = [next(iter(group))]
                while stack:
                    node = stack.pop()
                    if node in reached:
                        continue
                    reached.add(node)
                    stack.extend((set(adjacency[node]) & group) - reached)
            if reached != group:
                raise ValueError("WITNESS_CONNECTIVITY_INVARIANT_FAILED")
        canonical = json.dumps(sorted(sorted(group) for group in groups), separators=(",", ":")).encode()
        witness_sha256 = hashlib.sha256(canonical).hexdigest()
    if result.status == "SEARCH_EXHAUSTED":
        for ordering in forest_orderings:
            node_order = _node_ordering(ordering, nodes, adjacency, weights)
            attempt = search_tree_partition(
                nodes, adjacency, weights, k=k, floor=floor, cap=cap,
                node_order=node_order, max_states=tree_max_states,
                max_transitions=tree_max_transitions,
            )
            tree_attempts.append({
                "ordering": ordering,
                "node_order_sha256": hashlib.sha256(
                    json.dumps(node_order, separators=(",", ":")).encode()
                ).hexdigest(),
                "status": attempt.status,
                "input_sha256": attempt.input_sha256,
                "witness_sha256": attempt.witness_sha256,
                "explored_states": attempt.explored_states,
                "explored_transitions": attempt.explored_transitions,
                "spanning_forest_components": attempt.spanning_forest_components,
                "proof": attempt.proof,
            })
            if attempt.status == "TREE_WITNESS_FOUND_CONDITIONAL":
                tree_result = attempt
                break
            if tree_result is None:
                tree_result = attempt
    if result.status == "SOLUTION_FOUND":
        status = "SECTION_GRAPH_WITNESS_CONDITIONAL"
    elif tree_result and tree_result.status == "TREE_WITNESS_FOUND_CONDITIONAL":
        status = "TREE_WITNESS_FOUND_CONDITIONAL"
        witness_sha256 = tree_result.witness_sha256
    elif tree_result and tree_result.status == "PROVEN_INFEASIBLE":
        status = "NECESSARY_CONDITION_FAILED_CONDITIONAL"
    else:
        status = result.status
    return {
        "status": status,
        "solver_status": result.status,
        "proof": result.proof,
        "input_sha256": result.input_sha256,
        "witness_sha256": witness_sha256,
        "enumerated_groups": result.explored_groups,
        "explored_states": result.explored_states,
        "search_exhaustive": bool(result.certificate and result.certificate.get("search_exhaustive")),
        "tree_search": ({
            "status": tree_result.status,
            "input_sha256": tree_result.input_sha256,
            "witness_sha256": tree_result.witness_sha256,
            "explored_states": tree_result.explored_states,
            "explored_transitions": tree_result.explored_transitions,
            "spanning_forest_components": tree_result.spanning_forest_components,
            "proof": tree_result.proof,
        } if tree_result else None),
        "tree_search_attempts": tree_attempts,
        "partition_emitted": False,
    }


def run_batch(preflight_root: Path, product_root: Path, contract_path: Path,
              *, max_extra_groups: int = 512, max_states: int = 1,
              tree_max_states: int = 12_000,
              tree_max_transitions: int = 100_000,
              forest_orderings: Sequence[str] = ("cusec",)) -> dict:
    manifest_path = product_root / "manifest.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    quotas = {r["code"]: r["k"] for r in contract["quotas_by_origin_unit"]}
    rows = []
    for number in range(1, 53):
        cpro = f"{number:02d}"
        k = quotas[cpro]
        if k <= 1:
            continue
        preflight_dir = preflight_root / f"PREFLIGHT_CPRO{cpro}"
        preflight_path = preflight_dir / "PREFLIGHT.json"
        checkpoint_path = preflight_dir / "CHECKPOINT.json"
        unit_path = product_root / "unidades" / f"{cpro}.json.gz"
        bound = evaluate_unit(
            preflight_path=preflight_path, checkpoint_path=checkpoint_path,
            unit_path=unit_path, product_manifest_path=manifest_path,
            contract_path=contract_path,
        )
        input_hashes = bound["input_sha256"]
        with gzip.open(unit_path, "rt", encoding="utf-8") as stream:
            unit = json.load(stream)
        nodes = unit["nodes"]
        ids = [node["CUSEC"] for node in nodes]
        weights = {node["CUSEC"]: node["POB_2025"] for node in nodes}
        population = sum(weights.values())
        floor = (17 * population + 20 * k - 1) // (20 * k)
        cap = (23 * population) // (20 * k)
        adjacency = {node: set() for node in ids}
        for edge in unit["edges"]:
            if (edge.get("kind") == "linear" and edge.get("edge_type") == "geometric"
                    and isinstance(edge.get("shared_border_m"), (int, float))
                    and not isinstance(edge.get("shared_border_m"), bool)
                    and math.isfinite(edge["shared_border_m"]) and edge["shared_border_m"] > 0):
                adjacency[edge["u"]].add(edge["v"])
                adjacency[edge["v"]].add(edge["u"])
        topology_summary = unit["summary"]
        if bound["errors"]:
            outcome = {"status": "INPUT_VALIDATION_BLOCKED", "errors": bound["errors"],
                       "partition_emitted": False}
        else:
            outcome = diagnose_graph(
                ids, adjacency, weights, k=k, floor=floor, cap=cap,
                physical_part_components=topology_summary["physical_part_components"],
                max_extra_groups=max_extra_groups, max_states=max_states,
                tree_max_states=tree_max_states,
                tree_max_transitions=tree_max_transitions,
                forest_orderings=forest_orderings,
            )
        rows.append({
            "CPRO": cpro, "K": k, "sections": len(ids), "population": population,
            "floor": floor, "cap": cap, "section_edges": len(unit["edges"]),
            "section_graph_components": topology_summary["section_graph_components"],
            "physical_part_components": topology_summary["physical_part_components"],
            "multipart_sections_spanning_physical_components": len(
                topology_summary["multipart_sections_spanning_physical_components"]),
            "preflight_sha256": input_hashes["preflight"],
            "checkpoint_sha256": input_hashes["checkpoint"],
            "topology_sha256": input_hashes["unit_product"],
            "contract_sha256": input_hashes["contract"],
            **outcome,
            "territorial_factibility": "INSUFFICIENT_EVIDENCE",
            "external_boundary_accredited": False,
            "generation_authorized": False,
            "product_certification": "NOT_PERFORMED",
        })
    return {
        "schema": "ddd.congress-k-multiple-bounded-search/1.2",
        "method": "existing bounded exact connected-partition solver plus bounded deterministic spanning-forest DP over declared vertex orderings; CUSEC section graph",
        "budget": {"extra_connected_groups": max_extra_groups, "exact_cover_states": max_states,
                   "tree_dp_states_per_unit": tree_max_states,
                   "tree_dp_transitions_per_unit": tree_max_transitions,
                   "forest_orderings": list(forest_orderings)},
        "cases": len(rows), "results": rows,
        "partition_emitted": False, "districts_generated": 0,
        "generation_authorized": False, "product_certification": "NOT_PERFORMED",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight-root", type=Path, required=True)
    parser.add_argument("--product-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--max-extra-groups", type=int, default=512)
    parser.add_argument("--max-states", type=int, default=1)
    parser.add_argument("--tree-max-states", type=int, default=12_000)
    parser.add_argument("--tree-max-transitions", type=int, default=100_000)
    parser.add_argument("--forest-orderings", default="cusec",
                        help="comma-separated deterministic orders: " + ",".join(sorted(FOREST_ORDERINGS)))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_batch(args.preflight_root, args.product_root, args.contract,
                       max_extra_groups=args.max_extra_groups, max_states=args.max_states,
                       tree_max_states=args.tree_max_states,
                       tree_max_transitions=args.tree_max_transitions,
                       forest_orderings=tuple(args.forest_orderings.split(",")))
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
