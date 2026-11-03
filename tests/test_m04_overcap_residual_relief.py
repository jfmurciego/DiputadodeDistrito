"""T-22: el residuo R que absorbe enclaves sobre el techo cede secciones a núcleos U."""
import unittest

import pandas as pd

from ddd_core.m04_overcap_residual_relief import relieve_overcap_residuals

POP = {"a1": 50, "a2": 40, "r1": 20, "r2": 30, "r3": 30, "e": 40}
EDGES = [("a1", "a2"), ("a2", "r1"), ("r1", "r2"), ("r2", "r3"), ("r3", "e")]


def _frame():
    rows = [
        ("a1", "M", "M:U1", 1, True), ("a2", "M", "M:U1", 1, True),
        ("r1", "M", "M:R", 2, False), ("r2", "M", "M:R", 2, False),
        ("r3", "M", "M:R", 2, False), ("e", "E", "E", 2, False),
    ]
    return pd.DataFrame(rows, columns=["CUSEC", "CUMUN", "ddd_unit_id", "district_id", "ddd_closed_urban"])


def _adj():
    adj = {n: set() for n in POP}
    for u, v in EDGES:
        adj[u].add(v)
        adj[v].add(u)
    return adj


def _dist_pop(g):
    return g.assign(p=g.CUSEC.map(POP)).groupby("district_id").p.sum().to_dict()


class OvercapResidualRelief(unittest.TestCase):
    def test_residual_with_enclave_over_cap_cedes_to_core(self):
        g = _frame()
        self.assertEqual(_dist_pop(g)[2], 120)  # rojo: R+enclave sobre techo 115
        moves = relieve_overcap_residuals(
            g, pop=POP, adj=_adj(), cap=115, core_low=85, core_high=115,
            id_field="CUSEC", municipality_field="CUMUN")
        self.assertEqual([m["section"] for m in moves], ["r1"])
        self.assertEqual(_dist_pop(g), {1: 110, 2: 100})
        row = g[g.CUSEC == "r1"].iloc[0]
        self.assertEqual((row.ddd_unit_id, row.district_id, bool(row.ddd_closed_urban)), ("M:U1", 1, True))

    def test_no_move_when_core_would_exceed_limit(self):
        g = _frame()
        moves = relieve_overcap_residuals(
            g, pop=POP, adj=_adj(), cap=115, core_low=85, core_high=105,
            id_field="CUSEC", municipality_field="CUMUN")
        self.assertEqual(moves, [])
        self.assertEqual(_dist_pop(g)[2], 120)

    def test_protected_section_is_not_moved(self):
        g = _frame()
        moves = relieve_overcap_residuals(
            g, pop=POP, adj=_adj(), cap=115, core_low=85, core_high=115,
            id_field="CUSEC", municipality_field="CUMUN", protected={"r1"})
        self.assertEqual(moves, [])


def _run(rows, pop, edges, **kw):
    g = pd.DataFrame(rows, columns=["CUSEC", "CUMUN", "ddd_unit_id", "district_id", "ddd_closed_urban"])
    adj = {n: set() for n in pop}
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    moves = relieve_overcap_residuals(g, pop=pop, adj=adj, cap=115, core_low=85, core_high=115,
                                      id_field="CUSEC", municipality_field="CUMUN", **kw)
    return g, moves, g.assign(p=g.CUSEC.map(pop)).groupby("district_id").p.sum().to_dict()


class OvercapAtomicBlock(unittest.TestCase):
    def test_whole_municipality_moves_to_neighbouring_residual_district(self):
        # Madrid: bloque de municipios enteros sobre el techo junto a un residuo puro de otro municipio.
        pop = {"s1": 40, "s2": 35, "r1": 40, "r2": 40, "a": 60, "b": 60}
        rows = [("s1", "S", "S:U1", 1, True), ("s2", "S", "S:U1", 1, True),
                ("r1", "S", "S:R", 2, False), ("r2", "S", "S:R", 2, False),
                ("a", "A", "A:M", 3, False), ("b", "B", "B:M", 3, False)]
        edges = [("s1", "s2"), ("s2", "r1"), ("r1", "r2"), ("r2", "a"), ("a", "b")]
        g, moves, dp = _run(rows, pop, edges)
        self.assertEqual([m["kind"] for m in moves], ["unit_to_residual_district", "residual_to_core"])
        self.assertEqual(dp, {1: 115, 2: 100, 3: 60})

    def test_full_core_passes_section_to_other_core(self):
        pop = {"t1": 90, "s1": 20, "s3": 30, "s2": 60, "r1": 10, "r2": 40, "e": 70}
        rows = [("t1", "S", "S:U2", 4, True), ("s1", "S", "S:U1", 1, True), ("s3", "S", "S:U1", 1, True),
                ("s2", "S", "S:U1", 1, True), ("r1", "S", "S:R", 2, False), ("r2", "S", "S:R", 2, False),
                ("e", "E", "E:M", 2, False)]
        edges = [("t1", "s1"), ("s1", "s3"), ("s3", "s2"), ("s2", "r1"), ("r1", "r2"), ("r2", "e")]
        g, moves, dp = _run(rows, pop, edges)
        self.assertEqual([m["kind"] for m in moves], ["core_to_core", "residual_to_core"])
        self.assertEqual(dp, {1: 100, 2: 110, 4: 110})


if __name__ == "__main__":
    unittest.main()
