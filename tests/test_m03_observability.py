#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: pruebas M03 observabilidad
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Auditoría sin bloqueo
FECHA: 2026-09-12
ESTADO: vigente — R022
FUNCIÓN: protege el cálculo determinista de componentes globales y administrativos usado por el bootstrap nacional.
CAMBIOS: primera versión.
MOTIVO: separar diagnóstico y enforcement sin perder visibilidad topológica.
ANTERIOR: ninguno — prueba nueva.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("m03",ROOT/"modulos/03_construir_grafo.py")
M03=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M03)

def test_componentes_globales_deterministas():
    adj={"a":{"b"},"b":{"a"},"c":set()}
    comps=M03.component_sets({"a","b","c"},adj)
    assert [sorted(x) for x in comps]==[["a","b"],["c"]]

def test_auditoria_administrativa_informa_sin_decidir_bloqueo():
    g=pd.DataFrame({"CPRO":["01","01","01"],"CUSEC_KEY":["a","b","c"]})
    adj={"a":{"b"},"b":{"a"},"c":set()}
    details,bad=M03.audit_group_components(g,"CUSEC_KEY",["CPRO"],adj)
    assert details["01"]["components"]==2
    assert details["01"]["component_sizes"]==[2,1]
    assert bad[0]["key"]=="01"
