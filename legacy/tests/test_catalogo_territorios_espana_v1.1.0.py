#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: catálogo nacional
VERSIÓN: 1.1.0
NOMBRE DE VERSIÓN: Cobertura y niveles contractuales
FECHA: 2026-09-12
ESTADO: vigente — R036
FUNCIÓN: exige cobertura provincial exacta y distingue inventario bootstrap de contratos M01–M06 con K gobernado.
CAMBIOS: valida contract_level en 19 entradas y metadatos de K únicamente en las tres implantaciones con contrato de producción.
MOTIVO: impedir que una carpeta preparada se presente como territorio ejecutable o que K quede sin procedencia.
ANTERIOR: legacy/test_catalogo_territorios_espana_v1.0.0.py
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

def test_niveles_y_gobierno_de_k():
    production={x["territory_id"] for x in CAT if x["contract_level"]=="production_m01_m06"}
    assert production=={"aragon","castilla_y_leon","extremadura"}
    for territory in CAT:
        assert territory["contract_level"] in {"bootstrap_m01_m03","production_m01_m06"}
        governed=all(territory.get(key) not in (None, "") for key in ("k_districts","k_source","k_rationale"))
        assert governed == (territory["contract_level"]=="production_m01_m06")
