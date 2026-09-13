#!/usr/bin/env python3
"""Pruebas de manifiesto público v1.1.0."""
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from herramientas.g10_public_product_manifest import main,validate_product

class PublicProductManifest(unittest.TestCase):
 def test_manifiesto_declara_producto(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);source=root/"d.geojson";source.write_text(json.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{"district_id":1,"district_pop":10,"target":10,"relative_deviation":0,"municipality_names":"X"},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[0,0]]]}}]}),encoding="utf-8")
   registry=root/"r.json";registry.write_text(json.dumps({"products":[{"id":"x","label":"X","expected_districts":1,"source_path":str(source),"viewer_path":"data/x.geojson","status":"PASS"}]}),encoding="utf-8");out=root/"o.json"
   import sys
   old=sys.argv;sys.argv=["x","--registry",str(registry),"--output",str(out)]
   try:self.assertEqual(main(),0)
   finally:sys.argv=old
   self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["products"][0]["fields"]["population"],"district_pop")
 def test_rechaza_identidad_duplicada_y_geometria_invalida(self):
  spec={"id":"x","expected_districts":2}
  duplicated={"type":"FeatureCollection","features":[
   {"properties":{"district_id":1},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[0,0]]]}},
   {"properties":{"district_id":1},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[0,0]]]}}
  ]}
  with self.assertRaisesRegex(ValueError,"duplicado"): validate_product(spec,duplicated)
  invalid={"type":"FeatureCollection","features":[
   {"properties":{"district_id":1},"geometry":None},
   {"properties":{"district_id":2},"geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[0,0]]]}}
  ]}
  with self.assertRaisesRegex(ValueError,"Geometría"): validate_product(spec,invalid)
if __name__=="__main__":unittest.main()
