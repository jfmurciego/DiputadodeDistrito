#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-172 · indicadores de naturalidad (métricas, no reglas)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2 import naturalidad as nat  # noqa: E402

ASIG = {"a": "1", "b": "1", "c": "2", "d": "2"}
POB = {"a": 10, "b": 30, "c": 20, "d": 40}


class Demarcaciones(unittest.TestCase):
    def test_partida_y_mayoritario(self):
        r = nat.demarcaciones(ASIG, POB, {"a": "P", "b": "P", "c": "Q", "d": "P"})
        self.assertEqual((r["n"], r["partidas"], r["lista_partidas"]), (2, 1, ["P"]))
        # P: 1->40, 2->40 (mayoritario 40); Q: 20  => (40 + 20) / 100
        self.assertAlmostEqual(r["fraccion_poblacion_en_mayoritario"], 0.6)
        self.assertEqual(r["poblacion_fuera_de_mayoritario"], 40)

    def test_sin_dato_no_cuenta(self):
        r = nat.demarcaciones(ASIG, POB, {"a": "P", "b": "P"})
        self.assertEqual((r["n"], r["partidas"], r["poblacion_sin_dato"]), (1, 0, 60))

    def test_no_depende_del_orden(self):
        g = {"a": "P", "b": "Q", "c": "Q", "d": "P"}
        inv = dict(reversed(list(ASIG.items())))
        self.assertEqual(nat.demarcaciones(ASIG, POB, g), nat.demarcaciones(inv, POB, g))


class Corte(unittest.TestCase):
    def test_aristas(self):
        r = nat.aristas_de_corte(ASIG, [("a", "b", 1.0), ("b", "c", 3.0), ("c", "d", 1.0), ("d", "x", 9.0)])
        self.assertEqual((r["aristas"], r["cortes"]), (3, 1))
        self.assertAlmostEqual(r["fraccion_peso_corte"], 0.6)


class Movilidad(unittest.TestCase):
    def test_cohesion(self):
        area = {"a": "A", "b": "B", "c": "C", "d": "C"}
        # A->B dentro del distrito 1; A->C fuera; C->C no cuenta (misma área)
        r = nat.cohesion_movilidad(ASIG, POB, area, [("A", "B", 6), ("A", "C", 4), ("C", "C", 100), ("A", "Z", 5)])
        self.assertAlmostEqual(r["cohesion"], 0.6)
        self.assertEqual(r["flujo"], 10)

    def test_area_partida_reparte_por_poblacion(self):
        area = {"a": "A", "b": "B", "c": "B", "d": "C"}  # B: 30 en 1, 20 en 2
        r = nat.cohesion_movilidad(ASIG, POB, area, [("A", "B", 10)])
        self.assertAlmostEqual(r["cohesion"], 0.6)


@unittest.skipUnless(__import__("importlib").util.find_spec("shapely"), "sin shapely")
class Forma(unittest.TestCase):
    def test_cuadrado_y_ele(self):
        from shapely.geometry import Polygon, box
        f = nat.forma({"1": box(0, 0, 1, 1), "2": Polygon([(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)])})
        self.assertAlmostEqual(f["1"]["polsby_popper"], math.pi / 4)
        self.assertAlmostEqual(f["1"]["convexidad"], 1.0)
        self.assertLess(f["2"]["convexidad"], 1.0)
        self.assertLess(f["2"]["polsby_popper"], f["1"]["polsby_popper"])


class Laboratorio(unittest.TestCase):
    def test_huella_sin_etiquetas(self):
        from ddd_motor2.naturalidad_competicion import huella_plan
        self.assertEqual(huella_plan({"a": "1", "b": "2"}), huella_plan({"a": "7", "b": "3"}))
        self.assertNotEqual(huella_plan({"a": "1", "b": "2"}), huella_plan({"a": "1", "b": "1"}))

    def test_tope_d5_d8_solo_elige(self):
        from ddd_motor2.naturalidad_competicion import Laboratorio as Lab
        lab = Lab.__new__(Lab)
        lab.pob_u, lab.objetivo, lab.tol = {"a": 93, "b": 107, "c": 100, "d": 100}, 100, 15
        lab.pj = lab.ca = {u: None for u in lab.pob_u}
        lab.largo = {("a", "b"): 1.0, ("c", "d"): 1.0}
        cerca, lejos = {"a": "1", "b": "1", "c": "2", "d": "3"}, {"a": "1", "b": "2", "c": "2", "d": "3"}
        self.assertEqual(lab.clave(cerca, "D5")[1], 0.0)          # 200 fuera (no cuenta); 100 y 100: 0 %
        self.assertAlmostEqual(lab.clave(lejos, "D5")[1], 0.02)   # 93/207: fuera (no cuenta) y 7 % - 5 %
        self.assertEqual(lab.clave(lejos, "D8")[1], 0.0)
        self.assertEqual(lab.clave(cerca, "D5")[2:], lab.clave(cerca, "B")[1:])  # tras el tope, la clave de B

    def test_islas_y_enclaves_del_contrato(self):
        from ddd_motor2.naturalidad_competicion import particiones, puentes_contrato
        cfg = {"m": {"x": {"hard_partition_lookup": "configuracion/particiones_insulares_2025.json",
                           "hard_partition_territory_id": "congreso_baleares"}}}
        part = particiones(cfg)
        self.assertIn(("0702401001", "0702602001"), part.pop("_puentes"))  # Formentera con Ibiza
        self.assertEqual(len(set(part.values())), 3)
        cfg = {"modulos": {"m02": {"topology_bridges": [{"u": 910901001, "v": "0921904001"}]}}}
        self.assertEqual(puentes_contrato(cfg), {("0921904001", "910901001")})  # el cero lo repone el laboratorio

    def test_colores_emparejados(self):
        from ddd_motor2.naturalidad_informe import colores
        pob = {"a": 1, "b": 1, "c": 5}
        c = colores({"A": {"a": "1", "b": "1", "c": "2"}, "B": {"a": "9", "b": "8", "c": "8"},
                     "C": {"a": "1", "b": "1", "c": "2"}}, pob)
        self.assertEqual(c["B"]["8"], c["A"]["2"])  # B-8 comparte más población con A-2
        self.assertEqual(c["C"], c["A"])


class Vigentes(unittest.TestCase):
    """Los indicadores de los mapas vigentes están en el repo con su manifiesto y cubren toda datos/composicion."""

    def test_manifiesto_y_cobertura(self):
        d = ROOT / "datos" / "naturalidad"
        man = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(man["salida"]["vigentes.csv"], hashlib.sha256((d / "vigentes.csv").read_bytes()).hexdigest())
        self.assertEqual(man["errores"], {})
        filas = list(csv.DictReader(open(d / "vigentes.csv", encoding="utf-8")))
        comp = json.loads((ROOT / "datos" / "composicion" / "MANIFEST.json").read_text(encoding="utf-8"))["territorios"]
        self.assertEqual(sorted(r["territorio"] for r in filas), sorted(comp))
        bad = next(r for r in filas if r["territorio"] == "congreso_badajoz")
        self.assertEqual((bad["pj_n"], bad["pj_partidos"]), ("14", "13"))  # dato conocido del indicador C13
        for r in filas:
            self.assertGreater(float(r["pp_medio"]), 0)
            self.assertLessEqual(float(r["convexidad_min"]), 1.0)


if __name__ == "__main__":
    unittest.main()
