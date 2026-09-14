#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: catálogo nacional
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Cobertura provincial completa
FECHA: 2026-09-12
ESTADO: vigente — R022
FUNCIÓN: exige IDs únicos y cobertura exacta de los códigos provinciales 01–52 usados por INE, sin duplicados.
CAMBIOS: primera versión.
MOTIVO: impedir omisiones o solapes al paralelizar bootstraps territoriales.
ANTERIOR: ninguno — prueba nueva.
"""
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
CAT=yaml.safe_load((ROOT/"configuracion/catalogo_territorios_espana_2025.yaml").read_text(encoding="utf-8"))["territories"]

def test_catalogo_ids_y_codigos_unicos():
    ids=[x["territory_id"] for x in CAT]
    assert len(ids)==len(set(ids))==19
    codes=[str(c).zfill(2) for x in CAT for c in x["province_codes"]]
    assert len(codes)==len(set(codes))==52
    assert set(codes)=={f"{i:02d}" for i in range(1,53)}

def test_madrid_es_siguiente_y_arquipielagos_explicitos():
    madrid=next(x for x in CAT if x["territory_id"]=="madrid")
    assert madrid["batch"]=="madrid" and madrid["province_codes"]==["28"]
    assert {x["territory_id"] for x in CAT if x["batch"]=="insular"}=={"illes_balears","canarias"}
