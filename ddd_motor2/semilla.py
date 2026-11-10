#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — semilla pública de la competición
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Competición · semilla pública
FECHA: 2026-11-10
ESTADO: candidato (motor 2; producción no lo importa). Ancla PROPUESTA, a confirmar por el propietario.
CAMBIOS: fichero nuevo.
MOTIVO: T-163 / D-48: las N semillas de GerryChain no se eligen: se derivan de un dato oficial fijado de antemano, de
  modo que cualquiera puede rehacerlas y la misma entrada da el mismo mapa.
ANTERIOR: ninguna (fichero nuevo)
ANCLA (propuesta): el sha256 que el contrato declara para el padrón (rol «population», tabla INE 65034) y para el
  seccionado (rol «target_sectioning») en generation_state.source_inputs, más el identificador del territorio.
  Si falta alguna huella, falla (ErrorContrato): nunca se cae a una semilla fija.
DERIVACIÓN (esquema ddd-semilla-publica/1):
  semilla_i = int(sha256("ddd-semilla-publica/1|<sha padrón>|<sha seccionado>|<territorio>|<i>")[:16], 16)
              mod (2^31 − 2) + 1,   i = 1..N
  (entero en [1, 2^31 − 2]: válido para random, numpy y --seed-base de m05_gerrychain_strategy, que usa base + 1).
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from .reglas import ErrorContrato

ESQUEMA = "ddd-semilla-publica/1"
ROLES = ("population", "target_sectioning")
MODULO = 2**31 - 2


def ancla(cfg: Mapping[str, Any], roles: tuple[str, ...] = ROLES) -> dict[str, str]:
    """{rol: sha256} de las fuentes oficiales declaradas en el contrato."""
    out: dict[str, str] = {}
    for item in ((cfg or {}).get("generation_state") or {}).get("source_inputs") or []:
        if isinstance(item, Mapping) and item.get("role") in roles:
            sha = str(item.get("sha256") or "").strip().lower()
            if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
                raise ErrorContrato(f"huella no válida para el rol {item.get('role')}: {sha!r}")
            if out.get(item["role"], sha) != sha:
                raise ErrorContrato(f"dos huellas distintas para el rol {item['role']}")
            out[item["role"]] = sha
    faltan = [r for r in roles if r not in out]
    if faltan:
        raise ErrorContrato(f"el contrato no declara el sha256 de: {', '.join(faltan)} (generation_state.source_inputs)")
    return {r: out[r] for r in roles}


def semillas(cfg: Mapping[str, Any], territorio: str, n: int, roles: tuple[str, ...] = ROLES) -> list[int]:
    if n < 1:
        raise ValueError("n debe ser >= 1")
    if not str(territorio).strip():
        raise ValueError("territorio vacío")
    a = ancla(cfg, roles)
    base = "|".join([ESQUEMA, *(a[r] for r in roles), str(territorio).strip()])
    out = [int(hashlib.sha256(f"{base}|{i}".encode("utf-8")).hexdigest()[:16], 16) % MODULO + 1
           for i in range(1, n + 1)]
    if len(set(out)) != n:  # colisión (probabilidad despreciable): se dice, no se corrige en silencio
        raise ValueError(f"semillas repetidas en la derivación: {out}")
    return out


def descripcion(cfg: Mapping[str, Any], territorio: str, n: int, roles: tuple[str, ...] = ROLES) -> dict:
    """Lo que el informe publica para que cualquiera rehaga las semillas."""
    return {"esquema": ESQUEMA, "territorio": territorio, "ancla": ancla(cfg, roles), "n": n,
            "semillas": semillas(cfg, territorio, n, roles),
            "formula": "int(sha256('ddd-semilla-publica/1|<sha population>|<sha target_sectioning>|<territorio>|<i>')"
                       "[:16], 16) mod (2^31-2) + 1"}
