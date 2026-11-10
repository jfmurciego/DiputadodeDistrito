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


class FueraDelContrato(unittest.TestCase):
    """T-211 (D-68): con cuotas de varias provincias, el primer término de D8 es el recuento del contrato (objetivo
    regional, como reglas.evaluar), no el de la circunscripción. Provincia 22 (2 escaños, 400 hab.): A-B-C-D-E en línea;
    provincia 44 (1 escaño): F, 230 hab. Objetivo regional 210 ± 21; de la 22, 200 ± 20.
    Canónico: corte tras C (200/200, ninguno fuera). Cadena: corte tras B (186/214) por una frontera corta: dentro de
    tolerancia de su circunscripción (−7 %), pero 186 queda fuera del contrato (−11,4 %). Con 1.3.0 ganaba la cadena."""

    POB = {"A": 86, "B": 100, "C": 14, "D": 100, "E": 100, "F": 230}
    PROV = {"A": "22", "B": "22", "C": "22", "D": "22", "E": "22", "F": "44"}
    BORDE = {("A", "B"): 3000.0, ("B", "C"): 100.0, ("C", "D"): 3000.0, ("D", "E"): 3000.0, ("E", "F"): 3000.0}
    CANONICO = {"A": "1", "B": "1", "C": "1", "D": "2", "E": "2", "F": "3"}
    CADENA = {"A": "1", "B": "1", "C": "2", "D": "2", "E": "2", "F": "3"}

    def competir(self, funcion):
        tmp = Path(tempfile.mkdtemp())
        cfg = {"validation": {**CFG["validation"], "expected_districts": 3, "population_floor_ratio": 0.5,
                              "population_cap_ratio": 1.5, "province_districts": {"22": 2, "44": 1}}}
        secc = {u: f"{self.PROV[u]}0010100{i}" for i, u in enumerate(sorted(self.POB))}
        g = tmp / "grafo.json"
        g.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[b], "edge_type": "geometric", "shared_border_m": w}
            for (a, b), w in self.BORDE.items()]}))
        pob, prov = self.POB, self.PROV

        class Gen:
            def __init__(self, nombre, plan):
                self.nombre, self.plan = nombre, plan

            def generar(self, entrada, semilla, destino):
                ruta = Path(destino) / "comp.csv"
                ruta.parent.mkdir(parents=True, exist_ok=True)
                with open(ruta, "w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh)
                    w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id",
                                "ddd_closed_urban"])
                    for u in sorted(pob):
                        w.writerow([secc[u], self.plan[u], pob[u], prov[u], secc[u][:5], u, "0"])
                return Salida(ruta)
        return competir(EntradaTerritorio("sintetico", cfg, g), Gen("canonico", self.CANONICO),
                        Gen("cadena", self.CADENA), [5], tmp / "out", exhaustivo=False, funcion=funcion)

    def test_d8_no_elige_mas_fuera_que_el_canonico(self):
        r = self.competir("D8")
        cad = next(c for c in r.candidatos if c.id == "cadena-s5")
        self.assertTrue(all(c.estado == "VALIDO" for c in r.candidatos), [c.a_dict() for c in r.candidatos])
        self.assertEqual((r.canonico.fuera_tolerancia, cad.fuera_tolerancia), (0, 1))
        self.assertEqual((r.canonico.natural[0], cad.natural[0]), (0, 1))  # primer término = recuento del contrato
        self.assertLess(cad.natural[3], r.canonico.natural[3])  # la cadena corta menos frontera…
        self.assertEqual(r.ganador.id, "canonico")  # …pero gana la población dentro de tolerancia
        self.assertEqual(cad.extra["metricas_circunscripcion"]["fuera_tolerancia"], 0)
        self.assertLessEqual(r.ganador.fuera_tolerancia, r.canonico.fuera_tolerancia)

    def test_a_igual(self):
        r = self.competir("A")
        self.assertEqual(r.ganador.id, "canonico")
        self.assertNotIn("metricas_circunscripcion", r.canonico.extra)


