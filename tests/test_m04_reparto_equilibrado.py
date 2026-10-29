"""DDD regression 1.0.0, 2026-10-29: M04 7.4.15 reintento equilibrado solo si la búsqueda secuencial se agota.

Origen: Cartagena (Murcia, run 40773421805).
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _chain(weights):
    adj = {i: set() for i in weights}
    for i in range(len(weights) - 1):
        adj[i].add(i + 1)
        adj[i + 1].add(i)
    return adj


class BalancedLookaheadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.new = _load("ddd_core/m04_seed_engine_v7410.py", "m04_v7415")
        cls.old = _load("legacy/ddd_core/m04_seed_engine_v7.4.14_pre_balanced_lookahead.py", "m04_v7414")

    def test_exhausted_greedy_search_is_rescued_by_balanced_aim(self):
        w = {0: 20, 1: 10, 2: 8, 3: 10, 4: 20, 5: 5, 6: 12, 7: 5, 8: 5}
        adj = _chain(w)
        with self.assertRaises(SystemExit):
            self.old.split_sequential(set(w), 25, 21.25, 28.75, 0.15, adj, w)
        closed, residual, mode = self.new.split_sequential(set(w), 25, 21.25, 28.75, 0.15, adj, w)
        self.assertIn("balanced_lookahead", mode)
        self.assertEqual(set().union(*closed) | residual, set(w))
        self.assertTrue(all(21.25 <= sum(w[n] for n in c) <= 28.75 for c in closed))

    def test_partitions_that_already_succeed_are_unchanged(self):
        w = {0: 10, 1: 15, 2: 10, 3: 15, 4: 10, 5: 15}
        adj = _chain(w)
        args = (set(w), 25, 21.25, 28.75, 0.15, adj, w)
        self.assertEqual(self.new.split_sequential(*args), self.old.split_sequential(*args))


if __name__ == "__main__":
    unittest.main()
