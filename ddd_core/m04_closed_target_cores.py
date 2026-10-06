from __future__ import annotations

from itertools import permutations

EPS = 1e-9


def _connected(nodes, adjacency):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    stack = list(seen)
    while stack:
        node = stack.pop()
        for neighbor in adjacency.get(node, set()):
            if neighbor in nodes and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == nodes


def _population(nodes, weights):
    return sum(weights[node] for node in nodes)


def _core_bounds(target, floor, cap, tolerance):
    return max(float(floor), float(target - tolerance)), min(
        float(cap), float(target + tolerance)
    )


def _core_outliers(parts, weights, *, target, floor, cap, tolerance):
    lower, upper = _core_bounds(target, floor, cap, tolerance)
    result = []
    for index, part in enumerate(parts):
        population = _population(part, weights)
        if population < lower - EPS or population > upper + EPS:
            result.append((index, int(population)))
    return result


def _partition_evidence(parts, residual, weights, *, target, floor, cap, tolerance):
    lower, upper = _core_bounds(target, floor, cap, tolerance)
    return {
        "core_target_min": float(lower),
        "core_target_max": float(upper),
        "closed_core_populations": [int(_population(part, weights)) for part in parts],
        "residual_population": int(_population(residual, weights)),
    }


def _enumerate_connected_target_groups(
    nodes,
    adjacency,
    weights,
    *,
    lower,
    upper,
    protected=(),
    max_seen=100000,
):
    nodes = set(nodes)
    protected = set(protected or ())
    seen = {frozenset((node,)) for node in nodes if node not in protected}
    frontier = list(seen)
    groups = []
    while frontier:
        group = frontier.pop()
        population = _population(group, weights)
        if lower - EPS <= population <= upper + EPS:
            groups.append(group)
        if population > upper + EPS:
            continue
        boundary = sorted(
            {
                neighbor
                for node in group
                for neighbor in adjacency.get(node, set())
                if neighbor in nodes
                and neighbor not in group
                and neighbor not in protected
            },
            key=str,
        )
        for neighbor in boundary:
            candidate = frozenset(set(group) | {neighbor})
            if candidate in seen:
                continue
            seen.add(candidate)
            if len(seen) > max_seen:
                return None, len(seen)
            if _population(candidate, weights) <= upper + EPS:
                frontier.append(candidate)
    groups.sort(
        key=lambda group: (
            abs(_population(group, weights) - ((lower + upper) / 2.0)),
            len(group),
            tuple(sorted(group, key=str)),
        )
    )
    return groups, len(seen)


def _best_alignment(chosen, residual, initial_closed, initial_residual):
    chosen = [set(group) for group in chosen]
    initial_closed = [set(group) for group in initial_closed]
    initial_residual = set(initial_residual)
    if len(chosen) > 7:
        ordered = []
        remaining = list(chosen)
        for current in initial_closed:
            best = max(
                range(len(remaining)),
                key=lambda index: (
                    len(current & remaining[index]),
                    -len(remaining[index]),
                    tuple(sorted(remaining[index], key=str)),
                ),
            )
            ordered.append(remaining.pop(best))
        return ordered

    best = None
    for ordered in permutations(chosen):
        overlap = len(set(residual) & initial_residual)
        overlap += sum(
            len(set(group) & initial_closed[index])
            for index, group in enumerate(ordered)
        )
        signature = tuple(tuple(sorted(group, key=str)) for group in ordered)
        candidate = (-overlap, signature, [set(group) for group in ordered])
        if best is None or candidate[:2] < best[:2]:
            best = candidate
    return best[2]


