#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_movimientos_topologicos_m04.py
VERSIÓN: 1.0.0
NOMBRE: Probe de movimientos topológicos M04
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica asignaciones.
FUNCIÓN: enumerar movimientos de una unidad DDD entre distritos vecinos que preservan provincia, suelo/techo
y contigüidad, y medir si reducen la fragilidad topológica global. Separa mejoras estrictas que no empeoran
la función poblacional de mejoras topológicas guardadas que mantienen número de outliers y máximo desvío.
MOTIVO: EXT-07/08 agotaron operadores locales sobre M05; EXT-10 demostró que el seed M04 no se usa. Antes
de cambiar la construcción M04 se debe comprobar si un pulido topológico simple sobre su salida hard=0 basta.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, io, json, sys, zipfile
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
    s=next(iter(nodes));seen={s};q=deque([s])
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)

def articulation_signature(d_units,uadj,unit_pop,target):
    districts_with=0; total_arts=0; vulnerable_sum=0; max_vulnerable=0
    for us in d_units.values():
        us=set(us); ia={u:{v for v in uadj.get(u,set()) if v in us} for u in us}; arts=0
        for cut in us:
            rest=us-{cut}
            if len(rest)<=1:continue
            rem=set(rest); comps=[]
            while rem:
                s=next(iter(rem));rem.remove(s);seen={s};q=deque([s])
                while q:
                    x=q.popleft()
                    for y in ia.get(x,set()):
                        if y in rem:rem.remove(y);seen.add(y);q.append(y)
                comps.append(seen)
            if len(comps)<=1:continue
            arts+=1
            small=min(sum(unit_pop[u] for u in c) for c in comps)
            vulnerable_sum+=small;max_vulnerable=max(max_vulnerable,small)
        if arts:districts_with+=1
        total_arts+=arts
    return (districts_with,total_arts,round(vulnerable_sum/target,12),round(max_vulnerable/target,12))

def pop_objective(dpop,target,floor,cap,tol):
    vals=list(dpop.values()); hard=sum(p<floor or p>cap for p in vals);outside=sum(abs(p-target)>tol for p in vals);mx=max(abs(p-target)/target for p in vals);sq=sum(((p-target)/target)**2 for p in vals)
    return (hard,outside,round(mx,12),round(sq,12))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out',required=True);ap.add_argument('--top',type=int,default=100);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');val=cfg.get('validation',{}) or {}
    graph_path=s5.get('in_graph_json') or s4.get('in_graph_json');G=json.loads(Path(graph_path).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};sadj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v']);sadj[u].add(v);sadj[v].add(u)
    g=load_geo(a.geojson);idf=s5.get('id_field') or s4.get('id_field','CUSEC_KEY');did=s5.get('district_field','district_id');provf=s5.get('province_field') or s4.get('province_field','CPRO');munf=s5.get('municipality_field','CUMUN')
    g[idf]=g[idf].astype(str);g[did]=g[did].astype(int);g[provf]=g[provf].astype(str).str.zfill(2);g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    sec_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_prov={u:str(x[provf].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_mun={u:sorted(set(x[munf].astype(str))) if munf in x.columns else [] for u,x in g.groupby('ddd_unit_id')}
    uadj={u:set() for u in unit_nodes}
    for n,u in sec_unit.items():
        for nb in sadj.get(n,set()):
            v=sec_unit.get(nb)
            if v is not None and v!=u:uadj[u].add(v)
    d_units={d:set(x.ddd_unit_id.astype(str)) for d,x in g.groupby(did)};dpop={d:sum(unit_pop[u] for u in us) for d,us in d_units.items()};dprov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_units}
    total=sum(pop.values());K=len(d_units);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12))
    cur_pop=pop_objective(dpop,target,floor,cap,tol);cur_frag=articulation_signature(d_units,uadj,unit_pop,target);cands=[]
    for u,a0 in sorted(unit_dist.items(),key=lambda x:str(x[0])):
        if len(d_units[a0])<=1:continue
        neigh=sorted({unit_dist[v] for v in uadj.get(u,set()) if unit_dist[v]!=a0 and dprov.get(unit_dist[v])==dprov[a0]})
        if not neigh:continue
        donor_after=d_units[a0]-{u}
        if not connected(donor_after,uadj):continue
        for b in neigh:
            recv_after=d_units[b]|{u}
            if not connected(recv_after,uadj):continue
            pa=dpop[a0]-unit_pop[u];pb=dpop[b]+unit_pop[u]
            if not(floor<=pa<=cap and floor<=pb<=cap):continue
            trial_units={d:set(us) for d,us in d_units.items()};trial_units[a0].remove(u);trial_units[b].add(u)
            trial_pop=dict(dpop);trial_pop[a0]=pa;trial_pop[b]=pb
            pobj=pop_objective(trial_pop,target,floor,cap,tol);frag=articulation_signature(trial_units,uadj,unit_pop,target)
            if frag>=cur_frag:continue
            strict=pobj<=cur_pop
            guarded=(pobj[0]==0 and pobj[1]<=cur_pop[1] and pobj[2]<=cur_pop[2])
            cands.append({'unit':u,'from':a0,'to':b,'population':unit_pop[u],'municipalities':unit_mun[u],'population_objective':list(pobj),'fragility_signature':list(frag),'strict_population_nonworsening':strict,'guarded_population':guarded,'new_populations':[pa,pb]})
    cands.sort(key=lambda x:(not x['strict_population_nonworsening'],not x['guarded_population'],tuple(x['fragility_signature']),tuple(x['population_objective']),str(x['unit']),x['from'],x['to']))
    result={'current_population_objective':list(cur_pop),'current_fragility_signature':list(cur_frag),'valid_topology_improving_moves':len(cands),'strict_population_nonworsening':sum(x['strict_population_nonworsening'] for x in cands),'guarded_population':sum(x['guarded_population'] for x in cands),'best':cands[:a.top]}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:result[k] for k in ('current_population_objective','current_fragility_signature','valid_topology_improving_moves','strict_population_nonworsening','guarded_population')},ensure_ascii=False));print(json.dumps(result['best'][:5],ensure_ascii=False))
if __name__=='__main__':main()
