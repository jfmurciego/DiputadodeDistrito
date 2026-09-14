#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Validación de ejecución
VERSIÓN: 1.1.1
NOMBRE DE VERSIÓN: Puerta de calidad territorial
FECHA: 2026-09-11
ESTADO: candidato
QUÉ HACE: comprueba cardinalidad, unicidad, conservación de población, contigüidad sobre el grafo y límites poblacionales; genera VALIDACION.json.
POR QUÉ EXISTE SEPARADA: una ejecución sin excepción no es necesariamente válida; el algoritmo no puede aprobarse a sí mismo.
VERSIÓN ANTERIOR: legacy/2026-09-11_github_pre_modulos/scripts/validate_run.py
"""
from __future__ import annotations
import argparse,json,sys
from collections import defaultdict,deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import geopandas as gpd
import pandas as pd
from ddd_core.config import load_params_yaml,module_cfg
def read_geo(path:Path):return gpd.read_file(f"zip://{path}" if path.suffix==".zip" else path)
def graph_components(nodes,adjacency):
    remaining=set(nodes);comps=[]
    while remaining:
        start=min(remaining);remaining.remove(start);comp={start};q=deque([start])
        while q:
            u=q.popleft()
            for v in sorted(adjacency.get(u,())):
                if v in remaining:remaining.remove(v);comp.add(v);q.append(v)
        comps.append(comp)
    return comps
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--params',required=True);a=ap.parse_args();cfg=load_params_yaml(a.params)
    s6=module_cfg(cfg,'modulo_06_consolidar_distritos','step6_export_final');s3=module_cfg(cfg,'modulo_03_construir_grafo','step3_build_graph')
    paths={'secciones':Path(s6['out_geojson']),'distritos':Path(s6['out_district_geojson']),'resumen':Path(s6['out_summary_csv']),'grafo':Path(s3['out_graph_json'])};failures=[]
    for k,p in paths.items():
        if not p.exists():failures.append(f'falta salida {k}: {p}')
    report_path=ROOT/'output/VALIDACION.json';report_path.parent.mkdir(parents=True,exist_ok=True)
    if failures:
        report_path.write_text(json.dumps({'estado':'FAIL','failures':failures},ensure_ascii=False,indent=2),encoding='utf-8');print('\n'.join('[FAIL] '+x for x in failures));sys.exit(2)
    sec=read_geo(paths['secciones']);dist=read_geo(paths['distritos']);summ=pd.read_csv(paths['resumen']);graph=json.loads(paths['grafo'].read_text(encoding='utf-8'))
    expected=int(cfg.get('validation',{}).get('expected_districts',s6.get('expected_districts',67)));did=s6['district_field'];sid=s6['id_field'];pop=s6['pop_field']
    if sec[did].isna().any():failures.append('district_id nulo')
    if sec[sid].isna().any():failures.append('identificador de sección nulo')
    if sec[sid].duplicated().any():failures.append('identificadores de sección duplicados')
    k=int(sec[did].nunique())
    if k!=expected:failures.append(f'distritos={k}, esperados={expected}')
    if len(dist)!=expected:failures.append(f'geometrías distritales={len(dist)}, esperadas={expected}')
    section_pop=float(pd.to_numeric(sec[pop],errors='coerce').fillna(0).sum());pop_col='district_pop' if 'district_pop' in summ.columns else next((c for c in summ.columns if 'pop' in c.lower()),None);summary_pop=float(pd.to_numeric(summ[pop_col],errors='coerce').fillna(0).sum()) if pop_col else 0.0
    if not pop_col:failures.append('resumen sin columna de población')
    elif abs(section_pop-summary_pop)>0.5:failures.append(f'población no conservada: secciones={section_pop} resumen={summary_pop}')
    adjacency=defaultdict(set)
    for e in graph['edges']:
        u=str(e['u']);v=str(e['v']);adjacency[u].add(v);adjacency[v].add(u)
    disconnected=[]
    for district_id,grp in sec.groupby(did):
        nodes=set(grp[sid].astype(str));comps=graph_components(nodes,adjacency)
        if len(comps)!=1:disconnected.append({'district_id':str(district_id),'components':len(comps),'sections':len(nodes)})
    if disconnected:failures.append(f'distritos desconectados en grafo={len(disconnected)}')
    target=section_pop/expected;floor_ratio=float(cfg.get('validation',{}).get('population_floor_ratio',0.80));cap_ratio=float(cfg.get('validation',{}).get('population_cap_ratio',1.75));floor=target*floor_ratio;cap=target*cap_ratio;district_pops=pd.to_numeric(summ[pop_col],errors='coerce') if pop_col else pd.Series(dtype=float);below=summ.loc[district_pops<floor,['district_id',pop_col]].to_dict('records') if pop_col else [];above=summ.loc[district_pops>cap,['district_id',pop_col]].to_dict('records') if pop_col else []
    if below:failures.append(f'distritos bajo {floor_ratio:.2f}x target={len(below)}')
    if above:failures.append(f'distritos sobre {cap_ratio:.2f}x target={len(above)}')
    report={'estado':'PASS' if not failures else 'FAIL','expected_districts':expected,'districts_found':k,'sections':len(sec),'total_population':section_pop,'target_population':target,'population_floor':floor,'population_cap':cap,'below_floor':below,'above_cap':above,'graph_disconnected':disconnected,'failures':failures};report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    if failures:print('\n'.join('[FAIL] '+x for x in failures));sys.exit(3)
    print(f'[OK] {k} distritos; contigüidad PASS; población en [{floor:.1f}, {cap:.1f}]')
if __name__=='__main__':main()
