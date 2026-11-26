#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: estudio T-465/T-466 (piloto del banco) — tabla común Deslinde / GerryChain puro / exacto
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Tabla del piloto
FECHA: 2026-11-26
ESTADO: estudio (solo lee JSON de resultados)
CAMBIOS: fichero nuevo.
MOTIVO: juntar en un resumen los JSON del exacto (optimo_d8.py) y de GerryChain puro (gerrychain_puro.py, uno por semilla).
ANTERIOR: ninguna (fichero nuevo)
USO: python docs/ESTUDIOS/T465_BANCO_PILOTO/tabla.py --exacto <dir> --gc <dir> --salida resultados/RESUMEN.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TER = ("fuera", "exceso_8", "partidas", "frontera_km", "desvio_max")


def clave(d: dict) -> tuple:
    return tuple(d[k] for k in TER)


def primer_hueco(a: dict, b: dict) -> dict | None:
    for k in TER:
        if a[k] != b[k]:
            return {"termino": k, "metodo": a[k], "referencia": b[k]}
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exacto", type=Path, required=True)
    ap.add_argument("--gc", type=Path, required=True)
    ap.add_argument("--salida", type=Path, required=True)
    a = ap.parse_args()
    out = {}
    for f in sorted(a.exacto.glob("nac*.json")):
        ex = json.loads(f.read_text(encoding="utf-8"))
        t = ex["territorio"]
        esp = ex["espacios"]["canonico"]
        opt = esp["mejor_modelo"]["clave_d8"]
        gan = ex["ganador"]["clave_d8"]
        semillas = []
        for g in sorted(a.gc.glob(f"{t}_s*.json"), key=lambda p: int(p.stem.split("_s")[1])):
            for s in json.loads(g.read_text(encoding="utf-8"))["semillas"]:
                semillas.append(s)
        filas = []
        for s in semillas:
            fila = {"semilla": s["semilla"], "estado": s["estado"], "intentos_semilla": s.get("intentos_semilla"),
                    "paso_mejor": s.get("paso_mejor"), "autobucles": s.get("autobucles"),
                    "cpu_s": s.get("cpu_s")}
            for corte, c in (s.get("cortes") or {}).items():
                ck = c["clave_d8"]
                fila[corte] = {"partidas": ck["partidas"], "exceso_8": ck["exceso_8"], "fuera": ck["fuera"],
                               "frontera_km": ck["frontera_km"], "desvio_max": ck["desvio_max"],
                               "vs_deslinde": ("mejor" if clave(ck) < clave(gan) else "igual" if clave(ck) == clave(gan)
                                               else "peor"),
                               "hueco_optimo": primer_hueco(ck, opt)}
            filas.append(fila)
        mejores = {}
        for corte in ("1000", "10000", "100000"):
            ks = [f[corte] for f in filas if corte in f]
            if ks:
                m = min(ks, key=clave)
                mejores[corte] = {"mejor": {k: m[k] for k in TER}, "vs_deslinde": m["vs_deslinde"],
                                  "semillas_que_igualan_optimo": sum(1 for k in ks if k["hueco_optimo"] is None),
                                  "semillas_mejor_que_deslinde": sum(1 for k in ks if k["vs_deslinde"] == "mejor"),
                                  "n": len(ks)}
        out[t] = {"k": ex["k"], "unidades": esp["unidades"], "atomos": esp["atomos"],
                  "deslinde": {"ganador": ex["ganador_competicion"], **{k: gan[k] for k in TER},
                               "hueco_optimo": primer_hueco(gan, opt)},
                  "exacto": {"estado": esp["estado"], **{k: opt[k] for k in TER},
                             "valido_nucleo": esp["mejor_modelo"]["valido_nucleo"], "t_s": ex["t_total_s"],
                             "memoria_mb": ex["memoria_max_mb"]},
                  "gerrychain_puro": {"cortes": mejores, "cpu_total_s": round(sum(f["cpu_s"] or 0 for f in filas), 1),
                                      "semillas": filas}}
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for t, r in out.items():
        print(t, "K", r["k"], "Deslinde", clave(r["deslinde"])[:3], "óptimo", clave(r["exacto"])[:3])
        for c, m in r["gerrychain_puro"]["cortes"].items():
            print("   GC", c, clave(m["mejor"])[:4], m["vs_deslinde"], "=ópt", m["semillas_que_igualan_optimo"], "/",
                  m["n"], ">Desl", m["semillas_mejor_que_deslinde"])
        print("   CPU GC", r["gerrychain_puro"]["cpu_total_s"], "s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
