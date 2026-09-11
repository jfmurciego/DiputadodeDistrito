#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: pulir_topologia_m04.py
VERSIÓN: 1.0.0
NOMBRE: Pulido topológico protegido de M04
FECHA: 2026-09-11
ESTADO: experimental; no forma parte del motor productivo.
FUNCIÓN: aplicar iterativamente movimientos unitarios de frontera que reduzcen estrictamente la fragilidad
topológica de una solución M04, preservando provincia, contigüidad y restricciones poblacionales duras.
CRITERIO DE GUARDA: hard=0; número de distritos fuera de tolerancia no aumenta; máximo desvío relativo no
aumenta. Dentro de esos límites se elige lexicográficamente la mejor firma topológica disponible.
ENTRADAS: configuración territorial y GeoJSON ZIP M04 con ddd_unit_id reparado.
SALIDAS: GeoJSON ZIP con district_id pulido y JSON de auditoría antes/después y movimientos aceptados.
MOTIVO: EXT-11 mostró que M05 mejora población pero empeora fragilidad; EXT-12 encontró 123 movimientos M04
que reducen fragilidad, 70 de ellos protegidos por las restricciones poblacionales relevantes. Esta herramienta
prueba si un pulido previo a M05 abre un estado territorial mejor sin modificar aún M04/M05 productivos.
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


def read_zip_raw(path):
    p=Path(path)
    with zipfile.ZipFile(p) as z:
        name=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
        raw=json.loads(z.read(name).decode('utf-8'))
    return name,raw


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


def signature(d_units,uadj,unit_pop,target):
    districts_with=0; total_arts=0; vulnerable_sum=0; max_vulnerable=0
    for us0 in d_units.values():
        us=set(us0);ia={u:{v for v in uadj.get(u,set()) if v in us} for u in us};arts=0
        for cut in us:
            rest=us-{cut}
            if len(rest)<=1:continue
            rem=set(rest);cc=[]
            while rem:
                s=next(iter(rem));rem.remove(s);seen={s};q=deque([s])
                while q:
                    x=q.popleft()
                    for y in ia.get(x,set()):
                        if y in rem:rem.remove(y);seen.add(y);q.append(y)
                cc.append(seen)
            if len(cc)<=1:continue
            arts+=1
            small=min(sum(unit_pop[u] for u in c) for c in cc)
            vulnerable_sum+=small;max_vulnerable=max(max_vulnerable,small)
        if arts:districts_with+=1
        total_arts+=arts
    return (districts_with,total_arts,round(vulnerable_sum/target,12),round(max_vulnerable/target,12))


