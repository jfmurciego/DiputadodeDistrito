#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.2.0
NOMBRE DE VERSIÓN: Provincia primero y disciplina municipal
FECHA: 2026-09-11
ESTADO: candidato
FUNCIÓN: construir exactamente K distritos sin cruzar provincias y preservando municipios como unidades atómicas salvo cuando su población obliga a dividirlos.
ENTRADAS: grafo M03, geometría M01 y configuración R012.
SALIDAS: GeoJSON de secciones con district_id y metadatos de unidad territorial; informe M04.
REGLAS: reparto provincial fijo; municipio que cabe en un distrito no se fragmenta; municipio grande se divide internamente en bloques contiguos; los bloques urbanos completos quedan cerrados y solo el residual puede mezclarse con municipios menores.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.0.1.py
"""
from __future__ import annotations
import argparse, collections, io, json, math, sys, zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
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

def connected_chunk(nodes,adj,pop,target):
    nodes=set(nodes);start=max(nodes,key=lambda n:(pop.get(n,0),n));chosen={start};q=collections.deque(sorted(adj.get(start,set())&nodes));total=pop.get(start,0)
    while q and total<target:
        x=q.popleft()
        if x in chosen: continue
        chosen.add(x);total+=pop.get(x,0)
        for nb in sorted(adj.get(x,set())&nodes):
            if nb not in chosen:q.append(nb)
    return chosen

def unit_connected(unit_nodes,adj):
    if not unit_nodes:return False
    seen={next(iter(unit_nodes))};q=collections.deque(seen)
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in unit_nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(unit_nodes)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');val=cfg.get('validation',{}) or {}
    ing=require(s4.get('in_graph_json'),'Falta M04 grafo');ingeo=require(s4.get('in_geojson'),'Falta M04 geojson');idf=require(s4.get('id_field'),'Falta id');popf=require(s4.get('pop_field'),'Falta población');provf=s4.get('province_field','CPRO');munf=s4.get('municipality_field','CUMUN');munname=s4.get('municipality_name_field','NMUN');K=int(s4.get('k_districts',67));out=require(s4.get('out_geojson'),'Falta salida');report_path=s4.get('out_report','')
    G=json.loads(Path(ing).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};adj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v']);
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    g=load_geo(ingeo);g[idf]=g[idf].astype(str)
    for c in (provf,munf):
        if c not in g.columns:raise SystemExit(f'M04: falta columna {c}')
    g[provf]=g[provf].astype(str).str.zfill(2);g[munf]=g[munf].astype(str)
    total=sum(pop.values());target=total/K;cap=target*float(val.get('population_cap_ratio',1.75));quota={str(k).zfill(2):int(v) for k,v in (val.get('province_districts') or {}).items()}
    if sum(quota.values())!=K:raise SystemExit(f'M04: cuotas provinciales suman {sum(quota.values())}, esperado {K}')
    meta=g.set_index(idf)[[provf,munf]+([munname] if munname in g.columns else [])].to_dict('index')
    assign={};unit_id={};closed={};district_counter=0;prov_report={}
    for prov in sorted(quota):
        prov_nodes=[n for n in pop if n in meta and str(meta[n][provf]).zfill(2)==prov];qprov=quota[prov]
        mun_nodes=collections.defaultdict(set)
        for n in prov_nodes:mun_nodes[str(meta[n][munf])].add(n)
        units=[];locked=[]
        for mun,nodes in sorted(mun_nodes.items()):
            remaining=set(nodes);mp=sum(pop[n] for n in remaining);full=max(0,int(mp//target))
            # Evita crear un bloque final imposible: solo extraemos bloques urbanos completos mientras quede población residual positiva.
            for i in range(full):
                if not remaining:break
                rempop=sum(pop[n] for n in remaining)
                if rempop<=cap:break
                ch=connected_chunk(remaining,adj,pop,target)
                if not unit_connected(ch,adj):raise SystemExit(f'M04: bloque urbano no contiguo {prov}/{mun}')
                units.append((f'{prov}:{mun}:U{i+1}',ch,True));locked.append(len(units)-1);remaining-=ch
            if remaining:units.append((f'{prov}:{mun}:R',remaining,False))
        # Grafo de unidades.
        node_to_u={n:i for i,(_,ns,_) in enumerate(units) for n in ns};uadj={i:set() for i in range(len(units))};upop={i:sum(pop[n] for n in units[i][1]) for i in range(len(units))}
        for n in prov_nodes:
            i=node_to_u[n]
            for nb in adj.get(n,set()):
                if nb in node_to_u and node_to_u[nb]!=i:uadj[i].add(node_to_u[nb])
        locked_units=[i for i,(_,_,lk) in enumerate(units) if lk]
        if len(locked_units)>=qprov:raise SystemExit(f'M04: provincia {prov}: bloques urbanos cerrados={len(locked_units)} >= cuota={qprov}')
        udist={};dist_members={};dist_pop={};dist_closed={}
        local_ids=[]
        for i in locked_units:
            d=district_counter;district_counter+=1;local_ids.append(d);udist[i]=d;dist_members[d]={i};dist_pop[d]=upop[i];dist_closed[d]=True
        remaining_units=set(range(len(units)))-set(locked_units);need=qprov-len(local_ids)
        seeds=sorted(remaining_units,key=lambda i:(upop[i],len(uadj[i]),-i),reverse=True)[:need]
        for i in seeds:
            d=district_counter;district_counter+=1;local_ids.append(d);udist[i]=d;dist_members[d]={i};dist_pop[d]=upop[i];dist_closed[d]=False
        unassigned=remaining_units-set(seeds)
        safety=0
        while unassigned and safety<100000:
            safety+=1;best=None
            for u in sorted(unassigned):
                neigh=sorted({udist[v] for v in uadj[u] if v in udist and not dist_closed[udist[v]]})
                for d in neigh:
                    score=(abs((dist_pop[d]+upop[u])-target),dist_pop[d],d,u)
                    if best is None or score<best[0]:best=(score,u,d)
            if best is None:
                # El grafo de unidades puede quedar desconectado por peculiaridades cartográficas; anclamos al distrito abierto menos poblado de la misma provincia y la validación decidirá.
                u=min(unassigned,key=lambda x:(upop[x],x));d=min([x for x in local_ids if not dist_closed[x]],key=lambda x:(dist_pop[x],x))
            else:_,u,d=best
            udist[u]=d;dist_members[d].add(u);dist_pop[d]+=upop[u];unassigned.remove(u)
        for i,(uid,ns,lk) in enumerate(units):
            d=udist[i]
            for n in ns:assign[n]=d;unit_id[n]=uid;closed[n]=bool(dist_closed[d])
        prov_report[prov]={'quota':qprov,'district_ids':local_ids,'closed_urban_districts':sum(1 for d in local_ids if dist_closed[d]),'units':len(units),'population':sum(pop[n] for n in prov_nodes)}
    if district_counter!=K:raise SystemExit(f'M04: generados {district_counter} distritos, esperado {K}')
    g['district_id']=g[idf].map(assign).astype('int64');g['ddd_unit_id']=g[idf].map(unit_id);g['ddd_closed_urban']=g[idf].map(closed).fillna(False).astype(bool);g['district_pop_section']=g[idf].map(pop).fillna(0).astype('int64')
    write_geo(g,out)
    pops=g.groupby('district_id')['district_pop_section'].sum()
    rep={'module':'04','version':'7.2.0','K':K,'total_pop':int(total),'target':target,'min_pop':int(pops.min()),'max_pop':int(pops.max()),'province_districts':prov_report,'assigned_missing':int(g['district_id'].isna().sum()),'rules':{'single_province':True,'small_municipality_atomic':True,'closed_urban_blocks':True}}
    if report_path:Path(report_path).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[Módulo 4] OK v7.2.0 K={K} provincias={quota} target≈{target:.1f} out={out}')
if __name__=='__main__':main()
