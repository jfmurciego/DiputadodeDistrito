"""Versión 0.1.0; pruebas interfaces Congreso; 2026-10-12; candidato.
Alcance diagnóstico; cambios: pruebas nuevas; motivo N08; origen nuevo.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from shapely.geometry import box
from ddd_core.congreso_preflight_adapter import (
    validate_physical_product, physical_components, structural_component_bound,
    engine_input_contract, audit_synthetic_partition,
)
from ddd_core.config import hard_limits
from ddd_core.m04_seed_engine import _atomic_population_necessary_conditions
from ddd_core.m05_population_repair import verify_partition_constraints

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'modulos' / name)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def sample():
    c = json.loads((ROOT / 'territorios/congreso/contrato_congreso_2026.json').read_text())
    binding = {kind: {key: c['sources'][kind][key] for key in ('edition', 'sha256')}
               for kind in ('geometry', 'population')}
    nodes = [{'id': ident, 'CPRO': '39', 'CUMUN': '39001', 'pop': pop,
              'geometry_sha256': 'a' * 64, 'source_geometry_sha256': binding['geometry']['sha256'],
              'physical_component': '39:3900101001'}
             for ident, pop in [('3900101001', 300000), ('3900101002', 293623)]]
    edges = [{'u': nodes[0]['id'], 'v': nodes[1]['id'], 'edge_type': 'geometric',
              'shared_border_m': 1.0, 'overlap_m2': 0, 'contact_sha256': 'b' * 64}]
    return c, nodes, edges, binding

def validate(sample):
    c, n, e, b = sample
    return validate_physical_product(c, n, e, b, require_national=False)

class CongressPreflightAdapterTests(unittest.TestCase):
    def test_source_binding_matches_accredited_manifest(self):
        contract, _, _, binding = sample()
        manifest = json.loads((ROOT / 'territorios/congreso/fuentes/ine_2025_2025/manifest.json').read_text())
        self.assertEqual(manifest['edition'], 2025)
        for kind in ('geometry', 'population'):
            self.assertEqual(binding[kind]['edition'], manifest['edition'])
            self.assertEqual(binding[kind]['sha256'], manifest['sources'][kind]['sha256'])
            self.assertEqual(contract['sources'][kind]['accreditation'], 'ACCREDITED')

    def test_diagnostic_output_preserves_authorization(self):
        data = sample()
        report = validate(data)
        self.assertTrue(report['population'] == 593623)
        self.assertTrue(report['quotas']['39'] == 5)
        self.assertTrue(report['generation_authorized'] is False)
        self.assertTrue(report['production_blockers'])
        self.assertTrue(engine_input_contract()['M04']['status'] == 'BLOCKED')

    def _negative_case(self, defect, reason):
        data = sample()
        c, n, e, b = data
        if defect == 'point': e[0]['shared_border_m'] = 0
        if defect == 'nan': e[0]['shared_border_m'] = float('nan')
        if defect == 'bridge': e[0]['edge_type'] = 'bridge'
        if defect == 'overlap': e[0]['overlap_m2'] = 0.001
        if defect == 'duplicate': e.append({**e[0], 'u': e[0]['v'], 'v': e[0]['u']})
        if defect == 'self': e[0]['v'] = e[0]['u']
        if defect == 'node_duplicate': n.append(copy.deepcopy(n[0]))
        if defect == 'source': b['geometry']['sha256'] = 'c' * 64
        if defect == 'edition': b['population']['edition'] = 2026
        if defect == 'authorize': c['accreditation']['generation_authorized'] = True
        if defect == 'component': n[1]['physical_component'] = 'other'
        if defect == 'quota': c['quotas_by_origin_unit'][38]['k'] = 4
        if defect == 'autonomous': c['execution_identity'] = 'aragon'
        with self.assertRaisesRegex(ValueError, reason): validate(data)

    def test_interprovincial_edge(self):
        data = sample()
        c, n, e, b = data
        n[1].update(id='3800101001', CPRO='38', CUMUN='38001')
        e[0]['v'] = n[1]['id']
        with self.assertRaisesRegex(ValueError, 'CROSS_PROVINCE'): validate(data)

    def test_quota_population_and_national_coverage(self):
        data = sample()
        data[1][0]['pop'] = 0
        with self.assertRaisesRegex(ValueError, 'N06_QUOTA_POPULATION'): validate(data)

    def test_partial_never_claims_national(self):
        data = sample()
        with self.assertRaisesRegex(ValueError, 'NATIONAL_COVERAGE'):
            validate_physical_product(*data)

    def test_components_deterministic_including_zero_population(self):
        n = [{'id': 'c'}, {'id': 'a'}, {'id': 'b'}]
        e = [{'u': 'b', 'v': 'a'}]
        self.assertTrue(physical_components(n, e) == physical_components(n[::-1], e[::-1]) == [['a', 'b'], ['c']])
        self.assertTrue(not structural_component_bound([120000, 0], 1)['necessary_condition'])
        self.assertTrue(not structural_component_bound([593623], 5)['feasibility_proven'])

    def test_real_m01_normalizer_m02_point_vs_line_and_overlap(self):
        m01 = module('01_preparar_base_territorial.py')
        self.assertTrue(m01.normalize_section_key('3900101001') == '3900101001')
        m02 = module('02_construir_adyacencias.py')
        a = box(0, 0, 1, 1)
        self.assertTrue(m02._relation_ok(a, box(1, 0, 2, 1), 'contact', 0.001, 0))
        self.assertTrue(not m02._relation_ok(a, box(1, 1, 2, 2), 'contact', 0.001, 0))
        self.assertTrue(not m02._relation_ok(a, box(0.5, 0, 1.5, 1), 'contact', 0.001, 0))

    def test_real_m03_preserves_admin_fields(self):
        import pandas as pd
        m03 = module('03_construir_grafo.py')
        nodes = m03.build_nodes(pd.DataFrame([{'CUSEC': '3900101001', 'POB_2025': 2,
                                  'CPRO': '39', 'CUMUN': '39001'}]),
                               'CUSEC', 'POB_2025', ('CPRO', 'CUMUN'))
        self.assertTrue(nodes == [{'id': '3900101001', 'pop': 2, 'CPRO': '39', 'CUMUN': '39001'}])
        self.assertTrue(m03.component_sets(['a', 'b', 'c'], {'a': {'b'}, 'b': {'a'}}) == [{'a', 'b'}, {'c'}])

    def test_real_m04_missing_limits_and_atomic_failure(self):
        with self.assertRaisesRegex(SystemExit, 'no declara'):
            hard_limits({}, k=5, total_pop=593623)
        ok, reason, _ = _atomic_population_necessary_conditions(
            ['a'], {'a': 593623}, k=5, floor=1, cap=600000)
        self.assertTrue(not ok and reason == 'K_EXCEEDS_ATOMIC_UNITS')

    def test_real_m05_rejects_noncontiguous_and_split_municipality(self):
        units = {u: {'population': 120000, 'province': '39', 'municipality_group': '39001:M'}
                 for u in ('a', 'b')}
        result = verify_partition_constraints({'a': 1, 'b': 1}, units, {'a': set(), 'b': set()}, floor=100000, cap=250000)
        self.assertTrue(result['reason'] == 'DISTRICT_CONTIGUITY')
        result = verify_partition_constraints({'a': 1, 'b': 2}, units, {'a': {'b'}, 'b': {'a'}}, floor=100000, cap=130000)
        self.assertTrue(result['reason'] == 'MUNICIPAL_INTEGRITY')
        units['b']['municipality_group'] = '39002:M'
        self.assertTrue(verify_partition_constraints({'a': 1, 'b': 2}, units, {'a': {'b'}, 'b': {'a'}}, floor=100000, cap=130000)['hard_limits_met'])

    def test_real_m06_administrative_traceability_and_field_contract(self):
        import pandas as pd
        m06 = module('06_consolidar_distritos.py')
        self.assertTrue(m06.joined_unique(pd.Series(['39002', '39001', '39001', None, ' '])) == '39001 | 39002')
        self.assertTrue(engine_input_contract()['M06']['required_input_fields'] == ['CUSEC', 'district_id', 'POB_2025'])

    def test_k_decision_cannot_change_independently(self):
        data = sample()
        data[0]['k_decision']['total'] = 350
        with self.assertRaisesRegex(ValueError, 'N06_DECISION_INVALID'): validate(data)

    def test_m05_structural_validity_does_not_accredit_population(self):
        units = {'a': {'population': 200000, 'province': '39'}}
        result = verify_partition_constraints({'a': 1}, units, {'a': set()}, floor=100000, cap=130000)
        self.assertTrue(result['valid'] is True)
        self.assertTrue(result['hard_limits_met'] is False)

    def test_reject_point(self):
        self._negative_case('point', 'POINT_OR_INVALID_CONTACT')

    def test_reject_nan(self):
        self._negative_case('nan', 'POINT_OR_INVALID_CONTACT')

    def test_reject_bridge(self):
        self._negative_case('bridge', 'NON_PHYSICAL')

    def test_reject_overlap(self):
        self._negative_case('overlap', 'NON_PHYSICAL')

    def test_reject_duplicate(self):
        self._negative_case('duplicate', 'EDGE_DUPLICATE')

    def test_reject_self(self):
        self._negative_case('self', 'EDGE_ENDPOINT')

    def test_reject_node_duplicate(self):
        self._negative_case('node_duplicate', 'CUSEC_DUPLICATE')

    def test_reject_source(self):
        self._negative_case('source', 'SOURCE_BINDING')

    def test_reject_edition(self):
        self._negative_case('edition', 'SOURCE_BINDING')

    def test_reject_authorize(self):
        self._negative_case('authorize', 'GENERATION')

    def test_reject_component(self):
        self._negative_case('component', 'COMPONENT_LABEL')

    def test_reject_quota(self):
        self._negative_case('quota', 'N06_QUOTAS')

    def test_reject_autonomous(self):
        self._negative_case('autonomous', 'CONGRESS')

class CongressSyntheticOutputAuditTests(unittest.TestCase):
    def setUp(self):
        self.contract, _, _, self.binding = sample()
        self.nodes = [{'id': '3900101' + str(i).zfill(3), 'CPRO': '39', 'CUMUN': '39001',
                       'pop': 120000 if i < 5 else 113623,
                       'geometry_sha256': 'a' * 64,
                       'source_geometry_sha256': self.binding['geometry']['sha256'],
                       'physical_component': '3900101001',
                       'physical_part_components': ['3900101001:p0000']}
                      for i in range(1, 6)]
        self.edges = [{'u': self.nodes[i]['id'], 'v': self.nodes[i + 1]['id'],
                       'edge_type': 'geometric', 'shared_border_m': 1., 'overlap_m2': 0,
                       'contact_sha256': 'b' * 64} for i in range(4)]
        self.rows = [{'id': n['id'], 'pop': n['pop'], 'district_id': 'synthetic:' + str(i)}
                     for i, n in enumerate(self.nodes)]
        self.policy = {'minimum_unit': 'section', 'municipal_policy': 'splittable',
                       'population_floor': 110000, 'population_cap': 130000}

    def audit(self):
        return audit_synthetic_partition(self.contract, self.nodes, self.edges, self.binding,
                                         self.rows, self.policy, synthetic_fixture=True)

    def test_positive_output_never_institutionally_admitted(self):
        result = self.audit()
        self.assertEqual(result['status'], 'SYNTHETIC_OUTPUT_AUDIT_PASS')
        self.assertFalse(result['generation_authorized'])
        self.assertFalse(result['institutional_policy_approved'])
        self.assertTrue(result['production_blockers'])
        self.assertEqual(result['population'], 593623)
        self.assertEqual(len(result['district_populations']), 5)

    def test_empty_universe_rejected(self):
        self.nodes, self.edges, self.rows = [], [], []
        with self.assertRaisesRegex(ValueError, 'PARTITION_EMPTY_UNIVERSE'):
            self.audit()

    def test_requires_synthetic_fixture_flag(self):
        with self.assertRaisesRegex(ValueError, 'SYNTHETIC_FIXTURE_REQUIRED'):
            audit_synthetic_partition(self.contract, self.nodes, self.edges, self.binding,
                                      self.rows, self.policy)

    def test_closes_m05_valid_true_but_population_invalid(self):
        self.nodes[0]['pop'] = self.rows[0]['pop'] = 200000
        self.nodes[1]['pop'] = self.rows[1]['pop'] = 40000
        units = {n['id']: {'population': n['pop'], 'province': '39'} for n in self.nodes}
        state = {r['id']: r['district_id'] for r in self.rows}
        adjacency = {n['id']: set() for n in self.nodes}
        real = verify_partition_constraints(state, units, adjacency, floor=110000, cap=130000)
        self.assertTrue(real['valid'])
        self.assertFalse(real['hard_limits_met'])
        with self.assertRaisesRegex(ValueError, 'PARTITION_HARD_POPULATION_LIMITS'):
            self.audit()

    def test_closes_expected_k_derived_from_present_labels(self):
        for row in self.rows:
            row['district_id'] = 'synthetic:one'
        self.policy.update(population_floor=1, population_cap=600000)
        units = {n['id']: {'population': n['pop'], 'province': '39'} for n in self.nodes}
        state = {r['id']: r['district_id'] for r in self.rows}
        adjacency = {n['id']: set() for n in self.nodes}
        for e in self.edges:
            adjacency[e['u']].add(e['v'])
            adjacency[e['v']].add(e['u'])
        real = verify_partition_constraints(state, units, adjacency, floor=1, cap=600000)
        self.assertTrue(real['valid'])
        self.assertTrue(real['hard_limits_met'])
        with self.assertRaisesRegex(ValueError, 'PARTITION_EXTERNAL_QUOTA_MISMATCH'):
            self.audit()

    def test_exact_coverage_no_missing_duplicate_or_extra(self):
        original = copy.deepcopy(self.rows)
        for rows in (original[:-1], original + [original[0]], original + [{'id': '3900101999', 'pop': 1, 'district_id': 'x'}]):
            with self.subTest(rows=len(rows)):
                self.rows = rows
                with self.assertRaisesRegex(ValueError, 'PARTITION_COVERAGE'):
                    self.audit()

    def test_population_conservation(self):
        self.rows[0]['pop'] += 1
        with self.assertRaisesRegex(ValueError, 'PARTITION_POPULATION_NOT_CONSERVED'):
            self.audit()

    def test_explicit_finite_limits_and_minimum_unit(self):
        original = copy.deepcopy(self.policy)
        cases = [{}, {**original, 'population_cap': float('inf')},
                 {**original, 'population_floor': 0}, {**original, 'minimum_unit': 'municipality'}]
        for policy in cases:
            with self.subTest(policy=policy):
                self.policy = policy
                with self.assertRaises(ValueError):
                    self.audit()

    def test_municipal_policy_not_implicitly_indivisible(self):
        self.policy['municipal_policy'] = 'indivisible'
        with self.assertRaisesRegex(ValueError, 'PARTITION_MUNICIPAL_INTEGRITY'):
            self.audit()
        self.policy['municipal_policy'] = None
        with self.assertRaisesRegex(ValueError, 'MUNICIPAL_POLICY_REQUIRED'):
            self.audit()

    def test_missing_or_multipart_physical_evidence(self):
        for parts in (None, [], ['island:a', 'island:b']):
            with self.subTest(parts=parts):
                self.nodes[0]['physical_part_components'] = parts
                with self.assertRaisesRegex(ValueError, 'PHYSICAL_PART_CONNECTIVITY_NOT_EVIDENCED'):
                    self.audit()

    def test_partition_contiguity_uses_original_graph(self):
        self.rows[2]['district_id'] = self.rows[0]['district_id']
        self.policy.update(population_floor=1, population_cap=600000)
        with self.assertRaisesRegex(ValueError, 'PARTITION_DISTRICT_CONTIGUITY'):
            self.audit()


if __name__ == "__main__":
    unittest.main()
