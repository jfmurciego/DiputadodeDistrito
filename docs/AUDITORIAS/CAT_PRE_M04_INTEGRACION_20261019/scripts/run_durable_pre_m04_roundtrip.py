#!/usr/bin/env python3
"""Isolated durable persistence roundtrip against authentic CAT M03/M03U artifacts.

Uses a temporary git checkout and local bare origin. It does not contact GitHub,
write to the source repository, execute M04, or generate a territorial product.
"""
from __future__ import annotations
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from herramientas.persistir_evidencia_pre_m04_operacional import persist_pre_m04_evidence

ROOT=Path.cwd().resolve()
EV=Path(__file__).resolve().parents[1]
EX=Path(os.environ.get('DDD_CAT_PRE_M04_EVIDENCE_ROOT', EV/'github_actions/extracted')).resolve()
OUT=EV/'results'
PYTHON=sys.executable
RUN=37453376100
ART_M03='1a60164eeba923794a69873ed7fc9238e04e9816e2ca1b1f4ea0b2feedc617f4'
ART_M03U='27a4353d55c3464856ae2ed98e3064bc9a63c38284e6f13e7b83f18f425feaee'
ART_JOB='cbc9943db4bd256d57a2923c3f457aadbf12cd8d454f42dcc0b660d9543933e3'
TARGET='pre-m04-local-test'

