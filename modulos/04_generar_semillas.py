#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.3.0
NOMBRE DE VERSIÓN: Partición balanceada conexa por provincia
FECHA: 2026-09-11
ESTADO: candidato
FUNCIÓN: construir exactamente K distritos dentro de sus provincias, preservando municipios completos salvo cuando exceden el techo duro y garantizando contigüidad antes de exportar.
ENTRADAS: grafo M03, geometría M01 y configuración R012.
SALIDAS: GeoJSON M04 con district_id, ddd_unit_id y ddd_closed_urban; informe M04.
CAMBIOS VS 7.2.1: sustituye el crecimiento multisemilla que podía encerrar semillas pequeñas por una partición conexa híbrida (peeling + crecimiento) seguida de reparación local; aplica el mismo principio al ensamblaje provincial de unidades; añade autovalidación de provincia, cardinalidad y contigüidad antes de exportar.
MOTIVO: Run #6 reveló que M04 v7.2.0 entregaba el distrito 52 con 15 componentes. La prueba sobre los mismos artefactos del Run #6 demuestra 67 distritos, reparto 11/7/49, cero cruces, cero desconectados y cero violaciones de suelo/techo antes de M05.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.2.1.py
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
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True);tmp=out.parent/(out.stem.replace('.geojson','')+'.geojson')
    gdf.to_file(tmp,driver='GeoJSON')
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)

def connected(nodes,adj):
    nodes=set(nodes)
    if not nodes:return False
    s=next(iter(nodes));seen={s};q=[s]
    while q:
        u=q.pop()
        for v in adj.get(u,set()):
            if v in nodes and v not in seen:seen.add(v);q.append(v)
    return len(seen)==len(nodes)

def find_peel(rem,desired,adj,w,max_starts=120):
    rem=set(rem);starts=sorted(rem,key=lambda n:(sum(v in rem for v in adj[n]),w[n],str(n)))[:max_starts];best=None
    for s in starts:
        order=[];seen={s};q=collections.deque([s]);cum=0
        while q:
            u=q.popleft();order.append(u);cum+=w[u]
            if cum>=desired*.65:
                ch=set(order);rest=rem-ch
                if rest and cum<=desired*1.45 and connected(ch,adj) and connected(rest,adj):
                    score=(abs(cum-desired),cum,len(ch),str(s))
                    if best is None or score<best[0]:best=(score,ch)
                if cum>desired*1.45:break
            for v in sorted(adj[u],key=str):
                if v in rem and v not in seen:seen.add(v);q.append(v)
    return best[1] if best else None

def grow_partition(nodes,k,adj,w):
    nodes=set(nodes)
    if k==1:return [nodes]
    first=max(nodes,key=lambda n:(w[n],str(n)));seeds=[first];dist={n:10**9 for n in nodes}
    def update(seed):
        q=collections.deque([(seed,0)]);seen={seed}
        while q:
            u,d=q.popleft()
            if d<dist[u]:dist[u]=d
            for v in adj[u]:
                if v in nodes and v not in seen:seen.add(v);q.append((v,d+1))
    update(first)
    while len(seeds)<k:
        s=max(nodes-set(seeds),key=lambda n:(dist[n],w[n],str(n)));seeds.append(s);update(s)
    owner={s:i for i,s in enumerate(seeds)};parts=[{s} for s in seeds];pw=[w[s] for s in seeds];un=nodes-set(seeds);target=sum(w[n] for n in nodes)/k
    while un:
        best=None
        for u in sorted(un,key=str):
            for d in sorted({owner[v] for v in adj[u] if v in owner}):
                score=(pw[d]/target,abs(pw[d]+w[u]-target),d,str(u))
                if best is None or score<best[0]:best=(score,u,d)
        if best is None:raise SystemExit('M04: crecimiento conexo bloqueado')
        _,u,d=best;owner[u]=d;parts[d].add(u);pw[d]+=w[u];un.remove(u)
    return parts

def hybrid_partition(nodes,k,adj,w):
    nodes=set(nodes)
    if k<=1:return [nodes]
    if not connected(nodes,adj):raise SystemExit('M04: conjunto a particionar no conexo')
    rem=set(nodes);parts=[]
    for i in range(k-1):
        left=k-i;desired=sum(w[n] for n in rem)/left
        if left<=4:
            parts.extend(grow_partition(rem,left,adj,w));return parts
        ch=find_peel(rem,desired,adj,w)
        if ch is None:
            parts.extend(grow_partition(rem,left,adj,w));return parts
        parts.append(ch);rem-=ch
    parts.append(rem);return parts

