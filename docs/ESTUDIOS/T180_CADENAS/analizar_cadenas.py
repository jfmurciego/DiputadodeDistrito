#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-180 — cuántas cadenas hacen falta en la competición del motor 2
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: T-180 · curva de cadenas
FECHA: 2026-11-10
ESTADO: estudio (no lo importa producción ni el motor; no lanza nada)
CAMBIOS: fichero nuevo.
MOTIVO: T-180: con UNA tanda de 20 cadenas por territorio (semillas públicas anidadas: semilla_i por índice), calcular
  a posteriori el ganador con las primeras N = 1, 2, 3, 5, 10, 15, 20 y su coste, con la función de calidad vigente
  (A) y con la función B de naturalidad (selección a posteriori sobre los mismos candidatos).
ANTERIOR: ninguna (fichero nuevo)
USO: python docs/ESTUDIOS/T180_CADENAS/analizar_cadenas.py --out bateria --seccionado-dir <dir con s2023/ s2024/ s2025/>
       [--salida docs/ESTUDIOS/T180_CADENAS] [--sin-b]
  Lee <out>/competicion/<t>/COMPETICION.json (ddd_motor2.competir --cadenas 20). Escribe CURVA.csv (territorio × N × función),
  TIEMPOS.csv (por candidato) y TERRITORIOS.csv (resumen por territorio)
  y AGREGADO.csv (por función y N).
FUNCIONES:
  A  la de competicion.py: (evaluable, violaciones duras, fuera de tolerancia, desvío máximo, ECM, huella, orden).
  B  la de ddd_motor2/naturalidad_competicion.py llevada a los candidatos de la competición: (evaluable, violaciones
     duras, fuera de tolerancia, partidos judiciales partidos + comarcas agrarias partidas, frontera cortada en km,
     desvío máximo, huella, orden). Demarcaciones por municipio (naturalidad_mapas.tablas_municipio); frontera entre
     secciones del seccionado INE del contrato (naturalidad_mapas.Geometria, EPSG:3035, >= 1 m).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

NS = (1, 2, 3, 5, 10, 15, 20)


def cargar(f: Path) -> dict:
    d = json.loads(f.read_text(encoding="utf-8"))
    sem = d["semilla_publica"]["semillas"]
    idx = {s: i for i, s in enumerate(sem, start=1)}
    for c in d["candidatos"]:
        c["i"] = 0 if c["id"] == d["canonico"] else idx[c["semilla"]]
    d["candidatos"].sort(key=lambda c: c["i"])
    return d


def evaluable(c) -> bool:
    return c["estado"] in ("VALIDO", "INVALIDO")


def clave_a(c) -> tuple:
    if not evaluable(c):
        return (1, 0, 0, 0.0, 0.0, "", c["i"])
    return (0, c["violaciones_duras"], c["fuera_tolerancia"], c["desvio_max"], c["ecm"], c["huella_plan"], c["i"])


def clave_b(c) -> tuple:
    if not evaluable(c) or c.get("b_partidas") is None:
        return (1, 0, 0, 0, 0.0, 0.0, "", c["i"])
    return (0, c["violaciones_duras"], c["fuera_tolerancia"], c["b_partidas"], c["b_corte_km"], c["desvio_max"],
            c["huella_plan"], c["i"])


def naturalidad(d: dict, secc_dir: Path, tablas: dict) -> None:
    """Añade b_partidas y b_corte_km a cada candidato evaluable (una geometría por territorio)."""
    from ddd_motor2 import naturalidad_mapas as nm
    asigs = {}
    for c in d["candidatos"]:
        if evaluable(c) and c["composicion"]:
            with open(ROOT / c["composicion"] if not Path(c["composicion"]).is_absolute() else c["composicion"],
                      encoding="utf-8") as fh:
                asigs[c["id"]] = {r["CUSEC_KEY"]: str(r["district_id"]) for r in csv.DictReader(fh)}
    if not asigs:
        return
    secciones = set(next(iter(asigs.values())))
    geo = nm.Geometria(nm.shp_de(secc_dir, nm.anio_seccionado(d["territorio"])), secciones)
    aristas = geo.aristas()
    for c in d["candidatos"]:
        a = asigs.get(c["id"])
        if a is None:
            continue
        partidas = 0
        for dem in ("pj", "ca"):
            ds: dict[str, set] = defaultdict(set)
            for s, dist in a.items():
                v = tablas[dem].get(s[:5])
                if v is not None:
                    ds[v].add(dist)
            partidas += sum(1 for x in ds.values() if len(x) > 1)
        c["b_partidas"] = partidas
        c["b_corte_km"] = round(sum(w for x, y, w in aristas if x in a and y in a and a[x] != a[y]) / 1000, 3)


def curva(d: dict, clave) -> list[dict]:
    can = d["candidatos"][0]
    filas, prev = [], None
    for n in NS:
        pool = [c for c in d["candidatos"] if c["i"] <= n]
        if len(pool) < n + 1:
            break
        g = min(pool, key=clave)
        filas.append({"n": n, "ganador": g["id"], "ganador_i": g["i"], "estado": g["estado"],
                      "fuera_tolerancia": g["fuera_tolerancia"], "desvio_max": g["desvio_max"], "ecm": g["ecm"],
                      "b_partidas": g.get("b_partidas"), "b_corte_km": g.get("b_corte_km"),
                      "mejora_canonico": clave(g)[:-2] < clave(can)[:-2],
                      "no_peor_que_n_anterior": prev is None or clave(g) <= prev})
        prev = clave(g)
    return filas


def percentil(xs: list, q: float):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None


