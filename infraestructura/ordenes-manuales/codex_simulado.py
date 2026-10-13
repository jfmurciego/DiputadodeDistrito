#!/usr/bin/env python3
"""DDD simulated Codex 1.3.2; 2026-10-13; tests only, no model consumption.
Predecessor: legacy/1.3.1/codex_simulado.py. Changes: lossless nested criterion normalization.
Reason: preserve every criterion in structured READ_ONLY review output. Does not simulate validators.
"""
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid


def string_list(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        flattened = []
        for item in value:
            flattened.extend(string_list(item))
        return flattened
    raise SystemExit('SIMULATION_INPUT_ERROR: expected string or nested list of strings')


prompt=sys.stdin.read()
structured='--output-schema' in sys.argv
review=structured and 'executor' not in Path(sys.argv[sys.argv.index('--output-schema')+1]).name
if structured:
    manifest=Path.cwd().parent/('delivery-manifest.json' if review else 'input-manifest.json')
    task=json.loads(manifest.read_text())['task']
else:
    match=re.search(r'ORDEN EXACTA (\S+):',prompt)
    if match is None:
        raise SystemExit('SIMULATION_INPUT_ERROR: no task identity in legacy prompt')
    task=match.group(1)
scenario=os.environ.get('DDD_FAKE_SCENARIO','PASS')
event={'role':'reviewer' if review else 'executor','task':task,'argv':sys.argv[1:],'cwd':str(Path.cwd())}
with Path(os.environ['DDD_FAKE_TRACE']).open('a') as trace:
    trace.write(json.dumps(event)+'\n');trace.flush()
print(json.dumps({'type':'thread.started','thread_id':uuid.uuid4().hex}),flush=True)
if not review:
    if scenario=='INTERRUPT':
        while True:time.sleep(.2)
    if scenario=='QUOTA':
        print(json.dumps({'type':'error','message':'usage limit quota exceeded (SIMULATION)'}),flush=True)
        sys.exit(1)
    if structured:
        parent=Path.cwd().parent
        manifest=parent/'input-manifest.json'
        import hashlib
        m=json.loads(manifest.read_text())
        criteria=json.loads(os.environ['DDD_FAKE_CRITERIA'])
        if isinstance(criteria,dict):criteria=criteria[task]
        criteria=string_list(criteria)
        limitations=json.loads(os.environ.get('DDD_FAKE_LIMITATIONS','{}'))
        if isinstance(limitations,dict):limitations=limitations.get(task,[])
        limitations=string_list(limitations)+['SIMULATION_ONLY']
        summary={'task':task,'head':m['head'],'inputs_manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
                 'status':'READY_FOR_REVIEW','criteria_verified':criteria,'evidence':list(m['files']),
                 'tests':['SIMULATED executor; deterministic validator follows'],'limitations':limitations}
        Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(summary)+'\n')
    else:
        p=Path('docs/AUDITORIAS')/(task+'-simulation.txt');p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('Simulated executor delivery; actual historical validators are executed separately.\n')
    if scenario=='OUT_OF_SCOPE_MODE':Path('baseline.txt').chmod(0o755)
    if scenario=='IGNORED_CHANGE':Path('protected-data.bin').write_bytes(b'unauthorized change')
else:
    manifest=Path.cwd().parent/'delivery-manifest.json'
    import hashlib
    m=json.loads(manifest.read_text())
    passed=json.loads((Path.cwd()/'controller/policy.json').read_text())['simulation_acceptance'][task]
    passed=string_list(passed)
    verdict={'task':task,'delivery_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'head':m['head'],
             'verdict':'NO_GO' if (scenario=='NO_GO' or (scenario=='REPAIR_ONCE' and 'repair-' not in str(Path.cwd()))) and task=='F03' else 'PASS',
             'scope':'LOCAL_TECHNICAL_ONLY','criteria_passed':passed,
             'findings':['Simulated independent reviewer finding'] if (scenario=='NO_GO' or (scenario=='REPAIR_ONCE' and 'repair-' not in str(Path.cwd()))) and task=='F03' else [],
             'evidence':['tests.json']}
    if scenario=='INVALID_JSON': verdict['delivery_sha256']='0'*64
    output=Path(sys.argv[sys.argv.index('--output-last-message')+1])
    output.write_text(json.dumps(verdict)+'\n')
if scenario!='BROKEN_EVENTS':
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':0,'output_tokens':0}}),flush=True)
