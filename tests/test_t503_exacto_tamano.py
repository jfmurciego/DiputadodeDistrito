#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: tests de T-503 (Deslinde 1.2): el exacto se aplica por tamaño (átomos × K ≤ 2.000) y huella_resultado
  no lleva las cotas de las etapas de CP-SAT que no cierran
VERSIÓN: 1.0.0
FECHA: 2026-11-26
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: T-502 (#1029): con K=16 (Sevilla) el exacto no se aplicaba por K_MAX=4; y la cota de una etapa abierta cambia
  entre ejecuciones, así que la huella no se repetía. Sintéticos.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, evaluar  # noqa: E402
from tests.test_t297_deslinde_1_1 import _Natural, contrato  # noqa: E402


def linea(n):
    us = tuple(Unidad(f"u{i}", 100, municipio=f"30{i:03d}", provincia="30") for i in range(n))
    return Problema(us, tuple((f"u{i}", f"u{i + 1}") for i in range(n - 1)))


class AplicaPorTamano(unittest.TestCase):
    def test_k_mayor_que_4_aplica_y_da_el_optimo(self):
        from deslinde.exacto import resolver
        p = linea(12)
        r = Reglas.desde_contrato(contrato(6), Criterio())
        nat = _Natural({u.id: None for u in p.unidades}, {u.id: None for u in p.unidades}, {})
        plan, info = resolver(p, r, nat, None)
        self.assertEqual(info["estado"], "OPTIMO", info)
        self.assertEqual((info["atomos"], info["tamano"], info["tamano_max"]), (12, 72, 2000))
        self.assertEqual(info["version"], "1.0.0")  # el modelo CP-SAT no cambia: misma huella donde ya aplicaba
        self.assertTrue(evaluar(p, r, plan).valido)
        self.assertEqual(len(set(plan.values())), 6)

    def test_por_encima_del_tope_no_aplica(self):
        from unittest import mock
        from deslinde.exacto import resolver
        p = linea(12)
        with mock.patch("deslinde.exacto.TAMANO_MAX", 71):
            plan, info = resolver(p, Reglas.desde_contrato(contrato(6), Criterio()), _Natural({}, {}, {}), None)
        self.assertIsNone(plan)
        self.assertEqual(info["estado"], "NO_APLICA")
        self.assertEqual(info["motivo"], "tamaño 72 (átomos × K) > 71")


class HuellaSinCotasAbiertas(unittest.TestCase):
    def resultado(self, etapas):
        from deslinde.competicion import Candidato, Resultado
        g = Candidato("exacto", "exacto", None, 0)
        return Resultado("t", [g], g, g, "h", {}, 0.0, funcion="D8",
                         exacto={"version": "1.0.0", "aplicable": True, "estado": "MEJOR_VALIDO", "etapas": etapas,
                                 "ortools": "9.14"})

    def test_la_cota_de_una_etapa_abierta_no_cambia_la_huella(self):
        base = [["fuera", "OPTIMAL", 0, 0], ["exceso_8", "CONSTANTE", 5, 5], ["partidas", "OPTIMAL", 6, 6]]
        a = self.resultado(base + [["frontera_mm", "FEASIBLE", 785968300, 345072575]]).huella()
        b = self.resultado(base + [["frontera_mm", "FEASIBLE", 785968300, 355377584]]).huella()
        self.assertEqual(a, b)
        c = self.resultado(base + [["frontera_mm", "FEASIBLE", 785968301, 345072575]]).huella()
        self.assertNotEqual(a, c)  # el valor sí entra
        d = self.resultado([["fuera", "OPTIMAL", 0, 1]] + base[1:] + [["frontera_mm", "FEASIBLE", 785968300, 1]]).huella()
        self.assertNotEqual(a, d)  # la cota de una etapa cerrada sigue entrando (como en 1.5.0)


if __name__ == "__main__":
    unittest.main()
