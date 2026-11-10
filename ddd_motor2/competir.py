#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — interfaz de la competición para la batería T-132
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Competición · paso 4
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa; no lanza nada en Actions)
CAMBIOS: fichero nuevo.
MOTIVO: T-163 / D-48: que la batería T-132 corra la competición en los 71 con una orden y lea el criterio de
  aceptación (71/71 válidos, ninguno peor que el canónico, tiempos) de un solo fichero.
ANTERIOR: ninguna (fichero nuevo)
USO (en local, con las entradas de la batería en <out>/entradas/<t> y el entorno GerryChain de producción):
    PYTHONHASHSEED=0 python -m ddd_motor2.competir --out bateria --cadenas 5 --todos
    python -m ddd_motor2.competir --out bateria aragon murcia
  Por territorio: <out>/competicion/<t>/COMPETICION.{json,md} (+ composición de cada candidato).
  Agregado: <out>/competicion/RESUMEN.json y RESUMEN.md: por territorio, ganador, estado, si mejora / empata / empeora
  al canónico, huella del resultado y tiempo; totales y veredicto de aceptación.
  Código de salida: 0 si se cumple la aceptación en los territorios pedidos; 1 si no.
API: competir_territorio(t, out, n_cadenas=5) -> dict (fila del resumen).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .competicion import Candidato, competir_publico
from .generadores import Canonico, GerryChain, entrada_bateria
from .informe import escribir


def comparar(ganador: Candidato, canonico: Candidato) -> str:
    a, b = ganador.clave()[:5], canonico.clave()[:5]
    return "mejora" if a < b else ("empata" if a == b else "empeora")


def competir_territorio(t: str, out: Path, n_cadenas: int = 5) -> dict:
    out = Path(out)
    destino = out / "competicion" / t
    try:
        entrada = entrada_bateria(t, out)
        r = competir_publico(entrada, Canonico(), GerryChain(), destino, n_cadenas=n_cadenas)
    except Exception as exc:  # sin entradas, sin ancla en el contrato…: el territorio queda en el resumen
        return {"territorio": t, "estado": "ERROR", "detalle": f"{type(exc).__name__}: {exc}"}
    escribir(r, destino)
    validos = [c for c in r.candidatos if c.estado == "VALIDO"]
    return {"territorio": t, "estado": r.ganador.estado, "ganador": r.ganador.id,
            "frente_al_canonico": comparar(r.ganador, r.canonico), "canonico": r.canonico.estado,
            "candidatos_validos": len(validos), "candidatos": len(r.candidatos),
            "desvio_max": None if r.ganador.desvio_max is None else float(r.ganador.desvio_max),
            "desvio_max_canonico": None if r.canonico.desvio_max is None else float(r.canonico.desvio_max),
            "fuera_tolerancia": r.ganador.fuera_tolerancia, "huella_resultado": r.huella(),
            "tiempo_s": round(r.tiempo_total_s, 1)}


def resumen(filas: list[dict]) -> dict:
    n = len(filas)
    validos = sum(1 for f in filas if f.get("estado") == "VALIDO")
    cuenta = {k: sum(1 for f in filas if f.get("frente_al_canonico") == k) for k in ("mejora", "empata", "empeora")}
    tiempos = sorted(f["tiempo_s"] for f in filas if "tiempo_s" in f)
    return {"territorios": n, "validos": validos, **cuenta,
            "errores": [f["territorio"] for f in filas if f.get("estado") != "VALIDO"],
            "tiempo_total_s": round(sum(tiempos), 1),
            "tiempo_mediana_s": tiempos[len(tiempos) // 2] if tiempos else None,
            "tiempo_max_s": tiempos[-1] if tiempos else None,
            "aceptacion": n > 0 and validos == n and cuenta["empeora"] == 0}


def escribir_resumen(filas: list[dict], carpeta: Path) -> dict:
    carpeta.mkdir(parents=True, exist_ok=True)
    tot = resumen(filas)
    (carpeta / "RESUMEN.json").write_text(json.dumps({"totales": tot, "territorios": filas}, indent=2,
                                                     ensure_ascii=False) + "\n", encoding="utf-8")
    lin = ["# Competición canónico + GerryChain · resumen", "",
           f"- Válidos: {tot['validos']}/{tot['territorios']}; frente al canónico: mejora {tot['mejora']}, empata "
           f"{tot['empata']}, empeora {tot['empeora']}.",
           f"- Aceptación (todos válidos y ninguno peor): **{'sí' if tot['aceptacion'] else 'no'}**.",
           f"- Tiempo: total {tot['tiempo_total_s']} s, mediana {tot['tiempo_mediana_s']} s, máximo {tot['tiempo_max_s']} s.",
           "", "| Territorio | Ganador | Estado | Frente al canónico | Desvío máx. (canónico) | Válidos | Tiempo (s) |",
           "|---|---|---|---|---|---|---|"]
    for f in filas:
        if f.get("estado") == "ERROR":
            lin.append(f"| {f['territorio']} | — | ERROR | — | — | — | — |")
            continue
        dm = "—" if f["desvio_max"] is None else f"{f['desvio_max']:.4f}"
        dc = "—" if f["desvio_max_canonico"] is None else f"{f['desvio_max_canonico']:.4f}"
        lin.append(f"| {f['territorio']} | {f['ganador']} | {f['estado']} | {f['frente_al_canonico']} | {dm} ({dc}) | "
                   f"{f['candidatos_validos']}/{f['candidatos']} | {f['tiempo_s']} |")
    (carpeta / "RESUMEN.md").write_text("\n".join(lin) + "\n", encoding="utf-8")
    return tot


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("USO")[0])
    ap.add_argument("--out", default="bateria", help="carpeta de la batería (con entradas/<t>)")
    ap.add_argument("--cadenas", type=int, default=5)
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("territorios", nargs="*")
    a = ap.parse_args(argv)
    if a.todos:
        from .generadores import _bateria
        ts = _bateria().territorios()
    else:
        ts = a.territorios
    if not ts:
        ap.error("indica territorios o --todos")
    out = Path(a.out)
    filas = []
    for t in ts:
        f = competir_territorio(t, out, a.cadenas)
        filas.append(f)
        print(json.dumps(f, ensure_ascii=False), flush=True)
    tot = escribir_resumen(filas, out / "competicion")
    print(json.dumps(tot, ensure_ascii=False))
    return 0 if tot["aceptacion"] else 1


if __name__ == "__main__":
    sys.exit(main())
