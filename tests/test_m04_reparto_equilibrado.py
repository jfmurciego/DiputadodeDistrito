"""DDD regression 1.2.0, 2026-10-29: M04 7.4.15/7.4.16/7.4.17 reintentos solo si la búsqueda secuencial se agota.

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


def _greedy(w, target, floor, cap, adj, balanced=False):
    """Ruta 7.4.14 (balanced=False) o reintento 7.4.15 (balanced=True), sin crecimiento conexo."""
    mp = sum(w.values())
    lo = max(1, int(math.ceil(max(0.0, mp - cap) / cap)))
    hi = min(len(w) - 1, int(math.floor(mp / floor)))
    for count in range(lo, hi + 1):
        result, _ = engine._sequential_count(set(w), count, target, floor, cap, adj, w, set(), set(), balanced=balanced)
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

    def test_connected_growth_rescues_cores_that_bfs_prefixes_cannot_close(self):
        # Rejilla 4x3 sin las aristas 3-4 y 6-7: los prefijos BFS cortan el resto; el crecimiento conexo no.
        w = {0: 15, 1: 5, 2: 10, 3: 5, 4: 3, 5: 15, 6: 5, 7: 15, 8: 15, 9: 15, 10: 3, 11: 5}
        edges = [(0, 1), (0, 3), (1, 2), (1, 4), (2, 5), (3, 6), (4, 5), (4, 7), (5, 8),
                 (6, 9), (7, 8), (7, 10), (8, 11), (9, 10), (10, 11)]
        adj = {n: set() for n in w}
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        self.assertIsNone(_greedy(w, 25, 21.25, 28.75, adj))
        self.assertIsNone(_greedy(w, 25, 21.25, 28.75, adj, balanced=True))
        closed, residual, mode = engine.split_sequential(set(w), 25, 21.25, 28.75, 0.15, adj, w)
        self.assertIn("connected_growth", mode)
        self.assertEqual(set().union(*closed) | residual, set(w))
        self.assertTrue(all(21.25 <= sum(w[n] for n in c) <= 28.75 for c in closed))
        self.assertTrue(all(engine.connected(c, adj) for c in closed))
        self.assertTrue(engine.connected(residual, adj))

    def test_residual_first_gathers_scattered_protected_units(self):
        # Rejilla 6x6 con protegidas en esquinas opuestas: el residuo debe reunirlas.
        w = {r * 6 + c: 5 for r in range(6) for c in range(6)}
        adj = {n: set() for n in w}
        for n in w:
            if n % 6 != 5:
                adj[n].add(n + 1); adj[n + 1].add(n)
            if n + 6 in w:
                adj[n].add(n + 6); adj[n + 6].add(n)
        protected = {0, 5}
        result, reason = engine.split_residual_first(set(w), 30, 25.5, 52.5, 0.15, adj, w, protected, set())
        self.assertIsNotNone(result, reason)
        closed, residual, mode = result
        self.assertIn("residual_first_global", mode)
        self.assertTrue(protected <= residual)
        self.assertTrue(engine.connected(residual, adj))
        self.assertLessEqual(sum(w[n] for n in residual), 52.5)
        self.assertEqual(set().union(*closed) | residual, set(w))
        self.assertTrue(all(25.5 <= sum(w[n] for n in c) <= 52.5 and engine.connected(c, adj) for c in closed))

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
