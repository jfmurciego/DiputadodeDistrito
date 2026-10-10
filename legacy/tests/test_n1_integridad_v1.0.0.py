"""Version 1.0.0; 2026-10-10; N1 C1/C2/C3 functional negatives; review pending.
Scope: frozen local material only; origin: new; reason: separate-review findings.
"""
import copy,gzip,hashlib,json,tempfile,unittest
from pathlib import Path
from herramientas.evaluar_alternativas_nacionales import validate_model
from herramientas.inventariar_cartografia_historica import incorporate,read_json_verified
ROOT=Path(__file__).resolve().parents[1];FOLDER=ROOT/'docs/ESTUDIOS/cartografia_nacional_20261008'
class N1Integrity(unittest.TestCase):
 def test_altered_indicators_rejected_without_altering_vector(self):
  baseline=json.loads((ROOT/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json').read_text())
  for index in range(5):
   for field,value in [('within_constitutional_size_reference',not baseline['alternatives'][index]['within_constitutional_size_reference']),('equals_congress_size_reference',True),('minimum_reference_violations',['99']),('population_total',1),('city_fixed_one_reference_violations',['51']),('zero_district_populated_provinces',['01'])]:
    model=copy.deepcopy(baseline);model['alternatives'][index][field]=value
    with self.subTest(rule=index,field=field),self.assertRaisesRegex(ValueError,'INDICATOR_INCONSISTENT'):validate_model(model)
 def test_same_missing_attributes_cannot_accredit_material_end_to_end(self):
  for change in ('null','absent','blank','null_geometry'):
   with self.subTest(change=change),tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);found=[]
    for index,record in enumerate(json.loads((FOLDER/'inventario.json').read_text())['files']):
     raw=gzip.decompress((FOLDER/record['archived_path']).read_bytes())
     if record['name'] in {'map.geojson','spain-districts-selected.json'}:
      data=json.loads(raw);feature=data['features'][0]
      if change=='null_geometry':feature['geometry']=None
      elif change=='absent':feature['properties'].pop('map_iteration')
      else:feature['properties']['map_iteration']=None if change=='null' else ' '
      raw=json.dumps(data).encode()
     path=root/str(index)/record['name'];path.parent.mkdir();path.write_bytes(raw);found.append(str(path))
    search=root/'search.json';search.write_text(json.dumps({'found':found}));incorporate(search,root/'output')
    evidence=json.loads((root/'output/equivalencia_archivos.json').read_text());self.assertEqual(evidence['interpretation'],'INSUFFICIENT_EVIDENCE')
 def test_analytical_input_hash_verified_before_json_consumption(self):
  with tempfile.TemporaryDirectory() as temporary:
   f=Path(temporary)/'model.json';raw=b'{"value":42}';f.write_bytes(raw);digest=hashlib.sha256(raw).hexdigest()
   self.assertEqual(read_json_verified(f,digest),{'value':42})
   f.write_bytes(b'not valid JSON and altered bytes')
   with self.assertRaisesRegex(ValueError,'ANALYTICAL_INPUT_HASH_MISMATCH'):read_json_verified(f,digest)
if __name__=='__main__':unittest.main()