def _exact_repair(
    closed,
    residual,
    *,
    target,
    floor,
    cap,
    tolerance,
    adjacency,
    weights,
    protected=(),
    residual_gateways=(),
    max_seen=100000,
    max_states=200000,
):
    nodes = set(residual)
    for part in closed:
        nodes.update(part)
    lower, upper = _core_bounds(target, floor, cap, tolerance)
    groups, seen = _enumerate_connected_target_groups(
        nodes,
        adjacency,
        weights,
        lower=lower,
        upper=upper,
        protected=protected,
        max_seen=max_seen,
    )
    if groups is None:
        return None, "UNKNOWN_GROUP_LIMIT", {"groups_seen": int(seen)}

    protected = set(protected or ())
    residual_gateways = set(residual_gateways or ())
    core_count = len(closed)
    initial_closed = [set(part) for part in closed]
    initial_residual = set(residual)
    best = None
    states = 0

    class SearchLimit(RuntimeError):
        pass

    def solve(start, remaining, chosen):
        nonlocal states, best
        states += 1
        if states > max_states:
            raise SearchLimit
        left = core_count - len(chosen)
        if left == 0:
            candidate_residual = set(remaining)
            if not candidate_residual or not _connected(candidate_residual, adjacency):
                return
            if protected and not protected <= candidate_residual:
                return
            if residual_gateways and not (candidate_residual & residual_gateways):
                return
            residual_population = _population(candidate_residual, weights)
            if residual_population > cap + EPS:
                return
            aligned = _best_alignment(
                chosen, candidate_residual, initial_closed, initial_residual
            )
            owner_before = {}
            for index, part in enumerate(initial_closed + [initial_residual]):
                for node in part:
                    owner_before[node] = index
            owner_after = {}
            for index, part in enumerate(aligned + [candidate_residual]):
                for node in part:
                    owner_after[node] = index
            churn = sum(owner_before[node] != owner_after[node] for node in nodes)
            core_populations = [_population(part, weights) for part in aligned]
            score = (
                int(churn),
                abs(residual_population - target),
                sum((population - target) ** 2 for population in core_populations),
                tuple(tuple(sorted(part, key=str)) for part in aligned),
                tuple(sorted(candidate_residual, key=str)),
            )
            if best is None or score < best[0]:
                best = (score, aligned, candidate_residual)
            return
        if len(remaining) <= left:
            return
        remaining_population = _population(remaining, weights)
        if remaining_population < left * lower - EPS:
            return
        for index in range(start, len(groups)):
            group = groups[index]
            if group <= remaining:
                solve(index + 1, remaining - group, chosen + [group])

    try:
        solve(0, frozenset(nodes), [])
    except SearchLimit:
        return None, "UNKNOWN_STATE_LIMIT", {
            "groups_seen": int(seen),
            "search_states": int(states),
        }
    if best is None:
        return None, "INCOMPATIBLE", {
            "groups_seen": int(seen),
            "search_states": int(states),
        }
    return (best[1], best[2]), "FEASIBLE", {
        "groups_seen": int(seen),
        "search_states": int(states),
        "churn": int(best[0][0]),
    }


def _beam_repair(
    closed,
    residual,
    *,
    target,
    floor,
    cap,
    tolerance,
    adjacency,
    weights,
    protected=(),
    residual_gateways=(),
    allow_residual=False,
    focus_only=True,
    max_depth=4,
    beam_width=64,
):
    initial_parts = [set(part) for part in closed] + [set(residual)]
    node_order = sorted(set().union(*initial_parts), key=str)
    part_count = len(initial_parts)
    residual_index = part_count - 1
    protected = set(protected or ())
    residual_gateways = set(residual_gateways or ())
    lower, upper = _core_bounds(target, floor, cap, tolerance)
    initial_owner = {}
    for index, part in enumerate(initial_parts):
        for node in part:
            initial_owner[node] = index
    initial_state = tuple(initial_owner[node] for node in node_order)
    positions = {node: index for index, node in enumerate(node_order)}

    def unpack(state):
        result = [set() for _ in range(part_count)]
        for node, owner in zip(node_order, state):
            result[owner].add(node)
        return result

    def populations(parts):
        return [_population(part, weights) for part in parts]

    def outlier_indices(values):
        return {
            index
            for index, population in enumerate(values[:-1])
            if population < lower - EPS or population > upper + EPS
        }

    def score(state):
        parts = unpack(state)
        values = populations(parts)
        magnitudes = [
            max(0.0, lower - population, population - upper)
            for population in values[:-1]
        ]
        churn = sum(
            owner != initial_owner[node]
            for node, owner in zip(node_order, state)
        )
        residual_deviation = abs(values[-1] - target)
        return (
            sum(value > EPS for value in magnitudes),
            sum(magnitudes),
            max(magnitudes or [0.0]),
            int(churn),
            residual_deviation,
            sum((population - target) ** 2 for population in values[:-1]),
            state,
        )

    def goal(state):
        values = populations(unpack(state))
        return all(lower - EPS <= value <= upper + EPS for value in values[:-1])

    def moves(state):
        parts = unpack(state)
        owner = {node: value for node, value in zip(node_order, state)}
        values = populations(parts)
        outliers = outlier_indices(values)
        emitted = set()
        for node in node_order:
            source = owner[node]
            for neighbor in sorted(adjacency.get(node, set()), key=str):
                if neighbor not in owner:
                    continue
                destination = owner[neighbor]
                if source == destination:
                    continue
                if not allow_residual and (
                    source == residual_index or destination == residual_index
                ):
                    continue
                if focus_only and source not in outliers and destination not in outliers:
                    continue
                move = (node, source, destination)
                if move in emitted:
                    continue
                emitted.add(move)
                if len(parts[source]) <= 1:
                    continue
                source_population = values[source] - weights[node]
                destination_population = values[destination] + weights[node]
                if source != residual_index and not (
                    floor - EPS <= source_population <= cap + EPS
                ):
                    continue
                if destination != residual_index and not (
                    floor - EPS <= destination_population <= cap + EPS
                ):
                    continue
                if source == residual_index:
                    new_residual = parts[source] - {node}
                    if not new_residual or source_population > cap + EPS:
                        continue
                    if protected and not protected <= new_residual:
                        continue
                    if residual_gateways and not (new_residual & residual_gateways):
                        continue
                if destination == residual_index and destination_population > cap + EPS:
                    continue
                if not _connected(parts[source] - {node}, adjacency):
                    continue
                candidate = list(state)
                candidate[positions[node]] = destination
                yield tuple(candidate)

    beam = [initial_state]
    seen = {initial_state}
    explored = 0
    for depth in range(max_depth + 1):
        for state in beam:
            if goal(state):
                parts = unpack(state)
                return (
                    parts[:-1],
                    parts[-1],
                    {
                        "depth": int(depth),
                        "states_seen": int(len(seen)),
                        "explored": int(explored),
                    },
                )
        candidates = []
        for state in beam:
            for candidate in moves(state):
                explored += 1
                if candidate in seen:
                    continue
                seen.add(candidate)
                candidates.append(candidate)
        candidates.sort(key=score)
        beam = candidates[:beam_width]
        if not beam:
            break
    return None


