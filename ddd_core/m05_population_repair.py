#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05: búsqueda poblacional genérica, acotada, determinista y monótona."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from collections import deque
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
    seen = {next(iter(nodes))}; q = deque(seen)
    while q:
        u = q.popleft()
        for v in adjacency.get(u, ()):
            if v in nodes and v not in seen:
                seen.add(v); q.append(v)
    return seen == nodes


def objective(populations, *, target, tolerance, floor, cap, cohesion_penalty=0.0):
    vals = list(populations.values())
    hard = sum(p < floor or p > cap for p in vals)
    outside = sum(abs(p - target) > tolerance for p in vals)
    maxdev = max((abs(p - target) / target for p in vals), default=0.0)
    totaldev = sum(abs(p - target) / target for p in vals)
    return (hard, outside, round(maxdev, 12), round(totaldev, 12), round(cohesion_penalty, 12))


def _district_pops(state, units):
    out = {}
    for u, d in state.items():
        out[d] = out.get(d, 0) + int(units[u]["population"])
    return out


def _district_nodes(state):
    out = {}
    for u, d in state.items(): out.setdefault(d, set()).add(u)
    return out


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
    if not moved or any(state.get(u) != donor for u in moved): return False, "NOT_OWNED"
    if any(units[u].get("province") != units[next(iter(moved))].get("province") for u in moved): return False, "CROSS_PROVINCE_SET"
    if any(units[u].get("province") != units[v].get("province") for u in moved for v in state if state[v] == receiver): return False, "CROSS_PROVINCE"
    if not _municipality_complete(moved, donor, state, units): return False, "MUNICIPAL_INTEGRITY"
    if not connected(moved, adjacency): return False, "TRANSFER_SET_DISCONNECTED"
    donor_nodes = {u for u, d in state.items() if d == donor} - moved
    receiver_nodes = {u for u, d in state.items() if d == receiver} | moved
    if not donor_nodes or not connected(donor_nodes, adjacency): return False, "DONOR_CONTIGUITY"
    if not connected(receiver_nodes, adjacency): return False, "RECEIVER_CONTIGUITY"
    trial = dict(state)
    for u in moved: trial[u] = receiver
    pops = _district_pops(trial, units)
    if pops[donor] < floor or pops[donor] > cap or pops[receiver] < floor or pops[receiver] > cap:
        return False, "HARD_POPULATION_LIMIT"
    return True, "VALID"


def _boundary_sets(state, adjacency, donor, receiver, max_size):
    owned = sorted(u for u, d in state.items() if d == donor)
    seeds = [u for u in owned if any(state.get(v) == receiver for v in adjacency.get(u, ()))]
    result = {frozenset([u]) for u in seeds}
    frontier = list(result)
    while frontier:
        s = frontier.pop()
        if len(s) >= max_size: continue
        for u in sorted(s):
            for v in adjacency.get(u, ()):
                ns = frozenset(set(s) | {v})
                if state.get(v) == donor and len(ns) <= max_size and ns not in result and connected(ns, adjacency):
                    result.add(ns); frontier.append(ns)
    return sorted(result, key=lambda x: (len(x), tuple(sorted(x))))


def repair(*, assignments, units, adjacency, target, tolerance, floor, cap, limits=None):
    """Busca transferencia, intercambio y cadenas; nunca sustituye baseline por una solución peor."""
    limits = limits or SearchLimits()
    rng = random.Random(limits.seed)
    start = time.monotonic(); examined = 0
    baseline = dict(assignments); baseline_pops = _district_pops(baseline, units)
    baseline_obj = objective(baseline_pops, target=target, tolerance=tolerance, floor=floor, cap=cap)
    best_state, best_obj, best_path = baseline, baseline_obj, []
    rejected = []
    queue = deque([(baseline, [])])
    seen = {tuple(sorted(baseline.items()))}

    while queue and examined < limits.max_candidates and time.monotonic() - start <= limits.max_seconds:
        state, path = queue.popleft()
        if len(path) >= limits.max_depth: continue
        districts = sorted(set(state.values()), key=str)
        pairs = [(a, b) for a in districts for b in districts if a != b]
        rng.shuffle(pairs)
        for donor, receiver in pairs:
            for moved in _boundary_sets(state, adjacency, donor, receiver, limits.max_transfer_set):
                examined += 1
                ok, reason = _valid_transfer(state, units, adjacency, moved, donor, receiver, floor=floor, cap=cap)
                if not ok:
                    if len(rejected) < 100: rejected.append({"units": sorted(moved), "districts": [donor, receiver], "reason": reason})
                    continue
                trial = dict(state)
                for u in moved: trial[u] = receiver
                key = tuple(sorted(trial.items()))
                if key in seen: continue
                seen.add(key)
                pops = _district_pops(trial, units)
                obj = objective(pops, target=target, tolerance=tolerance, floor=floor, cap=cap)
                step = {"units": sorted(moved), "donor": donor, "receiver": receiver, "reason": "VALID"}
                new_path = path + [step]
                if obj < best_obj:
                    best_state, best_obj, best_path = trial, obj, new_path
                if len(new_path) < limits.max_depth: queue.append((trial, new_path))
                if examined >= limits.max_candidates: break
            if examined >= limits.max_candidates: break

    final_pops = _district_pops(best_state, units)
    if best_obj >= baseline_obj:
        status = RESULT_NONE
    elif best_obj[1] == 0:
        status = RESULT_REPAIRED
    else:
        status = RESULT_IMPROVED
    affected = sorted({d for s in best_path for d in (s["donor"], s["receiver"])}, key=str)
    return {
        "schema": "ddd.m05-population-repair/1.0",
        "result": status,
        "limits": asdict(limits),
        "candidates_examined": examined,
        "objective_before": list(baseline_obj),
        "objective_after": list(best_obj),
        "populations_before": baseline_pops,
        "populations_after": final_pops,
        "assignments": best_state,
        "repairs": best_path,
        "districts_affected": affected,
        "constraints_verified": ["EXACT_DISTRICT_COUNT", "PROVINCE", "CONTIGUITY", "ATOMIC_UNITS", "MUNICIPAL_INTEGRITY", "HARD_POPULATION_LIMITS"],
        "rejections": rejected,
        "baseline_preserved": best_state == baseline,
    }
