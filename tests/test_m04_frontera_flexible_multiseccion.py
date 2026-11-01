# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: test de la frontera flexible multisección de M04
VERSIÓN: 1.0.0
FECHA: 2026-11-01
FUNCIÓN: comprobar que M04 7.6.0 encuentra un bloque conexo de secciones fronterizas
cuando ninguna sección individual cubre el déficit del residual (Congreso Álava, T-02).
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("m04_entry", ROOT / "modulos/04_generar_semillas.py")
m04 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m04)


def grid(w, h):
    adj = {}
    for x in range(w):
        for y in range(h):
            n = f"{x}_{y}"
            adj[n] = set()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < w and 0 <= y + dy < h:
                    adj[n].add(f"{x+dx}_{y+dy}")
    return adj


class FronteraMultiseccion(unittest.TestCase):
    def setUp(self):
        # Donante: columnas 0-3 (16 secciones de 1.000); receptor: columna 4.
        self.adj = grid(5, 4)
        self.pop = {n: 1000 for n in self.adj}
        self.donor = {n for n in self.adj if int(n.split("_")[0]) < 4}
        self.recv = set(self.adj) - self.donor
        self.dn = lambda d: self.donor if d == 0 else self.recv
        self.dp = lambda d: sum(self.pop[n] for n in self.dn(d))

    def test_bloque_conexo_cubre_deficit(self):
        best = m04._connected_frontier_block(
            self.donor, set(), [1], self.dn, self.dp, self.pop, self.adj,
            deficit=2500, donor_slack=6000, hi=10000,
        )
        self.assertIsNotNone(best)
        _, block, q, total = best
        self.assertEqual(q, 1)
        self.assertEqual(total, 3000)
        self.assertTrue(m04.connected(block, self.adj))
        self.assertTrue(m04.connected(self.donor - block, self.adj))
        self.assertTrue(all(n.startswith("3_") for n in block))

    def test_respeta_slack_y_techo(self):
        self.assertIsNone(m04._connected_frontier_block(
            self.donor, set(), [1], self.dn, self.dp, self.pop, self.adj,
            deficit=2500, donor_slack=2000, hi=10000,
        ))
        self.assertIsNone(m04._connected_frontier_block(
            self.donor, set(), [1], self.dn, self.dp, self.pop, self.adj,
            deficit=2500, donor_slack=6000, hi=5500,
        ))

    def test_no_usa_secciones_puente(self):
        bridges = {f"3_{y}" for y in range(4)}
        self.assertIsNone(m04._connected_frontier_block(
            self.donor, bridges, [1], self.dn, self.dp, self.pop, self.adj,
            deficit=2500, donor_slack=6000, hi=10000,
        ))


if __name__ == "__main__":
    unittest.main()
