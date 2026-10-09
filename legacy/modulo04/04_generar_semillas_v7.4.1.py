#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.4.1
NOMBRE DE VERSIÓN: Núcleos municipales mínimos con residuo factible
FECHA: 2026-09-11
FUNCIÓN: construir exactamente K distritos dentro de sus provincias, preservando municipios completos mientras sean compatibles con el contrato territorial y dividiendo municipios sobredimensionados con el mínimo número de núcleos distritales cerrados necesario.
ENTRADAS: grafo M03, geometría M01 y configuración territorial.
SALIDAS: GeoJSON M04 con district_id, ddd_unit_id y ddd_closed_urban; informe M04.
ESTADO: candidato CYL-03.
CAMBIOS: sustituye la maximización floor(pop/target) de núcleos cerrados por el mínimo número necesario para que el residuo municipal sea absorbible; cada núcleo se busca dentro de target±tolerancia preservando conectividad del núcleo, del residuo y de las extracciones futuras. Mantiene retrocompatibilidad: si un territorio no declara municipality_atomicity_limit_ratio se usa population_cap_ratio.
MOTIVO: CYL-03 demostró con un municipio de 63.120 habitantes que dos núcleos cerrados dejaban un residuo artificialmente pequeño; un único núcleo bien dimensionado deja un residuo válido y reduce cortes municipales.
ANTERIOR: legacy/modulo04/04_generar_semillas_v7.4.0.py
"""
from __future__ import annotations
import argparse, collections, io, json, math, sys, zipfile
from pathlib import Path
import geopandas as gpd
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

def find_closed_core(rem,desired,lo,hi,adj,w,left_after,max_starts=800):
    """Busca un núcleo conexo [lo,hi] dejando un residuo conexo y factible para futuras extracciones."""
    rem=set(rem);rp=sum(w[n] for n in rem)
    starts=sorted(rem,key=lambda n:(sum(v in rem for v in adj[n]),w[n],str(n)))[:max_starts]
    best=None
    for s in starts:
        order=[];seen={s};q=collections.deque([s]);cum=0
        while q:
            u=q.popleft();order.append(u);cum+=w[u]
            if cum>=lo:
                ch=set(order);rest=rem-ch;rest_pop=rp-cum
                rest_connected=(not rest) or connected(rest,adj)
                if left_after:
                    future_ok=(rest_pop>=left_after*lo and rest_pop<=left_after*hi+hi)
                else:
                    future_ok=(rest_pop==0 or rest_pop<=hi)
                if cum<=hi and connected(ch,adj) and rest_connected and future_ok:
                    score=(abs(cum-desired),abs(rest_pop-min(rest_pop,hi)),cum,len(ch),str(s))
                    if best is None or score<best[0]:best=(score,ch)
                if cum>hi:break
            for v in sorted(adj[u],key=str):
                if v in rem and v not in seen:seen.add(v);q.append(v)
    return best[1] if best else None

def split_oversized_municipality(nodes,target,tol,adj,w,label=''):
    """Mínimos núcleos cerrados; un único residuo queda abierto y debe ser <= límite superior."""
    rem=set(nodes);mp=sum(w[n] for n in rem);lo=target-tol;hi=target+tol
    # Mínimo c tal que c núcleos de hasta hi pueden dejar un residuo <= hi.
    n_closed=max(1,int(math.ceil(max(0.0,mp-hi)/hi)))
    closed=[]
    for idx in range(n_closed):
        left=n_closed-idx;left_after=left-1;rp=sum(w[n] for n in rem)
        need_remove=max(0.0,rp-hi)
        core_min=max(lo,need_remove-left_after*hi)
        # Reservar como mínimo lo necesario para futuros cores; el resto final puede ser 0..hi.
        core_max=min(hi,rp-left_after*lo)
        if core_min>core_max+1e-9:
            raise SystemExit(f'M04: rango municipal imposible {label}: rem={rp} core_min={core_min:.2f} core_max={core_max:.2f}')
        desired=min(max(target,core_min),core_max)
        core=find_closed_core(rem,desired,core_min,core_max,adj,w,left_after)
        if core is None:
            raise SystemExit(f'M04: no se puede extraer núcleo municipal factible {label}; pop_rem={rp} desired={desired:.2f} rango=[{core_min:.2f},{core_max:.2f}] futuros={left_after}')
        closed.append(core);rem-=core
        if rem and not connected(rem,adj):raise SystemExit(f'M04: residuo municipal desconectado {label}')
    residual_pop=sum(w[n] for n in rem)
    if residual_pop>hi+1e-9:
        raise SystemExit(f'M04: residuo municipal excede tolerancia superior {label}: {residual_pop}>{hi:.2f}')
    return closed,rem

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

def objective(vals,target,floor,cap,tol):
    hard=sum(x<floor or x>cap for x in vals);mag=sum(max(0,floor-x,x-cap) for x in vals);outside=sum(abs(x-target)>tol for x in vals);mx=max(abs(x-target)/target for x in vals);sq=sum(((x-target)/target)**2 for x in vals)
    return (hard,mag,outside,mx,sq)

def rebalance(parts,adj,w,target,floor,cap,tol,iters=30000):
    parts=[set(p) for p in parts];owner={n:i for i,p in enumerate(parts) for n in p};pw=[sum(w[n] for n in p) for p in parts];cur=objective(pw,target,floor,cap,tol)
    for _ in range(iters):
        best=None
        for n,a in list(owner.items()):
            neigh={owner[v] for v in adj[n] if v in owner and owner[v]!=a}
            if not neigh or len(parts[a])<=1 or not connected(parts[a]-{n},adj):continue
            for b in neigh:
                vals=pw.copy();vals[a]-=w[n];vals[b]+=w[n];obj=objective(vals,target,floor,cap,tol)
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
    total=sum(pop.values());target=total/K
    floor_ratio=float(val.get('population_floor_ratio',.8));cap_ratio=float(val.get('population_cap_ratio',1.75));tol_ratio=float(val.get('target_tolerance_ratio',.12))
    floor=target*floor_ratio;cap=target*cap_ratio;tol=target*tol_ratio
    atomic_ratio=float(s4.get('municipality_atomicity_limit_ratio',cap_ratio));atomic_limit=target*atomic_ratio
    quota={str(k).zfill(2):int(v) for k,v in (val.get('province_districts') or {}).items()}
    if sum(quota.values())!=K:raise SystemExit(f'M04: cuotas provinciales suman {sum(quota.values())}, esperado {K}')
    meta=g.set_index(idf)[[provf,munf]+([munname] if munname in g.columns else [])].to_dict('index');assign={};unit_id={};closed={};district_counter=0;prov_report={}
    for prov in sorted(quota):
        prov_nodes=[n for n in pop if n in meta and str(meta[n][provf]).zfill(2)==prov];mun_nodes=collections.defaultdict(set)
        for n in prov_nodes:mun_nodes[str(meta[n][munf])].add(n)
        units=[];oversized_report=[]
        for mun,nodes in sorted(mun_nodes.items()):
            if not connected(nodes,adj):raise SystemExit(f'M04: municipio {prov}/{mun} no conexo en M03')
            mp=sum(pop[n] for n in nodes);mname=str(meta[next(iter(nodes))].get(munname,'')) if munname in g.columns else ''
            if mp<=atomic_limit:
                units.append((f'{prov}:{mun}:M',set(nodes),False,mun));continue
            label=f'{prov}/{mun}/{mname}'
            cores,residual=split_oversized_municipality(nodes,target,tol,adj,pop,label)
            for i,p in enumerate(cores,1):
                pp=sum(pop[n] for n in p)
                if not (target-tol<=pp<=target+tol):raise SystemExit(f'M04: núcleo {label}/U{i} fuera de tolerancia: {pp}')
                units.append((f'{prov}:{mun}:U{i}',set(p),True,mun))
            if residual:units.append((f'{prov}:{mun}:R',set(residual),False,mun))
            oversized_report.append({'municipality':mun,'municipality_name':mname,'population':mp,'closed_cores':len(cores),'closed_core_populations':[sum(pop[n] for n in p) for p in cores],'residual_population':sum(pop[n] for n in residual),'atomic_limit':atomic_limit})
        node_to_u={n:i for i,(_,ns,_,_) in enumerate(units) for n in ns};uadj={i:set() for i in range(len(units))};upop={i:sum(pop[n] for n in units[i][1]) for i in range(len(units))}
        for n in prov_nodes:
            i=node_to_u[n]
            for nb in adj[n]:
                if nb in node_to_u and node_to_u[nb]!=i:uadj[i].add(node_to_u[nb])
        locked=[i for i,u in enumerate(units) if u[2]];open_units=set(range(len(units)))-set(locked);need=quota[prov]-len(locked)
        if need<0:raise SystemExit(f'M04: provincia {prov}: núcleos cerrados={len(locked)} > cuota={quota[prov]}')
        if need==0 and open_units:raise SystemExit(f'M04: provincia {prov}: no quedan distritos abiertos para {len(open_units)} unidades')
        if need>len(open_units):raise SystemExit(f'M04: provincia {prov}: need={need} > unidades abiertas={len(open_units)}')
        open_parts=hybrid_partition(open_units,need,uadj,upop) if need else []
        open_parts,open_pops,open_obj=rebalance(open_parts,uadj,upop,target,floor,cap,tol,30000) if open_parts else ([],[],())
        local_ids=[];dist_nodes={}
        for i in locked:
            d=district_counter;district_counter+=1;local_ids.append(d);dist_nodes[d]=set(units[i][1])
            for n in units[i][1]:assign[n]=d;unit_id[n]=units[i][0];closed[n]=True
        for part in open_parts:
            d=district_counter;district_counter+=1;local_ids.append(d);ns=set().union(*(units[i][1] for i in part));dist_nodes[d]=ns
            for i in part:
                for n in units[i][1]:assign[n]=d;unit_id[n]=units[i][0];closed[n]=False
        for d in local_ids:
            if not connected(dist_nodes[d],adj):raise SystemExit(f'M04: distrito {d} desconectado antes de exportar')
            ps={str(meta[n][provf]).zfill(2) for n in dist_nodes[d]}
            if ps!={prov}:raise SystemExit(f'M04: distrito {d} cruza provincia: {sorted(ps)}')
        prov_report[prov]={'quota':quota[prov],'district_ids':local_ids,'closed_urban_districts':len(locked),'units':len(units),'population':sum(pop[n] for n in prov_nodes),'oversized_municipalities':oversized_report,'open_partition_objective':list(open_obj) if open_obj else []}
    if district_counter!=K:raise SystemExit(f'M04: generados {district_counter} distritos, esperado {K}')
    if len(assign)!=len(pop):raise SystemExit(f'M04: asignadas {len(assign)} secciones de {len(pop)}')
    g['district_id']=g[idf].map(assign).astype('int64');g['ddd_unit_id']=g[idf].map(unit_id);g['ddd_closed_urban']=g[idf].map(closed).fillna(False).astype(bool);g['district_pop_section']=g[idf].map(pop).fillna(0).astype('int64')
    pops=g.groupby('district_id')['district_pop_section'].sum();hard=int(((pops<floor)|(pops>cap)).sum());outside=int((abs(pops-target)>tol).sum());prov_counts={str(x[provf].iloc[0]).zfill(2):0 for _,x in g.groupby('district_id')}
    for _,x in g.groupby('district_id'):prov_counts[str(x[provf].iloc[0]).zfill(2)]+=1
    if prov_counts!=quota:raise SystemExit(f'M04: cardinalidad provincial {prov_counts}, esperada {quota}')
    if hard:raise SystemExit(f'M04: solución inicial mantiene {hard} distritos fuera de suelo/techo')
    write_geo(g,out)
    rep={'module':'04','version':'7.4.1','K':K,'total_pop':int(total),'target':target,'floor':floor,'cap':cap,'tolerance':tol,'municipality_atomicity_limit_ratio':atomic_ratio,'municipality_atomicity_limit':atomic_limit,'min_pop':int(pops.min()),'max_pop':int(pops.max()),'outside_target_tolerance':outside,'hard_population_violations':hard,'province_counts':prov_counts,'province_districts':prov_report,'assigned_missing':0,'rules':{'single_province':True,'municipality_atomic_until_configured_limit':True,'oversized_municipality_min_closed_cores_plus_open_residual':True,'municipal_partition_connected':True,'closed_urban_blocks':True,'district_contiguity_preexport':True}}
    if report_path:Path(report_path).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[Módulo 4] OK v7.4.1 K={K} provincias={prov_counts} hard=0 outside_tol={outside} min={int(pops.min())} max={int(pops.max())} out={out}')
if __name__=='__main__':main()
