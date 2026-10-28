#!/usr/bin/env python3
"""DDD investigación Work, v1.0.0, 2026-10-10; comparación aislada de esquemas.
Origen conceptual: inventario ya acreditado; implementación original, no copia Nacho.
No genera distritos ni modifica fuentes; predecesor: ninguno.
"""
import argparse,hashlib,json,resource,statistics,subprocess,sys,time,tracemalloc
from pathlib import Path
ROOT=Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos')
sys.path.insert(0,str(ROOT))
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def worker(fixture,mode):
 import geopandas as gpd
 import networkx as nx
 from shapely.ops import unary_union
 from gerrychain import Graph
 from ddd_core.m05_gerrychain_strategy import prepare_problem,StrategyContract
 graph=json.loads((fixture/'graph.json').read_text());meta=json.loads((fixture/'m04-report.json').read_text())
 from ddd_core.m05_gerrychain_strategy import _load_geojson_any
 sections=_load_geojson_any(fixture/'m04.zip').to_crs('EPSG:3035');pops={str(n['id']):int(n['pop']) for n in graph['nodes']}
 ids=list(sections.CUSEC_KEY.astype(str));sections['official_population']=[pops[s] for s in ids]
 source=unary_union(list(sections.geometry));target=meta['total_pop']/meta['K']
 tracemalloc.start();started=time.perf_counter()
 if mode=='nacho_scheme':
  t=time.perf_counter();municipal_pops=sections.groupby('CUMUN')['official_population'].sum().to_dict()
  mapping={str(row.CUSEC_KEY):('M:'+str(row.CUMUN) if municipal_pops[row.CUMUN]<target else 'S:'+str(row.CUSEC_KEY)) for row in sections.itertuples()}
  rows=[]
  grouped={}
  for index,s in enumerate(ids):grouped.setdefault(mapping[s],[]).append(index)
  for u,indexes in sorted(grouped.items()):
   block=sections.iloc[indexes];rows.append({'unit_id':u,'population':int(block.official_population.sum()),'municipality':str(block.CUMUN.iloc[0]),'geometry':unary_union(list(block.geometry))})
  units=gpd.GeoDataFrame(rows,geometry='geometry',crs=sections.crs).set_index('unit_id');aggregation=time.perf_counter()-t
  t=time.perf_counter();g=Graph.from_geodataframe(units,adjacency='rook',ignore_errors=False);graph_seconds=time.perf_counter()-t
  geometries=dict(zip(units.index,units.geometry));unitpop=dict(zip(units.index,units.population));edges={tuple(sorted(e)) for e in g.edges};allnodes=set(g.nodes)
  accepted_edges=edges;physical_threshold_description='GerryChain1.0 Graph.from_geodataframe rook; no min_border_m filtering; actual historical0.2.12 not executed'
  setup={'strategy':'small muni P<T->one node; big muni P>=T->section','target':target,'geom_crs':'EPSG:3035','adjacency':'rook','deletion_of_islands':False}
 else:
  t=time.perf_counter();contract=StrategyContract(expected_k=meta['K'],target_tolerance_ratio=meta['tolerance']/target,population_floor_ratio=meta['floor']/target,population_cap_ratio=meta['cap']/target,province_districts=meta['province_counts'])
  problem=prepare_problem(fixture/'graph.json',fixture/'m04.zip',contract,population_field='POP_2023',metric_crs='EPSG:3035',min_shared_border_m=1.0)
  graph_seconds=time.perf_counter()-t;aggregation=None
  mapping=dict(zip(problem.sections.CUSEC_KEY.astype(str),problem.sections.ddd_unit_id.astype(str)))
  geometries=None;unitpop={u:int(v['population']) for u,v in problem.units.items()};edges={tuple(sorted(e)) for e in problem.edges};allnodes=set(problem.units)
  accepted_edges=edges;physical_threshold_description='Existing prepare_problem: quotient M03 plus metric geometry/component cache and baseline validation; operational graph authoritative'
  setup={'strategy':'actual ddd_unit_id from frozenM04','contract':contract.__dict__,'metric_crs':'EPSG:3035','min_shared_border_m':1.0}
 elapsed=time.perf_counter()-started;current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 # Independent integrity checks after timed interval.
 groups={}
 for s,u in mapping.items():groups.setdefault(u,[]).append(s)
 assert set(mapping)==set(pops)==set(ids) and len(mapping)==len(ids)
 assert set(groups)==allnodes
 assert sum(unitpop.values())==sum(pops.values())==meta['total_pop']
 original={str(row.CUSEC_KEY):row for row in sections.itertuples()}
 if geometries is None:
  geometries={u:unary_union([original[s].geometry for s in members]) for u,members in groups.items()}
  assert all(abs(geometries[u].area-problem.unit_areas[u])<1e-6 for u in groups)
  assert all(abs(geometries[u].length-problem.unit_perimeters[u])<1e-6 for u in groups)
 assert all(len({str(original[s].CUMUN) for s in members})==1 for members in groups.values())
 max_population_error=max(abs(unitpop[u]-sum(pops[s] for s in members)) for u,members in groups.items())
 max_geometry_difference=max(geometries[u].symmetric_difference(unary_union([original[s].geometry for s in members])).area for u,members in groups.items())
 merged=unary_union(list(geometries.values()));area_delta=float(source.symmetric_difference(merged).area)
 originalunits={}
 for row in sections.itertuples():originalunits.setdefault(str(row.ddd_unit_id),[]).append(str(row.CUSEC_KEY))
 fractured=[u for u,members in originalunits.items() if len({mapping[s] for s in members})>1]
 closedunits={str(row.ddd_unit_id) for row in sections.itertuples() if row.ddd_closed_urban}
 source_quotient={tuple(sorted((mapping[str(e['u'])],mapping[str(e['v'])]))) for e in graph['edges'] if mapping[str(e['u'])]!=mapping[str(e['v'])]}
 municipality_nodes={}
 for u,members in groups.items():municipality_nodes.setdefault(str(original[members[0]].CUMUN),set()).add(u)
 obj={'mode':mode,'fixture_sha256':{'graph':sha(fixture/'graph.json'),'m04':sha(fixture/'m04.zip'),'report':sha(fixture/'m04-report.json')},'setup':setup,'n_sections':len(ids),'n_nodes':len(allnodes),'reduction_percent':100*(1-len(allnodes)/len(ids)),'n_edges':len(edges),'n_municipalities':len(municipality_nodes),'municipalities_with_multiple_nodes':sum(len(v)>1 for v in municipality_nodes.values()),'population':sum(unitpop.values()),'time':{'total_construction_seconds':elapsed,'aggregation_seconds':aggregation,'graph_or_full_prepare_seconds':graph_seconds,'excludes':'imports,fixture load/reprojection,independent verification'},'memory':{'python_peak_bytes':peak,'python_current_bytes':current,'rss_peak_process_bytes':rss if sys.platform=='darwin' else rss*1024,'rss_scope':'imports+loaded/reprojected fixture+work; no GEOS-only attribution'},'integrity':{'universe_exact':True,'one_municipality_per_node':True,'max_unit_population_error':max_population_error,'max_unit_geometry_symdiff_m2':max_geometry_difference,'total_geometry_symdiff_m2':area_delta,'original_ddd_units_fractured':fractured,'closed_ddd_units_fractured':sorted(set(fractured)&closedunits),'quotient_m03_edges_not_in_constructed':len(source_quotient-edges),'constructed_edges_not_in_m03_quotient':len(edges-source_quotient)},'edge_semantics':physical_threshold_description,'isolated_nodes_preserved':sorted(n for n in allnodes if not any(n in e for e in edges))}
 print(json.dumps(obj,ensure_ascii=False))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--worker',choices=['nacho_scheme','ddd_current']);ap.add_argument('--fixture',type=Path,default=HERE/'fixture-e1');a=ap.parse_args()
 if a.worker:worker(a.fixture,a.worker);return
 results=[]
 for rep in range(3):
  for mode in ['nacho_scheme','ddd_current']:
   cmd=[sys.executable,str(Path(__file__).resolve()),'--worker',mode,'--fixture',str(a.fixture.resolve())]
   run=subprocess.run(cmd,text=True,capture_output=True,timeout=30)
   (HERE/f'e1_{mode}_{rep}.stderr.log').write_text(run.stderr);(HERE/f'e1_{mode}_{rep}.stdout.log').write_text(run.stdout)
   if run.returncode:raise RuntimeError(f'{mode} exit={run.returncode}: {run.stderr[-1200:]}')
   obj=json.loads(run.stdout);obj['repetition']=rep;obj['command']=cmd;results.append(obj)
 dump(HERE/'e1-results.json',{'schema':'ddd.nacho-validation-e1/1.0','results':results,'summary':{m:{'nodes':next(r['n_nodes'] for r in results if r['mode']==m),'median_seconds':statistics.median(r['time']['total_construction_seconds'] for r in results if r['mode']==m),'median_python_peak_bytes':statistics.median(r['memory']['python_peak_bytes'] for r in results if r['mode']==m)} for m in ['nacho_scheme','ddd_current']},'limits':{'repetitions':3,'process_timeout_seconds':30,'memory_observation_threshold_mib':640,'no_rss_hard_limit':'record peak and mark overbudget; platformRLIMIT_AS inappropriate for GIS sharedlibs'},'decision':'SIN_VENTAJA_DEMOSTRADA','note':'Costes no homólogos: DDD incluye diagnóstico/preflight, Nacho sólo grafo geométrico. No equivalencia de edges ni permiso para fracturar units.'})
 print(json.dumps(json.loads((HERE/'e1-results.json').read_text())['summary']))
if __name__=='__main__':main()
