#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_swaps_2x2_m05.py
VERSIÓN: 1.0.0
NOMBRE: Diagnóstico de intercambios 2↔2 M05
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica soluciones.
FUNCIÓN: buscar intercambios de dos unidades conexas por dos unidades conexas entre distritos vecinos después
de agotar movimientos simples, swaps 1×1 y 1↔2/2↔1. Cada paquete debe ser conexo y estar anclado a la
frontera contraria. La solución resultante debe preservar provincia, suelo/techo, cierre urbano y contigüidad.
MOTIVO: EXT-07 Run 34643074456 probó 43 intercambios 1↔2/2↔1 y ninguno fue válido; 39 fallaron por
conectividad del distrito vecino y existen casos cuya masa sería aceptable pero cuya topología no. Un 2↔2 es
el siguiente operador compuesto mínimo capaz de sustituir simultáneamente piezas de articulación a ambos lados.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, io, itertools, json, sys, zipfile
from collections import deque
from pathlib import Path
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml, module_cfg

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
    s=next(iter(nodes)); seen={s}; q=deque([s])
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen: seen.add(v); q.append(v)
    return len(seen)==len(nodes)

def objective(vals,target,floor,cap,tol):
    xs=list(vals.values())
    hard=sum(p<floor or p>cap for p in xs)
    mag=sum(max(0,floor-p,p-cap) for p in xs)
    outside=sum(abs(p-target)>tol for p in xs)
    mx=max(abs(p-target)/target for p in xs)
    sq=sum(((p-target)/target)**2 for p in xs)
    return (hard,round(mag/target,12),outside,round(mx,12),round(sq,12))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--params',required=True); ap.add_argument('--geojson',required=True); ap.add_argument('--out',required=True); ap.add_argument('--top',type=int,default=100)
    a=ap.parse_args(); cfg=load_params_yaml(a.params); s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps'); val=cfg.get('validation',{}) or {}
    graph=json.loads(Path(s5['in_graph_json']).read_text(encoding='utf-8'))
    pop={str(n['id']):int(n.get('pop',0)) for n in graph['nodes']}; adj={n:set() for n in pop}
    for e in graph['edges']:
        u,v=str(e['u']),str(e['v']); adj[u].add(v); adj[v].add(u)
    g=load_geo(a.geojson); idf=s5.get('id_field','CUSEC_KEY'); did=s5.get('district_field','district_id'); provf=s5.get('province_field','CPRO')
    g[idf]=g[idf].astype(str); g[did]=g[did].astype(int); g[provf]=g[provf].astype(str).str.zfill(2); g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    section_unit=dict(zip(g[idf],g.ddd_unit_id)); unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')}; unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()}; unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')}
    d_nodes={d:set(x[idf].astype(str)) for d,x in g.groupby(did)}; d_pop={d:sum(pop[n] for n in ns) for d,ns in d_nodes.items()}; d_prov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_nodes}; d_units={d:set(x['ddd_unit_id'].astype(str)) for d,x in g.groupby(did)}
    d_closed={int(d):bool(x['ddd_closed_urban'].all()) for d,x in g.groupby(did)} if 'ddd_closed_urban' in g.columns else {d:False for d in d_nodes}
    total=sum(pop.values()); K=len(d_pop); target=total/K; floor=target*float(val.get('population_floor_ratio',.8)); cap=target*float(val.get('population_cap_ratio',1.75)); tol=target*float(val.get('target_tolerance_ratio',.12)); cur=objective(d_pop,target,floor,cap,tol); outliers={d for d,p in d_pop.items() if abs(p-target)>tol}
    uadj={u:set() for u in unit_nodes}
    for n,u in section_unit.items():
        for nb in adj.get(n,set()):
            v=section_unit.get(nb)
            if v and v!=u:uadj[u].add(v)
    def touches(u,d): return any(unit_dist.get(v)==d for v in uadj.get(u,set()))
    def packages(d,e):
        out=[]; units=sorted(d_units[d],key=str)
        for u,v in itertools.combinations(units,2):
            if v not in uadj.get(u,set()): continue
            if touches(u,e) or touches(v,e): out.append((u,v))
        return out
    pairs=set()
    for d in outliers:
        if d_closed.get(d,False):continue
        for u in d_units[d]:
            for v in uadj.get(u,set()):
                e=unit_dist[v]
                if e!=d and not d_closed.get(e,False) and d_prov[e]==d_prov[d]:pairs.add((d,e))
    results=[]
    for d,e in sorted(pairs):
        for left in packages(d,e):
            for right in packages(e,d):
                if not any(v in uadj.get(u,set()) for u in left for v in right):continue
                ln=set().union(*(unit_nodes[u] for u in left)); rn=set().union(*(unit_nodes[v] for v in right)); nd=(d_nodes[d]-ln)|rn; ne=(d_nodes[e]-rn)|ln; reasons=[]
                if not nd or not ne:reasons.append('empty')
                if nd and not connected(nd,adj):reasons.append('district_d_disconnect')
                if ne and not connected(ne,adj):reasons.append('district_e_disconnect')
                lp=sum(unit_pop[u] for u in left); rp=sum(unit_pop[v] for v in right); pd=d_pop[d]-lp+rp; pe=d_pop[e]-rp+lp
                if not(floor<=pd<=cap):reasons.append('district_d_floor_cap')
                if not(floor<=pe<=cap):reasons.append('district_e_floor_cap')
                trial=dict(d_pop); trial[d]=pd; trial[e]=pe; obj=objective(trial,target,floor,cap,tol)
                if obj>=cur:reasons.append('objective_non_improvement')
                results.append({'districts':[d,e],'units_d':list(left),'units_e':list(right),'population_d_package':lp,'population_e_package':rp,'new_pops':[pd,pe],'objective':list(obj),'reasons':reasons,'valid_improvement':not reasons})
    results.sort(key=lambda x:(tuple(x['objective']),tuple(x['units_d']),tuple(x['units_e']))); valid=[x for x in results if x['valid_improvement']]
    summary={'current_objective':list(cur),'outliers':sorted(outliers),'candidates_tested':len(results),'valid_improving_exchanges':len(valid),'best_valid':valid[:a.top],'best_any':results[:a.top]}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'outliers':sorted(outliers),'candidates_tested':len(results),'valid_improving_exchanges':len(valid),'best_valid':valid[:5]},ensure_ascii=False))
if __name__=='__main__':main()
