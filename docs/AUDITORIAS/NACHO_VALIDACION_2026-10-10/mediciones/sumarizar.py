#!/usr/bin/env python3
"""v1.0.0,2026-10-10,Work: resumen determinista de métricas, sin ejecutar motores.
Origen: nuevas medidasE2; sin predecesor ni cambios de producción.
"""
from pathlib import Path
import json,statistics
p=Path(__file__).resolve().parent;x=json.loads((p/'e2-results.json').read_text())
rows=x['runs'];passed=len(rows)==12 and all(r.get('status')=='PASS' for r in rows)
by={(r['fixture'],r['mode'],r['seed']):r for r in rows}
paired=[]
if passed:
 for fixture in ['A_lower_L1','B_lower_max']:
  for seed in [17,29,43]:
   c=by[fixture,'canonical',seed];r=by[fixture,'recom',seed];m=c['metrics'];n=r['metrics']
   assert c['fixture_sha256']==r['fixture_sha256']
   assert not m['hard_violations'] and not n['hard_violations']
   paired.append({'fixture':fixture,'seed':seed,'population_max_improves':n['population_max_relative']<m['population_max_relative'],'shape_median_improves':n['polsby_popper_median']>m['polsby_popper_median'],'time_ratio_recom_to_canonical':r['seconds_engine_including_io_instrumentation']/c['seconds_engine_including_io_instrumentation']})
x['decision']='MEJORA_DEMOSTRADA' if passed and any(r['population_max_improves'] or r['shape_median_improves'] for r in paired) else 'NO_EVALUABLE' if not passed else 'SIN_VENTAJA_DEMOSTRADA'
x['decision_scope']='Comparación a mismos topes máximos, sin equivalencia de tiempo gastado ni ley de propuestas; no evidencia de reparación duraA2'
x['a2_decision']='SIN_VENTAJA_DEMOSTRADA';x['pairs']=paired;x['summary']={}
for fixture in ['A_lower_L1','B_lower_max']:
 x['summary'][fixture]={}
 for mode in ['canonical','recom']:
  group=[r for r in rows if r['fixture']==fixture and r['mode']==mode and r.get('status')=='PASS']
  if group:x['summary'][fixture][mode]={'median_engine_seconds':statistics.median(r['seconds_engine_including_io_instrumentation'] for r in group),'median_python_peak_bytes':statistics.median(r['memory']['python_peak_bytes'] for r in group),'max_rss_peak_bytes':max(r['memory']['rss_peak_process_bytes'] for r in group),'max_relative_deviation_by_seed':{str(r['seed']):r['metrics']['population_max_relative'] for r in group},'median_polsby_popper':statistics.median(r['metrics']['polsby_popper_median'] for r in group)}
(p/'e2-results.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps({'decision':x['decision'],'pairs':paired},indent=2))
