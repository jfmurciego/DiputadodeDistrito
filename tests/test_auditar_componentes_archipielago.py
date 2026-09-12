#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: auditoría archipelágica
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Componentes deterministas
FECHA: 2026-09-12
ESTADO: vigente — R026
FUNCIÓN: protege el inventario determinista de componentes físicas.
CAMBIOS: primera versión.
MOTIVO: no confundir islas con errores topológicos.
ANTERIOR: ninguno — prueba nueva.
"""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];S=importlib.util.spec_from_file_location("arch",ROOT/"herramientas/auditar_componentes_archipielago.py");M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
def test_components():
    e=[{"u":"a","v":"b"},{"u":"c","v":"d"}]
    assert [sorted(x) for x in M.components(["a","b","c","d","e"],e)]==[["a","b"],["c","d"],["e"]]