class VigenteCompite(unittest.TestCase):
    """T-217: el vigente válido compite (orden 1) y el ganador nunca es peor; si no cumple el núcleo no compite."""

    def competir(self, plan_vigente):
        tmp = Path(tempfile.mkdtemp())
        return competir(entrada(tmp), Fijo("canonico", {None: plan_corte(2)}), Fijo("cadena", {7: plan_corte(2)}),
                        [7], tmp / "out", exhaustivo=False, funcion="D8",
                        vigente=Fijo("vigente", {None: plan_vigente}))

    def test_vigente_valido_gana(self):
        r = self.competir(plan_corte(3))  # corta por la frontera corta: mejor en D8 que el canónico
        self.assertEqual(r.ganador.id, "vigente")
        self.assertTrue(r.vigente["compite"])
        self.assertEqual([c.orden for c in sorted(r.candidatos, key=lambda c: c.orden)], [0, 1, 2])
        self.assertIn("vigente", r.a_dict())

    def test_vigente_invalido_no_compite(self):
        r = self.competir({u: "1" for u in UNIDADES})  # un solo distrito con K = 2
        self.assertFalse(r.vigente["compite"])
        self.assertEqual(r.vigente["estado"], "INVALIDO")
        self.assertNotIn("vigente", [c.id for c in r.candidatos])
        self.assertTrue(r.vigente["violaciones"])

    def test_sin_vigente_igual(self):
        tmp = Path(tempfile.mkdtemp())
        r = competir(entrada(tmp), Fijo("canonico", {None: plan_corte(2)}), Fijo("cadena", {7: plan_corte(3)}),
                     [7], tmp / "out", exhaustivo=False, funcion="D8")
        self.assertEqual(r.vigente, {})
        self.assertNotIn("vigente", r.a_dict())


class VigenteReparado(unittest.TestCase):
    """T-217 (D-66): el vigente publicado mete C en el núcleo cerrado {A, B} del canónico (R-NUCLEO); la reparación
    mínima pasa C al distrito de su vecina D, se juzga de nuevo y compite; lo publicado queda en «publicado»."""

    def test_repara_y_compite(self):
        self.repara(None)

    def test_repara_con_piezas_finas(self):  # ids «~» en A, B, D y E (divisibles con 0,45), núcleo cerrado {A, B}
        r = self.repara(0.45)
        cv = next(c for c in r.candidatos if c.id == "vigente")
        ids = {f["ddd_unit_id"] for f in csv.DictReader(open(cv.composicion, encoding="utf-8"))}
        self.assertIn("A~2200101000", ids)
        self.assertEqual(r.vigente["piezas_finas"]["secciones_sueltas"], 4)

    def repara(self, ratio):
        from ddd_motor2.generadores import Vigente

        class Cerrado:
            nombre = "canonico"

            def generar(self, entrada, semilla, destino):
                return Salida(escribir_comp(Path(destino) / "x_m06_composicion_distritos.csv", plan_corte(2), POB,
                                            cerradas=("A", "B")))
        tmp = Path(tempfile.mkdtemp())
        carpeta = tmp / "vig"
        carpeta.mkdir()
        (carpeta / "sintetico.csv").write_text("seccion,distrito,poblacion\n" + "".join(
            f"220010100{i},{'1' if i < 3 else '2'},0\n" for i in range(5)), encoding="utf-8")
        e = entrada(tmp)
        if ratio is not None:
            e = EntradaTerritorio("sintetico", {"validation": {**CFG["validation"],
                                                               "municipality_atomicity_limit_ratio": ratio}}, e.grafo_m03)
        r = competir(e, Cerrado(), Fijo("cadena", {7: plan_corte(2)}), [7], tmp / "out",
                     exhaustivo=False, funcion="D8", vigente=Vigente(carpeta))
        v = r.vigente
        self.assertEqual(v["publicado"]["violaciones"], [["R-NUCLEO", v["publicado"]["violaciones"][0][1]]])
        self.assertFalse(v["publicado"]["valido"])
        self.assertTrue(v["reparado"] and v["compite"], v)
        self.assertEqual(len(v["reparacion"]), 1)  # un solo paso
        cv = next(c for c in r.candidatos if c.id == "vigente")
        d = {f["CUSEC_KEY"]: f["district_id"] for f in csv.DictReader(open(cv.composicion, encoding="utf-8"))}
        self.assertEqual(d["2200101002"], d["2200101003"])  # C (6 hab.) pasa al distrito de su vecina D
        self.assertNotEqual(d["2200101001"], d["2200101002"])  # y el núcleo {A, B} queda solo
        self.assertIn("vigente", [c.id for c in r.candidatos])
        return r


