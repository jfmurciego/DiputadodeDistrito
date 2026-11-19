#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Doble vuelta con coaliciones por distrito (T-409, D-167): escenarios dv_base, dv_A y dv_B.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-17 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo. No toca el ganador actual (`primero`): es un paso aparte que lee la tabla de votos por partido y
  distrito de P31 (`district_id, party, votes`) y la tabla de bloques de `configuracion/`.
MOTIVO: D-167 (propietario, 17-11): escenario adicional de doble vuelta con coaliciones por bloque; diseño en
  docs/ESTUDIOS/T409_DOBLE_VUELTA/DISENO.md.
QUÉ HACE: por distrito y escenario (dv_base sin coaliciones; dv_A los tres bloques coaligados; dv_B solo Izquierdas y Patriotas):
  >50 % de los votos a candidaturas gana en primera vuelta; si no, segunda entre las dos más votadas y cada candidatura
  eliminada transfiere TODOS sus votos al finalista de su bloque (con dos finalistas del mismo bloque, al más votado en la
  primera vuelta); sin finalista de su bloque, o sin bloque, abstención. Empates: orden alfabético del id con `empate=true`.
  Sin tasas de trasvase inventadas ni votos reconstruidos. Salida CSV determinista y manifiesto con sha256 de entradas y salida.
USO: python herramientas/doble_vuelta.py --votos P31.csv --bloques configuracion/bloques_partidos_2026-11-17.csv
  --eleccion 2023-07 --salida salida.csv [--manifiesto manifiesto.json]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
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


def cargar_bloques(path, eleccion: str) -> dict[str, str]:
    """Partido → bloque de una elección. Un partido, un bloque; los vacíos quedan sin bloque."""
    out: dict[str, str] = {}
    with open(path, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            if fila["eleccion"] != eleccion:
                continue
            sigla, b = fila["siglas"], fila["bloque_propuesto"].strip()
            if b and b not in BLOQUES:
                raise ValueError(f"Bloque desconocido «{b}» para {sigla}")
            if sigla in out and out[sigla] != b:
                raise ValueError(f"{sigla} en dos bloques en {eleccion}")
            out[sigla] = b
    if not out:
        raise ValueError(f"Sin filas de la elección {eleccion} en {path}")
    return {k: v for k, v in out.items() if v}


def cargar_votos(path) -> dict[str, dict[str, int]]:
    d: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with open(path, encoding="utf-8", newline="") as f:
        for fila in csv.DictReader(f):
            d[str(fila["district_id"])][fila["party"]] += int(fila["votes"])
    return {k: dict(v) for k, v in d.items()}


def resolver(votos: dict[str, int], bloque_de: dict[str, str], escenario: str) -> dict:
    """Resuelve un distrito. `votos`: partido → votos; `bloque_de`: partido → bloque (ausente = sin bloque)."""
    coaligados = ESCENARIOS[escenario]
    cand: dict[str, int] = defaultdict(int)
    bloque: dict[str, str] = {}
    for p, v in votos.items():
        if v <= 0:
            continue
        b = bloque_de.get(p, "")
        k = f"bloque:{b}" if b and b in coaligados else p
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


def generar(votos_csv, bloques_csv, eleccion: str, salida, manifiesto=None) -> list[dict]:
    bloque_de = cargar_bloques(bloques_csv, eleccion)
    votos = cargar_votos(votos_csv)
    filas = []
    for distrito in sorted(votos, key=lambda x: (len(x), x)):
        for esc in ESCENARIOS:
            f = resolver(votos[distrito], bloque_de, esc)
            f["district_id"] = distrito
            filas.append(f)
    Path(salida).parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    if manifiesto:
        Path(manifiesto).write_text(json.dumps({
            "schema": "ddd.doble-vuelta/1.0", "eleccion": eleccion,
            "entradas": {"votos": {"ruta": str(votos_csv), "sha256": sha256(votos_csv)},
                         "bloques": {"ruta": str(bloques_csv), "sha256": sha256(bloques_csv)}},
            "salida": {"ruta": str(salida), "sha256": sha256(salida)}, "filas": len(filas),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--votos", required=True)
    ap.add_argument("--bloques", required=True)
    ap.add_argument("--eleccion", required=True, help="AAAA-MM, como en la tabla de bloques (p. ej. 2023-07)")
    ap.add_argument("--salida", required=True)
    ap.add_argument("--manifiesto")
    a = ap.parse_args()
    filas = generar(a.votos, a.bloques, a.eleccion, a.salida, a.manifiesto)
    print(f"[doble_vuelta] OK distritos={len(filas) // len(ESCENARIOS)} filas={len(filas)}")


if __name__ == "__main__":
    main()
