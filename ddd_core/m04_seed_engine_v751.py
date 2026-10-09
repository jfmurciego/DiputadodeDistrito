#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
MÓDULO 04 — MOTOR DE SEMILLAS
VERSIÓN: 7.5.1
NOMBRE: Puerta mínima por componente territorial dependiente
FECHA: 2026-09-11
ESTADO: experimental EXT-03.
QUÉ HACE: extiende v7.5.0 con `gateway_policy: preserve_component_gateways`. Para cada municipio sobredimensionado calcula las componentes de su provincia al retirar ese municipio y obliga a conservar en el residuo exactamente una sección-puerta determinista por componente exterior que dependa de él.
MOTIVO: preservar todas las puertas externas bloquea Badajoz; preservar solo alguna puede aislar La Albuera o Aliseda. La condición correcta es mantener conectada cada componente exterior al residuo con el mínimo número de puertas.
COMPATIBILIDAD: `legacy` reproduce 7.4.7; `preserve_all_external_gateways` conserva el experimento 7.5.0; la política nueva es opt-in.
ANTERIOR: ddd_core/m04_seed_engine_v750.py
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg,require

BASE_PATH=ROOT/'ddd_core'/'m04_seed_engine_v745.py'
POST_PATH=ROOT/'ddd_core'/'m04_seed_engine_v747.py'


def _load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise SystemExit(f'M04 v7.5.1: no se puede cargar {path}')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def _components(nodes,adj):
    unseen=set(nodes);out=[]
    while unseen:
        s=next(iter(unseen));unseen.remove(s);seen={s};stack=[s]
        while stack:
            u=stack.pop()
            for v in adj.get(u,set()):
                if v in unseen: unseen.remove(v);seen.add(v);stack.append(v)
        out.append(seen)
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);args=ap.parse_args()
    cfg=load_params_yaml(args.params);s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts')
    policy=str(s4.get('gateway_policy','legacy'))
    base=_load(BASE_PATH,'ddd_m04_seed_engine_v745_for_v751')
    original=base.partition_oversized_municipality

    if policy in {'preserve_all_external_gateways','preserve_component_gateways'}:
        ing=require(s4.get('in_graph_json'),'Falta M04 grafo')
        ingeo=require(s4.get('in_geojson'),'Falta M04 geojson')
        idf=require(s4.get('id_field'),'Falta id');provf=s4.get('province_field','CPRO')
        G=json.loads(Path(ing).read_text(encoding='utf-8'))
        adj={str(n['id']):set() for n in G['nodes']}
        for e in G['edges']:
            u,v=str(e['u']),str(e['v'])
            if u in adj and v in adj: adj[u].add(v);adj[v].add(u)
        geo=base.load_geo(ingeo);geo[idf]=geo[idf].astype(str);geo[provf]=geo[provf].astype(str).str.zfill(2)
        prov_by={str(r[idf]):str(r[provf]).zfill(2) for _,r in geo.iterrows()}
        province_nodes={p:set(x[idf].astype(str)) for p,x in geo.groupby(provf)}

        def protected_gateways(nodes):
            nodes=set(nodes);prov=prov_by[next(iter(nodes))]
            if policy=='preserve_all_external_gateways':
                return {n for n in nodes if any(nb in province_nodes[prov]-nodes for nb in adj.get(n,set()))}
            outside=province_nodes[prov]-nodes
            keep=set()
            for comp in _components(outside,adj):
                candidates={n for n in nodes if any(nb in comp for nb in adj.get(n,set()))}
                if not candidates: continue
                def score(n):
                    links=sum(1 for nb in adj.get(n,set()) if nb in comp)
                    return (-links,str(n))
                keep.add(min(candidates,key=score))
            return keep

        def patched(nodes,target,tol,adj_arg,w,label='',protected=None):
            expanded=set(protected or ()) | protected_gateways(nodes)
            return original(nodes,target,tol,adj_arg,w,label=label,protected=expanded)
        base.partition_oversized_municipality=patched
    elif policy!='legacy':
        raise SystemExit(f'M04 v7.5.1: gateway_policy desconocida: {policy}')

    base.main()
    post=_load(POST_PATH,'ddd_m04_seed_engine_v747_post_for_v751')
    post.postprocess(args.params)
    print(f'[Módulo 4] motor v7.5.1 gateway_policy={policy}')

if __name__=='__main__': main()
