# -*- coding: utf-8 -*-
"""Tests del modelo ligero del certificador exacto (T-164): superátomos (cota superior) y relajación fluida (cota
inferior).

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
"""
import random
import unittest

try:
    import ortools  # noqa: F401
    HAY_ORTOOLS = True
except ImportError:  # pragma: no cover
    HAY_ORTOOLS = False

from ddd_motor2.reglas import Problema, Unidad, evaluar
from tests.test_certificador_exacto import _cadena, _reglas

if HAY_ORTOOLS:
    from herramientas.certificador_exacto import (agregar_atomos, certificar_ligero, construir_atomos, cota_relajada,
                                                  resolver)


def _rejilla(n, m, semilla, municipios=4):
    """Rejilla n×m de secciones; municipios en franjas verticales; poblaciones pseudoaleatorias."""
    rnd = random.Random(semilla)
    us, ar = [], []
    for i in range(n):
        for j in range(m):
            us.append(Unidad(id=f"s{i}_{j}", poblacion=rnd.randint(5, 30),
                             municipio=f"{1 + j * municipios // m:05d}", provincia="01"))
            if i + 1 < n:
                ar.append((f"s{i}_{j}", f"s{i + 1}_{j}"))
            if j + 1 < m:
                ar.append((f"s{i}_{j}", f"s{i}_{j + 1}"))
    return Problema(tuple(us), tuple(ar))


@unittest.skipUnless(HAY_ORTOOLS, "ortools no instalado")
class ModeloLigero(unittest.TestCase):
    def test_superatomos_conexos_y_bajo_tope(self):
        p = _rejilla(4, 5, 1)
        r = _reglas(3, suelo="0.5", techo="1.5", municipal=False)
        atomos, aristas = construir_atomos(p, r, {})
        sup, sar = agregar_atomos(atomos, aristas, 40)
        self.assertEqual(sorted(s for a in sup for s in a["secs"]), sorted(u.id for u in p.unidades))
        adj = p.adyacencia(False)
        for a in sup:
            if len(a["secs"]) > 1:
                self.assertLessEqual(a["pop"], 40)
            vistos, pila, ss = {a["secs"][0]}, [a["secs"][0]], set(a["secs"])
            while pila:
                for v in adj[pila.pop()]:
                    if v in ss and v not in vistos:
                        vistos.add(v)
                        pila.append(v)
            self.assertEqual(vistos, ss)

    def test_cotas_encierran_el_optimo_exacto(self):
        for semilla in range(4):
            p = _rejilla(4, 4, semilla)
            r = _reglas(3, suelo="0.6", techo="1.4", municipal=False)
            exacto = resolver(p, r, tiempo=30, hilos=2, objetivo="minimax")
            self.assertEqual(exacto["estado"], "OPTIMO")
            lig = certificar_ligero(p, r, tiempo=30, hilos=2, objetivo="minimax", grano=0.3, umbral_exacto=0)
            self.assertIn(lig["estado"], ("OPTIMO_CERTIFICADO", "COTA"))
            self.assertLessEqual(lig["cota_inferior"], exacto["valor_objetivo"])
            self.assertGreaterEqual(lig["cota_superior"], exacto["valor_objetivo"])
            self.assertTrue(evaluar(p, r, lig["asignacion"]).valido)

    def test_pista_valida_no_empeora(self):
        p = _cadena([10, 10, 10, 10, 10, 10])
        r = _reglas(2, suelo="0.5", techo="1.5", municipal=False)
        pista = {f"s{i}": ("A" if i < 3 else "B") for i in range(6)}
        lig = certificar_ligero(p, r, tiempo=20, hilos=1, objetivo="minimax", pista=pista, grano=0.4, umbral_exacto=0)
        self.assertEqual(lig["estado"], "OPTIMO_CERTIFICADO")
        self.assertEqual(lig["cota_superior"], 0)

    def test_relajacion_prueba_infactibilidad(self):
        # Municipio indivisible de 9 hab. bajo el suelo (9,5): ningún plan; la relajación lo prueba sin contigüidad.
        p = _cadena([5, 4, 10, 11], mun=["00001", "00001", "00002", "00003"])
        r = _reglas(3, suelo="0.95", techo="2")
        self.assertEqual(cota_relajada(p, r, tiempo=20, hilos=1)["estado"], "INFACTIBLE")
        self.assertEqual(certificar_ligero(p, r, tiempo=20, hilos=1, objetivo="factibilidad", umbral_exacto=0)["estado"],
                         "INFACTIBLE")

    def test_relajacion_divisible_reparte_y_acota(self):
        # Un municipio de 60 hab. (6 secciones) y K=3: la relajación reparte 20/20/20 y da cota 0; el exacto también.
        p = _cadena([10] * 6, mun=["00001"] * 6)
        r = _reglas(3, suelo="0.9", techo="1.1")
        inf = cota_relajada(p, r, tiempo=20, hilos=1, objetivo="minimax")
        self.assertEqual(inf["divisibles"], 1)
        self.assertEqual(inf["cota_inferior"], 0)
        lig = certificar_ligero(p, r, tiempo=20, hilos=1, objetivo="minimax", grano=0.5, umbral_exacto=0)
        self.assertEqual(lig["estado"], "OPTIMO_CERTIFICADO")

    def test_relajacion_acepta_un_plan_valido(self):
        # Validez de la relajación: un plan válido proyectado (impuesto) es solución y da su propio valor.
        for semilla in range(3):
            p = _rejilla(4, 4, semilla)
            r = _reglas(3, suelo="0.6", techo="1.4")
            ex = resolver(p, r, tiempo=30, hilos=2, objetivo="minimax")
            if ex["estado"] != "OPTIMO":
                continue
            inf = cota_relajada(p, r, tiempo=30, hilos=2, objetivo="minimax", pista=ex["asignacion"], fijar_pista=True)
            self.assertEqual(inf["estado"], "RELAJACION_FACTIBLE")
            self.assertEqual(inf["cota_inferior"], ex["valor_objetivo"])

    def test_con_exacto_pequeno_certifica(self):
        p = _rejilla(4, 4, 2)
        r = _reglas(3, suelo="0.6", techo="1.4", municipal=False)
        exacto = resolver(p, r, tiempo=30, hilos=2, objetivo="minimax")
        lig = certificar_ligero(p, r, tiempo=30, hilos=2, objetivo="minimax", grano=0.3)
        self.assertEqual(lig["estado"], "OPTIMO_CERTIFICADO")
        self.assertEqual(lig["cota_superior"], exacto["valor_objetivo"])


if __name__ == "__main__":
    unittest.main()
