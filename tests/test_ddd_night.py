"""DDD night regression 1.0.0; 2026-10-11; new disposable simulations only.
Origin: user night supervisor specification; no real pilot is claimed.
"""
import copy
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from tests import test_ddd_auto as fixtures
from tests.test_ddd_auto import BUNDLE, auto, jsonwrite


class Night(unittest.TestCase):
    setUp = fixtures.AutoPilot.setUp
    tearDown = fixtures.AutoPilot.tearDown
    git = fixtures.AutoPilot.git
    command = fixtures.AutoPilot.command
    authorize = fixtures.AutoPilot.authorize
    save_catalog = fixtures.AutoPilot.save_catalog
    calls = fixtures.AutoPilot.calls
    states = fixtures.AutoPilot.states
    campaign_path = fixtures.AutoPilot.campaign_path
    run_auto = fixtures.AutoPilot.run_auto

    def owner_fixture(self):
        """Only synthetic repositories and approvals inside this test's directory."""
        catalog = copy.deepcopy(self.catalog)
        for tid,front in [('F03','distritos-autonomicos'),('F04','distritos-nacionales')]:
            name = catalog['worktrees'][front]['path'].split('/')[-1]
            repo = self.root/name
            shutil.copytree(self.repo,repo)
            subprocess.check_call(['git','-C',str(repo),'branch','-m','codex/'+front],stdout=subprocess.DEVNULL)
            catalog['worktrees'][front]['expected_head_prefix']=self.git('rev-parse','HEAD').strip()
            task = next(t for t in catalog['tasks'] if t['id']==tid)
            task.update(front=front,preparation_dependencies=[])
            spec = self.policy['tasks'][tid]
            spec.update(work_class='READ_ONLY', read_only_paths=['baseline.txt'], inputs={},validate_existing=False,
                        allowed_change_prefixes=[], prepare_dependencies=[])
            spec['validators']=[{'covers':[0], 'local_only':True,'argv':[sys.executable,'-c',
                'from pathlib import Path; assert Path("baseline.txt").read_text().startswith("Local infrastructure")']}]
        self.policy['technical_seeds']={}
        self.save_catalog(catalog)
        proof=self.root/'TEST_ONLY-owner-approval.txt';proof.write_text('SYNTHETIC OWNER FIXTURE; NOT HUMAN AUTHORIZATION\n')
        now=datetime.datetime.now(datetime.timezone.utc)
        receipt={'schema':'ddd.owner-window/1.0','authority':'Owner','status':'APPROVED','window_kind':'PILOT','approval_ref':{'path':str(proof),'sha256':auto.digest(proof)},
                 'plan_sha256':auto.digest(self.plan/'estado.json'),'catalog_sha256':auto.object_hash(catalog),
                 'window':{'start_utc':(now-datetime.timedelta(minutes=1)).isoformat(),'end_utc':(now+datetime.timedelta(minutes=5)).isoformat()},
                 'classes':['READ_ONLY'],'network':False,'production':False,
                 'guards':{'sessions_max':2,'gis_max':1,'review_required':True},'budget':{'seconds':60,'max_tasks':2},'tasks':{}}
        for tid,spec in self.policy['tasks'].items():
            receipt['tasks'][tid]={'spec_sha256':auto.object_hash({k:v for k,v in spec.items() if k not in ('authorization','repair_authorization')}),
                                   'work_class':'READ_ONLY','budget':{'seconds':30,'max_attempts':1}}
        path=self.root/'TEST_ONLY-owner-window.json';jsonwrite(path,receipt)
        for spec in self.policy['tasks'].values():spec['authorization']={'path':str(path),'sha256':auto.digest(path)}
        jsonwrite(self.data/'policy.json',self.policy)
        self.env['DDD_FAKE_CRITERIA']=json.dumps({t['id']:t['acceptance'] for t in catalog['tasks']})
        self.catalog=catalog
        return path,receipt

    def test_more_than_32_aliases_and_exact_long_prompt(self):
        catalog=copy.deepcopy(self.catalog)
        for i in range(8):
            task=copy.deepcopy(catalog['tasks'][0]);task.update(id='EXTRA'+str(i),status='PENDING',depends_on=[],execution='research',
                                                              origin='proposed_extension_fixture',aliases=['alias'+str(i)])
            catalog['tasks'].append(task)
        text='LONG SPEC EXACT\n'+('Objetivo local acreditado.\n'*200)
        path=self.data/'long.md';path.write_text(text)
        catalog['tasks'][0].update(prompt_file='long.md',prompt_sha256=auto.digest(path))
        jsonwrite(self.data/'catalogo.json',catalog)
        p=subprocess.run([sys.executable,str(self.data/'ddd.py'),'list'],env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('40 fichas',p.stdout)
        # Prompt fidelity is verified by the public composer against exact hashed bytes.
        script='import ddd; ddd.load_catalog(ddd.BASE/"catalogo.json"); print(ddd.prompt_master(ddd.TASKS["F01"]))'
        p=subprocess.run([sys.executable,'-c',script],cwd=self.data,env=self.env,capture_output=True,text=True)
        self.assertTrue(p.stdout.startswith(text),p.stderr)
        p=subprocess.run([sys.executable,str(self.data/'ddd.py'),'show','alias3'],env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr);self.assertIn('EXTRA3',p.stdout)
        catalog['tasks'][-1]['aliases']=['alias3'];jsonwrite(self.data/'catalogo.json',catalog)
        p=subprocess.run([sys.executable,str(self.data/'ddd.py'),'list'],env=self.env,capture_output=True,text=True)
        self.assertEqual(p.returncode,2);self.assertIn('Alias ambiguo',p.stderr)

    def test_zero_night_never_writes_or_calls_codex(self):
        before={str(p):auto.digest(p) for p in self.root.rglob('*') if p.is_file()}
        p=self.run_auto(extra=('--night','--dry-run'))
        self.assertEqual(p.returncode,1);self.assertIn('NO_READY',p.stdout)
        self.assertEqual(before,{str(p):auto.digest(p) for p in self.root.rglob('*') if p.is_file()})
        p=self.run_auto(extra=('--night',));self.assertEqual(p.returncode,1)
        self.assertFalse(self.auto_root.exists());self.assertEqual(self.calls(),[])

    def test_two_readonly_fronts_no_go_continues_and_inbox_accumulates(self):
        self.owner_fixture()
        self.run_auto(scenario='NO_GO',extra=('--night',))
        self.assertEqual(self.states(),{'F03':'REVIEW_NO_GO','F04':'TECH_PASS'})
        self.assertEqual(len(self.calls()),4)
        for c in self.calls():
            self.assertEqual(c['argv'][c['argv'].index('--sandbox')+1],'read-only')
        folder=self.campaign_path()
        self.assertEqual(len(list(folder.glob('BANDEJA_MATINAL-*.md'))),1)
        self.run_auto(extra=('--night','--resume',folder.name))
        self.assertEqual(len(self.calls()),4)
        self.assertEqual(len(list(folder.glob('BANDEJA_MATINAL-*.md'))),2)
        inbox=json.loads(next(folder.glob('summary-*.json')).read_text())['morning_inbox']
        self.assertEqual(len(inbox['accumulated_deliveries']),2)

    def test_owner_window_draft_expired_and_input_drift_fail_closed(self):
        path,receipt=self.owner_fixture()
        receipt['status']='DRAFT';jsonwrite(path,receipt)
        for spec in self.policy['tasks'].values():spec['authorization']['sha256']=auto.digest(path)
        jsonwrite(self.data/'policy.json',self.policy)
        p=self.run_auto(extra=('--night','--dry-run'));self.assertEqual(p.returncode,1)
        self.assertEqual(self.calls(),[])
        receipt['status']='APPROVED';receipt['window']['end_utc']='2000-01-01T00:00:00+00:00';jsonwrite(path,receipt)
        for spec in self.policy['tasks'].values():spec['authorization']['sha256']=auto.digest(path)
        jsonwrite(self.data/'policy.json',self.policy)
        p=self.run_auto(extra=('--night','--dry-run'));self.assertIn('expirada',p.stdout)

    def test_dirty_one_front_continues_other(self):
        self.policy['tasks']['F03']['validate_existing']=False
        catalog=copy.deepcopy(self.catalog)
        front='distritos-nacionales';other=self.root/'DDD-distritos-nacionales'
        shutil.copytree(self.repo,other)
        subprocess.check_call(['git','-C',str(other),'branch','-m','codex/'+front],stdout=subprocess.DEVNULL)
        next(t for t in catalog['tasks'] if t['id']=='F04')['front']=front
        catalog['worktrees'][front]['expected_head_prefix']=self.git('rev-parse','HEAD').strip()
        self.save_catalog(catalog)
        (self.repo/'foreign-dirty.txt').write_text('previous author, preserved')
        p=self.run_auto()
        self.assertIn('Worktree sucio',p.stdout)
        self.assertEqual(self.states(),{'F04':'TECH_PASS'})
        self.assertEqual([c['task'] for c in self.calls()],['F04','F04'])
        self.assertEqual((self.repo/'foreign-dirty.txt').read_text(),'previous author, preserved')

    def test_quota_stops_other_tasks_until_explicit_resume(self):
        self.run_auto(scenario='QUOTA')
        self.assertEqual(self.states()['F03'],'QUOTA_STOP');self.assertEqual(len(self.calls()),1)
        p=self.run_auto();self.assertEqual(len(self.calls()),1);self.assertIn('NO_READY',p.stdout)
        folder=self.campaign_path()
        self.run_auto(extra=('--resume',folder.name))
        self.assertEqual(self.states()['F04'],'TECH_PASS')
        self.assertEqual(len([c for c in self.calls() if c['task']=='F03']),1)


class PilotReceipt(unittest.TestCase):
    """Synthetic receipts exercise verification only; they never certify a pilot."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.results = []
        for tid, front in [('A', 'distritos-autonomicos'), ('N', 'distritos-nacionales')]:
            self.results.append({'task': tid, 'front': front, 'state': 'TECH_PASS',
                'work_class': 'READ_ONLY', 'dependencies': [],
                'executor_session': 'executor-'+tid, 'reviewer_session': 'reviewer-'+tid,
                'executor': {'argv': ['codex', '--sandbox', 'read-only', '--ask-for-approval', 'never']},
                'reviewer': {'argv': ['codex', '--sandbox', 'read-only', '--ask-for-approval', 'never']},
                'review': {'verdict': 'PASS'}, 'tests': [{'exit_code': 0, 'timeout': False}]})

    def tearDown(self):
        self.tmp.cleanup()

    def reference(self):
        tasks = []
        for result in self.results:
            folder = self.root/result['task']; folder.mkdir(exist_ok=True)
            path = folder/'result.json'; jsonwrite(path, result)
            jsonwrite(folder/'evidence-hashes.json', {'result.json': auto.digest(path)})
            tasks.append({'result_path': str(path), 'result_sha256': auto.digest(path)})
        path = self.root/'TEST_ONLY-receipt.json'
        jsonwrite(path, {'mode': 'REAL_CODEX', 'result': 'PASS', 'tasks': tasks})
        return {'path': str(path), 'sha256': auto.digest(path)}

    def test_valid_receipt_structure(self):
        auto.validate_real_pilot(self.reference())

    def test_missing_reviewer_fails_closed(self):
        self.results[0].pop('reviewer_session')
        with self.assertRaises(ValueError): auto.validate_real_pilot(self.reference())

    def test_writable_or_interactive_sessions_fail_closed(self):
        for role in ('executor', 'reviewer'):
            for index, value in [(2, 'workspace-write'), (4, 'on-request')]:
                with self.subTest(role=role, value=value):
                    self.results[0][role]['argv'][index] = value
                    with self.assertRaises(ValueError): auto.validate_real_pilot(self.reference())
                    self.results[0][role]['argv'] = ['codex', '--sandbox', 'read-only', '--ask-for-approval', 'never']

    def test_non_readonly_or_dependent_tasks_fail_closed(self):
        self.results[0]['work_class'] = 'LOCAL_IMPLEMENTATION'
        with self.assertRaises(ValueError): auto.validate_real_pilot(self.reference())
        self.results[0]['work_class'] = 'READ_ONLY'
        self.results[1]['dependencies'] = [{'task': 'A', 'state': 'TECH_PASS'}]
        with self.assertRaises(ValueError): auto.validate_real_pilot(self.reference())


if __name__=='__main__':unittest.main()