def repair_closed_target_cores(
    closed,
    residual,
    *,
    target,
    floor,
    cap,
    tolerance,
    adjacency,
    weights,
    protected=(),
    residual_gateways=(),
):
    """Enforce closed-target-cores + one open residual without relaxing hard limits."""
    closed = [set(part) for part in closed]
    residual = set(residual)
    protected = set(protected or ())
    residual_gateways = set(residual_gateways or ())
    before = _partition_evidence(
        closed,
        residual,
        weights,
        target=target,
        floor=floor,
        cap=cap,
        tolerance=tolerance,
    )
    before_outliers = _core_outliers(
        closed,
        weights,
        target=target,
        floor=floor,
        cap=cap,
        tolerance=tolerance,
    )
    if not before_outliers:
        return closed, residual, {
            "status": "PASS",
            "strategy": "already_conformant",
            "before": before,
            "after": before,
        }
    if protected and not protected <= residual:
        raise SystemExit(
            "M04: CLOSED_CORE_TARGET_CONTRACT_BREACH protected nodes are not in the open residual"
        )
    if residual_gateways and not (residual & residual_gateways):
        raise SystemExit(
            "M04: CLOSED_CORE_TARGET_CONTRACT_BREACH open residual has no municipal gateway"
        )

    exact_status = "SKIPPED_SIZE"
    exact_detail = {}
    if len(set().union(*closed, residual)) <= 24 and len(closed) <= 6:
        exact, exact_status, exact_detail = _exact_repair(
            closed,
            residual,
            target=target,
            floor=floor,
            cap=cap,
            tolerance=tolerance,
            adjacency=adjacency,
            weights=weights,
            protected=protected,
            residual_gateways=residual_gateways,
        )
        if exact is not None:
            repaired_closed, repaired_residual = exact
            after = _partition_evidence(
                repaired_closed,
                repaired_residual,
                weights,
                target=target,
                floor=floor,
                cap=cap,
                tolerance=tolerance,
            )
            return repaired_closed, repaired_residual, {
                "status": "PASS",
                "strategy": "exact_connected_target_cores",
                "before": before,
                "after": after,
                "search": exact_detail,
            }
        if exact_status == "INCOMPATIBLE":
            raise SystemExit(
                "M04: CLOSED_CORE_TARGET_INCOMPATIBLE same-piece connected target cores do not exist "
                f"cores={len(closed)} nodes={len(set().union(*closed, residual))} detail={exact_detail}"
            )

    attempts = (
        (False, True, 4, 64, "beam_core_only_focused"),
        (False, False, 4, 128, "beam_core_only_broad"),
        (True, True, 4, 128, "beam_with_residual_focused"),
        (True, False, 4, 256, "beam_with_residual_broad"),
    )
    for allow_residual, focus_only, depth, width, strategy in attempts:
        result = _beam_repair(
            closed,
            residual,
            target=target,
            floor=floor,
            cap=cap,
            tolerance=tolerance,
            adjacency=adjacency,
            weights=weights,
            protected=protected,
            residual_gateways=residual_gateways,
            allow_residual=allow_residual,
            focus_only=focus_only,
            max_depth=depth,
            beam_width=width,
        )
        if result is None:
            continue
        repaired_closed, repaired_residual, search = result
        after = _partition_evidence(
            repaired_closed,
            repaired_residual,
            weights,
            target=target,
            floor=floor,
            cap=cap,
            tolerance=tolerance,
        )
        return repaired_closed, repaired_residual, {
            "status": "PASS",
            "strategy": strategy,
            "before": before,
            "after": after,
            "search": search,
            "exact_status": exact_status,
            "exact_detail": exact_detail,
        }

    raise SystemExit(
        "M04: CLOSED_CORE_TARGET_SEARCH_EXHAUSTED no conforming same-piece partition found within bounded search; "
        f"cores={len(closed)} nodes={len(set().union(*closed, residual))} "
        f"outliers={before_outliers} exact_status={exact_status} exact_detail={exact_detail}"
    )
