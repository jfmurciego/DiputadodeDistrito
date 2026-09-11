#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba R016 de refinamiento post-factibilidad
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Refinamiento después de fuera_12=0
FECHA: 2026-09-11
ESTADO: candidato R016
FUNCIÓN: demostrar que M05 continúa el recocido después de la primera solución dentro de ±12 % y conserva una solución canónica igual o mejor.
CAMBIOS: primera versión.
MOTIVO: impedir que reaparezca la parada prematura de M05 v7.3.x.
ORIGEN: R016
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.test_r015_invariantes import M05Determinism


class M05RefinementAfterFeasible(unittest.TestCase):
    def test_continua_despues_de_primera_factibilidad(self):
        helper = M05Determinism(methodName="test_m05_misma_semilla_misma_salida")
        with tempfile.TemporaryDirectory() as td:
            cfg, output, report = helper.make_case(Path(td), "r016")
            helper.run_case(cfg)
            rep = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(rep["version"], "7.4.0")
            self.assertIsNotNone(rep["first_feasible_iteration"])
            self.assertGreater(rep["post_feasible_iterations"], 0)
            self.assertEqual(rep["anneal_iterations_executed"], 500)
            self.assertEqual(rep["districts_outside_tolerance"], 0)
            self.assertLessEqual(tuple(rep["objective_final"]), tuple(rep["objective_first_feasible"]))


if __name__ == "__main__":
    unittest.main()
