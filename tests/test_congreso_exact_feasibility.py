from ddd_core.congreso_exact_feasibility import solve_bounded_connected_partition


def test_path_four_has_exact_connected_bounded_partition():
    nodes = ["a", "b", "c", "d"]
    graph = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c"}}
    result = solve_bounded_connected_partition(
        nodes, graph, {node: 40 for node in nodes}, k=2, floor=80, cap=80
    )
    assert result.status == "SOLUTION_FOUND"
    assert result.proof == "EXACT_CONNECTED_COVER_WITNESS"
    assert result.groups == (("a", "b"), ("c", "d"))
    assert sorted(node for group in result.groups for node in group) == nodes


def test_exhaustive_small_failure_is_certified_not_heuristic():
    nodes = ["a", "b", "c"]
    graph = {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
    result = solve_bounded_connected_partition(
        nodes, graph, {node: 4 for node in nodes}, k=2, floor=5, cap=7
    )
    assert result.status == "PROVEN_INFEASIBLE"
    assert result.proof == "EXHAUSTIVE_CONNECTED_EXACT_COVER"
    assert result.certificate["proof_complete"] is True
    assert result.certificate["search_exhaustive"] is True
    assert result.certificate["input_sha256"] == result.input_sha256
    assert result.explored_groups > 0
    assert result.explored_states > 0


def test_budget_exhaustion_never_claims_impossibility():
    nodes = ["a", "b", "c", "d"]
    graph = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c"}}
    group_limited = solve_bounded_connected_partition(
        nodes, graph, {node: 40 for node in nodes}, k=2, floor=80, cap=80,
        max_groups=2,
    )
    assert group_limited.status == "SEARCH_EXHAUSTED"
    assert group_limited.proof == "CONNECTED_GROUP_BUDGET"

    state_limited = solve_bounded_connected_partition(
        nodes, graph, {node: 40 for node in nodes}, k=2, floor=80, cap=80,
        max_states=1,
    )
    assert state_limited.status == "SEARCH_EXHAUSTED"
    assert state_limited.proof == "EXACT_COVER_STATE_BUDGET"


def test_group_budget_includes_initial_singletons():
    result = solve_bounded_connected_partition(
        ["a", "b"], {"a": set(), "b": set()}, {"a": 1, "b": 1},
        k=2, floor=1, cap=1, max_groups=1,
    )
    assert result.status == "SEARCH_EXHAUSTED"
    assert result.proof == "CONNECTED_GROUP_BUDGET"
    assert result.explored_groups == 2
    assert result.certificate["search_exhaustive"] is False


def test_arithmetic_certificate_is_exact_and_result_digest_deterministic():
    nodes = ["x", "y"]
    graph = {"x": {"y"}, "y": {"x"}}
    args = (nodes, graph, {"x": 2, "y": 3})
    first = solve_bounded_connected_partition(*args, k=2, floor=3, cap=4)
    second = solve_bounded_connected_partition(*args, k=2, floor=3, cap=4)
    assert first.status == "PROVEN_INFEASIBLE"
    assert first.proof == "TOTAL_POPULATION_OUTSIDE_K_BOUNDS"
    assert first.certificate["proof_complete"] is True
    assert first.certificate["search_exhaustive"] is False
    assert first.input_sha256 == second.input_sha256
    assert first.certificate["minimum_total"] == 6
    assert first.certificate["maximum_total"] == 8


def test_rejects_non_symmetric_or_boolean_population_input():
    try:
        solve_bounded_connected_partition(
            ["a", "b"], {"a": {"b"}, "b": set()}, {"a": 1, "b": 1},
            k=1, floor=2, cap=2,
        )
    except ValueError as exc:
        assert "symmetric" in str(exc)
    else:
        raise AssertionError("asymmetric graph must be rejected")

    try:
        solve_bounded_connected_partition(
            ["a"], {"a": set()}, {"a": True}, k=1, floor=0, cap=1,
        )
    except ValueError as exc:
        assert "non-negative integer" in str(exc)
    else:
        raise AssertionError("bool must not be accepted as an integer population")


# Bridge function-style regressions into the repository's unittest CI.
def load_tests(loader, tests, pattern):
    import unittest

    suite = unittest.TestSuite()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn, description=name))
    return suite
