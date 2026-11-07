#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del hemiciclo (T-42)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: dos provincias sintéticas (Soria y Teruel): D'Hondt contra el oficial, un escaño por distrito, (b) «sin fuente»
  y lista de provincias que faltan calculada de los datos.
"""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import generar_hemiciclo as g  # noqa: E402


def _csv(ruta, cab, filas):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(cab)
        w.writerows(filas)


class Hemiciclo(unittest.TestCase):
    def setUp(self):
        self.t = Path(tempfile.mkdtemp())
        # Soria: 2 escaños oficiales; A 500, B 300, C 20 (bajo el 3 %) → A1 B1
        # Teruel: 3 escaños; A 500, B 400, C 100 → D'Hondt: A1 B1 + (250 vs 200 vs 100) A → A2 B1
        _csv(self.t / "of.csv", ["provincia", "partido", "votos", "escanos"], [
            ["42", "A", 500, 1], ["42", "B", 300, 1], ["42", "C", 20, 0],
            ["congreso_teruel", "A", 500, 2], ["congreso_teruel", "B", 400, 1], ["congreso_teruel", "C", 100, 0]])
        _csv(self.t / "k.csv", ["province_code", "k_province"], [["42", 2], ["44", 3], ["29", 5]])
        h = ["district_id", "winner_party"]
        _csv(self.t / "m08/congreso_soria/x/distritos_resultados.csv", h, [[0, "A"], [1, "B"]])
        _csv(self.t / "m08/congreso_teruel/x/distritos_resultados.csv", h, [[0, "B"], [1, "B"], [2, "A"]])

    def test_dos_provincias(self):
        r = g.generar(self.t / "m08", self.t / "of.csv", self.t / "k.csv")
        self.assertEqual(r["errores"], [])
        self.assertEqual(r["provincias_incluidas"], 2)
        self.assertEqual(r["totales"]["a"], {"A": 3, "B": 2})
        self.assertEqual(r["totales"]["c"], {"B": 3, "A": 2})
        self.assertEqual(r["escanos"]["c"], 5)  # uno por distrito (2 + 3)
        self.assertEqual(r["fuentes"]["b"], "sin fuente")
        self.assertIsNone(r["totales"]["b"])
        self.assertEqual(r["ambito"], "Nacional")

    def test_faltan_se_calculan(self):
        r = g.generar(self.t / "m08", self.t / "of.csv", self.t / "k.csv")
        nombres = {f["provincia"] for f in r["faltan"]}
        self.assertIn("Málaga", nombres)
        self.assertNotIn("Soria", nombres)
        self.assertEqual(len(r["faltan"]), 50)
        # un M08 con distritos de menos también falta
        (self.t / "m08/congreso_soria/x/distritos_resultados.csv").write_text("district_id,winner_party\n0,A\n")
        r = g.generar(self.t / "m08", self.t / "of.csv", self.t / "k.csv")
        self.assertIn("Soria", {f["provincia"] for f in r["faltan"]})

    def test_oficial_distinto_da_error(self):
        _csv(self.t / "of.csv", ["provincia", "partido", "votos", "escanos"], [
            ["42", "A", 600, 1], ["42", "B", 100, 1]])
        r = g.generar(self.t / "m08", self.t / "of.csv", self.t / "k.csv")
        self.assertTrue(r["errores"])

    def test_salida_csv_json(self):
        r = g.generar(self.t / "m08", self.t / "of.csv", self.t / "k.csv")
        g.escribir(r, self.t / "out")
        txt = (self.t / "out/hemiciclo.csv").read_text(encoding="utf-8")
        self.assertIn("Nacional,Nacional,A,3,sin fuente,2", txt)
        self.assertTrue((self.t / "out/hemiciclo.json").exists())


if __name__ == "__main__":
    unittest.main()