def pop_objective(dpop,target,floor,cap,tol):
    vals=list(dpop.values())
    hard=sum(p<floor or p>cap for p in vals)
    outside=sum(abs(p-target)>tol for p in vals)
    mx=max(abs(p-target)/target for p in vals)
    sq=sum(((p-target)/target)**2 for p in vals)
    return (hard,outside,round(mx,12),round(sq,12))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--geojson',required=True);ap.add_argument('--out-geojson',required=True);ap.add_argument('--out-report',required=True);ap.add_argument('--max-moves',type=int,default=50);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');val=cfg.get('validation',{}) or {}
    graph_path=s5.get('in_graph_json') or s4.get('in_graph_json');G=json.loads(Path(graph_path).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};sadj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v']);sadj[u].add(v);sadj[v].add(u)
    g=load_geo(a.geojson);idf=s5.get('id_field') or s4.get('id_field','CUSEC_KEY');did=s5.get('district_field','district_id');provf=s5.get('province_field') or s4.get('province_field','CPRO');munf=s5.get('municipality_field','CUMUN')
    g[idf]=g[idf].astype(str);g[did]=g[did].astype(int);g[provf]=g[provf].astype(str).str.zfill(2)
    raw_name,raw=read_zip_raw(a.geojson)
    raw_props={str(f.get('properties',{}).get(idf)):f.get('properties',{}) for f in raw.get('features',[])}
    if 'ddd_unit_id' not in g.columns:
        g['ddd_unit_id']=g[idf].map(lambda x:raw_props.get(str(x),{}).get('ddd_unit_id'))
    else:
        missing=g['ddd_unit_id'].isna()
        if missing.any():g.loc[missing,'ddd_unit_id']=g.loc[missing,idf].map(lambda x:raw_props.get(str(x),{}).get('ddd_unit_id'))
    if g['ddd_unit_id'].isna().any():raise SystemExit('No se pudo recuperar ddd_unit_id para todas las secciones')
    g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    sec_unit=dict(zip(g[idf],g.ddd_unit_id));unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop[n] for n in ns) for u,ns in unit_nodes.items()};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_prov={u:str(x[provf].iloc[0]) for u,x in g.groupby('ddd_unit_id')};unit_mun={u:sorted(set(x[munf].astype(str))) if munf in x.columns else [] for u,x in g.groupby('ddd_unit_id')}
    uadj={u:set() for u in unit_nodes}
    for n,u in sec_unit.items():
        for nb in sadj.get(n,set()):
            v=sec_unit.get(nb)
            if v is not None and v!=u:uadj[u].add(v)
    d_units={d:set(x.ddd_unit_id.astype(str)) for d,x in g.groupby(did)};dpop={d:sum(unit_pop[u] for u in us) for d,us in d_units.items()};dprov={d:str(g[g[did]==d][provf].iloc[0]) for d in d_units}
    total=sum(pop.values());K=len(d_units);target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12))
    before_pop=pop_objective(dpop,target,floor,cap,tol);before_frag=signature(d_units,uadj,unit_pop,target);moves=[]
    for iteration in range(a.max_moves):
        cur_pop=pop_objective(dpop,target,floor,cap,tol);cur_frag=signature(d_units,uadj,unit_pop,target);best=None
        for u,a0 in sorted(unit_dist.items(),key=lambda x:str(x[0])):
            if len(d_units[a0])<=1:continue
            neigh=sorted({unit_dist[v] for v in uadj.get(u,set()) if unit_dist[v]!=a0 and dprov.get(unit_dist[v])==dprov[a0]})
            if not neigh:continue
            donor=d_units[a0]-{u}
            if not connected(donor,uadj):continue
            for b in neigh:
                recv=d_units[b]|{u}
                if not connected(recv,uadj):continue
                pa=dpop[a0]-unit_pop[u];pb=dpop[b]+unit_pop[u]
                if not(floor<=pa<=cap and floor<=pb<=cap):continue
                trial_pop=dict(dpop);trial_pop[a0]=pa;trial_pop[b]=pb
                pobj=pop_objective(trial_pop,target,floor,cap,tol)
                if not(pobj[0]==0 and pobj[1]<=cur_pop[1] and pobj[2]<=cur_pop[2]):continue
                trial_units={d:set(us) for d,us in d_units.items()};trial_units[a0].remove(u);trial_units[b].add(u)
                frag=signature(trial_units,uadj,unit_pop,target)
                if not frag<cur_frag:continue
                key=(frag,pobj[1],pobj[2],pobj[3],str(u),a0,b)
                if best is None or key<best[0]:best=(key,u,a0,b,pa,pb,pobj,frag)
        if best is None:break
        _,u,a0,b,pa,pb,pobj,frag=best
        d_units[a0].remove(u);d_units[b].add(u);dpop[a0]=pa;dpop[b]=pb;unit_dist[u]=b
        moves.append({'iteration':iteration+1,'unit':u,'from':a0,'to':b,'population':unit_pop[u],'municipalities':unit_mun[u],'population_objective':list(pobj),'fragility_signature':list(frag),'new_populations':[pa,pb]})
    after_pop=pop_objective(dpop,target,floor,cap,tol);after_frag=signature(d_units,uadj,unit_pop,target)
    section_new_dist={n:unit_dist[u] for n,u in sec_unit.items()}
    for f in raw.get('features',[]):
        p=f.get('properties',{});sid=str(p.get(idf))
        if sid in section_new_dist:p[did]=int(section_new_dist[sid])
    outp=Path(a.out_geojson);outp.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(outp,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr(raw_name,json.dumps(raw,ensure_ascii=False,separators=(',',':')))
    report={'version':'1.0.0','target':target,'floor':floor,'cap':cap,'tolerance':tol,'max_moves':a.max_moves,'accepted_moves':len(moves),'before_population_objective':list(before_pop),'after_population_objective':list(after_pop),'before_fragility_signature':list(before_frag),'after_fragility_signature':list(after_frag),'moves':moves}
    rp=Path(a.out_report);rp.parent.mkdir(parents=True,exist_ok=True);rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('accepted_moves','before_population_objective','after_population_objective','before_fragility_signature','after_fragility_signature')},ensure_ascii=False))

if __name__=='__main__':main()
