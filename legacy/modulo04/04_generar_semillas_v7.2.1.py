#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.2.1
NOMBRE DE VERSIÓN: Partición municipal conexa
FECHA: 2026-09-11
ESTADO: candidato
FUNCIÓN: construir exactamente K distritos sin cruzar provincias y preservando municipios como unidades atómicas salvo cuando exceden el techo duro.
ENTRADAS: grafo M03, geometría M01 y configuración R012.
SALIDAS: GeoJSON de secciones con district_id y metadatos de unidad territorial; informe M04.
CAMBIOS VS 7.2.0: sustituye el pelado secuencial de bloques urbanos por partición simultánea conexa; elimina el fallback que podía asignar unidades no adyacentes; un municipio solo se divide si su población supera el techo duro.
MOTIVO: Run #6 generó el distrito 52 con 15 componentes; el residuo de Zaragoza quedó desconectado aunque cada bloque extraído fuese conexo.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.2.0.py
"""
from __future__ import annotations
import argparse, collections, io, json, math, sys, zipfile
from pathlib import Path
import geopandas as gpd
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
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True)
    tmp=out.parent/(out.stem.replace('.geojson','')+'.geojson')
    gdf.to_file(tmp,driver='GeoJSON')
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)

def is_connected(nodes,adj):
    nodes=set(nodes)
    if not nodes:return False
    seen={next(iter(nodes))};q=collections.deque(seen)
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)

def graph_distances(start,nodes,adj):
    nodes=set(nodes);dist={start:0};q=collections.deque([start])
    while q:
        u=q.popleft()
        for v in adj.get(u,set()):
            if v in nodes and v not in dist:dist[v]=dist[u]+1;q.append(v)
    return dist

def choose_spread_seeds(nodes,k,adj,pop):
    nodes=set(nodes)
    first=max(nodes,key=lambda n:(pop.get(n,0),len(adj.get(n,set())&nodes),n));seeds=[first]
    while len(seeds)<k:
        dmaps=[graph_distances(s,nodes,adj) for s in seeds]
        cand=max(nodes-set(seeds),key=lambda n:(min(d.get(n,-1) for d in dmaps),pop.get(n,0),n))
        seeds.append(cand)
    return seeds

def partition_connected(nodes,k,adj,pop):
    nodes=set(nodes)
    if k<=1:return [nodes]
    if not is_connected(nodes,adj):raise SystemExit('M04: municipio no conexo antes de particionar')
    if k>len(nodes):raise SystemExit(f'M04: no se pueden crear {k} partes con {len(nodes)} secciones')
    seeds=choose_spread_seeds(nodes,k,adj,pop);parts=[{s} for s in seeds];ppop=[pop.get(s,0) for s in seeds]
    target=sum(pop[n] for n in nodes)/k;unassigned=nodes-set(seeds)
    while unassigned:
        candidates=[]
        for i,members in enumerate(parts):
            frontier=set()
            for u in members:frontier.update(v for v in adj.get(u,set()) if v in unassigned)
            for v in frontier:
                score=(abs((ppop[i]+pop.get(v,0))-target),ppop[i],i,-pop.get(v,0),v)
                candidates.append((score,i,v))
        if not candidates:raise SystemExit('M04: partición municipal conexa bloqueada; quedan secciones sin frontera')
        _,i,v=min(candidates,key=lambda x:x[0]);parts[i].add(v);ppop[i]+=pop.get(v,0);unassigned.remove(v)
    bad=[i for i,p in enumerate(parts) if not is_connected(p,adj)]
    if bad:raise SystemExit(f'M04: partición municipal produjo partes desconectadas {bad}')
    return parts

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args()
    cfg=load_params_yaml(a.params);s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');val=cfg.get('validation',{}) or {}
    ing=require(s4.get('in_graph_json'),'Falta M04 grafo');ingeo=require(s4.get('in_geojson'),'Falta M04 geojson');idf=require(s4.get('id_field'),'Falta id');provf=s4.get('province_field','CPRO');munf=s4.get('municipality_field','CUMUN');munname=s4.get('municipality_name_field','NMUN');K=int(s4.get('k_districts',67));out=require(s4.get('out_geojson'),'Falta salida');report_path=s4.get('out_report','')
    G=json.loads(Path(ing).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};adj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v'])
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    g=load_geo(ingeo);g[idf]=g[idf].astype(str)
    for c in (provf,munf):
        if c not in g.columns:raise SystemExit(f'M04: falta columna {c}')
    g[provf]=g[provf].astype(str).str.zfill(2);g[munf]=g[munf].astype(str)
    total=sum(pop.values());target=total/K;floor=target*float(val.get('population_floor_ratio',0.8));cap=target*float(val.get('population_cap_ratio',1.75));quota={str(k).zfill(2):int(v) for k,v in (val.get('province_districts') or {}).items()}
    if sum(quota.values())!=K:raise SystemExit(f'M04: cuotas provinciales suman {sum(quota.values())}, esperado {K}')
    meta=g.set_index(idf)[[provf,munf]+([munname] if munname in g.columns else [])].to_dict('index')
    assign={};unit_id={};closed={};district_counter=0;prov_report={}
    for prov in sorted(quota):
        prov_nodes=[n for n in pop if n in meta and str(meta[n][provf]).zfill(2)==prov];qprov=quota[prov];mun_nodes=collections.defaultdict(set)
        for n in prov_nodes:mun_nodes[str(meta[n][munf])].add(n)
        units=[]
        for mun,nodes in sorted(mun_nodes.items()):
            mp=sum(pop[n] for n in nodes)
            if not is_connected(nodes,adj):raise SystemExit(f'M04: municipio {prov}/{mun} no es conexo en M03')
            if mp<=cap:
                units.append((f'{prov}:{mun}:R',set(nodes),False,mun));continue
            n_parts=max(2,int(round(mp/target)));n_parts=max(n_parts,int(math.ceil(mp/cap)));n_parts=min(n_parts,int(math.ceil(mp/floor)))
            parts=partition_connected(nodes,n_parts,adj,pop);parts=sorted(parts,key=lambda p:(sum(pop[n] for n in p),min(p)))
            for i,pnodes in enumerate(parts):
                residual=(i==0);uid=f'{prov}:{mun}:R' if residual else f'{prov}:{mun}:U{i}'
                units.append((uid,pnodes,not residual,mun))
        node_to_u={n:i for i,(_,ns,_,_) in enumerate(units) for n in ns};uadj={i:set() for i in range(len(units))};upop={i:sum(pop[n] for n in units[i][1]) for i in range(len(units))}
        for n in prov_nodes:
            i=node_to_u[n]
            for nb in adj.get(n,set()):
                if nb in node_to_u and node_to_u[nb]!=i:uadj[i].add(node_to_u[nb])
        locked_units=[i for i,(_,_,lk,_) in enumerate(units) if lk]
        if len(locked_units)>qprov:raise SystemExit(f'M04: provincia {prov}: bloques urbanos cerrados={len(locked_units)} > cuota={qprov}')
        udist={};dist_units={};dist_pop={};dist_closed={};local_ids=[]
        for i in locked_units:
            d=district_counter;district_counter+=1;local_ids.append(d);udist[i]=d;dist_units[d]={i};dist_pop[d]=upop[i];dist_closed[d]=True
        open_nodes=set(range(len(units)))-set(locked_units);need=qprov-len(local_ids)
        if need<=0 and open_nodes:raise SystemExit(f'M04: provincia {prov}: sin distritos abiertos para {len(open_nodes)} unidades')
        if need>len(open_nodes):raise SystemExit(f'M04: provincia {prov}: hacen falta {need} distritos abiertos pero solo hay {len(open_nodes)} unidades')
        seeds=[]
        if need:
            first=max(open_nodes,key=lambda i:(upop[i],len(uadj[i]&open_nodes),-i));seeds=[first]
            while len(seeds)<need:
                dmaps=[]
                for s in seeds:
                    dd={s:0};q=collections.deque([s])
                    while q:
                        x=q.popleft()
                        for y in uadj[x]&open_nodes:
                            if y not in dd:dd[y]=dd[x]+1;q.append(y)
                    dmaps.append(dd)
                cand=max(open_nodes-set(seeds),key=lambda i:(min(d.get(i,-1) for d in dmaps),upop[i],-i));seeds.append(cand)
        for i in seeds:
            d=district_counter;district_counter+=1;local_ids.append(d);udist[i]=d;dist_units[d]={i};dist_pop[d]=upop[i];dist_closed[d]=False
        unassigned=open_nodes-set(seeds)
        while unassigned:
            best=None
            for u in sorted(unassigned):
                neigh=sorted({udist[v] for v in uadj[u] if v in udist and not dist_closed[udist[v]]})
                for d in neigh:
                    score=(abs((dist_pop[d]+upop[u])-target),dist_pop[d],d,u)
                    if best is None or score<best[0]:best=(score,u,d)
            if best is None:raise SystemExit(f'M04: provincia {prov}: quedan {len(unassigned)} unidades sin conexión a ningún distrito abierto')
            _,u,d=best;udist[u]=d;dist_units[d].add(u);dist_pop[d]+=upop[u];unassigned.remove(u)
        for d in local_ids:
            sec=set().union(*(units[i][1] for i in dist_units[d]))
            if not is_connected(sec,adj):raise SystemExit(f'M04: distrito {d} desconectado antes de exportar')
        for i,(uid,ns,lk,mun) in enumerate(units):
            d=udist[i]
            for n in ns:assign[n]=d;unit_id[n]=uid;closed[n]=bool(dist_closed[d])
        prov_report[prov]={'quota':qprov,'district_ids':local_ids,'closed_urban_districts':sum(1 for d in local_ids if dist_closed[d]),'units':len(units),'population':sum(pop[n] for n in prov_nodes)}
    if district_counter!=K:raise SystemExit(f'M04: generados {district_counter} distritos, esperado {K}')
    if len(assign)!=len(pop):raise SystemExit(f'M04: asignadas {len(assign)} secciones de {len(pop)}')
    g['district_id']=g[idf].map(assign).astype('int64');g['ddd_unit_id']=g[idf].map(unit_id);g['ddd_closed_urban']=g[idf].map(closed).fillna(False).astype(bool);g['district_pop_section']=g[idf].map(pop).fillna(0).astype('int64');write_geo(g,out)
    pops=g.groupby('district_id')['district_pop_section'].sum();rep={'module':'04','version':'7.2.1','K':K,'total_pop':int(total),'target':target,'min_pop':int(pops.min()),'max_pop':int(pops.max()),'province_districts':prov_report,'assigned_missing':int(g['district_id'].isna().sum()),'rules':{'single_province':True,'municipality_atomic_until_cap':True,'municipal_partition_connected':True,'closed_urban_blocks':True,'no_nonadjacent_fallback':True}}
    if report_path:Path(report_path).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[Módulo 4] OK v7.2.1 K={K} provincias={quota} target≈{target:.1f} out={out}')
if __name__=='__main__':main()
