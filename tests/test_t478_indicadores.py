#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-478: indicadores por elección y sistema. Casos calculados a mano y escaños oficiales del BOE como literales."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "herramientas"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import indicadores_sistemas as ind  # noqa: E402

# Caso a mano: votos A 50, B 30, C 20; escaños A 6, B 4, C 0 (de 10).
VOTOS = {"A": 50, "B": 30, "C": 20}
ESCANOS = {"A": 6, "B": 4, "C": 0}


class Formulas(unittest.TestCase):
    def test_gallagher(self):
        # diferencias 10, 10, 20 puntos → raíz((100+100+400)/2) = raíz(300) = 17,3205
        self.assertAlmostEqual(ind.gallagher(VOTOS, ESCANOS), 17.320508, places=5)

    def test_gallagher_proporcional_es_cero(self):
        self.assertEqual(ind.gallagher({"A": 2, "B": 2}, {"A": 1, "B": 1}), 0.0)

    def test_loosemore_hanby(self):
        # (10 + 10 + 20) / 2 = 20 puntos
        self.assertAlmostEqual(ind.loosemore_hanby(VOTOS, ESCANOS), 20.0, places=9)

    def test_loosemore_hanby_reparto_territorial(self):
        # población 100 y 300 (25 % y 75 %), 2 y 2 escaños (50 % y 50 %) → (25 + 25) / 2 = 25 puntos
        self.assertAlmostEqual(ind.loosemore_hanby({"p1": 100, "p2": 300}, {"p1": 2, "p2": 2}), 25.0, places=9)

    def test_numero_efectivo(self):
        self.assertAlmostEqual(ind.numero_efectivo(VOTOS), 1 / 0.38, places=9)   # 2,6316
        self.assertAlmostEqual(ind.numero_efectivo(ESCANOS), 1 / 0.52, places=9)  # 1,9231
        self.assertEqual(ind.numero_efectivo({}), 0.0)

    def test_prima_al_ganador(self):
        p = ind.prima_ganador(VOTOS, ESCANOS)
        self.assertEqual(p["candidatura"], "A")
        self.assertAlmostEqual(p["pct_votos"], 50.0)
        self.assertAlmostEqual(p["pct_escanos"], 60.0)
        self.assertAlmostEqual(p["prima"], 10.0)
        self.assertFalse(p["mayoria_fabricada"])  # 60 % de escaños con 50 % de votos no es «fabricada» (no < 50)

    def test_mayoria_fabricada(self):
        p = ind.prima_ganador({"A": 40, "B": 35, "C": 25}, {"A": 3, "B": 1, "C": 0})
        self.assertTrue(p["mayoria_fabricada"])  # 75 % de escaños con 40 % de votos

    def test_votos_sin_representacion(self):
        # circ. 1: A 60, B 40, escaño A → 40 sin representar; circ. 2: A 30, B 70, escaño B → 30. 70 / 200 = 35 %
        circs = [({"A": 60, "B": 40}, {"A": 1}), ({"A": 30, "B": 70}, {"B": 1})]
        self.assertAlmostEqual(ind.votos_sin_representacion(circs), 35.0, places=9)

    def test_mayoria_simple_empate_alfabetico(self):
        self.assertEqual(ind.ganador_mayoria_simple({"B": 10, "A": 10, "C": 3}), "A")


class SistemaReal(unittest.TestCase):
    """Escaños oficiales (BOE-A-2023-18907 y BOE-A-2011-19391) pasados a partido homologado por la herramienta."""

    @classmethod
    def setUpClass(cls):
        cls.e23 = ind.escanos_reales("202307")
        cls.e11 = ind.escanos_reales("201111")

    def test_total_350(self):
        for e in (self.e23, self.e11):
            self.assertEqual(sum(sum(d.values()) for d in e.values()), 350)
            self.assertEqual(len(e), 52)

    def test_2023_literales_boe(self):
        tot = ind.sumar(self.e23.values())
        self.assertEqual(tot["PP"], 137)
        self.assertEqual(tot["PSOE"], 121)  # PSOE + PSC + PSE-EE + PSdeG en el BOE
        self.assertEqual(tot["VOX"], 33)

    def test_2023_madrid_37(self):
        self.assertEqual(sum(self.e23["28"].values()), 37)


if __name__ == "__main__":
    unittest.main()
