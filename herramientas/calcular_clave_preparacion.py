#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Clave de preparación territorial
VERSIÓN: 1.0.1
NOMBRE DE VERSIÓN: Caché selectiva M01-M03 — Gobernanza R015
FECHA: 2026-09-11
QUÉ HACE: calcula una huella SHA-256 solo de fuentes, configuración y código que pueden cambiar M01-M03.
POR QUÉ EXISTE: cambiar M04/M05 o parámetros electorales no debe invalidar una preparación territorial costosa e idéntica.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/herramientas/calcular_clave_preparacion_v1.0.0.py
"""
import argparse,hashlib,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args();p=(ROOT/a.params).resolve();cfg=yaml.safe_load(p.read_text(encoding='utf-8'));mods=cfg.get('modulos',{});payload={'meta':{k:cfg.get('meta',{}).get(k) for k in ('run_name','territory','year','scope')},'input':cfg.get('io',{}).get('input',{}),'m01':mods.get('modulo_01_preparar_base_territorial',{}),'m02':mods.get('modulo_02_construir_adyacencias',{}),'m03':mods.get('modulo_03_construir_grafo',{})};h=hashlib.sha256(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
    for rel in ['inputs/MANIFEST.sha256','modulos/01_preparar_base_territorial.py','modulos/02_construir_adyacencias.py','modulos/03_construir_grafo.py','ddd_core/config.py']:
        q=ROOT/rel
        if q.exists():h.update(rel.encode());h.update(q.read_bytes())
    print(h.hexdigest())
if __name__=='__main__':main()
