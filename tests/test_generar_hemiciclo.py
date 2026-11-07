#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del hemiciclo (T-42)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: dos provincias sintéticas (Soria y Teruel): D'Hondt con barrera, agrupación de partidos, un escaño por distrito,
  (b) «sin fuente» y provincias que faltan calculadas de los datos. Con DDD_MESA_ZIP (ZIP por mesa) contrasta las 52 circunscripciones,
  escaño a escaño, con el oficial del BOE (configuracion/resultados_oficiales_congreso_2023.csv).
"""
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import generar_hemiciclo as g  # noqa: E402

# Soria: 2 escaños; A 500, B 300, C 20 (bajo el 3 %) → A1 B1. Teruel: 3 escaños; A 500, B 400, C 100 → A2 B1.
OFICIAL = {"42": {"votos": {"A#1": 500, "PSC#2": 300, "C#3": 20}, "validos": 820},
           "44": {"votos": {"A#1": 500, "PSOE#2": 400, "C#3": 100}, "validos": 1000}}
ESC = {"42": 2, "44": 3}


class Hemiciclo(unittest.TestCase):
    def setUp(self):
        self.reparto = g.reparto_2023(OFICIAL, ESC)
        self.gan = {"42": ["A", "PSC"], "44": ["PSOE", "PSOE", "A"]}
        self.k = {"42": 2, "44": 3, "29": 5}

    def test_dos_provincias(self):
        self.assertEqual(self.reparto, {"42": {"A": 1, "PSOE": 1}, "44": {"A": 2, "PSOE": 1}})
        r = g.generar(self.gan, self.reparto, self.k)
        self.assertEqual(r["errores"], [])
        self.assertEqual(r["provincias_incluidas"], 2)
        self.assertEqual(r["totales"]["a"], {"A": 3, "PSOE": 2})
        self.assertEqual(r["totales"]["c"], {"PSOE": 3, "A": 2})  # PSC se agrupa en PSOE
        self.assertEqual(r["escanos"]["c"], 5)  # uno por distrito (2 + 3)
        self.assertEqual(r["fuentes"]["b"], "sin fuente")
        self.assertIsNone(r["totales"]["b"])
        self.assertEqual(r["ambito"], "Nacional")

    def test_faltan_se_calculan(self):
        r = g.generar(self.gan, self.reparto, self.k)
        nombres = {f["provincia"] for f in r["faltan"]}
        self.assertIn("Málaga", nombres)
        self.assertNotIn("Soria", nombres)
        self.assertEqual(len(r["faltan"]), 50)
        r = g.generar({**self.gan, "42": ["A"]}, self.reparto, self.k)  # M08 con distritos de menos
        self.assertIn("Soria", {f["provincia"] for f in r["faltan"]})

    def test_salida_csv_json(self):
        import tempfile
        r = g.generar(self.gan, self.reparto, self.k)
        d = Path(tempfile.mkdtemp())
        g.escribir(r, d)
        self.assertIn("Nacional,Nacional,A,3,sin fuente,2", (d / "hemiciclo.csv").read_text(encoding="utf-8"))
        self.assertTrue((d / "hemiciclo.json").exists())

    def test_contraste_con_oficial(self):
        of = {"42": {"A": 1, "PSOE": 1}, "44": {"A": 2, "PSOE": 1}}
        sin_52 = [e for e in g.contrastar(self.reparto, of, ESC)[0] if "falta" not in e]
        self.assertEqual(sin_52, [])
        # una diferencia cualquiera falla; PSOE→PP en una sola provincia es nota (CERA final)
        malo = {"42": {"A": 2}, "44": {"A": 2, "PSOE": 1}}
        self.assertTrue([e for e in g.contrastar(self.reparto, malo, ESC)[0] if "diferencias" in e])
        e, n, difs = g.contrastar({"42": {"A": 1, "PSOE": 1}, "44": {"A": 2, "PSOE": 1}},
                                  {"42": {"A": 1, "PSOE": 1}, "44": {"A": 2, "PSOE": 1}}, ESC)
        self.assertEqual((n, difs), ([], []))
        # PSOE→PP en una sola provincia: nota (CERA final), no error
        e, n, _ = g.contrastar({"42": {"PP": 1, "PSOE": 1}, "44": {"A": 2, "PSOE": 1}},
                               {"42": {"PP": 2}, "44": {"A": 2, "PSOE": 1}}, ESC)
        self.assertEqual([x for x in e if "diferencias" in x], [])
        self.assertEqual(len(n), 1)

    def test_barrera_del_3_por_ciento(self):
        self.assertEqual(g.dhondt({"A": 500, "B": 300, "C": 20}, 2, 820), {"A": 1, "B": 1})
        self.assertEqual(g.dhondt({"A": 500, "B": 300, "C": 100}, 3, 900), {"A": 2, "B": 1})


@unittest.skipUnless(os.environ.get("DDD_MESA_ZIP"), "DDD_MESA_ZIP no definido")
class OficialReal(unittest.TestCase):
    def test_52_circunscripciones_contra_el_boe(self):
        esc, of = g.leer_oficial()
        rep = g.reparto_2023(g.leer_mesa_zip(Path(os.environ["DDD_MESA_ZIP"])), esc)
        self.assertEqual(sum(esc.values()), 350)
        self.assertEqual(len(rep), 52)
        self.assertEqual(rep["42"], {"PP": 1, "PSOE": 1})
        self.assertEqual(rep["44"], {"PP": 2, "PSOE": 1})
        self.assertEqual(rep, of)  # escaño a escaño en las 52


if __name__ == "__main__":
    unittest.main()
