#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — excepción D-66 del contrato (distritos mixtos por municipio)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Excepción D-66 · esquema y validación
FECHA: 2026-11-12
ESTADO: candidato (motor 2; producción no lo importa)
CAMBIOS: fichero nuevo.
MOTIVO: T-259 / D-66: el núcleo admite como máximo 1 distrito mixto por municipio, sin aceptar las infracciones que
  trae el mapa vigente. Si un territorio es infactible por población, su contrato puede declarar una excepción
  explícita, con su motivo, que aprueba el propietario.
ANTERIOR: ninguna (fichero nuevo)
ESQUEMA: validation.max_mixed_districts_exceptions = lista de 0 a 2 entradas (municipios exceptuados), cada una con
  {municipio (código INE de 5 cifras), max_mixtos: 2 (exactamente; nunca más), motivo (texto no vacío),
  prueba_infactibilidad (ruta no vacía), aprobacion (id de decisión del propietario, «D-<n>»)}. Sin municipios
  repetidos ni claves de más.
ALCANCE: esta versión solo valida el esquema y deja la lista anotada en COMPETICION.json y COMPETICION.md. El núcleo
  (ddd_motor2/reglas) todavía no la aplica, así que validar() falla si el contrato declara alguna (T-269 hará la
  relajación real, solo cuando aparezca un territorio infactible con su prueba).
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .reglas import ErrorContrato, norm_codigo

CLAVE = "max_mixed_districts_exceptions"
MAX_ENTRADAS = 2
MAX_MIXTOS_EXCEPCION = 2
CAMPOS = ("municipio", "max_mixtos", "motivo", "prueba_infactibilidad", "aprobacion")
PENDIENTE = "excepción D-66 declarada pero el núcleo aún no la aplica: T-269"
_DECISION = re.compile(r"^D-\d+$")


def _texto(entrada: Mapping[str, Any], campo: str, i: int) -> str:
    v = entrada.get(campo)
    if not isinstance(v, str) or not v.strip():
        raise ErrorContrato(f"validation.{CLAVE}[{i}].{campo} falta o está vacío")
    return v.strip()


def leer(cfg: Mapping[str, Any] | None) -> list[dict]:
    """Excepciones D-66 del contrato, normalizadas y en orden de municipio. [] si no declara ninguna. Falla
    (ErrorContrato) si el esquema no se cumple: más de 2 entradas, campos que faltan, motivo vacío, max_mixtos ≠ 2…"""
    val = (cfg or {}).get("validation") or {}
    if not isinstance(val, Mapping):
        raise ErrorContrato("el contrato no tiene bloque validation")
    lista = val.get(CLAVE)
    if lista is None:
        return []
    if not isinstance(lista, list):
        raise ErrorContrato(f"validation.{CLAVE} debe ser una lista")
    if len(lista) > MAX_ENTRADAS:
        raise ErrorContrato(f"validation.{CLAVE} declara {len(lista)} excepciones; D-66 admite como máximo "
                            f"{MAX_ENTRADAS} por territorio")
    out: list[dict] = []
    for i, e in enumerate(lista):
        if not isinstance(e, Mapping):
            raise ErrorContrato(f"validation.{CLAVE}[{i}] debe ser un objeto")
        sobra = sorted(set(e) - set(CAMPOS))
        if sobra:
            raise ErrorContrato(f"validation.{CLAVE}[{i}] trae claves desconocidas: {', '.join(map(str, sobra))}")
        m = norm_codigo(e.get("municipio"), 5)
        if m is None or not (m.isdigit() and len(m) == 5):
            raise ErrorContrato(f"validation.{CLAVE}[{i}].municipio debe ser un código INE de 5 cifras "
                                f"(recibido {e.get('municipio')!r})")
        mx = e.get("max_mixtos")
        if isinstance(mx, bool) or mx != MAX_MIXTOS_EXCEPCION:
            raise ErrorContrato(f"validation.{CLAVE}[{i}].max_mixtos debe ser {MAX_MIXTOS_EXCEPCION} "
                                f"(D-66: hasta 2 distritos mixtos en ese municipio, nunca más; recibido {mx!r})")
        motivo = _texto(e, "motivo", i)
        prueba = _texto(e, "prueba_infactibilidad", i)
        aprob = _texto(e, "aprobacion", i)
        if not _DECISION.match(aprob):
            raise ErrorContrato(f"validation.{CLAVE}[{i}].aprobacion debe ser el id de una decisión del "
                                f"propietario («D-<n>»; recibido {aprob!r})")
        out.append({"municipio": m, "max_mixtos": MAX_MIXTOS_EXCEPCION, "motivo": motivo,
                    "prueba_infactibilidad": prueba, "aprobacion": aprob})
    muns = [x["municipio"] for x in out]
    if len(set(muns)) != len(muns):
        raise ErrorContrato(f"validation.{CLAVE} repite un municipio")
    return sorted(out, key=lambda x: x["municipio"])


def validar(cfg: Mapping[str, Any] | None) -> list[dict]:
    """leer() y, mientras el núcleo no aplique la excepción (T-269), falla si el contrato declara alguna."""
    excepciones = leer(cfg)
    if excepciones:
        raise ErrorContrato(f"{PENDIENTE} (municipios: {', '.join(x['municipio'] for x in excepciones)})")
    return excepciones
