# -*- coding: utf-8 -*-
"""Tests de R-NUCLEO en el certificador exacto (T-175): adaptador de núcleos cerrados desde las unidades.

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
"""
import unittest
from dataclasses import replace

try:
    import ortools  # noqa: F401
    HAY_ORTOOLS = True
except ImportError:  # pragma: no cover
    HAY_ORTOOLS = False

from ddd_motor2.adaptadores import con_nucleos, nucleos_desde_unidades
from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, enumerar, evaluar
from herramientas.certificador_exacto import nucleos_de_secciones, resolver


def _reglas(k, nucleos=True):
    return Reglas.desde_contrato({"validation": {
        "expected_districts": k, "population_floor_ratio": "0.5", "population_cap_ratio": "2",
        "target_tolerance_ratio": "0.15", "require_single_province_per_district": True,
        "province_districts": {"01": k}, "require_municipality_discipline": False,
        "preserve_closed_urban": nucleos}}, Criterio())


def _cadena(n, nucleo=()):
    us = [Unidad(id=f"s{i}", poblacion=10, municipio=f"{i:05d}", provincia="01") for i in range(n)]
    us = con_nucleos(us, {f"s{i}": "nucleo:N" for i in nucleo})
    return Problema(us, tuple((f"s{i}", f"s{i + 1}") for i in range(n - 1)))


class AdaptadorNucleos(unittest.TestCase):
    def test_solo_distritos_enteramente_cerrados(self):
        distrito = {"a": "1", "b": "1", "c": "2", "d": "2", "e": "3"}
        cerrada = {"a": True, "b": True, "c": True, "d": False}
        self.assertEqual(nucleos_desde_unidades(distrito, cerrada), {"a": "nucleo:1", "b": "nucleo:1"})

    def test_por_unidad_m04(self):
        # La unidad U abarca s1 (cerrada) y s2 (no): U no es cerrada y el distrito 1 no es núcleo.
        dist = {"s0": "0", "s1": "1", "s2": "1", "s3": "2", "s4": "2"}
        cerr = {"s0": False, "s1": True, "s2": False, "s3": True, "s4": True}
        self.assertEqual(nucleos_de_secciones(dist, cerr, {"s1": "U", "s2": "U", "s3": "V", "s4": "V"}),
                         {"s3": "nucleo:2", "s4": "nucleo:2"})

    def test_con_nucleos_conserva_campos(self):
        u = Unidad("x", 5, "00001", "01")
        self.assertEqual(con_nucleos([u], {"x": "nucleo:7"})[0], replace(u, nucleo_cerrado="nucleo:7"))


@unittest.skipUnless(HAY_ORTOOLS, "ortools no instalado")
class CertificadorNucleos(unittest.TestCase):
    def _cuenta(self, problema, reglas):
        res = resolver(problema, reglas, tiempo=30, hilos=1, objetivo="enumerar")
        self.assertEqual(res["estado"], "ENUMERADO")
        for plan in res["_planes"]:
            self.assertTrue(evaluar(problema, reglas, plan).valido)
        return res["planes_validos"]

    def test_nucleo_restringe_los_planes(self):
        # Cadena de 6 secciones de 10 hab., K=3: 10 planes contiguos válidos. Con el núcleo {s1, s2}, que ha de ser
        # exactamente un distrito, solo queda {s0}|{s1,s2}|{s3..s5}. Igual que la enumeración del núcleo.
        sin = _cadena(6)
        con = _cadena(6, nucleo=(1, 2))
        self.assertEqual(self._cuenta(sin, _reglas(3)), 10)
        self.assertEqual(self._cuenta(con, _reglas(3)), 1)
        self.assertEqual(enumerar(con, _reglas(3))["validos"], 1)
        self.assertEqual(self._cuenta(con, _reglas(3, nucleos=False)), 10)  # preserve_closed_urban=false

    def test_nucleo_en_superatomos(self):
        # Modelo restringido (grano): los superátomos no mezclan núcleo y resto; el plan sigue cumpliendo R-NUCLEO.
        p, r = _cadena(6, nucleo=(1, 2)), _reglas(3)
        res = resolver(p, r, tiempo=30, hilos=1, objetivo="minimax", grano=2.0)
        self.assertIn(res["estado"], ("OPTIMO_RESTRINGIDO", "FACTIBLE"))
        self.assertTrue(evaluar(p, r, res["asignacion"]).valido)


if __name__ == "__main__":
    unittest.main()
