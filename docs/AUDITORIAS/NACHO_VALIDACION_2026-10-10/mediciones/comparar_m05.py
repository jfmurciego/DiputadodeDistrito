#!/usr/bin/env python3
"""DDD Work, v1.0.0, 2026-10-10: comparación canónico/ReCom sobre candidatos sintéticos congelados.
Origen: resultados E1 previos, matriz y asignaciones existentes. Ningún código productivo editado.
Predecesor: ninguno. Sólo fixtures/temp y motores existentes, no ejecución territorial.
"""
import argparse,hashlib,importlib.util,json,os,resource,signal,statistics,subprocess,sys,time,tracemalloc,zipfile
from collections import defaultdict
from pathlib import Path
ROOT=Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos');sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
SOURCE=ROOT/'docs/AUDITORIAS/NACHO_2026-10-10/experimentos/results.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def assignment_hash(x):return digest({str(s):int(d) for s,d in sorted(x.items())})
def without_labels(x):return digest(sorted(sorted(s for s,d in x.items() if d==district) for district in set(x.values())))

def freeze():
 source=json.loads(SOURCE.read_text());pops=[p for row in source['ranking']['cell_population_matrix'] for p in row]
 from shapely.geometry import box,mapping
 for name,axis in [('A_lower_L1','rows'),('B_lower_max','columns')]:
  folder=HERE/'fixture-e2'/name;folder.mkdir(parents=True,exist_ok=True)
  sections=[];nodes=[];edges=[];assign={str(i):i//4 if axis=='rows' else i%4 for i in range(16)}
  # Verify exact old labeled assignment hash (old engine convention).
  old_list_hash=hashlib.sha256(json.dumps([assign[str(i)] for i in range(16)],sort_keys=True).encode()).hexdigest()
  assert old_list_hash==source['ranking']['candidates'][name]['assignment_sha256']
  for i,pop in enumerate(pops):
   x,y=i%4,i//4
   props={'CUSEC_KEY':str(i),'POP_2025':pop,'CPRO':'01','CUMUN':str(i),'ddd_unit_id':str(i),'ddd_closed_urban':False,'district_id':assign[str(i)],'COMARCA_COD':str(i),'COMARCA_NOM':str(i)}
   sections.append({'type':'Feature','properties':props,'geometry':mapping(box(4320000+1000*x,3210000+1000*y,4321000+1000*x,3211000+1000*y))});nodes.append({'id':str(i),'pop':pop,'CPRO':'01','CUMUN':str(i),'COMARCA_COD':str(i)})
   for j in ([i+1] if x<3 else [])+([i+4] if y<3 else []):edges.append({'u':str(i),'v':str(j),'edge_type':'geometric','source':'SYNTHETIC_ORTHOGONAL_GRID'})
  dump(folder/'initial.geojson',{'type':'FeatureCollection','crs':{'type':'name','properties':{'name':'urn:ogc:def:crs:EPSG::3035'}},'features':sections})
  dump(folder/'graph.json',{'nodes':nodes,'edges':edges})
  contract={'expected_districts':4,'target_tolerance_ratio':.12,'population_floor_ratio':.8,'population_cap_ratio':1.75,'province_districts':{'01':4},'require_graph_contiguity':True}
  config={'fixture':name,'source_file_sha256':sha(SOURCE),'prior_assignment_hash':old_list_hash,'K':4,'P':4000,'crs':'EPSG:3035','contract':contract,'seeds':[17,29,43],'budget':{'engine_wall_seconds':10,'parent_process_timeout_seconds':20,'rss_post_run_limit_mib':640,'canonical_greedy_moves_limit':100,'canonical_anneal_iters':1000,'recom_states':1001,'recom_max_bipartition_attempts':50},'scope':'Synthetic16, no closed urban or multipart examples; cannot generalize to A2'}
  dump(folder/'frozen.json',config)
 return [HERE/'fixture-e2'/n for n in ['A_lower_L1','B_lower_max']]

def connected(group,adj):
 if not group:return False
 seen={next(iter(group))};stack=list(seen)
 while stack:
  for n in adj[stack.pop()]&group-seen:seen.add(n);stack.append(n)
 return seen==group

def check_metrics(fixture,path,problem,contract):
 from shapely.geometry import shape
 from shapely.ops import unary_union
 from ddd_core.m05_gerrychain_strategy import _load_geojson_any,hard_constraint_violations
 original=json.loads((fixture/'initial.geojson').read_text());source={str(f['properties']['CUSEC_KEY']):f for f in original['features']};df=_load_geojson_any(path)
 assign={str(r.CUSEC_KEY):int(r.district_id) for r in df.itertuples()}
 graph=json.loads((fixture/'graph.json').read_text());pop={str(n['id']):int(n['pop']) for n in graph['nodes']};adj={s:set() for s in pop}
 for e in graph['edges']:adj[e['u']].add(e['v']);adj[e['v']].add(e['u'])
 assert len(df)==16 and set(assign)==set(source)==set(pop)
 assert all(shape(source[str(r.CUSEC_KEY)]['geometry']).equals_exact(r.geometry,0) for r in df.itertuples())
 groups={d:{s for s,v in assign.items() if v==d} for d in set(assign.values())};sums={d:sum(pop[s] for s in g) for d,g in groups.items()}
 geoms={d:unary_union([shape(source[s]['geometry']) for s in g]) for d,g in groups.items()};pps=[4*__import__('math').pi*g.area/g.length**2 for g in geoms.values()]
 violations=hard_constraint_violations(problem,assign,contract);independent=[]
 if len(groups)!=4:independent.append('K')
 if sum(sums.values())!=4000:independent.append('P')
 for d,g in groups.items():
  if not 800<=sums[d]<=1750:independent.append('bounds:'+str(d))
  if not connected(g,adj):independent.append('topology:'+str(d))
  if geoms[d].geom_type!='Polygon':independent.append('geometry:'+str(d))
  if {source[s]['properties']['CPRO'] for s in g}!={'01'}:independent.append('province:'+str(d))
 if len(df.ddd_unit_id.astype(str).unique())!=16:independent.append('units')
 rel=[abs(p-1000)/1000 for p in sums.values()]
 return {'assignment':assign,'assignment_hash':assignment_hash(assign),'unlabeled_partition_hash':without_labels(assign),'hard_violations':violations,'independent_fixture_violations':independent,'K':len(groups),'population':sum(sums.values()),'district_populations':sums,'population_max_relative':max(rel),'population_l1':sum(abs(p-1000) for p in sums.values()),'population_rms_relative':(sum(r*r for r in rel)/4)**.5,'outside_target_tolerance':sum(r>.12+1e-12 for r in rel),'graph_connected_districts':sum(connected(g,adj) for g in groups.values()),'physical_connected_districts':sum(g.geom_type=='Polygon' for g in geoms.values()),'municipalities_split':0,'municipality_count':16,'atomic_units':16,'closed_urban_districts':0,'geometry_preserved_exact':True,'polsby_popper_min':min(pps),'polsby_popper_median':statistics.median(pps),'comarca_retention':1.0,'fine_tolerance_role':'objective, not hard; floor800/cap1750 hard for both'}

def worker(fixture,mode,seed):
 import geopandas,yaml
 import ddd_core.m05_gerrychain_strategy as strategy
 spec=json.loads((fixture/'frozen.json').read_text());contract=strategy.contract_from_yaml({'validation':spec['contract']});problem=strategy.prepare_problem(fixture/'graph.json',fixture/'initial.geojson',contract)
 run=HERE/'e2-runs'/fixture.name/mode/str(seed);run.mkdir(parents=True,exist_ok=True);output=run/'selected.zip';report=run/'engine-report.json'
 traces={'greedy':[],'anneal':[],'recom':[],'initial':[]};instrumentation={}
 if mode=='canonical':
  path=ROOT/'modulos/05_optimizar_distritos.py';module_spec=importlib.util.spec_from_file_location('canonical_real_wrapper',path);engine=importlib.util.module_from_spec(module_spec);sys.modules[module_spec.name]=engine;module_spec.loader.exec_module(engine)
  cfg={'meta':{'territory_id':'SYNTHETIC','run_name':fixture.name},'validation':spec['contract'],'modulos':{'modulo_05_optimizar_distritos':{'in_graph_json':str(fixture/'graph.json'),'in_geojson':str(fixture/'initial.geojson'),'out_geojson':str(output),'out_report':str(report),'id_field':'CUSEC_KEY','pop_field':'POP_2025','district_field':'district_id','province_field':'CPRO','greedy_moves_limit':100,'anneal_iters':1000,'seed':seed,'anneal_seed_offset':0,'swap_polish_max':0}}}
  params=run/'params.yaml';params.write_text(yaml.safe_dump(cfg,sort_keys=False));base=ROOT/'ddd_core/m05_opt_engine_v741.py';lines=base.read_text().splitlines()
  watched={label:next(i for i,l in enumerate(lines,1) if l.strip()==text) for label,text in [('greedy','greedy_accepted += 1'),('anneal','anneal_iterations_executed = i + 1'),('last','unit_dist = best_unit_dist')]};instrumentation={'type':'read-only sys.settrace existing main, no code patch','source':str(base),'watched_lines':watched,'timing_includes_trace':True}
  def snapshot(frame):return {str(k):int(v) for k,v in frame.f_locals['unit_dist'].items()}
  def localtrace(frame,event,arg):
   if event=='line' and 'unit_dist' in frame.f_locals:
    if not traces['initial']:traces['initial'].append(snapshot(frame))
    if frame.f_lineno==watched['greedy']:traces['greedy'].append(snapshot(frame))
    if frame.f_lineno==watched['anneal']:traces['anneal'].append(snapshot(frame))
    if frame.f_lineno==watched['last']:traces['anneal'].append(snapshot(frame))
   return localtrace
  def globaltrace(frame,event,arg):
   if frame.f_code.co_filename==str(base) and frame.f_code.co_name=='main':return localtrace
   return None
  def call():
   old=sys.argv;sys.argv=[str(path),'--params',str(params)];sys.settrace(globaltrace)
   try:engine.main()
   finally:sys.settrace(None);sys.argv=old
 else:
  cfg=strategy.StrategyConfig(steps_per_seed=1001,seed_base=seed-1,seed_count=1,proposal_epsilon=.12,population_band=.005,metric_crs='EPSG:3035',min_shared_border_m=1,max_bipartition_attempts=50,comarca_surcharge=0,require_pythonhashseed_zero=True)
  dump(run/'params.json',{'contract':contract.__dict__,'strategy':cfg.__dict__});original_rank=strategy.candidate_rank
  def recording_rank(p,a,c,b,*args,**kwargs):
   if sys._getframe(1).f_code.co_name=='_run_seed':traces['recom'].append(dict(a))
   return original_rank(p,a,c,b,*args,**kwargs)
  strategy.candidate_rank=recording_rank;instrumentation={'type':'observe existing candidate_rank calls in _run_seed, no modified rank','timing_includes_observer':True}
  def call():return strategy.run_from_paths(graph_path=fixture/'graph.json',initial_path=fixture/'initial.geojson',output_path=output,report_path=report,contract=contract,strategy=cfg)
 def timeout(signum,frame):raise TimeoutError('engine wall budget10s exceeded')
 prev_handler=signal.getsignal(signal.SIGALRM);signal.signal(signal.SIGALRM,timeout);signal.alarm(10);tracemalloc.start();started=time.perf_counter();status='PASS';error=None
 try:call()
 except Exception as e:status='FAIL';error=f'{type(e).__name__}: {e}'
 finally:elapsed=time.perf_counter()-started;signal.alarm(0);signal.signal(signal.SIGALRM,prev_handler);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;rss_bytes=rss if sys.platform=='darwin' else rss*1024
 if rss_bytes>640*1024**2:status='OVER_MEMORY_BUDGET'
 result={'schema':'ddd.nacho-validation-e2-run/1.0','fixture':fixture.name,'fixture_sha256':{p.name:sha(p) for p in [fixture/'graph.json',fixture/'initial.geojson',fixture/'frozen.json']},'mode':mode,'seed':seed,'status':status,'error':error,'seconds_engine_including_io_instrumentation':elapsed,'memory':{'python_peak_bytes':peak,'rss_peak_process_bytes':rss_bytes,'rss_includes':'imports and common preparedbaseline, native libs'},'instrumentation':instrumentation,'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'modulos/05_optimizar_distritos.py',ROOT/'ddd_core/m05_opt_engine_v741.py',ROOT/'ddd_core/m05_population_repair.py',ROOT/'ddd_core/m05_gerrychain_strategy.py']}}
 if status=='PASS':
  data=json.loads(report.read_text());result['metrics']=check_metrics(fixture,output,problem,contract)
  if mode=='canonical':
   transitions=traces['anneal'];states=traces['initial']+traces['greedy']+transitions;result['search']={'greedy_accepted':data['accepted_greedy_moves'],'anneal_accepted':data['accepted_annealing_moves'],'anneal_attempts':data['anneal_iterations_executed'],'unique_labeled_states':len({assignment_hash(a) for a in states}),'unique_unlabeled_partitions':len({without_labels(a) for a in states}),'anneal_hold_transitions':sum(a==b for a,b in zip(transitions,transitions[1:])),'anneal_transition_count':max(0,len(transitions)-1),'population_repair':data.get('population_repair'),'note':'SA holds are not a MarkovChain quality gate; greedy selection not counted as failed proposals'}
   assert len(traces['greedy'])==data['accepted_greedy_moves'];assert max(0,len(transitions)-1)==data['anneal_iterations_executed']
  else:
   traces['recom']=traces['recom'][1:];states=traces['recom'];search=dict(data['search']['runs'][0]);result['search']=search
   result['search']['observed_unique_unlabeled_partitions']=len({without_labels(a) for a in states});result['search']['observed_unique_labeled_states']=len({assignment_hash(a) for a in states});result['search']['observed_states_from_harness']=len(states)
   assert len(states)==search['states_observed']
   assert len({assignment_hash(a) for a in states})==search['unique_states']
  # Every observed admissible state is independently checked for bounds + graph in common gate.
  state_violations=[strategy.hard_constraint_violations(problem,a,contract) for a in states]
  result['observed_states_with_hard_violations']=sum(bool(v) for v in state_violations)
  assert not any(state_violations),state_violations[:2]
  assert not result['metrics']['hard_violations'] and not result['metrics']['independent_fixture_violations']
  dump(run/'observed-states.json',traces)
 dump(run/'result.json',result);print('MEASURED_RESULT '+json.dumps(result,ensure_ascii=False))
 if status!='PASS':raise SystemExit(2)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--worker',choices=['canonical','recom']);ap.add_argument('--fixture',type=Path);ap.add_argument('--seed',type=int);a=ap.parse_args()
 if a.worker:worker(a.fixture.resolve(),a.worker,a.seed);return
 fixtures=freeze();results=[]
 for fixture in fixtures:
  for seed in [17,29,43]:
   for mode in ['canonical','recom']:
    command=[sys.executable,str(Path(__file__).resolve()),'--worker',mode,'--fixture',str(fixture),'--seed',str(seed)];started=time.perf_counter()
    try:r=subprocess.run(command,text=True,capture_output=True,timeout=20);status=r.returncode;stdout=r.stdout;stderr=r.stderr
    except subprocess.TimeoutExpired as e:status='PARENT_TIMEOUT';stdout=e.stdout or '';stderr=e.stderr or ''
    folder=HERE/'e2-runs'/fixture.name/mode/str(seed);folder.mkdir(parents=True,exist_ok=True)
    if isinstance(stdout,bytes):stdout=stdout.decode(errors='replace')
    if isinstance(stderr,bytes):stderr=stderr.decode(errors='replace')
    (folder/'stdout.log').write_text(stdout);(folder/'stderr.log').write_text(stderr);dump(folder/'command.json',{'command':command,'env':{'PYTHONHASHSEED':os.environ.get('PYTHONHASHSEED'),'PYTHONDONTWRITEBYTECODE':os.environ.get('PYTHONDONTWRITEBYTECODE')},'exit':status,'wall_seconds_process':time.perf_counter()-started})
    obj=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {'mode':mode,'seed':seed,'fixture':fixture.name,'status':status};results.append(obj)
    print(f'{fixture.name} {mode} seed{seed} exit{status}',flush=True)
 dump(HERE/'e2-results.json',{'schema':'ddd.nacho-validation-e2/1.0','runs':results,'runtime':'existing /private/tmp/madrid-gerrychain-venv; no installation','budget_comparability':'Same10s engine wall/20s process/640MiB measuredpeak,1000SAattempts vs1000chaintransitions plus up to100greedy moves. Not equivalent work and neither forced to exhaust wall budget.','fixture_scope':'two16section synthetic initial assignments already frozen, no territorial generalization','decision':'PENDING_RESULTS_REVIEW'})
if __name__=='__main__':main()
