"""Versión 1.0.0; puerta N08 Congreso; 2026-10-12; candidato.
Pruebas de checkpoint, políticas fail-closed y contratos sintéticos.
Origen: nueva, sin predecesor.
"""
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / 'docs/ESTUDIOS/N08_CACERES_20261012'
SPEC = importlib.util.spec_from_file_location('caceres_preflight_tool', ROOT / 'herramientas/preflight_caceres_n08.py')
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


class CaceresN08PreflightTests(unittest.TestCase):
    def test_recorded_run_is_fail_closed_and_hashable(self):
        report = json.loads((DOSSIER / 'preflight/PREFLIGHT.json').read_text())
        checkpoint = json.loads((DOSSIER / 'preflight/CHECKPOINT.json').read_text())
        self.assertEqual((report['province'], report['inputs']['sections'], report['inputs']['population'], report['inputs']['physical_edges'], report['inputs']['k_approved']), ('10', 411, 388190, 1125, 3))
        self.assertFalse(report['generation_authorized'])
        self.assertFalse(report['real_partition_created'])
        self.assertEqual(report['districts_generated'], 0)
        self.assertEqual(checkpoint['preflight_sha256'], hashlib.sha256((DOSSIER / 'preflight/PREFLIGHT.json').read_bytes()).hexdigest())
        tool_hash = hashlib.sha256((ROOT / 'herramientas/preflight_caceres_n08.py').read_bytes()).hexdigest()
        self.assertEqual(report['tool_sha256'], tool_hash)
        self.assertEqual(checkpoint['tool_sha256'], tool_hash)
        self.assertFalse(checkpoint['generation_authorized'])

    def test_recorded_source_hashes_match_contract(self):
        report = json.loads((DOSSIER / 'preflight/PREFLIGHT.json').read_text())
        contract = json.loads((ROOT / 'territorios/congreso/contrato_congreso_2026.json').read_text())
        for role in ('geometry', 'population'):
            self.assertEqual(report['source_binding'][role]['edition'], 2025)
            self.assertEqual(report['source_binding'][role]['sha256'], contract['sources'][role]['sha256'])
        artifact = ROOT / 'docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto/unidades/10.json.gz'
        self.assertEqual(hashlib.sha256(artifact.read_bytes()).hexdigest(), report['topology_unit_sha256'])

    def test_pending_policies_never_open_technical_gate(self):
        # El expediente 2026-10-12 se ejecutó sobre contrato 0.3; conservarlo
        # para revisar su bloqueo histórico sin atribuirle reglas N08 posteriores.
        contract = json.loads((ROOT / 'legacy/n08_caceres_20261012/contrato_congreso_2026_v0_3.json').read_text())
        pending, values = TOOL._approved_policies(contract)
        self.assertTrue(pending)
        self.assertIsNone(values)
        passed_m05 = {'status': 'SYNTHETIC_CONTRACT_PASS_ONLY'}
        passed_m06 = {'status': 'SYNTHETIC_OUTPUT_AUDIT_PASS'}
        self.assertFalse(TOOL.report_gate_ready(pending, 'limits pending', passed_m05, passed_m06))
        self.assertFalse(TOOL.report_gate_ready({}, None, passed_m05, passed_m06,
                                                ['CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52']))
        self.assertFalse(TOOL.report_gate_ready({}, None, {'status': 'BLOCKED'}, passed_m06))
        self.assertFalse(TOOL.report_gate_ready({}, None, passed_m05, {'status': 'BLOCKED'}))
        self.assertFalse(json.loads((DOSSIER / 'preflight/PREFLIGHT.json').read_text())['generation_authorized'])

    def test_m06_fixture_is_parameterized_and_rejects_wrong_quota(self):
        from ddd_core.congreso_preflight_adapter import audit_synthetic_partition
        contract = json.loads((ROOT / 'territorios/congreso/contrato_congreso_2026.json').read_text())
        binding = {r: {'edition': 2025, 'sha256': contract['sources'][r]['sha256']} for r in ('geometry', 'population')}
        fixture = TOOL._synthetic_m06_contract(contract, binding, province='10', quota=3, population=388190)
        self.assertEqual(fixture['status'], 'SYNTHETIC_OUTPUT_AUDIT_PASS')
        self.assertFalse(fixture['policy_approved'])
        with self.assertRaisesRegex(ValueError, 'PARTITION_EXTERNAL_QUOTA_MISMATCH'):
            TOOL._synthetic_m06_contract(contract, binding, province='10', quota=2, population=388190)

    def test_m05_fixture_uses_actual_final_invariant_checker(self):
        contract = json.loads((ROOT / 'territorios/congreso/contrato_congreso_2026.json').read_text())
        binding = {r: {'edition': 2025, 'sha256': contract['sources'][r]['sha256']} for r in ('geometry', 'population')}
        fixture = TOOL._synthetic_m06_contract(contract, binding, province='10', quota=3, population=388190)
        result = TOOL._synthetic_m05_contract(fixture['_fixture_nodes'], fixture['_fixture_edges'], province='10')
        self.assertEqual(result['status'], 'SYNTHETIC_CONTRACT_PASS_ONLY')
        self.assertFalse(result['optimizer_executed'])

    def test_dossier_manifest(self):
        manifest = json.loads((DOSSIER / 'MANIFEST.json').read_text())
        report = json.loads((DOSSIER / 'preflight/PREFLIGHT.json').read_text())
        self.assertFalse(manifest['generation_authorized'])
        self.assertEqual(manifest['tool_sha256'], report['tool_sha256'])
        # El manifiesto histórico es inmutable. Las tres rutas que evolucionan
        # con N08 0.4 se comprueban contra copias idénticas del HEAD acreditado;
        # ninguna de las 26 entradas ni un SHA del manifiesto se reescribe.
        original = {
            'ddd_core/congreso_contract.py':
                'legacy/n08_caceres_20261012/congreso_contract_v1_1.py',
            'territorios/congreso/contrato_congreso_2026.json':
                'legacy/n08_caceres_20261012/contrato_congreso_2026_v0_3.json',
            'tests/test_preflight_caceres_n08.py':
                'legacy/n08_caceres_20261012/test_preflight_caceres_n08_v1.py',
        }
        for rel, record in manifest['files'].items():
            data = (ROOT / original.get(rel, rel)).read_bytes()
            self.assertEqual((len(data), hashlib.sha256(data).hexdigest()), (record['bytes'], record['sha256']))


if __name__ == '__main__':
    unittest.main()
