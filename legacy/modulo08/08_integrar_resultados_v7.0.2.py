#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 08 — Integrar resultados en el mapa final
VERSIÓN: 7.0.2
NOMBRE DE VERSIÓN: Cableado modular corregido — Gobernanza R015
FECHA: 2026-09-11
QUÉ HACE: une resultados agregados con la geometría distrital.
POR QUÉ ES SEPARADO: es la unión final de dos productos ya generados y permite cambiar datos electorales sin redistritar.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/modulo08/08_integrar_resultados_v7.0.1.py
"""
from __future__ import annotations
import sys,argparse,io,zipfile
from pathlib import Path
import pandas as pd
import geopandas as gpd
PROJECT_ROOT=Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:sys.path.insert(0,str(PROJECT_ROOT))
from ddd_core.config import load_params_yaml,module_cfg,require
def load_geojson_zip(p):
    pp=Path(p).expanduser().resolve()
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp,"r") as z:
            members=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")];data=z.read(members[0])
        return gpd.read_file(io.BytesIO(data))
    return gpd.read_file(str(pp))
def write_geojson_zip(gdf,out_path):
    outp=Path(out_path);outp.parent.mkdir(parents=True,exist_ok=True);tmp=outp.parent/(outp.stem.replace(".geojson","")+".geojson");gdf.to_file(tmp,driver="GeoJSON")
    with zipfile.ZipFile(outp,"w",compression=zipfile.ZIP_DEFLATED) as z:z.write(tmp,arcname=tmp.name)
    tmp.unlink(missing_ok=True)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--params",required=True);args=ap.parse_args();cfg=load_params_yaml(args.params);s8=module_cfg(cfg,"modulo_08_integrar_resultados",legacy_step_key="step8_join_results");s7=module_cfg(cfg,"modulo_07_agregar_resultados_electorales",legacy_step_key="step7_elections");s6=module_cfg(cfg,"modulo_06_consolidar_distritos",legacy_step_key="step6_export_final");districts_geo=require(s8.get("in_district_geojson") or s6.get("out_district_geojson"),"Falta M08 geometría");results_csv=require(s8.get("in_district_summary_csv") or s7.get("out_district_summary_csv"),"Falta M08 resultados");out_geo=require(s8.get("out_districts_with_results_geojson"),"Falta M08 salida");gdf=load_geojson_zip(districts_geo);df=pd.read_csv(Path(results_csv))
    if "district_id" not in gdf.columns or "district_id" not in df.columns:raise SystemExit("Falta district_id en M08")
    gdf["district_id"]=gdf["district_id"].astype(str);df["district_id"]=df["district_id"].astype(str);out=gdf.merge(df,on="district_id",how="left");write_geojson_zip(out,out_geo);print(f"[Módulo 8] OK out={out_geo}")
if __name__=="__main__":main()
