#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cobertura de la tabla de bloques sobre los votos por partido de P31 (T-409, D-171).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.2.0 · FECHA: 2026-11-25 · ESTADO: candidato
ANTERIOR: legacy/herramientas/doble_vuelta_cobertura_v1.1.0_20261119.py
CAMBIOS: 1.2.0 (T-460): un bloque fuera de BLOQUES (p. ej. una tabla vieja con «Patriotas») falla con ValueError, como en doble_vuelta.py, y no se cuenta en silencio como bloque.
  1.1.0 (T-409): `--alias` (configuracion/alias_partidos_generales.csv): la cobertura se mide tras pasar cada id a su partido homologado, como
  hace `doble_vuelta.py --alias`; el JSON lleva el sha256 del alias. Sin `--alias` nada cambia. 1.0.0: fichero nuevo.
MOTIVO: los ids de partido de `<run>_m07_resultados_partido.csv` son los del diccionario de cada contrato («PP-EU», «SUMAR», «C's»), no
  las siglas homologadas de `configuracion/bloques_partidos_*.csv`; sin casar no es lo mismo que sin bloque, y un partido sin casar
  se abstiene en silencio en la doble vuelta. Esta herramienta lo mide y lo deja en un JSON con sha256; no corrige nada.
QUÉ HACE: lee el CSV por partido y distrito y la tabla de bloques de una elección y calcula, sobre los votos: casados (el partido
  está en la tabla, con o sin bloque), SIN CASAR (no está en la tabla) y sin bloque (está en la tabla con el bloque vacío), y la lista
  de partidos sin casar. Un ::warning DOBLE_VUELTA_COBERTURA si hay votos sin casar. Sale 0 aunque haya votos sin casar (no es fatal).
USO: python herramientas/doble_vuelta_cobertura.py --votos P31.csv --bloques configuracion/bloques_partidos_2026-11-17.csv
  --eleccion congreso_2023-07-23 --salida cobertura.json   (--eleccion: AAAA-MM o un texto con la fecha, p. ej. el election_id)
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

from doble_vuelta import BLOQUES, aplicar_alias, cargar_alias, sha256

MAX_LISTA = 25


def normalizar_eleccion(texto: str) -> str:
    """AAAA-MM de un texto con una fecha (AAAA-MM o AAAA-MM-DD): '2023-07', 'congreso_2023-07-23'."""
    m = re.search(r"(?<!\d)(\d{4})-(\d{2})(?!\d)", str(texto))
    if not m or not 1 <= int(m.group(2)) <= 12:
        raise ValueError(f"No se reconoce una elección AAAA-MM en «{texto}»")
    return f"{m.group(1)}-{m.group(2)}"


def cobertura(votos_csv, bloques_csv, eleccion: str, alias_csv=None) -> dict:
    eleccion = normalizar_eleccion(eleccion)
    tabla: dict[str, str] = {}
    with open(bloques_csv, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["eleccion"] == eleccion:
                b = fila["bloque_propuesto"].strip()
                if b and b not in BLOQUES:
                    raise ValueError(f"Bloque desconocido «{b}» para {fila['siglas']}")
                tabla[fila["siglas"]] = b
    if not tabla:
        raise ValueError(f"Sin filas de la elección {eleccion} en {bloques_csv}")
    por_partido: dict[str, int] = defaultdict(int)
    with open(votos_csv, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            por_partido[fila["party"]] += int(fila["votes"])
    if alias_csv:
        por_partido = aplicar_alias({"_": dict(por_partido)}, cargar_alias(alias_csv, eleccion))["_"]
    total = sum(por_partido.values())
    sin_casar = {p: v for p, v in por_partido.items() if p not in tabla and v > 0}
    sin_bloque = sum(v for p, v in por_partido.items() if p in tabla and not tabla[p])
    n = sum(sin_casar.values())
    pct = lambda x: round(100 * x / total, 4) if total else 0.0  # noqa: E731
    return {
        "schema": "ddd.doble-vuelta-cobertura/1.0", "eleccion": eleccion,
        "entradas": {"votos": {"ruta": str(votos_csv), "sha256": sha256(votos_csv)},
                     "bloques": {"ruta": str(bloques_csv), "sha256": sha256(bloques_csv)},
                     **({"alias": {"ruta": str(alias_csv), "sha256": sha256(alias_csv)}} if alias_csv else {})},
        "votos_total": total, "votos_sin_casar": n, "pct_sin_casar": pct(n),
        "votos_sin_bloque": sin_bloque, "pct_sin_bloque": pct(sin_bloque),
        "partidos_sin_casar": [{"partido": p, "votos": v} for p, v in sorted(sin_casar.items(), key=lambda a: (-a[1], a[0]))[:MAX_LISTA]],
        "n_partidos_sin_casar": len(sin_casar),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--votos", required=True)
    ap.add_argument("--bloques", required=True)
    ap.add_argument("--eleccion", required=True)
    ap.add_argument("--alias", help="configuracion/alias_partidos_generales.csv (opcional)")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    c = cobertura(a.votos, a.bloques, a.eleccion, a.alias)
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(a.salida).write_text(json.dumps(c, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if c["votos_sin_casar"] > 0:
        top = ", ".join(f"{x['partido']}={x['votos']}" for x in c["partidos_sin_casar"][:5])
        print(f"::warning title=DOBLE_VUELTA_COBERTURA::{c['pct_sin_casar']} % de los votos sin casar con la tabla de bloques "
              f"({c['n_partidos_sin_casar']} partidos; {top}): se abstienen en la doble vuelta hasta tener la tabla de alias.")
    print(f"[doble_vuelta_cobertura] {c['eleccion']} sin_casar={c['pct_sin_casar']} % sin_bloque={c['pct_sin_bloque']} %")


if __name__ == "__main__":
    main()
