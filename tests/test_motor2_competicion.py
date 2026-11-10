#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · orquestador de la competición canónico + GerryChain (generadores sintéticos; solo stdlib)."""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fractions import Fraction  # noqa: E402

from ddd_motor2.calidad import huella_plan  # noqa: E402
from ddd_motor2.competicion import Candidato, EntradaTerritorio, Salida, competir  # noqa: E402

# Cuatro unidades en línea A-B-C-D, un municipio cada una, una provincia, K=2.
POB = {"A": 100, "B": 100, "C": 100, "D": 100}
CFG = {"validation": {"expected_districts": 2, "population_floor_ratio": 0.8, "population_cap_ratio": 1.2,
                      "target_tolerance_ratio": 0.1, "require_single_province_per_district": True,
                      "require_municipality_discipline": True}}


def escribir_comp(ruta: Path, plan: dict, pob=POB, cerradas=()):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"])
        for i, (u, d) in enumerate(sorted(plan.items())):
            w.writerow([f"220010100{i}", d, pob[u], "22", f"2200{i}", u, "1" if u in cerradas else "0"])
    return ruta


class Fijo:
    """Generador sintético: plan por semilla (None = falla)."""

    def __init__(self, nombre, planes, pob=POB, cerradas=()):
        self.nombre, self.planes, self.pob, self.llamadas, self.cerradas = nombre, planes, pob, [], cerradas

    def generar(self, entrada, semilla, destino):
        self.llamadas.append(semilla)
        plan = self.planes.get(semilla)
        if plan == "excepcion":
            raise RuntimeError("roto")
        if plan is None:
            return Salida(None, "FALLO_M05", "sin plan")
        return Salida(escribir_comp(Path(destino) / "comp.csv", plan, self.pob, self.cerradas))


class Competicion(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        grafo = self.tmp / "grafo.json"
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b], "edge_type": "geometric"} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        self.entrada = EntradaTerritorio("prueba", CFG, grafo)

    def test_gana_el_mejor_y_nunca_peor_que_el_canonico(self):
        pob = {"A": 90, "B": 110, "C": 100, "D": 100}
        canon = Fijo("canonico", {None: {"A": "1", "B": "1", "C": "2", "D": "2"}}, pob)  # 200/200
        gc = Fijo("gerrychain", {1: {"A": "1", "B": "2", "C": "2", "D": "2"},              # 90/310: techo
                                 2: {"A": "x", "B": "x", "C": "y", "D": "y"},              # igual al canónico
                                 3: None, 4: "excepcion"}, pob)
        r = competir(self.entrada, canon, gc, [1, 2, 3, 4], self.tmp / "out", exhaustivo=False)
        self.assertEqual(r.ganador.id, "canonico")  # empate con s2 (mismo plan): gana el orden
        estados = {c.id: c.estado for c in r.candidatos}
        self.assertEqual(estados, {"canonico": "VALIDO", "gerrychain-s1": "INVALIDO", "gerrychain-s2": "VALIDO",
                                   "gerrychain-s3": "FALLO_GENERADOR", "gerrychain-s4": "FALLO_GENERADOR"})
        s2 = next(c for c in r.candidatos if c.id == "gerrychain-s2")
        self.assertEqual(s2.huella_plan, r.canonico.huella_plan)
        d = r.a_dict()
        self.assertEqual([c["id"] for c in d["candidatos"]][:2], ["canonico", "gerrychain-s2"])
        self.assertEqual(d["candidatos"][-1]["id"], "gerrychain-s4")
        json.dumps(d)

    def test_cadena_mejora_desvio(self):
        pob = {"A": 95, "B": 105, "C": 110, "D": 90}
        canon = Fijo("canonico", {None: {"A": "1", "B": "2", "C": "2", "D": "2"}}, pob)  # 95/305: inválido
        gc = Fijo("gerrychain", {7: {"A": "1", "B": "1", "C": "2", "D": "2"},              # 200/200
                                 8: {"A": "1", "B": "1", "C": "1", "D": "2"}}, pob)        # 310/90
        r = competir(self.entrada, canon, gc, [7, 8], self.tmp / "out")
        self.assertEqual(r.canonico.estado, "INVALIDO")
        self.assertEqual(r.ganador.id, "gerrychain-s7")
        self.assertEqual(r.ganador.desvio_max, 0)
        self.assertEqual(gc.llamadas, [7, 8])

    def test_orden_lexicografico_fuera_de_tolerancia_antes_que_desvio(self):
        a = Candidato("a", "g", 1, 1, "VALIDO", duras=0, fuera_tolerancia=0, desvio_max=Fraction(1, 5), ecm=Fraction(1),
                      huella_plan="z")
        b = Candidato("b", "g", 2, 2, "VALIDO", duras=0, fuera_tolerancia=1, desvio_max=Fraction(1, 50),
                      ecm=Fraction(0), huella_plan="a")
        c = Candidato("c", "g", 3, 3, "INVALIDO", duras=1, fuera_tolerancia=0, desvio_max=Fraction(0), ecm=Fraction(0))
        e = Candidato("e", "g", 4, 0, "FALLO_GENERADOR")
        self.assertEqual([x.id for x in sorted([e, c, b, a], key=Candidato.clave)], ["a", "b", "c", "e"])

    def test_desempate_por_huella_con_metricas_iguales(self):
        # Cuatro unidades de 100 en ciclo A-B-C-D-A: {A,B}{C,D} y {B,C}{D,A} empatan en todo salvo la huella.
        grafo = self.tmp / "ciclo.json"
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"))]}))
        e = EntradaTerritorio("ciclo", CFG, grafo)
        p1 = {"A": "1", "B": "1", "C": "2", "D": "2"}
        p2 = {"A": "1", "B": "2", "C": "2", "D": "1"}
        canon = Fijo("canonico", {None: None})
        gc = Fijo("gerrychain", {1: p1, 2: p2})
        r = competir(e, canon, gc, [1, 2], self.tmp / "o1")
        c1, c2 = r.candidatos[1], r.candidatos[2]
        self.assertEqual(c1.clave()[:5], c2.clave()[:5])
        self.assertNotEqual(c1.huella_plan, c2.huella_plan)
        esperado = min((c1, c2), key=lambda c: c.huella_plan)
        self.assertEqual(r.ganador.id, esperado.id)
        r2 = competir(e, canon, Fijo("gerrychain", {1: p2, 2: p1}), [1, 2], self.tmp / "o2")  # orden inverso
        self.assertEqual(r2.ganador.huella_plan, esperado.huella_plan)

    def test_canonico_falla_y_nadie_valido(self):
        pob = {"A": 95, "B": 105, "C": 110, "D": 90}
        r = competir(self.entrada, Fijo("canonico", {}, pob),
                     Fijo("gerrychain", {1: {"A": "1", "B": "2", "C": "2", "D": "2"}}, pob), [1], self.tmp / "o")
        self.assertEqual(r.canonico.estado, "FALLO_GENERADOR")
        self.assertEqual((r.ganador.id, r.ganador.estado), ("gerrychain-s1", "INVALIDO"))
        self.assertFalse(r.valido)
        self.assertFalse(r.a_dict()["valido"])

    def test_sin_referencia_de_nucleos_no_gana_un_plan_con_cerradas(self):
        plan = {"A": "1", "B": "1", "C": "2", "D": "2"}
        r = competir(self.entrada, Fijo("canonico", {}), Fijo("gerrychain", {1: plan}, cerradas=("A", "B")), [1],
                     self.tmp / "o")
        self.assertEqual(r.candidatos[1].estado, "ERROR_DATOS")
        self.assertIn("núcleos", r.candidatos[1].detalle)
        self.assertFalse(r.valido)

    def test_huella_plan_no_depende_de_etiquetas(self):
        self.assertEqual(huella_plan({"A": "1", "B": "2"}), huella_plan({"A": "q", "B": "p"}))
        self.assertNotEqual(huella_plan({"A": "1", "B": "1"}), huella_plan({"A": "1", "B": "2"}))

    def test_semillas_repetidas(self):
        with self.assertRaises(ValueError):
            competir(self.entrada, Fijo("canonico", {}), Fijo("gerrychain", {}), [1, 1], self.tmp / "o")