def agregado(curvas: list[dict], terr: list[dict]) -> list[dict]:
    """Por función y N: territorios que mejoran al canónico, distritos fuera de tolerancia y desvío máximo sumados,
    territorios cuyo ganador cambia respecto al N anterior; y percentiles del N de saturación."""
    can = {t["territorio"]: t for t in terr}
    out = []
    for f in ("A", "B"):
        sat = [t[f"{f}_saturacion_n"] for t in terr]
        prev = {}
        for n in NS:
            fs = [r for r in curvas if r["funcion"] == f and r["n"] == n]
            if not fs:
                continue
            out.append({"funcion": f, "n": n, "territorios": len(fs),
                        "mejoran_canonico": sum(1 for r in fs if r["mejora_canonico"]),
                        "fuera_tolerancia_total": sum(r["fuera_tolerancia"] for r in fs),
                        "fuera_tolerancia_canonico": sum(can[r["territorio"]]["canonico_fuera"] for r in fs),
                        "desvio_max_medio": round(sum(r["desvio_max"] for r in fs) / len(fs), 5),
                        "desvio_max_medio_canonico": round(sum(can[r["territorio"]]["canonico_desvio_max"]
                                                               for r in fs) / len(fs), 5),
                        "b_partidas_total": sum(r["b_partidas"] or 0 for r in fs),
                        "cambian_frente_n_anterior": sum(1 for r in fs if r["territorio"] in prev
                                                         and prev[r["territorio"]] != r["ganador"]),
                        "saturados_en_n": sum(1 for x in sat if x <= n),
                        "saturacion_p50": percentil(sat, .5), "saturacion_p75": percentil(sat, .75),
                        "saturacion_p90": percentil(sat, .9), "saturacion_max": max(sat)})
            prev = {r["territorio"]: r["ganador"] for r in fs}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bateria")
    ap.add_argument("--seccionado-dir", type=Path)
    ap.add_argument("--salida", type=Path, default=Path(__file__).parent)
    ap.add_argument("--sin-b", action="store_true")
    a = ap.parse_args(argv)
    from ddd_motor2 import naturalidad_mapas as nm
    tablas = None if a.sin_b else nm.tablas_municipio()
    curvas, tiempos, terr = [], [], []
    for f in sorted((Path(a.out) / "competicion").glob("*/COMPETICION.json")):
        d = cargar(f)
        t = d["territorio"]
        if len(d["candidatos"]) < 21:
            print(f"{t}: {len(d['candidatos']) - 1} cadenas (< 20), se omite", file=sys.stderr)
            continue
        if not a.sin_b:
            try:
                naturalidad(d, a.seccionado_dir, tablas)
            except Exception as exc:  # sin geometría: B queda vacía, se dice
                print(f"{t}: B no calculable: {type(exc).__name__}: {exc}", file=sys.stderr)
        can = d["candidatos"][0]
        fila_t = {"territorio": t, "k": None, "canonico_estado": can["estado"],
                  "canonico_fuera": can["fuera_tolerancia"], "canonico_desvio_max": can["desvio_max"],
                  "validos": sum(1 for c in d["candidatos"] if c["estado"] == "VALIDO"),
                  "huella_resultado": d["huella_resultado"]}
        for nombre, clave in (("A", clave_a), ("B", clave_b)):
            cv = curva(d, clave)
            g20 = cv[-1]
            sat = 0 if g20["ganador_i"] == 0 else min(n for n in NS if n >= g20["ganador_i"])  # 0: ninguna cadena mejora
            fila_t[f"{nombre}_saturacion_n"] = sat
            fila_t[f"{nombre}_ganador_20"] = g20["ganador"]
            fila_t[f"{nombre}_mejora_20"] = g20["mejora_canonico"]
            fila_t[f"{nombre}_anidamiento_ok"] = all(r["no_peor_que_n_anterior"] for r in cv)
            for r in cv:
                curvas.append({"territorio": t, "funcion": nombre, **r})
        try:
            with open(ROOT / can["composicion"], encoding="utf-8") as fh:
                fila_t["k"] = len({r["district_id"] for r in csv.DictReader(fh)})
        except OSError:
            fila_t["k"] = None
        for c in d["candidatos"]:
            ex = (c.get("extra") or {}).get("tiempos") or {}
            tiempos.append({"territorio": t, "i": c["i"], "id": c["id"], "estado": c["estado"],
                            "generar_s": c["tiempos"].get("generar_s"), "juzgar_s": c["tiempos"].get("juzgar_s"),
                            **{f"t_{k}": v for k, v in sorted(ex.items())}})
        ch = [c["tiempos"]["generar_s"] + c["tiempos"].get("juzgar_s", 0) for c in d["candidatos"][1:]]
        base = can["tiempos"]["generar_s"] + can["tiempos"].get("juzgar_s", 0)
        fila_t.update({"canonico_s": round(base, 1), "cadena_media_s": round(sum(ch) / len(ch), 1),
                       "cadena_max_s": round(max(ch), 1),
                       **{f"total_n{n}_s": round(base + sum(ch[:n]), 1) for n in (5, 10, 20)}})
        terr.append(fila_t)
    a.salida.mkdir(parents=True, exist_ok=True)
    for nombre, filas in (("AGREGADO.csv", agregado(curvas, terr)), ("CURVA.csv", curvas), ("TIEMPOS.csv", tiempos), ("TERRITORIOS.csv", terr)):
        cols = []
        for r in filas:
            cols += [k for k in r if k not in cols]
        with open(a.salida / nombre, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, cols)
            w.writeheader()
            w.writerows(filas)
    print(f"{len(terr)} territorios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
