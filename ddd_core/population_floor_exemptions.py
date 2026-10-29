#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Componente: exenciones de suelo poblacional por municipio
VERSIÓN: 1.0.0
FECHA: 2026-10-29
FUNCIÓN: leer validation.population_floor_exempt_municipalities y decidir si un distrito
queda exento del suelo porque contiene un municipio declarado (código INE de 5 cifras).
MOTIVO: Beniel (Murcia, 11.462 hab.) solo linda con la ciudad de Murcia; la exención por
partición (isla/provincia) quitaría el suelo a los 45 distritos de la comunidad.
ANTERIOR: ninguna (componente nuevo).
"""
from __future__ import annotations


def exempt_municipalities(cfg) -> set[str]:
    values = ((cfg or {}).get("validation") or {}).get("population_floor_exempt_municipalities") or []
    return {str(value) for value in values}


def unit_municipality(unit_id) -> str | None:
    """Unidades M04 '{prov}:{mun}:M|R|Un' → código de municipio; None si no sigue el formato."""
    parts = str(unit_id).split(":")
    return parts[1] if len(parts) >= 3 else None


def units_touch_exempt(unit_ids, exempt: set[str]) -> bool:
    return bool(exempt) and any(unit_municipality(unit) in exempt for unit in unit_ids)


def municipalities_touch_exempt(municipalities, exempt: set[str]) -> bool:
    return bool(exempt) and any(str(value) in exempt for value in municipalities)
