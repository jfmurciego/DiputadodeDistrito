"""DDD auto 1.1.0; 2026-10-10; directed offline simulation regression.
Origin: new controller acceptance, no predecessor. Codex fake, validators real.
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

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'infraestructura/ordenes-manuales'
sys.path.insert(0,str(BUNDLE))
import ddd_auto as auto
REAL=Path('/Users/macbookpro/Desarrollo/DDD-fuentes-oficiales')
GIS=Path('/usr/local/Caskroom/miniforge/base/envs/ddd/bin/python3')


def jsonwrite(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')


class AutoPilot(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='ddd-auto-sim-',dir=os.environ.get('DDD_AUTO_SIM_OUTPUT','/private/tmp')))
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
        self.policy['simulation_acceptance']={t['id']:t['acceptance'][0] for t in catalog['tasks'] if t['id'] in ('F03','F04')}
        for t in self.policy['tasks'].values():t['validate_existing']=False
        # Only the disposable simulation points F04 at pre-existing real evidence.
        # No product/worktree modifications occur there. Normal policy uses delivery/tree.
        self.policy['tasks']['F04']['validators'][0]['argv'][4]=str(REAL)
        jsonwrite(self.data/'policy.json',self.policy)
        self.plan=self.root/'plan';self.plan.mkdir()
        jsonwrite(self.plan/'estado.json',{'tasks':[{'id':t['id'],'status':'PENDING'} for t in catalog['tasks']]})
        (self.data/'historial.jsonl').write_text('')
        self.trace=self.root/'codex-calls.jsonl'
        self.env=dict(os.environ,DDD_LAUNCHER_HOME=str(self.data),DDD_PLAN_DIR=str(self.plan),DDD_WORK_ROOT=str(self.root),DDD_FAKE_TRACE=str(self.trace),PYTHONDONTWRITEBYTECODE='1')
        self.journal=self.data/'auto/eventos.jsonl'
        self.originals={str(p):auto.digest(p) for p in (self.plan/'estado.json', self.data/'historial.jsonl')}

    def git(self,*args):
        return subprocess.check_output(['git','-C',str(self.repo),*args],stderr=subprocess.DEVNULL,text=True)

    def command(self,*tasks,extra=()):
        return [sys.executable,str(self.data/'ddd.py'),'auto',*(tasks or ('F03','F04')),'--policy',str(self.data/'policy.json'),*extra]

    def run_auto(self,*tasks,scenario='PASS',extra=()):
        p=subprocess.run(self.command(*tasks,extra=extra),env=dict(self.env,DDD_FAKE_SCENARIO=scenario),capture_output=True,text=True,timeout=90)
        self.assertIn(p.returncode,(0,1),p.stdout+p.stderr)
        self.assertEqual(self.originals,{p:auto.digest(p) for p in self.originals})
        return p

    def calls(self):return [json.loads(x) for x in self.trace.read_text().splitlines()] if self.trace.exists() else []
    def states(self):return {e['task']:e['state'] for e in auto.read_events(self.journal)}
    def campaign_path(self):return next(p.parent for p in (self.data/'auto').glob('*/campaign.json'))

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
        jsonwrite(self.data/'policy.json',self.policy)
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
        jsonwrite(self.data/'catalogo.json',catalog)
        with auto.worktree_lock(self.repo):
            self.run_auto()
            self.assertEqual(self.states(),{'F04':'TECH_PASS'})
            self.assertEqual([c['task'] for c in self.calls()],['F04','F04'])
        self.run_auto();self.assertEqual(self.states(),{'F03':'TECH_PASS','F04':'TECH_PASS'})

    def test_dependency_in_batch_reorders_and_no_go_blocks_consumer(self):
        catalog=copy.deepcopy(self.catalog)
        next(t for t in catalog['tasks'] if t['id']=='F04')['depends_on']=['F03']
        jsonwrite(self.data/'catalogo.json',catalog)
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
        jsonwrite(self.data/'policy.json',self.policy)
        p=self.run_auto('F01','F09','F05',extra=('--dry-run',))
        rows=[json.loads(line) for line in p.stdout.splitlines() if line.startswith('{')]
        self.assertEqual([r['state'] for r in rows],['WAIT_OWNER','WAIT_OWNER','BLOCKED'])
        # Provide direct dependencies to isolate the missing validator gate.
        self.plan.joinpath('estado.json').write_text(json.dumps({'tasks':[{'id':'F03','status':'PASS'},{'id':'F04','status':'PASS'}]}))
        self.originals[str(self.plan/'estado.json')]=auto.digest(self.plan/'estado.json')
        self.policy['revalidate']=['F02'];jsonwrite(self.data/'policy.json',self.policy)
        p=self.run_auto('F05',extra=('--dry-run',));self.assertIn('Criterios ejecutables insuficientes',p.stdout)

    def test_orphan_started_and_corrupt_journal(self):
        self.journal.parent.mkdir()
        auto.append(self.journal,{'task':'F03','state':'STARTED','attempt':'historical-orphan'})
        self.run_auto('F03');self.assertEqual(self.states()['F03'],'BLOCKED');self.assertEqual(self.calls(),[])
        with self.journal.open('a') as f:f.write('truncated record')
        p=subprocess.run(self.command('F03'),env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertFalse(self.trace.exists())


class ControllerContracts(unittest.TestCase):
    def test_full_graph_unknown_and_cycle(self):
        with self.assertRaises(ValueError):auto.graph({'F03':{'depends_on':['F02']}})
        with self.assertRaises(ValueError):auto.graph({'F03':{'depends_on':['F04']},'F04':{'depends_on':['F03']}})

    def test_schema_rejects_unknown_or_missing_and_wrong_type(self):
        schema=json.loads((BUNDLE/'review.schema.json').read_text())
        for value in [{},{'verdict':'PASS'},{'verdict':True}]:
            with self.assertRaises(ValueError):auto.validate_schema(value,schema)

if __name__=='__main__':unittest.main()
