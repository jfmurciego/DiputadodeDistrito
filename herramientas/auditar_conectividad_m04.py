#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Auditoría de conectividad previa a M04
VERSIÓN: 1.0.0
FECHA: 2026-09-11
QUÉ HACE: inspecciona, desde M01+M03, cómo se conecta cada municipio con municipios vecinos y qué aristas/topology_bridges sostienen esa conectividad.
MOTIVO: distinguir si una futura desconexión del grafo de unidades M04 nace en la topología original o al convertir municipios sobredimensionados en núcleos cerrados y residuos abiertos.
NO HACE: no modifica geometría, no crea puentes, no ejecuta distritación y no decide parámetros.
"""
from __future__ import annotations
import argparse, io, json, zipfile
from collections import defaultdict
from pathlib import Path
import geopandas as gpd


def load_geo(path: str):
    p=Path(path)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            n=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            return gpd.read_file(io.BytesIO(z.read(n)))
    return gpd.read_file(p)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--geojson',required=True)
    ap.add_argument('--graph',required=True)
    ap.add_argument('--municipality',action='append',required=True,help='CUMUN, repetible')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()

    g=load_geo(args.geojson)
    g['CUSEC_KEY']=g['CUSEC_KEY'].astype(str)
    g['CUMUN']=g['CUMUN'].astype(str)
    g['CPRO']=g['CPRO'].astype(str).str.zfill(2)
    meta=g.set_index('CUSEC_KEY').to_dict('index')
    G=json.loads(Path(args.graph).read_text(encoding='utf-8'))
    edge_records=[]
    adj=defaultdict(list)
    for e in G['edges']:
        u,v=str(e['u']),str(e['v'])
        adj[u].append((v,e));adj[v].append((u,e))
    out={}
    targets=set(str(x) for x in args.municipality)
    for mun in sorted(targets):
        rows=g[g['CUMUN']==mun]
        if rows.empty:
            out[mun]={'error':'municipality_not_found'};continue
        sections=set(rows['CUSEC_KEY'])
        external=[];internal=[]
        external_by_mun=defaultdict(lambda:{'edges':0,'sections_from':set(),'sections_to':set(),'edge_types':set(),'neighbor_name':''})
        for u in sorted(sections):
            for v,e in adj.get(u,[]):
                rec={
                    'u':u,'v':v,'edge_type':e.get('edge_type',''),
                    'u_pop':int(meta[u].get('POP_2025',0)) if u in meta else None,
                    'v_pop':int(meta[v].get('POP_2025',0)) if v in meta else None,
                    'v_municipality':str(meta[v].get('CUMUN','')) if v in meta else '',
                    'v_municipality_name':str(meta[v].get('NMUN','')) if v in meta else '',
                }
                if v in sections:
                    if u<v: internal.append(rec)
                else:
                    external.append(rec)
                    vm=rec['v_municipality']; z=external_by_mun[vm]
                    z['edges']+=1;z['sections_from'].add(u);z['sections_to'].add(v);z['edge_types'].add(rec['edge_type']);z['neighbor_name']=rec['v_municipality_name']
        summary=[]
        for vm,z in sorted(external_by_mun.items()):
            summary.append({'municipality':vm,'name':z['neighbor_name'],'edges':z['edges'],'sections_from':sorted(z['sections_from']),'sections_to':sorted(z['sections_to']),'edge_types':sorted(z['edge_types'])})
        out[mun]={
            'municipality_name':str(rows['NMUN'].iloc[0]) if 'NMUN' in rows else '',
            'province':str(rows['CPRO'].iloc[0]),
            'sections':len(sections),
            'population':int(rows['POP_2025'].sum()),
            'internal_edges':len(internal),
            'external_edges':len(external),
            'external_neighbors_summary':summary,
            'external_edges_detail':external,
        }
    Path(args.out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
