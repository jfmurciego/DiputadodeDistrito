#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — identidad del territorio (código oficial y ámbito)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · resolutor de territorio
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88): Deslinde no lee la tabla maestra del repo; quien llama le da el
  código oficial (AUTnn = CODAUTO, NACnn = CPRO del INE) o registra un resolutor (el repo registra el suyo,
  ddd_core.territorio_ids, en ddd_motor2/semilla.py).
MOTIVO: T-257 (paquete independiente): la semilla pública (D-90) y las piezas finas (Congreso o no) dependen solo del
  código oficial del territorio, no de rutas del repositorio.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import re
from typing import Protocol

from .reglas import ErrorContrato

CODIGO = re.compile(r"^(AUT|NAC)\d{2}$")


class Resolutor(Protocol):
    derivacion: str

    def codigo(self, territorio: str) -> str: ...

    def es_nacional(self, territorio: str) -> bool: ...

    def tabla_maestra(self) -> dict | None: ...


class CodigoDirecto:
    """Sin tabla maestra: el territorio ES su código oficial (NAC22, AUT17…); cualquier otro valor falla."""

    derivacion = "código oficial dado por quien llama (AUTnn = CODAUTO, NACnn = CPRO del INE)"

    def codigo(self, territorio: str) -> str:
        t = str(territorio).strip().upper()
        if not CODIGO.match(t):
            raise ErrorContrato(f"semilla: {territorio!r} no es un código oficial AUTnn/NACnn (registra un resolutor)")
        return t

    def es_nacional(self, territorio: str) -> bool:
        return bool(CODIGO.match(str(territorio).strip().upper())) and str(territorio).strip().upper().startswith("NAC")

    def tabla_maestra(self) -> dict | None:
        return None


_RESOLUTOR: Resolutor = CodigoDirecto()


def registrar(resolutor: Resolutor) -> None:
    global _RESOLUTOR
    _RESOLUTOR = resolutor


def resolutor() -> Resolutor:
    return _RESOLUTOR
