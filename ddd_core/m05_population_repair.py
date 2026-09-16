#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05: reparación poblacional genérica, acotada, determinista y monótona."""
from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass
import random
import time

RESULT_REPAIRED = "REPAIRED"
RESULT_IMPROVED = "IMPROVED_NOT_REPAIRED"
RESULT_NONE = "NO_FEASIBLE_REPAIR_FOUND"


@dataclass(frozen=True)
class SearchLimits:
    max_depth: int = 3
    max_transfer_set: int = 2
    max_candidates: int = 5000
    max_seconds: float = 5.0
    seed: int = 0


def connected(nodes, adjacency):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    q = deque(seen)
    while q:
        u = q.popleft()
        for v in adjacency.get(u, ()):
            if v in nodes and v not in seen:
                seen.add(v)
                q.append(v)
    return seen == nodes


def _cut_edges(state, adjacency):
    """Aristas del grafo de unidades que atraviesan una frontera distrital."""
    seen = set()
    cuts = 0
    for u in sorted(state, key=str):
        for v in adjacency.get(u, ()):
            if v not in state:
                continue
            edge = frozenset((u, v))
            if len(edge) != 2 or edge in seen:
                continue
            seen.add(edge)
            if state[u] != state[v]:
                cuts += 1
    return cuts


def territorial_metrics(state, adjacency, *, boundary_units_moved=0):
    # El motor base no expone actualmente una métrica geométrica de
    # compactitud ni una penalización de corredor reutilizable. No se inventan.
    return {
        "cut_boundary_edges": _cut_edges(state, adjacency),
        "boundary_units_moved": int(boundary_units_moved),
        "corridor_penalty": None,
        "base_compactness": None,
    }


def objective(populations, *, target, tolerance, floor, cap, cohesion=0):
    vals = list(populations.values())
    hard = sum(p < floor or p > cap for p in vals)
    outside = sum(abs(p - target) > tolerance for p in vals)
    maxdev = max((abs(p - target) / target for p in vals), default=0.0)
    totaldev = sum(abs(p - target) / target for p in vals)
    # Jerarquía estricta: cohesión sólo decide después de los cuatro niveles poblacionales.
    return (hard, outside, round(maxdev, 12), round(totaldev, 12), int(cohesion))


def _district_pops(state, units):
    out = {}
    for u, d in state.items():
        out[d] = out.get(d, 0) + int(units[u]["population"])
    return out


def _deviations(pops, target):
    return {d: round((p - target) / target, 12) for d, p in pops.items()}


def _municipality_complete(moved, donor, state, units):
    moved = set(moved)
    groups = {units[u].get("municipality_group") for u in moved if units[u].get("municipality_group")}
    for group in groups:
        owned = {u for u, d in state.items() if d == donor and units[u].get("municipality_group") == group}
        if owned and not owned <= moved:
            return False
    return True


def _valid_transfer(state, units, adjacency, moved, donor, receiver, *, floor, cap):
    moved = set(moved)
    checks = {
        "province_verified": False,
        "donor_contiguity_verified": False,
        "receiver_contiguity_verified": False,
        "atomic_units_verified": False,
        "municipal_integrity_verified": False,
    }
    if not moved or any(state.get(u) != donor for u in moved):
        return False, "NOT_OWNED", checks
    checks["atomic_units_verified"] = True
    provinces = {units[u].get("province") for u in moved}
    receiver_provinces = {units[v].get("province") for v in state if state[v] == receiver}
    if len(provinces) != 1 or len(receiver_provinces) != 1 or provinces != receiver_provinces:
        return False, "CROSS_PROVINCE", checks
    checks["province_verified"] = True
    if not _municipality_complete(moved, donor, state, units):
        return False, "MUNICIPAL_INTEGRITY", checks
    checks["municipal_integrity_verified"] = True
    if not connected(moved, adjacency):
        return False, "TRANSFER_SET_DISCONNECTED", checks
    donor_nodes = {u for u, d in state.items() if d == donor} - moved
    receiver_nodes = {u for u, d in state.items() if d == receiver} | moved
    if not donor_nodes or not connected(donor_nodes, adjacency):
        return False, "DONOR_CONTIGUITY", checks
    checks["donor_contiguity_verified"] = True
    if not connected(receiver_nodes, adjacency):
        return False, "RECEIVER_CONTIGUITY", checks
    checks["receiver_contiguity_verified"] = True
    trial = dict(state)
    for u in moved:
        trial[u] = receiver
    pops = _district_pops(trial, units)
    if pops[donor] < floor or pops[donor] > cap or pops[receiver] < floor or pops[receiver] > cap:
        return False, "HARD_POPULATION_LIMIT", checks
    return True, "VALID", checks


def _boundary_sets(state, adjacency, donor, receiver, max_size):
    owned = sorted((u for u, d in state.items() if d == donor), key=str)
    seeds = [u for u in owned if any(state.get(v) == receiver for v in adjacency.get(u, ()))]
    result = {frozenset((u,)) for u in seeds}
    frontier = list(result)
    while frontier:
        s = frontier.pop()
        if len(s) >= max_size:
            continue
        for u in sorted(s, key=str):
            for v in adjacency.get(u, ()):
                ns = frozenset(set(s) | {v})
                if state.get(v) == donor and len(ns) <= max_size and ns not in result and connected(ns, adjacency):
                    result.add(ns)
                    frontier.append(ns)
    return sorted(result, key=lambda x: (len(x), tuple(sorted(x, key=str))))


