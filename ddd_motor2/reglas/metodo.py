#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: núcleo de reglas del motor 2 — umbral entre cadena y enumeración exacta
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Núcleo único de reglas · F1
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-160: el umbral es parámetro (Criterio.metodo). Por defecto provisional (b): enumerar con presupuesto de
  nodos y, si no se completa, cadena; (c) diagnóstico statistical_quality (0,10/0,90) como comprobación posterior.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .modelo import Problema, Reglas


@dataclass(frozen=True)
class Decision:
    metodo: str  # "enumeracion" | "cadena"
    motivo: str
    revisar: bool = False  # la comprobación posterior (c) ve la cadena degenerada


def cadena_degenerada(diagnostico: Mapping, reglas: Reglas) -> bool:
    """Mismos umbrales que ddd_ensemble/statistical_quality.py (parametrizados en Criterio)."""
    c = reglas.criterio
    for clave in ("unique_state_ratio", "self_loop_rate"):
        if clave not in diagnostico:
            raise ValueError(f"diagnóstico sin {clave}")
    return (float(diagnostico["unique_state_ratio"]) < c.diagnostico_min_unicos
            or float(diagnostico["self_loop_rate"]) > c.diagnostico_max_bucles)


def elegir_metodo(problema: Problema, reglas: Reglas, *, recuento: Mapping | None = None,
                  diagnostico: Mapping | None = None) -> Decision:
    """`recuento`: resultado del intento de enumeración con presupuesto ({"completo": bool, "nodos": int});
    `diagnostico`: métricas de la cadena ({"unique_state_ratio", "self_loop_rate"})."""
    c = reglas.criterio
    n = len(problema.unidades)
    if c.metodo == "tamano":
        if reglas.k <= c.tamano_max_k or n <= c.tamano_max_unidades:
            return Decision("enumeracion", f"tamaño: K={reglas.k}, unidades={n}")
        return Decision("cadena", f"tamaño: K={reglas.k}, unidades={n}")
    if c.metodo == "diagnostico":
        if diagnostico is None:
            raise ValueError("Criterio.metodo=diagnostico exige el diagnóstico de la cadena")
        if cadena_degenerada(diagnostico, reglas):
            return Decision("enumeracion", "cadena degenerada")
        return Decision("cadena", "cadena sana")
    # "presupuesto"
    if recuento is None:
        raise ValueError("Criterio.metodo=presupuesto exige el recuento de la enumeración con presupuesto")
    if recuento.get("completo") and int(recuento.get("nodos", 0)) <= c.presupuesto_nodos:
        return Decision("enumeracion", f"enumeración completa en {recuento.get('nodos')} nodos")
    revisar = diagnostico is not None and cadena_degenerada(diagnostico, reglas)
    return Decision("cadena", f"enumeración incompleta en {c.presupuesto_nodos} nodos", revisar=revisar)
