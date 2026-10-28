"""Connected atomic groups for accredited discontinuous municipalities.

Version: 1.0.0. Date: 2026-10-26. Status: candidate.
Scope: M04 formation only; no graph edges, municipal divisions or limits change.
Reason: an administrative municipality can have several physical components.
Origin: new generic component; no predecessor.
"""
from __future__ import annotations

import heapq


class AtomicConnectorSearchBlocked(ValueError):
    """A bounded search did not establish a usable connected atomic group."""


def _components(nodes, adjacency):
    unseen = set(nodes)
    groups = []
    while unseen:
        seed = min(unseen, key=str)
        unseen.remove(seed)
        component, pending = {seed}, [seed]
        while pending:
            node = pending.pop()
            for neighbor in adjacency.get(node, ()):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        groups.append(component)
    return groups


def connected_atomic_municipality_groups(
    municipality_nodes, physical_adjacency, populations, declarations,
    *, atomic_limit, max_states=4096,
):
    """Return disjoint connected groups of complete municipalities and an audit.

    The caller validates source binding and supplies one province at a time.
    Only original physical edges may be supplied. Declarations are matched
    exactly against the observed components. A best-first bounded search adds
    whole adjacent municipalities, never a synthetic bridge or a point contact.
    Oversized municipalities cannot be connectors. Search exhaustion explicitly
    reports a search limit, rather than claiming structural impossibility.
    """
    groups = {str(m): set(nodes) for m, nodes in municipality_nodes.items()}
    if atomic_limit <= 0 or max_states < 1:
        raise ValueError("atomic_limit and max_states must be positive")
    owner = {}
    for municipality, nodes in groups.items():
        if not nodes:
            raise ValueError(f"empty municipality: {municipality}")
        for node in nodes:
            if node in owner:
                raise ValueError(f"node belongs to several municipalities: {node}")
            if node not in populations or populations[node] < 0:
                raise ValueError(f"missing or negative population: {node}")
            owner[node] = municipality
    accredited = {}
    for declaration in declarations:
        scope = str(declaration.get("admin_scope", ""))
        if not scope.startswith("municipality:"):
            continue
        municipality = scope.split(":", 1)[1]
        if municipality not in groups:
            continue  # The declaration may belong to another province.
        if municipality in accredited:
            raise ValueError(f"duplicate component declaration: {scope}")
        declared = [frozenset(map(str, c)) for c in declaration.get("components", [])]
        observed = [frozenset(c) for c in _components(groups[municipality], physical_adjacency)]
        if len(declared) < 2 or len(set(declared)) != len(declared) or set(declared) != set(observed):
            raise ValueError(f"stale administrative components: {scope}")
        accredited[municipality] = declaration
    disconnected = [m for m, nodes in sorted(groups.items())
                    if len(_components(nodes, physical_adjacency)) > 1]
    for municipality in disconnected:
        if municipality not in accredited:
            raise ValueError(f"unaccredited disconnected municipality: {municipality}")

    clusters = {m: frozenset([m]) for m in groups}
    audit = []
    def cluster_nodes(members):
        return set().union(*(groups[m] for m in members))
    def population(members):
        return sum(populations[n] for n in cluster_nodes(members))

    for municipality in disconnected:
        initial = clusters[municipality]
        if len(_components(cluster_nodes(initial), physical_adjacency)) == 1:
            continue
        if population(initial) > atomic_limit:
            raise AtomicConnectorSearchBlocked(
                f"M04: accredited disconnected municipality exceeds atomic limit: {municipality}"
            )
        queue = [(population(initial), tuple(sorted(initial)))]
        seen = {initial}
        examined = 0
        solution = None
        while queue and examined < max_states:
            _, members_tuple = heapq.heappop(queue)
            members = frozenset(members_tuple)
            nodes = cluster_nodes(members)
            examined += 1
            if len(_components(nodes, physical_adjacency)) == 1:
                solution = members
                break
            neighbors = {owner[nb] for n in nodes for nb in physical_adjacency.get(n, ())
                         if nb in owner and owner[nb] not in members}
            for neighbor in sorted(neighbors):
                candidate = members | clusters[neighbor]
                if candidate in seen:
                    continue
                seen.add(candidate)
                amount = population(candidate)
                if amount <= atomic_limit:
                    heapq.heappush(queue, (amount, tuple(sorted(candidate))))
        if solution is None:
            reason = "search_limit" if queue else "no_connector_within_atomic_limit"
            raise AtomicConnectorSearchBlocked(
                f"M04: atomic connector search blocked municipality={municipality} "
                f"reason={reason} states={examined} limit={atomic_limit}"
            )
        for member in solution:
            clusters[member] = solution
        audit.append({"municipality": municipality, "members": sorted(solution),
                      "population": population(solution), "states_examined": examined,
                      "source_components": len(accredited[municipality]["components"]),
                      "result_components": 1, "added_edges": 0})
    unique = sorted(set(clusters.values()), key=lambda members: tuple(sorted(members)))
    return [(tuple(sorted(members)), cluster_nodes(members)) for members in unique], audit
