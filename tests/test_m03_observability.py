#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("m03",ROOT/"modulos/03_construir_grafo.py")
M03=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M03)

class M03Observability(unittest.TestCase):
    def test_componentes_globales_deterministas(self):
        adj={"a":{"b"},"b":{"a"},"c":set()}
        comps=M03.component_sets({"a","b","c"},adj)
        self.assertEqual([sorted(x) for x in comps],[["a","b"],["c"]])

    def test_auditoria_administrativa_informa_sin_decidir_bloqueo(self):
        g=pd.DataFrame({"CPRO":["01","01","01"],"CUSEC_KEY":["a","b","c"]})
        adj={"a":{"b"},"b":{"a"},"c":set()}
        details,bad=M03.audit_group_components(g,"CUSEC_KEY",["CPRO"],adj)
        self.assertEqual(details["01"]["components"],2)
        self.assertEqual(details["01"]["component_sizes"],[2,1])
        self.assertEqual(bad[0]["key"],"01")

if __name__=="__main__":
    unittest.main()
