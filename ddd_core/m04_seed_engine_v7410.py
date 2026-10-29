#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.4.18
NOMBRE DE VERSIÓN: Cardinalidad residual de unidades indivisibles
FECHA: 2026-10-26
FUNCIÓN: construir exactamente K distritos dentro de sus provincias, preservando municipios completos mientras sean compatibles con el contrato territorial y dividiendo municipios sobredimensionados sin aislar el residuo municipal abierto.
ENTRADAS: grafo M03, geometría M01, configuración territorial y topology_bridges declarados en M02.
SALIDAS: GeoJSON M04 con district_id, ddd_unit_id y ddd_closed_urban; informe M04.
ESTADO: candidato CYL-03.
CAMBIOS: mantiene la búsqueda de núcleo cerrado y el fallback residual-first, pero separa las cotas duras de población (suelo/techo contractuales) de la banda ±tolerancia, que queda exclusivamente como objetivo de calidad.
MOTIVO: CYL-03 v7.4.4 identificó correctamente dos puertas reales de Aranda de Duero, pero el BFS orientado al núcleo no encontró una solución aunque el problema natural es pequeño: reservar un residuo de borde y cerrar el complemento urbano.
ANTERIOR: legacy/ddd_core/m04_seed_engine_v7.4.17_pre_ideal_count_order.py
CAMBIO 7.4.18: el residuo primero (7.4.17) se intenta antes que el crecimiento conexo, porque reparte en piezas cercanas al objetivo; y los reintentos equilibrado y de crecimiento prueban primero el número de núcleos más cercano al reparto ideal (round(pop/target)-1) en vez del mínimo; la búsqueda primaria no cambia. Motivo: Cartagena salía en 3 núcleos de ~52k + residuo de 60k y dejaba distritos encajonados bajo el suelo (Aledo, Pliego, Beniel, La Unión).
CAMBIO 7.4.17: si también se agota el crecimiento conexo, construye primero el residuo (árbol mínimo que une las unidades protegidas y las bolsas que aísla) y reparte el resto con hybrid_partition+rebalance; las particiones que hoy tienen éxito no cambian. Motivo: municipio de Murcia (run 40853664303), 4 protegidas que la búsqueda secuencial nunca reunía en el residuo.
CAMBIO 7.4.16: solo si las búsquedas secuencial y equilibrada se agotan, reintenta con núcleos que crecen añadiendo únicamente unidades que dejan el resto conexo; las particiones que hoy tienen éxito no cambian. Motivo: Cartagena (Murcia, run 40850405847, 'no connected core' con banda amplia).
CAMBIO 7.4.15: solo cuando la búsqueda secuencial se agota, la reintenta apuntando cada núcleo al reparto equilibrado del resto (pop_restante/partes_restantes) en vez de al objetivo; las particiones que hoy tienen éxito no cambian. Motivo: Cartagena (Murcia, run 40773421805).
CAMBIO 7.4.14: reserva una unidad por distrito pendiente antes de aceptar una extracción y rechaza cardinalidades imposibles explícitamente; conserva K y el grafo.
"""
from __future__ import annotations
import argparse, collections, heapq, io, json, math, sys, zipfile
from pathlib import Path
import geopandas as gpd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg,require, hard_limits
from ddd_core.m04_partition_contract import validate_and_annotate_partition
from ddd_core.m04_administrative_atomic_groups import connected_atomic_municipality_groups
from ddd_core.topology_preflight import validate_topology_accreditation_binding, validate_administrative_components

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

def components(nodes,adj):
    unseen=set(nodes);out=[]
    while unseen:
        s=next(iter(unseen));unseen.remove(s);seen={s};q=[s]
        while q:
            u=q.pop()
            for v in adj.get(u,set()):
                if v in unseen:unseen.remove(v);seen.add(v);q.append(v)
        out.append(seen)
    return sorted(out,key=len,reverse=True)

def find_peel(rem,desired,adj,w,max_starts=120,min_remaining=1):
    rem=set(rem);starts=sorted(rem,key=lambda n:(sum(v in rem for v in adj[n]),w[n],str(n)))[:max_starts];best=None
    for s in starts:
        order=[];seen={s};q=collections.deque([s]);cum=0
        while q:
            u=q.popleft();order.append(u);cum+=w[u]
            if cum>=desired*.65:
                ch=set(order);rest=rem-ch
                if len(rest)>=min_remaining and rest and cum<=desired*1.45 and connected(ch,adj) and connected(rest,adj):
                    score=(abs(cum-desired),cum,len(ch),str(s))
                    if best is None or score<best[0]:best=(score,ch)
                if cum>desired*1.45:break
            for v in sorted(adj[u],key=str):
                if v in rem and v not in seen:seen.add(v);q.append(v)
    return best[1] if best else None

def _validate_partition_cardinality(nodes,k,label=''):
    if not isinstance(k,int) or isinstance(k,bool) or k<=0 or not nodes:
        raise SystemExit(f'M04: INVALID_PARTITION_CARDINALITY {label}: nodes={len(nodes)} k={k}')
    if k>len(nodes):
        raise SystemExit(f'M04: INSUFFICIENT_ATOMIC_UNITS {label}: nodes={len(nodes)} k={k}')

def grow_partition(nodes,k,adj,w):
    nodes=set(nodes)
    _validate_partition_cardinality(nodes,k)
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

def hybrid_partition(nodes,k,adj,w,label=''):
    nodes=set(nodes)
    _validate_partition_cardinality(nodes,k,label)
    if k==1:return [nodes]
    if not connected(nodes,adj):
        cs=components(nodes,adj);raise SystemExit(f'M04: conjunto a particionar no conexo {label}; componentes={[len(c) for c in cs]}')
    rem=set(nodes);parts=[]
    for i in range(k-1):
        left=k-i;desired=sum(w[n] for n in rem)/left
        if left<=4:parts.extend(grow_partition(rem,left,adj,w));return parts
        ch=find_peel(rem,desired,adj,w,min_remaining=left-1)
        if ch is None:parts.extend(grow_partition(rem,left,adj,w));return parts
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

def find_closed_core(rem,desired,lo,hi,adj,w,left_after,protected=None,residual_gateways=None,max_starts=800):
    rem=set(rem);protected=set(protected or ());residual_gateways=set(residual_gateways or ());rp=sum(w[n] for n in rem);starts=sorted(rem-protected,key=lambda n:(sum(v in rem for v in adj[n]),w[n],str(n)))[:max_starts];best=None
    for s in starts:
        order=[];seen={s};q=collections.deque([s]);cum=0
        while q:
            u=q.popleft();order.append(u);cum+=w[u]
            if cum>=lo:
                ch=set(order);rest=rem-ch;rest_pop=rp-cum
                rest_connected=(not rest) or connected(rest,adj);future_ok=(rest_pop>=left_after*lo and rest_pop<=left_after*hi+hi) if left_after else (rest_pop==0 or rest_pop<=hi)
                gateway_ok=(not residual_gateways) or bool(rest&residual_gateways)
                if not(ch&protected) and cum<=hi and len(rest)>=left_after+1 and connected(ch,adj) and rest_connected and future_ok and gateway_ok:
                    score=(abs(cum-desired),-len(rest&residual_gateways),cum,len(ch),str(s))
                    if best is None or score<best[0]:best=(score,ch)
                if cum>hi:break
            for v in sorted(adj[u],key=str):
                if v in rem and v not in seen and v not in protected:seen.add(v);q.append(v)
    return best[1] if best else None

def find_closed_core_grow(rem,desired,lo,hi,adj,w,left_after,protected=None,residual_gateways=None,max_starts=200):
    # Crecimiento que solo añade unidades frontera que dejan el resto conexo (el BFS por prefijos puede cortarlo).
    rem=set(rem);protected=set(protected or ());residual_gateways=set(residual_gateways or ());rp=sum(w[n] for n in rem);best=None
    starts=sorted(rem-protected,key=lambda n:(sum(v in rem for v in adj[n]),w[n],str(n)))[:max_starts]
    for s in starts:
        ch={s};cum=w[s]
        if not connected(rem-ch,adj):continue
        while True:
            rest=rem-ch;rest_pop=rp-cum
            if lo<=cum<=hi and len(rest)>=left_after+1:
                future_ok=(rest_pop>=left_after*lo and rest_pop<=left_after*hi+hi) if left_after else (rest_pop==0 or rest_pop<=hi)
                gateway_ok=(not residual_gateways) or bool(rest&residual_gateways)
                if future_ok and gateway_ok:
                    score=(abs(cum-desired),-len(rest&residual_gateways),cum,len(ch),str(s))
                    if best is None or score<best[0]:best=(score,set(ch))
            if cum>=desired:break
            frontier=sorted({v for u in ch for v in adj[u] if v in rest and v not in protected},key=lambda v:(-sum(x in ch for x in adj[v]),abs(cum+w[v]-desired),str(v)))
            pick=next((v for v in frontier if cum+w[v]<=hi and connected(rest-{v},adj)),None)
            if pick is None:break
            ch.add(pick);cum+=w[pick]
    return best[1] if best else None

def find_residual_complement(rem,desired,lo,hi,adj,w,protected=None,residual_gateways=None):
    rem=set(rem);protected=set(protected or ());residual_gateways=set(residual_gateways or ());rp=sum(w[n] for n in rem)
    starts=sorted(residual_gateways or protected or rem,key=str);best=None
    for s in starts:
        residual=set();seen={s};q=collections.deque([s]);rpop=0
        while q:
            u=q.popleft();residual.add(u);rpop+=w[u];core=rem-residual;cpop=rp-rpop
            if core and lo<=cpop<=hi and protected.issubset(residual) and ((not residual_gateways) or bool(residual&residual_gateways)) and connected(core,adj):
                score=(abs(cpop-desired),rpop,len(residual),str(s));
                if best is None or score<best[0]:best=(score,set(core),set(residual))
            if cpop<lo:break
            nbrs=sorted({v for x in residual for v in adj.get(x,set()) if v in rem and v not in seen},key=lambda n:(w[n],str(n)))
            for v in nbrs:seen.add(v);q.append(v)
    return (best[1],best[2]) if best else (None,None)

def _sequential_count(nodes,n_closed,target,floor,cap,adj,w,protected,residual_gateways,balanced=False,grow=False):
    rem=set(nodes);closed=[];mode='sequential_core_residual'
    for idx in range(n_closed):
        left_after=n_closed-idx-1;rp=sum(w[n] for n in rem)
        core_min=max(floor,rp-cap-left_after*cap)
        core_max=min(cap,rp-left_after*floor)
        if core_min>core_max+1e-9:
            return None, f'range=[{core_min:.2f},{core_max:.2f}] pop_rem={rp}'
        # balanced: reparto equilibrado del resto entre los núcleos pendientes y el residual.
        aim=rp/(left_after+2) if balanced else target
        desired=min(max(aim,core_min),core_max)
        core=find_closed_core(rem,desired,core_min,core_max,adj,w,left_after,protected,residual_gateways)
        if core is None and grow:
            core=find_closed_core_grow(rem,desired,core_min,core_max,adj,w,left_after,protected,residual_gateways)
        if core is None and left_after==0:
            core,residual=find_residual_complement(rem,desired,core_min,core_max,adj,w,protected,residual_gateways)
            if core is not None:
                closed.append(core);rem=residual;mode='residual_first_complement';break
        if core is None:
            return None, f'no connected core pop_rem={rp} range=[{core_min:.2f},{core_max:.2f}]'
        closed.append(core);rem-=core
        if not rem or len(rem)<left_after+1 or not connected(rem,adj):
            return None, 'residual cardinality or connectivity'
    if not protected.issubset(rem) or (residual_gateways and not(rem&residual_gateways)):
        return None, 'residual gateways'
    if sum(w[n] for n in rem)>cap+1e-9:
        return None, 'residual cap'
    return (closed,rem,mode), None


def _components_within(nodes,adj):
    nodes=set(nodes);out=[]
    while nodes:
        s=nodes.pop();comp={s};stack=[s]
        while stack:
            u=stack.pop()
            for v in adj[u]&nodes:nodes.discard(v);comp.add(v);stack.append(v)
        out.append(comp)
    return out

def split_residual_first(nodes,target,floor,cap,tol,adj,w,protected,residual_gateways,label=''):
    # El residuo se construye primero: árbol mínimo (por población) que une las unidades protegidas,
    # más las bolsas pequeñas que ese árbol aísla; con un único trozo restante el residuo crece hasta el reparto medio,
    # con varios cada trozo se reparte globalmente por separado.
    nodes=set(nodes);terms=sorted(set(protected) or (set(residual_gateways)&nodes) or nodes)[:]
    res={terms[0]};pending=set(terms[1:])
    while pending:
        dist={n:0 for n in res};prev={};heap=[(0,n) for n in sorted(res)]
        while heap:
            c,u=heapq.heappop(heap)
            if c>dist[u]:continue
            for v in sorted(adj[u]&nodes):
                if c+w[v]<dist.get(v,float('inf')):dist[v]=c+w[v];prev[v]=u;heapq.heappush(heap,(dist[v],v))
        reach=[x for x in pending if x in dist]
        if not reach:return None,'protected not connected within municipality'
        x=min(reach,key=lambda n:(dist[n],n));pending.discard(x)
        while x not in res:res.add(x);x=prev[x]
    comps=sorted(_components_within(nodes-res,adj),key=lambda c:(sum(w[n] for n in c),sorted(c)))
    big=[c for c in comps if sum(w[n] for n in c)>=floor] or comps[-1:]
    for c in comps:
        if not any(c is x for x in big):res|=c
    mp=sum(w[n] for n in nodes);rp=sum(w[n] for n in res);q=max(2,int(round(mp/target)))
    if len(big)==1:
        aim=mp/q
        while rp<aim:
            frontier=sorted({v for u in res for v in adj[u]&nodes if v not in res},key=lambda v:(-len(adj[v]&res),w[v],v))
            pick=next((v for v in frontier if rp+w[v]<=cap and connected(nodes-res-{v},adj)),None)
            if pick is None:break
            res.add(pick);rp+=w[pick]
        big=[nodes-res]
    if rp>cap or not connected(res,adj) or not all(connected(c,adj) for c in big):
        return None,f'residual pop={rp} components={[sum(w[n] for n in c) for c in big]}'
    if residual_gateways and not(res&residual_gateways):return None,'residual gateways'
    parts=[]
    for c in big:
        cp=sum(w[n] for n in c);k=q-1 if len(big)==1 else max(1,int(round(cp/target)))
        if k==1:parts.append(set(c));continue
        if len(c)<k:return None,f'component cardinality {len(c)}<{k}'
        cparts=hybrid_partition(c,k,adj,w,label=f'residuo-primero {label}');cparts,_,_=rebalance(cparts,adj,w,target,floor,cap,tol,50000);parts+=[set(x) for x in cparts]
    pvals=[sum(w[n] for n in x) for x in parts]
    if not all(floor<=x<=cap for x in pvals) or not all(connected(x,adj) for x in parts):
        return None,f'rest partition out of band {sorted(round(x) for x in pvals)}'
    return ([set(p) for p in parts],res,f'residual_first_global:{len(parts)}'),None

def split_sequential(nodes,target,floor,cap,tol,adj,w,label='',protected=None,residual_gateways=None):
    nodes=set(nodes);protected=set(protected or ());residual_gateways=set(residual_gateways or ())
    mp=sum(w[n] for n in nodes)
    minimum=max(1,int(math.ceil(max(0.0,mp-cap)/cap)))
    maximum=min(len(nodes)-1,int(math.floor(mp/floor))) if floor>0 else len(nodes)-1
    attempts=[]
    for count in range(minimum,maximum+1):
        result,reason=_sequential_count(nodes,count,target,floor,cap,adj,w,protected,residual_gateways)
        if result is not None:
            closed,residual,mode=result
            if count!=minimum:mode+=f'+reconsidered_core_count:{minimum}->{count}'
            return closed,residual,mode
        attempts.append({'closed_cores':count,'reason':reason})
    # Reintentos: primero el número de núcleos más cercano al reparto ideal (q-1), no el mínimo.
    ideal_order=sorted(range(minimum,maximum+1),key=lambda c:(abs(c-(round(mp/target)-1)),c))
    # Solo si la búsqueda anterior se agota: reintento con objetivo equilibrado por núcleo.
    for count in ideal_order:
        result,reason=_sequential_count(nodes,count,target,floor,cap,adj,w,protected,residual_gateways,balanced=True)
        if result is not None:
            closed,residual,mode=result
            return closed,residual,mode+f'+balanced_lookahead:{count}'
        attempts.append({'closed_cores':count,'reason':'balanced: '+reason})
    # Tras el equilibrado: residuo primero (une las protegidas) y reparto global del resto.
    result,reason=split_residual_first(nodes,target,floor,cap,tol,adj,w,protected,residual_gateways,label)
    if result is not None:
        closed,residual,mode=result
        return closed,residual,'sequential_core_residual+'+mode
    attempts.append({'closed_cores':'residual_first','reason':reason})
    # Último recurso: núcleos por crecimiento que preserva la conexión del resto.
    for balanced in (True,False):
        for count in ideal_order:
            result,reason=_sequential_count(nodes,count,target,floor,cap,adj,w,protected,residual_gateways,balanced=balanced,grow=True)
            if result is not None:
                closed,residual,mode=result
                return closed,residual,mode+f'+connected_growth:{count}'
            attempts.append({'closed_cores':count,'reason':'growth: '+reason})
    raise SystemExit(f'M04: SEQUENTIAL_PARTITION_SEARCH_EXHAUSTED {label}; attempts={attempts} protected={sorted(protected)}; no structural impossibility inferred')

def partition_oversized_municipality(nodes,target,floor,cap,tol,adj,w,label='',protected=None):
    nodes=set(nodes);protected=set(protected or ());residual_gateways={n for n in nodes if any(nb not in nodes for nb in adj.get(n,set()))};mp=sum(w[n] for n in nodes);lo=floor;hi=cap;q=max(2,int(round(mp/target)));avg=mp/q
    if lo<=avg<=hi and q<=len(nodes):
        parts=hybrid_partition(nodes,q,adj,w,label=f'municipio {label}');parts,pvals,obj=rebalance(parts,adj,w,target,lo,hi,tol,50000)
        if all(lo<=x<=hi for x in pvals):
            eligible=[]
            for i,p in enumerate(parts):
                if protected and not protected.issubset(p):continue
                if residual_gateways and not(p&residual_gateways):continue
                eligible.append(i)
            if eligible:
                residual_i=max(eligible,key=lambda i:(sum(1 for n in parts[i] for nb in adj[n] if nb not in nodes),len(parts[i]&residual_gateways),-abs(pvals[i]-target),-i))
                closed=[set(p) for i,p in enumerate(parts) if i!=residual_i];residual=set(parts[residual_i])
                return closed,residual,'global_q_partition',residual_gateways
    closed,residual,mode=split_sequential(nodes,target,floor,cap,tol,adj,w,label,protected,residual_gateways)
    return closed,residual,mode,residual_gateways

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args();cfg=load_params_yaml(a.params);s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');s2=module_cfg(cfg,'modulo_02_construir_adyacencias','step2_export_edges');val=cfg.get('validation',{}) or {}
    ing=require(s4.get('in_graph_json'),'Falta M04 grafo');ingeo=require(s4.get('in_geojson'),'Falta M04 geojson');idf=require(s4.get('id_field'),'Falta id');provf=s4.get('province_field','CPRO');munf=s4.get('municipality_field','CUMUN');munname=s4.get('municipality_name_field','NMUN');K=int(s4.get('k_districts',67));out=require(s4.get('out_geojson'),'Falta salida');report_path=s4.get('out_report','')
    bridge_nodes=set()
    for b in s2.get('topology_bridges',[]) or []:
        for x in (b.get('u'),b.get('v')):
            if x is not None:bridge_nodes.add(str(x))
    G=json.loads(Path(ing).read_text(encoding='utf-8'));pop={str(n['id']):int(n.get('pop',0)) for n in G['nodes']};adj={n:set() for n in pop}
    for e in G['edges']:
        u,v=str(e['u']),str(e['v'])
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    g=load_geo(ingeo);g[idf]=g[idf].astype(str)
    for c in (provf,munf):
        if c not in g.columns:raise SystemExit(f'M04: falta columna {c}')
    g[provf]=g[provf].astype(str).str.zfill(2);g[munf]=g[munf].astype(str)
    total=sum(pop.values());target,floor,cap,tol=hard_limits(cfg,k=K,total_pop=total);cap_ratio=cap/target;atomic_ratio=float(s4.get('municipality_atomicity_limit_ratio',cap_ratio));atomic_limit=target*atomic_ratio
    quota={str(k).zfill(2):int(v) for k,v in (val.get('province_districts') or {}).items()}
    floor_exempt={str(x) for x in (val.get('population_floor_exempt_partitions') or [])}
    if sum(quota.values())!=K:raise SystemExit(f'M04: cuotas provinciales suman {sum(quota.values())}, esperado {K}')
    meta=g.set_index(idf)[[provf,munf]+([munname] if munname in g.columns else [])].to_dict('index');assign={};unit_id={};closed={};district_counter=0;prov_report={}
    for prov in sorted(quota):
        prov_floor=0.0 if prov in floor_exempt else floor
        prov_nodes=[n for n in pop if n in meta and str(meta[n][provf]).zfill(2)==prov];mun_nodes=collections.defaultdict(set)
        for n in prov_nodes:mun_nodes[str(meta[n][munf])].add(n)
        units=[];oversized_report=[];administrative_group_audit=[]
        if any(not connected(ns,adj) for ns in mun_nodes.values()):
            binding=validate_topology_accreditation_binding(cfg)
            if not binding.get('present') or not binding.get('valid'):
                raise SystemExit(f'M04: invalid administrative component source binding: {binding}')
            declarations=(val.get('topology_accreditation') or {}).get('administrative_components') or []
            scoped=[item for item in declarations if item.get('admin_scope') in
                    {f'municipality:{mun}' for mun in mun_nodes}]
            accredited,rejected=validate_administrative_components(
                units={n:{'province':prov,'municipality':meta[n][munf]} for n in prov_nodes},
                declarations=scoped,
                operational_edges=[(edge['u'],edge['v']) for edge in G['edges']])
            if rejected:
                raise SystemExit(f'M04: invalid administrative component evidence: {rejected}')
            physical_adj={n:set() for n in pop}
            for edge in G['edges']:
                if edge.get('edge_type','geometric')!='geometric':continue
                u,v=str(edge['u']),str(edge['v'])
                if u in physical_adj and v in physical_adj:
                    physical_adj[u].add(v);physical_adj[v].add(u)
            try:
                groups,administrative_group_audit=connected_atomic_municipality_groups(
                    mun_nodes,physical_adj,pop,accredited,atomic_limit=min(atomic_limit,cap))
            except ValueError as exc:
                raise SystemExit(f'M04: {exc}') from exc
            mun_nodes={'|'.join(members):ns for members,ns in groups}
        for mun,nodes in sorted(mun_nodes.items()):
            if not connected(nodes,adj):raise SystemExit(f'M04: municipio {prov}/{mun} no conexo en M03')
            mp=sum(pop[n] for n in nodes);mname=str(meta[next(iter(nodes))].get(munname,'')) if munname in g.columns else ''
            if mp<=atomic_limit:units.append((f'{prov}:{mun}:M',set(nodes),False,mun));continue
            label=f'{prov}/{mun}/{mname}';protected=bridge_nodes&set(nodes);cores,residual,mode,residual_gateways=partition_oversized_municipality(nodes,target,floor,cap,tol,adj,pop,label,protected)
            for i,p in enumerate(cores,1):
                pp=sum(pop[n] for n in p)
                if not(floor<=pp<=cap):raise SystemExit(f'M04: núcleo {label}/U{i} fuera de suelo/techo: {pp}')
                units.append((f'{prov}:{mun}:U{i}',set(p),True,mun))
            if residual:units.append((f'{prov}:{mun}:R',set(residual),False,mun))
            oversized_report.append({'municipality':mun,'municipality_name':mname,'population':mp,'partition_mode':mode,'protected_gateway_nodes':sorted(protected),'municipal_boundary_gateways':sorted(residual_gateways),'residual_boundary_gateways':sorted(set(residual)&set(residual_gateways)),'closed_cores':len(cores),'closed_core_populations':[sum(pop[n] for n in p) for p in cores],'residual_population':sum(pop[n] for n in residual),'atomic_limit':atomic_limit})
        node_to_u={n:i for i,(_,ns,_,_) in enumerate(units) for n in ns};uadj={i:set() for i in range(len(units))};upop={i:sum(pop[n] for n in units[i][1]) for i in range(len(units))}
        for n in prov_nodes:
            i=node_to_u[n]
            for nb in adj[n]:
                if nb in node_to_u and node_to_u[nb]!=i:uadj[i].add(node_to_u[nb])
        locked=[i for i,u in enumerate(units) if u[2]];open_units=set(range(len(units)))-set(locked);need=quota[prov]-len(locked)
        if need<0:raise SystemExit(f'M04: provincia {prov}: núcleos cerrados={len(locked)} > cuota={quota[prov]}')
        if need==0 and open_units:raise SystemExit(f'M04: provincia {prov}: no quedan distritos abiertos para {len(open_units)} unidades')
        if need>len(open_units):raise SystemExit(f'M04: provincia {prov}: need={need} > unidades abiertas={len(open_units)}')
        if open_units and not connected(open_units,uadj):
            cs=components(open_units,uadj)
            # Los núcleos cerrados pueden separar legítimamente el residual provincial.
            # Evaluamos las cardinalidades factibles de cada componente con el mismo
            # particionador/rebalanceador y elegimos la combinación lexicográficamente
            # mejor que suma exactamente la cuota abierta.
            choices=[]
            for seq,comp in enumerate(cs,1):
                pcomp=sum(upop[i] for i in comp)
                kmin=max(1,int(math.ceil(pcomp/cap-1e-12)))
                kmax=min(len(comp),need) if prov_floor<=0 else min(len(comp),int(math.floor(pcomp/prov_floor+1e-12)))
                opts=[]
                for kc in range(kmin,kmax+1):
                    pp=hybrid_partition(comp,kc,uadj,upop,label=f'provincia {prov} componente abierto {seq} k={kc}')
                    pp,pvals,pobj=rebalance(pp,uadj,upop,target,prov_floor,cap,tol,30000)
                    opts.append((kc,pp,pvals,pobj))
                if not opts:
                    detail={'units':len(comp),'pop':pcomp,'kmin':kmin,'kmax':kmax,'ids':[units[i][0] for i in sorted(comp)[:12]]}
                    raise SystemExit(f'M04: componente abierto sin cardinalidad factible provincia {prov}: {detail}')
                choices.append(opts)
            def combine(a,b):
                return (a[0]+b[0],a[1]+b[1],a[2]+b[2],max(a[3],b[3]),a[4]+b[4])
            states={0:((0,0,0,0.0,0.0),[])}
            for opts in choices:
                nxt={}
                for used,(obj_acc,sel) in states.items():
                    for option in opts:
                        kc,pp,pvals,pobj=option
                        total_used=used+kc
                        if total_used>need:continue
                        obj=combine(obj_acc,pobj)
                        prev=nxt.get(total_used)
                        if prev is None or obj<prev[0]:
                            nxt[total_used]=(obj,sel+[option])
                states=nxt
            if need not in states:
                detail=[{'units':len(c),'pop':sum(upop[i] for i in c),'ids':[units[i][0] for i in sorted(c)[:12]]} for c in cs]
                raise SystemExit(f'M04: componentes abiertos no admiten need={need} provincia {prov}; componentes={detail}')
            open_obj,selected=states[need]
            open_parts=[];open_pops=[]
            for kc,pp,pvals,pobj in selected:
                open_parts.extend(pp);open_pops.extend(pvals)
        else:
            open_parts=hybrid_partition(open_units,need,uadj,upop,label=f'provincia {prov} unidades abiertas') if need else []
            open_parts,open_pops,open_obj=rebalance(open_parts,uadj,upop,target,prov_floor,cap,tol,30000) if open_parts else ([],[],())
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
        prov_report[prov]={'quota':quota[prov],'district_ids':local_ids,'closed_urban_districts':len(locked),'units':len(units),'population':sum(pop[n] for n in prov_nodes),'oversized_municipalities':oversized_report,'administrative_atomic_groups':administrative_group_audit,'open_partition_objective':list(open_obj) if open_obj else []}
    if district_counter!=K:raise SystemExit(f'M04: generados {district_counter} distritos, esperado {K}')
    if len(assign)!=len(pop):raise SystemExit(f'M04: asignadas {len(assign)} secciones de {len(pop)}')
    g['district_id']=g[idf].map(assign).astype('int64');g['ddd_unit_id']=g[idf].map(unit_id);g['ddd_closed_urban']=g[idf].map(closed).fillna(False).astype(bool);g['district_pop_section']=g[idf].map(pop).fillna(0).astype('int64')
    pops=g.groupby('district_id')['district_pop_section'].sum();outside=int((abs(pops-target)>tol).sum())
    diagnostics=validate_and_annotate_partition(
        g,
        id_field=idf,
        district_field='district_id',
        province_field=provf,
        expected_k=K,
        province_quota=quota,
        adjacency=adj,
        floor=floor,
        cap=cap,
        floor_exempt_partitions=floor_exempt,
    )
    hard=diagnostics['hard_population_violations'];prov_counts=diagnostics['province_counts']
    write_geo(g,out);rep={'module':'04','version':'7.4.14','K':K,'total_pop':int(total),'target':target,'floor':floor,'cap':cap,'tolerance':tol,'municipality_atomicity_limit_ratio':atomic_ratio,'municipality_atomicity_limit':atomic_limit,'topology_gateway_nodes':sorted(bridge_nodes),'min_pop':int(pops.min()),'max_pop':int(pops.max()),'outside_target_tolerance':outside,'hard_population_violations':hard,'districts_below_floor':diagnostics['districts_below_floor'],'districts_above_ceiling':diagnostics['districts_above_ceiling'],'population_districts':diagnostics['population_districts'],'population_floor_exempt_partitions':sorted(floor_exempt),'province_counts':prov_counts,'province_districts':prov_report,'assigned_missing':0,'population_baseline_status':'PASS' if hard==0 else 'PASS_WITH_EXCEPTIONS','rules':{'single_province':True,'municipality_atomic_until_configured_limit':True,'topology_bridge_gateways_preserved_in_open_residual':True,'municipal_boundary_gateway_preserved_in_open_residual':True,'residual_first_complement_fallback':True,'oversized_municipality_global_partition_when_feasible':True,'oversized_municipality_core_residual_fallback':True,'district_contiguity_preexport':True,'population_limits_are_diagnostic_at_m04':True}}
    if report_path:Path(report_path).write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[Módulo 4] OK v7.4.14 K={K} provincias={prov_counts} hard={hard} outside_tol={outside} min={int(pops.min())} max={int(pops.max())} out={out}')
if __name__=='__main__':main()
