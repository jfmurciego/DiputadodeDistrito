"""Bounded connected-partition witness search on one deterministic spanning forest.

Version: 1.0.0 (new isolated Congress diagnostic; 2026-10-20)
A found witness proves only the supplied section graph and population bounds.
It does not apply municipal policy, accredit multipart physical connectivity,
certify a territorial product or authorize generation. Assignments are not
returned; only a canonical witness digest is exposed.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


@dataclass(frozen=True)
class TreeSearchResult:
    status: str
    input_sha256: str
    witness_sha256: str | None
    explored_states: int
    explored_transitions: int
    spanning_forest_components: int
    proof: str


def _canonical_input(nodes, adjacency, weights, k, floor, cap):
    return json.dumps({
        "nodes": sorted(nodes),
        "edges": sorted([a, b] for a in nodes for b in adjacency[a] if a < b),
        "weights": {n: weights[n] for n in sorted(nodes)},
        "k": k, "floor": floor, "cap": cap,
    }, sort_keys=True, separators=(",", ":")).encode()


def search_tree_partition(
    nodes: Sequence[str], adjacency: Mapping[str, Sequence[str] | set[str]],
    weights: Mapping[str, int], *, k: int, floor: int, cap: int,
    max_states: int = 50_000, max_transitions: int = 250_000,
) -> TreeSearchResult:
    """Find a K-way bounded connected partition along a fixed BFS forest.

    The DP chooses tree-edge cuts, so every returned group is connected in the
    input graph. A negative result only concerns this one spanning forest and
    is never promoted to mathematical infeasibility of the original graph.
    """
    universe = tuple(nodes)
    if not universe or any(not isinstance(n, str) or not n for n in universe):
        raise ValueError("NODES_INVALID")
    if len(set(universe)) != len(universe):
        raise ValueError("NODES_INVALID")
    node_set = set(universe)
    if set(weights) != node_set or set(adjacency) != node_set:
        raise ValueError("GRAPH_COVERAGE_INVALID")
    for name, value in (("k", k), ("floor", floor), ("cap", cap),
                        ("max_states", max_states), ("max_transitions", max_transitions)):
        if type(value) is not int:
            raise ValueError(name + "_MUST_BE_INTEGER")
    if k < 1 or floor < 0 or cap < floor or max_states < 1 or max_transitions < 1:
        raise ValueError("BOUNDS_INVALID")
    if any(type(weights[n]) is not int or weights[n] < 0 for n in universe):
        raise ValueError("WEIGHTS_INVALID")
    graph = {n: set(adjacency[n]) for n in universe}
    if any(n in graph[n] or not graph[n] <= node_set for n in universe):
        raise ValueError("ADJACENCY_INVALID")
    if any(n not in graph[m] for n in universe for m in graph[n]):
        raise ValueError("ADJACENCY_NOT_SYMMETRIC")
    digest = hashlib.sha256(_canonical_input(universe, graph, weights, k, floor, cap)).hexdigest()

    def outcome(status, *, witness=None, states=0, transitions=0, components=0, proof):
        return TreeSearchResult(status, digest, witness, states, transitions, components, proof)

    total = sum(weights.values())
    if k > len(universe):
        return outcome("PROVEN_INFEASIBLE", components=0, proof="K_EXCEEDS_ATOMIC_CUSEC_COUNT")
    if total < k * floor or total > k * cap:
        return outcome("PROVEN_INFEASIBLE", components=0, proof="TOTAL_POPULATION_OUTSIDE_K_BOUNDS")
    if any(weights[n] > cap for n in universe):
        return outcome("PROVEN_INFEASIBLE", components=0, proof="CUSEC_POPULATION_EXCEEDS_HARD_CAP")

    # Build a deterministic spanning forest using physical section edges only.
    parent: dict[str, str | None] = {}
    children: dict[str, list[str]] = {n: [] for n in universe}
    roots: list[str] = []
    for root in sorted(universe):
        if root in parent:
            continue
        roots.append(root)
        parent[root] = None
        queue = deque([root])
        while queue:
            node = queue.popleft()
            for neighbor in sorted(graph[node]):
                if neighbor in parent:
                    continue
                parent[neighbor] = node
                children[node].append(neighbor)
                queue.append(neighbor)
    postorder: list[str] = []
    stack = [(root, False) for root in roots]
    while stack:
        node, visited = stack.pop()
        if visited:
            postorder.append(node)
            continue
        stack.append((node, True))
        stack.extend((child, False) for child in reversed(children[node]))

    # DP state is (closed_groups, open_population) -> canonical tuple of cuts.
    states_total = 0
    transitions = 0
    dp: dict[str, dict[tuple[int, int], tuple[tuple[str, str], ...]]] = {}

    class BudgetExceeded(Exception):
        pass

    def insert(target, key, cuts):
        nonlocal states_total
        old = target.get(key)
        if old is None:
            states_total += 1
            if states_total > max_states:
                raise BudgetExceeded
            target[key] = cuts
        elif cuts < old:
            target[key] = cuts

    try:
        for node in postorder:
            current: dict[tuple[int, int], tuple[tuple[str, str], ...]] = {}
            if weights[node] <= cap:
                insert(current, (0, weights[node]), ())
            for child in children[node]:
                child_dp = dp[child]
                combined: dict[tuple[int, int], tuple[tuple[str, str], ...]] = {}
                edge = tuple(sorted((node, child)))
                for (parent_closed, parent_open), parent_cuts in current.items():
                    for (child_closed, child_open), child_cuts in child_dp.items():
                        transitions += 1
                        if transitions > max_transitions:
                            raise BudgetExceeded
                        cuts = tuple(sorted(parent_cuts + child_cuts))
                        merged = parent_open + child_open
                        if merged <= cap and parent_closed + child_closed < k:
                            insert(combined, (parent_closed + child_closed, merged), cuts)
                        if floor <= child_open <= cap and parent_closed + child_closed + 1 < k:
                            insert(combined, (parent_closed + child_closed + 1, parent_open),
                                   tuple(sorted(cuts + (edge,))))
                current = combined
                if not current:
                    break
            dp[node] = current
    except BudgetExceeded:
        return outcome("SEARCH_EXHAUSTED", states=states_total, transitions=transitions,
                       components=len(roots), proof="TREE_DP_STATE_OR_TRANSITION_BUDGET")

    # Each graph component must be partitioned independently. Combine the
    # possible district counts from its root without adding artificial edges.
    component_options = []
    for root in roots:
        options: dict[int, tuple[tuple[str, str], ...]] = {}
        for (closed, opened), cuts in dp[root].items():
            if floor <= opened <= cap and closed + 1 <= k:
                count = closed + 1
                if count not in options or cuts < options[count]:
                    options[count] = cuts
        component_options.append(options)
    global_options: dict[int, tuple[tuple[str, str], ...]] = {0: ()}
    try:
        for options in component_options:
            updated: dict[int, tuple[tuple[str, str], ...]] = {}
            for previous_count, previous_cuts in global_options.items():
                for component_count, component_cuts in options.items():
                    transitions += 1
                    if transitions > max_transitions:
                        raise BudgetExceeded
                    count = previous_count + component_count
                    if count > k:
                        continue
                    cuts = tuple(sorted(previous_cuts + component_cuts))
                    if count not in updated:
                        states_total += 1
                        if states_total > max_states:
                            raise BudgetExceeded
                        updated[count] = cuts
                    elif cuts < updated[count]:
                        updated[count] = cuts
            global_options = updated
    except BudgetExceeded:
        return outcome("SEARCH_EXHAUSTED", states=states_total, transitions=transitions,
                       components=len(roots), proof="FOREST_COMBINATION_BUDGET")

    selected_cuts = global_options.get(k)
    if selected_cuts is None:
        return outcome("TREE_WITNESS_NOT_FOUND", states=states_total, transitions=transitions,
                       components=len(roots), proof="NO_PARTITION_ON_SELECTED_SPANNING_FOREST")

    cut_set = set(selected_cuts)
    tree = {n: set(children[n]) for n in universe}
    for child, p in parent.items():
        if p is not None:
            tree[child].add(p)
            tree[p].add(child)
    groups = []
    seen = set()
    for start in sorted(universe):
        if start in seen:
            continue
        group = set(); todo = [start]
        while todo:
            node = todo.pop()
            if node in seen:
                continue
            seen.add(node); group.add(node)
            for neighbor in tree[node]:
                if tuple(sorted((node, neighbor))) in cut_set:
                    continue
                if neighbor not in seen:
                    todo.append(neighbor)
        groups.append(tuple(sorted(group)))
    if len(groups) != k or any(not floor <= sum(weights[n] for n in group) <= cap for group in groups):
        return outcome("WITNESS_VALIDATION_FAILED", states=states_total, transitions=transitions,
                       components=len(roots), proof="INDEPENDENT_TREE_CUT_CHECK_FAILED")
    canonical = json.dumps(sorted(groups), separators=(",", ":")).encode()
    witness = hashlib.sha256(canonical).hexdigest()
    return outcome("TREE_WITNESS_FOUND_CONDITIONAL", witness=witness, states=states_total,
                   transitions=transitions, components=len(roots), proof="BOUNDED_TREE_CUT_WITNESS")
