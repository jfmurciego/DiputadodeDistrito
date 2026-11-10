#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga de la equivalencia de secciones del ZIP de Interior por fecha de elección (T-200, generaliza T-101).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: ``cargar(fecha)`` devuelve seccion_zip → [{seccion_m06, tipo, peso_area, frac_m06}] desde
  configuracion/equivalencia_secciones_congreso_<AAAAMMDD>.csv (con su JSON hermano y sha256). Para 2023-07-23 usa la
  tabla vigente. Para cualquier otra fecha exige el par CSV+JSON; mientras no exista falla con
  EQUIVALENCIA_NO_ACREDITADA y la causa. Generales 2026-11-29: el seccionado electoral 2026 y la correspondencia
  2025→2026 no están acreditados (F10-20261012-PAIR-2025, BLOCKED_PENDING_OFFICIAL_EVIDENCE); el censo electoral llega
  con el ZIP de Interior (tras el 29-11-2026). La tabla se construye con equivalencia_congreso_2023.py (que hoy fija 2023).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import resultados_partidos as rp  # noqa: E402

CAUSAS = {"2026-11-29": "seccionado electoral 2026 y correspondencia 2025→2026 sin acreditar "
                        "(BLOCKED_PENDING_OFFICIAL_EVIDENCE); el ZIP de Interior sale tras el 29-11-2026"}


def ruta(fecha: str, root: Path = ROOT) -> Path:
    sufijo = "2023" if fecha == "2023-07-23" else fecha.replace("-", "")
    return root / f"configuracion/equivalencia_secciones_congreso_{sufijo}.csv"


def cargar(fecha: str, root: Path = ROOT) -> dict[str, list[dict]]:
    r = ruta(fecha, root)
    if not (r.is_file() and r.with_suffix(".json").is_file()):
        causa = CAUSAS.get(fecha, "sin tabla de equivalencia para esa fecha")
        raise FileNotFoundError(f"EQUIVALENCIA_NO_ACREDITADA {fecha}: {causa}")
    return rp.leer_equivalencia(r)
