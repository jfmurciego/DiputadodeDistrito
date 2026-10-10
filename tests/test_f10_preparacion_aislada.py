"""F10 caller aislado v1.0.1; 2026-10-10; candidato local.

Alcance: límites de ejecución y preservación de acreditaciones #179.
Cambios: nuevas regresiones; motivo: impedir persistencia/generación o SHA prestado.
Origen: main@579ab82e84aadba778b0fe7d138ea96b66457e1e.
Predecesor: legacy/tests/test_f10_preparacion_aislada_v1.0.0.py; nombres CODAUTO.
"""
import json
import os
import subprocess
import unittest
from pathlib import Path

import yaml

from herramientas.consumir_par_fuentes_legislatura import (
    PreparedPairExecutionBlock, validate_territorial_receipt,
)
from herramientas.evaluar_persistencia_preparacion import resolve_persist_state, terminal_decision

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / '.github/workflows/f10-preparacion-territorial-aislada.yml'
TERRITORIES = {'andalucia', 'aragon', 'castilla_y_leon', 'comunidad_valenciana', 'extremadura'}
CHOICES = ['01 Andalucía', '02 Aragón', '07 Castilla y León', '10 Comunidad Valenciana', '11 Extremadura']


class F10PreparacionAisladaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load(PATH.read_text())
        cls.events = cls.workflow.get('on', cls.workflow.get(True))
        cls.guard = cls.workflow['jobs']['comprobar']['steps'][0]['run']

    def run_guard(self, territory, reviewed, actual='a' * 40):
        return subprocess.run(['bash', '-c', self.guard], env={
            **os.environ, 'TERRITORY_ID': territory, 'REVIEWED_SHA': reviewed,
            'ACTUAL_SHA': actual,
        }, capture_output=True, text=True).returncode

    def test_only_manual_single_territory_can_start(self):
        self.assertEqual({'workflow_dispatch'}, set(self.events))
        inputs = self.events['workflow_dispatch']['inputs']
        self.assertEqual(CHOICES, inputs['territory_id']['options'])
        self.assertEqual({'territory_id', 'reviewed_sha'}, set(inputs))
        self.assertTrue(inputs['reviewed_sha']['required'])
        for territory in CHOICES:
            with self.subTest(territory=territory):
                self.assertEqual(0, self.run_guard(territory, 'a' * 40))

    def test_matrix_unknown_or_injected_territory_blocks_before_production(self):
        for territory in ('Todos', 'madrid', '', 'andalucia; exit 0', '$(echo andalucia)'):
            with self.subTest(territory=territory):
                self.assertEqual(40, self.run_guard(territory, 'a' * 40))

    def test_missing_partial_uppercase_or_injected_sha_blocks(self):
        for sha in ('', 'main', 'a' * 39, 'a' * 41, 'A' * 40, '$(echo success)'):
            with self.subTest(sha=sha):
                self.assertEqual(41, self.run_guard('01 Andalucía', sha))

    def test_sha_from_another_commit_blocks(self):
        self.assertEqual(42, self.run_guard('01 Andalucía', 'b' * 40))

    def test_only_existing_territorial_producer_is_called_after_guard(self):
        jobs = self.workflow['jobs']
        self.assertEqual({'comprobar', 'preparar'}, set(jobs))
        call = jobs['preparar']
        self.assertEqual('comprobar', call['needs'])
        self.assertEqual('./.github/workflows/preparacion-fuentes.yml', call['uses'])
        self.assertNotIn('secrets', call)
        params = call['with']
        self.assertEqual('${{ github.sha }}', params['source_ref'])
        self.assertEqual('${{ inputs.territory_id }}', params['territory_id'])
        for key in ('data_edition', 'population_year', 'section_year'):
            self.assertEqual('2025', params[key])

    def test_reuse_recovery_and_persistence_are_not_dispatch_overrides(self):
        params = self.workflow['jobs']['preparar']['with']
        self.assertIs(False, params['persist_state'])
        self.assertIs(False, params['reutilizar_si_ya_preparada'])
        self.assertEqual('', params['recover_run_id'])
        self.assertEqual('', params['recover_artifact_sha256'])
        self.assertFalse(resolve_persist_state(params['persist_state']))
        self.assertEqual({'status': 'SUCCESS', 'reason': 'PERSISTENCE_NOT_REQUIRED'},
                         terminal_decision(preparation_result='success',
                                           registration_result='skipped', persist_state=False))
        self.assertEqual('FAILURE', terminal_decision(preparation_result='failure',
                         registration_result='skipped', persist_state=False)['status'])
        producer = yaml.safe_load((ROOT / '.github/workflows/preparacion-fuentes.yml').read_text())
        for job in ('registrar', 'generation_pending'):
            self.assertIn("needs.resolver.outputs.persist_state == 'true'", producer['jobs'][job]['if'])
        for key, level in producer['permissions'].items():
            self.assertEqual(level, self.workflow['permissions'][key])

    def test_fourteen_historical_receipts_and_five_canonical_blocks_remain(self):
        prior = ROOT / 'docs/AUDITORIAS/F04_F10_20261009/continuacion/evidencia-previa-reutilizada.json'
        rows = json.loads(prior.read_text())['rows']
        self.assertEqual(14, len(rows))
        for row in rows:
            with self.subTest(territory=row['territory_id']):
                _, receipt = validate_territorial_receipt(root_dir=ROOT,
                    territory=row['territory_id'], edition='2025')
                self.assertEqual(row['package_sha256'], receipt['package_sha256'])
                self.assertEqual(row['territorial_identity_sha256'], receipt['territorial_identity_sha256'])
                self.assertEqual('PASS', row['controls']['F03_effective_consumer'])
        for territory in TERRITORIES:
            with self.subTest(territory=territory), self.assertRaises(PreparedPairExecutionBlock):
                validate_territorial_receipt(root_dir=ROOT, territory=territory, edition='2025')


if __name__ == '__main__':
    unittest.main()