def _step_evidence(state, trial, units, adjacency, moved, donor, receiver, checks,
                   *, target, tolerance, floor, cap):
    before = _district_pops(state, units)
    after = _district_pops(trial, units)
    tm = territorial_metrics(trial, adjacency, boundary_units_moved=len(moved))
    obj = objective(after, target=target, tolerance=tolerance, floor=floor, cap=cap,
                    cohesion=tm["cut_boundary_edges"])
    return {
        "units": sorted(moved, key=str),
        "donor": donor,
        "receiver": receiver,
        "population_before": before,
        "population_after": after,
        "deviation_before": _deviations(before, target),
        "deviation_after": _deviations(after, target),
        "objective_after_step": list(obj),
        "territorial_metrics": tm,
        **checks,
        "reason": "ACCEPTED_VALID_CANDIDATE",
    }


def repair(*, assignments, units, adjacency, target, tolerance, floor, cap, limits=None):
    """Busca transferencias y cadenas; el mejor estado se ordena lexicográficamente."""
    limits = limits or SearchLimits()
    rng = random.Random(limits.seed)
    start = time.monotonic()
    examined = 0
    baseline = dict(assignments)
    baseline_pops = _district_pops(baseline, units)
    baseline_tm = territorial_metrics(baseline, adjacency)
    baseline_obj = objective(baseline_pops, target=target, tolerance=tolerance, floor=floor, cap=cap,
                             cohesion=baseline_tm["cut_boundary_edges"])
    best_state, best_obj, best_path = baseline, baseline_obj, []
    rejected = []
    queue = deque([(baseline, [])])
    seen = {tuple(sorted(baseline.items(), key=lambda x: str(x[0])))}

    while queue and examined < limits.max_candidates and time.monotonic() - start <= limits.max_seconds:
        state, path = queue.popleft()
        if len(path) >= limits.max_depth:
            continue
        districts = sorted(set(state.values()), key=str)
        pairs = [(a, b) for a in districts for b in districts if a != b]
        rng.shuffle(pairs)
        for donor, receiver in pairs:
            for moved in _boundary_sets(state, adjacency, donor, receiver, limits.max_transfer_set):
                if examined >= limits.max_candidates:
                    break
                examined += 1
                ok, reason, checks = _valid_transfer(state, units, adjacency, moved, donor, receiver,
                                                     floor=floor, cap=cap)
                if not ok:
                    if len(rejected) < 100:
                        rejected.append({"units": sorted(moved, key=str), "districts": [donor, receiver],
                                         "reason": reason, **checks})
                    continue
                trial = dict(state)
                for u in moved:
                    trial[u] = receiver
                key = tuple(sorted(trial.items(), key=lambda x: str(x[0])))
                if key in seen:
                    continue
                seen.add(key)
                step = _step_evidence(state, trial, units, adjacency, moved, donor, receiver, checks,
                                      target=target, tolerance=tolerance, floor=floor, cap=cap)
                obj = tuple(step["objective_after_step"])
                new_path = path + [step]
                if obj < best_obj:
                    best_state, best_obj, best_path = trial, obj, new_path
                if len(new_path) < limits.max_depth:
                    queue.append((trial, new_path))

    final_pops = _district_pops(best_state, units)
    final_tm = territorial_metrics(best_state, adjacency,
                                   boundary_units_moved=sum(len(s["units"]) for s in best_path))
    if best_obj >= baseline_obj:
        status = RESULT_NONE
    elif best_obj[1] == 0:
        status = RESULT_REPAIRED
    else:
        status = RESULT_IMPROVED
    affected = sorted({d for s in best_path for d in (s["donor"], s["receiver"])}, key=str)
    return {
        "schema": "ddd.m05-population-repair/1.1",
        "result": status,
        "limits": asdict(limits),
        "candidates_examined": examined,
        "objective_hierarchy": ["hard_constraints", "outliers", "max_deviation", "total_deviation", "cohesion"],
        "objective_before": list(baseline_obj),
        "objective_after": list(best_obj),
        "territorial_metrics_before": baseline_tm,
        "territorial_metrics_after": final_tm,
        "population_before": baseline_pops,
        "population_after": final_pops,
        "populations_before": baseline_pops,
        "populations_after": final_pops,
        "assignments": best_state,
        "repairs": best_path,
        "districts_affected": affected,
        "constraints_verified": ["EXACT_DISTRICT_COUNT", "PROVINCE", "CONTIGUITY", "ATOMIC_UNITS",
                                 "MUNICIPAL_INTEGRITY", "HARD_POPULATION_LIMITS"],
        "territorial_metric_availability": {
            "cut_boundary_edges": True,
            "boundary_units_moved": True,
            "corridor_penalty": False,
            "base_compactness": False,
        },
        "rejections": rejected,
        "baseline_preserved": best_state == baseline,
    }
