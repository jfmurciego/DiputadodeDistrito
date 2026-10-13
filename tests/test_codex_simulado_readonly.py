import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SIMULATOR = Path(__file__).parents[1] / 'infraestructura/ordenes-manuales/codex_simulado.py'


class ReadOnlySimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.trace = self.root / 'trace.jsonl'
        self.env = os.environ | {
            'DDD_FAKE_TRACE': str(self.trace),
            'DDD_FAKE_CRITERIA': json.dumps({'F10-TEST': [['source identity checked'], ['manifest hash preserved']]}),
            'DDD_FAKE_LIMITATIONS': json.dumps({'F10-TEST': 'simulation only'}),
        }

    def tearDown(self):
        self.temp.cleanup()

    def test_structured_executor_uses_manifest_and_normalizes_limitations(self):
        task = self.root / 'F10-TEST'
        executor = task / 'executor'
        executor.mkdir(parents=True)
        manifest = {'task': 'F10-TEST', 'head': 'abc123', 'files': ['evidence.json']}
        (task / 'input-manifest.json').write_text(json.dumps(manifest))
        schema = self.root / 'executor.schema.json'
        schema.write_text('{}')
        output = self.root / 'summary.json'
        subprocess.run(
            [sys.executable, str(SIMULATOR), '--output-schema', str(schema), '--output-last-message', str(output)],
            cwd=executor, env=self.env, input='READ_ONLY task prompt', text=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        summary = json.loads(output.read_text())
        self.assertEqual(summary['task'], 'F10-TEST')
        self.assertEqual(summary['head'], 'abc123')
        self.assertEqual(summary['limitations'], ['simulation only', 'SIMULATION_ONLY'])
        self.assertEqual(summary['criteria_verified'], ['source identity checked', 'manifest hash preserved'])

    def test_structured_reviewer_flattens_single_nested_policy_criterion(self):
        task = self.root / 'F10-TEST'
        reviewer = task / 'reviewer'
        (reviewer / 'controller').mkdir(parents=True)
        (task / 'delivery-manifest.json').write_text(json.dumps({'task': 'F10-TEST', 'head': 'abc123'}))
        (reviewer / 'controller/policy.json').write_text(json.dumps({'simulation_acceptance': {'F10-TEST': [['source identity checked'], ['second criterion'], ['third criterion']]}}))
        schema = self.root / 'reviewer.schema.json'
        schema.write_text('{}')
        output = self.root / 'review.json'
        subprocess.run(
            [sys.executable, str(SIMULATOR), '--output-schema', str(schema), '--output-last-message', str(output)],
            cwd=reviewer, env=self.env, input='structured review', text=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        verdict = json.loads(output.read_text())
        self.assertEqual(verdict['task'], 'F10-TEST')
        self.assertEqual(verdict['criteria_passed'], ['source identity checked', 'second criterion', 'third criterion'])
        self.assertEqual(verdict['scope'], 'LOCAL_TECHNICAL_ONLY')

    def test_structured_reviewer_rejects_non_string_criteria(self):
        task = self.root / 'F10-TEST'
        reviewer = task / 'reviewer'
        (reviewer / 'controller').mkdir(parents=True)
        (task / 'delivery-manifest.json').write_text(json.dumps({'task': 'F10-TEST', 'head': 'abc123'}))
        (reviewer / 'controller/policy.json').write_text(json.dumps({'simulation_acceptance': {'F10-TEST': [['valid criterion'], 7]}}))
        schema = self.root / 'reviewer.schema.json'
        schema.write_text('{}')
        output = self.root / 'review.json'
        result = subprocess.run(
            [sys.executable, str(SIMULATOR), '--output-schema', str(schema), '--output-last-message', str(output)],
            cwd=reviewer, env=self.env, input='structured review', text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
