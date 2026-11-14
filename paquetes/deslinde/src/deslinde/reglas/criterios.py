#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — variantes de criterio (misma vara para la batería T-132)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Núcleo único de reglas · F1
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-160: que la batería diga cuántos de los 71 territorios cambian de veredicto con cada opción de criterio.
ANTERIOR: ninguna (fichero nuevo)
USO (batería):
    res = {t: comparar_criterios(problema_t, cfg_t, plan_t) for t in territorios}
    resumen_por_opcion(res)  # {"tolerancia=dura": 3, "provincia_defecto=no": 0, ...} frente al Criterio por defecto
"""
from __future__ import annotations

import itertools
from dataclasses import replace
from typing import Iterable, Mapping

from .evaluar import evaluar
from .modelo import OPCIONES, Criterio, ErrorContrato, ErrorDatos, Problema, Reglas

DECISIONES = ("tolerancia", "max_mixtos", "provincia_defecto", "exencion_particion")


def variantes_criterio(base: Criterio | None = None, decisiones: Iterable[str] = DECISIONES) -> list[Criterio]:
    """Producto cartesiano de las opciones de las decisiones dadas sobre `base` (36 con las cuatro)."""
    base = base or Criterio()
    decisiones = tuple(decisiones)
    return [replace(base, **dict(zip(decisiones, combo)))
            for combo in itertools.product(*(OPCIONES[d] for d in decisiones))]


def veredicto(problema: Problema, cfg: Mapping, asignacion: Mapping, criterio: Criterio) -> dict:
    """{"veredicto": PASS|FAIL|ERROR_CONTRATO|ERROR_DATOS, "codigos": [...], "detalle": str, "huella": str}."""
    try:
        reglas = Reglas.desde_contrato(cfg, criterio)
        inf = evaluar(problema, reglas, asignacion)
    except ErrorContrato as exc:
        return {"veredicto": "ERROR_CONTRATO", "codigos": [], "detalle": str(exc), "huella": ""}
    except ErrorDatos as exc:
        return {"veredicto": "ERROR_DATOS", "codigos": [], "detalle": str(exc), "huella": ""}
    return {"veredicto": "PASS" if inf.valido else "FAIL", "codigos": sorted(inf.codigos()), "detalle": "",
            "huella": inf.huella_reglas}


def comparar_criterios(problema: Problema, cfg: Mapping, asignacion: Mapping,
                       variantes: Iterable[Criterio] | None = None) -> list[dict]:
    """Veredicto del plan con cada variante: lista de {"criterio": {...}, **veredicto}."""
    out = []
    for c in (variantes if variantes is not None else variantes_criterio()):
        fila = {"criterio": {d: getattr(c, d) for d in DECISIONES}}
        fila.update(veredicto(problema, cfg, asignacion, c))
        out.append(fila)
    return out


def resumen_por_opcion(resultados: Mapping[str, list[dict]], base: Criterio | None = None) -> dict[str, int]:
    """Por cada opción distinta de la base («decision=opcion»), cuántos territorios cambian de veredicto frente a
    la base al cambiar SOLO esa decisión. Es la evidencia para el propietario."""
    base = base or Criterio()
    ref = {d: getattr(base, d) for d in DECISIONES}
    cuenta: dict[str, int] = {f"{d}={o}": 0 for d in DECISIONES for o in OPCIONES[d] if o != ref[d]}
    for filas in resultados.values():
        por_crit = {tuple(sorted(f["criterio"].items())): f["veredicto"] for f in filas}
        v_base = por_crit.get(tuple(sorted(ref.items())))
        if v_base is None:
            continue
        for d in DECISIONES:
            for o in OPCIONES[d]:
                if o == ref[d]:
                    continue
                clave = tuple(sorted({**ref, d: o}.items()))
                if clave in por_crit and por_crit[clave] != v_base:
                    cuenta[f"{d}={o}"] += 1
    return cuenta
