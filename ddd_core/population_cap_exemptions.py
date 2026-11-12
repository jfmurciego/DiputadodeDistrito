#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Componente: exenciones de techo poblacional por partición atómica de un solo distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-12
FUNCIÓN: leer y validar validation.population_cap_exempt_partitions y decidir el techo efectivo de un
distrito. Es la única regla común que leen M04, M05, M06, el validador de ejecución y motor2.
MOTIVO (T-235, D-83): con el padrón 2025, Lanzarote y La Graciosa (35-G01 de nac35, Las Palmas) forman una
unidad insular atómica con un solo distrito y 1,424 veces la media, sobre el techo 1,40. El distrito es la isla
entera: no hay partición alternativa. Se exime solo ese distrito; el techo general no cambia.
REGLAS: la exención solo vale para una partición con K=1 en validation.province_districts y con su decisión
gobernada en validation.population_cap_exempt_partition_decisions (decided_at, decided_by=propietario, decision,
reason, evidence). Cualquier otro uso es un error del contrato. Sin la clave, nada cambia.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import math
from typing import Any, Iterable, Mapping

CLAVE = "population_cap_exempt_partitions"
CLAVE_DECISIONES = "population_cap_exempt_partition_decisions"
CAMPOS_DECISION = ("decided_at", "decided_by", "decision", "reason", "evidence")


class CapExemptionError(ValueError):
    """Contrato con una exención de techo no admitida."""


def _norm(value: Any) -> str:
    return str(value).strip().zfill(2)


def cap_exempt_partitions(cfg: Mapping[str, Any] | None) -> frozenset[str]:
    """Particiones exentas del techo, validadas. Vacío si la clave no está o está vacía."""
    val = (cfg or {}).get("validation") or {}
    raw = val.get(CLAVE)
    if raw in (None, [], ()):
        return frozenset()
    if not isinstance(raw, (list, tuple)):
        raise CapExemptionError(f"validation.{CLAVE} debe ser una lista")
    exentas = [_norm(x) for x in raw]
    if len(set(exentas)) != len(exentas):
        raise CapExemptionError(f"validation.{CLAVE} repite particiones: {exentas}")
    cuotas = {_norm(k): v for k, v in (val.get("province_districts") or {}).items()}
    decisiones = {_norm(k): v for k, v in (val.get(CLAVE_DECISIONES) or {}).items()}
    for p in exentas:
        if p not in cuotas:
            raise CapExemptionError(f"exención de techo {p}: la partición no está en validation.province_districts")
        if int(cuotas[p]) != 1:
            raise CapExemptionError(
                f"exención de techo {p}: K={cuotas[p]}; solo vale para una partición atómica de un distrito (K=1)")
        d = decisiones.get(p)
        if not isinstance(d, Mapping):
            raise CapExemptionError(f"exención de techo {p}: falta su decisión en validation.{CLAVE_DECISIONES}")
        faltan = [c for c in CAMPOS_DECISION if not str(d.get(c) or "").strip()]
        if faltan:
            raise CapExemptionError(f"exención de techo {p}: la decisión no trae {faltan}")
        if str(d["decided_by"]).strip() != "propietario":
            raise CapExemptionError(f"exención de techo {p}: decided_by={d['decided_by']!r}; solo decide el propietario")
    sobrantes = sorted(set(decisiones) - set(exentas))
    if sobrantes:
        raise CapExemptionError(f"validation.{CLAVE_DECISIONES} trae decisiones sin exención: {sobrantes}")
    return frozenset(exentas)


def district_cap(cap: float, partitions: Iterable[Any], exempt: frozenset[str]) -> float:
    """Techo efectivo de un distrito: infinito solo si todas sus unidades son de una única partición exenta."""
    if not exempt:
        return cap
    partes = {_norm(p) for p in partitions}
    return math.inf if len(partes) == 1 and next(iter(partes)) in exempt else cap
