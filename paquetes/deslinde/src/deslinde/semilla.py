#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — semilla pública de la competición
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · semilla sin tabla maestra del repo
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.2.0 — (T-257, D-88) movido de ddd_motor2/ al paquete Deslinde. El código oficial lo da el resolutor
  registrado (deslinde.territorio): por defecto el territorio es su código (NAC22…); el repo registra el suyo
  (ddd_motor2/semilla.py: ddd_core.territorio_ids sobre la tabla maestra). Misma fórmula y mismas semillas.
  1.1.0 — (T-265, D-90) el territorio de la semilla es el CÓDIGO OFICIAL de la tabla maestra; esquema
  `ddd-semilla-publica/2`. 1.0.1 — ancla aprobada (D-50). 1.0.0 — fichero nuevo.
MOTIVO: T-163 / D-48: las N semillas de GerryChain no se eligen: se derivan de un dato oficial fijado de antemano, de
  modo que cualquiera puede rehacerlas y la misma entrada da el mismo mapa. T-265 / D-90: el identificador del
  territorio también es un dato oficial (código INE), no un nombre de carpeta.
ANTERIOR: legacy/ddd_motor2/semilla_v1.1.0_20261114.py
ANCLA (D-50): el sha256 que el contrato declara para el padrón (rol «population», tabla INE 65034) y para el
  seccionado (rol «target_sectioning») en generation_state.source_inputs, más el código oficial del territorio.
  Si falta alguna huella o el territorio no está en la tabla maestra, falla (ErrorContrato): nunca semilla fija.
DERIVACIÓN (esquema ddd-semilla-publica/2):
  código   = codigo_semilla(<territorio>)   (tabla maestra; AUTnn = CODAUTO, NACnn = CPRO del INE)
  semilla_i = int(sha256("ddd-semilla-publica/2|<sha padrón>|<sha seccionado>|<código>|<i>")[:16], 16)
              mod (2^31 − 2) + 1,   i = 1..N
  (entero en [1, 2^31 − 2]: válido para random, numpy y --seed-base de m05_gerrychain_strategy, que usa base + 1).
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

from . import territorio as _territorio
from .reglas import ErrorContrato

ESQUEMA = "ddd-semilla-publica/2"
ROLES = ("population", "target_sectioning")
MODULO = 2**31 - 2
FORMULA = ("int(sha256('ddd-semilla-publica/2|<sha population>|<sha target_sectioning>|<código>|<i>')"
           "[:16], 16) mod (2^31-2) + 1")


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


def tabla_maestra() -> dict | None:
    """Ruta y sha256 de la tabla maestra del resolutor (None si el código lo da quien llama)."""
    return _territorio.resolutor().tabla_maestra()


def codigo(territorio: str) -> str:
    """Código oficial (NAC01, AUT17…) del territorio según el resolutor registrado."""
    t = str(territorio).strip()
    if not t:
        raise ValueError("territorio vacío")
    return _territorio.resolutor().codigo(t)


def semillas(cfg: Mapping[str, Any], territorio: str, n: int, roles: tuple[str, ...] = ROLES) -> list[int]:
    if n < 1:
        raise ValueError("n debe ser >= 1")
    cod = codigo(territorio)
    a = ancla(cfg, roles)
    base = "|".join([ESQUEMA, *(a[r] for r in roles), cod])
    out = [int(hashlib.sha256(f"{base}|{i}".encode("utf-8")).hexdigest()[:16], 16) % MODULO + 1
           for i in range(1, n + 1)]
    if len(set(out)) != n:  # colisión (probabilidad despreciable): se dice, no se corrige en silencio
        raise ValueError(f"semillas repetidas en la derivación: {out}")
    return out


def descripcion(cfg: Mapping[str, Any], territorio: str, n: int, roles: tuple[str, ...] = ROLES) -> dict:
    """Lo que el informe publica para que cualquiera rehaga las semillas."""
    return {"esquema": ESQUEMA, "territorio": territorio, "codigo": codigo(territorio), "derivacion": _territorio.resolutor().derivacion,
            "tabla_maestra": tabla_maestra(), "ancla": ancla(cfg, roles), "n": n,
            "semillas": semillas(cfg, territorio, n, roles), "formula": FORMULA}
