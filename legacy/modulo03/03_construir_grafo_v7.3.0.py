#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 03 — Construir grafo territorial
VERSIÓN: 7.3.0
NOMBRE DE VERSIÓN: Bloqueo de grafos degenerados
FECHA: 2026-09-14
QUÉ HACE: construye el grafo canónico y calcula siempre que se solicite la conectividad global, provincial y municipal, separando la observación diagnóstica de las reglas que hacen fallar el contrato.
POR QUÉ ES SEPARADO: M03 es la frontera entre GIS y optimización; una discontinuidad administrativa debe detectarse aquí, no durante M04/M05, para impedir que el algoritmo trabaje sobre unidades atómicas topológicamente inválidas.
ESTADO: vigente — integración local-first.
CAMBIOS: bloquea siempre grafos sin nodos y grafos con más de un nodo pero sin aristas; conserva las auditorías configurables por nivel administrativo.
MOTIVO: una ejecución histórica avanzó hasta M08 con 1.463 nodos y cero aristas; esa entrada es estructuralmente inválida con independencia de la política territorial.
ANTERIOR: legacy/modulo03/03_construir_grafo_v7.2.0.py
"""
from __future__ import annotations
import sys,argparse,io,json,zipfile,collections
from pathlib import Path
from typing import Any,List,Tuple
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

def validate_minimum_graph(nodes,edges):
    """Impide que una preparación topológicamente vacía avance a optimización."""
    if not nodes:raise SystemExit("M03: grafo sin nodos; no existe universo territorial")
    if len(nodes)>1 and not edges:raise SystemExit(f"M03: grafo degenerado: {len(nodes)} nodos y cero aristas")

def write_json(obj:Any,out_path:str):
    outp=Path(out_path).expanduser().resolve();outp.parent.mkdir(parents=True,exist_ok=True);outp.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

def component_sets(nodes,adj):
    unseen=set(nodes);comps=[]
    while unseen:
        s=next(iter(unseen));unseen.remove(s);seen={s};q=[s]
        while q:
            u=q.pop()
            for v in adj.get(u,set()):
                if v in unseen:
                    unseen.remove(v);seen.add(v);q.append(v)
        comps.append(seen)
    return sorted(comps,key=lambda c:(-len(c),sorted(c)[0] if c else ""))

def audit_group_components(gdf,id_field,group_fields,adj,name_field=None):
    cols=list(group_fields)+[id_field]+([name_field] if name_field and name_field in gdf.columns else [])
    x=gdf[cols].copy();x[id_field]=x[id_field].astype(str)
    out={};bad=[]
    grouper=group_fields[0] if len(group_fields)==1 else list(group_fields)
    for key,grp in x.groupby(grouper,dropna=False):
        if not isinstance(key,tuple):key=(key,)
        k="/".join(str(v) for v in key);nodes=set(grp[id_field]);comps=component_sets(nodes,adj)
        rec={"nodes":len(nodes),"components":len(comps),"component_sizes":[len(c) for c in comps]}
        if name_field and name_field in grp.columns:rec["name"]=str(grp[name_field].iloc[0])
        if len(comps)>1:
            rec["component_samples"]=[sorted(c)[:12] for c in comps]
            bad.append({"key":k,**rec})
        out[k]=rec
    return out,bad

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s3=module_cfg(cfg,"modulo_03_construir_grafo",legacy_step_key="step3_build_graph");val=cfg.get("validation",{}) or {}
    in_geo=require(s3.get("in_geojson",""),"Falta módulo 03 in_geojson");in_edges=require(s3.get("in_edges_jsonl",""),"Falta módulo 03 in_edges_jsonl");id_field=require(s3.get("id_field",""),"Falta módulo 03 id_field");pop_field=require(s3.get("pop_field",""),"Falta módulo 03 pop_field");out_graph=require(s3.get("out_graph_json",""),"Falta módulo 03 out_graph_json");out_report=s3.get("out_report","") or ""
    gdf=load_geojson_any(in_geo)
    if id_field not in gdf.columns:raise SystemExit(f"M03: GeoJSON sin id_field '{id_field}'.")
    if pop_field not in gdf.columns:raise SystemExit(f"M03: GeoJSON sin pop_field '{pop_field}'.")
    df=gdf[[id_field,pop_field]].copy();df[id_field]=df[id_field].astype(str);df[pop_field]=pd.to_numeric(df[pop_field],errors="coerce").fillna(0).astype("int64")
    nodes=[{"id":rid,"pop":int(pop)} for rid,pop in zip(df[id_field].tolist(),df[pop_field].tolist())];pop_map={n["id"]:n["pop"] for n in nodes};edges=load_edges_jsonl(in_edges);edges_f=[{"u":u,"v":v} for u,v in edges if u in pop_map and v in pop_map]
    validate_minimum_graph(nodes,edges_f)
    adj={n:set() for n in pop_map}
    for e in edges_f:
        adj[e["u"]].add(e["v"]);adj[e["v"]].add(e["u"])
    isolated=sum(1 for n in pop_map if not adj[n]);total_pop=int(sum(pop_map.values()))
    province_field=str(val.get("province_field","CPRO"));municipality_field=str(val.get("municipality_field","CUMUN"));municipality_name_field=str(val.get("municipality_name_field","NMUN"))
    audit_global=bool(val.get("audit_graph_components",True))
    audit_province=bool(val.get("audit_admin_level_1_components",val.get("require_one_graph_component_per_province",False)))
    audit_municipality=bool(val.get("audit_admin_level_2_components",val.get("require_connected_municipalities",False)))
    global_components=component_sets(set(pop_map),adj) if audit_global else []
    global_audit={"enabled":audit_global,"components":len(global_components),"component_sizes":[len(c) for c in global_components],"component_samples":[sorted(c)[:12] for c in global_components]}
    province_audit={};province_bad=[];municipality_audit={};municipality_bad=[]
    if audit_province:
        if province_field not in gdf.columns:raise SystemExit(f"M03: falta province_field '{province_field}' requerido por validación")
        gx=gdf.copy();gx[province_field]=gx[province_field].astype(str).str.zfill(2)
        province_audit,province_bad=audit_group_components(gx,id_field,[province_field],adj)
    if audit_municipality:
        for c in (province_field,municipality_field):
            if c not in gdf.columns:raise SystemExit(f"M03: falta campo administrativo '{c}' requerido por validación municipal")
        gx=gdf.copy();gx[province_field]=gx[province_field].astype(str).str.zfill(2);gx[municipality_field]=gx[municipality_field].astype(str).str.zfill(5)
        municipality_audit,municipality_bad=audit_group_components(gx,id_field,[province_field,municipality_field],adj,municipality_name_field)
    report={"module":"03","version":"7.3.0","nodes":len(nodes),"edges":len(edges_f),"isolated":isolated,"total_pop":total_pop,"id_field":id_field,"pop_field":pop_field,"out_graph_json":out_graph,"global_component_audit":global_audit,"province_component_audit":{"enabled":audit_province,"enforced":bool(val.get("require_one_graph_component_per_province",False)),"groups":len(province_audit),"disconnected":len(province_bad),"details":province_audit,"violations":province_bad},"municipality_component_audit":{"enabled":audit_municipality,"enforced":bool(val.get("require_connected_municipalities",False)),"groups":len(municipality_audit),"disconnected":len(municipality_bad),"details":municipality_audit,"violations":municipality_bad}}
    write_json({"nodes":nodes,"edges":edges_f},out_graph)
    if out_report:write_json(report,out_report)
    if province_bad and bool(val.get("require_one_graph_component_per_province",False)):raise SystemExit(f"M03: provincias desconectadas tras M02: {province_bad}")
    if municipality_bad and bool(val.get("require_connected_municipalities",False)):raise SystemExit(f"M03: municipios desconectados tras M02: {municipality_bad}")
    print(f"[Módulo 3] OK v7.3.0 nodes={len(nodes)} edges={len(edges_f)} isolated={isolated} provincias_bad={len(province_bad)} municipios_bad={len(municipality_bad)} out={out_graph}")
if __name__=="__main__":main()
