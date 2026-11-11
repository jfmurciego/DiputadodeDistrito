#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · semilla pública y reproducibilidad de la competición (solo stdlib). T-265: código oficial (D-90)."""
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
from ddd_motor2.semilla import MODULO, ancla, codigo, descripcion, semillas  # noqa: E402
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
        base = f"ddd-semilla-publica/2|{SHA_P}|{SHA_S}|AUT02"  # T-265: código oficial de la tabla maestra
        esperada = [int(hashlib.sha256(f"{base}|{i}".encode()).hexdigest()[:16], 16) % MODULO + 1 for i in (1, 2, 3)]
        self.assertEqual(semillas(cfg(), "aragon", 3), esperada)
        self.assertTrue(all(1 <= x <= 2**31 - 2 for x in esperada))

    def test_depende_del_dato_y_del_territorio(self):
        s = semillas(cfg(), "aragon", 5)
        self.assertEqual(s, semillas(cfg(), "aragon", 5))
        self.assertEqual(s[:3], semillas(cfg(), "aragon", 3))  # ampliar N conserva las primeras
        self.assertNotEqual(s, semillas(cfg(), "region_de_murcia", 5))
        self.assertNotEqual(s, semillas(cfg(p="c" * 64), "aragon", 5))
        self.assertNotEqual(s, semillas(cfg(s="c" * 64), "aragon", 5))

    def test_sin_huella_falla(self):
        c = cfg()
        c["generation_state"]["source_inputs"].pop()
        with self.assertRaisesRegex(ErrorContrato, "target_sectioning"):
            ancla(c)
        with self.assertRaisesRegex(ErrorContrato, "huella no válida"):
            ancla(cfg(p="xyz"))


class CodigoOficial(unittest.TestCase):
    """T-265 / D-90: la semilla sale del código de la tabla maestra, no del nombre de la carpeta."""

    def test_renombrar_la_carpeta_no_cambia_la_semilla(self):
        from ddd_motor2.produccion import _territorio
        for viejo, nuevo, cod in (("congreso_alava", "nac01", "NAC01"), ("la_rioja", "aut17", "AUT17"),
                                  ("congreso_la_rioja", "nac26", "NAC26"), ("melilla", "aut19", "AUT19")):
            with self.subTest(t=viejo):
                a = _territorio(Path(f"territorios/{viejo}/config/{viejo}_2025.yaml"))
                b = _territorio(Path(f"territorios/{nuevo}/config/{nuevo}_2025.yaml"))
                self.assertNotEqual(a, b)  # la carpeta cambia…
                self.assertEqual(codigo(a), cod)
                self.assertEqual(semillas(cfg(), a, 10), semillas(cfg(), b, 10))  # …y la semilla no
                self.assertEqual(semillas(cfg(), a, 10), semillas(cfg(), cod, 10))
                da, db = descripcion(cfg(), a, 3), descripcion(cfg(), b, 3)
                self.assertEqual({k: v for k, v in da.items() if k != "territorio"},
                                 {k: v for k, v in db.items() if k != "territorio"})

    def test_la_misma_provincia_y_comunidad_son_territorios_distintos(self):
        self.assertNotEqual(semillas(cfg(), "la_rioja", 5), semillas(cfg(), "congreso_la_rioja", 5))

    def test_fuera_de_la_tabla_falla(self):
        for t in ("prueba", "congreso350_alava", "nac01-350"):
            with self.subTest(t=t), self.assertRaisesRegex(ErrorContrato, "tabla maestra"):
                semillas(cfg(), t, 3)

    def test_descripcion_registra_codigo_y_tabla(self):
        d = descripcion(cfg(), "congreso_alava", 3)
        tabla = ROOT / "configuracion" / "notacion_territorial.csv"
        self.assertEqual((d["esquema"], d["codigo"]), ("ddd-semilla-publica/2", "NAC01"))
        self.assertEqual(d["tabla_maestra"], {"ruta": "configuracion/notacion_territorial.csv",
                                              "sha256": hashlib.sha256(tabla.read_bytes()).hexdigest()})
        self.assertIn("codigo_semilla", d["derivacion"])

    def test_huella_del_resultado_incluye_la_semilla(self):
        r = Reproducibilidad().ejecutar(Path(tempfile.mkdtemp()))
        h = r.huella()
        r.semilla_publica = dict(r.semilla_publica, tabla_maestra={"sha256": "0" * 64})
        self.assertNotEqual(h, r.huella())

    def test_huella_motor2_incluye_la_tabla_maestra(self):
        from ddd_motor2.produccion import huella_motor
        ficheros = huella_motor()["engine_files"]
        self.assertIn("configuracion/notacion_territorial.csv", ficheros)
        self.assertIn("ddd_core/territorio_ids.py", ficheros)


class Reproducibilidad(unittest.TestCase):
    def ejecutar(self, tmp):
        grafo = tmp / "grafo.json"
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b]} for a, b in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        e = EntradaTerritorio("la_rioja", cfg(), grafo)
        return competir_publico(e, Aleatorio("canonico"), Aleatorio("gerrychain"), tmp / "out", n_cadenas=5)

    def test_dos_ejecuciones_misma_huella(self):
        r1 = self.ejecutar(Path(tempfile.mkdtemp()))
        r2 = self.ejecutar(Path(tempfile.mkdtemp()))
        self.assertEqual(r1.huella(), r2.huella())
        self.assertEqual(r1.ganador.huella_plan, r2.ganador.huella_plan)
        self.assertEqual(r1.ganador.composicion_sha256, r2.ganador.composicion_sha256)
        d = r1.a_dict()
        self.assertEqual(d["semilla_publica"]["semillas"], semillas(cfg(), "la_rioja", 5))
        self.assertEqual([c.semilla for c in r1.candidatos if c.generador == "gerrychain"], d["semilla_publica"]["semillas"])


if __name__ == "__main__":
    unittest.main()
