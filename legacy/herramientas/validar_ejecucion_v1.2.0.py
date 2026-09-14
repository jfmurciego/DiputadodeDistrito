#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Validación de ejecución
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Puerta de calidad por ejecución
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: valida cardinalidad, unicidad, población y contigüidad de la ejecución indicada y escribe su VALIDACION.json.
POR QUÉ CAMBIA: cada corrida debe conservar su propio veredicto; la validación no puede ser global ni sobrescribible.
VERSIÓN ANTERIOR: legacy/herramientas/validar_ejecucion_v1.1.1.py
"""
from __future__ import annotations
import argparse,json,os,sys
from collections import defaultdict,deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import geopandas as gpd
import pandas as pd
from ddd_core.config import load_params_yaml,module_cfg
def read_geo(path:Path):return gpd.read_file(f"zip://{path}" if path.suffix==".zip" else path)
def components(nodes,adj):
    rem=set(nodes);n=0
    while rem:
        n+=1;q=deque([rem.pop()])
        while q:
            u=q.popleft()
            for v in adj.get(u,()):
                if v in rem:rem.remove(v);q.append(v)
    return n
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);ap.add_argument('--run-id',default=os.getenv('DDD_RUN_ID'));a=ap.parse_args()
    if not a.run_id:raise SystemExit('Falta --run-id/DDD_RUN_ID')
    os.environ['DDD_RUN_ID']=a.run_id;cfg=load_params_yaml(a.params);s6=module_cfg(cfg,'modulo_06_consolidar_distritos','step6_export_final');s3=module_cfg(cfg,'modulo_03_construir_grafo','step3_build_graph')
    paths={'secciones':Path(s6['out_geojson']),'distritos':Path(s6['out_district_geojson']),'resumen':Path(s6['out_summary_csv']),'grafo':Path(s3['out_graph_json'])};fails=[];report_path=ROOT/'ejecuciones'/a.run_id/'VALIDACION.json';report_path.parent.mkdir(parents=True,exist_ok=True)
    for k,p in paths.items():
        if not p.exists():fails.append(f'falta salida {k}: {p}')
    if fails:report_path.write_text(json.dumps({'estado':'FAIL','failures':fails},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join('[FAIL] '+x for x in fails));sys.exit(2)
    sec=read_geo(paths['secciones']);dist=read_geo(paths['distritos']);summ=pd.read_csv(paths['resumen']);graph=json.loads(paths['grafo'].read_text(encoding='utf-8'));val=cfg.get('validation',{});expected=int(val.get('expected_districts',s6.get('expected_districts',67)));did=s6['district_field'];sid=s6['id_field'];pop=s6['pop_field']
    if sec[did].isna().any():fails.append('district_id nulo')
    if sec[sid].isna().any():fails.append('identificador de sección nulo')
    if sec[sid].duplicated().any():fails.append('identificadores de sección duplicados')
    k=int(sec[did].nunique())
    if k!=expected:fails.append(f'distritos={k}, esperados={expected}')
    if len(dist)!=expected:fails.append(f'geometrías distritales={len(dist)}, esperadas={expected}')
    section_pop=float(pd.to_numeric(sec[pop],errors='coerce').fillna(0).sum());pop_col='district_pop' if 'district_pop' in summ.columns else next((c for c in summ.columns if 'pop' in c.lower()),None);summary_pop=float(pd.to_numeric(summ[pop_col],errors='coerce').fillna(0).sum()) if pop_col else 0.0
    if not pop_col:fails.append('resumen sin columna de población')
    elif abs(section_pop-summary_pop)>0.5:fails.append(f'población no conservada: {section_pop} vs {summary_pop}')
    adj=defaultdict(set)
    for e in graph['edges']:
        u=str(e['u']);v=str(e['v']);adj[u].add(v);adj[v].add(u)
    disconnected=[]
    for district_id,g in sec.groupby(did):
        n=components(set(g[sid].astype(str)),adj)
        if n!=1:disconnected.append({'district_id':str(district_id),'components':n})
    if disconnected:fails.append(f'distritos desconectados en grafo={len(disconnected)}')
    target=section_pop/expected;fr=float(val.get('population_floor_ratio',.8));cr=float(val.get('population_cap_ratio',1.75));floor=target*fr;cap=target*cr;pops=pd.to_numeric(summ[pop_col],errors='coerce') if pop_col else pd.Series(dtype=float);below=summ.loc[pops<floor,['district_id',pop_col]].to_dict('records') if pop_col else [];above=summ.loc[pops>cap,['district_id',pop_col]].to_dict('records') if pop_col else []
    if below:fails.append(f'distritos bajo {fr:.2f}x target={len(below)}')
    if above:fails.append(f'distritos sobre {cr:.2f}x target={len(above)}')
    report={'run_id':a.run_id,'estado':'PASS' if not fails else 'FAIL','expected_districts':expected,'districts_found':k,'sections':len(sec),'total_population':section_pop,'target_population':target,'population_floor':floor,'population_cap':cap,'below_floor':below,'above_cap':above,'graph_disconnected':disconnected,'failures':fails};report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if fails:print('\n'.join('[FAIL] '+x for x in fails));sys.exit(3)
    print(f'[OK] {k} distritos; contigüidad PASS; población en [{floor:.1f}, {cap:.1f}]')
if __name__=='__main__':main()