class Exhaustivo(unittest.TestCase):
    """T-175: en un territorio pequeño la competición enumera todos los planes válidos y compite el mejor."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        grafo = self.tmp / "grafo.json"
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        self.entrada = EntradaTerritorio("prueba", CFG, grafo)

    def test_el_exhaustivo_gana_si_las_cadenas_no_llegan(self):
        # A-B-C-D 90/110/100/100: el único válido es AB|CD (200/200). El canónico y la cadena
        # dan planes inválidos; la enumeración encuentra el único válido.
        pob = {"A": 90, "B": 110, "C": 100, "D": 100}
        malo = {"A": "1", "B": "2", "C": "2", "D": "2"}
        r = competir(self.entrada, Fijo("canonico", {None: malo}, pob), Fijo("gerrychain", {1: malo}, pob), [1],
                     self.tmp / "o")
        self.assertEqual(r.ganador.id, "exhaustivo")
        self.assertTrue(r.valido)
        self.assertEqual((r.exhaustivo["metodo"], r.exhaustivo["completo"], r.exhaustivo["validos"]),
                         ("enumeracion", True, 1))
        self.assertEqual(r.ganador.huella_plan, huella_plan({"A": "1", "B": "1", "C": "2", "D": "2"}))

    def test_presupuesto_agotado_no_compite(self):
        from ddd_motor2.reglas import Criterio
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        r = competir(self.entrada, Fijo("canonico", {None: bueno}), Fijo("gerrychain", {1: bueno}), [1],
                     self.tmp / "o", criterio=Criterio(presupuesto_nodos=2))
        self.assertEqual((r.exhaustivo["metodo"], r.exhaustivo["completo"]), ("cadena", False))
        self.assertNotIn("exhaustivo", [c.id for c in r.candidatos])
        self.assertEqual(r.ganador.id, "canonico")

    def test_empata_con_el_canonico_si_ya_es_el_optimo(self):
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        r = competir(self.entrada, Fijo("canonico", {None: bueno}), Fijo("gerrychain", {}), [1], self.tmp / "o")
        ex = next(c for c in r.candidatos if c.id == "exhaustivo")
        self.assertEqual(ex.clave()[:6], r.canonico.clave()[:6])
        self.assertEqual(r.ganador.id, "canonico")  # desempate final por orden

if __name__ == "__main__":
    unittest.main()
