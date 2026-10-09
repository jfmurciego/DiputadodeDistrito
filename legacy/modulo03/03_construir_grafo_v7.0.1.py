#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 03 — Construir grafo territorial
VERSIÓN: 7.0.1
NOMBRE DE VERSIÓN: Profesionalización reproducible — Gobernanza R015
FECHA: 2026-09-11
QUÉ HACE: construye el grafo de secciones, población y adyacencias.
POR QUÉ ES SEPARADO: desacopla GIS y optimización y constituye el contrato territorial del algoritmo.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/modulo03/03_construir_grafo_v7.0.0.py
"""
from __future__ import annotations
import sys,argparse,io,json,zipfile
from pathlib import Path
from typing import Dict,Any,List,Tuple
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
def load_geojson_any(path_str:str)->gpd.GeoDataFrame:
    p=Path(path_str).expanduser().resolve()
    if not p.exists():raise FileNotFoundError(f"GeoJSON no encontrado: {p}")
    if p.suffix.lower()==".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p,"r") as z:
            members=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            if not members:raise ValueError(f"ZIP GeoJSON sin .geojson/.json: {p}")
            data=z.read(members[0])
        return _gpd_read_file(io.BytesIO(data))
    return _gpd_read_file(str(p))
def load_edges_jsonl(path_str:str)->List[Tuple[str,str]]:
    p=Path(path_str).expanduser().resolve()
    if not p.exists():raise FileNotFoundError(f"Edges JSONL no encontrado: {p}")
    edges=[]
    with p.open("r",encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:continue
            o=json.loads(line);u=str(o.get("u"));v=str(o.get("v"))
            if u and v and u!=v:edges.append((u,v))
    return edges
def write_json(obj:Any,out_path:str):
    outp=Path(out_path).expanduser().resolve();outp.parent.mkdir(parents=True,exist_ok=True);outp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s3=module_cfg(cfg,"modulo_03_construir_grafo",legacy_step_key="step3_build_graph")
    in_geo=require(s3.get("in_geojson",""),"Falta módulo 03 in_geojson");in_edges=require(s3.get("in_edges_jsonl",""),"Falta módulo 03 in_edges_jsonl");id_field=require(s3.get("id_field",""),"Falta módulo 03 id_field");pop_field=require(s3.get("pop_field",""),"Falta módulo 03 pop_field");out_graph=require(s3.get("out_graph_json",""),"Falta módulo 03 out_graph_json");out_report=s3.get("out_report","") or ""
    gdf=load_geojson_any(in_geo)
    if id_field not in gdf.columns:raise SystemExit(f"GeoJSON sin id_field '{id_field}'.")
    if pop_field not in gdf.columns:raise SystemExit(f"GeoJSON sin pop_field '{pop_field}'.")
    df=gdf[[id_field,pop_field]].copy();df[id_field]=df[id_field].astype(str);df[pop_field]=pd.to_numeric(df[pop_field],errors="coerce").fillna(0).astype("int64");nodes=[{"id":rid,"pop":int(pop)} for rid,pop in zip(df[id_field].tolist(),df[pop_field].tolist())];pop_map={n["id"]:n["pop"] for n in nodes};edges=load_edges_jsonl(in_edges);edges_f=[{"u":u,"v":v} for u,v in edges if u in pop_map and v in pop_map];deg={}
    for e in edges_f:deg[e["u"]]=deg.get(e["u"],0)+1;deg[e["v"]]=deg.get(e["v"],0)+1
    isolated=sum(1 for n in pop_map if deg.get(n,0)==0);total_pop=int(sum(pop_map.values()));report={"module":"03","nodes":len(nodes),"edges":len(edges_f),"isolated":isolated,"total_pop":total_pop,"id_field":id_field,"pop_field":pop_field,"out_graph_json":out_graph};write_json({"nodes":nodes,"edges":edges_f},out_graph)
    if out_report:write_json(report,out_report)
    print(f"[Módulo 3] OK nodes={len(nodes)} edges={len(edges_f)} isolated={isolated} out={out_graph}")
if __name__=="__main__":main()
