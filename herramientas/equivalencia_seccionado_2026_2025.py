#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Equivalencia de las secciones del seccionado INE 2026 con el seccionado INE 2025 de los mapas del Congreso (T-225).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-11 · ESTADO: candidato (preparación; ningún consumidor la carga todavía)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-80 (propietario, vía Planificador): los mapas 2025/2025 del Congreso son los de la legislatura de la elección
  general del 29-11-2026; sus resultados llegarán por sección electoral 2026 y habrá que llevarlos a las secciones 2025.
  El ZIP por mesa de Interior sale tras la jornada; el seccionado INE a 1-1-2026 es la base de esas secciones y ya está
  publicado, así que la tabla se prepara ahora y se rehará (o completará, como T-101) con el ZIP real.
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: por provincia, las secciones de 2026 cuyo CUSEC no existe en 2025 se cruzan por geometría con las de 2025
  (herramientas/equivalencia_seccionados.equivalencia: 1:1 al 95 %, astillas < 1 %, peso de población del padrón
  65034 a 1-1-2025, D-13). Tipos: 1:1 (misma geometría), contenida (cae entera en una sección 2025: exacta) y partida
  (varias secciones 2025). La pérdida posible se mide en población 2025: la de las secciones 2025 que tocan las
  partidas, proporcional al área compartida (cota superior: solo se pierde si la partida cruza distritos). Escribe:
    configuracion/equivalencia_seccionado_ine_2026_a_2025.csv  seccion_2026, seccion_2025, tipo, peso_area, peso_poblacion
    configuracion/equivalencia_seccionado_ine_2026_a_2025.json fuentes con sha256, sha256 del CSV y, por provincia,
                                                              secciones nuevas, 1:1, contenidas, partidas y población afectada.
Uso: python herramientas/equivalencia_seccionado_2026_2025.py --s2026 SECC2026.zip --s2025 SECC2025.zip --padron 65034.csv.zip
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import equivalencia_seccionados as es  # noqa: E402

SALIDA = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2025.csv"
SCHEMA = "ddd.equivalencia-seccionado-2026-2025/1.0"


def medir(nuevas: dict, s2025: dict, pob: dict[str, int]) -> tuple[list[list], dict]:
    """Filas del CSV y resumen de una provincia (nuevas = {cusec_2026: geometría} ausentes de 2025)."""
    eq = es.equivalencia(nuevas, s2025, pob) if nuevas else {}
    filas, afectada, tipos = [], 0.0, {"1:1": 0, "contenida": 0, "partida": 0, "sin_vigente": 0}
    for s, e in sorted(eq.items()):
        # contenida: la sección 2026 cae entera (sin contar astillas < 1 %) en una sola sección 2025; es exacta.
        tipo = "contenida" if e["tipo"] == "reparto" and len(e["area"]) == 1 else ("partida" if e["tipo"] == "reparto" else e["tipo"])
        tipos[tipo] += 1
        for v in sorted(e["area"]):
            filas.append([s, v, tipo, f"{e['area'][v]:.6f}", f"{e['poblacion'][v]:.6f}"])
            if tipo == "partida":
                afectada += nuevas[s].intersection(s2025[v]).area / s2025[v].area * pob.get(v, 0)
    total = sum(pob.get(v, 0) for v in s2025)
    return filas, {"secciones_2026_sin_2025": len(eq), **{f"tipo_{k}": n for k, n in tipos.items()},
                   "poblacion_2025": total, "poblacion_afectada_partidas": round(afectada),
                   "pct_poblacion_afectada": round(100 * afectada / total, 4) if total else 0.0}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--s2026", type=Path, required=True)
    ap.add_argument("--s2025", type=Path, required=True)
    ap.add_argument("--padron", type=Path, required=True, help="INE 65034 (periodo 2025)")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args(argv)
    s26, s25, pob = es.leer_seccionado(a.s2026), es.leer_seccionado(a.s2025), es.leer_padron(a.padron, "2025")
    filas, provincias = [], {}
    for cpro in sorted(set(s26) | set(s25)):
        nuevas = {k: g for k, g in s26.get(cpro, {}).items() if k not in s25.get(cpro, {})}
        f, r = medir(nuevas, s25.get(cpro, {}), {k: v for k, v in pob.items() if k[:2] == cpro})
        r["secciones_2025_sin_2026"] = len(set(s25.get(cpro, {})) - set(s26.get(cpro, {})))
        filas += f
        provincias[cpro] = r
        print(cpro, r["secciones_2026_sin_2025"], r["pct_poblacion_afectada"], flush=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["seccion_2026", "seccion_2025", "tipo", "peso_area", "peso_poblacion"])
    w.writerows(filas)
    cuerpo = buf.getvalue().encode("utf-8")
    salida = a.salida.resolve()
    salida.write_bytes(cuerpo)
    tot = sum(p["poblacion_2025"] for p in provincias.values())
    afe = sum(p["poblacion_afectada_partidas"] for p in provincias.values())
    meta = {"schema": SCHEMA, "decision": "D-65 y D-80; peso D-13; preparación (sin consumidor hasta el ZIP de Interior)",
            "csv": {"ruta": salida.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(cuerpo).hexdigest()},
            "fuentes": {"seccionado_2026": {"url": f"{es.URL_INE}{a.s2026.name}", "sha256": es.sha256(a.s2026)},
                        "seccionado_2025": {"url": f"{es.URL_INE}{a.s2025.name}", "sha256": es.sha256(a.s2025)},
                        "padron_65034": {"url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv",
                                         "periodo": "2025", "sha256": es.sha256(a.padron)}},
            "umbral_1a1": es.UMBRAL, "astilla": es.ASTILLA,
            "nacional": {"poblacion_2025": tot, "poblacion_afectada_partidas": afe,
                         "pct_poblacion_afectada": round(100 * afe / tot, 4) if tot else 0.0},
            "provincias": provincias}
    salida.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
