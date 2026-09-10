#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict, deque
from pathlib import Path
import geopandas as gpd
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]

def resolve(v, run_name, year, scope):
    return (ROOT / str(v).format(run_name=run_name, year=year, scope=scope)).resolve()

def read_geo(path: Path):
    return gpd.read_file(f"zip://{path}" if path.suffix == ".zip" else path)

def graph_components(nodes, adjacency):
    remaining = set(nodes)
    comps = []
    while remaining:
        start = next(iter(remaining)); remaining.remove(start)
        comp = {start}; q = deque([start])
        while q:
            u = q.popleft()
            for v in adjacency.get(u, ()):
                if v in remaining:
                    remaining.remove(v); comp.add(v); q.append(v)
        comps.append(comp)
    return comps

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--params', required=True); a = ap.parse_args()
    cfg = yaml.safe_load((ROOT / a.params).read_text(encoding='utf-8'))
    meta = cfg['meta']; rn = meta['run_name']; year = meta['year']; scope = meta.get('scope','provincial'); s = cfg['steps']
    s6 = s['step6_export_final']; s3 = s['step3_build_graph']
    section_path = resolve(s6['out_geojson'], rn, year, scope)
    district_path = resolve(s6['out_district_geojson'], rn, year, scope)
    summary_path = resolve(s6['out_summary_csv'], rn, year, scope)
    graph_path = resolve(s3['out_graph_json'], rn, year, scope)
    failures=[]
    for p in [section_path,district_path,summary_path,graph_path]:
        if not p.exists(): failures.append(f'missing output: {p.relative_to(ROOT)}')
    if failures:
        print('\n'.join('[FAIL] '+x for x in failures)); sys.exit(2)

    sec=read_geo(section_path); dist=read_geo(district_path); summ=pd.read_csv(summary_path)
    graph=json.loads(graph_path.read_text(encoding='utf-8'))
    expected=int(s6['expected_districts']); did=s6['district_field']; sid=s6['id_field']; pop=s6['pop_field'].format(year=year)
    if sec[did].isna().any(): failures.append('null district_id in section output')
    if sec[sid].isna().any(): failures.append('null section id')
    if sec[sid].duplicated().any(): failures.append('duplicate section ids')
    k=int(sec[did].nunique())
    if k != expected: failures.append(f'district count={k}, expected={expected}')
    if len(dist) != expected: failures.append(f'dissolved district features={len(dist)}, expected={expected}')

    section_pop=float(pd.to_numeric(sec[pop],errors='coerce').fillna(0).sum())
    pop_col='district_pop' if 'district_pop' in summ.columns else next((c for c in summ.columns if 'pop' in c.lower()),None)
    if not pop_col:
        failures.append('district summary has no population column')
        summary_pop=0.0
    else:
        summary_pop=float(pd.to_numeric(summ[pop_col],errors='coerce').fillna(0).sum())
        if abs(section_pop-summary_pop)>0.5: failures.append(f'population mismatch sections={section_pop} summary={summary_pop}')

    adjacency=defaultdict(set)
    for e in graph['edges']:
        u=str(e['u']); v=str(e['v']); adjacency[u].add(v); adjacency[v].add(u)
    disconnected=[]
    for district_id, grp in sec.groupby(did):
        nodes=set(grp[sid].astype(str))
        comps=graph_components(nodes, adjacency)
        if len(comps) != 1: disconnected.append({'district_id':str(district_id),'components':len(comps),'sections':len(nodes)})
    if disconnected: failures.append(f'graph-disconnected districts={len(disconnected)}')

    target=section_pop/expected
    floor_ratio=float(cfg.get('validation',{}).get('population_floor_ratio',0.80))
    cap_ratio=float(cfg.get('validation',{}).get('population_cap_ratio',1.75))
    floor=target*floor_ratio; cap=target*cap_ratio
    district_pops=pd.to_numeric(summ[pop_col],errors='coerce') if pop_col else pd.Series(dtype=float)
    below=summ.loc[district_pops < floor, ['district_id',pop_col]].to_dict('records') if pop_col else []
    above=summ.loc[district_pops > cap, ['district_id',pop_col]].to_dict('records') if pop_col else []
    if below: failures.append(f'districts below {floor_ratio:.2f}x target={len(below)}')
    if above: failures.append(f'districts above {cap_ratio:.2f}x target={len(above)}')

    report={
      'expected_districts':expected,'districts_found':k,'sections':len(sec),'total_population':section_pop,
      'target_population':target,'population_floor':floor,'population_cap':cap,
      'below_floor':below,'above_cap':above,'graph_disconnected':disconnected,'failures':failures
    }
    (ROOT/'output/VALIDATION.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    if failures:
        print('\n'.join('[FAIL] '+x for x in failures)); sys.exit(3)
    print(f'[OK] validation: {k} districts, graph contiguous, population within [{floor:.1f}, {cap:.1f}]')

if __name__=='__main__': main()
