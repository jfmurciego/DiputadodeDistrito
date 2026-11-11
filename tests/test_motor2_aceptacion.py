#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-194 · criterio escrito y automatizado de «el motor nuevo puede relevar» (docs/ARQUITECTURA/ACEPTACION_MOTOR2.md).

VERSIÓN: 1.0.0
ANTERIOR: ninguna (fichero nuevo)
(a) huella bit a bit fija en Soria, Álava y Melilla (semilla pública D-50, N fijo); (b) todo ganador pasa el
certificador (núcleo único, R-NUCLEO y atomicidad M04); (c) nunca peor que el canónico en los 71, leído del informe de
la batería ya generado (no recalcula); (d) casos adversos: el certificador rechaza; (e) mismo mapa con id viejo y nuevo
(D-60), pendiente hasta el corte 5.0.0.
Solo stdlib: los territorios son fixtures sintéticos con generador determinista por semilla. La variante con el motor
real (GerryChain + entradas de la batería) se activa con DDD_ACEPTACION_BATERIA=<carpeta de la batería>.
"""
from __future__ import annotations

import csv
import json
import os
import random
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.adaptadores import problema_y_plan  # noqa: E402
from ddd_motor2.competicion import EntradaTerritorio, Salida, competir_publico  # noqa: E402
from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, evaluar  # noqa: E402
from herramientas.certificador_exacto import juzgar  # noqa: E402
from tests.test_motor2_competicion import escribir_comp  # noqa: E402
from tests.test_motor2_semilla import cfg as cfg_con_ancla  # noqa: E402

# ---- Parámetros del criterio (los fijan T-179 / T-180 / T-205; cambiarlos exige regenerar HUELLAS_FIJAS) --------------------
N_CADENAS = 5          # N de semillas públicas por territorio
CRITERIO = Criterio()  # criterio del núcleo: el vigente
FUNCION = "D8"         # función de calidad de la competición (T-205: D8 por defecto en competir.py)
TERRITORIOS = {"soria": (4, 2), "alava": (6, 3), "melilla": (8, 2)}  # nombre: (unidades, K); 100 habitantes cada una
ID_TABLA = {"soria": "congreso_soria", "alava": "congreso_alava", "melilla": "melilla"}  # T-265: id de la tabla maestra (semilla)
CERRADAS = {"soria": ("U0", "U1")}  # núcleo cerrado de referencia (R-NUCLEO) en el plan canónico
HUELLAS_FIJAS = {  # T-265 (D-90): regeneradas con la semilla del código oficial. huella_resultado de la competición: reglas, semillas, planes y composiciones de todos los candidatos
    "soria": "6ed61e24880aa8ec1f709f5001379e2f92ff0f08f76012184ee4a254df332ba8",
    "alava": "616f212889f202855eca0a58ba9dc93ed89fe090920e61e0ac44aeea73b8361a",
    "melilla": "1dfa8476c5d724556762ae3e40a6688a95abebb0ab7ec7df1e5556d21543f89f",
}
HUELLAS_FIJAS_A = {  # las de la función A (antes de T-205; regeneradas en T-265 por la semilla): la competición con --funcion A no cambia
    "soria": "115e61c5c35fd619121a9217087703e242c413859ac29dbab340b91758535cb6",
    "alava": "28b4350290cea09f1150e4b97597309d1a326b36b6641dd02393a3c871a500f0",
    "melilla": "5d464977e086fd71c359af9d0c444296660e9bfd55e65ea2ba5f486b37c3674e",
}
ESTUDIO = ROOT / "docs" / "ESTUDIOS" / "T132_BATERIA_MOTOR"


def unidades(t):
    return [f"U{i}" for i in range(TERRITORIOS[t][0])]


def cortar(us, cortes):
    """Plan contiguo en línea: `cortes` = posiciones donde empieza el distrito siguiente."""
    d, plan = 1, {}
    for i, u in enumerate(us):
        if i in cortes:
            d += 1
        plan[u] = str(d)
    return plan


class Generador:
    """Determinista por semilla: K-1 cortes al azar sobre la línea (None = el plan canónico, cortes iguales)."""

    def __init__(self, nombre, t):
        self.nombre, self.t = nombre, t

    def generar(self, entrada, semilla, destino):
        us, k = unidades(self.t), TERRITORIOS[self.t][1]
        n = len(us)
        cortes = {n * j // k for j in range(1, k)} if semilla is None else set(random.Random(semilla).sample(range(1, n), k - 1))
        pob = {u: 100 for u in us}
        return Salida(escribir_comp(Path(destino) / "comp.csv", cortar(us, cortes), pob, CERRADAS.get(self.t, ())))


def cfg_territorio(t):
    c = cfg_con_ancla()
    c["validation"] = dict(c["validation"], expected_districts=TERRITORIOS[t][1])
    return c


def entrada(t, tmp):
    us = unidades(t)
    secc = {u: f"220010100{i}" for i, u in enumerate(us)}
    g = tmp / f"grafo_{t}.json"
    g.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
        {"u": secc[a], "v": secc[b], "edge_type": "geometric"} for a, b in zip(us, us[1:])]}))
    return EntradaTerritorio(ID_TABLA[t], cfg_territorio(t), g)


def competir_t(t, tmp, funcion=FUNCION):
    e = entrada(t, tmp)
    return e, competir_publico(e, Generador("canonico", t), Generador("gerrychain", t), tmp / f"out_{t}",
                               n_cadenas=N_CADENAS, criterio=CRITERIO, funcion=funcion)


class HuellaFija(unittest.TestCase):
    """(a) La misma entrada, semilla y N dan la misma huella, ahora y siempre (fijada en HUELLAS_FIJAS)."""

    def test_huella_bit_a_bit(self):
        for t in TERRITORIOS:
            with self.subTest(t=t):
                h1 = competir_t(t, Path(tempfile.mkdtemp()))[1].huella()
                h2 = competir_t(t, Path(tempfile.mkdtemp()))[1].huella()
                self.assertEqual(h1, h2, "dos ejecuciones difieren")
                self.assertEqual(h1, HUELLAS_FIJAS[t], f"la huella de {t} cambió: si es intencionado, actualiza HUELLAS_FIJAS")

    def test_huella_funcion_a_compatible(self):
        """Pin de compatibilidad (T-205): con la función A, las huellas de antes de D8."""
        for t in TERRITORIOS:
            with self.subTest(t=t):
                self.assertEqual(competir_t(t, Path(tempfile.mkdtemp()), "A")[1].huella(), HUELLAS_FIJAS_A[t])

    @unittest.skipUnless(os.environ.get("DDD_ACEPTACION_BATERIA"), "motor real: define DDD_ACEPTACION_BATERIA")
    def test_motor_real_dos_ejecuciones(self):
        from ddd_motor2.competir import competir_territorio
        out = Path(os.environ["DDD_ACEPTACION_BATERIA"])
        for t in ("soria", "alava", "melilla"):
            nombre = t if t == "melilla" else f"congreso_{t}"
            with self.subTest(t=nombre):
                a = competir_territorio(nombre, out, N_CADENAS)
                b = competir_territorio(nombre, out, N_CADENAS)
                self.assertEqual(a.get("estado"), "VALIDO", a)
                self.assertEqual(a["huella_resultado"], b["huella_resultado"])


class GanadorCertificado(unittest.TestCase):
    """(b) Todo plan ganador pasa el certificador independiente (núcleo, R-NUCLEO, atomicidad M04) y el contrato."""

    def test_ganadores(self):
        for t in TERRITORIOS:
            with self.subTest(t=t):
                tmp = Path(tempfile.mkdtemp())
                e, r = competir_t(t, tmp)
                self.assertTrue(r.valido, r.ganador.detalle)
                ref = Path(r.canonico.composicion)
                problema, plan, _ = problema_y_plan(Path(r.ganador.composicion), e.grafo_m03, e.cfg, referencia_nucleos=ref)
                if t in CERRADAS:
                    self.assertTrue(any(u.nucleo_cerrado for u in problema.unidades), "sin núcleos: R-NUCLEO trivial")
                reglas = Reglas.desde_contrato(e.cfg, CRITERIO)
                veredicto = juzgar(problema, reglas, plan, {})
                self.assertEqual(veredicto["estado"], "PASS", veredicto)
                self.assertEqual(veredicto["violaciones"], [])
                self.assertEqual(len(set(plan.values())), TERRITORIOS[t][1])


class NuncaPeorQueElCanonico(unittest.TestCase):
    """(c) Sobre el informe de la batería ya generado (COMPETIDOR.csv): no se recalcula nada."""

    @classmethod
    def setUpClass(cls):
        f = ESTUDIO / "COMPETIDOR.csv"
        if not f.is_file():
            raise unittest.SkipTest("sin informe de la batería")
        with open(f, newline="", encoding="utf-8") as fh:
            cls.filas = list(csv.DictReader(fh))

    def test_71_validos_y_ninguno_peor(self):
        self.assertEqual(len(self.filas), 71)
        self.assertEqual(len({f["territorio"] for f in self.filas}), 71)
        for f in self.filas:
            with self.subTest(t=f["territorio"]):
                self.assertEqual(f["validacion"], "PASS")
                self.assertIn(f["frente_al_canonico"], ("mejora", "empata"))
                # misma regla que la competición: primero distritos fuera de tolerancia, después desvío máximo
                g = (int(f["fuera_tolerancia"]), float(f["desvio_max"]))
                c = (int(f["fuera_tolerancia_canonico"]), float(f["desvio_max_canonico"]))
                self.assertLessEqual(g, c)

    def test_el_resumen_es_coherente(self):
        n = {k: sum(f["frente_al_canonico"] == k for f in self.filas) for k in ("mejora", "empata", "empeora")}
        self.assertEqual(n["empeora"], 0)
        self.assertEqual(n["mejora"] + n["empata"], 71)


def _problema(pob, municipios, provincias, aristas):
    us = [Unidad(id=u, poblacion=p, municipio=municipios[u], provincia=provincias[u]) for u, p in pob.items()]
    return Problema(us, tuple(aristas))


def _reglas(k, **extra):
    v = {"expected_districts": k, "population_floor_ratio": "0.8", "population_cap_ratio": "1.2",
         "target_tolerance_ratio": "0.1", "require_single_province_per_district": True,
         "require_municipality_discipline": True, **extra}
    return Reglas.desde_contrato({"validation": v}, CRITERIO)


LINEA = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F")]
POB6 = {u: 100 for u in "ABCDEF"}
MUN6 = {u: f"2200{i}" for i, u in enumerate("ABCDEF")}
PROV1 = {u: "22" for u in "ABCDEF"}


class CasosAdversos(unittest.TestCase):
    """(d) El certificador rechaza planes que rompen una regla dura, con el código estable de la regla."""

    def rechaza(self, problema, reglas, plan, codigo):
        self.assertIn(codigo, evaluar(problema, reglas, plan).codigos())
        v = juzgar(problema, reglas, plan, {})
        self.assertEqual(v["estado"], "FAIL")
        self.assertTrue(any(x.startswith(codigo) for x in v["violaciones"]), v)

    def test_base_valida(self):
        p = _problema(POB6, MUN6, PROV1, LINEA)
        plan = {u: "1" if u in "ABC" else "2" for u in "ABCDEF"}
        self.assertEqual(juzgar(p, _reglas(2, province_districts={"22": 2}), plan, {})["estado"], "PASS")

    def test_distrito_discontinuo(self):
        p = _problema(POB6, MUN6, PROV1, LINEA)
        plan = {"A": "1", "B": "1", "F": "1", "C": "2", "D": "2", "E": "2"}
        self.rechaza(p, _reglas(2, province_districts={"22": 2}), plan, "R-CONTIG")

    def test_fuera_de_techo_y_de_suelo(self):
        p = _problema(POB6, MUN6, PROV1, LINEA)
        plan = {u: "1" if u in "ABCD" else "2" for u in "ABCDEF"}  # 400 y 200 sobre objetivo 300
        r = _reglas(2, province_districts={"22": 2})
        self.rechaza(p, r, plan, "R-POB-TECHO")
        self.rechaza(p, r, plan, "R-POB-SUELO")

    def test_municipio_partido_de_mas(self):
        # el municipio M = {B, C} se reparte entre dos distritos que además tienen otros municipios: 2 mixtos > 1
        mun = {**MUN6, "C": MUN6["B"]}
        p = _problema(POB6, mun, PROV1, LINEA)
        plan = {"A": "1", "B": "1", "C": "2", "D": "2", "E": "3", "F": "3"}
        self.rechaza(p, _reglas(3, province_districts={"22": 3}), plan, "R-MUN-MIXTOS")

    def test_distrito_que_cruza_provincia(self):
        prov = {**PROV1, "D": "28", "E": "28", "F": "28"}
        p = _problema(POB6, MUN6, prov, LINEA)
        plan = {u: "1" if u in "ABD" else "2" for u in "ABCDEF"}  # cada distrito mezcla las provincias 22 y 28
        self.rechaza(p, _reglas(2, province_districts={"22": 1, "28": 1}), plan, "R-PROV")


class MismoMapaIdViejoYNuevo(unittest.TestCase):
    """(e) D-60: el motor con identificador viejo y nuevo y la misma semilla da el mismo mapa bit a bit."""

    @unittest.skip("pendiente hasta el corte 5.0.0 (D-60, docs/ARQUITECTURA/CORTE_5_0_0.md): aún no existen los ids nuevos")
    def test_mismo_mapa(self):
        # tras el corte: competir con el id viejo y con el nuevo («nac01» ↔ «NAC01 · Soria») y comparar
        # competir_t(...).ganador.composicion_sha256 y .huella() de ambos: deben ser idénticos.
        self.fail("sin implementar hasta el corte 5.0.0")


if __name__ == "__main__":
    unittest.main()
