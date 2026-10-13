"""DDD auto 1.2.0; 2026-10-10; directed offline simulation regression.
Predecessor: infraestructura/ordenes-manuales/legacy/1.1.0/test_ddd_auto.py.
Changes/reason: pilot interface, authorization, atomicity, repair, resource limits.
"""
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'infraestructura/ordenes-manuales'
sys.path.insert(0,str(BUNDLE))
import ddd_auto as auto
REAL=Path(os.environ.get('DDD_AUTO_SIM_REAL_REPO', ROOT if (ROOT/'docs/AUDITORIAS/F04_F10_20261009').exists() else ROOT.parent/'DDD-fuentes-oficiales'))
GIS=Path('/usr/local/Caskroom/miniforge/base/envs/ddd/bin/python3')


def jsonwrite(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


class AutoPilot(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='ddd-auto-sim-',dir=os.environ.get('DDD_AUTO_SIM_OUTPUT',tempfile.gettempdir())))
        self.data=self.root/'launcher';self.data.mkdir()
        for p in BUNDLE.iterdir():
            if p.is_file():shutil.copy2(p,self.data/p.name)
        self.repo=self.root/'DDD-fuentes-oficiales';self.repo.mkdir()
        self.git('init','-b','codex/fuentes-oficiales');self.git('config','user.email','simulation@local.invalid');self.git('config','user.name','DDD Simulation')
        (self.repo/'baseline.txt').write_text('Local infrastructure simulation only\n')
        self.git('add','baseline.txt');self.git('commit','-m','Simulation baseline')
        catalog=json.loads((self.data/'catalogo.json').read_text())
        catalog['worktrees']['fuentes-oficiales']['expected_head_prefix']=self.git('rev-parse','HEAD').strip()
        jsonwrite(self.data/'catalogo.json',catalog)
        self.catalog=catalog
        cfg=json.loads((self.data/'parametros.json').read_text());cfg.update(codex_bin=str(BUNDLE/'codex_simulado.py'),python_gis=str(GIS),segundos_maximos=30)
        jsonwrite(self.data/'parametros.json',cfg)
        self.policy=json.loads((BUNDLE/'auto-policy.json').read_text())
        self.policy.update(authorized_local_tasks=['F03','F04'],revalidate=['F02','F03','F04'])
        self._make_f02_seed()
        self.git('add','receipts');self.git('commit','-m','Synthetic F02 seed fixtures')
        catalog['worktrees']['fuentes-oficiales']['expected_head_prefix']=self.git('rev-parse','HEAD').strip()
        jsonwrite(self.data/'catalogo.json',catalog);self.catalog=catalog
        self.policy['technical_seeds']['F02']={'kind':'F02_14_OFFLINE','path':str(self.seed_path),
            'sha256':auto.digest(self.seed_path),'repo':str(self.repo)}
        packet=self.root/'F03-synthetic.zip'
        import zipfile
        with zipfile.ZipFile(packet,'w') as z:z.writestr('simulation.json','{"task":"F03","result":"PASS"}\n')
        self.policy['tasks']['F03']['inputs']['F03.zip']={'path':str(packet),'sha256':auto.digest(packet)}
        validator=ROOT/'tests/fixtures/ddd_auto_validator_fixture.py'
        self.policy['tasks']['F03']['validators'][0]['argv']=[sys.executable,str(validator),'F03','--repo','{repo}',
            '--output','{output}','--packet','{inputs}/F03.zip']
        self.policy['simulation_acceptance']={t['id']:t['acceptance'][0] for t in catalog['tasks'] if t['id'] in ('F03','F04')}
        for t in self.policy['tasks'].values():t['validate_existing']=False
        # Only the disposable simulation points F04 at pre-existing real evidence.
        # No product/worktree modifications occur there. Normal policy uses delivery/tree.
        self.policy['tasks']['F04']['validators'][0]['argv'][4]=str(REAL)
        jsonwrite(self.data/'policy.json',self.policy)
        self.plan=self.root/'plan';self.plan.mkdir()
        jsonwrite(self.plan/'estado.json',{'plan_revision':'SIMULATION','tasks':[dict(t,status='PASS' if t['id']=='F01' else 'PENDING') for t in catalog['tasks']]})
        self.authorize()
        (self.data/'historial.jsonl').write_text('')
        self.trace=self.root/'codex-calls.jsonl'
        self.env=dict(os.environ,DDD_LAUNCHER_HOME=str(self.data),DDD_PLAN_DIR=str(self.plan),DDD_WORK_ROOT=str(self.root),DDD_FAKE_TRACE=str(self.trace),PYTHONDONTWRITEBYTECODE='1')
        self.auto_root=self.data/'auto'/hashlib.sha256(str(self.plan.resolve()).encode()).hexdigest()[:16]
        self.journal=self.auto_root/'eventos.jsonl'
        self.originals={str(p):auto.digest(p) for p in (self.plan/'estado.json', self.data/'historial.jsonl')}

    def _make_f02_seed(self):
        """Create disposable seed evidence; never treat it as project F02 evidence."""
        self.seed_path=self.root/'F02-synthetic-seed.json'
        rows=[]
        for index in range(14):
            territory=f'SIM-{index:02d}'
            artifact=self.root/f'{territory}.bin';artifact.write_bytes(f'{territory} test bytes\n'.encode())
            receipt_rel=f'receipts/{territory}.json';receipt=self.repo/receipt_rel
            receipt.parent.mkdir(parents=True,exist_ok=True)
            receipt.write_text(json.dumps({'synthetic_test_fixture':True,'territory_id':territory})+'\n')
            rows.append({'territory_id':territory,'artifact_path':str(artifact),'artifact_sha256':auto.digest(artifact),
                'receipt_path':receipt_rel,'controls':{'F02_inventory_receipt_origin':'PASS','F02_bytes_hashes_editions':'PASS'},
                'details':{'F02_inventory_receipt_origin':{'receipt_sha256':auto.digest(receipt)}}})
        jsonwrite(self.seed_path,{'rows':rows,'originals_unchanged':True,'network':'FORBIDDEN',
            'synthetic_test_fixture_only':True})

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL,text=True)

    def command(self,*tasks,extra=()):
        mode=() if '--dry-run' in extra or '--status' in extra else ('--pilot','--run')
        return [sys.executable,str(self.data/'ddd.py'),'auto',*(tasks or ('F03','F04')),'--plan',str(self.plan),'--policy',str(self.data/'policy.json'),*mode,*extra]

    def authorize(self, repair=None):
        for tid,spec in self.policy['tasks'].items():
            receipt={'authority':'Work','decision':'Disposable simulation authorization only',
                     'task':tid,'scope':'local_repair' if repair else 'local_prepare',
                     'plan_sha256':auto.digest(self.plan/'estado.json'),
                     'spec_sha256':auto.object_hash({k:v for k,v in spec.items() if k not in ('authorization','repair_authorization')}),
                     'production':False,'network':False,'budget':{'seconds':30,'max_attempts':1}}
            if repair:
                if tid!=repair:continue
                prior=[e for e in auto.read_events(self.journal) if e['task']==tid][-1]
                receipt.update(cause='Authorized simulation correction',prior_attempt_sha256=auto.digest(Path(prior['attempt'])/'result.json'))
            path=self.root/(tid+('-repair' if repair else '')+'-authorization.json');jsonwrite(path,receipt)
            spec['repair_authorization' if repair else 'authorization']={'path':str(path),'sha256':auto.digest(path)}
        jsonwrite(self.data/'policy.json',self.policy)

    def save_catalog(self,catalog):
        jsonwrite(self.data/'catalogo.json',catalog)
        plan=json.loads((self.plan/'estado.json').read_text());states={t['id']:t['status'] for t in plan['tasks']}
        plan['tasks']=[dict(t,status=states[t['id']]) for t in catalog['tasks']]
        jsonwrite(self.plan/'estado.json',plan)
        self.originals[str(self.plan/'estado.json')]=auto.digest(self.plan/'estado.json')
        self.authorize()

    def run_auto(self,*tasks,scenario='PASS',extra=()):
        p=subprocess.run(self.command(*tasks,extra=extra),env=dict(self.env,DDD_FAKE_SCENARIO=scenario),capture_output=True,text=True,timeout=90)
        self.assertIn(p.returncode,(0,1),p.stdout+p.stderr)
        self.assertEqual(self.originals,{p:auto.digest(p) for p in self.originals})
        return p

    def calls(self):return [json.loads(x) for x in self.trace.read_text().splitlines()] if self.trace.exists() else []
    def states(self):return {e['task']:e['state'] for e in auto.read_events(self.journal)}
    def campaign_path(self):return next(p.parent for p in self.auto_root.glob('*/campaign.json'))

    def test_dependency_satisfied_pass_and_evidence_resume(self):
        p=self.run_auto('F04','F03')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(self.states(),{'F03':'TECH_PASS','F04':'TECH_PASS'})
        calls=self.calls();self.assertEqual(len(calls),4)
        for c in calls:
            a=c['argv'];self.assertEqual(a[a.index('--ask-for-approval')+1],'never')
            self.assertEqual(a[a.index('--sandbox')+1],'read-only' if c['role']=='reviewer' else 'workspace-write')
        folder=self.campaign_path()
        for task in ['F03','F04']:
            result=json.loads((folder/task/'result.json').read_text())
            self.assertEqual(result['dependencies'][0]['state'],'TECH_PASS')
            self.assertTrue(result['dependencies'][0]['external_to_batch'])
            self.assertNotEqual(result['executor_session'],result['reviewer_session'])
            hashes=json.loads((folder/task/'evidence-hashes.json').read_text())
            self.assertEqual(hashes,{n:auto.digest(folder/task/n) for n in hashes})
        before=auto.digest(self.journal)
        self.run_auto('F04','F03',extra=('--resume',folder.name))
        self.assertEqual(len(self.calls()),4);self.assertEqual(auto.digest(self.journal),before)
        self.assertEqual(len(list(folder.glob('summary-*.json'))),2)

    def test_external_dependency_absent_and_dry_run_zero_codex(self):
        self.policy['technical_seeds']={};jsonwrite(self.data/'policy.json',self.policy)
        p=self.run_auto('F03','F04',extra=('--dry-run',))
        self.assertIn('F02',p.stdout);self.assertIn('BLOCKED',p.stdout)
        self.assertFalse((self.data/'auto').exists());self.assertFalse(self.trace.exists())
        p=self.run_auto('F03','F04');self.assertEqual(p.returncode,1)
        self.assertEqual(self.calls(),[]);self.assertEqual(auto.read_events(self.journal),[])

    def test_executor_finished_real_validator_fails_no_retry(self):
        packet=self.root/'invalid-F03.zip';packet.write_bytes(b'Not a zip: real validator must fail')
        self.policy['tasks']['F03']['inputs']['F03.zip']={'path':str(packet),'sha256':auto.digest(packet)}
        # This negative case deliberately exercises the real F03 validator.
        self.policy['tasks']['F03']['validators'][0]['argv']=[sys.executable,str(BUNDLE/'validar_piloto.py'),'F03',
            '--repo','{repo}','--output','{output}','--packet','{inputs}/F03.zip']
        self.authorize()
        p=self.run_auto('F03');self.assertEqual(p.returncode,1,p.stdout)
        self.assertEqual(self.states()['F03'],'BLOCKED')
        result=json.loads((self.campaign_path()/'F03/result.json').read_text())
        self.assertEqual(result['executor']['exit_code'],0)
        self.assertNotEqual(result['tests'][0]['exit_code'],0)
        self.assertEqual([c['role'] for c in self.calls()],['executor'])
        self.run_auto('F03');self.assertEqual(len(self.calls()),1)

    def test_reviewer_no_go_continues_other_enabled_task(self):
        p=self.run_auto(scenario='NO_GO');self.assertEqual(p.returncode,1)
        self.assertEqual(self.states(),{'F03':'REVIEW_NO_GO','F04':'TECH_PASS'})
        self.run_auto();self.assertEqual(len(self.calls()),4)

    def test_invalid_verdict_fails_closed(self):
        self.run_auto('F03',scenario='INVALID_JSON')
        self.assertEqual(self.states()['F03'],'BLOCKED')
        self.assertIn('otra entrega',(self.campaign_path()/'F03/result.json').read_text())

    def test_broken_executor_events_preserve_partial_bytes_sha_diff(self):
        self.run_auto('F03',scenario='BROKEN_EVENTS')
        result=json.loads((self.campaign_path()/'F03/result.json').read_text())
        self.assertEqual(result['state'],'BLOCKED')
        self.assertEqual(result['head_end'],self.git('rev-parse','HEAD').strip())
        name='docs/AUDITORIAS/F03-simulation.txt'
        self.assertIn(name,result['changes'])
        partial=Path(result['partial_delivery'])
        self.assertEqual((partial/'tree'/name).read_bytes(),(self.repo/name).read_bytes())
        self.assertEqual([c['role'] for c in self.calls()],['executor'])

    def test_interrupted_resume_without_repetition(self):
        p=subprocess.Popen(self.command('F03','F04'),env=dict(self.env,DDD_FAKE_SCENARIO='INTERRUPT'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            deadline=time.monotonic()+10
            while not self.calls() and time.monotonic()<deadline:time.sleep(.05)
            self.assertTrue(self.calls());p.send_signal(signal.SIGTERM)
            p.communicate(timeout=10)
        finally:
            if p.poll() is None:p.kill();p.communicate()
        self.assertEqual(self.states()['F03'],'BLOCKED')
        folder=self.campaign_path()
        self.run_auto('F03','F04',extra=('--resume',folder.name))
        self.assertEqual(self.states(),{'F03':'BLOCKED','F04':'TECH_PASS'})
        self.assertEqual(len([c for c in self.calls() if c['task']=='F03']),1)

    def test_legacy_done_review_only_validates_existing(self):
        old={'task':'F03','result':'DONE_REVIEW'}
        (self.data/'historial.jsonl').write_text(json.dumps(old)+'\n')
        self.originals[str(self.data/'historial.jsonl')]=auto.digest(self.data/'historial.jsonl')
        self.run_auto('F03')
        self.assertEqual([c['role'] for c in self.calls()],['reviewer'])
        self.assertEqual(self.states()['F03'],'TECH_PASS')

    def test_worktree_lock_manual_interop_and_separate_data(self):
        with auto.worktree_lock(self.repo):
            p=self.run_auto('F03')
            self.assertIn('Concurrencia bloqueada',p.stdout)
            self.assertEqual(self.calls(),[])
        self.run_auto('F03');self.assertEqual(self.states()['F03'],'TECH_PASS')

    def test_lock_on_one_front_continues_other_free_front(self):
        other=self.root/'DDD-distritos-autonomicos';other.mkdir()
        def git(*a):return subprocess.check_output(['git','-C',str(other),*a],text=True,stderr=subprocess.DEVNULL)
        git('init','-b','codex/distritos-autonomicos');git('config','user.email','simulation@local.invalid');git('config','user.name','DDD Simulation')
        (other/'baseline.txt').write_text('Second disposable worktree\n')
        git('add','baseline.txt');git('commit','-m','Other simulation baseline')
        catalog=copy.deepcopy(self.catalog)
        next(t for t in catalog['tasks'] if t['id']=='F04')['front']='distritos-autonomicos'
        catalog['worktrees']['distritos-autonomicos']['expected_head_prefix']=git('rev-parse','HEAD').strip()
        self.save_catalog(catalog)
        with auto.worktree_lock(self.repo):
            self.run_auto()
            self.assertEqual(self.states(),{'F04':'TECH_PASS'})
            self.assertEqual([c['task'] for c in self.calls()],['F04','F04'])
        self.run_auto();self.assertEqual(self.states(),{'F03':'TECH_PASS','F04':'TECH_PASS'})

    def test_dependency_in_batch_reorders_and_no_go_blocks_consumer(self):
        catalog=copy.deepcopy(self.catalog)
        next(t for t in catalog['tasks'] if t['id']=='F04')['depends_on']=['F03']
        self.save_catalog(catalog)
        self.run_auto('F04','F03',scenario='NO_GO')
        self.assertEqual(self.states(),{'F03':'REVIEW_NO_GO'})
        self.assertEqual([c['task'] for c in self.calls()],['F03','F03'])

    def test_sigkill_child_holds_lock_and_resume_consumes_orphan(self):
        proc=subprocess.Popen(self.command(),env=dict(self.env,DDD_FAKE_SCENARIO='INTERRUPT'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        child=None
        try:
            deadline=time.monotonic()+10
            while not self.calls() and time.monotonic()<deadline:time.sleep(.05)
            self.assertTrue(self.calls())
            folder=self.campaign_path();child=json.loads((folder/'F03/executor.process.json').read_text())['pid']
            proc.kill();proc.communicate(timeout=5)
            blocked=subprocess.run(self.command(extra=('--resume',folder.name)),env=self.env,capture_output=True,text=True,timeout=10)
            self.assertEqual(blocked.returncode,2)
            self.assertIn('Concurrencia bloqueada',blocked.stderr)
            self.assertEqual(len(self.calls()),1)
            os.killpg(child,signal.SIGTERM);time.sleep(.2);child=None
            self.run_auto(extra=('--resume',folder.name))
            self.assertEqual(self.states(),{'F03':'BLOCKED','F04':'TECH_PASS'})
            self.assertEqual(len([c for c in self.calls() if c['task']=='F03']),1)
        finally:
            if proc.poll() is None:proc.kill();proc.communicate()
            if child:
                try:os.killpg(child,signal.SIGKILL)
                except ProcessLookupError:pass

    def test_reserved_and_insufficient_criteria(self):
        self.policy['authorized_local_tasks'].append('F05')
        self.policy['tasks']['F05']={'validators':[]};self.authorize()
        p=self.run_auto('F01','F09','F05',extra=('--dry-run',))
        rows=[json.loads(line) for line in p.stdout.splitlines() if line.startswith('{') and '"task"' in line]
        self.assertEqual([r['state'] for r in rows],['FORMAL_PASS','WAIT_OWNER','BLOCKED'])
        # Provide direct dependencies to isolate the missing validator gate.
        plan=json.loads((self.plan/'estado.json').read_text())
        for t in plan['tasks']:
            if t['id'] in ('F03','F04'):t['status']='PASS'
        jsonwrite(self.plan/'estado.json',plan)
        self.originals[str(self.plan/'estado.json')]=auto.digest(self.plan/'estado.json')
        self.policy['revalidate']=['F02'];self.policy['tasks']['F05']={'validators':[]};self.authorize()
        p=self.run_auto('F05',extra=('--dry-run',));self.assertIn('Criterios ejecutables insuficientes',p.stdout)

    def test_orphan_started_and_corrupt_journal(self):
        self.journal.parent.mkdir(parents=True)
        auto.append(self.journal,{'task':'F03','state':'STARTED','attempt':'historical-orphan'})
        self.run_auto('F03');self.assertEqual(self.states()['F03'],'BLOCKED');self.assertEqual(self.calls(),[])
        with self.journal.open('a') as f:f.write('truncated record')
        p=subprocess.run(self.command('F03'),env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertFalse(self.trace.exists())

    def test_authorization_missing_tampered_scope_and_budget_fail_closed(self):
        spec=self.policy['tasks']['F03'];reference=spec.pop('authorization')
        jsonwrite(self.data/'policy.json',self.policy)
        p=self.run_auto('F03');self.assertIn('Sin autorización acreditada',p.stdout);self.assertEqual(self.calls(),[])
        spec['authorization']=reference
        receipt=json.loads(Path(reference['path']).read_text());receipt['production']=True
        jsonwrite(Path(reference['path']),receipt);reference['sha256']=auto.digest(reference['path'])
        jsonwrite(self.data/'policy.json',self.policy)
        self.run_auto('F03');self.assertEqual(self.calls(),[])
        receipt['production']=False;receipt['budget']['seconds']=0
        jsonwrite(Path(reference['path']),receipt);reference['sha256']=auto.digest(reference['path'])
        jsonwrite(self.data/'policy.json',self.policy)
        self.run_auto('F03');self.assertEqual(self.calls(),[])

    def test_required_interface_status_and_front_no_write(self):
        args=[sys.executable,str(self.data/'ddd.py'),'auto','--plan',str(self.plan),'--front','distritos-nacionales','--status','--policy',str(self.data/'policy.json')]
        before={str(p):auto.digest(p) for p in self.data.rglob('*') if p.is_file()}
        p=subprocess.run(args,env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('N02',p.stdout);self.assertNotIn('"task": "F03"',p.stdout)
        self.assertEqual(before,{str(p):auto.digest(p) for p in self.data.rglob('*') if p.is_file()})
        p=subprocess.run(args[:-4]+['--run'],env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertEqual(self.calls(),[])

    def test_formal_inconsistency_gates_and_catalog_drift(self):
        plan=json.loads((self.plan/'estado.json').read_text())
        for t in plan['tasks']:
            if t['id']=='F05':t['status']='PASS'
        jsonwrite(self.plan/'estado.json',plan);self.originals[str(self.plan/'estado.json')]=auto.digest(self.plan/'estado.json')
        self.authorize()
        p=self.run_auto('F05',extra=('--dry-run',))
        rows=[json.loads(s) for s in p.stdout.splitlines() if s.startswith('{')]
        self.assertFalse(rows[0]['gates']['accept']);self.assertFalse(rows[0]['gates']['integrate']);self.assertFalse(rows[0]['gates']['produce'])
        self.assertIn('F05',str(rows[1]['plan']['inconsistencies']))
        plan['tasks'][0]['depends_on']=['UNKNOWN'];jsonwrite(self.plan/'estado.json',plan)
        p=subprocess.run(self.command('F03'),env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertFalse(self.trace.exists())

    def test_authorized_repair_one_attempt_then_no_automatic_retry(self):
        packet=self.root/'bad.zip';packet.write_bytes(b'bad zip')
        original=copy.deepcopy(self.policy['tasks']['F03']['inputs'])
        self.policy['tasks']['F03']['inputs']={'F03.zip':{'path':str(packet),'sha256':auto.digest(packet)}};self.authorize()
        self.run_auto('F03');self.assertEqual(self.states()['F03'],'BLOCKED')
        self.run_auto('F03',extra=('--repair','F03'));self.assertEqual(len(self.calls()),1)
        self.policy['tasks']['F03']['inputs']=original;self.authorize();self.authorize(repair='F03')
        self.run_auto('F03',extra=('--repair','F03'))
        self.assertEqual(self.states()['F03'],'TECH_PASS');self.assertEqual(len(self.calls()),3)
        self.run_auto('F03',extra=('--repair','F03'));self.assertEqual(len(self.calls()),3)

    def test_tampered_pass_evidence_blocks_consumer_without_retry(self):
        catalog=copy.deepcopy(self.catalog);next(t for t in catalog['tasks'] if t['id']=='F04')['depends_on']=['F03'];self.save_catalog(catalog)
        self.run_auto('F03');folder=self.campaign_path()
        result=folder/'F03/result.json';result.chmod(0o644);result.write_text('{}\n')
        p=self.run_auto('F04');self.assertIn('BLOCKED',p.stdout);self.assertEqual(len(self.calls()),2)

    def test_out_of_scope_mode_change_never_passes(self):
        self.run_auto('F03',scenario='OUT_OF_SCOPE_MODE')
        self.assertEqual(self.states()['F03'],'BLOCKED');self.assertEqual(len(self.calls()),1)
        result=json.loads((self.campaign_path()/'F03/result.json').read_text())
        self.assertIn('fuera del alcance',result['reason'])

    def test_ignored_existing_bytes_protected(self):
        (self.repo/'.gitignore').write_text('protected-data.bin\n')
        self.git('add','.gitignore');self.git('commit','-m','Ignore protected fixture')
        (self.repo/'protected-data.bin').write_bytes(b'protected original')
        self.run_auto('F03',scenario='IGNORED_CHANGE')
        self.assertEqual(self.states()['F03'],'BLOCKED');self.assertEqual(len(self.calls()),1)
        result=json.loads((self.campaign_path()/'F03/result.json').read_text())
        self.assertIn('fuera del alcance',result['reason'])

    def test_resume_rejects_changed_authoritative_revision(self):
        self.run_auto('F03',extra=('--dry-run',))
        # A blocked, unattempted campaign suffices to test identity without Codex.
        self.policy['authorized_local_tasks']=[];jsonwrite(self.data/'policy.json',self.policy)
        self.run_auto('F03');folder=self.campaign_path()
        plan=json.loads((self.plan/'estado.json').read_text());plan['plan_revision']='CHANGED';jsonwrite(self.plan/'estado.json',plan)
        p=subprocess.run(self.command('F03',extra=('--resume',folder.name)),env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertIn('misma revisión',p.stderr);self.assertEqual(self.calls(),[])


class ControllerContracts(unittest.TestCase):
    def test_process_checkpoint_failure_stops_real_child(self):
        processes=[];original=subprocess.Popen
        def start(*args,**kwargs):
            p=original(*args,**kwargs);processes.append(p);return p
        def stop(p):
            p.terminate();p.wait(timeout=3)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(auto.subprocess,'Popen',side_effect=start),patch.object(auto,'write_new',side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    auto.run_process([sys.executable,'-c','import time;time.sleep(30)'],Path(tmp),None,Path(tmp)/'child.log',2,stop)
            self.assertEqual(len(processes),1);self.assertIsNotNone(processes[0].poll())

    def test_atomic_failure_keeps_checkpoint_and_exclusive_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'events.jsonl';auto.append(p,{'task':'F03','state':'STARTED'});before=p.read_bytes()
            with patch.object(auto.os,'replace',side_effect=OSError('simulated crash')):
                with self.assertRaises(OSError):auto.append(p,{'task':'F03','state':'TECH_PASS'})
            self.assertEqual(p.read_bytes(),before);self.assertEqual(list(Path(tmp).glob('.atomic-*')),[])
            q=Path(tmp)/'checkpoint.json';auto.write_new(q,{'state':'STARTED'})
            with self.assertRaises(FileExistsError):auto.write_new(q,{'state':'PASS'})
            self.assertEqual(json.loads(q.read_text()),{'state':'STARTED'})

    def test_two_session_slots_and_one_gis_across_processes(self):
        command=[sys.executable,'-c','import sys; sys.path.insert(0,sys.argv[1]); import ddd_auto as a; ctx=a.session_slot() if sys.argv[2]=="session" else a.gis_lock(True); ctx.__enter__()',str(BUNDLE)]
        with auto.session_slot(),auto.session_slot():
            p=subprocess.run(command+['session'],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('máximo dos',p.stderr)
        with auto.gis_lock(True):
            p=subprocess.run(command+['gis'],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0);self.assertIn('Concurrencia bloqueada',p.stderr)
        self.assertEqual(subprocess.run(command+['session'],capture_output=True).returncode,0)

    def test_installer_dry_run_backup_and_protected_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'manual';target.mkdir()
            shutil.copy2(BUNDLE/'legacy/1.0.0/ddd.py',target/'ddd.py')
            for name in ('catalogo.json','parametros.json','encargos.json'):
                shutil.copy2(BUNDLE/name,target/name)
            (target/'historial.jsonl').write_text('{"task":"F03","result":"TIME_LIMIT"}\n')
            (target/'logs').mkdir();(target/'logs/old.log').write_text('untouched')
            original={str(p.relative_to(target)):auto.digest(p) for p in target.rglob('*') if p.is_file()}
            command=['bash',str(ROOT/'scripts/instalar-ddd-auto.sh'),'--target',str(target)]
            p=subprocess.run(command+['--dry-run'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(original,{str(p.relative_to(target)):auto.digest(p) for p in target.rglob('*') if p.is_file()})
            p=subprocess.run(command+['--apply'],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            backup=next((target/'respaldos-instalacion').iterdir())
            for name,sha in original.items():
                self.assertEqual(auto.digest(backup/name if name=='ddd.py' else target/name),sha)
            self.assertEqual(auto.digest(target/'ddd.py'),auto.digest(BUNDLE/'ddd.py'))
    def test_full_graph_unknown_and_cycle(self):
        with self.assertRaises(ValueError):auto.graph({'F03':{'depends_on':['F02']}})
        with self.assertRaises(ValueError):auto.graph({'F03':{'depends_on':['F04']},'F04':{'depends_on':['F03']}})

    def test_schema_rejects_unknown_or_missing_and_wrong_type(self):
        schema=json.loads((BUNDLE/'review.schema.json').read_text())
        for value in [{},{'verdict':'PASS'},{'verdict':True}]:
            with self.assertRaises(ValueError):auto.validate_schema(value,schema)

if __name__=='__main__':unittest.main()
