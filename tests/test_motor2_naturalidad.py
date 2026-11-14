#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-172 · indicadores de naturalidad (métricas, no reglas)."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2 import naturalidad as nat  # noqa: E402
from ddd_core.territorio_ids import mismo_territorio  # noqa: E402  (T-220)

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
        lab.obj_circ = {}
        cerca, lejos = {"a": "1", "b": "1", "c": "2", "d": "3"}, {"a": "1", "b": "2", "c": "2", "d": "3"}
        self.assertEqual(lab.clave(cerca, "D5")[1], 0.0)          # 200 fuera (no cuenta); 100 y 100: 0 %
        self.assertAlmostEqual(lab.clave(lejos, "D5")[1], 0.02)   # 93/207: fuera (no cuenta) y 7 % - 5 %
        self.assertEqual(lab.clave(lejos, "D8")[1], 0.0)
        self.assertEqual(lab.clave(cerca, "D5")[2:], lab.clave(cerca, "B")[1:])  # tras el tope, la clave de B

    def test_objetivo_por_circunscripcion(self):
        from fractions import Fraction
        from ddd_motor2.naturalidad_competicion import Laboratorio as Lab
        lab = Lab.__new__(Lab)
        lab.pob_u, lab.objetivo, lab.tol = {"a": 50, "b": 50, "c": 150}, Fraction(250, 3), Fraction(250, 3) * Fraction(15, 100)
        lab.circ_u = {"a": "01", "b": "01", "c": "02"}
        lab.obj_circ = {"01": Fraction(50), "02": Fraction(150)}  # 01: 100 hab. / 2 escaños; 02: 150 / 1
        lab.pj = lab.ca = {u: None for u in lab.pob_u}
        lab.largo = {("a", "b"): 1.0}
        k = lab.clave({"a": "1", "b": "2", "c": "3"}, "A")
        self.assertEqual(k[:2], (0, 0.0))  # contra el objetivo regional (83) los tres estarían fuera

    def test_funciones_y_reanudar(self):
        from types import SimpleNamespace
        from ddd_motor2.naturalidad_competicion import FUNCIONES, VERSION, funciones_de, incompatible, parametros
        self.assertEqual(funciones_de("C,D8"), ("A", "C", "D8"))  # A siempre: es la referencia
        self.assertEqual(funciones_de(",".join(FUNCIONES)), FUNCIONES)
        with self.assertRaises(ValueError):
            funciones_de("C,X")
        a = SimpleNamespace(cadenas=20, pasos=300, rpj=0.5, rca=0.3, rmov=0.2, rlong=0.3)
        f, ent = funciones_de("C,D8"), {"geos": "3.14.1"}
        previo = {"version": VERSION, "parametros": parametros(a, f), "entorno": ent}
        self.assertEqual(incompatible(previo, a, f, ent), "")
        self.assertIn("parámetros", incompatible(previo, a, FUNCIONES, ent))       # otras funciones
        self.assertIn("parámetros", incompatible(previo, SimpleNamespace(**{**vars(a), "pasos": 150}), f, ent))
        self.assertIn("entorno", incompatible(previo, a, f, {"geos": "3.12.0"}))
        self.assertIn("versión", incompatible({**previo, "version": "1.2.0"}, a, f, ent))
        self.assertNotIn("funciones", parametros(a, FUNCIONES))  # con las cinco, los parámetros de 1.1.0

    def test_municipio_en_dos_islas(self):
        from ddd_motor2.naturalidad_competicion import unidades_de
        sec = ["3502401001", "3502401010", "3501601001", "3501601002"]
        pob_m = {"35024": 20, "35016": 500}
        psec = {"3502401001": "35-C01", "3502401010": "35-C04", "3501601001": "35-C01", "3501601002": "35-C01"}
        u = unidades_de(sec, pob_m, 100, psec)
        self.assertEqual(u["3502401001"], "35024:35-C01")  # Teguise en Lanzarote
        self.assertEqual(u["3502401010"], "35024:35-C04")  # y en La Graciosa
        self.assertEqual(u["3501601001"], "3501601001")    # municipio mayor que el objetivo: por secciones
        self.assertEqual(unidades_de(sec[:1], pob_m, 100, {}), {"3502401001": "35024"})  # sin islas, el municipio

    @unittest.skipUnless(os.environ.get("DDD_SECCIONADO_DIR"), "necesita el seccionado INE (DDD_SECCIONADO_DIR)")
    def test_huella_leon_igual_a_1_1_0(self):
        """Sin islas ni puentes, la versión vigente reproduce la huella de 1.1.0 (#656) en León (unos 2 min)."""
        import tempfile
        from ddd_motor2.naturalidad_competicion import main
        ref = json.loads((ROOT / "docs/ESTUDIOS/T172_naturalidad/resultados/congreso_leon/RESULTADO.json")
                         .read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(main(["--seccionado-dir", os.environ["DDD_SECCIONADO_DIR"], "--out", d, "--pasos", "300",
                                   "nac24"]), 0)
            r = json.loads((Path(d) / "nac24" / "RESULTADO.json").read_text(encoding="utf-8"))
        self.assertEqual(r["huella_d"], ref["huella_d"])

    def test_reparar_vigente_con_dos_mixtos(self):
        """D-66: el municipio 10001 está en dos distritos mixtos (incumple); la reparación lo deja en uno."""
        from ddd_motor2.naturalidad_competicion import Laboratorio as Lab
        from ddd_motor2.reglas import Reglas, evaluar
        from ddd_motor2.reglas.modelo import Problema, Unidad
        reglas = Reglas.desde_contrato({"validation": {
            "expected_districts": 3, "population_floor_ratio": 0, "population_cap_ratio": 10,
            "target_tolerance_ratio": 5, "require_single_province_per_district": False,
            "require_municipality_discipline": True}})
        ids = ["2000100001", "1000100001", "1000100002", "1000100003", "3000100001"]  # o1 - s1 - s2 - s3 - o2
        lab = Lab.__new__(Lab)
        lab.reglas = reglas
        lab.problema = Problema(tuple(Unidad(u, 100, municipio=u[:5], provincia="10") for u in ids),
                                tuple(zip(ids, ids[1:])))
        lab.pob_u = {u: 100 for u in ids}
        vigente = dict(zip(ids, ["1", "1", "2", "3", "3"]))  # 10001 en el 1 y el 3, ambos mixtos
        self.assertFalse(evaluar(lab.problema, reglas, vigente).valido)
        plan, notas = lab.reparar(vigente)
        self.assertTrue(plan and evaluar(lab.problema, reglas, plan).valido, notas)
        self.assertEqual(plan["2000100001"], "1")  # el resto del plan no se toca

    def test_corte_por_mitad_del_par(self):
        """Con objetivo por circunscripción, el corte usa la mitad de la población del par y la tolerancia real."""
        from ddd_motor2.naturalidad_competicion import _bip_mitad

        class Sub:
            node_indices = [0, 1, 2]

            def node_data(self, n):
                return {"population": [30, 50, 20][n]}

        visto = {}

        def bip(sub, pop_col, pop_target, epsilon, **kw):
            visto.update(pop_target=pop_target, epsilon=epsilon, kw=kw)
            return {0}

        self.assertEqual(_bip_mitad(Sub(), "population", 999.0, 1e6, bip=bip, eps=0.15, rng=7), {0})
        self.assertEqual(visto, {"pop_target": 50.0, "epsilon": 0.15, "kw": {"rng": 7}})

    def test_islas_y_enclaves_del_contrato(self):
        from ddd_motor2.naturalidad_competicion import particiones, puentes_contrato
        cfg = {"m": {"x": {"hard_partition_lookup": "configuracion/particiones_insulares_2025.json",
                           "hard_partition_territory_id": "nac07"}}}
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
        bad = next(r for r in filas if mismo_territorio(r["territorio"], "nac06"))  # T-220: datos derivados con el id viejo
        self.assertEqual((bad["pj_n"], bad["pj_partidos"]), ("14", "13"))  # dato conocido del indicador C13
        for r in filas:
            self.assertGreater(float(r["pp_medio"]), 0)
            self.assertLessEqual(float(r["convexidad_min"]), 1.0)


if __name__ == "__main__":
    unittest.main()
