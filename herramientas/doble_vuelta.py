#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Doble vuelta con coaliciones por distrito (T-409, D-167): escenarios dv_base, dv_A y dv_B.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.4.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: legacy/herramientas/doble_vuelta_v1.3.0_20261119.py
CAMBIOS: 1.4.0 (T-421): `--comunidad`: tabla de bloques y alias de autonómicas llevan columna `comunidad` y se filtran por ella (la tabla va por partido tras el alias); `--comunidad` sin `--alias` falla; sin `--comunidad` nada cambia.
  1.3.0 (T-409): `--alias` (configuracion/alias_partidos_generales.csv): el id de partido de P31 pasa a su partido homologado antes de buscar el bloque
  (los ids que dan el mismo partido suman sus votos); sin `--alias` nada cambia. El manifiesto lleva el sha256 del alias.
  1.2.0 (T-409, revisor de #904): los partidos con votos que NO están en la tabla de bloques de la elección («sin casar») se informan
  (manifiesto `sin_casar` con recuento, votos y lista, y ::warning en stderr) en vez de tratarse en silencio como sin bloque; el cálculo no cambia.
  1.1.0 (T-409): detalle por partido (`--detalle`, `detalle()`): por distrito y escenario, cada partido con su bloque, su
  candidatura (la coalición en dv_A/dv_B) y sus votos de primera vuelta; `resolver` no cambia. 1.0.0: fichero nuevo. No toca el ganador actual (`primero`): es un paso aparte que lee la tabla de votos por partido y
  distrito de P31 (`district_id, party, votes`) y la tabla de bloques de `configuracion/`.
MOTIVO: D-167 (propietario, 17-11): escenario adicional de doble vuelta con coaliciones por bloque; diseño en
  docs/ESTUDIOS/T409_DOBLE_VUELTA/DISENO.md.
QUÉ HACE: por distrito y escenario (dv_base sin coaliciones; dv_A los tres bloques coaligados; dv_B solo Izquierdas y Patriotas):
  >50 % de los votos a candidaturas gana en primera vuelta; si no, segunda entre las dos más votadas y cada candidatura
  eliminada transfiere TODOS sus votos al finalista de su bloque (con dos finalistas del mismo bloque, al más votado en la
  primera vuelta); sin finalista de su bloque, o sin bloque, abstención. Empates: orden alfabético del id con `empate=true`.
  Sin tasas de trasvase inventadas ni votos reconstruidos. Salida CSV determinista y manifiesto con sha256 de entradas y salida.
USO: python herramientas/doble_vuelta.py --votos P31.csv --bloques configuracion/bloques_partidos_2026-11-17.csv
  --eleccion 2023-07 --salida salida.csv [--manifiesto manifiesto.json] [--detalle detalle.csv]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

BLOQUES = ("Izquierdas", "Nacionalistas", "Patriotas")
ESCENARIOS = {
    "dv_base": frozenset(),
    "dv_A": frozenset(BLOQUES),
    "dv_B": frozenset({"Izquierdas", "Patriotas"}),
}
COLUMNAS = [
    "district_id", "escenario", "vuelta_decisiva", "candidatura_ganadora", "bloque_ganador", "votos_1v", "cuota_1v",
    "finalista_a", "finalista_b", "votos_a_2v", "votos_b_2v", "cuota_ganador_2v", "votos_abstencion", "empate",
]


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def cargar_tabla(path, eleccion: str, comunidad: str | None = None) -> dict[str, str]:
    """Partido → bloque de TODAS las filas de la elección (el bloque vacío = sin bloque, pero casado). Un partido, un bloque."""
    out: dict[str, str] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["eleccion"] != eleccion or (comunidad is not None and fila.get("comunidad") != comunidad):
                continue
            sigla, b = fila["siglas"], fila["bloque_propuesto"].strip()
            if b and b not in BLOQUES:
                raise ValueError(f"Bloque desconocido «{b}» para {sigla}")
            if sigla in out and out[sigla] != b:
                raise ValueError(f"{sigla} en dos bloques en {eleccion}")
            out[sigla] = b
    if not out:
        raise ValueError(f"Sin filas de la elección {eleccion} en {path}")
    return out


def cargar_bloques(path, eleccion: str, comunidad: str | None = None) -> dict[str, str]:
    """Partido → bloque de una elección; los vacíos (sin bloque) no figuran."""
    return {k: v for k, v in cargar_tabla(path, eleccion, comunidad).items() if v}


def eleccion_alias(eleccion: str) -> str:
    """'2023-07' → '202307' (formato de la tabla de alias)."""
    return eleccion.replace("-", "")


def cargar_alias(path, eleccion: str, comunidad: str | None = None) -> dict[str, str]:
    """id de fuente → partido homologado de una elección (tabla de configuracion/alias_partidos_generales.csv)."""
    e = eleccion_alias(eleccion)
    out: dict[str, str] = {}
    with open(path, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        if "comunidad" in (lector.fieldnames or []) and comunidad is None:
            raise ValueError(f"El alias {path} es por comunidad: indica --comunidad")
        for fila in lector:
            if fila["eleccion"] == e and (comunidad is None or fila.get("comunidad") == comunidad):
                out[fila["id_fuente"]] = fila["partido_homologado"]
    if not out:
        raise ValueError(f"Sin alias de la elección {eleccion} en {path}")
    return out


def aplicar_alias(votos: dict[str, dict[str, int]], alias: dict[str, str]) -> dict[str, dict[str, int]]:
    """Pasa cada id a su partido homologado (los sin alias quedan como están) y suma los que coinciden."""
    out: dict[str, dict[str, int]] = {}
    for d, por_partido in votos.items():
        acc: dict[str, int] = defaultdict(int)
        for p, v in por_partido.items():
            acc[alias.get(p, p)] += v
        out[d] = dict(acc)
    return out


def sin_casar(votos: dict[str, dict[str, int]], tabla: dict[str, str]) -> dict[str, int]:
    """Partidos con votos que no están en la tabla de la elección (≠ sin bloque): partido → votos."""
    out: dict[str, int] = defaultdict(int)
    for por_partido in votos.values():
        for p, v in por_partido.items():
            if v > 0 and p not in tabla:
                out[p] += v
    return dict(out)


def cargar_votos(path) -> dict[str, dict[str, int]]:
    d: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with open(path, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            d[str(fila["district_id"])][fila["party"]] += int(fila["votes"])
    return {k: dict(v) for k, v in d.items()}


DETALLE_COLUMNAS = ["district_id", "escenario", "candidatura", "partido", "bloque", "votos_1v", "votos_candidatura"]


def _clave(partido: str, bloque_de: dict[str, str], coaligados) -> str:
    b = bloque_de.get(partido, "")
    return f"bloque:{b}" if b and b in coaligados else partido


def detalle(votos: dict[str, int], bloque_de: dict[str, str], escenario: str) -> list[dict]:
    """Votos de primera vuelta por partido con su bloque y la candidatura en la que compite (la coalición, si la hay)."""
    coaligados = ESCENARIOS[escenario]
    filas = [{"escenario": escenario, "candidatura": _clave(p, bloque_de, coaligados), "partido": p,
              "bloque": bloque_de.get(p, ""), "votos_1v": v} for p, v in votos.items() if v > 0]
    por_cand: dict[str, int] = defaultdict(int)
    for f in filas:
        por_cand[f["candidatura"]] += f["votos_1v"]
    for f in filas:
        f["votos_candidatura"] = por_cand[f["candidatura"]]
    return sorted(filas, key=lambda f: (-f["votos_candidatura"], f["candidatura"], -f["votos_1v"], f["partido"]))


def resolver(votos: dict[str, int], bloque_de: dict[str, str], escenario: str) -> dict:
    """Resuelve un distrito. `votos`: partido → votos; `bloque_de`: partido → bloque (ausente = sin bloque)."""
    coaligados = ESCENARIOS[escenario]
    cand: dict[str, int] = defaultdict(int)
    bloque: dict[str, str] = {}
    for p, v in votos.items():
        if v <= 0:
            continue
        b = bloque_de.get(p, "")
        k = _clave(p, bloque_de, coaligados)
        cand[k] += v
        bloque[k] = b
    fila = {c: "" for c in COLUMNAS}
    fila["escenario"] = escenario
    total = sum(cand.values())
    if total == 0:
        fila.update(vuelta_decisiva="", votos_1v=0, votos_abstencion=0, empate="false")
        return fila
    orden = sorted(cand, key=lambda k: (-cand[k], k))
    top = orden[0]
    fila.update(votos_1v=cand[top], cuota_1v=f"{cand[top] / total:.6f}")
    if cand[top] * 2 > total or len(orden) == 1:
        fila.update(vuelta_decisiva=1, candidatura_ganadora=top, bloque_ganador=bloque[top], votos_abstencion=0, empate="false")
        return fila
    a, b = orden[0], orden[1]
    empate = len(orden) > 2 and cand[orden[1]] == cand[orden[2]]
    fin = {a: cand[a], b: cand[b]}
    abst = 0
    for k in orden[2:]:
        mismos = [f for f in (a, b) if bloque[k] and bloque[f] == bloque[k]]
        if mismos:
            fin[sorted(mismos, key=lambda f: (-cand[f], f))[0]] += cand[k]
        else:
            abst += cand[k]
    gana, pierde = sorted(fin, key=lambda k: (-fin[k], k))
    empate = empate or fin[gana] == fin[pierde]
    fila.update(
        vuelta_decisiva=2, candidatura_ganadora=gana, bloque_ganador=bloque[gana], finalista_a=a, finalista_b=b,
        votos_a_2v=fin[a], votos_b_2v=fin[b], cuota_ganador_2v=f"{fin[gana] / (fin[a] + fin[b]):.6f}",
        votos_abstencion=abst, empate="true" if empate else "false",
    )
    return fila


def generar(votos_csv, bloques_csv, eleccion: str, salida, manifiesto=None, detalle_csv=None, alias_csv=None, comunidad=None) -> list[dict]:
    if comunidad and not alias_csv:
        raise ValueError("--comunidad exige --alias")
    tabla = cargar_tabla(bloques_csv, eleccion, comunidad)
    bloque_de = {k: v for k, v in tabla.items() if v}
    votos = cargar_votos(votos_csv)
    if alias_csv:
        votos = aplicar_alias(votos, cargar_alias(alias_csv, eleccion, comunidad))
    huerfanos = sin_casar(votos, tabla)
    if huerfanos:
        total = sum(v for d in votos.values() for v in d.values())
        top = sorted(huerfanos.items(), key=lambda a: (-a[1], a[0]))
        print(f"::warning title=DOBLE_VUELTA_SIN_CASAR::{len(huerfanos)} partidos con {sum(huerfanos.values())} votos "
              f"({100 * sum(huerfanos.values()) / total:.2f} %) no están en la tabla de bloques de {eleccion} y se abstienen: "
              + ", ".join(f"{p}={v}" for p, v in top[:5]), file=sys.stderr)
    filas, det = [], []
    for distrito in sorted(votos, key=lambda x: (len(x), x)):
        for esc in ESCENARIOS:
            f = resolver(votos[distrito], bloque_de, esc)
            f["district_id"] = distrito
            filas.append(f)
            det += [{**d, "district_id": distrito} for d in detalle(votos[distrito], bloque_de, esc)]
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    if detalle_csv:
        Path(detalle_csv).parent.mkdir(parents=True, exist_ok=True)
        with open(detalle_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=DETALLE_COLUMNAS, lineterminator="\n")
            w.writeheader()
            w.writerows(det)
    if manifiesto:
        Path(manifiesto).write_text(json.dumps({
            "schema": "ddd.doble-vuelta/1.0", "eleccion": eleccion, **({"comunidad": comunidad} if comunidad else {}),
            "entradas": {"votos": {"ruta": str(votos_csv), "sha256": sha256(votos_csv)},
                         "bloques": {"ruta": str(bloques_csv), "sha256": sha256(bloques_csv)}},
            "salida": {"ruta": str(salida), "sha256": sha256(salida)}, "filas": len(filas),
            "sin_casar": {"n_partidos": len(huerfanos), "votos": sum(huerfanos.values()),
                          "lista": [{"partido": p, "votos": v} for p, v in sorted(huerfanos.items(), key=lambda a: (-a[1], a[0]))[:25]]},
            **({"alias": {"ruta": str(alias_csv), "sha256": sha256(alias_csv)}} if alias_csv else {}),
            **({"detalle": {"ruta": str(detalle_csv), "sha256": sha256(detalle_csv)}} if detalle_csv else {}),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--votos", required=True)
    ap.add_argument("--bloques", required=True)
    ap.add_argument("--eleccion", required=True, help="AAAA-MM, como en la tabla de bloques (p. ej. 2023-07)")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--manifiesto")
    ap.add_argument("--comunidad", help="con --alias de autonómicas: id del territorio (aut01…) cuyo alias se usa")
    ap.add_argument("--alias", help="configuracion/alias_partidos_generales.csv: id de partido de P31 → partido homologado (opcional)")
    ap.add_argument("--detalle", help="CSV de detalle por partido, bloque y candidatura (opcional)")
    a = ap.parse_args()
    if a.comunidad and not a.alias:
        ap.error("--comunidad exige --alias")
    filas = generar(a.votos, a.bloques, a.eleccion, a.salida, a.manifiesto, a.detalle, a.alias, a.comunidad)
    print(f"[doble_vuelta] OK distritos={len(filas) // len(ESCENARIOS)} filas={len(filas)}")


if __name__ == "__main__":
    main()
