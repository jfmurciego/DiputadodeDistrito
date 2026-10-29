"""DDD regression 1.0.0, 2026-10-29: M04 7.4.15 reintento equilibrado solo si la búsqueda secuencial se agota.

Origen: Cartagena (Murcia, run 40773421805).
"""
import math
import unittest

from ddd_core import m04_seed_engine_v7410 as engine


def _chain(weights):
    adj = {i: set() for i in weights}
    for i in range(len(weights) - 1):
        adj[i].add(i + 1)
        adj[i + 1].add(i)
    return adj


def _greedy(w, target, floor, cap, adj):
    """Ruta 7.4.14: solo objetivo fijo por núcleo."""
    mp = sum(w.values())
    lo = max(1, int(math.ceil(max(0.0, mp - cap) / cap)))
    hi = min(len(w) - 1, int(math.floor(mp / floor)))
    for count in range(lo, hi + 1):
        result, _ = engine._sequential_count(set(w), count, target, floor, cap, adj, w, set(), set())
        if result is not None:
            return result
    return None


class BalancedLookaheadTests(unittest.TestCase):
    def test_exhausted_greedy_search_is_rescued_by_balanced_aim(self):
        w = {0: 20, 1: 10, 2: 8, 3: 10, 4: 20, 5: 5, 6: 12, 7: 5, 8: 5}
        adj = _chain(w)
        self.assertIsNone(_greedy(w, 25, 21.25, 28.75, adj))
        closed, residual, mode = engine.split_sequential(set(w), 25, 21.25, 28.75, 0.15, adj, w)
        self.assertIn("balanced_lookahead", mode)
        self.assertEqual(set().union(*closed) | residual, set(w))
        self.assertTrue(all(21.25 <= sum(w[n] for n in c) <= 28.75 for c in closed))

    def test_partitions_that_already_succeed_are_unchanged(self):
        w = {0: 10, 1: 15, 2: 10, 3: 15, 4: 10, 5: 15}
        adj = _chain(w)
        expected = _greedy(w, 25, 21.25, 28.75, adj)
        self.assertIsNotNone(expected)
        result = engine.split_sequential(set(w), 25, 21.25, 28.75, 0.15, adj, w)
        self.assertNotIn("balanced_lookahead", result[2])
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