class ReparaMixtos(unittest.TestCase):
    """T-217 (D-66, caso Ávila 05019): el municipio 22001 (M1, M2) en dos distritos mixtos (máximo 1); la reparación
    pasa la parte con menos población del municipio al otro distrito y el plan queda válido."""

    def test_r_mun_mixtos(self):
        from ddd_motor2.adaptadores import problema_y_plan
        from ddd_motor2.generadores import reparar
        from ddd_motor2.reglas import Reglas, evaluar
        tmp = Path(tempfile.mkdtemp())
        filas = [("2200201000", "1", 190, "22002", "X"), ("2200101000", "1", 9, "22001", "M1"),
                 ("2200101001", "2", 11, "22001", "M2"), ("2200301000", "2", 190, "22003", "Y")]
        comp = tmp / "c.csv"
        with open(comp, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"])
            for sec, d, p, m, u in filas:
                w.writerow([sec, d, p, "22", m, u, "0"])
        g = tmp / "g.json"
        g.write_text(json.dumps({"nodes": [f[0] for f in filas], "edges": [
            {"u": filas[i][0], "v": filas[i + 1][0], "edge_type": "geometric"} for i in range(3)]}))
        prob, plan, _ = problema_y_plan(comp, g, CFG)
        reglas = Reglas.desde_contrato(CFG)
        self.assertIn("R-MUN-MIXTOS", {v.regla for v in evaluar(prob, reglas, plan).violaciones})
        nuevo, notas = reparar(prob, reglas, plan)
        self.assertTrue(evaluar(prob, reglas, nuevo).valido, notas)
        self.assertEqual(nuevo["M1"], nuevo["M2"])
        self.assertEqual(nuevo["M1"], plan["M2"])  # se mueve la parte menor (M1, 9 hab.)
        self.assertEqual(sum(1 for u in plan if plan[u] != nuevo[u]), 1)

    def test_sin_reparacion_posible(self):
        from ddd_motor2.adaptadores import problema_y_plan
        from ddd_motor2.generadores import reparar
        from ddd_motor2.reglas import Reglas
        tmp = Path(tempfile.mkdtemp())
        comp = escribir_comp(tmp / "c.csv", {u: "1" for u in UNIDADES}, POB)  # un distrito con K = 2: R-K, sin arreglo
        prob, plan, _ = problema_y_plan(comp, entrada(tmp).grafo_m03, CFG)
        nuevo, notas = reparar(prob, Reglas.desde_contrato(CFG), plan)
        self.assertEqual(nuevo, {})
        self.assertTrue(notas)


class PiezasFinas(unittest.TestCase):
    """T-218: fuera del Congreso, sección por unidad en los municipios de más de ratio × objetivo; Vigente sobre ellas."""

    def preparar(self, ratio, territorio="sintetico"):
        tmp = Path(tempfile.mkdtemp())
        e = entrada(tmp)
        cfg = {"validation": {**CFG["validation"], "municipality_atomicity_limit_ratio": ratio}}
        comp = escribir_comp(tmp / "canonico" / "x_m06_composicion_distritos.csv", plan_corte(2), POB)
        return tmp, EntradaTerritorio(territorio, cfg, e.grafo_m03, contexto={"composicion_canonica": str(comp)}), comp

    def test_divide_solo_los_grandes(self):
        from ddd_motor2.generadores import piezas_finas
        tmp, e, comp = self.preparar(0.45)  # objetivo 403,5 → límite 181,6: A, B, D y E (200/201) son divisibles
        sal, info = piezas_finas(comp, e, tmp / "finas.csv")
        unidades = [r["ddd_unit_id"] for r in csv.DictReader(open(sal, encoding="utf-8"))]
        self.assertEqual(unidades, ["A~2200101000", "B~2200101001", "C", "D~2200101003", "E~2200101004"])
        self.assertEqual((info["municipios_divisibles"], info["secciones_sueltas"]), (4, 4))

    def test_congreso_y_sin_ratio_no_cambian(self):
        from ddd_motor2.generadores import piezas_finas
        tmp, e, comp = self.preparar(0.45, "congreso_x")
        self.assertEqual(piezas_finas(comp, e, tmp / "f.csv")[0], comp)
        tmp, e, comp = self.preparar(None)
        self.assertEqual(piezas_finas(comp, e, tmp / "f.csv")[0], comp)

    def test_congreso_no_parte_unidades_m04(self):
        from ddd_motor2.generadores import Vigente
        for territorio, ratio, esperado in (("congreso_x", 0.45, "VIGENTE_NO_REPRESENTABLE"), ("sintetico", 0.45, "OK"),
                                            ("sintetico", 1.15, "VIGENTE_NO_REPRESENTABLE")):
            tmp = Path(tempfile.mkdtemp())
            e = entrada(tmp)
            comp = tmp / "canonico" / "x_m06_composicion_distritos.csv"
            comp.parent.mkdir(parents=True)
            with open(comp, "w", newline="", encoding="utf-8") as fh:  # la unidad A tiene dos secciones (A0, A1)
                w = csv.writer(fh)
                w.writerow(["CUSEC_KEY", "district_id", "section_pop", "CPRO", "CUMUN", "ddd_unit_id", "ddd_closed_urban"])
                for i, u in enumerate(UNIDADES):
                    w.writerow([f"220010100{i}", "1" if i < 2 else "2", POB[u], "22", f"2200{i}", u, "0"])
            g = json.loads(Path(e.grafo_m03).read_text())
            g["nodes"].append("2200101009")
            g["edges"].append({"u": "2200101000", "v": "2200101009", "edge_type": "geometric", "shared_border_m": 1.0})
            Path(e.grafo_m03).write_text(json.dumps(g))
            with open(comp, "a", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(["2200101009", "1", 1, "22", "22000", "A", "0"])
            carpeta = tmp / "vig"
            carpeta.mkdir()
            (carpeta / f"{territorio}.csv").write_text("seccion,distrito,poblacion\n" + "".join(
                f"220010100{i},{'1' if i < 2 else '2'},0\n" for i in range(5)) + "2200101009,2,0\n", encoding="utf-8")
            cfg = {"validation": {**CFG["validation"], "municipality_atomicity_limit_ratio": ratio}}
            en = EntradaTerritorio(territorio, cfg, e.grafo_m03, contexto={"composicion_canonica": str(comp)})
            self.assertEqual(Vigente(carpeta).generar(en, None, tmp / "v").estado, esperado, (territorio, ratio))

    def test_vigente_representable_o_no(self):
        from ddd_motor2.generadores import Vigente
        tmp, e, comp = self.preparar(1.15)
        secc = [r["CUSEC_KEY"] for r in csv.DictReader(open(comp, encoding="utf-8"))]
        carpeta = tmp / "vig"
        carpeta.mkdir()
        (carpeta / "sintetico.csv").write_text("seccion,distrito,poblacion\n" + "".join(
            f"{s},{'1' if i < 3 else '2'},0\n" for i, s in enumerate(secc)), encoding="utf-8")
        sal = Vigente(carpeta).generar(e, None, tmp / "v")
        filas = list(csv.DictReader(open(sal.composicion, encoding="utf-8")))
        self.assertEqual([f["district_id"] for f in filas], ["1", "1", "1", "2", "2"])
        self.assertEqual([f["section_pop"] for f in filas], [str(POB[u]) for u in UNIDADES])  # población de la entrada
        (carpeta / "sintetico.csv").write_text("seccion,distrito,poblacion\n9999999999,1,0\n", encoding="utf-8")
        self.assertEqual(Vigente(carpeta).generar(e, None, tmp / "v2").estado, "VIGENTE_NO_REPRESENTABLE")


@unittest.skipUnless(importlib.util.find_spec("gerrychain"), "sin gerrychain")
class PonderadoDesdeVigente(unittest.TestCase):
    def test_mitad_desde_el_vigente(self):
        from ddd_motor2.generadores import Ponderado as Gen
        tmp = Path(tempfile.mkdtemp())
        r = competir(entrada(tmp), Fijo("canonico", {None: plan_corte(2)}), Gen(pasos=20), [11, 12], tmp / "out",
                     exhaustivo=False, funcion="D8", vigente=Fijo("vigente", {None: plan_corte(3)}))
        inicio = {c.semilla: c.extra.get("inicio") for c in r.candidatos if c.generador == "ponderado"}
        self.assertEqual(inicio, {11: "canonico", 12: "vigente"})
        self.assertLessEqual(r.ganador.clave()[:-1], next(c for c in r.candidatos if c.id == "vigente").clave()[:-1])


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
        self.assertEqual(c.fuera_tolerancia, c.natural[0])  # publicado = primer término = contrato
        self.assertNotEqual(c.extra["metricas_circunscripcion"]["fuera_tolerancia"], c.fuera_tolerancia)


if __name__ == "__main__":
    unittest.main()
