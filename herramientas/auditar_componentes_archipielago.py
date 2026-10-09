#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Auditoría de componentes archipelágicos
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Inventario topológico por isla
FECHA: 2026-09-12
ESTADO: vigente — R026
QUÉ HACE: identifica componentes físicas del grafo y resume secciones, población, provincias, municipios y extensión métrica de cada componente.
POR QUÉ ES SEPARADA: en archipiélagos la desconexión entre islas es estructura territorial, no error ni pasarela que deba cerrarse.
CAMBIOS: primera versión.
MOTIVO: preparar contratos insulares de Baleares y Canarias antes de fijar K o abrir M04.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse,io,json,zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd

def components(nodes,edges):
    adj={str(n):set() for n in nodes}
    for e in edges:
        u,v=str(e["u"]),str(e["v"])
        if u in adj and v in adj:adj[u].add(v);adj[v].add(u)
    unseen=set(adj);out=[]
    while unseen:
        s=min(unseen);seen={s};stack=[s];unseen.remove(s)
        while stack:
            u=stack.pop()
            for v in sorted(adj[u]):
                if v in unseen:unseen.remove(v);seen.add(v);stack.append(v)
        out.append(seen)
    return sorted(out,key=lambda c:(-len(c),min(c)))

def load_geo(path):
    p=Path(path)
    if p.suffix.lower()==".zip":
        with zipfile.ZipFile(p) as z:
            n=next(x for x in z.namelist() if x.lower().endswith((".geojson",".json")))
            return gpd.read_file(io.BytesIO(z.read(n)))
    return gpd.read_file(p)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--geojson",required=True);ap.add_argument("--graph",required=True);ap.add_argument("--out",required=True);ap.add_argument("--metric-crs",default="EPSG:3035");a=ap.parse_args()
    g=load_geo(a.geojson);graph=json.loads(Path(a.graph).read_text());g["CUSEC_KEY"]=g["CUSEC_KEY"].astype(str);g["POP_2025"]=pd.to_numeric(g["POP_2025"],errors="coerce").fillna(0).astype("int64");gm=g.to_crs(a.metric_crs)
    rows=[]
    for i,c in enumerate(components(g["CUSEC_KEY"],graph.get("edges",[])),1):
        x=g[g["CUSEC_KEY"].isin(c)];xm=gm[gm["CUSEC_KEY"].isin(c)];bounds=[round(float(v),3) for v in xm.total_bounds]
        rows.append({"component_id":i,"sections":len(x),"population":int(x["POP_2025"].sum()),"province_codes":sorted(x["CPRO"].astype(str).str.zfill(2).unique()),"municipalities":int(x["CUMUN"].astype(str).nunique()),"sample_sections":sorted(c)[:20],"bounds_epsg3035":bounds})
    out={"version":"1.0.0","metric_crs":a.metric_crs,"components":len(rows),"sections":len(g),"population":int(g["POP_2025"].sum()),"component_inventory":rows}
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n");print(json.dumps(out,ensure_ascii=False))
if __name__=="__main__":main()
