#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tabla de alias id de fuente → partido homologado de las generales 2011-2023, derivada de los ficheros de homologación (T-409).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: los ids de partido de P31 (`<run>_m07_resultados_partido.csv`) son siglas de la fuente («PP-EU», «PSE-EE (PSOE)», «SUMAR», «C's»), no
  las siglas homologadas de `configuracion/bloques_partidos_*.csv`: sin este paso entre el 16 % y el 54 % de los votos no casaban y se
  abstenían en la doble vuelta (D-167, D-171). Orden del Planificador: se DERIVA de la homologación existente (con fuente y sha256), no se
  escribe a mano; lo que no sale solo se lista para el propietario.
QUÉ HACE: por elección, une cuatro fuentes ficheradas, en este orden de prioridad, y no admite que un mismo id (elección, id) acabe en dos
  partidos homologados (esos casos van a CONFLICTOS, no a la tabla):
  HOMOLOGACION  datos/homologacion_siglas/homologacion_siglas_generales.csv: sigla_fuente → partido_homologado (sha256 del fichero);
  INTERIOR      datos/homologacion_siglas/reglas_generales.json, clave `interior` (siglas de Interior 2019-11 y 2023);
  ALIAS_BOE     configuracion/alias_siglas_boe_espejo.csv: sigla del BOE → siglas del espejo → partido homologado (solo si todas las siglas del
                espejo de esa fila dan el mismo partido);
  IDENTIDAD     el propio partido homologado.
  Mide la cobertura (votos) sobre los ids que pueden llegar a P31: los partidos de los CSV oficiales del BOE
  (configuracion/resultados_oficiales_congreso_*.csv) y los de las salidas M07 históricas del repositorio
  (datos/resultados/historico/<elección>/<territorio>/resultados_partido.csv). Los ids sin alias se escriben en el fichero de pendientes.
USO: python herramientas/alias_partidos_generales.py generar | comprobar
  generar     escribe configuracion/alias_partidos_generales.csv, _pendientes.csv y .json (determinista).
  comprobar   falla si lo versionado no es lo que se deriva hoy de las fuentes (huellas incluidas).
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOMOLOGACION = Path("datos/homologacion_siglas/homologacion_siglas_generales.csv")
REGLAS = Path("datos/homologacion_siglas/reglas_generales.json")
ALIAS_BOE = Path("configuracion/alias_siglas_boe_espejo.csv")
BOE = {"201111": "2011_11", "201512": "2015_12", "201606": "2016_06", "201904": "2019_04", "201911": "2019_11", "202307": "2023"}
SALIDA = Path("configuracion/alias_partidos_generales.csv")
PENDIENTES = Path("configuracion/alias_partidos_generales_pendientes.csv")
RESUMEN = Path("configuracion/alias_partidos_generales.json")
COLS = ["eleccion", "id_fuente", "partido_homologado", "origen", "fuente"]
COLS_P = ["eleccion", "id_fuente", "votos", "universo", "motivo"]
HISTORICO = "datos/resultados/historico/[0-9]*/*/resultados_partido.csv"  # <elección>/<territorio>: sin detección por prefijo (T-220)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def derivar(root: Path = ROOT) -> dict:
    cand: dict[tuple, dict[str, tuple]] = defaultdict(dict)  # (e, id) → {partido: (origen, fuente)} en orden de prioridad

    def alta(e, i, p, origen, fuente):
        cand[(e, i)].setdefault(p, (origen, fuente))

    hom = list(csv.DictReader(open(root / HOMOLOGACION, encoding="utf-8", newline="")))
    por_sigla: dict[tuple, set] = defaultdict(set)
    for x in hom:
        por_sigla[(x["eleccion"], x["sigla_fuente"])].add(x["partido_homologado"])
    for (e, s), ps in por_sigla.items():
        for p in ps:
            alta(e, s, p, "HOMOLOGACION", str(HOMOLOGACION))
    reglas = json.loads((root / REGLAS).read_text(encoding="utf-8"))
    for e, m in (reglas.get("interior") or {}).items():
        for s, p in m.items():
            alta(e, s, p, "INTERIOR", f"{REGLAS}#interior")
    for x in csv.DictReader(open(root / ALIAS_BOE, encoding="utf-8", newline="")):
        e = x["eleccion"]
        ps = set()
        for s in [t.strip() for t in x["siglas_espejo"].split("+")] if "+" in x["siglas_espejo"] else [x["siglas_espejo"].strip()]:
            ps |= por_sigla.get((e, s), set())
        if len(ps) == 1:
            alta(e, x["sigla_boe"], next(iter(ps)), "ALIAS_BOE", str(ALIAS_BOE))
    for x in hom:
        alta(x["eleccion"], x["partido_homologado"], x["partido_homologado"], "IDENTIDAD", str(HOMOLOGACION))
    filas, conflictos = [], []
    for (e, i), ps in sorted(cand.items()):
        elegido = {p for p, (o, _) in ps.items() if o != "IDENTIDAD"} or set(ps)
        if len(elegido) > 1:
            conflictos.append({"eleccion": e, "id_fuente": i, "candidatos": sorted(elegido)})
            continue
        p = next(iter(elegido))
        o, f = ps[p]
        filas.append({"eleccion": e, "id_fuente": i, "partido_homologado": p, "origen": o, "fuente": f})
    return {"filas": filas, "conflictos": conflictos}


