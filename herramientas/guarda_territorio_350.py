#!/usr/bin/env python3
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: Guarda del mapa de 350 en la 00 (T-268)
# FECHA: 2026-11-12
# ESTADO: vigente — T-268
# QUÉ HACE: `python -m herramientas.guarda_territorio_350 <territorio>` sale con 0 si el territorio puede entrar en la
#   00 y con 3 (y un ::error:: accionable) si es un gemelo «Congreso 350 <provincia>» / `congreso350_*`.
# CAMBIOS: fichero nuevo.
# MOTIVO: D-76, el mapa de 350 queda fuera del motor y del registro; con la semilla D-90 (codigo_semilla de la tabla
#   maestra) un P30 sobre `congreso350_*` fallaría tarde con ErrorContrato. Se rechaza antes de cualquier fase cara.
# ANTERIOR: ninguna (fichero nuevo)
"""Rechaza en la 00 los territorios del mapa de 350 (D-76)."""
from __future__ import annotations

import argparse
import sys
import unicodedata

PREFIJO_ID = "congreso350_"
PREFIJOS_ETIQUETA = ("congreso 350 ", "nacional 350 ")
CODIGO_RECHAZO = 3


def _normalizar(valor: str) -> str:
    return " ".join(unicodedata.normalize("NFC", valor or "").split()).casefold()


def es_territorio_350(territorio: str) -> bool:
    """True para `congreso350_*` y las etiquetas «Congreso 350 …» / «Nacional 350 …» del selector."""
    t = _normalizar(territorio)
    return t.startswith(PREFIJO_ID) or t.startswith(PREFIJOS_ETIQUETA)


def mensaje_rechazo(territorio: str) -> str:
    provincia = territorio.strip()
    for p in ("Congreso 350 ", "Nacional 350 "):
        if provincia.casefold().startswith(p.casefold()):
            provincia = provincia[len(p):]
            break
    else:
        provincia = "<provincia>"
    return (
        f"TERRITORIO_350_FUERA_DEL_MOTOR: «{territorio.strip()}» es del mapa de 350 (congreso350_*), que por D-76 está "
        "fuera del motor y del registro; la 00 no lo ejecuta (con la semilla D-90 fallaría tarde: no está en la tabla "
        f"maestra). Usa «Congreso {provincia}» (escaños reales de la provincia) o un territorio autonómico."
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("territorio")
    a = ap.parse_args(argv)
    if es_territorio_350(a.territorio):
        print(f"::error::{mensaje_rechazo(a.territorio)}")
        return CODIGO_RECHAZO
    print(f"Territorio admitido en la 00: {a.territorio.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
