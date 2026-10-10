"""Versión 1.0.0; 2026-10-08; candidato local; pruebas de recuperación.

Alcance: almacén explícito; cambios: pruebas nuevas; motivo: integridad/offline.
Origen: 4e5e3be53364874d0e056ade64d64ab6471b28b7; predecesor: ninguno.
Los casos con datos se ejecutan con DDD_LOCAL_STORE explícito; nunca descargan.
"""
import copy
import hashlib
import json
import os
import shutil
import socket
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from herramientas.almacen_fuentes_local import (
    LocalSourceError, consume, inspect_zip, recover, sha256, validate_artifact,
)


class ZipSafetyTests(unittest.TestCase):
    def test_traversal_links_and_duplicates(self):
        for name, mode, duplicate in [('../escape', 0, False),
                ('/escape', 0, False), ('a\\b', 0, False),
                ('link', 0o120777, False), ('same', 0, True)]:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'bad.zip'
                with zipfile.ZipFile(path, 'w') as z:
                    info = zipfile.ZipInfo(name)
                    info.external_attr = mode << 16
                    z.writestr(info, 'payload')
                    if duplicate:
                        z.writestr(name, 'second')
                with zipfile.ZipFile(path) as z, self.assertRaises(LocalSourceError):
                    inspect_zip(z)


