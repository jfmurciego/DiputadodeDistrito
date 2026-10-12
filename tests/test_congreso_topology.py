"""VERSIÓN 1.0.0; FECHA 2026-10-12; N08 contactos y artefactos diagnósticos.
ALCANCE: regresión automática; ESTADO candidato; ORIGEN nuevo.
CAMBIOS/MOTIVO: prevenir contactos ficticios y componentes omitidos.
"""
import copy
import gzip
import hashlib
import json
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import box, MultiPolygon
from ddd_core.congreso_topology import contacts, analyze_unit, canonical_components, digest
from ddd_core.congreso_preflight_adapter import validate_physical_product

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / 'docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto'


class GeometryContactTests(unittest.TestCase):
    def test_point_is_not_edge_and_overlapping_border_is_not_edge(self):
        geometries = [box(0, 0, 1, 1), box(1, 0, 2, 1), box(2, 1, 3, 2), box(0, 0, .5, 1)]
        rows = contacts(geometries, ['a', 'b', 'c', 'd'])
        lookup = {(r['u'], r['v']): r for r in rows}
        self.assertEqual(lookup['a', 'b']['kind'], 'linear')
        self.assertEqual(lookup['b', 'c']['kind'], 'point')
        self.assertEqual(lookup['a', 'd']['kind'], 'overlap')
        self.assertGreater(lookup['a', 'd']['shared_border_m'], 0)
        edges = [r for r in rows if r['kind'] == 'linear']
        self.assertNotIn(('b', 'c'), [(r['u'], r['v']) for r in edges])
        self.assertNotIn(('a', 'd'), [(r['u'], r['v']) for r in edges])

    def test_multipart_does_not_invent_physical_passage_or_population(self):
        f = gpd.GeoDataFrame({'CUSEC': ['3900101001', '3900101002'], 'CPRO': ['39', '39'],
                              'CUMUN': ['39001', '39001'], 'POB_2025': [200, 300]},
                             geometry=[MultiPolygon([box(0, 0, 1, 1), box(5, 0, 6, 1)]), box(1, 0, 2, 1)], crs=25830)
        p = analyze_unit(f, 1, 'a'*64, precision_grids=())
        self.assertEqual(p['summary']['section_graph_components'], 1)
        self.assertEqual(p['summary']['physical_part_components'], 2)
        self.assertEqual(len(p['nodes'][0]['physical_part_components']), 2)
        self.assertTrue(all(c['population_exact'] is None for c in p['polygon_part_components']))
        self.assertIn('PHYSICAL_PART_COMPONENTS_EXCEED_K_WITHOUT_GEOGRAPHICAL_EXCEPTIONS',
                      p['summary']['structural_impossibilities_under_strict_physical_contiguity'])
        self.assertFalse(p['summary']['generation_authorized'])
        self.assertEqual(p['municipalities'][0]['physical_part_components'], 2)

    def test_rounding_only_sensitivity_never_changes_original_graph(self):
        f = gpd.GeoDataFrame({'CUSEC': ['3900101001', '3900101002'], 'CPRO': ['39', '39'],
                              'CUMUN': ['39001', '39002'], 'POB_2025': [200, 300]},
                             geometry=[box(0, 0, 1, 1), box(1.001, 0, 2, 1)], crs=25830)
        p = analyze_unit(f, 2, 'a'*64, precision_grids=(.01,))
        self.assertEqual(p['edges'], [])
        self.assertEqual(p['summary']['physical_part_components'], 2)
        self.assertEqual(len(p['sensitivity'][-1]['new_edges_not_accredited']), 1)
        self.assertEqual(p['operational_graph'], 'IDENTICAL_TO_PHYSICAL_SECTION_GRAPH_NO_BRIDGES')

    def test_components_deterministic_including_zero_population_isolate(self):
        edges = [{'u': 'a', 'v': 'b'}]
        self.assertEqual(canonical_components(['c', 'b', 'a'], edges), [['a', 'b'], ['c']])
        self.assertEqual(canonical_components(['b', 'a', 'c'], list(reversed(edges))), [['a', 'b'], ['c']])


class NationalArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The deliverable is committed alongside tests, not a downloaded fixture.
        cls.manifest = json.loads((PRODUCT / 'manifest.json').read_text())
        cls.contract = json.loads((ROOT / 'territorios/congreso/contrato_congreso_2026.json').read_text())
        cls.products = [json.loads(gzip.decompress((PRODUCT / f'unidades/{i:02d}.json.gz').read_bytes())) for i in range(1, 53)]
        cls.nodes = [n for p in cls.products for n in p['nodes']]
        cls.edges = [e for p in cls.products for e in p['edges']]

    def test_manifest_identity_artifact_hashes_and_no_sources_changed(self):
        m = copy.deepcopy(self.manifest); identity = m.pop('identity_sha256')
        self.assertEqual(digest(m), identity)
        for name, record in self.manifest['artifacts'].items():
            data = (PRODUCT/name).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), record['sha256'], name)
        for kind in ('geometry', 'population'):
            self.assertEqual(self.manifest['evidence']['source_binding'][kind]['sha256'], self.contract['sources'][kind]['sha256'])
        self.assertEqual(hashlib.sha256((ROOT/'territorios/congreso/fuentes/ine_2025_2025/manifest.json').read_bytes()).hexdigest(),
                         self.manifest['evidence']['source_manifest_sha256'])

    def test_full_national_contract_coverage_population_and_quotas(self):
        report = validate_physical_product(self.contract, self.nodes, self.edges, self.manifest['evidence']['source_binding'])
        self.assertEqual(report['nodes'], 36554)
        self.assertEqual(report['population'], 49128297)
        self.assertEqual(sum(report['quotas'].values()), 407)
        self.assertFalse(report['generation_authorized'])
        self.assertFalse(self.contract['accreditation']['generation_authorized'])

    def test_every_physical_edge_valid_in_records_no_cross_province(self):
        nodes = {n['id']: n for n in self.nodes}; seen = set()
        for edge in self.edges:
            pair = edge['u'], edge['v']
            self.assertLess(*pair); self.assertNotIn(pair, seen); seen.add(pair)
            self.assertEqual(nodes[edge['u']]['CPRO'], nodes[edge['v']]['CPRO'])
            self.assertEqual(edge['overlap_m2'], 0)
            self.assertGreater(edge['shared_border_m'], 0)
            self.assertEqual(edge['edge_type'], 'geometric')
        self.assertEqual(len(seen), self.manifest['edges'])
        self.assertEqual(self.manifest['interprovincial_edges'], 0)

    def test_components_and_parts_cover_nodes_exactly(self):
        for product in self.products:
            expected = canonical_components([n['id'] for n in product['nodes']], list(reversed(product['edges'])))
            self.assertEqual(expected, [c['sections'] for c in product['physical_components']])
            self.assertEqual(sum(c['population'] for c in product['physical_components']), product['summary']['population'])
            parts = [part for c in product['polygon_part_components'] for part in c['parts']]
            self.assertEqual(len(parts), len(set(parts)))
            self.assertEqual(len(parts), product['summary']['polygon_parts'])

    def test_invalid_edition_hash_and_unaccredited_bridge_rejected(self):
        binding = copy.deepcopy(self.manifest['evidence']['source_binding'])
        binding['geometry']['edition'] = 2026
        with self.assertRaisesRegex(ValueError, 'SOURCE_BINDING'):
            validate_physical_product(self.contract, self.nodes, self.edges, binding)
        binding['geometry']['edition'] = 2025; binding['geometry']['sha256'] = 'c'*64
        with self.assertRaisesRegex(ValueError, 'SOURCE_BINDING'):
            validate_physical_product(self.contract, self.nodes, self.edges, binding)
        edges = copy.deepcopy(self.edges[:1]); edges[0]['edge_type'] = 'bridge'
        with self.assertRaisesRegex(ValueError, 'NON_PHYSICAL'):
            validate_physical_product(self.contract, self.nodes, edges, self.manifest['evidence']['source_binding'])

    def test_cantabria_and_three_gates_never_infer_ready(self):
        p = self.products[38]
        self.assertEqual((p['summary']['CPRO'], p['summary']['population'], p['summary']['k']), ('39', 593623, 5))
        self.assertEqual(self.manifest['gates']['A_diagnostic_coverage'], 'PASS')
        self.assertNotEqual(self.manifest['gates']['B_first_pilot_feasibility'], 'PASS')
        self.assertEqual(self.manifest['gates']['C_productive_authorization'], 'BLOCKED')
        self.assertFalse(self.manifest['generation_authorized'])


if __name__ == '__main__': unittest.main()
