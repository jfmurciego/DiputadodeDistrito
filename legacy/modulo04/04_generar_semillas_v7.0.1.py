#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.0.1
NOMBRE DE VERSIÓN: Semillado determinista y contiguo
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: genera una asignación inicial contigua de secciones a K distritos.
POR QUÉ ES SEPARADO: inicialización y optimización son problemas distintos y deben poder compararse independientemente.
CAMBIOS: corrige no determinismo por iteración de sets y elimina un fallback que podía romper contigüidad.
VERSIÓN ANTERIOR: legacy/2026-09-11_modulo04_v7.0.0/04_generar_semillas.py
"""
from __future__ import annotations
import sys,argparse,io,json,zipfile,random,collections
from pathlib import Path
from typing import Dict,Any
PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:sys.path.insert(0,str(PROJECT_ROOT))
import geopandas as gpd
from ddd_core.config import load_params_yaml,module_cfg,require
def _gpd_read_file(path_or_buf,layer=None):
    try:
        import pyogrio;return pyogrio.read_dataframe(path_or_buf,layer=layer)
    except Exception:pass
    try:return gpd.read_file(path_or_buf,layer=layer,engine="pyogrio")
    except Exception:return gpd.read_file(path_or_buf,layer=layer)
def load_geojson_any(path_str):
    p=Path(path_str).expanduser().resolve()
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
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s4=module_cfg(cfg,"modulo_04_generar_semillas",legacy_step_key="step4_seed_districts");in_graph=require(s4.get("in_graph_json"),"Falta M04 grafo");in_geo=require(s4.get("in_geojson"),"Falta M04 geojson");id_field=require(s4.get("id_field"),"Falta M04 id");K=int(require(s4.get("k_districts"),"Falta M04 K"));out_geo=require(s4.get("out_geojson"),"Falta M04 salida");out_report=s4.get("out_report","");seed=int(s4.get("seed",12345));random.seed(seed)
    G=load_graph(in_graph);nodes=[n["id"] for n in G.get("nodes",[])];pop_map={n["id"]:int(n.get("pop",0)) for n in G.get("nodes",[])};adj={nid:set() for nid in nodes}
    for e in G.get("edges",[]):
        u=str(e["u"]);v=str(e["v"])
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    total_pop=sum(pop_map.values());target=total_pop/float(K);deg=sorted([(len(adj[n]),n) for n in nodes],reverse=True);seed_nodes=[n for _,n in deg[:max(K*3,K)]];random.shuffle(seed_nodes);seeds=seed_nodes[:K] if len(seed_nodes)>=K else nodes[:K];assign={n:None for n in nodes};dist_pops=[0]*K;frontiers=[collections.deque() for _ in range(K)]
    for k,s in enumerate(seeds):
        assign[s]=k;dist_pops[k]+=pop_map.get(s,0)
        for nb in sorted(adj[s]):
            if assign[nb] is None:frontiers[k].append(nb)
    unassigned={n for n,v in assign.items() if v is None};safety=0
    while unassigned and safety<len(nodes)*20:
        safety+=1;k=min(range(K),key=lambda i:(dist_pops[i]/target,i))
        if not frontiers[k]:
            boundary=[]
            for u in sorted(unassigned):
                neighbor_ds=sorted({assign.get(nb) for nb in adj.get(u,set()) if assign.get(nb) is not None})
                if neighbor_ds:
                    kk=min(neighbor_ds,key=lambda d:(dist_pops[d]/target,d));boundary.append((dist_pops[kk]/target,u,kk))
            if not boundary:
                start=min(unassigned);assign[start]=k;dist_pops[k]+=pop_map.get(start,0);unassigned.remove(start);continue
            _,start,kk=min(boundary);assign[start]=kk;dist_pops[kk]+=pop_map.get(start,0);unassigned.remove(start)
            for nb in sorted(adj[start]):
                if assign.get(nb) is None:frontiers[kk].append(nb)
            continue
        cand=frontiers[k].popleft()
        if assign[cand] is not None:continue
        if any(assign.get(nb)==k for nb in adj[cand]):
            assign[cand]=k;dist_pops[k]+=pop_map.get(cand,0);unassigned.remove(cand)
            for nb in sorted(adj[cand]):
                if assign.get(nb) is None:frontiers[k].append(nb)
    gdf=load_geojson_any(in_geo);gdf["_id"]=gdf[id_field].astype(str);gdf["district_id"]=gdf["_id"].map(lambda x:assign.get(x,-1)).astype("int64");gdf["district_pop"]=gdf["_id"].map(lambda x:pop_map.get(x,0)).astype("int64");write_geojson_zip(gdf.drop(columns=["_id"]),out_geo);report={"module":"04","K":K,"total_pop":int(total_pop),"target":float(target),"min_pop":int(min(dist_pops)),"max_pop":int(max(dist_pops)),"assigned_missing":sum(1 for v in assign.values() if v is None),"seed":seed}
    if out_report:write_json(report,out_report)
    print(f"[Módulo 4] OK K={K} target≈{target:.1f} out={out_geo}")
if __name__=="__main__":main()
