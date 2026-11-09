#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Numeración pública de distritos (T-135, regla del propietario 09-11).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
QUÉ HACE: UNA regla: en todo lo que ve o recibe el lector, los distritos de cada circunscripción se numeran de 1 a K;
  no existe el distrito 0. El id INTERNO del motor (M04-M06, huellas, GeoJSON M06) sigue siendo 0..K-1 y no se toca
  (rediseño del motor: numerar desde 1 de origen). Toda capa de publicación convierte con `numero_publico`.
"""
from __future__ import annotations

import csv
import io


def numero_publico(interno: int) -> int:
    """Id interno (0..K-1) -> número que ve el lector (1..K)."""
    i = int(interno)
    if i < 0:
        raise ValueError(f"id interno de distrito negativo: {interno}")
    return i + 1


def id_interno(publico: int) -> int:
    """Número público (1..K) -> id interno (0..K-1)."""
    p = int(publico)
    if p < 1:
        raise ValueError(f"no existe el distrito {publico}: se numera de 1 a K")
    return p - 1


def csv_publico(datos: bytes, columna: str = "distrito") -> bytes:
    """Copia el CSV (cabecera + filas) con la columna de distrito en numeración pública."""
    filas = list(csv.reader(io.StringIO(datos.decode("utf-8"), newline="")))
    if not filas or columna not in filas[0]:
        raise ValueError(f"el CSV no tiene la columna «{columna}»")
    j = filas[0].index(columna)
    for f in filas[1:]:
        if f:
            f[j] = str(numero_publico(f[j]))
    out = io.StringIO(newline="")
    csv.writer(out, lineterminator="\n").writerows(filas)
    return out.getvalue().encode("utf-8")


def ceros_en_csv(datos: bytes, columna: str = "distrito") -> int:
    """Número de filas con distrito 0 (debe ser 0 en cualquier producto público)."""
    filas = list(csv.DictReader(io.StringIO(datos.decode("utf-8"), newline="")))
    return sum(1 for f in filas if str(f.get(columna, "")).strip() == "0")
