#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Validación de ejecución
VERSIÓN: 1.3.1
NOMBRE DE VERSIÓN: Provincia dura y disciplina municipal — Gobernanza R015
FECHA: 2026-09-11
QUÉ HACE: valida cardinalidad, unicidad, población, contigüidad, integridad provincial y disciplina de división municipal.
ESTADO: vigente — R015 de gobernanza; lógica funcional heredada sin cambios.
CAMBIOS: normaliza cabecera y predecesor legacy; no modifica algoritmo ni contrato funcional.
MOTIVO: cerrar la deuda de auditoría y hacer verificable la disciplina de versiones.
ANTERIOR: legacy/herramientas/validar_ejecucion_v1.3.0.py
"""
from __future__ import annotations
import argparse,json,math,os,sys
from collections import defaultdict,deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import geopandas as gpd
import pandas as pd
from ddd_core.config import load_params_yaml,module_cfg, hard_limits

def read_geo(path:Path):
    return gpd.read_file(f"zip://{path}" if path.suffix==".zip" else path)

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
    os.environ['DDD_RUN_ID']=a.run_id
    cfg=load_params_yaml(a.params)
    s6=module_cfg(cfg,'modulo_06_consolidar_distritos','step6_export_final')
    s3=module_cfg(cfg,'modulo_03_construir_grafo','step3_build_graph')
    paths={'secciones':Path(s6['out_geojson']),'distritos':Path(s6['out_district_geojson']),'resumen':Path(s6['out_summary_csv']),'grafo':Path(s3['out_graph_json'])}
    fails=[];report_path=ROOT/'ejecuciones'/a.run_id/'VALIDACION.json';report_path.parent.mkdir(parents=True,exist_ok=True)
    for k,p in paths.items():
        if not p.exists():fails.append(f'falta salida {k}: {p}')
    if fails:
        report_path.write_text(json.dumps({'estado':'FAIL','failures':fails},ensure_ascii=False,indent=2),encoding='utf-8')
        print('\n'.join('[FAIL] '+x for x in fails));sys.exit(2)

    sec=read_geo(paths['secciones']);dist=read_geo(paths['distritos']);summ=pd.read_csv(paths['resumen']);graph=json.loads(paths['grafo'].read_text(encoding='utf-8'))
    val=cfg.get('validation',{}) or {}
    expected=int(val.get('expected_districts',s6.get('expected_districts',67)))
    did=s6['district_field'];sid=s6['id_field'];pop=s6['pop_field']
    province_field=str(val.get('province_field','CPRO'))
    municipality_field=str(val.get('municipality_field','CUMUN'))

    if sec[did].isna().any():fails.append('district_id nulo')
    if sec[sid].isna().any():fails.append('identificador de sección nulo')
    if sec[sid].duplicated().any():fails.append('identificadores de sección duplicados')
    k=int(sec[did].nunique())
    if k!=expected:fails.append(f'distritos={k}, esperados={expected}')
    if len(dist)!=expected:fails.append(f'geometrías distritales={len(dist)}, esperadas={expected}')

    section_pop=float(pd.to_numeric(sec[pop],errors='coerce').fillna(0).sum())
    pop_col='district_pop' if 'district_pop' in summ.columns else next((c for c in summ.columns if 'pop' in c.lower()),None)
    summary_pop=float(pd.to_numeric(summ[pop_col],errors='coerce').fillna(0).sum()) if pop_col else 0.0
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

    target,floor,cap,_=hard_limits(cfg,k=expected,total_pop=section_pop)
    pops=pd.to_numeric(summ[pop_col],errors='coerce') if pop_col else pd.Series(dtype=float)
    below=summ.loc[pops<floor,['district_id',pop_col]].to_dict('records') if pop_col else []
    above=summ.loc[pops>cap,['district_id',pop_col]].to_dict('records') if pop_col else []
    if below:fails.append(f'distritos bajo {fr:.2f}x target={len(below)}')
    if above:fails.append(f'distritos sobre {cr:.2f}x target={len(above)}')

    # R012: provincia como frontera dura.
    province_crossings=[];province_counts={}
    if bool(val.get('require_single_province_per_district',False)):
        if province_field not in sec.columns:
            fails.append(f'falta campo provincial {province_field}')
        else:
            for district_id,g in sec.groupby(did):
                provs=sorted({str(x) for x in g[province_field].dropna().astype(str)})
                if len(provs)!=1:province_crossings.append({'district_id':str(district_id),'provinces':provs})
            if province_crossings:fails.append(f'distritos interprovinciales={len(province_crossings)}')
            clean=sec.groupby(did)[province_field].agg(lambda s: sorted({str(x) for x in s.dropna().astype(str)}))
            for prov in sorted({str(x) for x in sec[province_field].dropna().astype(str)}):
                province_counts[prov]=sum(1 for xs in clean if xs==[prov])
            expected_pc={str(k):int(v) for k,v in (val.get('province_districts') or {}).items()}
            for prov,exp in expected_pc.items():
                got=int(province_counts.get(prov,0))
                if got!=exp:fails.append(f'provincia {prov}: distritos={got}, esperados={exp}')

    # R012: disciplina municipal. Un municipio pequeño no se trocea; uno grande
    # puede ocupar como máximo ceil(P/target) distritos y solo uno de ellos puede
    # ser mixto con otros municipios.
    municipality_violations=[]
    if bool(val.get('require_municipality_discipline',False)):
        if municipality_field not in sec.columns:
            fails.append(f'falta campo municipal {municipality_field}')
        else:
            work=sec[[did,municipality_field,pop]].copy()
            work[municipality_field]=work[municipality_field].astype(str)
            work[did]=work[did].astype(str)
            work[pop]=pd.to_numeric(work[pop],errors='coerce').fillna(0)
            municipality_pop=work.groupby(municipality_field)[pop].sum().to_dict()
            district_municipalities=work.groupby(did)[municipality_field].agg(lambda s:set(s)).to_dict()
            for mun,g in work.groupby(municipality_field):
                p=float(municipality_pop[mun]);dids=sorted(set(g[did]))
                min_allowed=max(1,int(math.ceil(p/cap))) if p>0 else 1
                max_allowed=max(1,int(math.ceil(p/target))) if p>0 else 1
                mixed=[d for d in dids if len(district_municipalities.get(d,set()))>1]
                reasons=[]
                if len(dids)<min_allowed:reasons.append(f'min={min_allowed}')
                if len(dids)>max_allowed:reasons.append(f'max={max_allowed}')
                if len(dids)>1 and len(mixed)>1:reasons.append(f'mixtos={len(mixed)}>1')
                if reasons:
                    municipality_violations.append({'municipality_id':mun,'population':p,'districts':dids,'mixed_districts':mixed,'allowed_min':min_allowed,'allowed_max':max_allowed,'reasons':reasons})
            if municipality_violations:fails.append(f'municipios con fragmentación inválida={len(municipality_violations)}')

    report={
        'run_id':a.run_id,'estado':'PASS' if not fails else 'FAIL','expected_districts':expected,'districts_found':k,
        'sections':len(sec),'total_population':section_pop,'target_population':target,'population_floor':floor,'population_cap':cap,
        'below_floor':below,'above_cap':above,'graph_disconnected':disconnected,
        'province_crossings':province_crossings,'province_district_counts':province_counts,
        'municipality_violations':municipality_violations,'failures':fails
    }
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if fails:
        print('\n'.join('[FAIL] '+x for x in fails));sys.exit(3)
    print(f'[OK] {k} distritos; provincias PASS; disciplina municipal PASS; contigüidad PASS; población en [{floor:.1f}, {cap:.1f}]')
if __name__=='__main__':main()
