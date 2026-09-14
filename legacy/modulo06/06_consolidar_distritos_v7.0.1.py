#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 06 — Consolidar distritos
VERSIÓN: 7.0.1
NOMBRE DE VERSIÓN: Profesionalización reproducible — Gobernanza R015
FECHA: 2026-09-11
QUÉ HACE: genera resúmenes poblacionales y geometrías finales.
POR QUÉ ES SEPARADO: la optimización no debe controlar el formato de publicación ni sus validaciones.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/modulo06/06_consolidar_distritos_v7.0.0.py
"""
from __future__ import annotations
import sys,argparse,io,zipfile
from pathlib import Path
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
    if p.suffix.lower()==".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p,"r") as z:
            members=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")];data=z.read(members[0])
        return _gpd_read_file(io.BytesIO(data))
    return _gpd_read_file(str(p))
def ensure_geojson_zip(gdf,out_zip):
    outp=Path(out_zip);outp.parent.mkdir(parents=True,exist_ok=True);tmp=outp.parent/(outp.stem.replace(".geojson","")+".geojson");gdf.to_file(tmp,driver="GeoJSON")
    with zipfile.ZipFile(outp,"w",compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s6=module_cfg(cfg,"modulo_06_consolidar_distritos",legacy_step_key="step6_export_final");in_geo=require(s6.get("in_geojson"),"Falta M06 entrada");id_field=require(s6.get("id_field"),"Falta M06 id");district_field=require(s6.get("district_field"),"Falta M06 distrito");pop_field=require(s6.get("pop_field"),"Falta M06 población");out_summary=require(s6.get("out_summary_csv"),"Falta M06 resumen");out_geo=s6.get("out_geojson","");gdf=load_geojson_any(in_geo)
    for col in (id_field,district_field,pop_field):
        if col not in gdf.columns:raise SystemExit(f"Entrada sin columna '{col}'")
    df=gdf.copy();df[id_field]=df[id_field].astype(str);df[district_field]=df[district_field].astype(str);df[pop_field]=pd.to_numeric(df[pop_field],errors="coerce").fillna(0).astype("int64");exp_k=int(s6.get("expected_districts",0) or 0);summ=df.groupby(district_field,as_index=False)[pop_field].sum().rename(columns={pop_field:"district_pop",district_field:"district_id"}).sort_values("district_id").reset_index(drop=True)
    if exp_k and bool(s6.get("strict_expected_k",True)) and len(summ)!=exp_k:raise SystemExit(f"[Módulo 6] ERROR: distritos={len(summ)} esperados={exp_k}")
    out_district_geo=s6.get("out_district_geojson","")
    if out_district_geo:
        work=df.copy();dist_gdf=work.dissolve(by=district_field,aggfunc={pop_field:"sum"},as_index=False).rename(columns={district_field:"district_id",pop_field:"district_pop"});ensure_geojson_zip(dist_gdf,out_district_geo)
    outp=Path(out_summary);outp.parent.mkdir(parents=True,exist_ok=True);summ.to_csv(outp,index=False)
    if out_geo:ensure_geojson_zip(gdf,out_geo)
    print(f"[Módulo 6] OK summary_rows={len(summ)} out_summary={out_summary}")
if __name__=="__main__":main()
