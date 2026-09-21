#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
S=importlib.util.spec_from_file_location("arch",ROOT/"herramientas/auditar_componentes_archipielago.py")
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)

class AuditarComponentesArchipielago(unittest.TestCase):
    def test_components(self):
        e=[{"u":"a","v":"b"},{"u":"c","v":"d"}]
        self.assertEqual([sorted(x) for x in M.components(["a","b","c","d","e"],e)],[["a","b"],["c","d"],["e"]])

if __name__=="__main__":
    unittest.main()
