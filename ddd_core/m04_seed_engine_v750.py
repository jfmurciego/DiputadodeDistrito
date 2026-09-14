#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
MÓDULO 04 — MOTOR DE SEMILLAS
VERSIÓN: 7.5.0
NOMBRE: Preservación explícita de puertas territoriales externas
FECHA: 2026-09-11

QUÉ HACE
Ejecuta el motor 7.4.5 con una política configurable para municipios sobredimensionados y después aplica el postproceso 7.4.7 de factibilidad provincial.

NUEVA POLÍTICA
`gateway_policy: preserve_all_external_gateways` obliga a que TODA sección de un municipio sobredimensionado que tenga una arista hacia fuera del municipio permanezca en el residuo abierto. Por tanto un núcleo urbano cerrado no puede cortar la única conexión territorial de municipios vecinos.

COMPATIBILIDAD
Si `gateway_policy` falta o vale `legacy`, reproduce la semántica 7.4.7: las puertas externas solo orientan la elección del residuo, pero no todas son obligatorias. Esto permite probar EXT-03 sin cambiar todavía Aragón/CYL.

MOTIVO
EXT-03 demostró que La Albuera solo enlaza con el resto de Badajoz mediante dos secciones del municipio de Badajoz y Aliseda solo mediante una sección del municipio de Cáceres. M03 es conexo; la desconexión nace al cerrar esas puertas en M04.

NO RESUELVE AÚN
La política de extremos de topology_bridges internos al mismo municipio se mantiene como legado. Se probará separadamente si Don Benito sigue bloqueado después de preservar puertas externas.
"""
from __future__ import annotations
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg

BASE_PATH=ROOT/'ddd_core'/'m04_seed_engine_v745.py'
POST_PATH=ROOT/'ddd_core'/'m04_seed_engine_v747.py'


def _load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise SystemExit(f'M04 v7.5.0: no se puede cargar {path}')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);args=ap.parse_args()
    cfg=load_params_yaml(args.params)
    s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts')
    policy=str(s4.get('gateway_policy','legacy'))
    base=_load(BASE_PATH,'ddd_m04_seed_engine_v745_for_v750')
    original=base.partition_oversized_municipality

    if policy=='preserve_all_external_gateways':
        def patched(nodes,target,tol,adj,w,label='',protected=None):
            nodes=set(nodes)
            external_gateways={n for n in nodes if any(nb not in nodes for nb in adj.get(n,set()))}
            expanded=set(protected or ()) | external_gateways
            return original(nodes,target,tol,adj,w,label=label,protected=expanded)
        base.partition_oversized_municipality=patched
    elif policy!='legacy':
        raise SystemExit(f'M04 v7.5.0: gateway_policy desconocida: {policy}')

    # v7.4.5 parsea el mismo --params desde sys.argv.
    base.main()
    post=_load(POST_PATH,'ddd_m04_seed_engine_v747_post_for_v750')
    post.postprocess(args.params)
    print(f'[Módulo 4] motor v7.5.0 gateway_policy={policy}')

if __name__=='__main__': main()
