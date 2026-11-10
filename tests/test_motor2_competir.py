#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-163 · resumen de aceptación de la competición para la batería (solo stdlib)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.competir import escribir_resumen, resumen  # noqa: E402


def fila(t, estado="VALIDO", frente="empata", s=10.0):
    return {"territorio": t, "estado": estado, "ganador": "canonico", "frente_al_canonico": frente,
            "canonico": "VALIDO", "candidatos_validos": 6, "candidatos": 6, "desvio_max": 0.1,
            "desvio_max_canonico": 0.1, "fuera_tolerancia": 0, "huella_resultado": "x", "tiempo_s": s}


class Resumen(unittest.TestCase):
    def test_aceptacion(self):
        self.assertTrue(resumen([fila("a"), fila("b", frente="mejora")])["aceptacion"])
        self.assertFalse(resumen([fila("a"), fila("b", estado="INVALIDO")])["aceptacion"])
        self.assertFalse(resumen([fila("a"), {"territorio": "b", "estado": "ERROR", "detalle": "x"}])["aceptacion"])
        self.assertFalse(resumen([])["aceptacion"])

    def test_ficheros(self):
        tmp = Path(tempfile.mkdtemp())
        tot = escribir_resumen([fila("a", s=3), fila("b", frente="mejora", s=5),
                                {"territorio": "c", "estado": "ERROR", "detalle": "x"}], tmp)
        self.assertEqual((tot["validos"], tot["mejora"], tot["empata"], tot["errores"]), (2, 1, 1, ["c"]))
        md = (tmp / "RESUMEN.md").read_text(encoding="utf-8")
        self.assertIn("Válidos: 2/3", md)
        self.assertIn("| c | — | ERROR |", md)


if __name__ == "__main__":
    unittest.main()
