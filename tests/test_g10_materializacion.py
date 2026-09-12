#!/usr/bin/env python3
"""Pruebas G10 para materialización sin cálculos territoriales."""
from __future__ import annotations
import hashlib,json,tempfile,unittest
from pathlib import Path
from herramientas.g10_materializar_checkpoints import materialize,plan
class Materializacion(unittest.TestCase):
 def test_m05_exige_grafo_y_semillas_y_copia(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/"cache").mkdir();(root/"old").mkdir()
   graph=root/"cache/graph.json";graph.write_text("graph");seed=root/"old/seed.zip";seed.write_text("seed")
   def manifest(path,product):
    path.write_text(json.dumps({"products":[{"path":str(product.relative_to(root)),"bytes":product.stat().st_size,"sha256":hashlib.sha256(product.read_bytes()).hexdigest()}]}))
   m3=root/"m3.json";m4=root/"m4.json";manifest(m3,graph);manifest(m4,seed)
   index={"territories":[{"territory":"aragon","release_status":"CERTIFIED","source_run":"old","checkpoints":[{"stage_id":"TERRITORY_GRAPH","status":"CANONICAL_VERIFIED_LEGACY","products_manifest":"m3.json"},{"stage_id":"DISTRICT_FORMATION","status":"CANONICAL_VERIFIED_LEGACY","products_manifest":"m4.json"}]}]}
   job=plan(index,"aragon","DISTRICT_BALANCING");self.assertEqual([x["stage_id"] for x in job["checkpoints"]],["TERRITORY_GRAPH","DISTRICT_FORMATION"])
   report=materialize(job,root=root,cache=root/"hydrated_cache",run=root/"hydrated_run")
   self.assertEqual(len(report["artifacts"]),2);self.assertTrue((root/"hydrated_cache/graph.json").is_file());self.assertTrue((root/"hydrated_run/seed.zip").is_file())
 def test_bloqueado_se_rechaza(self):
  with self.assertRaises(ValueError):plan({"territories":[{"territory":"extremadura","release_status":"EXPERIMENTAL_BLOCKED","checkpoints":[]}]},"extremadura","DISTRICT_FORMATION")
if __name__=="__main__":unittest.main()
