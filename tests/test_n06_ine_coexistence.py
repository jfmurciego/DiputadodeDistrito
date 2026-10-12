"""Versión 1.0.0; 2026-10-12; coexistencia N06/PR241; nuevo, sin generación."""
import copy
import csv
import json
import hashlib
import unittest
from collections import Counter
from pathlib import Path
from ddd_core.congreso_contract import validate_congress_identity, production_blockers, validate_production_admission

BASE = 'f87445f5d75a53cee17cd3bcc711854318b795ff'
CONTRACT = Path('territorios/congreso/contrato_congreso_2026.json')
SOURCES = Path('territorios/congreso/fuentes/ine_2025_2025')

class Coexistence(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(CONTRACT.read_text())
    def test_quotas_from_accredited_population(self):
        with (SOURCES/'poblacion_por_seccion_2025.csv').open() as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 36554)
        self.assertEqual(len({r['CUSEC'] for r in rows}),36554)
        populations = Counter()
        for row in rows: populations[row['CPRO']] += int(row['POB_2025'])
        self.assertEqual(sum(populations.values()),49128297)
        expected = {code:max(1,(population+60000)//120000) for code,population in populations.items()}
        quotas = {row['code']:row['k'] for row in self.c['quotas_by_origin_unit']}
        self.assertEqual(quotas,expected)
        self.assertEqual(len(quotas),52)
        self.assertEqual(sum(quotas.values()),407)
        for code in ('42','51','52'):self.assertEqual(quotas[code],1)
    def test_pr241_sources_bytes_and_metadata_unchanged(self):
        base=json.loads(Path('legacy/territorios/congreso/contrato_congreso_2026_pre_n06_integracion.json').read_text())
        self.assertEqual(self.c['sources'],base['sources'])
        expected = {'territorios/congreso/fuentes/ine_2025_2025/poblacion_por_seccion_2025.csv': 'c4a22fc47f7542da0b3e1cef65ea59dc555442eda23f7f74ba4f4db7d6c4a988', 'territorios/congreso/fuentes/ine_2025_2025/manifest.json': 'f99e1690071b6383d90094b35fe024865d5bc75ef95983014452d1d25dbadc37', 'territorios/congreso/fuentes/ine_2025_2025/crosswalk_n07_2025.csv': '0ceb2cab2b7843a9ab042e5130a66762ffa958983ced91220e18d2bb38f14d54'}
        for name,digest in expected.items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),digest)
    def test_all_aliases_and_conflicts(self):
        c=copy.deepcopy(self.c)
        for canonical,alias in [('origin_units','circumscriptions'),('quotas_by_origin_unit','quotas_by_circumscription')]:
            c[alias]=copy.deepcopy(c[canonical])
            self.assertEqual(validate_congress_identity(c),validate_congress_identity(self.c))
            bad=copy.deepcopy(c);bad[alias]=[]
            with self.assertRaisesRegex(ValueError,'ALIAS_CONFLICT'):validate_congress_identity(bad)
        c['origin_unit_codes']=[f'{i:02d}' for i in range(1,53)]
        c['circumscription_codes']=c['origin_unit_codes'][:]
        validate_congress_identity(c)
        c['circumscription_codes']=[]
        with self.assertRaisesRegex(ValueError,'ALIAS_CONFLICT'):validate_congress_identity(c)
    def test_approval_cannot_admit_production(self):
        self.assertFalse(self.c['accreditation']['generation_authorized'])
        self.assertFalse(validate_congress_identity(self.c)['generation_authorized'])
        blockers=production_blockers(self.c)
        self.assertNotIn('OWNER_DECISION_PENDING',blockers)
        self.assertNotIn('CONGRESS_K_UNDECIDED_OR_INVALID',blockers)
        self.assertIn('DECISION_CONTIGUITY_PENDING',blockers)
        self.assertIn('DECISION_MUNICIPAL_INDIVISIBILITY_PENDING',blockers)
        with self.assertRaisesRegex(ValueError,'PRODUCTION_BLOCKED'):validate_production_admission(self.c)
