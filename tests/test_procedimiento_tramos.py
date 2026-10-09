#!/usr/bin/env python3
"""Contrato estático del lanzador semántico: no admite reenganche sin evidencia."""
from __future__ import annotations
import unittest
from pathlib import Path
class ProcedimientoTramos(unittest.TestCase):
 def test_guardas_y_etapas_semanticas(self):
  text=Path("procedimiento.sh").read_text(encoding="utf-8")
  for token in ("DDD_FROM_STAGE","DDD_TO_STAGE","DDD_CHECKPOINT_MANIFEST","DDD_CHECKPOINT_CACHE_DIR","TERRITORY_PREPARATION","PUBLIC_PRODUCT_PUBLICATION"):
   self.assertIn(token,text)
  self.assertIn("Reenganche requiere DDD_CHECKPOINT_MANIFEST",text)
  self.assertIn("checkpoint M03 materializado",text)
if __name__=="__main__": unittest.main()
