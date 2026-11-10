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
USO: (1) desde la tanda local, calculando B con la geometría y guardando los datos para el repo:
       python docs/ESTUDIOS/T180_CADENAS/analizar_cadenas.py --out bateria --seccionado-dir <dir con s2023/ s2024/ s2025/> \
         --guardar-datos docs/ESTUDIOS/T180_CADENAS/datos [--reproducibilidad bateria_rep]
     (2) desde el repo, sin geometría ni tanda (regenera las mismas tablas):
       python docs/ESTUDIOS/T180_CADENAS/analizar_cadenas.py --out docs/ESTUDIOS/T180_CADENAS/datos \
         --naturalidad-b docs/ESTUDIOS/T180_CADENAS/datos/NATURALIDAD_B.csv [--salida <dir>]
  Lee <out>/competicion/<t>/COMPETICION.json (ddd_motor2.competir --cadenas 20). Si un territorio no tiene B (sin
  geometría o con error), su fila de TERRITORIOS.csv lo dice en B_estado y no entra en la curva B. Escribe CURVA.csv (territorio × N × función),
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
import shutil
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


def naturalidad(d: dict, secc_dir: Path, tablas: dict) -> str:
    """Añade b_partidas y b_corte_km a cada candidato evaluable (una geometría por territorio)."""
    from ddd_motor2 import naturalidad_mapas as nm
    asigs = {}
    for c in d["candidatos"]:
        if evaluable(c) and c["composicion"]:
            with open(ROOT / c["composicion"] if not Path(c["composicion"]).is_absolute() else c["composicion"],
                      encoding="utf-8") as fh:
                asigs[c["id"]] = {r["CUSEC_KEY"]: str(r["district_id"]) for r in csv.DictReader(fh)}
    if not asigs:
        return ""
    secciones = set(next(iter(asigs.values())))
    shp = nm.shp_de(secc_dir, nm.anio_seccionado(d["territorio"]))
    geo = nm.Geometria(shp, secciones)
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
    return nm.sha256(shp)


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
                      # cierto por construcción (mínimo sobre un conjunto creciente): comprobación de coherencia, no prueba
                      "monotono": prev is None or clave(g) <= prev})
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
        sat = [t[f"{f}_saturacion_n"] for t in terr if f"{f}_saturacion_n" in t]
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
                        "saturacion_p90": percentil(sat, .9), "saturacion_max": max(sat) if sat else None})
            prev = {r["territorio"]: r["ganador"] for r in fs}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bateria")
    ap.add_argument("--seccionado-dir", type=Path)
    ap.add_argument("--salida", type=Path, default=Path(__file__).parent)
    ap.add_argument("--naturalidad-b", type=Path, help="B ya calculada (NATURALIDAD_B.csv); evita la geometría")
    ap.add_argument("--guardar-datos", type=Path, help="copia COMPETICION.json y NATURALIDAD_B.csv para el repo")
    ap.add_argument("--reproducibilidad", type=Path, help="otra tanda (<dir>/competicion/<t>) para comparar huellas")
    a = ap.parse_args(argv)
    from ddd_motor2 import naturalidad_mapas as nm
    tablas = nm.tablas_municipio() if a.seccionado_dir else None
    b_guardada: dict[str, dict] = defaultdict(dict)
    if a.naturalidad_b:
        with open(a.naturalidad_b, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                b_guardada[r["territorio"]][r["id"]] = (int(r["b_partidas"]), float(r["b_corte_km"]))
    curvas, tiempos, terr, b_filas = [], [], [], []
    for f in sorted((Path(a.out) / "competicion").glob("*/COMPETICION.json")):
        d = cargar(f)
        t = d["territorio"]
        if len(d["candidatos"]) < 21:
            print(f"{t}: {len(d['candidatos']) - 1} cadenas (< 20), se omite", file=sys.stderr)
            continue
        b_estado = "NO_EVALUABLE: sin geometría ni NATURALIDAD_B.csv"
        if t in b_guardada:
            for c in d["candidatos"]:
                if c["id"] in b_guardada[t]:
                    c["b_partidas"], c["b_corte_km"] = b_guardada[t][c["id"]]
            b_estado = "OK"
        elif a.seccionado_dir:
            try:
                sha_shp = naturalidad(d, a.seccionado_dir, tablas)
                b_estado = "OK"
                b_filas += [{"territorio": t, "id": c["id"], "b_partidas": c["b_partidas"],
                             "b_corte_km": c["b_corte_km"], "seccionado_sha256": sha_shp}
                            for c in d["candidatos"] if c.get("b_partidas") is not None]
            except Exception as exc:  # se dice en la salida: el territorio no entra en la curva B
                b_estado = f"ERROR: {type(exc).__name__}: {exc}"
        if b_estado == "OK" and any(evaluable(c) and c.get("b_partidas") is None for c in d["candidatos"]):
            b_estado = "ERROR: candidatos evaluables sin B"
        can = d["candidatos"][0]
        fila_t = {"territorio": t, "k": None, "canonico_estado": can["estado"],
                  "canonico_fuera": can["fuera_tolerancia"], "canonico_desvio_max": can["desvio_max"],
                  "validos": sum(1 for c in d["candidatos"] if c["estado"] == "VALIDO"),
                  "huella_resultado": d["huella_resultado"]}
        fila_t["B_estado"] = b_estado
        for nombre, clave in (("A", clave_a), ("B", clave_b)):
            if nombre == "B" and b_estado != "OK":
                continue
            cv = curva(d, clave)
            g20 = cv[-1]
            sat = 0 if g20["ganador_i"] == 0 else min(n for n in NS if n >= g20["ganador_i"])  # 0: ninguna cadena mejora
            fila_t[f"{nombre}_saturacion_n"] = sat
            fila_t[f"{nombre}_ganador_20"] = g20["ganador"]
            fila_t[f"{nombre}_mejora_20"] = g20["mejora_canonico"]
            fila_t[f"{nombre}_monotono"] = all(r["monotono"] for r in cv)
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
    if a.guardar_datos:
        for t in terr:
            dst = a.guardar_datos / "competicion" / t["territorio"]
            dst.mkdir(parents=True, exist_ok=True)
            shutil.copy2(Path(a.out) / "competicion" / t["territorio"] / "COMPETICION.json", dst / "COMPETICION.json")
        if b_filas:
            with open(a.guardar_datos / "NATURALIDAD_B.csv", "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, list(b_filas[0]))
                w.writeheader()
                w.writerows(b_filas)
    if a.reproducibilidad:
        rep = []
        for f in sorted((a.reproducibilidad / "competicion").glob("*/COMPETICION.json")):
            r2 = cargar(f)
            r1 = cargar(Path(a.out) / "competicion" / r2["territorio"] / "COMPETICION.json")
            c1 = {c["semilla"]: c for c in r1["candidatos"]}
            s2 = r2["semilla_publica"]["semillas"]
            for c in r2["candidatos"]:
                o = c1.get(c["semilla"]) if c["i"] else r1["candidatos"][0]
                rep.append({"territorio": r2["territorio"], "i": c["i"], "id": c["id"],
                            "semilla_anidada": c["i"] == 0 or s2[c["i"] - 1] == r1["semilla_publica"]["semillas"][c["i"] - 1],
                            "huella_plan_igual": o is not None and o["huella_plan"] == c["huella_plan"],
                            "composicion_sha256_igual": o is not None and o["composicion_sha256"] == c["composicion_sha256"],
                            "huella_plan": c["huella_plan"], "composicion_sha256": c["composicion_sha256"]})
        if rep:
            with open(a.salida / "REPRODUCIBILIDAD.csv", "w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, list(rep[0]))
                w.writeheader()
                w.writerows(rep)
            if a.guardar_datos:
                for f in (a.reproducibilidad / "competicion").glob("*/COMPETICION.json"):
                    dst = a.guardar_datos / "reproducibilidad" / f.parent.name
                    dst.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dst / "COMPETICION.json")
    print(f"{len(terr)} territorios")
    return 0


if __name__ == "__main__":
    sys.exit(main())
