#!/usr/bin/env python3
"""Reparto de diputados del Congreso (art. 162 LOREG) a partir de población provincial.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: 2 diputados por provincia, 1 Ceuta y 1 Melilla, y el resto (248) por cociente y mayores restos.
  Es un oráculo de comprobación del dato electoral (RD de convocatoria); NO es el K de DDD (N06).
  Solo biblioteca estándar. La población debe venir de un fichero con fuente y sha256, nunca de memoria.
"""
from __future__ import annotations

CEUTA_MELILLA = ("51", "52")
TOTAL = 350


def repartir(poblacion: dict[str, int]) -> dict[str, int]:
    """poblacion: código INE de provincia -> habitantes (50 provincias; Ceuta/Melilla se ignoran)."""
    prov = [k for k in poblacion if k not in CEUTA_MELILLA]
    libres = TOTAL - len(CEUTA_MELILLA) - 2 * len(prov)  # 248
    cuota = sum(poblacion[k] for k in prov) / libres
    esc = {k: 2 + int(poblacion[k] // cuota) for k in prov}
    pendientes = TOTAL - len(CEUTA_MELILLA) - sum(esc.values())
    for k in sorted(prov, key=lambda k: (-(poblacion[k] % cuota), k))[:pendientes]:
        esc[k] += 1
    for k in CEUTA_MELILLA:
        esc[k] = 1
    return esc
