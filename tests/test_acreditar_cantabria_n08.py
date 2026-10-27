"""Versión1.0.0; fecha2026-10-12; nombre pruebas acreditación Cantabria.
Alcance diagnóstico aislado; estado candidato; origen N08 #251; sin predecesor.
Cambio pruebas de contraste y rechazo; motivo impedir falsa acreditación.
"""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import shapely
from herramientas.acreditar_cantabria_n08 import DOSSIER, PRODUCT, checked, classify_void, validate_sections


class AccreditationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((DOSSIER / 'RESULTADOS.json').read_bytes())
        cls.geo = json.loads(gzip.decompress((DOSSIER / 'GEOMETRIAS.json.gz').read_bytes()))
        cls.product = json.loads(gzip.decompress(PRODUCT.read_bytes()))

    def test_invariants_and_no_generation(self):
        expected = dict(sections=458, municipalities=102, population=593623, K=5, K_national=407, edges=1208, part_components=5, generation_authorized=False, physical_edges_created=0)
        self.assertEqual(self.result['invariants'], expected)
        self.assertEqual(self.result['districts_created'], 0)

    def test_unknown_part_population_not_zero(self):
        for p in self.result['parts']:
            if p['CUSEC'] == '3910101001':
                self.assertEqual(p['population_part'], 249)
            else:
                self.assertIsNone(p['population_part'])
                self.assertEqual(p['population_part_status'], 'NOT_EVIDENCED')
        self.assertEqual(sum({p['CUSEC']: p['population_section'] for p in self.result['parts'] if p['CUSEC'] != '3910101001'}.values()), 3382)

    def test_exact_original_void_identities_and_areas(self):
        self.assertEqual(len(self.geo['voids']), 28)
        expected = {r['boundary_sha256']: r['area_m2'] for r in self.product['enclosed_voids']}
        for v in self.geo['voids']:
            g = shapely.from_wkb(bytes.fromhex(v['wkb_hex']))
            self.assertEqual(hashlib.sha256(g.wkb).hexdigest(), v['wkb_sha256'])
            self.assertEqual(g.area, expected[v['wkb_sha256']])
        self.assertAlmostEqual(sum(v['area_m2'] for v in self.geo['voids']), 75426757.88657923)

    def test_each_void_contrasted_and_precision_is_not_policy(self):
        for v in self.result['voids']:
            self.assertTrue(v['official_municipal_matches'])
            self.assertEqual(len(v['uncovered_original_area_by_grid_m2']), 5)
            self.assertIsNone(v['population'])
        self.assertTrue(self.result['precision_policy'].startswith('NOT_APPROVED'))
        self.assertEqual(sum(v['classification'].startswith('MICRO') for v in self.result['voids']), 25)

    def test_no_fictitious_contact_islands_enclave_laredo(self):
        isolated = [p for p in self.result['parts'] if p['part_id'].endswith('p0000')]
        self.assertEqual(len(isolated), 4)
        for p in isolated:
            self.assertEqual(p['contacts'], [])
        laredo = next(p for p in isolated if p['CUSEC'] == '3903503001')
        self.assertGreater(laredo['distance_to_other_same_section_parts_m'], 78)
        self.assertEqual(laredo['ign_municipal_coverage_ratio_raw'], 0)

    def test_torre_name_is_external_correspondence_not_original_point(self):
        p = next(p for p in self.result['parts'] if p['part_id'] == '3907504011:p0000')
        self.assertEqual(p['official_named_points_inside'], [])
        self.assertTrue(any('Isla de la Torre' in m['names_inside_external_part'] and m['coverage_ratio_raw'] > .99 for m in p['external_part_matches']))

    def test_overlap_inventory_not_cause_of_large_voids(self):
        self.assertEqual(len(self.result['overlaps']), 30)
        self.assertAlmostEqual(sum(o['overlap_m2'] for o in self.result['overlaps']), .09629237443831391)
        for o in self.result['overlaps']:
            self.assertTrue(o['u'].startswith('39') and o['v'].startswith('39'))
            self.assertIn('0.0001', o['area_by_grid_m2'])

    def test_hash_rejects_foreign_source(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'source';p.write_bytes(b'2026')
            with self.assertRaises(ValueError):
                checked(p, hashlib.sha256(b'2025').hexdigest())

    def test_foreign_void_not_classified_by_fallback(self):
        with self.assertRaises(ValueError):
            classify_void('f' * 64)
        with self.assertRaises(ValueError):
            classify_void('1ea675806a11cc3a' + 'f' * 48)

    def test_duplicate_missing_foreign_population_sections_rejected(self):
        # Valid synthetic geometry binding isolates each negative route from unrelated corruption.
        polygon = shapely.box(0, 0, 1, 1)
        product = copy.deepcopy(self.product)
        for n in product['nodes']:
            n['geometry_sha256'] = hashlib.sha256(polygon.wkb).hexdigest()
        sections = [dict(CUSEC=n['CUSEC'], CUMUN=n['CUMUN'], pop=n['pop'], wkb_hex=polygon.wkb_hex) for n in product['nodes']]
        validate_sections(sections, product)
        cases = [(sections[:-1], 'Cobertura'), (sections[:-1] + [sections[0]], 'Cobertura'),
                 ([{**s, 'CUSEC': '4800000000'} if i == 0 else s for i,s in enumerate(sections)], 'Identidad CUSEC'),
                 ([{**s, 'pop': 0} if i == 0 else s for i,s in enumerate(sections)], 'población'),
                 ([{**s, 'wkb_hex': '00'} if i == 0 else s for i,s in enumerate(sections)], 'Geometría')]
        for mutant, message in cases:
            with self.assertRaisesRegex(ValueError, message):
                validate_sections(mutant, product)



if __name__ == '__main__':
    unittest.main()
