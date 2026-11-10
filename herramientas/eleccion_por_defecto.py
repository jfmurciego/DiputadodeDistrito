#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Elección por defecto de las entradas sin `election_date` (T-203).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ESTADO: candidato
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: fuente única de la constante, sin dependencias pesadas (el registro importa pyproj y rompía los planes «sin shapely/pyproj»).
ANTERIOR: ninguna (fichero nuevo)
"""
ELECCION_POR_DEFECTO = "2023-07-23"  # entradas sin election_date (anteriores a 1.5.0)
