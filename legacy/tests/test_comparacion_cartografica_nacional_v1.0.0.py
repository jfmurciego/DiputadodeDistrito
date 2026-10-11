"""VERSIÓN: 1.0.0; NOMBRE: comparación cartográfica fail-closed; FECHA: 2026-10-08.
ALCANCE: fixtures geométricos; ESTADO: CI_PENDIENTE; CAMBIOS: regresiones de admisión y métricas.
MOTIVO: no producir correspondencias sobre entradas no acreditadas; ORIGEN: nuevo, sin predecesor.
"""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from herramientas.comparar_cartografia_nacional import compare_maps, inspect_geojson


def rectangle(x0, x1, y0=0, y1=10):
    return {"type": "Polygon", "coordinates": [[[3000000+x0,2000000+y0],[3000000+x1,2000000+y0],[3000000+x1,2000000+y1],[3000000+x0,2000000+y1],[3000000+x0,2000000+y0]]]}


def feature(key, geometry=None, population=100, province="01"):
    return {"type":"Feature", "properties":{"id":key,"population":population,"province":province},"geometry":geometry or rectangle(0,10)}


class CartographicComparison(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)

    def fixture(self, features, year, name):
        path = Path(self.temp.name) / name
        path.write_text(json.dumps({"type":"FeatureCollection","crs":{"type":"name","properties":{"name":"EPSG:3035"}},"features":features}))
        descriptor = {"id_field":"id","province_field":"province","population_field":"population",
                      "geometry_edition":year,"population_edition":year,"file_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                      "scope":"synthetic_scope", "unit_kind":"districts", "provenance":{"accredited":True,"evidence":["synthetic_fixture_not_normative"]},
                      "stable_identity_accredited":True,"identity_namespace":"synthetic_namespace"}
        return path, descriptor

    def compare(self, old, new):
        return compare_maps(old[0],old[1],new[0],new[1])

    def test_identical_geometry_population_delta_and_identity(self):
        old=self.fixture([feature("a")],2022,"old.json"); new=self.fixture([feature("a",population=120)],2025,"new.json")
        result=self.compare(old,new)
        self.assertEqual(result['status'],'COMPARABLE')
        self.assertEqual(result['conserved_identities'],['a'])
        self.assertEqual(result['population_differences']['stable_identity_deltas'],{'a':'20'})
        self.assertAlmostEqual(result['pairs'][0]['jaccard'],1)
        self.assertEqual(result['coverage']['symmetric_difference_m2'],0)

    def test_renumbering_is_not_identity_conservation_without_accreditation(self):
        old=self.fixture([feature("a")],2022,"old.json");new=self.fixture([feature("b")],2025,"new.json")
        new[1]['stable_identity_accredited']=False
        result=self.compare(old,new)
        self.assertIsNone(result['conserved_identities'])
        self.assertTrue(result['pairs'][0]['equivalent_geometry_within_epsilon'])
        self.assertFalse(result['pairs'][0]['same_identifier'])

    def test_shift_overlap_and_coverage_known_analytically(self):
        old=self.fixture([feature('a',rectangle(0,10))],2022,'old.json');new=self.fixture([feature('a',rectangle(5,15))],2025,'new.json')
        result=self.compare(old,new)
        self.assertAlmostEqual(result['pairs'][0]['intersection_m2'],50)
        self.assertAlmostEqual(result['pairs'][0]['jaccard'],1/3)
        self.assertAlmostEqual(result['coverage']['old_covered_by_new'],0.5)
        self.assertAlmostEqual(result['coverage']['symmetric_difference_m2'],100)
        self.assertEqual(result['pairs'][0]['boundary_change_cause'],'UNACCREDITED')

    def test_split_does_not_force_one_to_one_mapping(self):
        old=self.fixture([feature('a',rectangle(0,20))],2022,'old.json')
        new=self.fixture([feature('b',rectangle(0,10)),feature('c',rectangle(10,20))],2025,'new.json')
        result=self.compare(old,new)
        self.assertEqual(len(result['pairs']),2)
        self.assertAlmostEqual(result['coverage']['old_covered_by_new'],1)
        self.assertEqual([p['old_coverage'] for p in result['pairs']],[0.5,0.5])

    def test_missing_identity_and_duplicate_identity_fail_closed(self):
        for features in ([feature(None)],[feature('a'),feature('a',rectangle(10,20))]):
            old=self.fixture(features,2022,'old.json');new=self.fixture([feature('a')],2025,'new.json')
            result=self.compare(old,new)
            self.assertEqual(result['status'],'NOT_COMPARABLE');self.assertIsNone(result['pairs'])

    def test_edition_unknown_incompatible_and_hash_false(self):
        for field,value in [('geometry_edition',None),('geometry_edition',2025),('population_edition',True),('file_sha256','0'*64)]:
            old=self.fixture([feature('a')],2022,'old.json');new=self.fixture([feature('a')],2025,'new.json')
            old[1][field]=value
            result=self.compare(old,new)
            self.assertEqual(result['status'],'NOT_COMPARABLE');self.assertIsNone(result['coverage'])

    def test_invalid_bowtie_and_hole_outside_shell(self):
        invalid={'type':'Polygon','coordinates':[[[0,0],[10,10],[0,10],[10,0],[0,0]]]}
        hole={'type':'Polygon','coordinates':rectangle(0,10)['coordinates']+rectangle(20,21)['coordinates']}
        for geom in (invalid,hole):
            old=self.fixture([feature('a',geom)],2022,'old.json');new=self.fixture([feature('a')],2025,'new.json')
            result=self.compare(old,new)
            self.assertEqual(result['status'],'NOT_COMPARABLE')
            self.assertIn('GEOMETRY_INVALID',result['input_reports'][0]['errors'][0]['error'])

    def test_discontinuity_is_diagnostic_or_blocked_by_explicit_contract(self):
        multi={'type':'MultiPolygon','coordinates':[rectangle(0,10)['coordinates'],rectangle(20,30)['coordinates']]}
        path,descriptor=self.fixture([feature('a',multi)],2022,'old.json')
        report,_,_=inspect_geojson(path,descriptor)
        self.assertEqual(report['status'],'VALID_GEOMETRY_INVENTORY')
        self.assertEqual(report['disconnected_features'][0]['components'],2)
        descriptor['require_connected']=True
        report,_,_=inspect_geojson(path,descriptor)
        self.assertEqual(report['status'],'BLOCKED_INVALID_INPUT')

    def test_point_contact_is_not_positive_area_correspondence(self):
        old=self.fixture([feature('a',rectangle(0,10))],2022,'old.json');new=self.fixture([feature('b',rectangle(10,20))],2025,'new.json')
        self.assertEqual(self.compare(old,new)['pairs'],[])

    def test_internal_overlapping_districts_block(self):
        old=self.fixture([feature('a',rectangle(0,10)),feature('b',rectangle(5,15))],2022,'old.json')
        new=self.fixture([feature('a')],2025,'new.json')
        result=self.compare(old,new)
        self.assertEqual(result['status'],'NOT_COMPARABLE');self.assertIsNone(result['pairs'])

    def test_geographic_unit_scope_and_crs_incompatible(self):
        old=self.fixture([feature('a')],2022,'old.json');new=self.fixture([feature('a')],2025,'new.json')
        new[1]['unit_kind']='census_sections'
        self.assertIn('GEOGRAPHIC_UNIT_INCOMPATIBLE',self.compare(old,new)['blockers'])
        old[1]['crs']='EPSG:4326'
        with self.assertRaisesRegex(ValueError,'CRS_CONTRADICTION'):
            self.compare(old,new)

    def test_permutation_determinism(self):
        features=[feature('b',rectangle(10,20)),feature('a',rectangle(0,10))]
        old=self.fixture(features,2022,'old.json');new=self.fixture(features,2025,'new.json')
        first=self.compare(old,new)
        swapped=self.fixture(list(reversed(features)),2025,'swapped.json')
        second=self.compare(old,swapped)
        self.assertEqual(first['pairs'],second['pairs'])
        self.assertEqual(first['coverage'],second['coverage'])

    def test_different_crs_equivalent_geometry_uses_metric_projection(self):
        from pyproj import Transformer
        from shapely.geometry import shape,mapping
        from shapely.ops import transform
        old=self.fixture([feature('a')],2022,'old.json')
        geom=mapping(transform(Transformer.from_crs('EPSG:3035','EPSG:4326',always_xy=True).transform,shape(rectangle(0,10))))
        new=self.fixture([feature('a',geom)],2025,'new.json')
        payload=json.loads(new[0].read_text());payload['crs']['properties']['name']='EPSG:4326'
        new[0].write_text(json.dumps(payload));new[1]['file_sha256']=hashlib.sha256(new[0].read_bytes()).hexdigest()
        result=self.compare(old,new)
        self.assertEqual(result['status'],'COMPARABLE')
        self.assertAlmostEqual(result['pairs'][0]['intersection_m2'],100,places=3)

    def test_provenance_must_be_explicitly_accredited(self):
        for evidence in [[],[''],[1]]:
            old=self.fixture([feature('a')],2022,'old.json');new=self.fixture([feature('a')],2025,'new.json')
            old[1]['provenance']['evidence']=evidence
            self.assertIn('PROVENANCE_NOT_ACCREDITED',self.compare(old,new)['blockers'])
        old[1]['provenance']={'accredited':'true','evidence':['fixture']}
        self.assertIn('PROVENANCE_NOT_ACCREDITED',self.compare(old,new)['blockers'])


if __name__=='__main__':
    unittest.main()
