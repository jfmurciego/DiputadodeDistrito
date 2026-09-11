#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_relevo_d25_2x2.py
VERSIÓN: 1.0.0
NOMBRE: Probe dirigido 2→2 para cerrar el distrito 25
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica asignaciones.
FUNCIÓN: sobre el estado m50+M05 fija el tramo A→D identificado por EXT-18: distrito 38 cede las unidades
DDD 192 y 58 al distrito deficitario 25. Enumera exclusivamente paquetes conexos de dos unidades desde cada
distrito B vecino de 38 hacia 38, evaluando simultáneamente el estado final B→38→25.
RESTRICCIONES: misma provincia, conectividad final de B/38/25, suelo/techo duro y conservación de K.
CRITERIO: prioriza reducción de outside_10, después máximo desvío y error cuadrático.
MOTIVO: EXT-18 dejó d38 en 14.548 al recibir una sola unidad de 995 habitantes desde d22, apenas 36,8 hab.
por debajo del límite de -10 %. Un segundo componente de compensación puede cerrar d25 sin trasladar el outlier.
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

D,A=25,38
OUT={'192','58'}

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
 if not OUT.issubset(d_units[A]):raise SystemExit(f'Las unidades {sorted(OUT)} ya no pertenecen al distrito {A}')
 total=sum(pop.values());K=len(d_units);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12));lower=target-tol;base=objective(dpop,target,floor,cap,tol)
 Df=d_units[D]|OUT;A_base=d_units[A]-OUT
 if not connected(Df,uadj):raise SystemExit('El tramo fijo 38→25 desconecta el receptor')
 p_out=sum(unit_pop[u] for u in OUT);Bs=sorted({unit_dist[v] for u in A_base for v in uadj[u] if unit_dist[v] not in (A,D) and dprov.get(unit_dist[v])==dprov[A]});cand=[]
 for B in Bs:
  bus=d_units[B];pool=sorted({u for u in bus if any(v in A_base for v in uadj[u])},key=str)
  # Añadir un salto interior para permitir parejas en las que solo una unidad toca originalmente a A.
  ext=set(pool)
  for u in pool:ext|={v for v in uadj[u] if v in bus}
  for y1,y2 in itertools.combinations(sorted(ext,key=str),2):
   ys={y1,y2}
   if y2 not in uadj.get(y1,set()):continue
   Bf=bus-ys
   if not Bf or not connected(Bf,uadj):continue
   Af=A_base|ys
   if not connected(Af,uadj):continue
   if not any(v in A_base for y in ys for v in uadj[y]):continue
   py=sum(unit_pop[y] for y in ys);pD=dpop[D]+p_out;pA=dpop[A]-p_out+py;pB=dpop[B]-py
   if not(floor<=pD<=cap and floor<=pA<=cap and floor<=pB<=cap):continue
   trial=dict(dpop);trial[D]=pD;trial[A]=pA;trial[B]=pB;obj=objective(trial,target,floor,cap,tol)
   cand.append({'D':D,'A':A,'B':B,'A_to_D_units':sorted(OUT),'B_to_A_units':sorted(ys),'A_to_D_population':p_out,'B_to_A_population':py,'B_to_A_municipalities':sorted({m for y in ys for m in unit_mun[y]}),'before':{'D':dpop[D],'A':dpop[A],'B':dpop[B]},'after':{'D':pD,'A':pA,'B':pB},'outside_10_after':obj[1],'population_objective':list(obj),'improves_global_objective':obj<base,'all_three_within_tolerance':all(abs(p-target)<=tol for p in (pD,pA,pB))})
 cand.sort(key=lambda z:(tuple(z['population_objective']),not z['all_three_within_tolerance'],abs(z['B_to_A_population']-(p_out-(dpop[A]-lower))),z['B'],z['B_to_A_units']))
 out={'base_population_objective':list(base),'target':target,'floor':floor,'lower_tolerance':lower,'fixed_A_to_D':{'A':A,'D':D,'units':sorted(OUT),'population':p_out},'B_candidates':Bs,'valid_relays':len(cand),'relays_reducing_outside':sum(c['outside_10_after']<base[1] for c in cand),'globally_improving':sum(c['improves_global_objective'] for c in cand),'best':cand[:a.top]};p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'base':out['base_population_objective'],'valid':out['valid_relays'],'reducing_outside':out['relays_reducing_outside'],'globally_improving':out['globally_improving'],'best':out['best'][:10]},ensure_ascii=False))
if __name__=='__main__':main()
