"""Bounded exact solver for small synthetic connected-partition fixtures.

This module is diagnostic only. It does not read territorial sources, invoke
the district-generation pipeline, apply municipality policy, or authorize a
product. A returned witness proves feasibility only for the supplied finite
graph, integer weights and bounds.

Version: 1.0.0 (new isolated Congress diagnostic; 2026-10-13)
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


@dataclass(frozen=True)
class ExactPartitionResult:
    status: str
    input_sha256: str
    groups: tuple[tuple[str, ...], ...] = ()
    explored_groups: int = 0
    explored_states: int = 0
    proof: str | None = None
    certificate: dict | None = None


def solve_bounded_connected_partition(
    nodes: Sequence[str],
    adjacency: Mapping[str, Sequence[str] | set[str] | frozenset[str]],
    weights: Mapping[str, int],
    *,
    k: int,
    floor: int,
    cap: int,
    max_groups: int = 100_000,
    max_states: int = 200_000,
) -> ExactPartitionResult:
    """Find exactly ``k`` connected groups covering nodes within hard bounds.

    ``PROVEN_INFEASIBLE`` is emitted only for a sound arithmetic necessary-
    condition certificate or after exhaustive connected-group enumeration and
    exhaustive exact-cover search. Budget exhaustion is always
    ``SEARCH_EXHAUSTED``. Municipality rules are deliberately outside scope.
    """
    universe = tuple(nodes)
    if (not universe or any(not isinstance(n, str) or not n for n in universe)
            or len(set(universe)) != len(universe)):
        raise ValueError("nodes must be a non-empty sequence of unique strings")
    node_set = set(universe)
    if set(weights) != node_set:
        raise ValueError("weights keys must exactly match nodes")
    if set(adjacency) != node_set:
        raise ValueError("adjacency keys must exactly match nodes")
    for value, label in ((k, "k"), (floor, "floor"), (cap, "cap"),
                         (max_groups, "max_groups"), (max_states, "max_states")):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{label} must be an integer")
    if k < 1 or floor < 0 or cap < floor or max_groups < 1 or max_states < 1:
        raise ValueError("invalid k, bounds, or search budget")
    for node, pop in weights.items():
        if isinstance(pop, bool) or not isinstance(pop, int) or pop < 0:
            raise ValueError(f"weight for {node!r} must be a non-negative integer")

    graph: dict[str, frozenset[str]] = {}
    for node, neighbors in adjacency.items():
        ns = frozenset(neighbors)
        if node in ns or not ns <= node_set:
            raise ValueError(f"invalid self-loop or external neighbor at {node!r}")
        graph[node] = ns
    if any(node not in graph[neighbor] for node, ns in graph.items() for neighbor in ns):
        raise ValueError("adjacency must be symmetric")

    canonical = {
        "nodes": sorted(universe),
        "edges": sorted([a, b] for a in universe for b in graph[a] if a < b),
        "weights": {n: weights[n] for n in sorted(universe)},
        "k": k, "floor": floor, "cap": cap,
    }
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def result(status: str, *, groups=(), eg=0, es=0, proof=None, facts=None):
        certificate = {
            "input_sha256": digest,
            "method": proof,
            "proof_complete": status in {"PROVEN_INFEASIBLE", "SOLUTION_FOUND"},
            "search_exhaustive": status == "PROVEN_INFEASIBLE" and proof == "EXHAUSTIVE_CONNECTED_EXACT_COVER",
            "enumerated_groups": eg,
            "explored_states": es,
        }
        if facts:
            certificate.update(facts)
        return ExactPartitionResult(status, digest, tuple(groups), eg, es, proof, certificate)

    total = sum(weights.values())
    if k > len(universe):
        return result("PROVEN_INFEASIBLE", proof="K_EXCEEDS_NONEMPTY_ATOMIC_UNITS",
                      facts={"k": k, "atomic_units": len(universe)})
    if total < k * floor or total > k * cap:
        return result("PROVEN_INFEASIBLE", proof="TOTAL_POPULATION_OUTSIDE_K_BOUNDS",
                      facts={"total_population": total, "k": k,
                             "minimum_total": k * floor, "maximum_total": k * cap})

    # Enumerate all connected subsets whose population can still be extended
    # without exceeding cap. Zero-weight vertices remain correctly searchable.
    seen = {frozenset((node,)) for node in universe}
    if len(seen) > max_groups:
        return result("SEARCH_EXHAUSTED", eg=len(seen), proof="CONNECTED_GROUP_BUDGET",
                      facts={"max_groups": max_groups, "search_exhaustive": False})
    frontier = sorted(seen, key=lambda g: tuple(sorted(g)))
    admissible: list[frozenset[str]] = []
    while frontier:
        group = frontier.pop()
        pop = sum(weights[n] for n in group)
        if floor <= pop <= cap:
            admissible.append(group)
        if pop > cap:
            continue
        boundary = sorted({v for u in group for v in graph[u] if v not in group})
        for v in boundary:
            extended = group | {v}
            if extended in seen:
                continue
            seen.add(extended)
            if len(seen) > max_groups:
                return result("SEARCH_EXHAUSTED", eg=len(seen), proof="CONNECTED_GROUP_BUDGET",
                              facts={"max_groups": max_groups, "search_exhaustive": False})
            if sum(weights[n] for n in extended) <= cap:
                frontier.append(extended)
    admissible.sort(key=lambda g: (len(g), tuple(sorted(g))))

    by_node = {n: [] for n in universe}
    for group in admissible:
        for node in group:
            by_node[node].append(group)
    for node in universe:
        by_node[node].sort(key=lambda g: (len(g), tuple(sorted(g))))
    memo: dict[tuple[frozenset[str], int], tuple[tuple[str, ...], ...] | None] = {}
    states = 0

    class BudgetExceeded(Exception):
        pass

    def cover(remaining: frozenset[str], groups_left: int):
        nonlocal states
        states += 1
        if states > max_states:
            raise BudgetExceeded
        if not remaining:
            return () if groups_left == 0 else None
        if groups_left <= 0 or len(remaining) < groups_left:
            return None
        pop = sum(weights[n] for n in remaining)
        if pop < groups_left * floor or pop > groups_left * cap:
            return None
        key = (remaining, groups_left)
        if key in memo:
            return memo[key]
        candidates_by_node = {
            n: [g for g in by_node[n] if g <= remaining]
            for n in remaining
        }
        pivot = min(remaining, key=lambda n: (len(candidates_by_node[n]), n))
        for group in candidates_by_node[pivot]:
            tail = cover(remaining - group, groups_left - 1)
            if tail is not None:
                answer = (tuple(sorted(group)),) + tail
                memo[key] = answer
                return answer
        memo[key] = None
        return None

    try:
        solution = cover(frozenset(universe), k)
    except BudgetExceeded:
        return result("SEARCH_EXHAUSTED", eg=len(seen), es=states, proof="EXACT_COVER_STATE_BUDGET",
                      facts={"max_states": max_states, "search_exhaustive": False})
    if solution is None:
        return result("PROVEN_INFEASIBLE", eg=len(seen), es=states, proof="EXHAUSTIVE_CONNECTED_EXACT_COVER")
    ordered = tuple(sorted(solution))
    return result("SOLUTION_FOUND", groups=ordered, eg=len(seen), es=states, proof="EXACT_CONNECTED_COVER_WITNESS")
