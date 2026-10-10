"""DDD F05-F08 tracked-reference regression, version 1.0.0, 2026-10-10.
Scope: clean checkout, metadata and historical aggregation only. Candidate.
Reason: remove untracked dependency; origin 0e09de5f; no predecessor.
No acquisitions, package consumption, territorial runs or gate changes.
"""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[4]
PREFIX = 'docs/AUDITORIAS/F04_F10_20261009/continuacion/'
OLD = 'docs/AUDITORIAS/verificacion_F02_F03_2026-10-09.json'
NEW = PREFIX + 'evidencia-previa-reutilizada.json'
FILES = ['acreditar_identidades.py', 'verificar_offline.py',
         'identity-alignment.json', 'offline-results.json', 'matriz-19-final.json']

def normalized(value):
    if isinstance(value, str):
        return value.replace(OLD, NEW)
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, dict):
        return {key: normalized(item) for key, item in value.items() if key != 'version'}
    return value

class CleanCheckoutReferences(unittest.TestCase):
    def test_checkout_has_only_tracked_evidence(self):
        self.assertFalse((ROOT / OLD).exists())
        self.assertEqual(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True), '')
        self.assertEqual(hashlib.sha256((ROOT / NEW).read_bytes()).hexdigest(),
                         '08ee87ca4e904075d3b229964b61a184ab64a63d83bae7b879383fb39651dac6')
        for name in FILES:
            self.assertNotIn(OLD, (ROOT / PREFIX / name).read_text())

    def test_metadata_script_reproduces_exact_result(self):
        output = ROOT / PREFIX / 'identity-alignment.json'
        expected = output.read_bytes()
        result = subprocess.run([sys.executable, '-B', str(ROOT / PREFIX / 'acreditar_identidades.py')],
                                cwd=ROOT, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'},
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(output.read_bytes(), expected)

    def test_real_historical_aggregation_without_consumption(self):
        output = ROOT / PREFIX / 'offline-results.json'
        expected = output.read_bytes()
        saved = json.loads(expected)
        # Execute the actual suffix that only reads/aggregates historical results.
        # The unchanged first-five consumer checks are deliberately not executed.
        source = ast.parse((ROOT / PREFIX / 'verificar_offline.py').read_text())
        start = next(index for index, node in enumerate(source.body)
                     if isinstance(node, ast.Assign) and any(
                         isinstance(target, ast.Name) and target.id == 'prior' for target in node.targets))
        suffix = ast.Module(body=source.body[start:], type_ignores=[])
        namespace = {'json': json, 'ROOT': ROOT, 'OUT': ROOT / PREFIX,
                     'results': saved['rows'][:5]}
        exec(compile(suffix, 'verificar_offline.py:historical_aggregation_only', 'exec'), namespace)
        self.assertEqual(output.read_bytes(), expected)
        self.assertEqual(len(namespace['results']), 19)
        self.assertEqual(sum(row['canonical_territorial_consumer']['result'] == 'PASS_REUSED'
                             for row in namespace['results']), 14)
        self.assertEqual(sum(row['canonical_territorial_consumer']['result'] == 'BLOCKED'
                             for row in namespace['results']), 5)

    def test_results_and_criteria_unchanged(self):
        for name in FILES[2:]:
            current = json.loads((ROOT / PREFIX / name).read_text())
            predecessor = json.loads((ROOT / 'legacy' / PREFIX / name).read_text())
            self.assertEqual(normalized(current), normalized(predecessor), name)
        self.assertEqual(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True), '')

if __name__ == '__main__':
    unittest.main(verbosity=2)
