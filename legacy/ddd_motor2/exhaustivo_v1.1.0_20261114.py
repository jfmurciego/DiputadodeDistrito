#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — enumeración exacta para territorios pequeños, con elección por la regla de calidad
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Enumeración exacta · sin intento imposible
FECHA: 2026-11-11
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: 1.1.0 — enumerar_exacto(..., plan=None): con un plan de partida (el canónico), antes de enumerar calcula
  reglas.cota.cota_nodos; si la cota inferior de nodos supera el presupuesto, la enumeración no podría completarse
  y no se lanza: metodo=cadena, completo=False, intentada=False, motivo «cota…», cota_nodos (sin nodos, validos ni
  huella). Si la cota no lo demuestra (o no hay plan, o el plan no es válido), todo igual que 1.0.0.
  1.0.0 — fichero nuevo.
MOTIVO: T-175: donde el espacio de planes cabe, el motor nuevo enumera TODOS los planes válidos y elige el mejor por
  la regla de calidad vigente (calidad.py), en vez de muestrear; el certificador usa la misma regla.
MOTIVO 1.1.0: T-261 (D-89): T-254 midió que el exhaustivo agota los 200 000 nodos sin aportar candidato y se lleva
  el 60-87 % de la competición. Un intento que no puede acabar no cambia ningún mapa: se omite.
ANTERIOR: legacy/ddd_motor2/exhaustivo_v1.0.0_20261110.py
QUÉ HACE:
  enumerar_exacto(problema, reglas, presupuesto=None, plan=None) -> dict: decide con reglas.elegir_metodo (Criterio.metodo:
    «presupuesto» intenta la enumeración con Criterio.presupuesto_nodos; «tamano» solo si K <= tamano_max_k o
    unidades <= tamano_max_unidades, y también con presupuesto) y, si enumera, recorre todos los planes válidos con
    reglas.enumerar y guarda el mejor por calidad. Campos: metodo, motivo, completo, nodos, presupuesto, validos,
    huella (del conjunto de planes), mejor (plan), mejor_metricas, segundo_clave, empatados, tiempo_s.
    Solo «completo» certifica el óptimo; si no, la cadena sigue (los planes vistos son una cota inferior del recuento).
  CLI: python -m ddd_motor2.exhaustivo --params --composicion <m06.csv> --grafo <m03.json> [--presupuesto N].
  escribir_composicion(base_csv, plan, salida, cfg): composición M06 con el plan (unidad -> distrito) sobre las filas
    de otra composición del mismo territorio (mismas secciones y unidades); distritos 0..K-1 por la menor sección
    (como M05/M06).
  huella_composicion(csv, cfg): huella de la partición en secciones (comparable con la del certificador, que trabaja
    por secciones; la numeración de unidades cambia entre M04 y M06).
