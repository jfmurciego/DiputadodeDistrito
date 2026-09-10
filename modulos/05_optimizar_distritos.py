#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.0.1
NOMBRE DE VERSIÓN: Optimización determinista
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: optimiza la asignación inicial manteniendo contigüidad.
POR QUÉ ES SEPARADO: es el núcleo experimental y debe poder ejecutarse muchas veces sin reconstruir la base territorial.
CAMBIOS: ordena decisiones basadas en sets antes de aleatoriedad sembrada, haciendo reproducible la ejecución.
VERSIÓN ANTERIOR: legacy/2026-09-11_modulo05_v7.0.0/05_optimizar_distritos.py
"""
from __future__ import annotations
import sys,argparse,io,json,zipfile,random,collections
from pathlib import Path
from typing import Dict,Any,Set
PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:sys.path.insert(0,str(PROJECT_ROOT))
import geopandas as gpd
import pandas as pd
from ddd_core.config import load_params_yaml,module_cfg,require
def _gpd_read_file(path_or_buf,layer=None):
    try:
        import pyogrio;return pyogrio.read_dataframe(path_or_buf,layer=layer)
    except Exception:pass
    try:return gpd.read_file(path_or_buf,layer=layer,engine="pyogrio")
    except Exception:return gpd.read_file(path_or_buf,layer=layer)
def load_geojson_any(path_str):
    p=Path(path_str).expanduser().resolve()
    if not p.exists():raise FileNotFoundError(f"GeoJSON no encontrado: {p}")
    if p.suffix.lower()==".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p,"r") as z:
            members=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")];data=z.read(members[0])
        return _gpd_read_file(io.BytesIO(data))
    return _gpd_read_file(str(p))
def load_graph(path_str):return json.loads(Path(path_str).read_text(encoding="utf-8"))
def write_geojson_zip(gdf,out_path):
    outp=Path(out_path);outp.parent.mkdir(parents=True,exist_ok=True);tmp=outp.parent/(outp.stem.replace(".geojson","")+".geojson");gdf.to_file(tmp,driver="GeoJSON")
    with zipfile.ZipFile(outp,"w",compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)
def write_json(obj,out_path):Path(out_path).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def district_connected(adj:Dict[str,Set[str]],members:Set[str])->bool:
    if not members:return True
    start=min(members);q=collections.deque([start]);seen={start}
    while q:
        x=q.popleft()
        for nb in sorted(adj.get(x,set())):
            if nb in members and nb not in seen:seen.add(nb);q.append(nb)
    return len(seen)==len(members)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s5=module_cfg(cfg,"modulo_05_optimizar_distritos",legacy_step_key="step5_optimize_swaps");in_graph=require(s5.get("in_graph_json"),"Falta M05 grafo");in_geo=require(s5.get("in_geojson"),"Falta M05 geojson");id_field=require(s5.get("id_field"),"Falta M05 id");pop_field=require(s5.get("pop_field"),"Falta M05 población");district_field=s5.get("district_field","district_id");out_geo=require(s5.get("out_geojson"),"Falta M05 salida");out_report=s5.get("out_report","");iters=int(s5.get("iters",20000));seed=int(s5.get("seed",12345));random.seed(seed)
    G=load_graph(in_graph);nodes=[n["id"] for n in G.get("nodes",[])];pop_map={n["id"]:int(n.get("pop",0)) for n in G.get("nodes",[])};adj={nid:set() for nid in nodes}
    for e in G.get("edges",[]):
        u=str(e["u"]);v=str(e["v"])
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    gdf=load_geojson_any(in_geo)
    if id_field not in gdf.columns or district_field not in gdf.columns:raise SystemExit("Entrada M05 sin columnas requeridas")
    if pop_field in gdf.columns:
        df_pop=gdf[[id_field,pop_field]].copy();df_pop[id_field]=df_pop[id_field].astype(str);df_pop[pop_field]=pd.to_numeric(df_pop[pop_field],errors="coerce").fillna(0).astype("int64")
        for rid,pv in zip(df_pop[id_field],df_pop[pop_field]):
            if rid in pop_map:pop_map[rid]=int(pv)
    df=gdf[[id_field,district_field]].copy();df[id_field]=df[id_field].astype(str);df[district_field]=pd.to_numeric(df[district_field],errors="coerce").fillna(-1).astype("int64");assign={rid:int(did) for rid,did in zip(df[id_field],df[district_field])};K=max(assign.values())+1;total_pop=sum(pop_map.values());target=total_pop/float(K);members=[set() for _ in range(K)];pops=[0]*K
    for n,d in assign.items():
        if d>=0:members[d].add(n);pops[d]+=pop_map.get(n,0)
    def score():return max(abs(p-target)/target for p in pops) if target>0 else 0.0
    best=score();improved=0;boundary=[]
    def rebuild_boundary():
        nonlocal boundary;boundary=[]
        for n,d in assign.items():
            if d<0:continue
            if any(assign.get(nb,-1)>=0 and assign.get(nb,-1)!=d for nb in sorted(adj.get(n,set()))):boundary.append(n)
    rebuild_boundary()
    for t in range(iters):
        if not boundary:
            rebuild_boundary()
            if not boundary:break
        n=random.choice(boundary);d_from=assign[n]
        if len(members[d_from])<=1:continue
        neigh_ds={assign.get(nb,-1) for nb in adj.get(n,set()) if assign.get(nb,-1)>=0 and assign.get(nb,-1)!=d_from}
        if not neigh_ds:continue
        d_to=random.choice(sorted(neigh_ds));popn=pop_map.get(n,0);old=best;members[d_from].remove(n);pops[d_from]-=popn;members[d_to].add(n);pops[d_to]+=popn;assign[n]=d_to;ok=district_connected(adj,members[d_from]);new=score()
        if ok and new<=old:best=new;improved+=1
        else:assign[n]=d_from;members[d_to].remove(n);pops[d_to]-=popn;members[d_from].add(n);pops[d_from]+=popn
        if (t+1)%2000==0:rebuild_boundary()
    empty=[k for k in range(K) if not members[k]]
    for k_empty in empty:
        donors=sorted([k for k in range(K) if len(members[k])>1],key=lambda kk:(-len(members[kk]),kk))
        if not donors:break
        k_donor=donors[0];cand=next((node for node in sorted(members[k_donor]) if any(assign.get(nb,-1)!=k_donor for nb in sorted(adj.get(node,set())))),min(members[k_donor]));popn=pop_map.get(cand,0);members[k_donor].remove(cand);pops[k_donor]-=popn;members[k_empty].add(cand);pops[k_empty]+=popn;assign[cand]=k_empty
    gdf["_id"]=gdf[id_field].astype(str);gdf[district_field]=gdf["_id"].map(lambda x:assign.get(x,-1)).astype("int64");write_geojson_zip(gdf.drop(columns=["_id"]),out_geo);report={"module":"05","K":K,"total_pop":int(total_pop),"target":float(target),"best_max_rel_dev":float(best),"iters":iters,"improved_moves":improved,"seed":seed}
    if out_report:write_json(report,out_report)
    print(f"[Módulo 5] OK best_max_rel_dev={best:.4f} out={out_geo}")
if __name__=="__main__":main()