@unittest.skipUnless(os.environ.get('DDD_LOCAL_STORE'), 'requiere almacén explícito')
class PersistedSourceTests(unittest.TestCase):
    def setUp(self):
        self.original = Path(os.environ['DDD_LOCAL_STORE']).resolve()
        self.manifest = json.loads((self.original / 'recovery-manifest.json').read_text())
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.store = self.root / 'store'
        self.store.mkdir()
        self.rows = [r for r in self.manifest['rows'] if
                     r['expected']['territory_id'] in ('melilla', 'la_rioja')]
        self.assertEqual(len(self.rows), 2)
        for row in self.rows:
            for field in ('artifact_path', 'receipt_path'):
                source = Path(row[field])
                target = self.store / source.relative_to(self.original)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                row[field] = str(target)
        self.manifest['rows'] = self.rows
        self.save()

    def save(self):
        (self.store / 'recovery-manifest.json').write_text(json.dumps(self.manifest))

    def read(self, row=None, **overrides):
        row = row or self.rows[0]
        e = row['expected']
        kwargs = {k: e[k] for k in ('territory_id', 'edition',
                   'territorial_identity_sha256', 'package_sha256')}
        kwargs.update(overrides)
        return consume(self.store, destination=self.root / 'output', **kwargs)

    def test_two_territories_offline_and_originals_unchanged(self):
        before = {p: sha256(p) for p in self.original.rglob('*') if p.is_file()}
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('red prohibida')):
            for row in self.rows:
                result = self.read(row)
                self.assertEqual(sha256(result / 'prepared_sources.zip'),
                                 row['expected']['package_sha256'])
                shutil.rmtree(result)
        self.assertEqual(before, {p: sha256(p) for p in before})

    def test_wrong_digest(self):
        path = Path(self.rows[0]['artifact_path'])
        with path.open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaisesRegex(LocalSourceError, 'tamaño artifact'):
            self.read()

    def test_same_size_wrong_sha(self):
        path = Path(self.rows[0]['artifact_path'])
        raw = bytearray(path.read_bytes())
        raw[-1] ^= 1
        path.write_bytes(raw)
        with self.assertRaisesRegex(LocalSourceError, 'SHA artifact'):
            self.read()

    def test_identity_and_edition_exact(self):
        for kwargs in ({'territory_id': 'ceuta'}, {'edition': '2024'},
                       {'territorial_identity_sha256': '0' * 64},
                       {'package_sha256': '0' * 64}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(LocalSourceError, 'identidad exacta'):
                self.read(**kwargs)

    def test_contradictory_identity_and_receipt(self):
        self.rows[0]['expected']['territorial_identity_sha256'] = '0' * 64
        self.save()
        with self.assertRaisesRegex(LocalSourceError, 'receipt contradictorio'):
            self.read()

    def test_recomputed_identity_rejects_forged_receipt(self):
        row = self.rows[0]
        row['expected']['territorial_identity_sha256'] = '0' * 64
        receipt = Path(row['receipt_path'])
        value = json.loads(receipt.read_text())
        value['territorial_identity_sha256'] = '0' * 64
        raw = json.dumps(value).encode()
        digest = hashlib.sha256(raw).hexdigest()
        target = self.store / 'receipts' / (digest + '.json')
        target.write_bytes(raw)
        row.update(receipt_path=str(target), receipt_sha256=digest)
        self.save()
        with self.assertRaisesRegex(LocalSourceError, 'identidad territorial contradictoria'):
            self.read()

    def test_incompatible_edition_in_artifact(self):
        row = self.rows[0]
        expected = copy.deepcopy(row['expected'])
        expected['edition'] = '2024'
        receipt = json.loads(Path(row['receipt_path']).read_text())
        receipt['edition'] = '2024'
        from herramientas.identidad_fuentes_legislatura import territorial_identity
        expected['territorial_identity_sha256'] = territorial_identity(**{k:expected[k] for k in
            ('territory_id','edition','population_year','section_year','package_sha256',
             'compatibility_identity_sha256')})['territorial_identity_sha256']
        receipt['territorial_identity_sha256'] = expected['territorial_identity_sha256']
        with self.assertRaisesRegex(LocalSourceError, 'manifest incompatible: edition'):
            validate_artifact(Path(row['artifact_path']), expected, row['origin'],
                              receipt, self.root / 'invalid')

    def test_missing_ambiguous_and_unverified(self):
        self.manifest['rows'].append(copy.deepcopy(self.rows[0]))
        self.save()
        with self.assertRaisesRegex(LocalSourceError, 'ambigua'):
            self.read()
        self.manifest['rows'].pop()
        self.rows[0]['status'] = 'PENDING'
        self.save()
        with self.assertRaisesRegex(LocalSourceError, 'no verificado'):
            self.read()
        self.rows[0]['status'] = 'RECOVERED_VERIFIED'
        self.save()
        Path(self.rows[0]['artifact_path']).unlink()
        with self.assertRaisesRegex(LocalSourceError, 'artifact ausente'):
            self.read()

    def test_receipt_corruption(self):
        Path(self.rows[0]['receipt_path']).write_text('{}')
        with self.assertRaisesRegex(LocalSourceError, 'SHA receipt'):
            self.read()

    def test_import_promotion_and_conflicting_object(self):
        inventory = self.root / 'inventory.json'
        inventory.write_text(json.dumps({'rows': [{
            'territory_id': r['expected']['territory_id'], 'expected': r['expected'],
            'observation': {'result': {'structuredContent': {'artifacts': [r['origin']]}}}
        } for r in self.rows]}))
        downloads = self.root / 'downloads'
        downloads.mkdir()
        for row in self.rows:
            shutil.copyfile(row['artifact_path'], downloads /
                ('ddd-' + row['expected']['territory_id'] + '-original.zip'))
        target = self.root / 'imported'
        result = recover(inventory, downloads, target, Path.cwd())
        self.assertEqual([r['status'] for r in result['rows']],
                         ['RECOVERED_VERIFIED', 'RECOVERED_VERIFIED'])
        originals = {p: sha256(p) for p in target.rglob('*') if p.name != 'recovery-manifest.json' and p.is_file()}
        result = recover(inventory, downloads, target, Path.cwd())
        self.assertEqual(originals, {p: sha256(p) for p in originals})
        for download in downloads.iterdir():
            download.unlink()
        result = recover(inventory, downloads, target, Path.cwd())
        self.assertEqual([r['status'] for r in result['rows']],
                         ['RECOVERED_VERIFIED', 'RECOVERED_VERIFIED'])
        with patch('herramientas.almacen_fuentes_local.validate_artifact',
                   side_effect=KeyboardInterrupt), self.assertRaises(KeyboardInterrupt):
            recover(inventory, downloads, target, Path.cwd())
        preserved = json.loads((target / 'recovery-manifest.json').read_text())
        self.assertEqual(preserved['rows'], result['rows'])
        for row in self.rows:
            shutil.copyfile(row['artifact_path'], downloads /
                ('ddd-' + row['expected']['territory_id'] + '-original.zip'))
        conflict = Path(result['rows'][0]['artifact_path'])
        conflict.write_bytes(b'conflict-preserve')
        result = recover(inventory, downloads, target, Path.cwd())
        self.assertEqual(result['rows'][0]['status'], 'RECOVERED_INVALID')
        self.assertIn('objeto existente contradictorio', result['rows'][0]['error'])
        self.assertEqual(conflict.read_bytes(), b'conflict-preserve')
        self.assertEqual(result['rows'][1]['status'], 'RECOVERED_VERIFIED')
        (downloads / ('ddd-' + result['rows'][0]['expected']['territory_id'] + '-original.zip')).unlink()
        result = recover(inventory, downloads, self.root / 'missing-import', Path.cwd())
        self.assertEqual(result['rows'][0]['status'], 'UNAVAILABLE')
        self.assertEqual(result['rows'][1]['status'], 'RECOVERED_VERIFIED')


if __name__ == '__main__':
    unittest.main()
