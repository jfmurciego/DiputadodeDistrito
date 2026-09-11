#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.2.0
NOMBRE DE VERSIÓN: Optimización por unidades territoriales protegidas
FECHA: 2026-09-11
ESTADO: candidato
FUNCIÓN: optimizar población sin cruzar provincias ni romper las unidades municipales/urbanas construidas por M04.
ENTRADAS: grafo M03 y solución M04 v7.2.0 con ddd_unit_id y ddd_closed_urban.
SALIDAS: asignación optimizada y reporte.
REGLAS DURAS: provincia única por distrito; movimientos de unidad completa; distritos urbanos cerrados no reciben ni ceden unidades; contigüidad estricta; suelo/techo poblacional.
OBJETIVO: primero eliminar violaciones duras; después minimizar distritos fuera de ±12%; después máximo desvío y error cuadrático.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.1.0.py
"""
from __future__ import annotations
import argparse,collections,io,json,random,sys,zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg,require

def load_geo(path):
    p=Path(path)
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            m=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            return gpd.read_file(io.BytesIO(z.read(m)))
    return gpd.read_file(p)

def write_geo(gdf,path):
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.parent/(out.stem.replace('.geojson','')+'.geojson')
    gdf.to_file(tmp,driver='GeoJSON')
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)

def connected(nodes,adj):
    nodes=set(nodes)
    if not nodes:return False
    seen={next(iter(nodes))};q=collections.deque(seen)
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args();cfg=load_params_yaml(a.params);s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');val=cfg.get('validation',{}) or {}
    ing=require(s5.get('in_graph_json'),'Falta M05 grafo');ingeo=require(s5.get('in_geojson'),'Falta M05 geojson');idf=require(s5.get('id_field'),'Falta id');popf=require(s5.get('pop_field'),'Falta población');did=s5.get('district_field','district_id');provf=s5.get('province_field','CPRO');out=require(s5.get('out_geojson'),'Falta salida');report_path=s5.get('out_report','');iters=int(s5.get('iters',20000));rng=random.Random(int(s5.get('seed',12345)))
    G=json.loads(Path(ing).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};adj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v']);
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    g=load_geo(ingeo);g[idf]=g[idf].astype(str)
    for c in (did,provf,'ddd_unit_id','ddd_closed_urban'):
        if c not in g.columns:raise SystemExit(f'M05 requiere {c}; ejecutar M04 v7.2.0')
    g[provf]=g[provf].astype(str).str.zfill(2);g[did]=pd.to_numeric(g[did],errors='raise').astype(int);g['ddd_unit_id']=g['ddd_unit_id'].astype(str)
    section_to_unit=dict(zip(g[idf],g['ddd_unit_id']));unit_nodes={u:set(x[idf].astype(str)) for u,x in g.groupby('ddd_unit_id')};unit_pop={u:sum(pop.get(n,0) for n in ns) for u,ns in unit_nodes.items()};unit_prov={u:str(x[provf].iloc[0]).zfill(2) for u,x in g.groupby('ddd_unit_id')};unit_dist={u:int(x[did].iloc[0]) for u,x in g.groupby('ddd_unit_id')}
    if any(x[did].nunique()!=1 for _,x in g.groupby('ddd_unit_id')):raise SystemExit('M05: una unidad territorial llega partida entre distritos')
    K=int(g[did].nunique());total=sum(pop.values());target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));tol=target*float(val.get('target_tolerance_ratio',.12))
    d_units={d:set() for d in sorted(g[did].unique())};d_nodes={d:set() for d in d_units};d_pop={d:0 for d in d_units};d_prov={};d_closed={}
    for u,d in unit_dist.items():d_units[d].add(u);d_nodes[d]|=unit_nodes[u];d_pop[d]+=unit_pop[u];d_prov.setdefault(d,unit_prov[u])
    for d,x in g.groupby(did):
        ps=set(x[provf].astype(str).str.zfill(2));
        if len(ps)!=1:raise SystemExit(f'M05 entrada inválida: distrito {d} cruza provincias {sorted(ps)}')
        d_closed[int(d)]=bool(x['ddd_closed_urban'].all())
    # adyacencia entre unidades, derivada del grafo de secciones
    uadj={u:set() for u in unit_nodes}
    for n in pop:
        u=section_to_unit.get(n)
        if u is None:continue
        for nb in adj.get(n,set()):
            v=section_to_unit.get(nb)
            if v is not None and v!=u:uadj[u].add(v)
    def obj(values):
        vals=list(values.values());hard=sum(p<floor or p>cap for p in vals);hard_mag=sum(max(0,floor-p,p-cap) for p in vals);outside=sum(abs(p-target)>tol for p in vals);maxdev=max(abs(p-target)/target for p in vals);sq=sum(((p-target)/target)**2 for p in vals)
        return (hard,round(hard_mag/target,12),outside,round(maxdev,12),round(sq,12))
    def candidates():
        out=[]
        for u,d0 in unit_dist.items():
            if d_closed[d0]:continue
            for v in uadj[u]:
                d1=unit_dist[v]
                if d1==d0 or d_closed[d1] or d_prov[d1]!=unit_prov[u]:continue
                out.append((u,d0,d1))
        return out
    start=obj(d_pop);accepted=0
    for _ in range(iters):
        cand=candidates()
        if not cand:break
        u,d0,d1=rng.choice(cand)
        if len(d_units[d0])<=1:continue
        remaining=d_nodes[d0]-unit_nodes[u];newrecv=d_nodes[d1]|unit_nodes[u]
        if not connected(remaining,adj) or not connected(newrecv,adj):continue
        trial=dict(d_pop);trial[d0]-=unit_pop[u];trial[d1]+=unit_pop[u]
        if obj(trial)<obj(d_pop):
            d_units[d0].remove(u);d_units[d1].add(u);d_nodes[d0]=remaining;d_nodes[d1]=newrecv;d_pop=trial;unit_dist[u]=d1;accepted+=1
    # reconstrucción sección->distrito y guardas duras
    sec_assign={n:unit_dist[u] for u,ns in unit_nodes.items() for n in ns};g[did]=g[idf].map(sec_assign).astype(int)
    province_viol=[]
    for d,x in g.groupby(did):
        ps=sorted(set(x[provf].astype(str).str.zfill(2)))
        if len(ps)!=1:province_viol.append({'district_id':int(d),'provinces':ps})
        if not connected(set(x[idf].astype(str)),adj):raise SystemExit(f'M05 produjo distrito desconectado {d}')
    if province_viol:raise SystemExit(f'M05 produjo cruces provinciales: {province_viol}')
    write_geo(g,out);final=obj(d_pop)
    rep={'module':'05','version':'7.2.0','K':K,'total_pop':int(total),'target':target,'population_floor':floor,'population_cap':cap,'tolerance_absolute':tol,'objective_start':list(start),'objective_final':list(final),'districts_below_floor':sum(p<floor for p in d_pop.values()),'districts_above_cap':sum(p>cap for p in d_pop.values()),'districts_outside_tolerance':sum(abs(p-target)>tol for p in d_pop.values()),'best_max_rel_dev':final[3],'accepted_unit_moves':accepted,'atomic_units':len(unit_nodes),'province_violations':province_viol,'seed':int(s5.get('seed',12345)),'iters':iters}
    if report_path:Path(report_path).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"[Módulo 5] OK v7.2.0 hard={final[0]} fuera_12={final[2]} max_rel_dev={final[3]:.4f} movimientos_unidad={accepted} out={out}")
if __name__=='__main__':main()