def universo(root: Path = ROOT) -> list[tuple]:
    """(elección, id, votos, universo) de los ids que pueden llegar a P31."""
    out = []
    for e, f in BOE.items():
        por = defaultdict(int)
        for r in csv.DictReader(open(root / f"configuracion/resultados_oficiales_congreso_{f}.csv", encoding="utf-8", newline="")):
            por[r["partido"]] += int(r["votos"] or 0)
        out += [(e, p, v, "BOE") for p, v in por.items()]
    por = defaultdict(int)
    for f in sorted(glob.glob(str(root / HISTORICO))):
        e = Path(f).parts[-3]
        for r in csv.DictReader(open(f, encoding="utf-8", newline="")):
            por[(e, r["party"])] += int(float(r["votes"]))
    out += [(e, p, v, "M07_HISTORICO") for (e, p), v in por.items()]
    return out


def construir(root: Path = ROOT) -> dict:
    d = derivar(root)
    tabla = {(f["eleccion"], f["id_fuente"]) for f in d["filas"]}
    conf = {(c["eleccion"], c["id_fuente"]): "|".join(c["candidatos"]) for c in d["conflictos"]}
    pend, tot, sin = [], defaultdict(int), defaultdict(int)
    for e, i, v, u in universo(root):
        tot[(e, u)] += v
        if (e, i) not in tabla:
            sin[(e, u)] += v
            pend.append({"eleccion": e, "id_fuente": i, "votos": v, "universo": u,
                         "motivo": f"CONFLICTO: {conf[(e, i)]}" if (e, i) in conf else "SIN_FUENTE_DE_HOMOLOGACION"})
    pend.sort(key=lambda p: (p["eleccion"], p["universo"], -p["votos"], p["id_fuente"]))
    resumen = {
        "schema": "ddd.alias-partidos-generales/1.0",
        "fuentes": {str(p): sha256(root / p) for p in (HOMOLOGACION, REGLAS, ALIAS_BOE)},
        "filas": len(d["filas"]), "conflictos": d["conflictos"],
        "cobertura_votos": {f"{e}/{u}": {"votos": tot[(e, u)], "sin_alias": sin[(e, u)],
                                         "pct_cubierto": round(100 * (1 - sin[(e, u)] / tot[(e, u)]), 4) if tot[(e, u)] else None}
                            for (e, u) in sorted(tot)},
        "pendientes": len(pend),
    }
    return {"filas": d["filas"], "pendientes": pend, "resumen": resumen}


def _csv(filas, cols) -> str:
    import io
    b = io.StringIO()
    w = csv.DictWriter(b, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    return b.getvalue()


def textos(root: Path = ROOT) -> dict[Path, str]:
    c = construir(root)
    return {SALIDA: _csv(c["filas"], COLS), PENDIENTES: _csv(c["pendientes"], COLS_P),
            RESUMEN: json.dumps(c["resumen"], ensure_ascii=False, indent=2) + "\n"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("orden", choices=["generar", "comprobar"])
    a = ap.parse_args(argv)
    t = textos()
    if a.orden == "generar":
        for p, s in t.items():
            (ROOT / p).write_text(s, encoding="utf-8")
        r = json.loads(t[RESUMEN])
        print(f"[alias_partidos] filas={r['filas']} conflictos={len(r['conflictos'])} pendientes={r['pendientes']}")
        return 0
    malos = [str(p) for p, s in t.items() if not (ROOT / p).is_file() or (ROOT / p).read_text(encoding="utf-8") != s]
    if malos:
        print(f"::error title=ALIAS_PARTIDOS::distinto de lo derivado hoy: {', '.join(malos)}; ejecuta `generar`.")
        return 1
    print("[alias_partidos] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
