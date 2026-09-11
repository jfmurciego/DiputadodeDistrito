#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_swaps_m05.py
VERSIÓN: 1.0.0
NOMBRE: Diagnóstico de swaps 1×1 M05
FECHA: 2026-09-11
FUNCIÓN: buscar intercambios de una unidad por una unidad entre distritos vecinos, preservando restricciones duras y midiendo la función objetivo canónica.
MOTIVO: cuando ningún movimiento unitario mejora un outlier, comprobar si el mínimo local se cruza con un operador compuesto mínimo antes de modificar M05.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, io, json, sys, zipfile
from collections import deque
from pathlib import Path
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg

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
    vs=list(vals.values());hard=sum(p<floor or p>cap for p in vs);mag=sum(max(0,floor-p,p-cap) for p in vs);outside=sum(abs(p-target)>tol for p in vs);mx=max(abs(p-target)/target for p in vs);sq=sum(((p-target)/target)**2 for p in vs)
    return (hard,mag/target,outside,mx,sq)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out',required=True);ap.add_argument('--top',type=int,default=50);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');val=cfg.get('validation',{}) or {};graph=json.loads(Path(s5['in_graph_json']).read_text());pop={str(n['id']):int(n.get('pop',0)) for n in graph['nodes']};adj={n:set() for n in pop}
    for e in graph['edges']:
        u,v=str(e['u']),str(e['v']);adj[u].add(v);adj[v].add(u)
    g=load_geo(a.geojson);idf=s5.get('id_field','CUSEC_KEY');did=s5.get('district_field','district_id');provf=s5.get('province_field','CPRO');munf=s5.get('municipality_field','CUMUN');g[idf]=g[idf].astype(str);g[did]=g[did].astype(int);g[provf]=g[provf].astype(str).str.zfill(2);g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    section_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf]) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_mun={u:sorted(set(x[munf].astype(str))) for u,x in g.groupby('ddd_unit_id')};d_nodes={d:set(x[idf]) for d,x in g.groupby(did)};d_pop={d:sum(pop[n] for n in ns) for d,ns in d_nodes.items()};d_prov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_nodes};d_units={d:set(g[g[did]==d].ddd_unit_id) for d in d_nodes}
    total=sum(pop.values());K=len(d_pop);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12));cur=objective(d_pop,target,floor,cap,tol);outliers={d for d,p in d_pop.items() if abs(p-target)>tol}
    uadj={u:set() for u in unit_nodes}
    for n,u in section_unit.items():
        for nb in adj.get(n,set()):
            v=section_unit.get(nb)
            if v and v!=u:uadj[u].add(v)
    boundary={d:set() for d in d_pop}
    for u,d in unit_dist.items():
        if any(unit_dist[v]!=d for v in uadj.get(u,set())):boundary[d].add(u)
    results=[];seen=set()
    pairs=set()
    for d in outliers:
        for u in boundary[d]:
            for v in uadj.get(u,set()):
                e=unit_dist[v]
                if e!=d and d_prov[e]==d_prov[d]:pairs.add(tuple(sorted((d,e))))
    for d,e in sorted(pairs):
        for u in sorted(boundary[d]):
            if not any(unit_dist.get(v)==e for v in uadj.get(u,set())):continue
            for v in sorted(boundary[e]):
                if not any(unit_dist.get(x)==d for x in uadj.get(v,set())):continue
                key=(u,v,d,e)
                if key in seen:continue
                seen.add(key);pu,pv=unit_pop[u],unit_pop[v];nd=(d_nodes[d]-unit_nodes[u])|unit_nodes[v];ne=(d_nodes[e]-unit_nodes[v])|unit_nodes[u]
                reasons=[]
                if not nd or not ne:reasons.append('empty')
                if nd and not connected(nd,adj):reasons.append('district_d_disconnect')
                if ne and not connected(ne,adj):reasons.append('district_e_disconnect')
                pd=d_pop[d]-pu+pv;pe=d_pop[e]-pv+pu
                if not(floor<=pd<=cap):reasons.append('district_d_floor_cap')
                if not(floor<=pe<=cap):reasons.append('district_e_floor_cap')
                trial=dict(d_pop);trial[d]=pd;trial[e]=pe;obj=objective(trial,target,floor,cap,tol)
                improves=obj<cur
                if not improves:reasons.append('objective_non_improvement')
                results.append({'districts':[d,e],'unit_d':u,'unit_e':v,'unit_d_pop':pu,'unit_e_pop':pv,'unit_d_municipalities':unit_mun[u],'unit_e_municipalities':unit_mun[v],'new_pops':[pd,pe],'objective':list(obj),'reasons':reasons,'valid_improvement':not reasons})
    results.sort(key=lambda x:(tuple(x['objective']),x['unit_d'],x['unit_e']))
    summary={'current_objective':list(cur),'outliers':sorted(outliers),'pairs_tested':len(results),'valid_improving_swaps':sum(x['valid_improvement'] for x in results),'best':results[:a.top]}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True);Path(a.out).write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({'outliers':sorted(outliers),'pairs_tested':len(results),'valid_improving_swaps':summary['valid_improving_swaps'],'best_valid':[x for x in results if x['valid_improvement']][:5]},ensure_ascii=False))
if __name__=='__main__':main()
