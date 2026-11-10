#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-205 · D8 en la competición del motor nuevo: clave compartida con el laboratorio de naturalidad, generador
«ponderado» y --funcion. Sintético y solo stdlib salvo lo marcado (gerrychain; seccionado INE con DDD_SECCIONADO_DIR).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.competicion import EntradaTerritorio, Salida, competir  # noqa: E402
from tests.test_motor2_competicion import CFG, escribir_comp  # noqa: E402

UNIDADES = ["A", "B", "C", "D", "E"]
POB = {"A": 200, "B": 201, "C": 6, "D": 200, "E": 200}  # 807 habitantes, K = 2
BORDE = {("A", "B"): 3000.0, ("B", "C"): 5000.0, ("C", "D"): 100.0, ("D", "E"): 3000.0}  # metros


def plan_corte(i):
    return {u: ("1" if j < i else "2") for j, u in enumerate(UNIDADES)}


class Fijo:
    def __init__(self, nombre, planes):
        self.nombre, self.planes = nombre, planes

    def generar(self, entrada, semilla, destino):
        return Salida(escribir_comp(Path(destino) / "comp.csv", self.planes[semilla], POB))


def entrada(tmp: Path) -> EntradaTerritorio:
    secc = {u: f"220010100{i}" for i, u in enumerate(UNIDADES)}  # como escribir_comp (orden alfabético)
    g = tmp / "grafo.json"
    g.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
        {"u": secc[a], "v": secc[b], "edge_type": "geometric", "shared_border_m": w} for (a, b), w in BORDE.items()]}))
    return EntradaTerritorio("sintetico", CFG, g)


class EligeConD8(unittest.TestCase):
    """A elige el más equilibrado (corte tras B: 401/406); D8 corta por la frontera corta (tras C: 407/400): los dos
    dentro del 8 %, así que manda la frontera cortada."""

    def competir(self, funcion):
        tmp = Path(tempfile.mkdtemp())
        return competir(entrada(tmp), Fijo("canonico", {None: plan_corte(2)}), Fijo("cadena", {7: plan_corte(3)}),
                        [7], tmp / "out", exhaustivo=False, funcion=funcion)

    def test_a_y_d8(self):
        a, d8 = self.competir("A"), self.competir("D8")
        self.assertEqual(a.ganador.id, "canonico")
        self.assertEqual(d8.ganador.id, "cadena-s7")
        self.assertEqual(d8.funcion, "D8")
        fuera, exceso, partidas, corte, _, huella = d8.ganador.natural
        self.assertEqual((fuera, exceso, corte), (0, 0.0, 0.1))
        self.assertEqual(partidas, d8.canonico.natural[2])  # CUMUN 22000-22004: mismas demarcaciones partidas
        self.assertEqual(huella, d8.ganador.huella_plan)
        self.assertEqual(d8.canonico.natural[3], 5.0)
        self.assertNotEqual(a.huella(), d8.huella())  # la función entra en la huella (si no es A)
        self.assertIn("clave_naturalidad", d8.a_dict()["candidatos"][0])
        self.assertEqual(d8.a_dict()["orden_calidad"][3], "exceso_tope")

    def test_funcion_desconocida(self):
        with self.assertRaises(ValueError):
            self.competir("X")


class Interfaz(unittest.TestCase):
    def test_competir_territorio_d8_y_reanudar(self):
        from ddd_motor2.competir import competir_territorio, fila_guardada
        from tests.test_motor2_semilla import cfg as cfg_con_ancla
        tmp = Path(tempfile.mkdtemp())
        e = entrada(tmp)
        e = EntradaTerritorio("sintetico", cfg_con_ancla(), e.grafo_m03)
        e.cfg["validation"] = dict(CFG["validation"])
        planes = {None: plan_corte(2)}
        gen = (Fijo("canonico", planes), type("F", (), {"nombre": "cadena", "generar": lambda s, en, se, d: Salida(
            escribir_comp(Path(d) / "comp.csv", plan_corte(3), POB))})())
        f = competir_territorio("sintetico", tmp, 3, generadores=gen, entrada=e)
        self.assertEqual((f["funcion"], f["frente_al_canonico"]), ("D8", "mejora"), f)
        g = fila_guardada("sintetico", tmp, 3, cfg=e.cfg, funcion="D8")
        self.assertEqual((g["frente_al_canonico"], g["ganador"]), ("mejora", f["ganador"]))
        self.assertIsNone(fila_guardada("sintetico", tmp, 3, cfg=e.cfg, funcion="A"))  # otra función: se recalcula


