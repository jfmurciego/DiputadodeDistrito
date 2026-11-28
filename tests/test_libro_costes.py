"""Pruebas de herramientas/libro_costes.py (T-512, D-217).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: candidato
CAMBIOS 1.0.0: fichero nuevo.
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: criterio de aceptación de T-512: el resumen reproduce 862,13 USD ± 1 % con las 97 partidas históricas y el
  guion sale ≠0 si una fila nueva no tiene sesión o rol (las históricas están exentas).
Los valores esperados son literales del informe T-509 (C_agentes.md, apartado 3), no recalculados con el código.
"""
from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from herramientas import libro_costes as lc

HIST = {"fecha": "2026-11-20", "sesion": None, "rol": "implementador", "tarea": "T-1", "cost_usd": 1.5,
        "origen": "historico", "fuente": "x:1"}
NUEVA = {"fecha": "2026-11-29", "sesion": "session_01ABC", "rol": "operador", "tarea": "T-2", "cost_usd": 2.0,
         "origen": "nuevo"}


def correr(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = lc.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class LibroReal(unittest.TestCase):
    def test_97_partidas_y_862_13_usd(self):
        filas = lc.leer()
        self.assertEqual(len(filas), 97)
        total = sum(f["cost_usd"] for f in filas)
        self.assertAlmostEqual(total, 862.13, delta=862.13 * 0.01)
        self.assertTrue(all(f["origen"] == "historico" and f["sesion"] is None for f in filas))

    def test_resumen_por_rol_del_informe(self):
        rc, out, _ = correr("--resumen", "--desde", "2026-11-14")
        self.assertEqual(rc, 0)
        self.assertIn("97 partidas", out)
        self.assertIn("total 862.13 USD", out)
        for esperado in ("implementador     602.00", "coordinador       183.39", "auditoria          76.74"):
            self.assertIn(esperado, out)
        self.assertIn("2026-S48", out)

    def test_comprobar_pasa_con_el_libro_versionado(self):
        self.assertEqual(correr("--comprobar")[0], 0)


class Validacion(unittest.TestCase):
    def libro(self, *filas: dict) -> str:
        d = Path(tempfile.mkdtemp())
        ruta = d / "libro.jsonl"
        ruta.write_text("".join(json.dumps(f) + "\n" for f in filas), encoding="utf-8")
        return str(ruta)

    def test_historica_sin_sesion_esta_exenta(self):
        self.assertEqual(correr("--comprobar", "--libro", self.libro(HIST))[0], 0)

    def test_fila_nueva_valida_pasa(self):
        self.assertEqual(correr("--comprobar", "--libro", self.libro(HIST, NUEVA))[0], 0)

    def test_fila_nueva_sin_sesion_falla(self):
        rc, _, err = correr("--comprobar", "--libro", self.libro(HIST, dict(NUEVA, sesion=None)))
        self.assertEqual(rc, 1)
        self.assertIn("sin id de sesión", err)

    def test_fila_nueva_sin_rol_falla(self):
        sin_rol = {k: v for k, v in NUEVA.items() if k != "rol"}
        rc, _, err = correr("--comprobar", "--libro", self.libro(sin_rol))
        self.assertEqual(rc, 1)
        self.assertIn("rol ausente", err)

    def test_resumen_tambien_falla_con_fila_invalida(self):
        self.assertEqual(correr("--resumen", "--libro", self.libro(dict(NUEVA, sesion="")))[0], 1)


class Anotar(unittest.TestCase):
    def test_anotar_valida_añade_una_fila_con_coma_decimal(self):
        ruta = Path(tempfile.mkdtemp()) / "libro.jsonl"
        rc, _, _ = correr("--anotar", "--libro", str(ruta), "--sesion", "session_01XYZ", "--rol", "planificador",
                          "--tarea", "T-509", "--coste", "216,33", "--fecha", "2026-11-28")
        self.assertEqual(rc, 0)
        filas = lc.leer(ruta)
        self.assertEqual(len(filas), 1)
        self.assertEqual((filas[0]["rol"], filas[0]["cost_usd"], filas[0]["origen"]), ("planificador", 216.33, "nuevo"))

    def test_anotar_sin_sesion_se_rechaza_y_no_escribe(self):
        ruta = Path(tempfile.mkdtemp()) / "libro.jsonl"
        rc, _, err = correr("--anotar", "--libro", str(ruta), "--rol", "operador", "--tarea", "T-1", "--coste", "1")
        self.assertEqual(rc, 1)
        self.assertIn("sin id de sesión", err)
        self.assertFalse(ruta.exists())


if __name__ == "__main__":
    unittest.main()
