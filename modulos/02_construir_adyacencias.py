#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 02 — Construir adyacencias
VERSIÓN: 7.0.0
NOMBRE DE VERSIÓN: Profesionalización reproducible
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: calcula relaciones de vecindad entre secciones.
POR QUÉ ES SEPARADO: la adyacencia depende de la cartografía, no del algoritmo de reparto; puede auditarse y reutilizarse.
VERSIÓN ANTERIOR: legacy/2026-09-11_github_pre_modulos/scripts/ddd_step2_export_edges_v6_params.py
"""
from __future__ import annotations
import sys,argparse,io,json,zipfile
from pathlib import Path
from typing import Iterable,Tuple
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
    if not p.exists():raise FileNotFoundError(f"GeoJSON no encontrado: {p}")
    if p.suffix.lower()==".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p,"r") as z:
            members=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            if not members:raise ValueError(f"ZIP GeoJSON sin .geojson/.json: {p}")
            data=z.read(members[0])
        return _gpd_read_file(io.BytesIO(data))
    return _gpd_read_file(str(p))
def iter_edges(gdf,id_field,predicate,min_shared_border_m,buffer_m,simplify_m,max_candidates,log_every)->Iterable[Tuple[str,str]]:
    if id_field not in gdf.columns:raise SystemExit(f"id_field '{id_field}' no existe")
    gdf=gdf.copy();gdf[id_field]=gdf[id_field].astype(str)
    if gdf.crs is None:gdf=gdf.set_crs(25830,allow_override=True)
    else:
        try:gdf=gdf.to_crs(25830)
        except Exception:pass
    geom=gdf.geometry
    if simplify_m and simplify_m>0:geom=geom.simplify(simplify_m,preserve_topology=True)
    if buffer_m and buffer_m!=0:geom=geom.buffer(buffer_m)
    gdf["_geom_work"]=geom;sindex=gdf.sindex;seen=set()
    for i,row in gdf.iterrows():
        gi=row["_geom_work"]
        if gi is None or gi.is_empty:continue
        cand_idx=list(sindex.intersection(gi.bounds))
        if max_candidates and len(cand_idx)>max_candidates:
            ib=gi.bounds;icx,icy=(ib[0]+ib[2])/2,(ib[1]+ib[3])/2
            def _dist(j):
                jb=gdf.loc[j,"_geom_work"].bounds;jcx,jcy=(jb[0]+jb[2])/2,(jb[1]+jb[3])/2;return (icx-jcx)**2+(icy-jcy)**2
            cand_idx=sorted(cand_idx,key=_dist)[:max_candidates]
        u=row[id_field]
        for j in cand_idx:
            if j==i:continue
            v=gdf.loc[j,id_field];a,b=(u,v) if u<v else (v,u);key=(a,b)
            if key in seen:continue
            gj=gdf.loc[j,"_geom_work"]
            if gj is None or gj.is_empty:continue
            ok=gi.touches(gj) if predicate=="touches" else gi.intersects(gj) if predicate=="intersects" else False
            if not ok:continue
            if min_shared_border_m and min_shared_border_m>0 and gi.boundary.intersection(gj.boundary).length<min_shared_border_m:continue
            seen.add(key)
            if log_every and len(seen)%log_every==0:print(f"[Módulo 2] edges={len(seen)}")
            yield key
def write_edges_jsonl(edges,out_path):
    outp=Path(out_path);outp.parent.mkdir(parents=True,exist_ok=True);n=0
    with outp.open("w",encoding="utf-8") as f:
        for u,v in edges:f.write(json.dumps({"u":u,"v":v},ensure_ascii=False)+"\n");n+=1
    return n
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s2=module_cfg(cfg,"modulo_02_construir_adyacencias",legacy_step_key="step2_export_edges");in_geo=require(s2.get("in_geojson"),"Falta M02 entrada");id_field=require(s2.get("id_field"),"Falta M02 id");out_edges=require(s2.get("out_edges_jsonl"),"Falta M02 salida");gdf=load_geojson_any(in_geo);edges=iter_edges(gdf,id_field,s2.get("predicate","touches"),float(s2.get("min_shared_border_m",0)),float(s2.get("buffer_m",0)),float(s2.get("simplify_m",0)),int(s2.get("max_candidates",50)),int(s2.get("log_every",10000)));n=write_edges_jsonl(edges,out_edges);print(f"[Módulo 2] OK edges={n} out={out_edges}")
if __name__=="__main__":main()
