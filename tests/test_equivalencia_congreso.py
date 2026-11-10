# -*- coding: utf-8 -*-
"""PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ANTERIOR: ninguna (fichero nuevo)
Tests de T-200: carga de la equivalencia de secciones por fecha de elección."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import equivalencia_congreso as ec  # noqa: E402


class Equivalencia(unittest.TestCase):
    def test_2023_carga_la_tabla_vigente(self):
        t = ec.cargar("2023-07-23")
        # literal de la primera fila de configuracion/equivalencia_secciones_congreso_2023.csv
        self.assertIn({"seccion_m06": "0200302024", "tipo": "reparto", "peso_area": 1.0, "frac_m06": 0.840289},
                      t["0200302025"])

    def test_2026_bloqueada_con_causa(self):
        with self.assertRaisesRegex(FileNotFoundError, "EQUIVALENCIA_NO_ACREDITADA 2026-11-29.*BLOCKED_PENDING"):
            ec.cargar("2026-11-29")

    def test_fecha_desconocida(self):
        with self.assertRaisesRegex(FileNotFoundError, "EQUIVALENCIA_NO_ACREDITADA"):
            ec.cargar("2027-01-01")


if __name__ == "__main__":
    unittest.main()
