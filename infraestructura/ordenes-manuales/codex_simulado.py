#!/usr/bin/env python3
"""DDD simulated Codex 1.2.0; 2026-10-10; tests only, no model consumption.
Predecessor: legacy/1.1.0/codex_simulado.py. Changes: negative scope cases.
Reason: preserve ignored bytes/modes. Does not simulate validators.
"""
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid

prompt=sys.stdin.read()
review='--output-schema' in sys.argv
match=re.search(r'Tarea (\S+):' if review else r'ORDEN EXACTA (\S+):',prompt)
task=match.group(1)
scenario=os.environ.get('DDD_FAKE_SCENARIO','PASS')
event={'role':'reviewer' if review else 'executor','task':task,'argv':sys.argv[1:],'cwd':str(Path.cwd())}
with Path(os.environ['DDD_FAKE_TRACE']).open('a') as trace:
    trace.write(json.dumps(event)+'\n');trace.flush()
print(json.dumps({'type':'thread.started','thread_id':uuid.uuid4().hex}),flush=True)
if not review:
    if scenario=='INTERRUPT':
        while True:time.sleep(.2)
    p=Path('docs/AUDITORIAS')/(task+'-simulation.txt');p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text('Simulated executor delivery; actual historical validators are executed separately.\n')
    if scenario=='OUT_OF_SCOPE_MODE':Path('baseline.txt').chmod(0o755)
    if scenario=='IGNORED_CHANGE':Path('protected-data.bin').write_bytes(b'unauthorized change')
else:
    manifest=Path.cwd().parent/'delivery-manifest.json'
    import hashlib
    m=json.loads(manifest.read_text())
    verdict={'task':task,'delivery_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'head':m['head'],
             'verdict':'NO_GO' if scenario=='NO_GO' and task=='F03' else 'PASS',
             'scope':'LOCAL_TECHNICAL_ONLY','criteria_passed':[json.loads((Path.cwd()/'controller/policy.json').read_text())['simulation_acceptance'][task]],
             'findings':['Simulated independent reviewer finding'] if scenario=='NO_GO' and task=='F03' else [],
             'evidence':['tests.json']}
    if scenario=='INVALID_JSON': verdict['delivery_sha256']='0'*64
    output=Path(sys.argv[sys.argv.index('--output-last-message')+1])
    output.write_text(json.dumps(verdict)+'\n')
if scenario!='BROKEN_EVENTS':
    print(json.dumps({'type':'turn.completed','usage':{'input_tokens':0,'output_tokens':0}}),flush=True)