class FueraPorCircunscripcion(unittest.TestCase):
    """T-211: con cuotas de varias provincias, lo publicado (fuera_tolerancia, desvio_max) se mide como la clave:
    contra el objetivo de cada circunscripción. A y B en la 22 (200 hab., 1 escaño); C y D en la 44 (120, 1 escaño).
    Objetivo regional 160: los dos distritos quedan fuera (±25 %); por circunscripción, ninguno."""

    POB = {"A": 100, "B": 100, "C": 60, "D": 60}
    PROV = {"A": "22", "B": "22", "C": "44", "D": "44"}

    def competir(self, funcion):
        tmp = Path(tempfile.mkdtemp())
        cfg = {"validation": {**CFG["validation"], "population_floor_ratio": 0.5, "population_cap_ratio": 1.5,
                              "province_districts": {"22": 1, "44": 1}}}
        secc = {u: f"{self.PROV[u]}0010100{i}" for i, u in enumerate(sorted(self.POB))}
        g = tmp / "grafo.json"
        g.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b], "edge_type": "geometric", "shared_border_m": 100.0}
            for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        pob, prov = self.POB, self.PROV

        class Gen:
            nombre = "canonico"

            def generar(self, entrada, semilla, destino):
                ruta = Path(destino) / "comp.csv"
                ruta.parent.mkdir(parents=True, exist_ok=True)
                with open(ruta, "w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id",
                                "ddd_closed_urban"])
                    for u in sorted(pob):
                        w.writerow([secc[u], "1" if prov[u] == "22" else "2", pob[u], prov[u], secc[u][:5], u, "0"])
                return Salida(ruta)
        return competir(EntradaTerritorio("sintetico", cfg, g), Gen(), Gen(), [], tmp / "out", exhaustivo=False,
                        funcion=funcion)

    def test_d8_publica_lo_que_elige(self):
        r = self.competir("D8")
        c = r.canonico
        self.assertEqual(c.estado, "VALIDO", c.a_dict())
        self.assertEqual((c.fuera_tolerancia, c.desvio_max), (0, 0))
        self.assertEqual(c.natural[0], c.fuera_tolerancia)  # la clave y lo publicado, con la misma medida
        self.assertEqual(c.extra["metricas_regionales"], {"fuera_tolerancia": 2, "desvio_max": 0.25})

    def test_a_no_cambia(self):
        c = self.competir("A").canonico
        self.assertEqual((c.fuera_tolerancia, float(c.desvio_max)), (2, 0.25))
        self.assertNotIn("metricas_regionales", c.extra)


@unittest.skipUnless(importlib.util.find_spec("gerrychain"), "sin gerrychain")
class Ponderado(unittest.TestCase):
    def test_parte_del_canonico_y_no_empeora(self):
        from ddd_motor2.generadores import Ponderado as Gen
        tmp = Path(tempfile.mkdtemp())
        r = competir(entrada(tmp), Fijo("canonico", {None: plan_corte(2)}), Gen(pasos=30), [11, 12], tmp / "out",
                     exhaustivo=False, funcion="D8")
        self.assertTrue(all(c.estado == "VALIDO" for c in r.candidatos), [c.a_dict() for c in r.candidatos])
        self.assertLessEqual(r.ganador.clave(), r.canonico.clave())
        self.assertEqual(r.ganador.natural[3], 0.1)  # la cadena encuentra el corte por la frontera corta
        r2 = competir(entrada(Path(tempfile.mkdtemp())), Fijo("canonico", {None: plan_corte(2)}), Gen(pasos=30),
                      [11, 12], Path(tempfile.mkdtemp()), exhaustivo=False, funcion="D8")
        self.assertEqual(r.huella(), r2.huella())  # bit a bit


