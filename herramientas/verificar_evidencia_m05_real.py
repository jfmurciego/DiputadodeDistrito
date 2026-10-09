#!/usr/bin/env python3
"""Verifica trazabilidad y determinismo de dos ejecuciones reales de Optimización poblacional (M05).

No implementa ni invoca el algoritmo de reparación. Valida artefactos producidos por el
entrypoint productivo declarado en el manifiesto.
"""
from __future__ import annotations
import argparse, hashlib, io, json, zipfile
from pathlib import Path
import geopandas as gpd

ELAPSED_PATHS={
    ("population_repair","elapsed_seconds"),
    ("population_repair","focal_search","elapsed_seconds"),
}

def sha256(path: Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def read_zip_gdf(path:Path):
    with zipfile.ZipFile(path) as z:
        names=[n for n in z.namelist() if n.lower().endswith(('.geojson','.json')) and not n.endswith('/')]
        if len(names)!=1:raise ValueError(f'{path}: GeoJSON interno no unívoco')
        raw=z.read(names[0]); info=z.getinfo(names[0])
    return gpd.read_file(io.BytesIO(raw)),raw,info

def canonical_assignment(g)->str:
    rows=sorted((str(a),int(b)) for a,b in zip(g['CUSEC_KEY'].astype(str),g['district_id']))
    raw=''.join(f'{a},{b}\n' for a,b in rows).encode()
    return hashlib.sha256(raw).hexdigest()

def functional_report_hash(path:Path)->str:
    r=json.loads(path.read_text(encoding='utf-8'))
    (r.get('population_repair') or {}).pop('elapsed_seconds',None)
    ((r.get('population_repair') or {}).get('focal_search') or {}).pop('elapsed_seconds',None)
    raw=json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--results-root',required=True,type=Path)
    ap.add_argument('--checkpoint-zip',required=True,type=Path)
    ap.add_argument('--repo-root',required=True,type=Path)
    a=ap.parse_args(); m=json.loads(a.manifest.read_text(encoding='utf-8'))
    errors=[]
    if sha256(a.checkpoint_zip)!=m['input']['artifact_sha256']:errors.append('checkpoint_sha256')
    for row in m['source_integrity']['operational_files']:
        p=a.repo_root/row['path']
        if not p.is_file() or sha256(p)!=row['sha256']:errors.append('code:'+row['path'])
    cfg=a.repo_root/'territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml'
    if sha256(cfg)!=m['source_integrity']['territory_config_sha256']:errors.append('config_sha256')
    canonical=[]; inner=[]; functional=[]; repairs=[]; states=[]; term=[]; pops=[]
    for rn in ('run1','run2'):
        d=a.results_root/rn
        geo=d/'castilla_y_leon_2025_m05_distritos_optimizados.geojson.zip'
        rep=d/'castilla_y_leon_2025_m05_informe.json'
        g,raw,info=read_zip_gdf(geo); r=json.loads(rep.read_text(encoding='utf-8')); pr=r['population_repair']
        observed={
            'full_zip_sha256':sha256(geo),'inner_geojson_sha256':hashlib.sha256(raw).hexdigest(),
            'canonical_assignment_sha256':canonical_assignment(g),'full_report_sha256':sha256(rep),
            'functional_report_sha256':functional_report_hash(rep),
        }
        for k,v in observed.items():
            if v!=m['runs'][rn][k]:errors.append(f'{rn}:{k}')
        if len(g)!=3506 or g['CUSEC_KEY'].astype(str).nunique()!=3506:errors.append(f'{rn}:section_count')
        if g['district_id'].nunique()!=82:errors.append(f'{rn}:district_count')
        if pr['objective_after'][0]!=0 or pr['objective_after'][1]!=0:errors.append(f'{rn}:population_objective')
        canonical.append(observed['canonical_assignment_sha256']);inner.append(observed['inner_geojson_sha256']);functional.append(observed['functional_report_sha256'])
        repairs.append([(x['units'],x['donor'],x['receiver']) for x in pr['repairs']]);states.append(pr['focal_search']['states_explored']);term.append(pr['termination_reason']);pops.append(pr['population_after'])
    if len(set(canonical))!=1:errors.append('determinism:assignment')
    if len(set(inner))!=1:errors.append('determinism:geojson')
    if len(set(functional))!=1:errors.append('determinism:functional_report')
    if repairs[0]!=repairs[1]:errors.append('determinism:repairs')
    if states[0]!=states[1]:errors.append('determinism:states')
    if term[0]!=term[1]:errors.append('determinism:termination')
    if pops[0]!=pops[1]:errors.append('determinism:populations')
    result={'decision':'PASS' if not errors else 'BLOCK','errors':errors,'validated_source_head':m['validated_source_head'],'canonical_assignment_sha256':canonical[0] if canonical else None,'functional_report_sha256':functional[0] if functional else None}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if not errors else 2
if __name__=='__main__':raise SystemExit(main())
