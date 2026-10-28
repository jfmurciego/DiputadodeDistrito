#!/usr/bin/env python3
"""v1.0.0,2026-10-10,Work: caso negativo ReCom sobre C ya existente. Sólo fixture.
Origen: candidato congelado anterior; sin predecesor ni cambios productivos.
"""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path('/Users/macbookpro/Desarrollo/DDD-distritos-autonomicos');sys.path.insert(0,str(ROOT));HERE=Path(__file__).resolve().parent
from ddd_core.m05_gerrychain_strategy import prepare_problem,contract_from_yaml,BaselineValidationError
folder=HERE/'fixture-e2'/'C_negative';folder.mkdir(exist_ok=True)
base=HERE/'fixture-e2'/'A_lower_L1';geo=json.loads((base/'initial.geojson').read_text())
for index in [4,5]:geo['features'][index]['properties']['district_id']=0
source=json.loads((ROOT/'docs/AUDITORIAS/NACHO_2026-10-10/experimentos/results.json').read_text())
legacy=hashlib.sha256(json.dumps([f['properties']['district_id'] for f in geo['features']],sort_keys=True).encode()).hexdigest()
assert legacy==source['ranking']['candidates']['C_hard_invalid']['assignment_sha256']
(folder/'initial.geojson').write_text(json.dumps(geo,indent=2)+'\n');(folder/'graph.json').write_bytes((base/'graph.json').read_bytes())
contract=json.loads((base/'frozen.json').read_text())['contract'];(folder/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
started=time.perf_counter()
try:
 prepare_problem(folder/'graph.json',folder/'initial.geojson',contract_from_yaml({'validation':contract}))
 raise AssertionError('Invalid existing baseline unexpectedly accepted')
except BaselineValidationError as e:
 result={'status':'EXPECTED_BASELINE_REJECTION','error':str(e),'seconds':time.perf_counter()-started,'fixture_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()},'legacy_assignment_hash':legacy,'recom_chain_executed':False,'scope':'Prerequisite hard0 in actual strategy; not a test of A2 repair ability'}
(HERE/'e2-negative-baseline.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
