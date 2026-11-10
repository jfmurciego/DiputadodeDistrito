#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — interfaz de la competición para la batería T-132
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Competición · interfaz
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa; no lanza nada en Actions)
CAMBIOS: 1.0.1 — --reanudar solo reutiliza un COMPETICION.json de la misma competición (versión del
  orquestador, huella de reglas, ancla y número de cadenas); un fallo al escribir el informe deja el territorio en ERROR
  sin abortar la tanda;
  1.0.0 — fichero nuevo.
MOTIVO: T-163 / D-48: que la batería T-132 corra la competición en los 71 con una orden y lea el criterio de
  aceptación (71/71 válidos, ninguno peor que el canónico, tiempos) de un solo fichero.
ANTERIOR: legacy/ddd_motor2/competir_v1.0.0_20261110.py
USO (en local, con las entradas de la batería en <out>/entradas/<t> y el entorno GerryChain de producción):
    PYTHONHASHSEED=0 python -m ddd_motor2.competir --out bateria --cadenas 5 --todos
    python -m ddd_motor2.competir --out bateria aragon murcia
    python -m ddd_motor2.competir --out bateria --todos --reanudar   # salta los COMPETICION.json ya escritos
  Por territorio: <out>/competicion/<t>/COMPETICION.{json,md} (+ composición de cada candidato).
  Agregado: <out>/competicion/RESUMEN.json y RESUMEN.md: por territorio, ganador, estado, si mejora / empata / empeora
  al canónico, huella del resultado y tiempo; totales y veredicto de aceptación.
  El resumen se reescribe tras cada territorio. Código de salida: 0 si se cumple la aceptación en los territorios
  pedidos; 1 si no.
API: competir_territorio(t, out, n_cadenas=5) -> dict (fila del resumen).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dataclasses import asdict

from .competicion import VERSION, Candidato, competir_publico
from .generadores import Canonico, GerryChain, entrada_bateria
from .informe import escribir
from .reglas import Criterio, Reglas
from .semilla import ancla


def comparar(ganador: Candidato, canonico: Candidato) -> str:
    a, b = ganador.clave()[:5], canonico.clave()[:5]
    return "mejora" if a < b else ("empata" if a == b else "empeora")


def competir_territorio(t: str, out: Path, n_cadenas: int = 5, *, generadores=None, entrada=None) -> dict:
    """`generadores` (canónico, cadena) y `entrada` se pueden inyectar (pruebas); por defecto, los de la batería."""
    out = Path(out)
    destino = out / "competicion" / t
    try:
        entrada = entrada or entrada_bateria(t, out)
        can, cad = generadores or (Canonico(), GerryChain())
        r = competir_publico(entrada, can, cad, destino, n_cadenas=n_cadenas)
        escribir(r, destino)
    except Exception as exc:  # sin entradas, sin ancla, fallo al escribir…: el territorio queda en el resumen
        return {"territorio": t, "estado": "ERROR", "detalle": f"{type(exc).__name__}: {exc}"}
    validos = [c for c in r.candidatos if c.estado == "VALIDO"]
    return {"territorio": t, "estado": r.ganador.estado, "ganador": r.ganador.id, "valido": r.valido,
            "frente_al_canonico": comparar(r.ganador, r.canonico), "canonico": r.canonico.estado,
            "candidatos_validos": len(validos), "candidatos": len(r.candidatos),
            "desvio_max": None if r.ganador.desvio_max is None else float(r.ganador.desvio_max),
            "desvio_max_canonico": None if r.canonico.desvio_max is None else float(r.canonico.desvio_max),
            "fuera_tolerancia": r.ganador.fuera_tolerancia, "huella_resultado": r.huella(),
            "tiempo_s": round(r.tiempo_total_s, 1)}


def fila_guardada(t: str, out: Path, n_cadenas: int, cfg=None) -> dict | None:
    """Fila del resumen desde un COMPETICION.json ya escrito (reanudación). None —y el territorio se recalcula— si no
    hay, no se puede leer o no es de esta misma competición: versión del orquestador, huella de reglas, ancla de la
    semilla y número de cadenas."""
    f = Path(out) / "competicion" / t / "COMPETICION.json"
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
        cands = {c["id"]: c for c in d["candidatos"]}
        g, c = cands[d["ganador"]], cands[d["canonico"]]
        if cfg is None:
            from .generadores import _bateria
            cfg = _bateria()._cfg(t)
        sp = d.get("semilla_publica") or {}
        if (d.get("version_orquestador") != VERSION or sp.get("n") != n_cadenas or sp.get("ancla") != ancla(cfg)
                or d.get("huella_reglas") != Reglas.desde_contrato(cfg, Criterio(**d["criterio"])).huella()
                or d.get("criterio") != asdict(Criterio())):
            return None
    except (OSError, ValueError, KeyError, TypeError):  # ErrorContrato es ValueError
        return None
    clave = lambda x: (x["estado"] not in ("VALIDO", "INVALIDO"), x["violaciones_duras"] or 0,  # noqa: E731
                       x["fuera_tolerancia"] or 0, x["desvio_max"] or 0, x["ecm"] or 0)
    frente = "empata" if clave(g) == clave(c) else ("mejora" if clave(g) < clave(c) else "empeora")
    if c["estado"] not in ("VALIDO", "INVALIDO") and g["estado"] in ("VALIDO", "INVALIDO"):
        frente = "mejora"
    return {"territorio": t, "estado": g["estado"], "ganador": g["id"], "valido": d.get("valido"),
            "frente_al_canonico": frente, "canonico": c["estado"],
            "candidatos_validos": sum(1 for x in d["candidatos"] if x["estado"] == "VALIDO"),
            "candidatos": len(d["candidatos"]), "desvio_max": g["desvio_max"], "desvio_max_canonico": c["desvio_max"],
            "fuera_tolerancia": g["fuera_tolerancia"], "huella_resultado": d.get("huella_resultado"),
            "tiempo_s": d.get("tiempo_total_s"), "reanudado": True}


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
    ap.add_argument("--reanudar", action="store_true",
                    help="salta los territorios con COMPETICION.json ya escrito (los lee para el resumen)")
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
        f = fila_guardada(t, out, a.cadenas) if a.reanudar else None
        f = f or competir_territorio(t, out, a.cadenas)
        filas.append(f)
        print(json.dumps(f, ensure_ascii=False), flush=True)
        tot = escribir_resumen(filas, out / "competicion")  # incremental: un corte deja lo hecho
    print(json.dumps(tot, ensure_ascii=False))
    return 0 if tot["aceptacion"] else 1


if __name__ == "__main__":
    sys.exit(main())
