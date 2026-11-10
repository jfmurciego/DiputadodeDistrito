#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · competidor como sustituto de M05: lógica de semilla inicial de GerryChain (sin ejecutar M05 real)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.competicion import Salida  # noqa: E402
from ddd_motor2.competidor import CanonicoM05, GerryChainM05  # noqa: E402


class PasoFalso:
    params, run_id = "p.yaml", "r"
    s5 = {"out_geojson": "/x/t_m05_distritos_optimizados.geojson.zip"}

    def __init__(self, baseline_rc):
        self.baseline_rc, self.ordenes = baseline_rc, []

    def run(self, cmd):
        self.ordenes.append(cmd)
        return self.baseline_rc

    def m05_y_m06(self, cmd, destino, extra):
        self.ordenes.append(cmd)
        return Salida(Path(destino) / "comp.csv", extra=extra)


class Competidor(unittest.TestCase):
    def test_m04_admisible_sin_initial(self):
        p = PasoFalso(0)
        gc = GerryChainM05(p, CanonicoM05(p))
        gc.generar(None, 11, Path("/d1"))
        gc.generar(None, 12, Path("/d2"))
        self.assertEqual(sum("--validate-baseline-only" in c for c in p.ordenes), 1)  # una vez por territorio
        cadenas = [c for c in p.ordenes if "--seed-base" in c]
        self.assertEqual([c[c.index("--seed-base") + 1] for c in cadenas], ["11", "12"])
        self.assertFalse(any("--initial" in c for c in cadenas))

    def test_m04_no_admisible_parte_del_canonico(self):
        p = PasoFalso(1)
        can = CanonicoM05(p)
        gc = GerryChainM05(p, can)
        self.assertEqual(gc.generar(None, 5, Path("/d")).estado, "SIN_SEMILLA")
        can.generar(None, None, Path("/c"))
        s = gc.generar(None, 5, Path("/d"))
        self.assertEqual(s.extra["semilla_inicial"], "canonica")
        self.assertIn(str(Path("/c/t_m05_distritos_optimizados.geojson.zip")), p.ordenes[-1])


if __name__ == "__main__":
    unittest.main()
