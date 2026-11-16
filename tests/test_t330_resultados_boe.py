#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de los CSV oficiales de resultados 2011, 2015, 2016 y 2019-04 desde el BOE (T-330)
VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: cada convocatoria tiene 52 circunscripciones y 350 escaños; los escaños por partido de cada circunscripción suman los
  suyos; la suma de cada partido coincide con la fila «Total estatal» del BOE (guardada en el JSON) y el sha256 del CSV, con el de
  su JSON; valores leídos a mano del texto del BOE (Albacete y totales); las circunscripciones de 2019-04 y 2019-11 tienen los mismos escaños y
  2015 y 2016 difieren solo en León y Valencia y el extractor gestiona la columna sin sigla y el orden por tabla.
"""
import csv
import hashlib
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import resultados_oficiales_boe as b  # noqa: E402

ELECCIONES = ("2011_11", "2015_12", "2016_06", "2019_04")


def leer(e):
    ruta = ROOT / f"configuracion/resultados_oficiales_congreso_{e}.csv"
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    return ruta, filas, json.loads(ruta.with_suffix(".json").read_text(encoding="utf-8"))


class Convocatorias(unittest.TestCase):
    def test_cuadran_con_el_total_oficial(self):
        for e in ELECCIONES:
            ruta, filas, meta = leer(e)
            self.assertEqual(meta["sha256_csv"], hashlib.sha256(ruta.read_bytes()).hexdigest(), e)
            self.assertEqual(len({r["codigo"] for r in filas}), 52, e)
            esc_prov, esc_part = {}, defaultdict(int)
            por_prov, tot = defaultdict(int), defaultdict(lambda: [0, 0])
            for r in filas:
                esc_prov[r["codigo"]] = int(r["escanos_circunscripcion"])
                por_prov[r["codigo"]] += int(r["escanos"])
                tot[r["partido"]][0] += int(r["votos"])
                tot[r["partido"]][1] += int(r["escanos"])
            self.assertEqual(sum(esc_prov.values()), 350, e)
            self.assertEqual(dict(por_prov), esc_prov, e)
            oficial = {s: [x["votos"], x["escanos"]] for s, x in meta["totales_oficiales"].items()}
            self.assertEqual(dict(tot), oficial, e)
            self.assertEqual(sum(x[1] for x in oficial.values()), 350, e)

    def test_valores_leidos_del_boe(self):
        esperado = {"2011_11": ("PP", 127995, 3, 10061311, 170), "2015_12": ("PP", 85241, 2, 6717462, 112),
                    "2016_06": ("PP", 89717, 2, 7372172, 126), "2019_04": ("PSOE", 75005, 2, 6550885, 111)}
        for e, (partido, votos, esc, tvotos, tesc) in esperado.items():
            _, filas, meta = leer(e)
            alba = next(r for r in filas if r["codigo"] == "02" and r["partido"] == partido)
            self.assertEqual((alba["provincia"], int(alba["votos"]), int(alba["escanos"])), ("Albacete", votos, esc), e)
            self.assertEqual(meta["totales_oficiales"][partido], {"votos": tvotos, "escanos": tesc}, e)

    def test_misma_distribucion_de_escanos(self):
        def esc(e):
            return {r["codigo"]: int(r["escanos_circunscripcion"]) for r in leer(e)[1]}
        self.assertEqual(esc("2019_04"), esc("2019_11"))
        a, c = esc("2015_12"), esc("2016_06")  # 2016 repartió un escaño de León (5→4) a Valencia (15→16), según su BOE
        self.assertEqual({k: (a[k], c[k]) for k in a if a[k] != c[k]}, {"24": (5, 4), "46": (15, 16)})

    def test_fuente_con_sha256_y_toponimos_en_espanol(self):
        ident = json.loads((ROOT / "configuracion/identificadores_boe_resultados_congreso.json").read_text("utf-8"))["elecciones"]
        for e in ELECCIONES:
            _, filas, meta = leer(e)
            clave = e.replace("_", "-")
            self.assertEqual(meta["boe"], ident[clave]["boe"])
            self.assertEqual(meta["sha256_xml"], ident[clave]["sha256_xml"])
            self.assertEqual(ident[clave]["csv_resultados"], f"configuracion/resultados_oficiales_congreso_{e}.csv")
            self.assertEqual({r["provincia"] for r in filas} & {"Girona", "Lleida", "Bizkaia", "Gipuzkoa", "Ourense"}, set())
        self.assertIn("sha256_pdf", ident["2016-06"])
        self.assertEqual(leer("2016_06")[2]["sha256_pdf"], ident["2016-06"]["sha256_pdf"])


class Extractor(unittest.TestCase):
    XML = """CUADRO II <table><tr><th></th><th>Total escaños</th><th>COALICIÓN «X» *</th><th>PARTIDO B</th></tr>
      <tr><th></th><th>B</th></tr><tr><th>Votos</th><th>Escaños</th><th>Votos</th><th>Escaños</th></tr>
      <tr><td>Albacete.</td><td>4</td><td>1.000</td><td>1</td><td>500</td><td></td></tr>
      <tr><td>Total estatal.</td><td>350</td><td>1.000</td><td>1</td><td>500</td><td>0</td></tr>
      <tr><td>(*) nota</td></tr></table> CUADRO III <"""

    def test_columna_sin_sigla_y_total(self):
        d = b.parsear_xml(self.XML)
        self.assertEqual(d["provincias"], [("Albacete", 4, [("COALICIÓN «X»", 1000, 1), ("B", 500, 0)])])
        self.assertEqual(d["totales"], {"COALICIÓN «X»": (1000, 1), "B": (500, 0)})
        self.assertEqual(d["bloque"]["B"], (0, 1))

    def test_comprobar_detecta_total_distinto(self):
        d = b.parsear_xml(self.XML)
        self.assertTrue(any("52" in e for e in b.comprobar(d)))


if __name__ == "__main__":
    unittest.main()
