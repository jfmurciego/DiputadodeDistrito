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

from ddd_motor2.competicion import Candidato, EntradaTerritorio, Salida, competir, huella_plan  # noqa: E402

# Cuatro unidades en línea A-B-C-D, un municipio cada una, una provincia, K=2.
POB = {"A": 100, "B": 100, "C": 100, "D": 100}
CFG = {"validation": {"expected_districts": 2, "population_floor_ratio": 0.8, "population_cap_ratio": 1.2,
                      "target_tolerance_ratio": 0.1, "require_single_province_per_district": True,
                      "require_municipality_discipline": True}}


def escribir_comp(ruta: Path, plan: dict, pob=POB):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"])
        for i, (u, d) in enumerate(sorted(plan.items())):
            w.writerow([f"220010100{i}", d, pob[u], "22", f"2200{i}", u, "0"])
    return ruta


class Fijo:
    """Generador sintético: plan por semilla (None = falla)."""

    def __init__(self, nombre, planes, pob=POB):
        self.nombre, self.planes, self.pob, self.llamadas = nombre, planes, pob, []

    def generar(self, entrada, semilla, destino):
        self.llamadas.append(semilla)
        plan = self.planes.get(semilla)
        if plan == "excepcion":
            raise RuntimeError("roto")
        if plan is None:
            return Salida(None, "FALLO_M05", "sin plan")
        return Salida(escribir_comp(Path(destino) / "comp.csv", plan, self.pob))


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
        r = competir(self.entrada, canon, gc, [1, 2, 3, 4], self.tmp / "out")
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

    def test_huella_plan_no_depende_de_etiquetas(self):
        self.assertEqual(huella_plan({"A": "1", "B": "2"}), huella_plan({"A": "q", "B": "p"}))
        self.assertNotEqual(huella_plan({"A": "1", "B": "1"}), huella_plan({"A": "1", "B": "2"}))

    def test_semillas_repetidas(self):
        with self.assertRaises(ValueError):
            competir(self.entrada, Fijo("canonico", {}), Fijo("gerrychain", {}), [1, 1], self.tmp / "o")


if __name__ == "__main__":
    unittest.main()
