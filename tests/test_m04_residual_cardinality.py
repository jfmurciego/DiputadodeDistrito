"""DDD regression 1.0.0, 2026-10-26: preserve residual atomic cardinality.

Origin: executor C; initial formation must reserve one unit per pending district.
"""
import unittest
import json
from pathlib import Path

from ddd_core import m04_seed_engine_v7410 as engine
from ddd_core import m04_seed_engine as canonical


class ResidualCardinalityTests(unittest.TestCase):
    def test_canarias_original_reconsiders_core_count_without_relaxing_limits(self):
        path = Path(__file__).parent / "fixtures/m04_residual_cardinality/canarias_lalaguna_run_40241596981.json"
        case = json.loads(path.read_text())
        nodes, weights = set(case["nodes"]), case["weights"]
        adjacency = {n: set(v) for n, v in case["adjacency"].items()}
        cores, residual, mode, gateways = engine.partition_oversized_municipality(
            nodes, case["target"], case["floor"], case["cap"], case["tol"],
            adjacency, weights, protected=set(case["protected"]),
        )
        self.assertIn("reconsidered_core_count:2->3", mode)
        parts = cores + [residual]
        self.assertEqual(set.union(*parts), nodes)
        self.assertEqual(sum(map(len, parts)), len(nodes))
        self.assertTrue(set(case["protected"]) <= residual)
        self.assertTrue(residual & gateways)
        self.assertTrue(all(engine.connected(part, adjacency) for part in parts))
        self.assertTrue(all(case["floor"] <= sum(weights[n] for n in part) <= case["cap"] for part in parts))

    def test_ceuta_original_exact_proof_returns_executable_25_districts(self):
        path = Path(__file__).parent / "fixtures/m04_residual_cardinality/ceuta_run_40241776365.json"
        fixture = json.loads(path.read_text())
        weights = {str(node["id"]): int(node["pop"]) for node in fixture["nodes"]}
        adjacency = {node: set() for node in weights}
        for edge in fixture["edges"]:
            adjacency[edge["u"]].add(edge["v"])
            adjacency[edge["v"]].add(edge["u"])
        target = sum(weights.values()) / fixture["k"]
        floor, cap = target * .8, target * 1.75
        groups, _ = canonical._enumerate_connected_hard_groups(
            weights, adjacency, weights, floor=floor, cap=cap,
        )
        parts, _ = canonical._exact_connected_hard_partition(
            weights, groups, weights, k=25, floor=floor, cap=cap,
            return_partition=True,
        )
        self.assertEqual(len(parts), 25)
        self.assertEqual(sum(map(len, parts)), len(weights))
        self.assertEqual(set.union(*parts), set(weights))
        self.assertTrue(all(engine.connected(part, adjacency) for part in parts))
        self.assertTrue(all(floor <= sum(weights[n] for n in part) <= cap for part in parts))

    def test_peel_reconsiders_extraction_that_consumes_pending_districts(self):
        weights = dict(enumerate([5, 7, 9, 20, 21, 2]))
        nodes = set(weights)
        adjacency = {i: {i - 1, i + 1} & nodes for i in nodes}
        parts = engine.hybrid_partition(nodes, 6, adjacency, weights)
        self.assertEqual(len(parts), 6)
        self.assertEqual(set.union(*parts), nodes)
        self.assertTrue(all(len(part) == 1 for part in parts))
        self.assertTrue(all(engine.connected(part, adjacency) for part in parts))

    def test_impossible_cardinality_has_explicit_structural_decision(self):
        for partition in (engine.hybrid_partition, engine.grow_partition):
            with self.subTest(partition=partition.__name__):
                with self.assertRaisesRegex(SystemExit, "INSUFFICIENT_ATOMIC_UNITS"):
                    partition({0, 1}, 3, {0: {1}, 1: {0}}, {0: 4, 1: 7})

    def test_zero_and_empty_cardinalities_are_rejected_explicitly(self):
        for nodes, k in ((set(), 1), ({0}, 0), ({0}, -1)):
            with self.subTest(nodes=nodes, k=k):
                with self.assertRaisesRegex(SystemExit, "INVALID_PARTITION_CARDINALITY"):
                    engine.hybrid_partition(nodes, k, {0: set()}, {0: 1})


if __name__ == "__main__":
    unittest.main()
