#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Deslinde — tablas de naturalidad (partidos judiciales, comarcas agrarias, áreas de movilidad)
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · tablas aportadas por quien llama
FECHA: 2026-11-14
ESTADO: candidato (paquete Deslinde, T-257)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88). Deslinde no empaqueta datos de terceros: quien llama da las tres tablas
  (`desde_ficheros`) o registra un proveedor (el repo registra el suyo en ddd_motor2/tablas_repo.py). La salida
  registra la ruta y el sha256 de cada una (`fuentes`).
MOTIVO: la clave D8 (§3 de DESLINDE_1_0.md) cuenta partidos judiciales y comarcas agrarias partidos y los recargos del
  ReCom ponderado usan además el área de movilidad EM-1 de cada unidad.
FORMATO: partidos  CSV con columnas codigo_ine,id_partido (líneas que empiezan por «#» se ignoran; UTF-8 con BOM o sin)
         comarcas  CSV con columnas codigo_ine,id_comarca (ídem)
         areas     CSV de áreas de movilidad EM-1 (INE 2019) con columnas id_area_geo,id_grupo,tipo; cuentan las filas
                   de tipo SECCIÓN, DISTRITO o MUNICIPIO (clave de 10, 7 o 5 cifras).
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .reglas import ErrorDatos


@dataclass(frozen=True)
class Tablas:
    pj: dict            # municipio INE (5 cifras) -> partido judicial
    ca: dict            # municipio INE -> comarca agraria
    indice: dict        # clave de 10/7/5 cifras -> (área de movilidad, tipo)
    fuentes: list = field(default_factory=list)  # [{"tabla", "ruta", "sha256"}]


def _csv_comentado(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def _csv(p: Path) -> list[dict]:
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def indice_secciones(areas: list[dict]) -> dict[str, tuple[str, str]]:
    """Clave (10, 7 o 5 cifras) -> (id_grupo, tipo). SCD (11 caracteres) no se puede casar con secciones."""
    ind = {}
    for a in areas:
        if a["tipo"] in ("SECCIÓN", "DISTRITO", "MUNICIPIO"):
            ind[a["id_area_geo"]] = (a["id_grupo"], a["tipo"])
    return ind


def grupo_area(sec: str, ind: dict) -> str | None:
    for k in (sec[:10], sec[:7], sec[:5]):
        if k in ind:
            return ind[k][0]
    return None


def fuente(tabla: str, ruta: Path, nombre: str | None = None) -> dict:
    return {"tabla": tabla, "ruta": nombre or Path(ruta).name, "sha256": hashlib.sha256(Path(ruta).read_bytes()).hexdigest()}


def desde_ficheros(partidos: str | Path, comarcas: str | Path, areas: str | Path) -> Tablas:
    partidos, comarcas, areas = Path(partidos), Path(comarcas), Path(areas)
    return Tablas(pj={r["codigo_ine"]: r["id_partido"] for r in _csv_comentado(partidos)},
                  ca={r["codigo_ine"]: r["id_comarca"] for r in _csv_comentado(comarcas)},
                  indice=indice_secciones(_csv(areas)),
                  fuentes=[fuente("partidos_judiciales", partidos), fuente("comarcas_agrarias", comarcas),
                           fuente("areas_movilidad", areas)])


def _sin_tablas() -> Tablas:
    raise ErrorDatos("Deslinde: faltan las tablas de naturalidad (deslinde.tablas.registrar(desde_ficheros(...)))")


_PROVEEDOR: Callable[[], Tablas] = _sin_tablas
_CACHE: list = []


def registrar(proveedor: Tablas | Callable[[], Tablas]) -> None:
    """Fija las tablas (o una función que las da, perezosa: se llama una vez, al primer uso)."""
    global _PROVEEDOR
    _PROVEEDOR = (lambda: proveedor) if isinstance(proveedor, Tablas) else proveedor
    _CACHE.clear()


def tablas() -> Tablas:
    if not _CACHE:
        _CACHE.append(_PROVEEDOR())
    return _CACHE[0]
