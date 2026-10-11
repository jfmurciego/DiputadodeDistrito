#!/usr/bin/env python3
"""Versión 1.0.0; fecha 2026-10-11; N03/N04/N05/N06 diagnóstico local.
Estado candidato CI_PENDIENTE; nuevo sin predecesor.
Motivo: conservar diagnóstico verificable sin reparar ni adoptar K.
"""
import gzip
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from herramientas.comparar_cartografia_nacional import inspect_geojson
from herramientas.evaluar_alternativas_nacionales import evaluate
from herramientas.inventariar_cartografia_historica import read_json_verified
from shapely.geometry import shape, Polygon
from shapely.validation import explain_validity


def diagnose(output):
    folder=ROOT/'docs/ESTUDIOS/cartografia_nacional_20261008'
    descriptor=json.loads((folder/'descriptor_historico_map.json').read_text())
    path=folder/'inputs/a2c8f630bd84_map.geojson.gz'
    raw=gzip.decompress(path.read_bytes())
    if hashlib.sha256(raw).hexdigest()!=descriptor['file_sha256']:
        raise ValueError('HISTORICAL_HASH_MISMATCH')
    inventory,_,_=inspect_geojson(path,descriptor)
    features=json.loads(raw)['features']; feature=features[44]
    geom=shape(feature['geometry'])
    hole_tests=[]
    polygons=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom]
    for i,polygon in enumerate(polygons):
        shell=Polygon(polygon.exterior)
        for j,ring in enumerate(polygon.interiors):
            hole=Polygon(ring)
            hole_tests.append({'component':i,'hole':j,'covered_by_own_shell':shell.covers(hole),
                               'hole_area_coordinate_units':hole.area,'bounds':list(hole.bounds)})
    report={'schema':'ddd.national-continuity-evidence/1.0','version':'1.0.0',
            'N03':{'status':'BLOCKED','source_sha256':descriptor['file_sha256'],
                   'geometry_edition':descriptor['geometry_edition'], 'population_edition':descriptor['population_edition'],
                   'provenance':descriptor['provenance'],
                   'reason':'No accredited source/edition pair; archived bytes prove identity only'},
            'N04':{'status':'PASS_DIAGNOSTIC','feature_index':44,'id':str(feature['properties'][descriptor['id_field']]),
                   'province':str(feature['properties'][descriptor['province_field']]),
                   'valid':geom.is_valid,'reason':explain_validity(geom),'hole_tests':hole_tests,
                   'original_sha256':hashlib.sha256(raw).hexdigest(),
                   'treatment':'Preserve original; reject as admissible geometry. Repair/replacement requires accredited source.',
                   'repair_performed':False,'inventory_errors':inventory['errors']}}
    model=read_json_verified(ROOT/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json','c183f71e7a433eaaff77456d82a13f8afbc3f1fd2ec08e73ca3fce371d7d7ee4')
    counts=json.loads((folder/'recuentos_historicos.json').read_text())
    alternatives=evaluate(model,counts)
    report['N05']={'status':'PASS_DIAGNOSTIC','alternatives':alternatives}
    report['N06']={'status':'WAIT_OWNER','decision_adopted':False,
                   'restrictions':['Provincial barriers plus floor 96000 incompatible with positive K in Soria, Ceuta, Melilla',
                                   'K 407,409,435 exceed constitutional size reference 400',
                                   'K 383 leaves Soria, Ceuta, Melilla without representation',
                                   'Target 120000, legal reference 350 and provincial minima cannot all be imposed without institutional decision'],
                   'scope':'Arithmetic model only; no district geometries or current legal determination'}
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    (output/'evidence.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    return report
if __name__=='__main__':
    result=diagnose(sys.argv[1]);print(json.dumps({k:v['status'] for k,v in result.items() if k.startswith('N')}))
