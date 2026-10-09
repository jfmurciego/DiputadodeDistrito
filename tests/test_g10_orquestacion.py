#!/usr/bin/env python3
"""Pruebas G10 v1.1.0: control sin cómputo GIS."""
from __future__ import annotations
import tempfile,unittest
from pathlib import Path
from g10.core import TaskStatus,admission_matrix,compute_fingerprint,merge_successful_state,normalized_task,validate_plan
class G10Orquestacion(unittest.TestCase):
 def task(self):return {"task_id":"t1","territory":"aragon","stage":"M05","depends_on":[],"max_attempts":2,"timeout_minutes":10,"estimated_runner_minutes":3,"success_contract":"c.json","action":"territory_m01_m06"}
 def test_compatibilidad_m05(self):
  item=normalized_task(self.task());self.assertEqual(item["stage_id"],"DISTRICT_BALANCING");self.assertEqual(item["stage_name"],"Equilibrar y reparar distritos")
 def test_plan_v10(self):
  plan={"schema_version":"1.0","lot_id":"l","budget":{"runner_minutes":10,"max_parallel":1},"tasks":[self.task()]};validate_plan(plan)
 def test_admision_durable(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/"a").write_text("a"); task={**self.task(),"stage_id":"DISTRICT_BALANCING","fingerprint_inputs":["a"],"action":"g10_selftest"}
   plan={"schema_version":"1.1","lot_id":"l","budget":{"runner_minutes":10,"max_parallel":1},"tasks":[task]};first=admission_matrix(plan,{"records":[]},root=root);self.assertEqual(first["include"][0]["admission"],"ADMITTED")
   state=merge_successful_state({"records":[]},[{"task_id":"t1","territory":"aragon","stage_id":"DISTRICT_BALANCING","legacy_module":"M05","fingerprint":first["include"][0]["fingerprint"],"status":"SUCCESS","artifacts":[]}],run_id="1")
   second=admission_matrix(plan,state,root=root);self.assertEqual(second["include"][0]["admission"],"REUSED")
 def test_huella_cambia(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);(root/"a").write_text("1");one=compute_fingerprint(["a"],root=root);(root/"a").write_text("2");self.assertNotEqual(one,compute_fingerprint(["a"],root=root))
if __name__=="__main__":unittest.main()
