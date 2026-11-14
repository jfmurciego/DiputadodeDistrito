#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: motor 2 — tablas de naturalidad del repo para Deslinde
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Deslinde 1.0.0 · tablas del repo
FECHA: 2026-11-14
ESTADO: candidato (motor 2)
CAMBIOS: 1.0.0 — fichero nuevo (T-257, D-88): registra en Deslinde (deslinde.tablas) las tres tablas versionadas que
  leía naturalidad_clave._tablas: configuracion/partidos_judiciales.csv, docs/ESTUDIOS/T64_comarcas_partidos/
  comarcas_agrarias.csv y datos/movilidad/areas_movilidad_2019.csv (índice de secciones). Mismos datos, misma lectura.
MOTIVO: Deslinde no empaqueta datos de terceros (D-88): quien llama da las tablas; el repo da las suyas.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

from pathlib import Path

from deslinde import tablas as _tablas

ROOT = Path(__file__).resolve().parents[1]
PARTIDOS = ROOT / "configuracion" / "partidos_judiciales.csv"
AGRARIAS = ROOT / "docs" / "ESTUDIOS" / "T64_comarcas_partidos" / "comarcas_agrarias.csv"
AREAS = ROOT / "datos" / "movilidad" / "areas_movilidad_2019.csv"


def tablas_repo() -> _tablas.Tablas:
    t = _tablas.desde_ficheros(PARTIDOS, AGRARIAS, AREAS)
    for f, ruta in zip(t.fuentes, (PARTIDOS, AGRARIAS, AREAS)):
        f["ruta"] = ruta.relative_to(ROOT).as_posix()
    return t


_tablas.registrar(tablas_repo)
