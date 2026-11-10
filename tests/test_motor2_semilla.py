#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · semilla pública y reproducibilidad de la competición (solo stdlib)."""
from __future__ import annotations

import hashlib
import json
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.competicion import EntradaTerritorio, Salida, competir_publico  # noqa: E402
from ddd_motor2.reglas import ErrorContrato  # noqa: E402
from ddd_motor2.semilla import MODULO, ancla, semillas  # noqa: E402
from tests.test_motor2_competicion import CFG, POB, escribir_comp  # noqa: E402

SHA_P, SHA_S = "a" * 64, "b" * 64


def cfg(p=SHA_P, s=SHA_S):
    c = json.loads(json.dumps(CFG))
    c["generation_state"] = {"source_inputs": [{"path": "inputs/65034.csv.zip", "sha256": p, "role": "population"},
                                               {"path": "inputs/seccionado_2025.zip", "sha256": s,
                                                "role": "target_sectioning"}]}
    return c


class Aleatorio:
    """Generador sintético que depende de la semilla (como una cadena): parte A-B-C-D por un corte al azar."""

    def __init__(self, nombre):
        self.nombre = nombre

    def generar(self, entrada, semilla, destino):
        corte = 2 if semilla is None else random.Random(semilla).choice([1, 2, 3])
        plan = {u: ("1" if i < corte else "2") for i, u in enumerate(sorted(POB))}
        return Salida(escribir_comp(Path(destino) / "comp.csv", plan))


class Semilla(unittest.TestCase):
    def test_formula_publica(self):
        base = f"ddd-semilla-publica/1|{SHA_P}|{SHA_S}|aragon"
        esperada = [int(hashlib.sha256(f"{base}|{i}".encode()).hexdigest()[:16], 16) % MODULO + 1 for i in (1, 2, 3)]
        self.assertEqual(semillas(cfg(), "aragon", 3), esperada)
        self.assertTrue(all(1 <= x <= 2**31 - 2 for x in esperada))

    def test_depende_del_dato_y_del_territorio(self):
        s = semillas(cfg(), "aragon", 5)
        self.assertEqual(s, semillas(cfg(), "aragon", 5))
        self.assertEqual(s[:3], semillas(cfg(), "aragon", 3))  # ampliar N conserva las primeras
        self.assertNotEqual(s, semillas(cfg(), "murcia", 5))
        self.assertNotEqual(s, semillas(cfg(p="c" * 64), "aragon", 5))
        self.assertNotEqual(s, semillas(cfg(s="c" * 64), "aragon", 5))

    def test_sin_huella_falla(self):
        c = cfg()
        c["generation_state"]["source_inputs"].pop()
        with self.assertRaisesRegex(ErrorContrato, "target_sectioning"):
            ancla(c)
        with self.assertRaisesRegex(ErrorContrato, "huella no válida"):
            ancla(cfg(p="xyz"))


class Reproducibilidad(unittest.TestCase):
    def ejecutar(self, tmp):
        grafo = tmp / "grafo.json"
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        e = EntradaTerritorio("prueba", cfg(), grafo)
        return competir_publico(e, Aleatorio("canonico"), Aleatorio("gerrychain"), tmp / "out", n_cadenas=5)

    def test_dos_ejecuciones_misma_huella(self):
        r1 = self.ejecutar(Path(tempfile.mkdtemp()))
        r2 = self.ejecutar(Path(tempfile.mkdtemp()))
        self.assertEqual(r1.huella(), r2.huella())
        self.assertEqual(r1.ganador.huella_plan, r2.ganador.huella_plan)
        self.assertEqual(r1.ganador.composicion_sha256, r2.ganador.composicion_sha256)
        d = r1.a_dict()
        self.assertEqual(d["semilla_publica"]["semillas"], semillas(cfg(), "prueba", 5))
        self.assertEqual([c.semilla for c in r1.candidatos[1:]], d["semilla_publica"]["semillas"])


if __name__ == "__main__":
    unittest.main()