@unittest.skipUnless(os.environ.get("DDD_SECCIONADO_DIR") and importlib.util.find_spec("geopandas"),
                     "necesita el seccionado INE (DDD_SECCIONADO_DIR)")
class ClaveCompartida(unittest.TestCase):
    """Para un mismo plan, la clave D8 de la competición (M06 + M03 con shared_border_m) es la del laboratorio
    (secciones + geometría INE): León (ganador D8 del laboratorio) y Soria (un solo distrito)."""

    def comparar(self, t, plan_secciones):
        from ddd_motor2 import naturalidad_mapas as nm
        from ddd_motor2.adaptadores import problema_y_plan
        from ddd_motor2.naturalidad_clave import natural_desde_m06
        from ddd_motor2.naturalidad_competicion import Laboratorio
        from ddd_motor2.reglas import Reglas
        lab = Laboratorio(t, Path(os.environ["DDD_SECCIONADO_DIR"]), nm.tablas_municipio(), nm.movilidad())
        plan_u = {lab.unidad[s]: d for s, d in plan_secciones.items()}
        tmp = Path(tempfile.mkdtemp())
        comp, grafo = tmp / "comp.csv", tmp / "grafo.json"
        with open(comp, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"])
            for s in sorted(lab.asig0):
                w.writerow([s, plan_secciones[s], lab.pob_s[s], s[:2], s[:5], lab.unidad[s], "0"])
        edges = [{"u": a, "v": b, "edge_type": "geometric", "shared_border_m": x} for a, b, x in lab.geo.aristas()]
        edges += [{"u": a, "v": b, "edge_type": "contact_bridge", "shared_border_m": 0} for a, b in lab.geo.contactos()]
        grafo.write_text(json.dumps({"nodes": sorted(lab.asig0), "edges": edges}))
        reglas = Reglas.desde_contrato(lab.cfg)
        problema, plan, _ = problema_y_plan(comp, grafo, lab.cfg)
        self.assertEqual(plan, plan_u)
        nat = natural_desde_m06(problema, reglas, comp, grafo, lab.cfg)
        self.assertEqual(nat.clave(plan, "D8", huella="h"), lab.clave(plan_u, "D8", huella="h"))

    def test_leon(self):
        d = ROOT / "docs/ESTUDIOS/T172_naturalidad/resultados/congreso_leon/congreso_leon_D8.csv"
        with open(d, encoding="utf-8") as fh:
            self.comparar("congreso_leon", {r["seccion"]: r["distrito"] for r in csv.DictReader(fh)})

    def test_soria(self):
        from ddd_motor2 import naturalidad_mapas as nm
        asig, _ = nm.leer_composicion(nm.COMPOSICION / "congreso_soria.csv")
        self.comparar("congreso_soria", asig)


@unittest.skipUnless(os.environ.get("DDD_BATERIA_OUT") and importlib.util.find_spec("geopandas"),
                     "necesita las entradas y la competición de la batería (DDD_BATERIA_OUT)")
class AutonomicaReal(unittest.TestCase):
    """T-211 con datos reales: País Vasco (tres provincias, 25 escaños cada una), composición del canónico."""

    def test_pais_vasco(self):
        from ddd_motor2.competicion import Candidato, juzgar
        from ddd_motor2.generadores import entrada_bateria
        from ddd_motor2.reglas import Criterio
        out = Path(os.environ["DDD_BATERIA_OUT"])
        e = entrada_bateria("pais_vasco", out)
        comp = next((out / "competicion" / "pais_vasco" / "canonico").glob("*_m06_composicion_distritos.csv"))
        c = Candidato("canonico", "canonico", None, 0)
        juzgar(c, Salida(comp), e, Criterio(), comp, "D8")
        self.assertEqual(c.estado, "VALIDO", c.detalle)
        self.assertEqual(c.fuera_tolerancia, c.natural[0])
        self.assertNotEqual(c.extra["metricas_regionales"]["fuera_tolerancia"], c.fuera_tolerancia)


if __name__ == "__main__":
    unittest.main()
