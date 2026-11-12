#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-261: la cota de nodos (ddd_motor2/reglas/cota.py) nunca supera los nodos reales de enumerar(), y si supera el
presupuesto, enumerar() con ese presupuesto no acaba. enumerar_exacto(plan=…) solo cambia cuando la cota lo demuestra.

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from ddd_motor2.exhaustivo import enumerar_exacto  # noqa: E402
from ddd_motor2.reglas import Criterio, Reglas, enumerar  # noqa: E402
from ddd_motor2.reglas.cota import cota_nodos  # noqa: E402
from test_motor2_reglas import _contrato_aleatorio, _rejilla  # noqa: E402


def _caso(rng, caso, grande=False):
    filas, cols = (3, 4) if grande else (rng.choice([2, 3]), rng.choice([3, 4]))
    p = _rejilla(rng, filas=filas, cols=cols, nucleos=caso % 3 == 0)
    k = rng.choice([2, 3, 4])
    r = Reglas.desde_contrato(_contrato_aleatorio(rng, k, permisivo=caso % 2 == 0),
                              Criterio(tolerancia=rng.choice(["metrica", "dura"])))
    return p, r


def _sin_tiempos(d):
    return {k: v for k, v in d.items() if k != "tiempo_s"}


class CotaNodos(unittest.TestCase):
    def test_cota_no_supera_los_nodos_reales(self):
        rng = random.Random(261)
        con_cota = exactas = 0
        for caso in range(200):
            p, r = _caso(rng, caso)
            res = enumerar(p, r, presupuesto=10**7, max_planes=10**6)
            self.assertTrue(res["completo"])
            if not res["planes"]:
                self.assertEqual(cota_nodos(p, r, {u.id: "X" for u in p.unidades}, 10**9)["cota"], 0)
                continue
            plan = res["planes"][rng.randrange(len(res["planes"]))]
            c = cota_nodos(p, r, plan, 10**9)
            self.assertLessEqual(c["cota"], res["nodos"], f"caso {caso}")
            self.assertFalse(c["supera"])
            con_cota += 1
            exactas += c["cota"] == res["nodos"]
        self.assertGreater(con_cota, 50)  # no vacuo

    def test_si_supera_enumerar_no_acaba(self):
        rng = random.Random(89)
        superan = 0
        for caso in range(60):
            p, r = _caso(rng, caso, grande=True)
            todo = enumerar(p, r, presupuesto=10**7, max_planes=1)
            if not todo["planes"]:
                continue
            plan = todo["planes"][0]
            c = cota_nodos(p, r, plan, 10**9)
            self.assertLessEqual(c["cota"], todo["nodos"], f"caso {caso}")
            presupuesto = c["cota"] - 1
            if presupuesto < 1:
                continue
            c2 = cota_nodos(p, r, plan, presupuesto)
            self.assertTrue(c2["supera"], f"caso {caso}")
            self.assertFalse(enumerar(p, r, presupuesto=presupuesto, max_planes=0)["completo"], f"caso {caso}")
            ex = enumerar_exacto(p, r, presupuesto, plan=plan)
            self.assertEqual((ex["metodo"], ex["completo"], ex["intentada"]), ("cadena", False, False))
            self.assertIn("cota_nodos", ex)
            superan += 1
        self.assertGreater(superan, 10, superan)

    def test_sin_demostracion_igual_que_antes(self):
        rng = random.Random(1)
        for caso in range(60):
            p, r = _caso(rng, caso)
            todo = enumerar(p, r, presupuesto=10**7, max_planes=1)
            plan = todo["planes"][0] if todo["planes"] else {u.id: "X" for u in p.unidades}
            for presupuesto in (todo["nodos"], todo["nodos"] + 1, 10**6):
                antes = enumerar_exacto(p, r, presupuesto)
                despues = enumerar_exacto(p, r, presupuesto, plan=plan)
                self.assertEqual(_sin_tiempos(despues), _sin_tiempos(antes), f"caso {caso}")

    def test_plan_no_valido_sin_cota(self):
        rng = random.Random(7)
        p, r = _caso(rng, 0)
        c = cota_nodos(p, r, {u.id: "X" for u in p.unidades}, 10)
        self.assertEqual((c["cota"], c["supera"]), (0, False))


if __name__ == "__main__":
    unittest.main()
