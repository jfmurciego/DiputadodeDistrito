#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_relevos_bundles_outliers_m05.py
VERSIÓN: 1.0.0
NOMBRE: Auditor de relevos asimétricos 1↔2 para outliers
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica asignaciones.
FUNCIÓN: buscar cadenas simultáneas B→A→D en las que exactamente una pata mueve una unidad DDD y la otra
un paquete conexo de dos unidades DDD. Se prueban las dos familias mínimas: B(1)→A + A(2)→D y
B(2)→A + A(1)→D. El estado final debe conservar conectividad de B/A/D, provincia y suelo/techo duro.
MOTIVO: EXT-16 descartó inyecciones directas 1–3; EXT-17 descartó relevos unitarios 1→1. Antes de abandonar
la optimización local se prueba el siguiente aumento combinatorio mínimo, sin abrir 2→2 ni cadenas más largas.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse,io,itertools,json,sys,zipfile
from collections import deque
from pathlib import Path
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg

def load_geo(path):
 p=Path(path)
 with zipfile.ZipFile(p) as z:
  n=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'));raw=z.read(n)
 return gpd.read_file(io.BytesIO(raw)),json.loads(raw.decode('utf-8'))

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
 vals=list(dpop.values());return (sum(p<floor or p>cap for p in vals),sum(abs(p-target)>tol for p in vals),max(abs(p-target)/target for p in vals),sum(((p-target)/target)**2 for p in vals))

def conn_pairs(pool,adj):
 p=sorted(pool,key=str);return [set(x) for x in itertools.combinations(p,2) if x[1] in adj.get(x[0],set())]

def touches(bundle,target,adj):return any(v in target for u in bundle for v in adj.get(u,set()))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out',required=True);ap.add_argument('--top',type=int,default=100);a=ap.parse_args()
 cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');val=cfg.get('validation',{}) or {}
 G=json.loads(Path(s5['in_graph_json']).read_text());pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};sadj={n:set() for n in pop}
 for e in G['edges']:
  u,v=str(e['u']),str(e['v']);sadj[u].add(v);sadj[v].add(u)
 g,raw=load_geo(a.geojson);idf=s5.get('id_field','CUSEC_KEY');did=s5.get('district_field','district_id');provf=s5.get('province_field','CPRO');munf=s5.get('municipality_field','CUMUN')
 g[idf]=g[idf].astype(str);g[did]=g[did].astype(int);g[provf]=g[provf].astype(str).str.zfill(2);props={str(f['properties'].get(idf)):f['properties'] for f in raw['features']}
 if 'ddd_unit_id' not in g.columns:g['ddd_unit_id']=g[idf].map(lambda x:props.get(str(x),{}).get('ddd_unit_id'))
 else:
  m=g['ddd_unit_id'].isna()
  if m.any():g.loc[m,'ddd_unit_id']=g.loc[m,idf].map(lambda x:props.get(str(x),{}).get('ddd_unit_id'))
 if g['ddd_unit_id'].isna().any():raise SystemExit('No se pudo recuperar ddd_unit_id')
 g.ddd_unit_id=g.ddd_unit_id.astype(str);sec_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf]) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_mun={u:sorted(set(x[munf].astype(str))) for u,x in g.groupby('ddd_unit_id')}
 uadj={u:set() for u in unit_nodes}
 for n,u in sec_unit.items():
  for nb in sadj.get(n,set()):
   v=sec_unit.get(nb)
   if v is not None and v!=u:uadj[u].add(v)
 d_units={d:set(x.ddd_unit_id) for d,x in g.groupby(did)};dpop={d:sum(unit_pop[u] for u in us) for d,us in d_units.items()};dprov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_units}
 total=sum(pop.values());K=len(d_units);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12));lower=target-tol;base=objective(dpop,target,floor,cap,tol);results=[]
 for D in sorted(d for d,p in dpop.items() if p<lower):
  dus=d_units[D];As=sorted({unit_dist[v] for u in dus for v in uadj[u] if unit_dist[v]!=D and dprov.get(unit_dist[v])==dprov[D]});cand=[]
  for A in As:
   aus=d_units[A];a_boundary={u for u in aus if touches({u},dus,uadj)};a_pairs=conn_pairs(aus,uadj)
   Bs=sorted({unit_dist[v] for u in aus for v in uadj[u] if unit_dist[v] not in (A,D) and dprov.get(unit_dist[v])==dprov[A]})
   for B in Bs:
    bus=d_units[B];b_boundary={u for u in bus if touches({u},aus,uadj)};b_pairs=conn_pairs(bus,uadj)
    patterns=[]
    for x in sorted(a_boundary,key=str):
     for yp in b_pairs:
      if touches(yp,aus-{x},uadj):patterns.append(('B2_A1',{x},yp))
    for xp in a_pairs:
     if not touches(xp,dus,uadj):continue
     for y in sorted(b_boundary,key=str):patterns.append(('B1_A2',xp,{y}))
    for kind,xs,ys in patterns:
     Bf=bus-ys;Af=(aus-xs)|ys;Df=dus|xs
     if not Bf or not Af or not connected(Bf,uadj) or not connected(Af,uadj) or not connected(Df,uadj):continue
     if not touches(xs,dus,uadj) or not touches(ys,Af,uadj):continue
     px=sum(unit_pop[u] for u in xs);py=sum(unit_pop[u] for u in ys);pD=dpop[D]+px;pA=dpop[A]-px+py;pB=dpop[B]-py
     if not(floor<=pD<=cap and floor<=pA<=cap and floor<=pB<=cap):continue
     trial=dict(dpop);trial[D]=pD;trial[A]=pA;trial[B]=pB;obj=objective(trial,target,floor,cap,tol)
     cand.append({'pattern':kind,'D':D,'A':A,'B':B,'A_to_D_units':sorted(xs),'B_to_A_units':sorted(ys),'A_to_D_population':px,'B_to_A_population':py,'A_to_D_municipalities':sorted({m for u in xs for m in unit_mun[u]}),'B_to_A_municipalities':sorted({m for u in ys for m in unit_mun[u]}),'before':{'D':dpop[D],'A':dpop[A],'B':dpop[B]},'after':{'D':pD,'A':pA,'B':pB},'closes_D':pD>=lower,'population_objective':list(obj),'improves_global_objective':obj<base})
  cand.sort(key=lambda z:(not z['closes_D'],tuple(z['population_objective']),len(z['A_to_D_units'])+len(z['B_to_A_units']),z['A'],z['B'],z['A_to_D_units'],z['B_to_A_units']))
  results.append({'district':D,'needed':lower-dpop[D],'valid_relays':len(cand),'closing_relays':sum(c['closes_D'] for c in cand),'improving_relays':sum(c['improves_global_objective'] for c in cand),'best':cand[:a.top]})
 out={'base_population_objective':list(base),'target':target,'floor':floor,'lower_tolerance':lower,'results':results};p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'base':out['base_population_objective'],'results':[{'district':r['district'],'valid':r['valid_relays'],'closing':r['closing_relays'],'improving':r['improving_relays'],'best':r['best'][:5]} for r in results]},ensure_ascii=False))
if __name__=='__main__':main()
