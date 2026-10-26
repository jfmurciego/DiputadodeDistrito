#!/usr/bin/env python3
"""Materialize source-bound analytical candidates for one Congress province.

Version: 1.1.0 (León audit-first repair and reusable province parameter; 2026-10-26)
Predecessor: legacy/nac_piloto_20261026/herramientas/generar_piloto_congreso_leon.py
Analytical only: does not run M04-M06, certify a product, authorize production,
or publish geometry. Existing candidates are audited before any repair.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from ddd_core.congreso_constructive_witness import evaluate_unit
from ddd_core.congreso_bounded_tree_search import search_tree_partition
from ddd_core.congreso_pilot_adapter import (
    assignment_witness_sha, audit_candidate, canonical_sha, consolidate_avoidable_splits, groups, model,
    split_inventory, state_from_candidate,
)
from herramientas.diagnosticar_factibilidad_congreso_k_multiple import _node_ordering

ORDERS = ("cusec", "degree_desc", "population_desc", "hash_order",
          "degree_asc", "population_asc", "degree_pop_asc",
          "degree_pop_desc", "hash_seed_1", "hash_seed_2")
MAX_STATES = 5_000
MAX_TRANSITIONS = 30_000
MAX_REPAIR_TRIALS = 30_000


def _reject_duplicate_pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("JSON_DUPLICATE_KEY:" + key)
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError("JSON_NONFINITE:" + value)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_pairs,
                      parse_constant=_reject_constant)


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                               allow_nan=False) + "\n", encoding="utf-8")


def _load_bound_inputs(root: Path, cpro: str):
    preflight = root / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013" / f"PREFLIGHT_CPRO{cpro}"
    product = root / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
    contract_path = root / "territorios/congreso/contrato_congreso_2026.json"
    unit_path = product / "unidades" / f"{cpro}.json.gz"
    bound = evaluate_unit(preflight_path=preflight / "PREFLIGHT.json",
                          checkpoint_path=preflight / "CHECKPOINT.json",
                          unit_path=unit_path,
                          product_manifest_path=product / "manifest.json",
                          contract_path=contract_path)
    if bound["errors"]:
        raise ValueError("PREFLIGHT_BLOCKED:" + repr(bound["errors"]))
    with gzip.open(unit_path, "rt", encoding="utf-8") as stream:
        unit = json.load(stream, object_pairs_hook=_reject_duplicate_pairs,
                         parse_constant=_reject_constant)
    contract = read_json(contract_path)
    units, graph, actual_cpro, k, population, floor, cap = model(unit, contract)
    if actual_cpro != cpro:
        raise ValueError("REQUESTED_CPRO_MISMATCH")
    if len(units) != bound["sections"] or population != bound["population"] or k != bound["k"]:
        raise ValueError("SOURCE_BOUND_MODEL_MISMATCH")
    return unit, contract, bound, units, graph, k, population, floor, cap


def _candidate_from_state(*, cpro, k, population, floor, cap, state, units,
                          bound, input_sha256, witness_sha256, selected_order,
                          attempts, predecessor_sha256=None, repair=None):
    districts = []
    for district, members in sorted(groups(state).items()):
        districts.append({"id": district,
                          "population": sum(units[u]["population"] for u in members),
                          "cusecs": sorted(members)})
    return {
        "schema": "ddd.congress-provincial-analytical-candidate/1.0",
        "cpro": cpro, "k": k, "population": population,
        "floor": floor, "cap": cap, "districts": districts,
        "input_sha256": input_sha256, "witness_sha256": assignment_witness_sha(state),
        "source_witness_sha256": witness_sha256,
        "selected_order": selected_order, "attempts": attempts,
        "source_binding": bound["input_sha256"],
        "predecessor_candidate_sha256": predecessor_sha256,
        "repair": repair,
        "municipalities_split": [x["CUMUN"] for x in split_inventory(state, units)],
        "municipal_policy_certified": False,
        "external_boundaries_accredited": False,
        "generation_authorized": False,
        "product_certification": "NOT_PERFORMED",
        "publication_authorized": False,
        "pilot_only": True,
    }


def produce(root: Path, output: Path, *, cpro="24", input_candidate: Path | None = None,
            repair=False):
    if cpro not in ("24", "10"):
        raise ValueError("ANALYTICAL_SCOPE_LIMITED_TO_LEON_AND_CACERES")
    if input_candidate is not None and output.resolve() == input_candidate.resolve():
        raise ValueError("OUTPUT_MUST_PRESERVE_ORIGINAL_CANDIDATE")
    unit, contract, bound, units, graph, k, population, floor, cap = _load_bound_inputs(root, cpro)
    ids = sorted(units)
    weights = {u: units[u]["population"] for u in ids}
    if input_candidate is not None:
        original_bytes = input_candidate.read_bytes()
        original = read_json(input_candidate)
        # Validate exact source identity against inputs independently evaluated now.
        audit = audit_candidate(original, unit, contract, expected_binding=bound["input_sha256"])
        input_audit_path = output.with_suffix(output.suffix + ".pre-repair-audit.json")
        write_json(input_audit_path, audit)
        state = state_from_candidate(original, units, cpro, k)
        input_digest = canonical_sha(original)
        witness_digest = original.get("witness_sha256")
        selected_order = original.get("selected_order", "historical_candidate")
        attempts = original.get("attempts", [])
        predecessor_sha = hashlib.sha256(original_bytes).hexdigest()
        if not repair:
            # Re-emit no changed assignment: this mode exists for a byte-bound audit.
            return {"candidate": original, "audit": audit, "original_sha256": predecessor_sha,
                    "audit_path": str(input_audit_path), "output": None}
        repair_result = consolidate_avoidable_splits(state, units, graph, floor=floor, cap=cap,
                                                       max_trials=MAX_REPAIR_TRIALS)
        state = repair_result["state"]
        if not repair_result["validation"].get("valid"):
            raise ValueError("REPAIRED_CANDIDATE_INVALID:" + repr(repair_result["validation"]))
        repair_record = {key: value for key, value in repair_result.items() if key != "state"}
    else:
        predecessor_sha = None
        repair_record = None
        attempts = []
        result = None
        for order in ORDERS:
            result = search_tree_partition(ids, graph, weights, k=k, floor=floor, cap=cap,
                                           node_order=_node_ordering(order, ids, graph, weights),
                                           max_states=MAX_STATES,
                                           max_transitions=MAX_TRANSITIONS,
                                           return_groups=True)
            attempts.append({"order": order, "status": result.status,
                             "input_sha256": result.input_sha256,
                             "witness_sha256": result.witness_sha256,
                             "explored_states": result.explored_states,
                             "explored_transitions": result.explored_transitions})
            if result.status == "TREE_WITNESS_FOUND_CONDITIONAL":
                state = {u: f"CPRO{cpro}-{i:02d}" for i, group in enumerate(result.groups, 1) for u in group}
                input_digest, witness_digest, selected_order = result.input_sha256, result.witness_sha256, order
                break
        else:
            raise RuntimeError("NO_CONDITIONAL_WITNESS_IN_DECLARED_BUDGET:" + repr(attempts))
        if repair:
            repair_result = consolidate_avoidable_splits(state, units, graph, floor=floor, cap=cap,
                                                           max_trials=MAX_REPAIR_TRIALS)
            state = repair_result["state"]
            repair_record = {key: value for key, value in repair_result.items() if key != "state"}
            if not repair_result["validation"].get("valid"):
                raise ValueError("REPAIR_FINAL_VALIDATION_INVALID:" + repr(repair_result["validation"]))
    candidate = _candidate_from_state(cpro=cpro, k=k, population=population, floor=floor,
                                      cap=cap, state=state, units=units, bound=bound,
                                      input_sha256=input_digest, witness_sha256=witness_digest,
                                      selected_order=selected_order, attempts=attempts,
                                      predecessor_sha256=predecessor_sha, repair=repair_record)
    final_audit = audit_candidate(candidate, unit, contract, expected_binding=bound["input_sha256"])
    write_json(output, candidate)
    write_json(output.with_suffix(output.suffix + ".audit.json"), final_audit)
    return {"candidate": candidate, "audit": final_audit,
            "original_sha256": predecessor_sha, "output": str(output)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cpro", choices=("24", "10"), default="24")
    parser.add_argument("--input-candidate", type=Path)
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    result = produce(args.root, args.output, cpro=args.cpro,
                     input_candidate=args.input_candidate, repair=args.repair)
    candidate, audit = result["candidate"], result["audit"]
    print(json.dumps({"cpro": candidate["cpro"], "k": candidate["k"],
                      "population": audit["district_populations"],
                      "municipal_split_count": len(audit["municipalities_split"]),
                      "checks": audit["checks"],
                      "candidate_sha256": hashlib.sha256(
                          (args.output.read_bytes() if args.output.exists() else
                           json.dumps(candidate, sort_keys=True, ensure_ascii=False).encode())).hexdigest(),
                      "generation_authorized": candidate["generation_authorized"],
                      "product_certification": candidate["product_certification"]},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
