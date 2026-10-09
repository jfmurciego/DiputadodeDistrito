#!/usr/bin/env python3
"""Pruebas de manifiesto público v1.0.0."""
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from herramientas.g10_public_product_manifest import main

class PublicProductManifest(unittest.TestCase):
 def test_manifiesto_declara_producto(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);source=root/"d.geojson";source.write_text(json.dumps({"type":"FeatureCollection","features":[{"type":"Feature","properties":{"district_id":1,"district_pop":10,"target":10,"relative_deviation":0,"municipality_names":"X"},"geometry":None}]}),encoding="utf-8")
   registry=root/"r.json";registry.write_text(json.dumps({"products":[{"id":"x","label":"X","expected_districts":1,"source_path":str(source),"viewer_path":"data/x.geojson","status":"PASS"}]}),encoding="utf-8");out=root/"o.json"
   import sys
   old=sys.argv;sys.argv=["x","--registry",str(registry),"--output",str(out)]
   try:self.assertEqual(main(),0)
   finally:sys.argv=old
   self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["products"][0]["fields"]["population"],"district_pop")
if __name__=="__main__":unittest.main()
