#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Equivalencia de las secciones del seccionado INE 2026 con el seccionado INE 2023 de los mapas vigentes (T-291).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-65 (propietario): la noche electoral del 29-11-2026 va sobre los mapas vigentes (padrón y seccionado 2023)
  y lleva los resultados 2026 a ellos por equivalencia de secciones. La tabla 2026→2025 (T-225) es para la
  legislatura nueva. El ZIP por mesa de Interior sale tras la jornada; el seccionado INE a 1-1-2026 es la base de sus
  secciones, así que la tabla se prepara ahora y se completará con el ZIP real (como T-101).
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: por provincia, las secciones de 2026 cuyo CUSEC no existe en 2023, o que lo conservan con el límite
  cambiado (diferencia simétrica > 5 % del área), se cruzan por geometría con las de 2023
  (herramientas/equivalencia_seccionados.equivalencia: 1:1 al 95 %, astillas < 1 %, peso de población del padrón
  65034 a 1-1-2023, el de los mapas vigentes, D-13). Tipos: 1:1, contenida (cae entera en una sección 2023: exacta),
  partida (varias secciones 2023: M07 reparte por peso de población) y sin_vigente. Escribe:
    configuracion/equivalencia_seccionado_ine_2026_a_2023.csv  seccion_2026, seccion_2023, tipo, peso_area, peso_poblacion
    configuracion/equivalencia_seccionado_ine_2026_a_2023.json fuentes con sha256, sha256 del CSV y resumen por provincia.
Uso: python herramientas/equivalencia_seccionado_2026_2023.py --s2026 SECC2026.zip --s2023 SECC2023.zip --padron 65034.csv.zip
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

SALIDA = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2023.csv"
SCHEMA = "ddd.equivalencia-seccionado-2026-2023/1.0"
CABECERA = ["seccion_2026", "seccion_2023", "tipo", "peso_area", "peso_poblacion"]
TIPOS = ("1:1", "contenida", "partida", "sin_vigente")


def clasificar(e: dict) -> str:
    """contenida: la sección 2026 cae entera (sin astillas < 1 %) en una sola sección 2023; es exacta."""
    if e["tipo"] == "reparto":
        return "contenida" if len(e["area"]) == 1 else "partida"
    return e["tipo"]


def medir(nuevas: dict, vig: dict, pob: dict[str, int]) -> tuple[list[list], dict]:
    """Filas del CSV y resumen de una provincia (nuevas = {cusec_2026: geometría} sin equivalente directo en 2023)."""
    eq = es.equivalencia(nuevas, vig, pob) if nuevas else {}
    filas, afectada, tipos = [], 0.0, dict.fromkeys(TIPOS, 0)
    for s, e in sorted(eq.items()):
        tipo = clasificar(e)
        tipos[tipo] += 1
        if tipo == "sin_vigente":
            filas.append([s, "", tipo, "", ""])
            continue
        for v in sorted(e["area"]):
            filas.append([s, v, tipo, f"{e['area'][v]:.6f}", f"{e['poblacion'][v]:.6f}"])
            if tipo == "partida":
                afectada += nuevas[s].intersection(vig[v]).area / vig[v].area * pob.get(v, 0)
    total = sum(pob.get(v, 0) for v in vig)
    return filas, {"secciones_2026_sin_2023": len(eq), **{f"tipo_{k}": n for k, n in tipos.items()},
                   "poblacion_2023": total, "poblacion_afectada_partidas": round(afectada),
                   "pct_poblacion_afectada": round(100 * afectada / total, 4) if total else 0.0}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--s2026", type=Path, required=True)
    ap.add_argument("--s2023", type=Path, required=True)
    ap.add_argument("--padron", type=Path, required=True, help="INE 65034 (periodo 2023)")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args(argv)
    s26, s23, pob = es.leer_seccionado(a.s2026), es.leer_seccionado(a.s2023), es.leer_padron(a.padron, "2023")
    filas, provincias = [], {}
    for cpro in sorted(set(s26) | set(s23)):
        a26, a23 = s26.get(cpro, {}), s23.get(cpro, {})
        nuevas = {k: g for k, g in a26.items() if k not in a23}
        cambiadas = {k: g for k, g in a26.items()
                     if k in a23 and g.symmetric_difference(a23[k]).area > (1 - es.UMBRAL) * g.area}
        nuevas.update(cambiadas)
        f, r = medir(nuevas, a23, {k: v for k, v in pob.items() if k[:2] == cpro})
        r["secciones_2023_sin_2026"] = len(set(a23) - set(a26))
        r["secciones_mismo_cusec_limite_cambiado"] = len(cambiadas)
        filas += f
        provincias[cpro] = r
        print(cpro, r["secciones_2026_sin_2023"], r["pct_poblacion_afectada"], flush=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CABECERA)
    w.writerows(filas)
    cuerpo = buf.getvalue().encode("utf-8")
    salida = a.salida.resolve()
    salida.write_bytes(cuerpo)
    tot = sum(p["poblacion_2023"] for p in provincias.values())
    afe = sum(p["poblacion_afectada_partidas"] for p in provincias.values())
    meta = {"schema": SCHEMA, "decision": "D-65; peso D-13 (padrón 2023 de los mapas vigentes); consumidor M07 (T-291)",
            "csv": {"ruta": salida.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(cuerpo).hexdigest()},
            "fuentes": {"seccionado_2026": {"url": f"{es.URL_INE}{a.s2026.name}", "sha256": es.sha256(a.s2026)},
                        "seccionado_2023": {"url": f"{es.URL_INE}{a.s2023.name}", "sha256": es.sha256(a.s2023)},
                        "padron_65034": {"url": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv",
                                         "periodo": "2023", "sha256": es.sha256(a.padron)}},
            "umbral_1a1": es.UMBRAL, "astilla": es.ASTILLA,
            "nacional": {"poblacion_2023": tot, "poblacion_afectada_partidas": afe,
                         "pct_poblacion_afectada": round(100 * afe / tot, 4) if tot else 0.0},
            "provincias": provincias}
    salida.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