def objective(vals,target,floor,cap):
    hard=sum(x<floor or x>cap for x in vals);mag=sum(max(0,floor-x,x-cap) for x in vals);outside=sum(abs(x-target)>target*.12 for x in vals);mx=max(abs(x-target)/target for x in vals);sq=sum(((x-target)/target)**2 for x in vals)
    return (hard,mag,outside,mx,sq)

def rebalance(parts,adj,w,target,floor,cap,iters=30000):
    parts=[set(p) for p in parts];owner={n:i for i,p in enumerate(parts) for n in p};pw=[sum(w[n] for n in p) for p in parts];cur=objective(pw,target,floor,cap)
    for _ in range(iters):
        best=None
        for n,a in list(owner.items()):
            neigh={owner[v] for v in adj[n] if v in owner and owner[v]!=a}
            if not neigh or len(parts[a])<=1 or not connected(parts[a]-{n},adj):continue
            for b in neigh:
                vals=pw.copy();vals[a]-=w[n];vals[b]+=w[n];obj=objective(vals,target,floor,cap)
                if obj<cur:
                    cand=(obj,str(n),a,b,n)
                    if best is None or cand<best:best=cand
        if best is None:break
        obj,_,a,b,n=best;parts[a].remove(n);parts[b].add(n);owner[n]=b;pw[a]-=w[n];pw[b]+=w[n];cur=obj
    return parts,pw,cur

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args();cfg=load_params_yaml(a.params);s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');val=cfg.get('validation',{}) or {}
    ing=require(s4.get('in_graph_json'),'Falta M04 grafo');ingeo=require(s4.get('in_geojson'),'Falta M04 geojson');idf=require(s4.get('id_field'),'Falta id');provf=s4.get('province_field','CPRO');munf=s4.get('municipality_field','CUMUN');munname=s4.get('municipality_name_field','NMUN');K=int(s4.get('k_districts',67));out=require(s4.get('out_geojson'),'Falta salida');report_path=s4.get('out_report','')
    G=json.loads(Path(ing).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};adj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v'])
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    g=load_geo(ingeo);g[idf]=g[idf].astype(str)
    for c in (provf,munf):
        if c not in g.columns:raise SystemExit(f'M04: falta columna {c}')
    g[provf]=g[provf].astype(str).str.zfill(2);g[munf]=g[munf].astype(str)
    total=sum(pop.values());target=total/K;floor=target*float(val.get('population_floor_ratio',.8));cap=target*float(val.get('population_cap_ratio',1.75));quota={str(k).zfill(2):int(v) for k,v in (val.get('province_districts') or {}).items()}
    if sum(quota.values())!=K:raise SystemExit(f'M04: cuotas provinciales suman {sum(quota.values())}, esperado {K}')
    meta=g.set_index(idf)[[provf,munf]+([munname] if munname in g.columns else [])].to_dict('index');assign={};unit_id={};closed={};district_counter=0;prov_report={}
    for prov in sorted(quota):
        prov_nodes=[n for n in pop if n in meta and str(meta[n][provf]).zfill(2)==prov];mun_nodes=collections.defaultdict(set)
        for n in prov_nodes:mun_nodes[str(meta[n][munf])].add(n)
        units=[]
        for mun,nodes in sorted(mun_nodes.items()):
            if not connected(nodes,adj):raise SystemExit(f'M04: municipio {prov}/{mun} no conexo en M03')
            mp=sum(pop[n] for n in nodes)
            if mp<=cap:
                units.append((f'{prov}:{mun}:M',set(nodes),False,mun));continue
            k=max(2,int(math.ceil(mp/target)));parts=hybrid_partition(nodes,k,adj,pop);parts,pvals,_=rebalance(parts,adj,pop,target,floor,cap,5000)
            ext=[]
            for i,p in enumerate(parts):
                contacts=sum(1 for n in p for nb in adj[n] if nb not in nodes and nb in meta and str(meta[nb][provf]).zfill(2)==prov)
                ext.append((contacts,-abs(pvals[i]-target),-i,i))
            residual=max(ext)[-1]
            for i,p in enumerate(parts):units.append((f'{prov}:{mun}:{"R" if i==residual else "U"+str(i+1)}',set(p),i!=residual,mun))
        node_to_u={n:i for i,(_,ns,_,_) in enumerate(units) for n in ns};uadj={i:set() for i in range(len(units))};upop={i:sum(pop[n] for n in units[i][1]) for i in range(len(units))}
        for n in prov_nodes:
            i=node_to_u[n]
            for nb in adj[n]:
                if nb in node_to_u and node_to_u[nb]!=i:uadj[i].add(node_to_u[nb])
        locked=[i for i,u in enumerate(units) if u[2]];open_units=set(range(len(units)))-set(locked);need=quota[prov]-len(locked)
        if need<=0 and open_units:raise SystemExit(f'M04: provincia {prov}: no quedan distritos abiertos')
        if need>len(open_units):raise SystemExit(f'M04: provincia {prov}: need={need} > unidades abiertas={len(open_units)}')
        open_parts=hybrid_partition(open_units,need,uadj,upop) if need else []
        open_parts,open_pops,open_obj=rebalance(open_parts,uadj,upop,target,floor,cap,30000) if open_parts else ([],[],())
        local_ids=[];dist_nodes={};dist_closed={}
        for i in locked:
            d=district_counter;district_counter+=1;local_ids.append(d);dist_nodes[d]=set(units[i][1]);dist_closed[d]=True
            for n in units[i][1]:assign[n]=d;unit_id[n]=units[i][0];closed[n]=True
        for part in open_parts:
            d=district_counter;district_counter+=1;local_ids.append(d);ns=set().union(*(units[i][1] for i in part));dist_nodes[d]=ns;dist_closed[d]=False
            for i in part:
                for n in units[i][1]:assign[n]=d;unit_id[n]=units[i][0];closed[n]=False
        for d in local_ids:
            if not connected(dist_nodes[d],adj):raise SystemExit(f'M04: distrito {d} desconectado antes de exportar')
            ps={str(meta[n][provf]).zfill(2) for n in dist_nodes[d]}
            if ps!={prov}:raise SystemExit(f'M04: distrito {d} cruza provincia: {sorted(ps)}')
        prov_report[prov]={'quota':quota[prov],'district_ids':local_ids,'closed_urban_districts':len(locked),'units':len(units),'population':sum(pop[n] for n in prov_nodes),'open_partition_objective':list(open_obj) if open_obj else []}
    if district_counter!=K:raise SystemExit(f'M04: generados {district_counter} distritos, esperado {K}')
    if len(assign)!=len(pop):raise SystemExit(f'M04: asignadas {len(assign)} secciones de {len(pop)}')
    g['district_id']=g[idf].map(assign).astype('int64');g['ddd_unit_id']=g[idf].map(unit_id);g['ddd_closed_urban']=g[idf].map(closed).fillna(False).astype(bool);g['district_pop_section']=g[idf].map(pop).fillna(0).astype('int64')
    # Puerta interna M04: cardinalidad provincial, contigüidad y límites duros antes de exportar.
    pops=g.groupby('district_id')['district_pop_section'].sum();hard=int(((pops<floor)|(pops>cap)).sum());prov_counts={str(x[provf].iloc[0]).zfill(2):0 for _,x in g.groupby('district_id')}
    for _,x in g.groupby('district_id'):prov_counts[str(x[provf].iloc[0]).zfill(2)]+=1
    if prov_counts!=quota:raise SystemExit(f'M04: cardinalidad provincial {prov_counts}, esperada {quota}')
    if hard:raise SystemExit(f'M04: solución inicial mantiene {hard} distritos fuera de suelo/techo')
    write_geo(g,out);rep={'module':'04','version':'7.3.0','K':K,'total_pop':int(total),'target':target,'floor':floor,'cap':cap,'min_pop':int(pops.min()),'max_pop':int(pops.max()),'hard_population_violations':hard,'province_counts':prov_counts,'province_districts':prov_report,'assigned_missing':0,'rules':{'single_province':True,'municipality_atomic_until_cap':True,'municipal_partition_connected':True,'closed_urban_blocks':True,'district_contiguity_preexport':True}}
    if report_path:Path(report_path).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[Módulo 4] OK v7.3.0 K={K} provincias={prov_counts} hard=0 min={int(pops.min())} max={int(pops.max())} out={out}')
if __name__=='__main__':main()
