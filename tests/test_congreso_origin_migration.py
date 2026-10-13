"""Version 1.0.0, 2026-10-12; Congress origin migration regression; new."""
import copy
import json
from pathlib import Path
import unittest
from ddd_core.congreso_contract import validate_congress_identity, production_blockers

class Migration(unittest.TestCase):
    def setUp(self):
        self.c=json.loads(Path('territorios/congreso/contrato_congreso_2026.json').read_text())
    def test_canonical_and_legacy_equivalence(self):
        c=copy.deepcopy(self.c)
        c['circumscriptions']=c.pop('origin_units')
        c['quotas_by_circumscription']=c.pop('quotas_by_origin_unit')
        self.assertEqual(validate_congress_identity(c),validate_congress_identity(self.c))
        v=validate_congress_identity(self.c)
        self.assertEqual(v['origin_unit_count'],52)
        self.assertEqual(v['electoral_district_count'],407)
        self.assertFalse(v['generation_authorized'])
    def test_alias_conflict_and_wrong_version_rejected(self):
        c=copy.deepcopy(self.c); c['circumscriptions']=[]
        with self.assertRaisesRegex(ValueError,'ALIAS_CONFLICT'): validate_congress_identity(c)
        c=copy.deepcopy(self.c); c['schema']='ddd.congress-contract/0.1'
        with self.assertRaisesRegex(ValueError,'REQUIRE_SCHEMA'): validate_congress_identity(c)
    def test_k_decision_never_clears_sources_or_topology(self):
        b=production_blockers(self.c)
        self.assertNotIn('OWNER_DECISION_PENDING',b)
        self.assertNotIn('CONGRESS_K_UNDECIDED_OR_INVALID',b)
        self.assertNotIn('SOURCE_POPULATION_MISSING',b)
        self.assertIn('CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52',b)
        self.assertFalse(self.c['accreditation']['generation_authorized'])
    def test_bad_quota_and_contamination_fail_closed(self):
        c=copy.deepcopy(self.c); c['quotas_by_origin_unit'][0]['k']+=1
        self.assertIn('CIRCUMSCRIPTION_QUOTAS_DO_NOT_SUM_TO_K',production_blockers(c))
        c=copy.deepcopy(self.c); c['origin_units'][0]['regional_k']=3
        with self.assertRaises(ValueError): validate_congress_identity(c)
