"""Contrato F10 v1.0.0 (2026-10-10), candidato local; origen: #179.

Cambios: regresiones de acreditación efectiva; motivo: evitar READY local.
Alcance: receipts y artefactos conservados; predecesor: ninguno.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from herramientas import consumir_par_fuentes_legislatura as consumer
from herramientas.compatibilidad_poblacion_seccionado import REPORT_NAME, validate_compatibility_package
from tests.test_prepared_source_pair_execution import build_source_fixture

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'docs/AUDITORIAS/F04_F10_20261009'
TERRITORIES = ('andalucia', 'comunidad_valenciana', 'extremadura', 'aragon', 'castilla_y_leon')

# Sólo para demostrar la regresión con el contenido exacto de la base preservada.
if os.environ.get('DDD_F10_BASELINE') == '1':
    spec = importlib.util.spec_from_file_location(
        'f10_baseline', ROOT / 'legacy/herramientas/consumir_par_fuentes_legislatura_pre_F10.py')
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)


class F10ReceiptContractTests(unittest.TestCase):
    def test_local_derived_receipts_never_accredit_effective_bytes(self):
        for territory in TERRITORIES:
            with self.subTest(territory=territory), self.assertRaisesRegex(
                consumer.PreparedPairExecutionBlock, 'schema de receipt'):
                consumer.validate_effective_territorial_package(
                    root_dir=ROOT,
                    territorial_receipt_path=EVIDENCE / territory / 'derived-receipt-v3.json',
                    territorial_package=EVIDENCE / territory / 'candidato-v3')

    def test_retagging_and_borrowing_historical_run_cannot_accredit_candidate(self):
        for territory in TERRITORIES:
            candidate = json.loads((EVIDENCE / territory / 'derived-receipt-v3.json').read_text())
            original = json.loads((EVIDENCE / territory / 'recovery-receipt.json').read_text())
            # Intento deliberadamente ilegítimo; nunca se escribe en evidencia durable.
            candidate.update({key: original[key] for key in
                              ('run_id', 'artifact_name', 'artifact_sha256', 'source_commit')})
            candidate.update(schema='ddd.territorial-source-receipt/1.0', kind='territorial_source',
                             compatibility_report_member=REPORT_NAME)
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / 'forged.json'
                path.write_text(json.dumps(candidate))
                with self.subTest(territory=territory), self.assertRaises(
                    consumer.PreparedPairExecutionBlock):
                    consumer.validate_effective_territorial_package(
                        root_dir=ROOT, territorial_receipt_path=path,
                        territorial_package=EVIDENCE / territory / 'candidato-v3')

    def test_original_artifact_digests_and_missing_report(self):
        metadata = json.loads((EVIDENCE / 'artifact-metadata.json').read_text())
        for item in metadata:
            territory = item['territory']
            artifact = EVIDENCE / 'originales' / f"artifact-{item['id']}.zip"
            with self.subTest(territory=territory):
                self.assertEqual(item['digest'], 'sha256:' + hashlib.sha256(artifact.read_bytes()).hexdigest())
                with zipfile.ZipFile(artifact) as outer:
                    self.assertIsNone(outer.testzip())
                    manifest = json.loads(outer.read('manifest.json'))
                    package = outer.read('prepared_sources.zip')
                    self.assertEqual(manifest['sha256'], hashlib.sha256(package).hexdigest())
                    with zipfile.ZipFile(io.BytesIO(package)) as inner:
                        self.assertIsNone(inner.testzip())
                        self.assertNotIn(REPORT_NAME, inner.namelist())
                report, report_sha, reasons = validate_compatibility_package(
                    EVIDENCE / territory / 'original', territory_id=territory,
                    edition='2025', population_year=2025, section_year=2025)
                self.assertEqual({}, report)
                self.assertEqual('', report_sha)
                self.assertTrue(any('histórico no reutilizable' in reason for reason in reasons))

    def test_wrong_receipt_kind_and_report_member_block(self):
        for key, value, reason in (
            ('kind', 'local_derivation', 'kind de receipt'),
            ('compatibility_report_member', 'invented.json', 'miembro de compatibilidad'),
        ):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                path, _, receipt = build_source_fixture(root, include_pair=False, include_electoral=False)
                receipt[key] = value
                path.write_text(json.dumps(receipt))
                with self.subTest(key=key), self.assertRaisesRegex(consumer.PreparedPairExecutionBlock, reason):
                    consumer.validate_effective_territorial_package(
                        root_dir=root, territorial_receipt_path=path, territorial_package=root / 'absent')

    def test_effective_receipt_must_equal_durable_receipt_before_reading_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _, _, receipt = build_source_fixture(root, include_pair=False, include_electoral=False)
            receipt['run_id'] += 1
            path = root / 'substitute.json'
            path.write_text(json.dumps(receipt))
            with mock.patch.object(consumer, 'validate_prepared_package') as validate_bytes:
                with self.assertRaisesRegex(consumer.PreparedPairExecutionBlock, 'acreditación durable'):
                    consumer.validate_effective_territorial_package(
                        root_dir=root, territorial_receipt_path=path, territorial_package=root / 'absent')
                validate_bytes.assert_not_called()

    def test_absent_durable_receipt_blocks_even_with_self_consistent_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, _, receipt = build_source_fixture(root, include_pair=False, include_electoral=False)
            alternate = root / 'alternate.json'
            alternate.write_text(json.dumps(receipt))
            path.unlink()
            with self.assertRaisesRegex(consumer.PreparedPairExecutionBlock, 'no disponible'):
                consumer.validate_effective_territorial_package(
                    root_dir=root, territorial_receipt_path=alternate, territorial_package=root / 'absent')


if __name__ == '__main__':
    unittest.main()
