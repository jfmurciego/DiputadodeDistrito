# -*- coding: utf-8 -*-
"""Tests del certificador exacto CP-SAT (T-136) sobre el núcleo ddd_motor2.reglas.

VERSIÓN: 1.1.0 — reglas del núcleo (Reglas.desde_contrato, evaluar); casos de los fallos F1 (exención por partición) y
F2 (unidad M04 que abarca varios municipios).
ANTERIOR: legacy/tests/test_certificador_exacto_v1.0.0_20261110.py
"""
import unittest

try:
    import ortools  # noqa: F401
    HAY_ORTOOLS = True
except ImportError:  # pragma: no cover
    HAY_ORTOOLS = False

from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, evaluar
from herramientas.certificador_exacto import construir_atomos, resolver


def _reglas(k, suelo="0.85", techo="1.15", municipal=True, exentos=(), particiones=(), criterio=None, prov="01"):
    cfg = {"validation": {
        "expected_districts": k, "population_floor_ratio": suelo, "population_cap_ratio": techo,
        "target_tolerance_ratio": "0.15", "require_single_province_per_district": True,
        "province_districts": {prov: k}, "require_municipality_discipline": municipal,
        "population_floor_exempt_municipalities": list(exentos),
        "population_floor_exempt_partitions": list(particiones)}}
    return Reglas.desde_contrato(cfg, criterio or Criterio())


def _cadena(pops, mun=None, prov="01", part=None):
    """Secciones en fila s0-s1-...; municipio propio por sección salvo que se indique."""
    us = tuple(Unidad(id=f"s{i}", poblacion=p, municipio=(mun[i] if mun else f"{i:05d}"), provincia=prov,
                      particion=(part[i] if part else None)) for i, p in enumerate(pops))
    return Problema(us, tuple((f"s{i}", f"s{i + 1}") for i in range(len(pops) - 1)))


def _ok(problema, reglas, asig):
    return evaluar(problema, reglas, asig).valido


@unittest.skipUnless(HAY_ORTOOLS, "ortools no instalado")
class CertificadorExacto(unittest.TestCase):
    def test_optimo_en_cadena(self):
        p = _cadena([10, 10, 10, 10])
        r = _reglas(2)
        res = resolver(p, r, tiempo=20, hilos=1, objetivo="minimax")
        self.assertEqual(res["estado"], "OPTIMO")
        self.assertEqual(res["valor_objetivo"], 0)
        self.assertTrue(_ok(p, r, res["asignacion"]))

    def test_contiguidad_hace_infactible(self):
        # 30-1-30, K=2, techo = objetivo (30,5): {30}|{1,30} pasa de techo y {30,30} sin el centro no es conexo.
        p = _cadena([30, 1, 30])
        self.assertEqual(resolver(p, _reglas(2, suelo="0.99", techo="1"), tiempo=20, hilos=1)["estado"], "INFACTIBLE")

    def test_municipio_indivisible_y_exencion(self):
        # M (s0-s1, 9 hab.) no llega al objetivo (10): no se parte. Con K=3 solo cabe {M}|{A}|{B} y M queda bajo el
        # suelo (9,5) salvo que esté exento.
        p = _cadena([5, 4, 10, 11], mun=["00001", "00001", "00002", "00003"])
        self.assertEqual(resolver(p, _reglas(3, suelo="0.95", techo="2"), tiempo=20, hilos=1)["estado"], "INFACTIBLE")
        r = _reglas(3, suelo="0.95", techo="2", exentos=("00001",))
        res = resolver(p, r, tiempo=20, hilos=1)
        self.assertEqual(res["estado"], "FACTIBLE")
        self.assertEqual(res["asignacion"]["s0"], res["asignacion"]["s1"])
        self.assertTrue(_ok(p, r, res["asignacion"]))

    def test_exencion_por_particion_f1(self):
        # Como las islas: partición P2 exenta (2 hab.) en su propia provincia-partición. Sin exención, infactible.
        us = (Unidad("a", 10, "00001", "P1", "P1"), Unidad("b", 10, "00002", "P1", "P1"),
              Unidad("c", 2, "00003", "P2", "P2"))
        p = Problema(us, (("a", "b"),))
        base = {"expected_districts": 3, "population_floor_ratio": "0.5", "population_cap_ratio": "2",
                "target_tolerance_ratio": "0.15", "require_single_province_per_district": True,
                "province_districts": {"P1": 2, "P2": 1}, "require_municipality_discipline": True}
        r = Reglas.desde_contrato({"validation": base})
        self.assertEqual(resolver(p, r, tiempo=20, hilos=1)["estado"], "INFACTIBLE")
        r = Reglas.desde_contrato({"validation": {**base, "population_floor_exempt_partitions": ["P2"]}})
        res = resolver(p, r, tiempo=20, hilos=1)
        self.assertEqual(res["estado"], "FACTIBLE")
        self.assertTrue(_ok(p, r, res["asignacion"]))

    def test_unidad_m04_entre_municipios_f2(self):
        # La unidad U abarca s1 (mun 2) y s2 (mun 3): debe quedar en un solo átomo y en un solo distrito.
        p = _cadena([10, 10, 10, 10])
        r = _reglas(2, suelo="0.5", techo="1.5", municipal=False)
        atomos, _ = construir_atomos(p, r, {"s1": "U", "s2": "U"})
        self.assertIn(["s1", "s2"], [a["secs"] for a in atomos])
        res = resolver(p, r, {"s1": "U", "s2": "U"}, tiempo=20, hilos=1, objetivo="enumerar")
        self.assertEqual(res["estado"], "ENUMERADO")
        self.assertEqual(res["planes_validos"], 2)  # {s0}|{s1,s2,s3} y {s0,s1,s2}|{s3}
        self.assertTrue(all(pl["s1"] == pl["s2"] for pl in res["_planes"]))

    def test_mixtos_del_contrato(self):
        # Municipio grande G partido en dos distritos, los dos mixtos: el núcleo lo rechaza y el certificador no lo da.
        p = _cadena([5, 10, 10, 10, 10, 5], mun=["00001", "G", "G", "G", "G", "00002"])
        r = _reglas(2, suelo="0.5", techo="1.5")
        self.assertFalse(_ok(p, r, {"s0": "0", "s1": "0", "s2": "0", "s3": "1", "s4": "1", "s5": "1"}))
        res = resolver(p, r, tiempo=20, hilos=1, objetivo="enumerar")
        self.assertEqual(res["estado"], "ENUMERADO")
        self.assertTrue(all(_ok(p, r, pl) for pl in res["_planes"]))

    def test_enumerar_cuenta_exacta(self):
        # Cadena de 4 secciones de 10, K=2, techo 1,5 (≤30) y suelo 0,5 (≥10): cortes 1|3, 2|2, 3|1 = 3 planes.
        p = _cadena([10, 10, 10, 10])
        res = resolver(p, _reglas(2, suelo="0.5", techo="1.5"), tiempo=30, hilos=1, objetivo="enumerar")
        self.assertEqual(res["estado"], "ENUMERADO")
        self.assertEqual(res["planes_validos"], 3)


if __name__ == "__main__":
    unittest.main()
