import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class IndependentVerifierTest(unittest.TestCase):
    def test_certified_evidence_is_recomputed_independently(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"report.json"
            result=subprocess.run([sys.executable,str(ROOT/"herramientas/verificar_independiente_m03_m06.py"),"--config",str(ROOT/"configuracion/verificacion_independiente_m03_m06.json"),"--output",str(output)],cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            report=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["decision"],"PASS")
            self.assertEqual([row["decision"] for row in report["territories"]],["PASS","PASS","BLOCKED_INDEPENDENT_VALIDATION"])

if __name__=="__main__": unittest.main()
