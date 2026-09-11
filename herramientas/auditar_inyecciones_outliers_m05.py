#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: auditar_inyecciones_outliers_m05.py
VERSIÓN: 1.0.0
NOMBRE: Auditor de paquetes entrantes hacia outliers M05
FECHA: 2026-09-11
ESTADO: diagnóstico; no modifica asignaciones.
FUNCIÓN: para cada distrito fuera de tolerancia por déficit, enumerar paquetes conexos de 1 a N unidades DDD
procedentes de un único distrito vecino de la misma provincia que puedan transferirse completos al outlier,
preservando la conectividad del donante y receptor, el suelo/techo duro y las cuotas provinciales.
CRITERIO: prioriza cerrar el outlier; después minimizar el máximo desvío global y el error cuadrático.
MOTIVO: EXT-15 demostró que d14 y d25 no pueden ceder lóbulos porque caerían por debajo del suelo duro.
Ambos necesitan recibir muy poca población para entrar en ±10 %, por lo que el operador correcto a probar es
una inyección conexa desde un vecino, no otro swap simétrico ni más pulido global.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, io, itertools, json, sys, zipfile
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
            raw=z.read(n)
            return gpd.read_file(io.BytesIO(raw)),json.loads(raw.decode('utf-8'))
    return gpd.read_file(p),json.loads(Path(p).read_text(encoding='utf-8'))


def connected(nodes,adj):
    nodes=set(nodes)
    if not nodes:return False
    s=next(iter(nodes));seen={s};q=deque([s])
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)


def pop_objective(dpop,target,floor,cap,tol):
    vals=list(dpop.values())
    hard=sum(p<floor or p>cap for p in vals)
    outside=sum(abs(p-target)>tol for p in vals)
    mx=max(abs(p-target)/target for p in vals)
    sq=sum(((p-target)/target)**2 for p in vals)
    return (hard,outside,mx,sq)


def bundle_connected(bundle,uadj):
    return len(bundle)==1 or connected(bundle,uadj)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out',required=True);ap.add_argument('--max-size',type=int,default=3);ap.add_argument('--top',type=int,default=100);a=ap.parse_args()
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
    sec_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_prov={u:str(x[provf].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_mun={u:sorted(set(x[munf].astype(str))) for u,x in g.groupby('ddd_unit_id')}
    uadj={u:set() for u in unit_nodes}
    for n,u in sec_unit.items():
        for nb in sadj.get(n,set()):
            v=sec_unit.get(nb)
            if v is not None and v!=u:uadj[u].add(v)
    d_units={d:set(x.ddd_unit_id.astype(str)) for d,x in g.groupby(did)};dpop={d:sum(unit_pop[u] for u in us) for d,us in d_units.items()};dprov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_units}
    total=sum(pop.values());K=len(d_units);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12));lower=target-tol;upper=target+tol
    base_obj=pop_objective(dpop,target,floor,cap,tol)
    deficits=sorted(d for d,p in dpop.items() if p<lower)
    results=[]
    for dest in deficits:
        dus=d_units[dest];boundary_sources={unit_dist[v] for u in dus for v in uadj.get(u,set()) if unit_dist[v]!=dest and dprov.get(unit_dist[v])==dprov[dest]}
        candidates=[]
        for src in sorted(boundary_sources):
            sus=d_units[src]
            boundary=sorted({u for u in sus if any(v in dus for v in uadj.get(u,set()))},key=str)
            # Amplía a unidades contiguas dentro del donante hasta profundidad N-1 para permitir paquetes conexos.
            pool=set(boundary);front=set(boundary)
            for _ in range(max(0,a.max_size-1)):
                nxt={v for u in front for v in uadj.get(u,set()) if v in sus and v not in pool};pool|=nxt;front=nxt
            pool=sorted(pool,key=str)
            for size in range(1,min(a.max_size,len(pool))+1):
                for comb in itertools.combinations(pool,size):
                    bundle=set(comb)
                    if not(bundle&set(boundary)):continue
                    if not bundle_connected(bundle,uadj):continue
                    donor_after=sus-bundle
                    if not donor_after or not connected(donor_after,uadj):continue
                    recv_after=dus|bundle
                    if not connected(recv_after,uadj):continue
                    bp=sum(unit_pop[u] for u in bundle);ps=dpop[src]-bp;pd=dpop[dest]+bp
                    if not(floor<=ps<=cap and floor<=pd<=cap):continue
                    trial=dict(dpop);trial[src]=ps;trial[dest]=pd;obj=pop_objective(trial,target,floor,cap,tol)
                    closes=lower<=pd<=upper
                    improves=obj<base_obj
                    candidates.append({'from':src,'to':dest,'units':sorted(bundle,key=str),'unit_count':size,'population':bp,'municipalities':sorted({m for u in bundle for m in unit_mun[u]}),'donor_before':dpop[src],'donor_after':ps,'receiver_before':dpop[dest],'receiver_after':pd,'closes_receiver':closes,'population_objective':list(obj),'improves_global_population_objective':improves})
        candidates.sort(key=lambda x:(not x['closes_receiver'],tuple(x['population_objective']),x['unit_count'],x['population'],x['from'],x['units']))
        results.append({'district':dest,'population':dpop[dest],'needed_to_lower_tolerance':lower-dpop[dest],'neighbor_districts':sorted(boundary_sources),'valid_incoming_bundles':len(candidates),'closing_bundles':sum(x['closes_receiver'] for x in candidates),'best':candidates[:a.top]})
    out={'K':K,'target':target,'floor':floor,'cap':cap,'tolerance':tol,'lower_tolerance':lower,'upper_tolerance':upper,'base_population_objective':list(base_obj),'deficit_outliers':results}
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'base_population_objective':out['base_population_objective'],'outliers':[{'district':x['district'],'need':round(x['needed_to_lower_tolerance'],3),'neighbors':x['neighbor_districts'],'valid':x['valid_incoming_bundles'],'closing':x['closing_bundles'],'best':x['best'][:5]} for x in results]},ensure_ascii=False))

if __name__=='__main__':main()
