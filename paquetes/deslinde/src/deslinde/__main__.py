#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — línea de órdenes
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · CLI
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88).
MOTIVO: ejecutar la competición de Deslinde sin el repo. Sin PYTHONHASHSEED=0 efectivo (también con -I/-E, que lo ignoran) se niega (sale con 6).
USO: PYTHONHASHSEED=0 python -m deslinde competir --contrato c.yaml --grafo g.json --composicion m06.csv
       --territorio NAC22 --partidos pj.csv --comarcas ca.csv --areas areas.csv --out salida/
       [--vigente vigente.csv] [--atributos m06_secciones.geojson.zip] [--cadenas 10] [--funcion D8]
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import argparse
import json
import sys


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="deslinde")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("competir")
    for nombre in ("--contrato", "--grafo", "--composicion", "--territorio", "--out"):
        c.add_argument(nombre, required=True)
    for nombre in ("--partidos", "--comarcas", "--areas", "--vigente", "--atributos"):
        c.add_argument(nombre)
    c.add_argument("--cadenas", type=int, default=10)
    c.add_argument("--funcion", default="D8")
    a = ap.parse_args(argv)
    from . import api  # noqa: PLC0415
    if not api.hashseed_fijo():
        print("deslinde: PYTHONHASHSEED=0 es obligatorio y Python no debe ignorarlo (sin -I ni -E)", file=sys.stderr)
        return 6
    tablas = (a.partidos, a.comarcas, a.areas) if a.partidos and a.comarcas and a.areas else None
    r = api.competir(a.contrato, a.grafo, a.composicion, a.out, territorio=a.territorio, tablas=tablas,
                     vigente=a.vigente, atributos=a.atributos, n_cadenas=a.cadenas, funcion=a.funcion)
    print(json.dumps({k: r[k] for k in ("estado", "ganador", "valido", "huella_resultado")}, ensure_ascii=False))
    return 0 if r["valido"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
