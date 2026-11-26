#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: test de regresión T-502 — Deslinde en Sevilla (nac41, K=16) debe alcanzar el óptimo D8 demostrado
VERSIÓN: 1.0.0
FECHA: 2026-11-26
ANTERIOR: ninguna (fichero nuevo)
MOTIVO: el piloto del banco (T-466, #1025) demostró con CP-SAT (optimo_d8.py, 5 etapas OPTIMAL) que en Sevilla hay un
  plan válido con 6 demarcaciones partidas; el ganador de Deslinde parte 8. Causa (T-502): el candidato exacto no se
  aplica con K > 4 (exacto.K_MAX) y el exhaustivo no se intenta (cota de nodos > presupuesto), así que solo compiten
  las cadenas, que no bajan de 8.
DESACTIVADO hasta que haya arreglo: se salta salvo DDD_T502_ACTIVO=1, y además necesita las entradas de la batería
  de Sevilla (no están en git): DDD_BATERIA_OUT=<carpeta> con <carpeta>/entradas/nac41, generadas con
  `python herramientas/bateria_motor.py entradas --desde-fuente --seccionado shapefile --out <carpeta> nac41`.
Valor esperado: literal del estudio, no recalculado: óptimo D8 de Sevilla en el espacio del canónico =
  fuera 0, demarcaciones partidas 6 (docs/ESTUDIOS/T465_BANCO_PILOTO/resultados/exacto/nac41.json, etapas OPTIMAL).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVO = os.environ.get("DDD_T502_ACTIVO") == "1"
BATERIA = os.environ.get("DDD_BATERIA_OUT")
OPTIMO_FUERA = 0
OPTIMO_PARTIDAS = 6


@unittest.skipUnless(ACTIVO, "T-502: se activa cuando Deslinde alcance el óptimo en Sevilla (DDD_T502_ACTIVO=1)")
class SevillaAlcanzaElOptimo(unittest.TestCase):
    def test_ganador_parte_6_demarcaciones(self):
        if not BATERIA or not (Path(BATERIA) / "entradas" / "nac41").is_dir():
            self.skipTest("faltan las entradas de la batería de nac41 (DDD_BATERIA_OUT)")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "entradas").symlink_to(Path(BATERIA).resolve() / "entradas")
            env = {**os.environ, "PYTHONHASHSEED": "0"}
            r = subprocess.run([sys.executable, "-m", "ddd_motor2.competir", "--out", str(out), "nac41"],
                               cwd=ROOT, env=env, capture_output=True, text=True, timeout=1800)
            self.assertEqual(r.returncode, 0, r.stderr[-2000:])
            comp = json.loads((out / "competicion" / "nac41" / "COMPETICION.json").read_text(encoding="utf-8"))
        gan = next(c for c in comp["candidatos"] if c["id"] == comp["ganador"])
        clave = gan["clave_naturalidad"]
        self.assertEqual(clave[0], OPTIMO_FUERA)
        self.assertEqual(clave[2], OPTIMO_PARTIDAS, f"ganador {comp['ganador']} parte {clave[2]} demarcaciones")


if __name__ == "__main__":
    unittest.main()