Solo stdlib.
"""
from __future__ import annotations

import csv
import time
from pathlib import Path
from typing import Any, Mapping

from .adaptadores import columnas_de_contrato
from .calidad import huella_plan, legible, metricas
from .reglas import Problema, Reglas, elegir_metodo, enumerar
from .reglas.cota import cota_nodos


def enumerar_exacto(problema: Problema, reglas: Reglas, presupuesto: int | None = None,
                    plan: Mapping[str, str] | None = None) -> dict:
    t0 = time.monotonic()
    c = reglas.criterio
    presupuesto = int(presupuesto or c.presupuesto_nodos)
    base = {"k": reglas.k, "unidades": len(problema.unidades), "presupuesto": presupuesto,
            "criterio_metodo": c.metodo, "huella_reglas": reglas.huella()}
    if c.metodo == "tamano":
        d = elegir_metodo(problema, reglas)
        if d.metodo != "enumeracion":
            return {**base, "metodo": "cadena", "motivo": d.motivo, "completo": False, "intentada": False,
                    "tiempo_s": round(time.monotonic() - t0, 3)}
    elif c.metodo == "diagnostico":
        return {**base, "metodo": "cadena", "motivo": "criterio diagnóstico: decide la cadena", "completo": False,
                "intentada": False, "tiempo_s": 0.0}
    if plan is not None:
        cota = cota_nodos(problema, reglas, plan, presupuesto)
        if cota["supera"]:
            return {**base, "metodo": "cadena", "intentada": False, "completo": False,
                    "motivo": f"cota: el árbol de enumeración tiene al menos {cota['cota']} nodos > presupuesto "
                              f"{presupuesto}; no se intenta",
                    "cota_nodos": {k: cota[k] for k in ("cota", "planes_validos", "evaluaciones", "tiempo_s")},
                    "tiempo_s": round(time.monotonic() - t0, 3)}
    r = enumerar(problema, reglas, presupuesto, max_planes=0,
                 clave=lambda plan: metricas(problema, reglas, plan)["clave"])
    if c.metodo == "presupuesto":
        d = elegir_metodo(problema, reglas, recuento={**r, "nodos": r["nodos"]})
        metodo, motivo = d.metodo, d.motivo
    else:
        metodo = "enumeracion" if r["completo"] else "cadena"
        motivo = f"tamaño; enumeración {'completa' if r['completo'] else 'incompleta'} en {r['nodos']} nodos"
    out = {**base, "metodo": metodo, "motivo": motivo, "intentada": True, "completo": r["completo"],
           "nodos": r["nodos"], "validos": r["validos"], "huella": r["huella"], "mejor": r["mejor"],
           "mejor_metricas": legible(metricas(problema, reglas, r["mejor"])) if r["mejor"] else None,
           "segundo_clave": None if r["segundo_clave"] is None else
           {"violaciones_duras": r["segundo_clave"][0], "fuera_tolerancia": r["segundo_clave"][1],
            "desvio_max": float(r["segundo_clave"][2]), "ecm": float(r["segundo_clave"][3])},
           "empatados": r["empatados"], "tiempo_s": round(time.monotonic() - t0, 3)}
    return out


def escribir_composicion(base_csv: str | Path, plan: Mapping[str, str], salida: str | Path,
                         cfg: Mapping[str, Any], columnas: Mapping[str, str] | None = None) -> Path:
    col = {**columnas_de_contrato(cfg), **(columnas or {})}
    with open(base_csv, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        campos, filas = list(rd.fieldnames or []), list(rd)
    for c in (col["seccion"], col["distrito"]):
        if c not in campos:
            raise ValueError(f"{base_csv}: falta la columna {c}")
    con_unidad = col["unidad"] in campos

    def unidad(f):
        return str(f[col["unidad"]]).strip() if con_unidad else str(f[col["seccion"]]).strip()

    faltan = sorted({unidad(f) for f in filas} - set(plan))
    if faltan:
        raise ValueError(f"el plan no asigna {len(faltan)} unidades (p. ej. {faltan[0]})")
    menor: dict[str, str] = {}
    for f in filas:
        d, s = str(plan[unidad(f)]), str(f[col["seccion"]]).strip()
        menor[d] = min(menor.get(d, s), s)
    etiqueta = {d: str(i) for i, d in enumerate(sorted(menor, key=menor.get))}
    for f in filas:
        f[col["distrito"]] = etiqueta[str(plan[unidad(f)])]
    salida = Path(salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with open(salida, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    return salida


def huella_composicion(ruta: str | Path, cfg: Mapping[str, Any], columnas: Mapping[str, str] | None = None) -> str:
    col = {**columnas_de_contrato(cfg), **(columnas or {})}
    with open(ruta, encoding="utf-8", newline="") as fh:
        return huella_plan({str(f[col["seccion"]]).strip(): str(f[col["distrito"]]).strip() for f in csv.DictReader(fh)})


def main(argv=None) -> int:
    """python -m ddd_motor2.exhaustivo --params <contrato> --composicion <m06.csv> --grafo <m03.json>
    [--atributos <m06_secciones.geojson.zip>] [--presupuesto N] [--salida <csv del mejor>]
    --salida solo se escribe si la enumeración es completa (si no, aviso_salida)."""
    import argparse
    import json
    import sys
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from ddd_core.config import load_params_yaml
    from .adaptadores import problema_y_plan
    from .reglas import Criterio
    ap = argparse.ArgumentParser(prog="python -m ddd_motor2.exhaustivo")
    ap.add_argument("--params", required=True)
    ap.add_argument("--composicion", required=True)
    ap.add_argument("--grafo", required=True)
    ap.add_argument("--atributos")
    ap.add_argument("--presupuesto", type=int)
    ap.add_argument("--salida")
    a = ap.parse_args(argv)
    cfg = load_params_yaml(a.params)
    problema, plan, avisos = problema_y_plan(a.composicion, a.grafo, cfg, atributos_secciones=a.atributos)
    reglas = Reglas.desde_contrato(cfg, Criterio())
    res = enumerar_exacto(problema, reglas, a.presupuesto, plan=plan)
    mejor = res.pop("mejor", None)
    res["avisos"] = avisos
    res["entrada"] = legible(metricas(problema, reglas, plan))
    res["mejor_es_la_entrada"] = bool(mejor) and huella_plan(mejor) == res["entrada"]["huella_plan"]
    if a.salida and not res.get("completo"):
        res["aviso_salida"] = "enumeración incompleta: no se escribe --salida (el mejor visto no es el óptimo)"
    elif mejor and a.salida:
        res["mejor_huella_secciones"] = huella_composicion(escribir_composicion(a.composicion, mejor, a.salida, cfg), cfg)
    print(json.dumps(res, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
