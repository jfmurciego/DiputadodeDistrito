"""Contrato F10 v1.0.1 (2026-10-11), candidato local; origen: #179.

Cambios: regresión de Extremadura separa receipt auténtico del linaje activo del producto.
Motivo: prevenir sustitución implícita; predecesor: legacy/tests/test_f10_receipt_contract_v1.0.0.py.
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
from herramientas.resolver_ejecucion_completa import build_plan
from tests.test_prepared_source_pair_execution import build_source_fixture

from tests._raiz_congelada import frozen_root  # noqa: E402

# Estado congelado en aee8215e: los recuentos y receipts exactos no dependen de las ejecuciones
# completas posteriores, que reescriben catálogo y productos en main.
ROOT = frozen_root()
EVIDENCE = ROOT / 'docs/AUDITORIAS/F04_F10_20261009'
TERRITORIES = ('andalucia', 'comunidad_valenciana', 'extremadura', 'aragon', 'castilla_y_leon')

# Sólo para demostrar la regresión con el contenido exacto de la base preservada.
if os.environ.get('DDD_F10_BASELINE') == '1':
    spec = importlib.util.spec_from_file_location(
        'f10_baseline', ROOT / 'legacy/herramientas/consumir_par_fuentes_legislatura_pre_F10.py')
    consumer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(consumer)


class F10ReceiptContractTests(unittest.TestCase):
    def test_extremadura_f10_receipt_is_authentic_evidence_without_replacing_product_lineage(self):
        receipt_rel = (
            'territorios/extremadura/evidencia/fuentes_territoriales/2025/'
            '70d7a964b7b837555ce03d5874c5fa04a74a80d5d724947b89fa9107684fd084/'
            '38091144559/receipt.json'
        )
        receipt = json.loads((ROOT / receipt_rel).read_text(encoding='utf-8'))
        registry = json.loads(
            (ROOT / 'docs/AUDITORIAS/CIERRE_REAL_FUENTES_20261011/registro-autenticos.json')
            .read_text(encoding='utf-8')
        )
        entry = next(row for row in registry['rows'] if row['territory_id'] == 'extremadura')
        self.assertEqual(entry['receipt_path'], receipt_rel)
        self.assertFalse(entry['promoted'])
        self.assertEqual(entry['promotion_status'],
                         'AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED')
        validation = entry['effective_validation']
        self.assertEqual(validation['decision'], 'READY')
        self.assertEqual(validation['territory_id'], receipt['territory_id'])
        self.assertEqual(validation['edition'], receipt['edition'])
        self.assertEqual(validation['territorial_identity_sha256'], receipt['territorial_identity_sha256'])
        self.assertEqual(validation['compatibility_report_sha256'], receipt['compatibility_report_sha256'])
        self.assertEqual(validation['compatibility_identity_sha256'], receipt['compatibility_identity_sha256'])
        self.assertEqual(
            {key: receipt[key] for key in (
                'schema', 'kind', 'territory_id', 'edition', 'run_id', 'artifact_name',
                'artifact_sha256', 'package_sha256', 'source_commit',
                'territorial_identity_sha256', 'compatibility_report_sha256',
                'compatibility_identity_sha256',
            )},
            {
                'schema': 'ddd.territorial-source-receipt/1.0',
                'kind': 'territorial_source',
                'territory_id': 'extremadura',
                'edition': '2025',
                'run_id': 38091144559,
                'artifact_name': 'ddd-source-package-extremadura-2025-38091144559',
                'artifact_sha256': 'b4241708cbc7eb1fcf3dd7b6298152392731975106bbddaf6d8ae03bc3fcd8dc',
                'package_sha256': '5f55db978522cc3fe5c32cbe25e61005a3e30823acab1ff10b3fe2a824f21b0a',
                'source_commit': '776006e62ebd80ab20a55b186c3778bce76e9f19',
                'territorial_identity_sha256': '70d7a964b7b837555ce03d5874c5fa04a74a80d5d724947b89fa9107684fd084',
                'compatibility_report_sha256': 'a45c3ff9833d9898c56f177180731fd07b52e6dadeb3d3e937a510eaa1664346',
                'compatibility_identity_sha256': 'cccf94fe04269dc88a5b187bd99ab90c68010619f9b1e6c25319f4b4820d1959',
            },
        )

        plan = build_plan(
            territory='Extremadura', edition='2025', execution_mode='reuse',
            catalog=ROOT / 'configuracion/catalogo_preparacion.yaml', root_dir=ROOT,
            optimization_algorithm='Canónico', force_selected_algorithm=True,
        )
        self.assertFalse(plan['run_prepare_territorial'])
        self.assertFalse(plan['run_generate'])
        self.assertEqual(plan['existing']['territorial_product']['run_id'], 40656175842)
        self.assertEqual(plan['existing']['territorial_source']['run_id'], 40656175842)

    def test_local_derived_receipts_never_accredit_effective_bytes(self):
        for territory in TERRITORIES:
            with self.subTest(territory=territory), self.assertRaisesRegex(
                consumer.PreparedPairExecutionBlock, 'schema de receipt'):
                consumer.validate_effective_territorial_package(
                    root_dir=ROOT,
                    territorial_receipt_path=EVIDENCE / territory / 'derived-receipt-v3.json',
                    territorial_package=EVIDENCE / territory / 'candidato-v3')

    def test_extremadura_independent_receipt_consumes_without_replacing_product_source(self):
        row, receipt = consumer.validate_territorial_receipt(
            root_dir=ROOT, territory='extremadura', edition='2025')
        self.assertEqual(38091144559, receipt['run_id'])
        self.assertEqual(40656175842, row['preparation_evidence']['run_id'])
        self.assertEqual(
            'AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED',
            row['independent_source_evidence']['status'])
        self.assertFalse(row['independent_source_evidence']['promoted'])
        product = json.loads((ROOT / 'territorios/extremadura/evidencia/catalogo/territorial_product_2025.json').read_text())
        self.assertEqual(40656175842, product['run_id'])

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
