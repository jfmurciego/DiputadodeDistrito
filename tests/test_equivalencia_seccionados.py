#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la equivalencia de seccionados históricos con el vigente (T-85)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: provincia sintética con cuadrados de 10 × 10 (valores esperados escritos a mano): sección idéntica = 1:1,
  sección partida en dos = reparto 0,5/0,5 por área y 0,75/0,25 por población (300 frente a 100 habitantes),
  astilla < 1 % descartada, traslación de 63 m corregida (y 5 m no), prueba del censo, sección fuera del vigente,
  geometría tomada del seccionado más cercano y el informe de % de votos no 1:1 y de votos que cambian de sección según el peso.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
try:
    from shapely.geometry import box
    import equivalencia_seccionados as es
except ImportError:  # pragma: no cover
    es = None

VIG = None if es is None else {"A": box(0, 0, 10, 10), "B": box(10, 0, 20, 10), "C": box(20, 0, 30, 10)}
POB = {"A": 50, "B": 300, "C": 100}


@unittest.skipIf(es is None, "shapely no instalado")
class Equivalencia(unittest.TestCase):
    def test_identica_es_1a1(self):
        e = es.equivalencia({"H1": box(0, 0, 10, 10)}, VIG, POB)["H1"]
        self.assertEqual(e, {"tipo": "1:1", "area": {"A": 1.0}, "poblacion": {"A": 1.0}})

    def test_partida_reparte_por_area_y_por_poblacion(self):
        e = es.equivalencia({"H2": box(10, 0, 30, 10)}, VIG, POB)["H2"]
        self.assertEqual(e["tipo"], "reparto")
        self.assertAlmostEqual(e["area"]["B"], 0.5)
        self.assertAlmostEqual(e["area"]["C"], 0.5)
        self.assertAlmostEqual(e["poblacion"]["B"], 0.75)
        self.assertAlmostEqual(e["poblacion"]["C"], 0.25)

    def test_astilla_se_descarta(self):
        e = es.equivalencia({"H": box(0, 0, 10.05, 10)}, VIG, POB)["H"]
        self.assertEqual(e["tipo"], "1:1")
        self.assertEqual(e["area"], {"A": 1.0})

    def test_fusion_no_es_1a1(self):
        # la vigente A recibe dos históricas: cada una solo aporta la mitad de A
        eq = es.equivalencia({"H1": box(0, 0, 5, 10), "H2": box(5, 0, 10, 10)}, VIG, POB)
        self.assertEqual({k: v["tipo"] for k, v in eq.items()}, {"H1": "reparto", "H2": "reparto"})
        self.assertEqual(eq["H1"]["area"], {"A": 1.0})

    def test_fuera_del_vigente(self):
        self.assertEqual(es.equivalencia({"X": box(100, 100, 110, 110)}, VIG, POB)["X"]["tipo"], "sin_vigente")

    def test_geometria_del_seccionado_mas_cercano(self):
        por_año = {2015: {"H1": "g15"}, 2012: {"H9": "g12"}, 2016: {"H9": "g16"}}
        hist, tomadas = es.completar_geometrias({"H1": {}, "H9": {}, "H7": {}}, 2015, por_año)
        self.assertEqual(hist, {"H1": "g15", "H9": "g16"})
        self.assertEqual(tomadas, ["H9"])

    def test_desplazamiento_sistematico(self):
        movida = {k: box(*(g.bounds[0], g.bounds[1] - 63, g.bounds[2], g.bounds[3] - 63)) for k, g in VIG.items()}
        self.assertEqual(es.desplazamiento_sistematico(movida, VIG), (0.0, 63.0))
        casi = {k: box(*(g.bounds[0] + 5, g.bounds[1], g.bounds[2] + 5, g.bounds[3])) for k, g in VIG.items()}
        self.assertEqual(es.desplazamiento_sistematico(casi, VIG), (0.0, 0.0))

    def test_prueba_censo(self):
        # H2 (censo 400) se parte en B y C; censo real de B = 300 y de C = 100
        eq = es.equivalencia({"H1": box(0, 0, 10, 10), "H2": box(10, 0, 30, 10)}, VIG, POB)
        ref = es.censo_referencia({"H1": 50, "B": 300, "C": 100},
                                  {"H1": eq["H1"], "B": {"tipo": "1:1", "area": {"B": 1.0}},
                                   "C": {"tipo": "1:1", "area": {"C": 1.0}}})
        self.assertEqual(ref, {"A": 50, "B": 300, "C": 100})
        r = es.prueba_censo({"H1": 50, "H2": 400}, eq, ref)
        # área: 200/200 → error (100 + 100) / 400 = 50 %; población: 300/100 → 0 %
        self.assertEqual(r, {"secciones": 2, "censo_real": 400, "error_area": 50.0, "error_poblacion": 0.0})

    def test_informe(self):
        eq = es.equivalencia({"H1": box(0, 0, 10, 10), "H2": box(10, 0, 30, 10)}, VIG, POB)
        votos = {"H1": {"votos_candidaturas": 100, "votos": {"PP": 100}},
                 "H2": {"votos_candidaturas": 200, "votos": {"PP": 120, "PSOE": 80}},
                 "H8": {"votos_candidaturas": 0, "votos": {}}}
        r = es.informe_eleccion(votos, eq)
        self.assertEqual(r["votos"], 300)
        self.assertEqual(r["pct_1a1"], 33.333)
        self.assertEqual(r["pct_no_1a1"], 66.667)
        # área: B y C reciben 100 votos (60 PP + 40 PSOE); población: B 150 y C 50 → 50 votos cambian de sección
        self.assertEqual(r["pct_difiere_area_poblacion"], 16.667)
        self.assertEqual(r["pct_sin_geometria"], 0.0)


if __name__ == "__main__":
    unittest.main()
