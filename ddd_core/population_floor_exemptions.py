#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Componente: exenciones de suelo poblacional por municipio
VERSIÓN: 1.0.1
FECHA: 2026-11-01
FUNCIÓN: leer validation.population_floor_exempt_municipalities y decidir si un distrito
queda exento del suelo porque contiene un municipio declarado (código INE de 5 cifras).
MOTIVO: Beniel (Murcia, 11.462 hab.) solo linda con la ciudad de Murcia; la exención por
partición (isla/provincia) quitaría el suelo a los 45 distritos de la comunidad.
CAMBIO 1.0.1 (T-13): en contratos con particiones físicas (islas) el campo municipal vale «35012:35-C01»;
se compara solo el código de municipio. Las Palmas fallaba la 04 con la exención de 35012 (run 41339428006).
ANTERIOR: legacy/ddd_core/population_floor_exemptions_v1.0.0_20261101.py
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
    """Acepta «35012» o «35012:35-C01» (DDD_MUNICIPALITY_PARTITION de los contratos con islas)."""
    return bool(exempt) and any(str(value).split(":", 1)[0] in exempt for value in municipalities)
