#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la homologación de siglas autonómicas (T-121)
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: valores a mano (D-20) sobre las reglas; la tabla real se revalida sin red.
"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import homologacion_siglas_autonomicas as ha  # noqa: E402


class Reglas(unittest.TestCase):
    def setUp(self):
        self.r = ha.reglas()

    def test_familia_sin_regla_es_baja_y_conserva_la_sigla(self):
        self.assertEqual(ha.resolver(self.r, "aut12", "202402", "DO", "a43"), ("DO", "BAJA", "SIN_REGLA_FAMILIA:a43"))

    def test_sigla_propia_de_autonomicas(self):
        self.assertEqual(ha.resolver(self.r, "aut07", "202603", "AHORA DECIDE/AS", "a51")[:2], ("AHORA DECIDE", "MEDIA"))

    def test_coalicion_con_pp_de_cabeza_vale_en_autonomicas(self):
        self.assertEqual(ha.resolver(self.r, "aut02", "201505", "PP-PAR", "a5")[0], "PP")

    def test_upn_en_navarra_no_cae_en_la_familia_del_pp(self):
        # D-20 C (generales): UPN-PP y NA+ → «UPN y coaliciones»; en autonómicas la regla debe aplicarse por comunidad
        self.assertEqual(ha.resolver(self.r, "aut15", "201105", "UPN-PP", "a5")[0], "UPN y coaliciones")
        self.assertEqual(ha.resolver(self.r, "aut02", "201105", "UPN-PP", "a5")[0], "PP")


class TablaReal(unittest.TestCase):
    def test_tabla_al_dia_con_las_reglas(self):
        self.assertEqual(ha.comprobar(), [])

    def test_ganadores_de_galicia_2024_homologados(self):
        with (ROOT / "datos/resultados/historico/autonomicas/galicia/rotacion.csv").open(encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        self.assertTrue(all(r["202402"] in {"PP", "BNG", "PSOE"} for r in filas))


if __name__ == "__main__":
    unittest.main()
