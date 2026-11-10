# -*- coding: utf-8 -*-
"""Tests del certificador exacto CP-SAT (T-136). VERSIÓN: 1.0.0. ANTERIOR: ninguna (fichero nuevo)."""
import unittest

try:
    import ortools  # noqa: F401
    HAY_ORTOOLS = True
except ImportError:  # pragma: no cover
    HAY_ORTOOLS = False

from herramientas.certificador_exacto import evaluar_particion, resolver


def _reglas(k, total, suelo=0.85, techo=1.15, municipal=True, exentos=()):
    t = total / k
    return {"k": k, "objetivo": t, "suelo": t * suelo, "techo": t * techo, "provincia": True,
            "provincias": {"01": k}, "municipal": municipal, "exentos": list(exentos), "particiones_exentas": []}


def _cadena(pops, mun=None):
    """Secciones en fila: s0-s1-...; municipio propio por sección salvo que se indique."""
    sec = {f"s{i}": {"pop": p, "mun": (mun[i] if mun else f"m{i}"), "prov": "01"} for i, p in enumerate(pops)}
    adj = {f"s{i}": set() for i in range(len(pops))}
    for i in range(len(pops) - 1):
        adj[f"s{i}"].add(f"s{i+1}")
        adj[f"s{i+1}"].add(f"s{i}")
    return sec, adj


@unittest.skipUnless(HAY_ORTOOLS, "ortools no instalado")
class CertificadorExacto(unittest.TestCase):
    def test_optimo_en_cadena(self):
        sec, adj = _cadena([10, 10, 10, 10])
        reglas = _reglas(2, 40)
        res = resolver(sec, adj, reglas, tiempo=20, hilos=1)
        self.assertEqual(res["estado"], "OPTIMO")
        self.assertEqual(res["valor_objetivo"], 0)
        self.assertEqual(evaluar_particion(res["asignacion"], sec, adj, reglas)["estado"], "PASS")

    def test_contiguidad_hace_infactible(self):
        # 30-1-30 y K=2: ningún corte conexo deja ambos distritos entre suelo y techo (31 frente a 30 vale, pero
        # el objetivo es 30,5 y los extremos solo se unen pasando por el centro).
        sec, adj = _cadena([30, 1, 30])
        reglas = _reglas(2, 61, suelo=0.99, techo=1.0)
        res = resolver(sec, adj, reglas, tiempo=20, hilos=1)
        self.assertEqual(res["estado"], "INFACTIBLE")

    def test_municipio_indivisible_y_exencion(self):
        # M (s0-s1, 9 hab.) no llega al objetivo (10): no se parte. Con K=3 solo cabe {M}|{A}|{B} y M queda bajo el
        # suelo (9,5) salvo que esté exento.
        sec, adj = _cadena([5, 4, 10, 11], mun=["M", "M", "A", "B"])
        reglas = _reglas(3, 30, suelo=0.95, techo=2.0)
        self.assertEqual(resolver(sec, adj, reglas, tiempo=20, hilos=1)["estado"], "INFACTIBLE")
        reglas = _reglas(3, 30, suelo=0.95, techo=2.0, exentos=("M",))
        res = resolver(sec, adj, reglas, tiempo=20, hilos=1)
        self.assertEqual(res["estado"], "OPTIMO")
        self.assertEqual(res["asignacion"]["s0"], res["asignacion"]["s1"])
        self.assertEqual(evaluar_particion(res["asignacion"], sec, adj, reglas)["estado"], "PASS")

    def test_evaluar_detecta_mixtos(self):
        # Municipio grande G (4 secciones) partido en dos distritos, los dos mixtos con vecinos: inválido.
        sec, adj = _cadena([5, 10, 10, 10, 10, 5], mun=["a", "G", "G", "G", "G", "b"])
        reglas = _reglas(2, 50, suelo=0.5, techo=1.5)
        asig = {"s0": "0", "s1": "0", "s2": "0", "s3": "1", "s4": "1", "s5": "1"}
        ev = evaluar_particion(asig, sec, adj, reglas)
        self.assertEqual(ev["estado"], "FAIL")
        self.assertIn("G", ev["municipios_invalidos"])
        res = resolver(sec, adj, reglas, tiempo=20, hilos=1)
        self.assertIn(res["estado"], ("OPTIMO", "INFACTIBLE"))
        if res["estado"] == "OPTIMO":
            self.assertEqual(evaluar_particion(res["asignacion"], sec, adj, reglas)["estado"], "PASS")

    def test_enumerar_cuenta_exacta(self):
        # Cadena de 4 secciones de 10 y K=2 con techo 1,5 (≤30) y suelo 0,5 (≥10): cortes 1|3, 2|2, 3|1 = 3 planes.
        sec, adj = _cadena([10, 10, 10, 10])
        reglas = _reglas(2, 40, suelo=0.5, techo=1.5)
        res = resolver(sec, adj, reglas, tiempo=30, hilos=1, objetivo="enumerar")
        self.assertEqual(res["estado"], "ENUMERADO")
        self.assertEqual(res["planes_validos"], 3)
        self.assertEqual(len({frozenset(frozenset(s for s, d in p.items() if d == k) for k in set(p.values()))
                              for p in res["_planes"]}), 3)


if __name__ == "__main__":
    unittest.main()
