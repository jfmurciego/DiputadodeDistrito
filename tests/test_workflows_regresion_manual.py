import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=(ROOT/"legacy/workflows/consolidacion-interfaz/regresion-m06-aragon_v1.6.1.yml",ROOT/"legacy/workflows/consolidacion-interfaz/regresion-m06-castilla-y-leon_v1.3.0.yml")

def _trigger_block(path:Path)->str:
    text=path.read_text(encoding="utf-8")
    start=text.index("\non:\n")+1
    end=text.index("\npermissions:\n",start)
    return text[start:end]

class WorkflowsRegresionManual(unittest.TestCase):
    def test_regresiones_archivadas_preservan_su_disparador_historico(self):
        for workflow in WORKFLOWS:
            self.assertTrue(workflow.is_file())
            trigger=_trigger_block(workflow)
            self.assertEqual(trigger,"on:\n  workflow_dispatch:\n")
            self.assertNotIn("push:",trigger)
            self.assertNotIn("schedule:",trigger)

if __name__=="__main__":
    unittest.main()
