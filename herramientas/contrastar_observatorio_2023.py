#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contraste de los votos 2023 por sección con el Observatorio Electoral de las Naciones (T-71, D-8).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: por provincia con contrato Infoelectoral 2023, compara los votos a candidaturas por sección y partido del ZIP
  por mesa (fuente de datos/resultados) con data/202307/sekzioa/<cpro>.json de nazioenbehatokia.eus (r = {sección:
  [censo, votantes, votos a candidaturas, [[índice de partido, votos]…]], s = siglas}). Escribe
  datos/resultados/contraste_2023.csv: provincia, secciones en cada fuente, secciones solo en una, secciones con votos
  distintos, votos a candidaturas en cada fuente y partidos con total provincial distinto. Solo contrasta, no corrige.
Uso: python herramientas/contrastar_observatorio_2023.py [--zip ZIP] [--cache DIR] [--salida CSV]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import tempfile
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import fuente_infoelectoral_mesas as fim  # noqa: E402
import resultados_partidos as rp  # noqa: E402

URL = "https://nazioenbehatokia.eus/data/202307/sekzioa/{cpro}.json"
SALIDA = ROOT / "datos/resultados/contraste_2023.csv"
CABECERA = ["provincia", "territorio", "secciones_zip", "secciones_observatorio", "solo_zip", "solo_observatorio",
            "secciones_votos_distintos", "votos_zip", "votos_observatorio", "partidos_total_distinto"]


def observatorio(cpro: str, cache: Path | None) -> dict:
    f = cache / f"obs_{cpro}.json" if cache else None
    if f and f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    with urllib.request.urlopen(URL.format(cpro=cpro), timeout=120) as r:
        datos = r.read()
    if f:
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(datos)
    return json.loads(datos)


def votos_zip(zip_path: Path, contrato: dict) -> dict[str, dict[str, int]]:
    with tempfile.TemporaryDirectory() as tmp:
        fim.convert(zip_path, contrato, Path(tmp) / "m.csv")
        filas = list(csv.DictReader(open(Path(tmp) / "m.csv", encoding="utf-8")))
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in filas:
        out[r["codigo_provincia"] + r["codigo_municipio"] + r["codigo_distrito"] + r["codigo_seccion"]][r["partido"]] += int(r["votos"])
    return out


def votos_obs(d: dict) -> dict[str, dict[str, int]]:
    siglas = d["s"]
    return {s: {siglas[i]: v for i, v in x[3]} for s, x in d["r"].items()}


def contrastar(zv: dict, ov: dict) -> list:
    z, o = set(zv), set(ov)
    distintas = sum(1 for s in z & o if {p: v for p, v in zv[s].items() if v} != {p: v for p, v in ov[s].items() if v})
    tz, to = defaultdict(int), defaultdict(int)
    for s in z & o:
        for p, v in zv[s].items():
            tz[p] += v
        for p, v in ov[s].items():
            to[p] += v
    pd = sorted(p for p in set(tz) | set(to) if tz.get(p, 0) != to.get(p, 0))
    return [len(z), len(o), len(z - o), len(o - z), distintas, sum(tz.values()), sum(to.values()), " ".join(pd)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip", type=Path)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args(argv)
    ctr = rp.contratos()
    with tempfile.TemporaryDirectory() as tmp:
        zp = a.zip or rp.bajar_zip(next(iter(ctr.values())), Path(tmp) / "mesa.zip")
        vistos, filas = set(), []
        for t, c in sorted(ctr.items(), key=lambda kv: str(kv[1]["province"])):
            cpro = str(c["province"]).zfill(2)
            if cpro in vistos:
                continue
            vistos.add(cpro)
            filas.append([cpro, t] + contrastar(votos_zip(zp, c), votos_obs(observatorio(cpro, a.cache))))
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    with a.salida.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(CABECERA)
        w.writerows(filas)
    malas = [r for r in filas if r[4] or r[5] or r[6] or r[9]]
    print(f"contraste: {len(filas)} provincias; con diferencias: {len(malas)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
