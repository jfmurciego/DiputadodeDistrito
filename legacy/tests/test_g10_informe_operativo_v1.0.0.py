#!/usr/bin/env python3
"""Pruebas del informe operativo G10 v1.0.0."""
from __future__ import annotations
import json,tempfile,unittest
from pathlib import Path
from herramientas.g10_informe_operativo import build,main

class InformeOperativoG10(unittest.TestCase):
 def factual(self): return {"phase":"Fase 1","status":"CLOSED","territories":{"aragon":{"status":"PASS","districts":67},"extremadura":{"status":"EXPERIMENTAL_BLOCKED","promotion":False,"districts":65}}}
 def test_sin_bloqueo_no_ordena_recalculo(self):
  report=build({"records":[{"territory":"aragon","task_id":"e","status":"SUCCESS"}]},self.factual());self.assertEqual(report["next_reengagement"]["kind"],"WAIT_FOR_MATERIAL_CHANGE");self.assertFalse(report["territories"][1]["promotion"])
 def test_bloqueo_aisla_tarea(self):
  report=build({"records":[{"territory":"aragon","task_id":"ok","status":"SUCCESS"},{"territory":"extremadura","task_id":"x","status":"REQUIRES_AGENT"}]},self.factual());self.assertEqual(report["next_reengagement"]["tasks"],["x"])
 def test_cli_escribe_dos_salidas(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);state=root/"s.json";factual=root/"f.json";out=root/"o.json";md=root/"o.md;";state.write_text("{\"records\":[]}",encoding="utf-8");factual.write_text(json.dumps(self.factual()),encoding="utf-8")
   import sys
   old=sys.argv;sys.argv=["x","--state",str(state),"--factual",str(factual),"--output-json",str(out),"--output-md",str(md)]
   try:self.assertEqual(main(),0)
   finally:sys.argv=old
   self.assertTrue(out.is_file());self.assertIn("Estado operativo G10",md.read_text(encoding="utf-8"))
if __name__=="__main__":unittest.main()
