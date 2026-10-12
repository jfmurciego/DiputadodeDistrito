"""VERSIÓN 1.0.0; 2026-10-12; límites necesarios; nuevo, sin generación."""
import unittest
from ddd_core.congreso_feasibility import evaluate_option


def product(populations, k, municipal_population=None, code='39'):
    nodes = [{'id': str(i), 'pop': p} for i,p in enumerate(populations)]
    return {'summary': {'CPRO': code, 'k': k, 'population': sum(populations),
                        'multipart_sections_spanning_physical_components': []},
            'physical_components': [{'id': n['id'], 'population': n['pop'], 'sections':[n['id']]} for n in nodes],
            'municipalities': [{'CUMUN':'39001', 'population': municipal_population or sum(populations)}], 'nodes': nodes}


class NecessaryLimitsTests(unittest.TestCase):
    def test_zero_component_coverage_cannot_disappear(self):
        p = product([0, 200000], 2)
        r = evaluate_option(p, '1/5')
        self.assertTrue(r['arithmetic_impossibility_section_graph'])
        self.assertEqual(r['necessary_component_intervals'][0]['minimum_districts'],1)
        self.assertFalse(r['feasibility_proven'])

    def test_rounding_mean_does_not_invent_provincial_exception(self):
        p = product([160738],1,code='05')
        self.assertFalse(evaluate_option(p,'3/20',basis='reference_120000')['ordinary_mean_within_limits'])
        self.assertTrue(evaluate_option(p,'3/20')['ordinary_mean_within_limits'])
        self.assertFalse(evaluate_option(p,'3/20')['exception'])

    def test_municipality_large_requires_split_but_is_not_feasibility_proof(self):
        p = product([118000]*5,5)
        r = evaluate_option(p,'3/20')
        self.assertTrue(r['municipal_indivisibility_impossibility_by_size_or_count'])
        self.assertFalse(r['feasibility_proven'])
        self.assertFalse(r['institutionally_approved'])

    def test_explicit_population_exception_does_not_remove_physical_component_bound(self):
        p = product([10000,80000],1,code='42')
        r = evaluate_option(p,'3/20')
        self.assertTrue(r['exception'])
        self.assertTrue(r['arithmetic_impossibility_section_graph'])
        self.assertFalse(r['generation_authorized'])


if __name__ == '__main__': unittest.main()