def run(args, cwd=None, env=None, check=True):
    p=subprocess.run(args,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and p.returncode:
        raise RuntimeError(f"command failed {args}: rc={p.returncode}\nstdout={p.stdout}\nstderr={p.stderr}")
    return p

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(cwd,*args): return run(['git',*args],cwd=cwd).stdout.strip()

with tempfile.TemporaryDirectory(prefix='ddd-cat-pre-m04-durable-') as td:
    tmp=Path(td); repo=tmp/'work'; bare=tmp/'origin.git'
    run(['git','clone','--shared','--no-checkout',str(ROOT),str(repo)])
    source_head=run(['git','rev-parse','HEAD'],cwd=ROOT).stdout.strip()
    run(['git','checkout','--detach',source_head],cwd=repo)
    for rel in ('herramientas/_resolver_ejecucion_completa_core.py','herramientas/materializar_evidencia_pre_m04.py'):
        shutil.copy2(ROOT/rel,repo/rel)
    run(['git','add','herramientas/_resolver_ejecucion_completa_core.py','herramientas/materializar_evidencia_pre_m04.py'],cwd=repo)
    run(['git','-c','user.name=DDD isolated test','-c','user.email=ddd-isolated@example.invalid','commit','-m','test: CAT pre-M04 durable roundtrip code snapshot'],cwd=repo)
    code_head=git(repo,'rev-parse','HEAD')
    code_tree=git(repo,'rev-parse','HEAD^{tree}')
    code_snapshot_paths=run(['git','diff-tree','--no-commit-id','--name-only','-r',code_head],cwd=repo).stdout.splitlines()
    assert sorted(code_snapshot_paths)==sorted(['herramientas/_resolver_ejecucion_completa_core.py','herramientas/materializar_evidencia_pre_m04.py'])
    # Seed the isolated bare origin from the same checkout so it has the exact
    # shallow/shared object boundary; an empty bare rejects this checkout's
    # missing historical parent objects before the persistence behavior runs.
    run(['git','clone','--bare','--shared',str(ROOT),str(bare)])
    run(['git','remote','set-url','origin',str(bare)],cwd=repo)
    run(['git','push','origin',f'HEAD:refs/heads/{TARGET}'],cwd=repo)
    original_remote=run(['git','--git-dir',str(bare),'rev-parse',f'refs/heads/{TARGET}']).stdout.strip()
    assert original_remote==code_head

    env=os.environ.copy(); env['PYTHONPATH']=str(repo)+os.pathsep+str(ROOT/'tests');
    cand=tmp/'candidate.json'; handoff=tmp/'handoff.json'; hmeta=tmp/'handoff.meta.json'
    result1=OUT/'durable-persist-result-1.json'; result2=OUT/'durable-persist-result-2.json'
    common=['--root-dir',str(repo),'--territory-id','cataluna','--edition','2025','--run-id',str(RUN),'--contract-path','territorios/cataluna/config/cataluna_2025.yaml']
    run([PYTHON,'-m','herramientas.materializar_evidencia_pre_m04',*common,
         '--m03-state-dir',str(EX/'artifact-11409125228'),
         '--partition-job',str(EX/'artifact-11409600198/job.json'),
         '--m03-artifact-sha256',ART_M03,'--m03u-artifact-sha256',ART_M03U,
         '--partition-artifact-sha256',ART_JOB,'--output',str(cand)],cwd=repo,env=env)
    candidate=json.loads(cand.read_text())
    assert candidate['source_commit']==code_head
    assert candidate['effective_gate']=={'allowed':True,'route':'validated_pre_m04_topology'}
    run([PYTHON,'-m','herramientas.handoff_evidencia_pre_m04','stage',
         '--persisted-evidence',str(cand),'--handoff',str(handoff),'--metadata',str(hmeta),
         '--territory-id','cataluna','--edition','2025','--run-id',str(RUN),'--source-commit',code_head],cwd=repo,env=env)

    persist=['-m','herramientas.persistir_evidencia_pre_m04_operacional',*common,
             '--candidate-evidence',str(cand),'--source-commit',code_head,
             '--target-branch',TARGET,'--max-attempts','4','--result-json']
    first=run([PYTHON,*persist,str(result1),'--handoff',str(handoff),'--handoff-metadata',str(hmeta)],cwd=repo,env=env)
    after_first=run(['git','--git-dir',str(bare),'rev-parse',f'refs/heads/{TARGET}']).stdout.strip()
    stored_repo=tmp/'verify'; run(['git','clone','--shared','--branch',TARGET,str(bare),str(stored_repo)])
    stored=stored_repo/'territorios/cataluna/evidencia/catalogo/generation_preflight_2025.json'
    stored_bytes=stored.read_bytes(); candidate_bytes=cand.read_bytes()
    stored_data=json.loads(stored_bytes)
    assert stored_bytes==candidate_bytes
    assert stored_data['source_commit']==code_head and stored_data['run_id']==RUN
    assert stored_data['effective_gate']['allowed'] is True
    assert stored_data['graph']['topology_accreditation']==candidate['graph']['topology_accreditation']
    run([PYTHON,'-m','herramientas.handoff_evidencia_pre_m04','verify',
         '--persisted-evidence',str(stored),'--handoff',str(handoff),'--metadata',str(hmeta),
         '--territory-id','cataluna','--edition','2025','--run-id',str(RUN),'--source-commit',code_head],cwd=repo,env=env)

    # A clean retry starts from the same source commit. The writer fetches the
    # already registered target and must observe an exact NO_OP, with no new commit.
    run(['git','reset','--hard',code_head],cwd=repo)
    second=run([PYTHON,*persist,str(result2),'--handoff',str(handoff),'--handoff-metadata',str(hmeta)],cwd=repo,env=env)
    after_second=run(['git','--git-dir',str(bare),'rev-parse',f'refs/heads/{TARGET}']).stdout.strip()
    result1_data=json.loads(result1.read_text()); result2_data=json.loads(result2.read_text())
    assert result1_data['status']=='REGISTERED'
    assert result2_data['status']=='NO_OP'
    assert after_first==after_second

    # Simulate interruption after the local commit, before a remote push. The
    # fake remote must stay unchanged; a fresh retry from the source commit must
    # discard that local partial commit and rederive/persist the candidate.
    run(['git','reset','--hard',code_head],cwd=repo)
    run(['git','push','origin',f'{code_head}:refs/heads/interrupt-target'],cwd=repo)
    interrupt_result=OUT/'durable-interruption-result.json'
    try:
        persist_pre_m04_evidence(root_dir=repo,territory_id='cataluna',edition='2025',run_id=RUN,
            contract_path='territorios/cataluna/config/cataluna_2025.yaml',candidate_evidence=cand,
            source_commit=code_head,target_branch='interrupt-target',max_attempts=1,result_json=interrupt_result,
            handoff=handoff,handoff_metadata=hmeta,
            before_push=lambda attempt: (_ for _ in ()).throw(RuntimeError('simulated interruption before push')))
        raise AssertionError('injected interruption did not fire')
    except RuntimeError as exc:
        interruption_error=str(exc)
    interrupt_remote_before=run(['git','--git-dir',str(bare),'rev-parse','refs/heads/interrupt-target']).stdout.strip()
    interruption_diag=json.loads(interrupt_result.read_text())
    assert interrupt_remote_before==code_head
    assert interruption_diag['status']=='PUSH_RETRY_EXHAUSTED'
    run(['git','reset','--hard',code_head],cwd=repo)
    retry_head=persist_pre_m04_evidence(root_dir=repo,territory_id='cataluna',edition='2025',run_id=RUN,
        contract_path='territorios/cataluna/config/cataluna_2025.yaml',candidate_evidence=cand,
        source_commit=code_head,target_branch='interrupt-target',max_attempts=1,
        handoff=handoff,handoff_metadata=hmeta)
    interrupt_remote_after=run(['git','--git-dir',str(bare),'rev-parse','refs/heads/interrupt-target']).stdout.strip()
    assert retry_head==interrupt_remote_after and interrupt_remote_after!=code_head

    # Corrupt/inconsistent candidate must fail identity validation before the
    # temporary origin or any durable target is touched.
    bad=tmp/'candidate-corrupt.json'; bad_obj=json.loads(cand.read_text());bad_obj['source']['section_year']=1900;bad.write_text(json.dumps(bad_obj))
    bad_result=OUT/'durable-corrupt-rejection.json'
    run(['git','reset','--hard',code_head],cwd=repo)
    run(['git','push','origin',f'{code_head}:refs/heads/reject-target'],cwd=repo)
    bad_persist=['-m','herramientas.persistir_evidencia_pre_m04_operacional',*common,
                 '--candidate-evidence',str(bad),'--source-commit',code_head,
                 '--target-branch','reject-target','--max-attempts','4','--result-json']
    badrun=run([PYTHON,*bad_persist,str(bad_result)],cwd=repo,env=env,check=False)
    after_bad=run(['git','--git-dir',str(bare),'rev-parse','refs/heads/reject-target']).stdout.strip()
    bad_result_data=json.loads(bad_result.read_text())
    assert badrun.returncode!=0 and after_bad==code_head
    assert bad_result_data['status']=='INCOMPATIBLE_CURRENT_STATE'

    payload={
      'schema':'ddd.cat-pre-m04-durable-roundtrip/1.0','mode':'isolated local filesystem + local bare Git origin; no GitHub write',
      'source_worktree_head':source_head,'isolated_code_snapshot_head':code_head,'isolated_code_snapshot_tree':code_tree,'isolated_code_snapshot_changed_paths':sorted(code_snapshot_paths),
      'tested_local_code_sha256':{rel:sha(repo/rel) for rel in ('herramientas/_resolver_ejecucion_completa_core.py','herramientas/materializar_evidencia_pre_m04.py','herramientas/persistir_evidencia_pre_m04_operacional.py','herramientas/persistir_estado_operativo_compartido.py','herramientas/handoff_evidencia_pre_m04.py')},
      'authentic_inputs':{'run_id':RUN,'m03_artifact_sha256':ART_M03,'m03u_artifact_sha256':ART_M03U,'partition_job_artifact_sha256':ART_JOB,'source_package_sha256':'e904289f179ee4fe552f0bb7dae11b8822d2deecf918eb036bf52a0614e97ee0','compatibility_identity_sha256':'58c715a51035474378a2b8986da25d2b54fa5c714d736c1d3bf2e4e51c85ab6a','section_year':2024,'edition':'2025','municipality':'25234','municipality_sections':['2523401001','2523401002','2523402001','2523402002','2523403001'],'component_sizes':[4,1]},
      'candidate_sha256':sha(cand),'candidate_source_commit':candidate['source_commit'],'candidate_gate':candidate['effective_gate'],
      'handoff_sha256':sha(handoff),'handoff_metadata_sha256':sha(hmeta),'persisted_json_sha256':hashlib.sha256(stored_bytes).hexdigest(),'persisted_equals_candidate_bytes':stored_bytes==candidate_bytes,
      'first_persistence':result1_data,'second_persistence':result2_data,'first_push_head':after_first,'second_push_head':after_second,'idempotent_no_new_commit':after_first==after_second,
      'interrupted_after_local_commit':True,'interruption_error':interruption_error,'interruption_remote_unchanged_before_retry':interrupt_remote_before==code_head,'interruption_result':interruption_diag,'retry_after_interruption_head':retry_head,'interruption_remote_after_retry':interrupt_remote_after,'interruption_retry_persisted':retry_head==interrupt_remote_after and retry_head!=code_head,
      'independent_checkout_head':git(stored_repo,'rev-parse','HEAD'),'independent_checkout_readback':'PASS','handoff_recovery':'PASS',
      'corrupt_candidate_rejected':True,'remote_head_unchanged_after_rejection':after_bad==code_head,'corrupt_candidate_exit_code':badrun.returncode,'corrupt_candidate_persistence_result':bad_result_data,'reject_remote_head_before_after':{'before':code_head,'after':after_bad},
      'm04_executed':False,'territorial_generation_executed':False,
      'limitations':['Local bare Git origin emulates the Git remote boundary; no GitHub Actions/Contents API, permissions or hosted runner were exercised.','The isolated integration code snapshot adds the current dirty core/materializer files to a local test commit derived from HEAD; original run artifacts remain authentic, while source_commit in the test candidate binds to that exact isolated code snapshot.']
    }
    (OUT/'durable-roundtrip.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    (OUT/'durable-candidate.json').write_bytes(candidate_bytes)
    (OUT/'durable-handoff.json').write_bytes(handoff.read_bytes())
    (OUT/'durable-handoff-metadata.json').write_bytes(hmeta.read_bytes())
    (OUT/'durable-persist-result-1.json').write_bytes(result1.read_bytes())
    (OUT/'durable-persist-result-2.json').write_bytes(result2.read_bytes())
    (OUT/'durable-corrupt-rejection.json').write_bytes(bad_result.read_bytes())
    (OUT/'durable-interruption-result.json').write_bytes(interrupt_result.read_bytes())
    (OUT/'durable-persist.stdout.log').write_text('FIRST:\n'+first.stdout+'\nSECOND:\n'+second.stdout+'\nBAD_CANDIDATE_EXIT='+str(badrun.returncode)+'\nBAD_STDERR:\n'+badrun.stderr)
print(json.dumps(payload,ensure_ascii=False,indent=2))
