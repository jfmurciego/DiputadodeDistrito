#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_relevos_outliers_m05.py
VERSIÓN: 1.0.0
NOMBRE: Auditor de relevos B→A→D para outliers deficitarios
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica asignaciones.
FUNCIÓN: buscar cadenas simultáneas de dos transferencias unitarias entre tres distritos de la misma provincia:
B cede una unidad a A y A cede otra unidad a D (outlier deficitario). Evalúa exclusivamente el estado final,
exigiendo contigüidad de B, A y D, suelo/techo duro, mantenimiento de K/cuotas y mejora lexicográfica de la
función poblacional. Las dos unidades transferidas deben ser distintas y cada una tocar su receptor final.
MOTIVO: EXT-16 probó paquetes entrantes directos de tamaño 1–3 hacia d14/d25 y obtuvo cero candidatos válidos.
La hipótesis mínima restante es que el donante A sí puede alimentar D si recibe simultáneamente compensación
de un tercer distrito B. Se prueba primero 1→1 por tramo antes de ampliar combinatoria.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, io, json, sys, zipfile
from collections import deque
from pathlib import Path
import geopandas as gpd

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg


def load_geo(path):
    p=Path(path)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            n=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            raw=z.read(n); return gpd.read_file(io.BytesIO(raw)),json.loads(raw.decode('utf-8'))
    raw=Path(p).read_text(encoding='utf-8');return gpd.read_file(p),json.loads(raw)


def connected(nodes,adj):
    nodes=set(nodes)
    if not nodes:return False
    s=next(iter(nodes));seen={s};q=deque([s])
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)


def objective(dpop,target,floor,cap,tol):
    vals=list(dpop.values())
    hard=sum(p<floor or p>cap for p in vals)
    outside=sum(abs(p-target)>tol for p in vals)
    mx=max(abs(p-target)/target for p in vals)
    sq=sum(((p-target)/target)**2 for p in vals)
    return (hard,outside,mx,sq)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out',required=True);ap.add_argument('--top',type=int,default=100);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');val=cfg.get('validation',{}) or {}
    G=json.loads(Path(s5['in_graph_json']).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};sadj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v']);sadj[u].add(v);sadj[v].add(u)
    g,raw=load_geo(a.geojson);idf=s5.get('id_field','CUSEC_KEY');did=s5.get('district_field','district_id');provf=s5.get('province_field','CPRO');munf=s5.get('municipality_field','CUMUN')
    g[idf]=g[idf].astype(str);g[did]=g[did].astype(int);g[provf]=g[provf].astype(str).str.zfill(2)
    props={str(f.get('properties',{}).get(idf)):f.get('properties',{}) for f in raw.get('features',[])}
    if 'ddd_unit_id' not in g.columns:g['ddd_unit_id']=g[idf].map(lambda x:props.get(str(x),{}).get('ddd_unit_id'))
    else:
        miss=g['ddd_unit_id'].isna()
        if miss.any():g.loc[miss,'ddd_unit_id']=g.loc[miss,idf].map(lambda x:props.get(str(x),{}).get('ddd_unit_id'))
    if g['ddd_unit_id'].isna().any():raise SystemExit('No se pudo recuperar ddd_unit_id')
    g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    sec_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_mun={u:sorted(set(x[munf].astype(str))) for u,x in g.groupby('ddd_unit_id')}
    uadj={u:set() for u in unit_nodes}
    for n,u in sec_unit.items():
        for nb in sadj.get(n,set()):
            v=sec_unit.get(nb)
            if v is not None and v!=u:uadj[u].add(v)
    d_units={d:set(x.ddd_unit_id.astype(str)) for d,x in g.groupby(did)};dpop={d:sum(unit_pop[u] for u in us) for d,us in d_units.items()};dprov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_units}
    total=sum(pop.values());K=len(d_units);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12));lower=target-tol;upper=target+tol;base_obj=objective(dpop,target,floor,cap,tol)
    deficits=sorted(d for d,p in dpop.items() if p<lower);results=[]
    for D in deficits:
        dus=d_units[D];As=sorted({unit_dist[v] for u in dus for v in uadj.get(u,set()) if unit_dist[v]!=D and dprov.get(unit_dist[v])==dprov[D]})
        cand=[]
        for A in As:
            aus=d_units[A]
            outgoing=sorted({u for u in aus if any(v in dus for v in uadj.get(u,set()))},key=str)
            for x in outgoing:
                # x: A -> D. Its removal may disconnect/underfill A temporarily; final A will be tested after y enters.
                D_final=dus|{x}
                if not connected(D_final,uadj):continue
                Bs=sorted({unit_dist[v] for u in aus for v in uadj.get(u,set()) if unit_dist[v] not in (A,D) and dprov.get(unit_dist[v])==dprov[A]})
                for B in Bs:
                    bus=d_units[B]
                    incoming=sorted({y for y in bus if any(v in aus for v in uadj.get(y,set()))},key=str)
                    for y in incoming:
                        if y==x:continue
                        B_final=bus-{y}
                        if not B_final or not connected(B_final,uadj):continue
                        A_final=(aus-{x})|{y}
                        if not A_final or not connected(A_final,uadj):continue
                        # y must touch final A, not only x which leaves A.
                        if not any(v in A_final for v in uadj.get(y,set())):continue
                        pD=dpop[D]+unit_pop[x];pA=dpop[A]-unit_pop[x]+unit_pop[y];pB=dpop[B]-unit_pop[y]
                        if not(floor<=pD<=cap and floor<=pA<=cap and floor<=pB<=cap):continue
                        trial=dict(dpop);trial[D]=pD;trial[A]=pA;trial[B]=pB;obj=objective(trial,target,floor,cap,tol)
                        closes=lower<=pD<=upper
                        cand.append({'D':D,'A':A,'B':B,'A_to_D_unit':x,'B_to_A_unit':y,'A_to_D_population':unit_pop[x],'B_to_A_population':unit_pop[y],'A_to_D_municipalities':unit_mun[x],'B_to_A_municipalities':unit_mun[y],'before':{'D':dpop[D],'A':dpop[A],'B':dpop[B]},'after':{'D':pD,'A':pA,'B':pB},'closes_D':closes,'population_objective':list(obj),'improves_global_objective':obj<base_obj})
        cand.sort(key=lambda z:(not z['closes_D'],tuple(z['population_objective']),abs(z['A_to_D_population']-(lower-dpop[D])),z['A_to_D_population']+z['B_to_A_population'],z['A'],z['B'],str(z['A_to_D_unit']),str(z['B_to_A_unit'])))
        results.append({'district':D,'population':dpop[D],'needed_to_lower_tolerance':lower-dpop[D],'neighbor_districts':As,'valid_relays':len(cand),'closing_relays':sum(z['closes_D'] for z in cand),'improving_relays':sum(z['improves_global_objective'] for z in cand),'best':cand[:a.top]})
    out={'K':K,'target':target,'floor':floor,'cap':cap,'tolerance':tol,'lower_tolerance':lower,'base_population_objective':list(base_obj),'deficit_outliers':results}
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'base':out['base_population_objective'],'outliers':[{'district':r['district'],'need':round(r['needed_to_lower_tolerance'],3),'valid':r['valid_relays'],'closing':r['closing_relays'],'improving':r['improving_relays'],'best':r['best'][:5]} for r in results]},ensure_ascii=False))

if __name__=='__main__':main()
