#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — regla de calidad vigente (una sola definición para competición, enumeración y certificador)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Calidad lexicográfica compartida
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo (sale de competicion.juzgar 1.1.0, sin cambiar el orden).
MOTIVO: T-175: la enumeración exacta y el certificador eligen el plan con la misma regla que la competición.
ANTERIOR: ninguna (fichero nuevo)
REGLA (lexicográfica, menor es mejor): violaciones duras → distritos fuera de tolerancia → desvío máximo |p−obj|/obj
  → error cuadrático medio de (p−obj)/obj → huella del plan (partición sin etiquetas). Fracciones exactas.
Solo stdlib.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from typing import Mapping

from .reglas import Informe, Problema, Reglas, evaluar

ORDEN = ("violaciones_duras", "fuera_tolerancia", "desvio_max", "ecm", "huella_plan")


def huella_plan(plan: Mapping[str, str]) -> str:
    """sha256 del plan como partición (conjuntos de unidades), sin depender de las etiquetas de distrito."""
    grupos: dict[str, list[str]] = {}
    for u, d in plan.items():
        grupos.setdefault(str(d), []).append(str(u))
    forma = sorted(sorted(us) for us in grupos.values())
    return hashlib.sha256(json.dumps(forma, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def metricas(problema: Problema, reglas: Reglas, plan: Mapping[str, str], informe: Informe | None = None,
             unidad_de: Mapping[str, str] | None = None) -> dict:
    """Métricas de calidad del plan (exactas) y su clave de orden. `unidad_de` (sección -> unidad M04): la huella se
    calcula sobre las unidades, como en la competición, aunque el problema sea por secciones (certificador)."""
    inf = informe if informe is not None else evaluar(problema, reglas, plan)
    objetivo = reglas.limites(problema.poblacion_total)[0]
    pob: dict[str, int] = {}
    for u, d in plan.items():
        pob[d] = pob.get(d, 0) + problema.por_id[u].poblacion
    desv = [Fraction(p) / objetivo - 1 for p in pob.values()] if objetivo and pob else [Fraction(0)]
    m = {"valido": inf.valido, "violaciones_duras": len(inf.violaciones),
         "fuera_tolerancia": len(inf.metricas["fuera_tolerancia"]),
         "desvio_max": max(abs(x) for x in desv),
         "ecm": sum((x * x for x in desv), Fraction(0)) / len(desv),
         "huella_plan": huella_plan({unidad_de.get(s, s): d for s, d in plan.items()} if unidad_de else plan)}
    m["clave"] = tuple(m[c] for c in ORDEN)
    return m


def legible(m: Mapping) -> dict:
    """Las métricas en JSON (fracciones como decimales y como texto exacto)."""
    out = {k: v for k, v in m.items() if k != "clave"}
    for c in ("desvio_max", "ecm"):
        out[c] = float(m[c])
        out[c + "_exacto"] = str(m[c])
    return out
