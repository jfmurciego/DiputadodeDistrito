#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: integridad de evidencia publicada R016
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Baseline Run #9
FECHA: 2026-09-11
ESTADO: vigente
FUNCIÓN: proteger la evidencia publicada R016 comparando Run #9 con Run #8.
CAMBIOS: migra las comparaciones R016 a la evidencia territorial canónica única.
MOTIVO: convertir la mejora de R016 en una regresión automática y evitar volver al máximo desvío de Run #8.
ORIGEN: R016 / GitHub Run #9 34599224954
ANTERIOR: legacy/tests/test_r016_evidencia_publicada_v1.0.0.py
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN8 = ROOT / "territorios" / "aragon" / "resultados" / "ejecuciones" / "gh-34592470470-1"
RUN9 = ROOT / "territorios" / "aragon" / "resultados" / "ejecuciones" / "gh-34599224954-1"


class R016EvidenciaPublicada(unittest.TestCase):
    """No reejecuta el pipeline. La regresión real vive en GitHub Actions."""
    @classmethod
    def setUpClass(cls):
        cls.r8 = json.loads((RUN8 / "M05" / "aragon_2025_m05_informe.json").read_text(encoding="utf-8"))
        cls.r9 = json.loads((RUN9 / "M05" / "aragon_2025_m05_informe.json").read_text(encoding="utf-8"))
        cls.val = json.loads((RUN9 / "VALIDACION.json").read_text(encoding="utf-8"))

    def test_run9_es_pass_territorial(self):
        self.assertEqual(self.val["estado"], "PASS")
        self.assertEqual(self.val["districts_found"], 67)
        self.assertEqual(self.val["sections"], 1463)
        self.assertEqual(self.val["total_population"], 1364621.0)
        self.assertEqual(self.val["province_district_counts"], {"22": 11, "44": 7, "50": 49})
        self.assertEqual(self.val["below_floor"], [])
        self.assertEqual(self.val["above_cap"], [])
        self.assertEqual(self.val["graph_disconnected"], [])
        self.assertEqual(self.val["province_crossings"], [])
        self.assertEqual(self.val["municipality_violations"], [])
        self.assertEqual(self.val["failures"], [])

    def test_r016_continua_despues_de_primera_factibilidad(self):
        self.assertEqual(self.r9["version"], "7.4.0")
        self.assertEqual(self.r9["districts_outside_tolerance"], 0)
        self.assertEqual(self.r9["first_feasible_iteration"], 9038)
        self.assertEqual(self.r9["anneal_iterations_executed"], 20000)
        self.assertEqual(self.r9["post_feasible_iterations"], 10962)
        self.assertEqual(self.r9["objective_first_feasible"], self.r8["objective_final"])
        self.assertLess(tuple(self.r9["objective_final"]), tuple(self.r9["objective_first_feasible"]))

    def test_r016_mejora_run8(self):
        self.assertLess(self.r9["best_max_rel_dev"], self.r8["best_max_rel_dev"])
        self.assertLess(self.r9["objective_final"][4], self.r8["objective_final"][4])
        self.assertAlmostEqual(self.r9["best_max_rel_dev"], 0.099299365905, places=12)
        self.assertAlmostEqual(self.r9["objective_final"][4], 0.161271162560, places=12)


if __name__ == "__main__":
    unittest.main()
