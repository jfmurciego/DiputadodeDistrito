#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_bloqueos_m05.py
VERSIÓN: 1.0.1
NOMBRE: Diagnóstico de bloqueos M05 — ejecución directa
FECHA: 2026-09-11
FUNCIÓN: explicar por qué los distritos fuera de tolerancia no pueden mejorar mediante movimientos unitarios M05.
ENTRADAS: grafo M03, GeoJSON M05, configuración territorial.
SALIDAS: JSON con outliers, unidades, municipios, candidatos fronterizos y motivos de rechazo.
CAMBIOS: añade el raíz del repositorio a `sys.path` antes de importar `ddd_core`; sin cambio de lógica diagnóstica.
MOTIVO: v1.0.0 falló al ejecutarse directamente desde `herramientas/` dentro del contenedor por `ModuleNotFoundError: ddd_core`.
ANTERIOR: legacy/herramientas/auditar_bloqueos_m05_v1.0.0.py
"""
from __future__ import annotations
import argparse, io, json, sys, zipfile
from pathlib import Path
from collections import deque
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml, module_cfg, hard_limits


def load_geo(path):
    p=Path(path)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            n=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            return gpd.read_file(io.BytesIO(z.read(n)))
    return gpd.read_file(p)
def connected(nodes,adj):
    nodes=set(nodes)
    if not nodes:return False
    s=next(iter(nodes));seen={s};q=deque([s])
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)
def objective(vals,target,floor,cap,tol):
    vs=list(vals.values());hard=sum(p<floor or p>cap for p in vs);hardmag=sum(max(0,floor-p,p-cap) for p in vs);outside=sum(abs(p-target)>tol for p in vs);mx=max(abs(p-target)/target for p in vs);sq=sum(((p-target)/target)**2 for p in vs)
    return (hard,round(hardmag/target,12),outside,round(mx,12),round(sq,12))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');val=cfg.get('validation',{}) or {}
    graph=json.loads(Path(s5['in_graph_json']).read_text());pop={str(n['id']):int(n.get('pop',0)) for n in graph['nodes']};adj={n:set() for n in pop}
    for e in graph['edges']:
        u,v=str(e['u']),str(e['v']);adj.setdefault(u,set()).add(v);adj.setdefault(v,set()).add(u)
    g=load_geo(a.geojson);idf=s5.get('id_field','CUSEC_KEY');did=s5.get('district_field','district_id');provf=s5.get('province_field','CPRO');munf=s5.get('municipality_field','CUMUN');g[idf]=g[idf].astype(str);g[provf]=g[provf].astype(str).str.zfill(2);g[did]=g[did].astype(int)
    if 'ddd_unit_id' not in g.columns: raise SystemExit('Diagnóstico M05 requiere ddd_unit_id legible en output')
    g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    section_to_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf]) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_prov={u:str(x[provf].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_muns={u:sorted(set(x[munf].astype(str))) for u,x in g.groupby('ddd_unit_id')}
    d_nodes={d:set(x[idf]) for d,x in g.groupby(did)};d_pop={d:sum(pop[n] for n in ns) for d,ns in d_nodes.items()};d_prov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_nodes};d_units={d:set(g[g[did]==d].ddd_unit_id) for d in d_nodes}
    total=sum(pop.values());K=len(d_nodes);target,floor,cap,tol=hard_limits(cfg,k=K,total_pop=total);cur_obj=objective(d_pop,target,floor,cap,tol)
    uadj={u:set() for u in unit_nodes}
    for n,u in section_to_unit.items():
        for nb in adj.get(n,set()):
            v=section_to_unit.get(nb)
            if v and v!=u:uadj[u].add(v)
    outliers=[d for d,p in d_pop.items() if abs(p-target)>tol]
    diagnostics=[]
    for d in sorted(outliers):
        cand=[];boundary_units=[]
        for u in sorted(d_units[d]):
            neigh_ds=sorted({unit_dist[v] for v in uadj.get(u,set()) if unit_dist[v]!=d})
            if neigh_ds: boundary_units.append({'unit':u,'population':unit_pop[u],'municipalities':unit_muns[u],'neighbor_districts':neigh_ds})
        possible_units=set()
        for u,d0 in unit_dist.items():
            for v in uadj.get(u,set()):
                d1=unit_dist[v]
                if d0==d1:continue
                if d0==d or d1==d: possible_units.add((u,d0,d1))
        for u,d0,d1 in sorted(possible_units,key=lambda x:(str(x[0]),x[1],x[2])):
            reasons=[];p=unit_pop[u]
            if d_prov[d0]!=d_prov[d1] or unit_prov[u]!=d_prov[d0]: reasons.append('province')
            if len(d_units[d0])<=1: reasons.append('empty_donor')
            new0=d_pop[d0]-p;new1=d_pop[d1]+p
            if new0<floor or new0>cap: reasons.append('donor_floor_cap')
            if new1<floor or new1>cap: reasons.append('receiver_floor_cap')
            if len(d_units[d0])>1 and not connected(d_nodes[d0]-unit_nodes[u],adj): reasons.append('donor_disconnect')
            if not connected(d_nodes[d1]|unit_nodes[u],adj): reasons.append('receiver_disconnect')
            trial=dict(d_pop);trial[d0]=new0;trial[d1]=new1;tobj=objective(trial,target,floor,cap,tol)
            if tobj>=cur_obj: reasons.append('objective_non_improvement')
            cand.append({'unit':u,'population':p,'municipalities':unit_muns[u],'from':d0,'to':d1,'new_from_pop':new0,'new_to_pop':new1,'objective':list(tobj),'reasons':reasons,'accepted_by_greedy_rules':not reasons})
        diagnostics.append({'district':d,'province':d_prov[d],'population':d_pop[d],'relative_deviation':(d_pop[d]-target)/target,'units':sorted(d_units[d]),'municipalities':g[g[did]==d].groupby(munf)['POP_2025'].sum().sort_values(ascending=False).to_dict() if 'POP_2025' in g.columns else {},'boundary_units':boundary_units,'candidate_moves':cand,'has_single_move_improvement':any(x['accepted_by_greedy_rules'] for x in cand)})
    split=g.groupby(munf)[did].nunique();result={'K':K,'target':target,'floor':floor,'cap':cap,'tolerance':tol,'objective':list(cur_obj),'outlier_count':len(outliers),'outliers':diagnostics,'split_municipalities':{str(k):int(v) for k,v in split[split>1].items()}}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str));print(json.dumps({'outliers':[(x['district'],round(x['relative_deviation'],4),x['has_single_move_improvement']) for x in diagnostics],'splits':result['split_municipalities']},ensure_ascii=False))

if __name__=='__main__':main()
