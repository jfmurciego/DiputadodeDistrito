"""M04 administrative atomic groups regression, version 1.0.0, 2026-10-26.

Scope: physical connectors of complete municipalities, no topology relaxation.
Status: candidate. Origin: new tests plus exact graph from run 40200428904.
"""
import json
from pathlib import Path
import unittest

from ddd_core.m04_administrative_atomic_groups import (
    AtomicConnectorSearchBlocked, connected_atomic_municipality_groups,
)

ROOT = Path(__file__).resolve().parents[1]


def adjacency(nodes, edges):
    result = {n: set() for n in nodes}
    for left, right in edges:
        result[left].add(right)
        result[right].add(left)
    return result


class AdministrativeAtomicGroupsTests(unittest.TestCase):
    def setUp(self):
        self.groups = {"00001": {"a", "b"}, "00002": {"c", "d"}}
        self.pop = {"a": 2, "b": 3, "c": 5, "d": 1}
        self.adj = adjacency(self.pop, [("a", "c"), ("b", "c"), ("c", "d")])
        self.declaration = [{"admin_scope": "municipality:00001", "components": [["a"], ["b"]]}]

    def test_connector_keeps_whole_municipality_without_adding_edges(self):
        before = {n: set(v) for n, v in self.adj.items()}
        result, audit = connected_atomic_municipality_groups(
            self.groups, self.adj, self.pop, self.declaration, atomic_limit=11,
        )
        self.assertEqual(result, [(('00001', '00002'), set(self.pop))])
        self.assertEqual(self.adj, before)
        self.assertEqual(audit[0]["population"], 11)
        self.assertEqual(audit[0]["added_edges"], 0)

    def test_missing_accreditation_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unaccredited"):
            connected_atomic_municipality_groups(self.groups, self.adj, self.pop, [], atomic_limit=20)

    def test_stale_component_membership_fails_closed(self):
        bad = [{"admin_scope": "municipality:00001", "components": [["a"], ["b", "c"]]}]
        with self.assertRaisesRegex(ValueError, "stale"):
            connected_atomic_municipality_groups(self.groups, self.adj, self.pop, bad, atomic_limit=20)

    def test_connector_cannot_split_municipality_to_satisfy_hard_cap(self):
        # Taking only c would fit cap=10, but taking all of its municipality does not.
        with self.assertRaisesRegex(AtomicConnectorSearchBlocked, "no_connector_within_atomic_limit"):
            connected_atomic_municipality_groups(self.groups, self.adj, self.pop, self.declaration, atomic_limit=10)

    def test_point_contact_is_not_promoted_to_graph_edge(self):
        self.adj["b"].remove("c")
        self.adj["c"].remove("b")
        with self.assertRaisesRegex(AtomicConnectorSearchBlocked, "no_connector_within_atomic_limit"):
            connected_atomic_municipality_groups(self.groups, self.adj, self.pop, self.declaration, atomic_limit=20)

    def test_search_limit_is_distinguished_from_exhausted_search(self):
        with self.assertRaisesRegex(AtomicConnectorSearchBlocked, "reason=search_limit"):
            connected_atomic_municipality_groups(
                self.groups, self.adj, self.pop, self.declaration, atomic_limit=20, max_states=1,
            )

    def test_connected_baseline_is_unchanged(self):
        self.adj["a"].add("b")
        self.adj["b"].add("a")
        result, audit = connected_atomic_municipality_groups(self.groups, self.adj, self.pop, [], atomic_limit=20)
        self.assertEqual(result, [(('00001',), {'a', 'b'}), (('00002',), {'c', 'd'})])
        self.assertEqual(audit, [])

    def test_real_tremp_connector_uses_original_physical_graph(self):
        fixture = json.loads((ROOT / "tests/fixtures/m04_administrative_components/tremp_run_40200428904.json").read_text())
        pop = fixture["populations"]
        adj = adjacency(pop, fixture["physical_edges"])
        self.assertNotIn("2523403001", adj["2523401002"])
        groups = {m: set(nodes) for m, nodes in fixture["municipalities"].items()}
        limit = fixture["population_total"] / fixture["k"] * fixture["atomic_ratio"]
        result, audit = connected_atomic_municipality_groups(
            groups, adj, pop, [fixture["declaration"]], atomic_limit=limit,
        )
        self.assertEqual(result, [(('25215', '25234'), set(pop))])
        self.assertEqual(len(pop), 6)
        self.assertEqual(sum(pop.values()), 6597)
        self.assertEqual(audit[0]["result_components"], 1)
        self.assertEqual(audit[0]["added_edges"], 0)


if __name__ == "__main__":
    unittest.main()
