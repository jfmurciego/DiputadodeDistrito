import os
from pathlib import Path
import unittest,yaml
ROOT=Path(__file__).resolve().parents[1]
WORKFLOWS=ROOT/".github/workflows"

class WorkflowSafety(unittest.TestCase):
    def test_solo_tres_workflows_y_unica_ci_automatica(self):
        names=sorted(p.name for p in WORKFLOWS.glob("*.yml"))
        self.assertEqual(names,["preparacion-fuentes.yml","produccion-distritos.yml","pruebas-plataforma.yml"])
        tests=yaml.safe_load((WORKFLOWS/"pruebas-plataforma.yml").read_text(encoding="utf-8"))
        triggers=tests.get("on") or tests.get(True)
        self.assertEqual(set(triggers),{"push","pull_request"})
        for manual in ("preparacion-fuentes.yml","produccion-distritos.yml"):
            data=yaml.safe_load((WORKFLOWS/manual).read_text(encoding="utf-8"))
            t=data.get("on") or data.get(True)
            self.assertEqual(set(t),{"workflow_dispatch"})

    def test_produccion_aplica_politica_geometrica_y_preserva_excepciones(self):
        production=(WORKFLOWS/"produccion-distritos.yml").read_text(encoding="utf-8")
        state=(ROOT/"herramientas/estado_produccion.py").read_text(encoding="utf-8")
        self.assertIn('continuidad_geometrica_{year}.json',production)
        self.assertIn('policy_args=(--policy "/app/$policy")',production)
        self.assertIn('GEOMETRIC_DECISION: ${{ steps.geometric.outputs.decision }}',production)
        self.assertIn('"PASS_WITH_EXCEPTIONS"',state)

    def test_workflows_territoriales_retirados_no_reaparecen(self):
        for name in ("g10-control.yml","g10-operar-lote.yml","regresion-m06-aragon.yml","regresion-m06-castilla-y-leon.yml"):
            self.assertFalse((WORKFLOWS/name).exists())

if __name__=="__main__": unittest.main()
