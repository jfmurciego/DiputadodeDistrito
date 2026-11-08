#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la reagregación del histórico a los distritos vigentes (T-83 paso B)
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: provincia sintética de cuadrados de 10 × 10 con valores esperados escritos a mano: asignación de secciones
  vigentes al distrito de mayor solape, sección 1:1, sección partida 75/25 por población, votos perdidos
  (sin geometría, fuera de distritos), mayor resto que conserva el total, ganador con desempate y cuadre con la oficial.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
try:
    from shapely.geometry import box
    import equivalencia_seccionados as es
    import reagregacion_historico as rh
except ImportError:  # pragma: no cover
    rh = None


def _s(cand, **votos):
    return {"censo": cand * 2, "votantes": cand, "votos_candidaturas": cand, "votos": votos}


@unittest.skipIf(rh is None, "falta shapely")
class Reagregacion(unittest.TestCase):
    def setUp(self):
        # vigente: A, B, C en fila; distritos: 0 = A+B, 1 = C
        self.vig = {"A": box(0, 0, 10, 10), "B": box(10, 0, 20, 10), "C": box(20, 0, 30, 10)}
        self.dist = {"0": box(0, 0, 20, 10), "1": box(20, 0, 30, 10)}
        self.pob = {"A": 100, "B": 300, "C": 50}

    def test_asignacion_mayor_solape(self):
        dist = {"0": box(0, 0, 14, 10), "1": box(14, 0, 30, 10)}  # B: 4 en 0, 6 en 1
        asign, fuera = rh.asignar_distritos(self.vig, dist)
        self.assertEqual(asign, {"A": "0", "B": "1", "C": "1"})
        self.assertEqual(fuera, [])
        asign, fuera = rh.asignar_distritos(self.vig, {"0": box(0, 0, 10, 10)})
        self.assertEqual((asign, fuera), ({"A": "0"}, ["B", "C"]))

    def test_uno_a_uno_reparto_y_perdidos(self):
        # h1 = A exacta; h2 cubre media A y media B (reparto 100/300 → 0,25 A / 0,75 B, ambas en distrito 0);
        # h3 cubre media B y media C (B pesa 300·0,5... ver cálculo); h4 sin geometría
        hist = {"h1": box(0, 0, 10, 10), "h2": box(5, 0, 15, 10), "h3": box(15, 0, 25, 10)}
        eq = es.equivalencia(hist, self.vig, self.pob)
        votos = {"h1": _s(100, PP=60, PSOE=40), "h2": _s(200, PP=100, PSOE=100),
                 "h3": _s(100, PP=50, PSOE=50), "h4": _s(10, PP=10)}
        asign, _ = rh.asignar_distritos(self.vig, self.dist)
        r = rh.reagregar(votos, eq, asign)
        d0, d1 = r["distritos"]["0"], r["distritos"]["1"]
        # h2: población A = 0,5·100 = 50, B = 0,5·300 = 150 → 0,25 / 0,75: todo en el distrito 0 (200 votos)
        # h3: B = 0,5·300 = 150, C = 0,5·50 = 25 → B 6/7 al distrito 0, C 1/7 al distrito 1
        self.assertAlmostEqual(d0["votos"]["PP"], 60 + 100 + 50 * 6 / 7)
        self.assertAlmostEqual(d1["votos"]["PP"], 50 / 7)
        self.assertAlmostEqual(d0["votos_candidaturas"] + d1["votos_candidaturas"], 400)
        self.assertEqual(r["perdido"]["sin_geometria"]["votos_candidaturas"], 10)
        self.assertEqual(r["perdido"]["sin_geometria"]["votos"]["PP"], 10)

    def test_fuera_de_distritos(self):
        eq = es.equivalencia({"h1": box(0, 0, 10, 10)}, self.vig, self.pob)
        r = rh.reagregar({"h1": _s(100, PP=100)}, eq, {})  # A sin distrito
        self.assertEqual(r["distritos"], {})
        self.assertEqual(r["perdido"]["fuera_de_distritos"]["votos_candidaturas"], 100)

    def test_mayor_resto_conserva_total(self):
        self.assertEqual(rh.mayor_resto({"a": 1.5, "b": 1.5, "c": 1.0}), {"a": 2, "b": 1, "c": 1})  # suma 4, desempate por clave
        self.assertEqual(rh.mayor_resto({"a": 10 / 3, "b": 10 / 3, "c": 10 / 3}), {"a": 4, "b": 3, "c": 3})
        self.assertEqual(rh.mayor_resto({"a": 0.4, "b": 0.4}), {"a": 1, "b": 0})  # suma 0,8 → 1

    def test_redondeo_y_ganador(self):
        res = {"distritos": {"0": {"censo": 10.4, "votantes": 5.5, "votos_candidaturas": 5.5,
                                   "votos": {"PP": 2.5, "PSOE": 2.5, "VOX": 0.5}},
                             "1": {"censo": 9.6, "votantes": 4.5, "votos_candidaturas": 4.5,
                                   "votos": {"PP": 1.5, "PSOE": 2.5, "VOX": 0.5}}}, "perdido": {}}
        red = rh.redondear(res)
        self.assertEqual(red["0"]["censo"] + red["1"]["censo"], 20)
        self.assertEqual(red["0"]["votos"]["PP"] + red["1"]["votos"]["PP"], 4)
        self.assertEqual(red["0"]["votos"]["PSOE"] + red["1"]["votos"]["PSOE"], 5)
        self.assertEqual(rh.ganador({"PSOE": 7, "PP": 7, "VOX": 1}), ("PP", 7))  # empate: orden alfabético
        self.assertEqual(rh.ganador({}), ("", 0))

    def test_cuadre_con_oficial(self):
        votos = {"h1": _s(100, PP=60, PSOE=40)}
        res = {"distritos": {}, "perdido": {k: {"votos_candidaturas": 0, "votos": {}} for k in ("a",)}}
        red = {"0": {"censo": 200, "votantes": 100, "votos_candidaturas": 100, "votos": {"PP": 60, "PSOE": 40}}}
        ok = rh.cuadre(votos, res, red, {"PP": 62, "PSOE": 41}, 0.10)  # CERA: defecto 2/62 y 1/41
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["dif_max_partido"], 0)
        self.assertEqual(ok["oficial"]["defecto_total"], round(3 / 103, 5))
        self.assertEqual(ok["oficial"]["errores"], [])
        mal = rh.cuadre(votos, res, red, {"PP": 59, "PSOE": 41}, 0.10)  # el espejo supera a la oficial
        self.assertFalse(mal["ok"])
        perdido = rh.cuadre(votos, res, {"0": {**red["0"], "votos": {"PP": 55, "PSOE": 40}}}, None, 0.10)
        self.assertFalse(perdido["ok"])  # faltan 5 votos que no constan como perdidos
        self.assertEqual(perdido["oficial"], "sin fuente oficial local: AVISO")


if __name__ == "__main__":
    unittest.main()
