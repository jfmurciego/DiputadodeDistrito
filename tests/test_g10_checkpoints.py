#!/usr/bin/env python3
"""Pruebas de reenganche G10: los checkpoints no inventan evidencia."""
from __future__ import annotations
import unittest
from g10.checkpoints import select_resume_checkpoint
class G10Checkpoints(unittest.TestCase):
 def items(self):
  return [
   {"stage_id":"TERRITORY_GRAPH","status":"CANONICAL_VERIFIED_LEGACY","products_manifest":"M03/PRODUCTOS.json"},
   {"stage_id":"DISTRICT_FORMATION","status":"CANONICAL_VERIFIED_LEGACY","products_manifest":"M04/PRODUCTOS.json"},
   {"stage_id":"DISTRICT_BALANCING","status":"CANONICAL_VERIFIED_LEGACY","products_manifest":"M05/PRODUCTOS.json"}]
 def test_m05_reanuda_m04(self):
  decision=select_resume_checkpoint(self.items(),changed_stage_id="DISTRICT_BALANCING",target_stage_id="TERRITORIAL_CERTIFICATION")
  self.assertEqual(decision.resume_stage_id,"DISTRICT_FORMATION")
 def test_m01_no_reutiliza_nada(self):
  decision=select_resume_checkpoint(self.items(),changed_stage_id="TERRITORY_PREPARATION",target_stage_id="TERRITORIAL_CERTIFICATION")
  self.assertIsNone(decision.resume_stage_id)
 def test_bloqueado_no_reanuda(self):
  items=[{"stage_id":"DISTRICT_FORMATION","status":"EXPERIMENTAL_BLOCKED","products_manifest":"M04/PRODUCTOS.json"}]
  self.assertIsNone(select_resume_checkpoint(items,changed_stage_id="DISTRICT_BALANCING",target_stage_id="TERRITORIAL_CERTIFICATION").resume_stage_id)
if __name__=="__main__": unittest.main()
