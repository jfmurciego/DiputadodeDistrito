#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
NOMBRE DE VERSIÓN: Gobernanza R015
HERRAMIENTA: Generar outputs auditables por módulo
VERSIÓN: 1.0.1
FECHA: 2026-09-11
FUNCIÓN: materializar, para una ejecución, tablas completas y manifiestos por módulo a partir de los productos canónicos M01-M08.
ENTRADAS: caché territorial M01-M03, outputs M04-M08 y configuración.
SALIDAS: ejecuciones/<run_id>/auditoria/M01..M08 con CSV/JSON/JSONL completos y referencias SHA-256 a los GeoJSON pesados.
RAZÓN DE EXISTENCIA: ningún módulo debe quedar representado solo por un contador o un log; cada estado intermedio debe ser inspeccionable y trazable sin inflar el historial Git con geometrías pesadas.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/herramientas/generar_outputs_auditables_v1.0.0.py
"""
from __future__ import annotations
import argparse, hashlib, io, json, shutil, sys, zipfile
from pathlib import Path
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from ddd_core.config import load_params_yaml,module_cfg, hard_limits

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def read_geo(p:Path):
    if p.suffix.lower()=='.zip':
        with zipfile.ZipFile(p) as z:
            m=next(n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/'))
            return gpd.read_file(io.BytesIO(z.read(m)))
    return gpd.read_file(p)
def ref(path:Path,role:str):
    return {'role':role,'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha256(path)}
def write_ref(folder:Path,items):
    (folder/'PRODUCTOS.json').write_text(json.dumps({'products':items},ensure_ascii=False,indent=2),encoding='utf-8')
def csv_no_geometry(gdf,path,cols=None):
    df=pd.DataFrame(gdf.drop(columns=['geometry'],errors='ignore'))
    if cols: df=df[[c for c in cols if c in df.columns]]
    df.to_csv(path,index=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--run-id',required=True);a=ap.parse_args()
    cfg=load_params_yaml(a.params);run=ROOT/'ejecuciones'/a.run_id;audit=run/'auditoria';audit.mkdir(parents=True,exist_ok=True)
    s1=module_cfg(cfg,'modulo_01_preparar_base_territorial','step1_build_sections');s2=module_cfg(cfg,'modulo_02_construir_adyacencias','step2_export_edges');s3=module_cfg(cfg,'modulo_03_construir_grafo','step3_build_graph');s4=module_cfg(cfg,'modulo_04_generar_semillas','step4_seed_districts');s5=module_cfg(cfg,'modulo_05_optimizar_distritos','step5_optimize_swaps');s6=module_cfg(cfg,'modulo_06_consolidar_distritos','step6_export_final');s7=module_cfg(cfg,'modulo_07_agregar_resultados_electorales','step7_elections');s8=module_cfg(cfg,'modulo_08_integrar_resultados','step8_join_results')
    # M01: catálogo completo de las 1.463 secciones, no solo contador.
    d=audit/'M01';d.mkdir(exist_ok=True);p=Path(s1['out_geojson']);g=read_geo(p);csv_no_geometry(g,d/'secciones.csv');items=[ref(p,'geometria_secciones')]
    rp=Path(s1.get('out_report','')); 
    if rp.exists(): shutil.copy2(rp,d/rp.name);items.append(ref(rp,'informe'))
    write_ref(d,items)
    # M02: las 4.293 relaciones reales.
    d=audit/'M02';d.mkdir(exist_ok=True);p=Path(s2['out_edges_jsonl']);shutil.copy2(p,d/'adyacencias.jsonl');write_ref(d,[ref(p,'adyacencias')])
    # M03: grafo completo nodos+aristas.
    d=audit/'M03';d.mkdir(exist_ok=True);p=Path(s3['out_graph_json']);shutil.copy2(p,d/'grafo.json');items=[ref(p,'grafo')];rp=Path(s3.get('out_report',''))
    if rp.exists(): shutil.copy2(rp,d/rp.name);items.append(ref(rp,'informe'))
    write_ref(d,items)
    # M04 y M05: asignación sección→distrito completa + referencia a geometría.
    for name,s,fn in [('M04',s4,'asignacion_inicial.csv'),('M05',s5,'asignacion_optimizada.csv')]:
        d=audit/name;d.mkdir(exist_ok=True);p=Path(s['out_geojson']);g=read_geo(p);cols=[s.get('id_field','CUSEC_KEY'),'CUMUN','NMUN','CPRO','NPRO',s.get('pop_field','POP_2025'),'district_id'];csv_no_geometry(g,d/fn,cols);items=[ref(p,'geometria_asignacion')];rp=Path(s.get('out_report',''))
        if rp.exists(): shutil.copy2(rp,d/rp.name);items.append(ref(rp,'informe'))
        write_ref(d,items)
    # M06: catálogo rico de distritos + composición sección a sección.
    d=audit/'M06';d.mkdir(exist_ok=True);sec=read_geo(Path(s6['out_geojson']));dist=read_geo(Path(s6['out_district_geojson']));did=s6.get('district_field','district_id');sid=s6.get('id_field','CUSEC_KEY');pop=s6.get('pop_field','POP_2025');K=int(s6.get('expected_districts',sec[did].nunique()));total=float(pd.to_numeric(sec[pop],errors='coerce').fillna(0).sum());target,floor,cap,_=hard_limits(cfg,k=K,total_pop=total);val=cfg.get('validation',{})
    rows=[]
    for district_id,x in sec.groupby(did):
        geom=dist.loc[dist['district_id'].astype(str)==str(district_id),'geometry'].iloc[0];pp=int(pd.to_numeric(x[pop],errors='coerce').fillna(0).sum());area=float(geom.area);per=float(geom.length);cent=geom.centroid;b=geom.bounds;mun_names=sorted(set(x['NMUN'].dropna().astype(str))) if 'NMUN' in x else [];provs=sorted(set(x['NPRO'].dropna().astype(str))) if 'NPRO' in x else [];compact=(4*3.141592653589793*area/(per*per)) if per else None
        rows.append({'district_id':district_id,'population':pp,'target_population':target,'population_difference':pp-target,'relative_deviation':(pp-target)/target,'population_ratio':pp/target,'floor_population':floor,'cap_population':cap,'within_hard_limits':bool(floor<=pp<=cap),'section_count':len(x),'municipality_count':x['CUMUN'].nunique() if 'CUMUN' in x else None,'municipalities':' | '.join(mun_names),'province_count':len(provs),'provinces':' | '.join(provs),'area_km2':area/1e6,'perimeter_km':per/1000,'compactness_polsby_popper':compact,'centroid_x_etrs89_utm30':cent.x,'centroid_y_etrs89_utm30':cent.y,'bbox_minx':b[0],'bbox_miny':b[1],'bbox_maxx':b[2],'bbox_maxy':b[3]})
    pd.DataFrame(rows).sort_values('district_id').to_csv(d/'catalogo_distritos.csv',index=False)
    comp_cols=[did,sid,'CUSEC','CUMUN','NMUN','CPRO','NPRO','CUDIS',pop];csv_no_geometry(sec.sort_values([did,sid]),d/'composicion_distritos.csv',comp_cols)
    write_ref(d,[ref(Path(s6['out_geojson']),'secciones_con_distrito'),ref(Path(s6['out_district_geojson']),'geometria_distritos'),ref(Path(s6['out_summary_csv']),'resumen_poblacional')])
    # M07: conservar ambos CSV completos y referencia a secciones electorales.
    d=audit/'M07';d.mkdir(exist_ok=True);items=[]
    for key,name in [('out_district_party_csv','resultados_por_partido.csv'),('out_district_summary_csv','resumen_electoral.csv')]:
        p=Path(s7[key]);shutil.copy2(p,d/name);items.append(ref(p,key))
    p=Path(s7.get('out_sections_enriched_geojson',''))
    if p.exists():items.append(ref(p,'secciones_resultados'))
    write_ref(d,items)
    # M08: tabla final completa de atributos distritales + referencia al GeoJSON final.
    d=audit/'M08';d.mkdir(exist_ok=True);p=Path(s8['out_districts_with_results_geojson']);g=read_geo(p);csv_no_geometry(g,d/'distritos_resultados.csv');write_ref(d,[ref(p,'producto_final_geografico')])
    print(f'[AUDITORÍA] Outputs completos materializados en {audit}')
if __name__=='__main__':main()
