"""Version 1.0.0; 2026-10-09; regresiones C1-C3; revisión pendiente; nuevo."""
import copy,json,unittest
from pathlib import Path
from herramientas.evaluar_alternativas_nacionales import validate_model
from herramientas.inventariar_cartografia_historica import historical_material_verdict
class Closure(unittest.TestCase):
 def test_c1_balanced_allocation_tampering_each_rule(self):
  model=json.loads((Path(__file__).resolve().parents[1]/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json').read_text())
  validate_model(model)
  for index in range(5):
   altered=copy.deepcopy(model);rows=altered['alternatives'][index]['rows'];rows[0]['k_assigned']+=1;rows[1]['k_assigned']-=1
   with self.subTest(rule=index),self.assertRaisesRegex(ValueError,'PROVINCIAL_ALLOCATION'):validate_model(altered)
 def test_c1_balanced_quota_tampering_each_rule(self):
  from fractions import Fraction
  model=json.loads((Path(__file__).resolve().parents[1]/'docs/ESTUDIOS/modelo_nacional_2025_120000/modelo.json').read_text())
  for index in range(5):
   altered=copy.deepcopy(model);rows=altered['alternatives'][index]['rows'];rows[0]['allocation_quota']=str(Fraction(rows[0]['allocation_quota'])+1);rows[1]['allocation_quota']=str(Fraction(rows[1]['allocation_quota'])-1)
   with self.subTest(rule=index),self.assertRaisesRegex(ValueError,'ALLOCATION_QUOTA'):validate_model(altered)
 def test_c2_positive(self):self.assertTrue(historical_material_verdict({'1'},{'1'},1,1,['abc','abc']).startswith('same_historical_material'))
 def test_c2_distinct(self):
  for args in [({'1'},{'2'},0,0,['a','a']),({'1'},{'1'},0,1,['a','a']),({'1'},{'1'},1,0,['a','a']),({'1'},{'1'},1,1,['a','b'])]:self.assertEqual(historical_material_verdict(*args),'DIFFERENT_HISTORICAL_MATERIAL')
 def test_c2_insufficient(self):
  for sheets in [[],['a'],['a',None]]:self.assertEqual(historical_material_verdict({'1'},{'1'},1,1,sheets),'INSUFFICIENT_EVIDENCE')
if __name__=='__main__':unittest.main()
