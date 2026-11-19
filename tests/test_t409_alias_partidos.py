#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: tabla de alias id de fuente → partido homologado (generales 2011-2023) y su uso en la doble vuelta (T-409)
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: la tabla versionada es la que se deriva hoy de las fuentes; cobertura del 100 % salvo el resto declarado; cada partido de la tabla
  existe en la tabla de bloques; valores esperados de ficheros de origen (reglas_generales.json `interior`, homologación), no del código.
"""
import contextlib
import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import alias_partidos_generales as ap  # noqa: E402
import doble_vuelta as dv  # noqa: E402

ALIAS = ROOT / "configuracion/alias_partidos_generales.csv"
BLOQUES = ROOT / "configuracion/bloques_partidos_2026-11-17.csv"


def tabla():
    return {(f["eleccion"], f["id_fuente"]): f for f in csv.DictReader(open(ALIAS, encoding="utf-8", newline=""))}


class TablaVersionada(unittest.TestCase):
    def test_es_lo_que_se_deriva_hoy(self):
        for p, s in ap.textos().items():
            self.assertEqual((ROOT / p).read_text(encoding="utf-8"), s, p)

    def test_un_id_un_partido(self):
        filas = list(csv.DictReader(open(ALIAS, encoding="utf-8", newline="")))
        self.assertEqual(len(filas), len({(f["eleccion"], f["id_fuente"]) for f in filas}))

    def test_valores_de_las_fuentes(self):
        t = tabla()
        # reglas_generales.json → interior (2019-11 y 2023) y homologación de siglas (sigla_fuente → partido_homologado)
        self.assertEqual(t[("201911", "PSC")]["partido_homologado"], "PSOE")
        self.assertEqual(t[("202307", "JUNTS")]["partido_homologado"], "CiU–Junts")
        self.assertEqual(t[("202307", "SUMAR")]["partido_homologado"], "Podemos–Sumar")
        self.assertEqual(t[("201111", "PP-EU")]["partido_homologado"], "PP")  # PP-COALICIONES de reglas_generales.json

    def test_todo_partido_homologado_esta_en_la_tabla_de_bloques(self):
        bl = {(f["eleccion"].replace("-", ""), f["siglas"]) for f in csv.DictReader(open(BLOQUES, encoding="utf-8", newline=""))}
        falta = sorted({(e, f["partido_homologado"]) for (e, _), f in tabla().items() if (e, f["partido_homologado"]) not in bl})
        self.assertEqual(falta, [])

    def test_cobertura_total_salvo_el_resto_declarado(self):
        r = json.loads((ROOT / "configuracion/alias_partidos_generales.json").read_text(encoding="utf-8"))
        self.assertEqual([(c["eleccion"], c["id_fuente"], c["candidatos"]) for c in r["conflictos"]],
                         [("201111", "LA IZQUIERDA PLURAL", ["CHA-IU", "IU"])])
        pend = list(csv.DictReader(open(ROOT / "configuracion/alias_partidos_generales_pendientes.csv", encoding="utf-8", newline="")))
        self.assertEqual([(p["eleccion"], p["id_fuente"]) for p in pend], [("201111", "LA IZQUIERDA PLURAL")])
        for k, c in r["cobertura_votos"].items():
            if k != "201111/BOE":
                self.assertEqual(c["sin_alias"], 0, k)

    def test_el_resto_declarado_es_del_mismo_bloque(self):
        bl = {(f["eleccion"], f["siglas"]): f["bloque_propuesto"] for f in csv.DictReader(open(BLOQUES, encoding="utf-8", newline=""))}
        self.assertEqual({bl[("2011-11", "IU")], bl[("2011-11", "CHA-IU")]}, {"Izquierdas"})

    def test_conflicto_sintetico_va_a_conflictos_no_a_la_tabla(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for rel in (ap.HOMOLOGACION, ap.REGLAS, ap.ALIAS_BOE):
                (d / rel).parent.mkdir(parents=True, exist_ok=True)
            (d / ap.HOMOLOGACION).write_text(
                "eleccion,provincia,sigla_fuente,votos_fuente,familia_fuente,partido_homologado,nivel_certeza,regla,interior,ruta_fuente,sha256_fuente\n"
                "201111,01,AAA,1,a,PARTIDO1,ALTA,x,x,x,x\n201111,02,AAA,1,a,PARTIDO2,ALTA,x,x,x,x\n201111,01,BBB,1,a,PARTIDO3,ALTA,x,x,x,x\n",
                encoding="utf-8")
            (d / ap.REGLAS).write_text('{"interior": {}}', encoding="utf-8")
            (d / ap.ALIAS_BOE).write_text("eleccion,provincia,sigla_boe,siglas_espejo,regla,prueba\n", encoding="utf-8")
            r = ap.derivar(d)
        self.assertEqual([c["id_fuente"] for c in r["conflictos"]], ["AAA"])
        self.assertIn(("201111", "BBB"), {(f["eleccion"], f["id_fuente"]) for f in r["filas"]})
        self.assertNotIn(("201111", "AAA"), {(f["eleccion"], f["id_fuente"]) for f in r["filas"]})


class AliasEnDobleVuelta(unittest.TestCase):
    def test_aplicar_alias_suma_ids_del_mismo_partido(self):
        v = dv.aplicar_alias({"1": {"PP-EU": 30, "PP": 50, "X": 5}}, {"PP-EU": "PP", "PP": "PP"})
        self.assertEqual(v, {"1": {"PP": 80, "X": 5}})

    def test_eleccion_alias(self):
        self.assertEqual(dv.eleccion_alias("2023-07"), "202307")

    def test_generar_con_alias_casa_y_lo_registra(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n1,PP-EU,60,\n1,SUMAR,40,\n", encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n2023-07,PP,PP,Patriotas,x\n"
                                     "2023-07,Podemos–Sumar,x,Izquierdas,x\n", encoding="utf-8")
            (d / "a.csv").write_text("eleccion,id_fuente,partido_homologado,origen,fuente\n202307,PP-EU,PP,HOMOLOGACION,x\n"
                                     "202307,SUMAR,Podemos–Sumar,HOMOLOGACION,x\n", encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                filas = dv.generar(d / "v.csv", d / "b.csv", "2023-07", d / "s.csv", d / "m.json", alias_csv=d / "a.csv")
            self.assertEqual(err.getvalue(), "")  # todo casa
            m = json.loads((d / "m.json").read_text())
            self.assertEqual(m["sin_casar"]["n_partidos"], 0)
            self.assertEqual(m["alias"]["sha256"], dv.sha256(d / "a.csv"))
            base = next(f for f in filas if f["escenario"] == "dv_base")
            self.assertEqual((base["candidatura_ganadora"], base["bloque_ganador"]), ("PP", "Patriotas"))  # 60 % en primera vuelta

    def test_sin_alias_los_ids_no_casan(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n1,PP-EU,60,\n", encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n2023-07,PP,PP,Patriotas,x\n", encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                dv.generar(d / "v.csv", d / "b.csv", "2023-07", d / "s.csv")
            self.assertIn("DOBLE_VUELTA_SIN_CASAR", err.getvalue())


if __name__ == "__main__":
    unittest.main()
