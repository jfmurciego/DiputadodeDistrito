"""Micropruebas aisladas de contratos DDD, 1.0.0, 2026-10-10.
Origen: investigación Work/Nacho; implementación independiente, sin predecesor.
No ejecuta MarkovChain ni producción. Escribe sólo el expediente autorizado.
"""
import copy
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from time import perf_counter

ROOT=Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos')
sys.path.insert(0,str(ROOT))
from ddd_core.m05_gerrychain_engine import Contract, adapt_inputs, assignment_hash, hard_constraint_violations, geometric_shape_metrics
from ddd_ensemble.runner import ensure_plan, _valid_existing

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(tempfile.mkdtemp(prefix='ddd-nacho-microchecks-'))
OUT.mkdir(parents=True, exist_ok=True)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,obj):path.write_text(json.dumps(obj,sort_keys=True)+'\n')
started=perf_counter()
graph={'nodes':[{'id':str(i),'pop':10} for i in range(4)],'edges':[{'u':str(i),'v':str(i+1)} for i in range(3)]}
geo={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'CUSEC_KEY':str(i),'district_id':i//2,'CPRO':'01','CUMUN':'M' if i<3 else 'N','ddd_unit_id':str(i)},'geometry':None} for i in range(4)]}
data=adapt_inputs(graph,geo)
contract=Contract(k=2,target_tolerance_ratio=.2,municipality_atomicity_limit_ratio=1.75)
viol=hard_constraint_violations(data,data.initial_assignment,contract)
assert viol==[],viol
atomicity={'municipality_population':30,'target':20,'atomicity_limit':35,'observed_municipality_districts':2,'ddd_validator_violations':viol,'conclusion':'VALIDATOR_ACCEPTS_SPLIT_BELOW_DECLARED_ATOMICITY_LIMIT','scope':'adaptador de laboratorio; no demuestra producto certificado inválido'}

# Misma partición física con permutación de etiquetas.
geo2=copy.deepcopy(geo)
for i,f in enumerate(geo2['features']):f['properties']['CUMUN']=str(i)
data2=adapt_inputs(graph,geo2)
a=data2.initial_assignment;b={s:1-d for s,d in a.items()}
canonical=lambda x:sorted(sorted(s for s,d in x.items() if d==label) for label in set(x.values()))
assert canonical(a)==canonical(b)
assert assignment_hash(a)!=assignment_hash(b)
assert not hard_constraint_violations(data2,a,contract)
assert not hard_constraint_violations(data2,b,contract)
label={'assignment_hashes':[assignment_hash(a),assignment_hash(b)],'labeled_unique_count':2,'unlabeled_partition_count':1,'same_unlabeled_members':canonical(a)==canonical(b),'scope':'diagnóstico de diversidad; conservar IDs oficiales'}

# Reanudar evidencias del mismo candidato después de cambiar presupuesto/contrato.
# Artefacto mock autoconsistente: ejercita solo identidad de caché, no certifica geometría.
config={'territory_id':'synthetic','prepared_bundle_id':'same-inputs','ensemble':{'candidate_count':5,'seed':42},'engine':{'steps':56},'contract':{'k':2,'target_tolerance_ratio':.2}}
with tempfile.TemporaryDirectory(prefix='ddd-nacho-resume-') as td:
 base=Path(td);p=ensure_plan(config,base);cid=p['candidates'][0]['candidate_id'];d=base/'results'/cid;d.mkdir(parents=True)
 write(d/'candidate.geojson',{'type':'FeatureCollection','features':[]})
 (d/'statistical-states.jsonl').write_text('{}\n')
 report={'candidate_id':cid,'assignment_hash':'test-hash','geojson':'candidate.geojson','hard_constraints':{'all_pass':True},'engine_run':{'chain_quality':{'all_pass':True},'run':{'steps_requested':56}}}
 write(d/'report.json',report)
 write(d/'candidate-manifest.json',{'candidate_id':cid,'assignment_hash':'test-hash','plan_sha256':p['plan_sha256'],'geojson_sha256':digest(d/'candidate.geojson'),'report_sha256':digest(d/'report.json')})
 before=bool(_valid_existing(d/'report.json',cid))
 changed=copy.deepcopy(config);changed['engine']['steps']=1000;changed['contract']['target_tolerance_ratio']=.01
 after_plan=ensure_plan(changed,base);after=bool(_valid_existing(d/'report.json',cid))
 assert before and after and p['plan_sha256']==after_plan['plan_sha256']
 resume={'old_steps':56,'new_steps':1000,'old_tolerance':.2,'new_tolerance':.01,'same_plan_hash':p['plan_sha256']==after_plan['plan_sha256'],'cache_accepted_before':before,'cache_accepted_after':after,'mock_artifact':True,'conclusion':'CACHE_IDENTITY_DOES_NOT_BIND_FULL_EXECUTION_CONFIGURATION','scope':'funciones reales ensure_plan/_valid_existing; mock autoconsistente, sin cadena'}

# Fórmula de perímetro requiere todas las fronteras internas compartidas.
# Tres rectángulos en L: M03 contiene dos aristas válidas de un triángulo.
from shapely.geometry import box, mapping
g={'nodes':[{'id':str(i),'pop':10} for i in range(3)],'edges':[{'u':'0','v':'1'},{'u':'1','v':'2'}]}
shapes=[box(0,0,1,2),box(1,0,2,1),box(1,1,2,2)]
j={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'CUSEC_KEY':str(i),'district_id':0,'CPRO':'01','CUMUN':str(i),'ddd_unit_id':str(i)},'geometry':mapping(shape)} for i,shape in enumerate(shapes)]}
x=adapt_inputs(g,j,min_shared_border_m=.1)
cached=geometric_shape_metrics(x,x.initial_assignment)['polsby_popper_median']
from shapely.ops import unary_union
import math
union=unary_union(shapes);exact=4*math.pi*union.area/union.length**2
assert not math.isclose(cached,exact)
complete=copy.deepcopy(g);complete['edges'].append({'u':'0','v':'2'})
y=adapt_inputs(complete,j,min_shared_border_m=.1)
complete_pp=geometric_shape_metrics(y,y.initial_assignment)['polsby_popper_median']
assert math.isclose(complete_pp,exact)
shape={'operational_edges':2,'geometric_contact_edges':3,'cached_pp_incomplete_graph':cached,'dissolved_pp':exact,'cached_pp_complete_graph':complete_pp,'all_input_geometry_valid':True,'conclusion':'CACHED_PERIMETER_REQUIRES_COMPLETE_INTERNAL_CONTACTS','scope':'condicional: no prueba que M03 productivo tenga una arista omitida'}
result={'schema':'ddd.nacho-microchecks/1.0','python':sys.version,'seconds':perf_counter()-started,'source_sha256':{p:digest(ROOT/p) for p in ['ddd_core/m05_gerrychain_engine.py','ddd_ensemble/runner.py','ddd_ensemble/ensemble_plan.py']},'atomicity':atomicity,'label_diversity':label,'resume_identity':resume,'shape_contact_completeness':shape,'assertions_pass':True,'production_changes':False}
write(OUT/'microchecks.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
