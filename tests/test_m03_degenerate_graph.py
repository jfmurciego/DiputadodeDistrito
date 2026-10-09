#!/usr/bin/env python3
"""Regresión del defecto histórico: M03 no puede aceptar un grafo topológicamente vacío."""
from __future__ import annotations
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("m03",ROOT/"modulos"/"03_construir_grafo.py")
M03=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M03)

class DegenerateGraphContract(unittest.TestCase):
    def test_rechaza_universo_vacio(self):
        with self.assertRaises(SystemExit):
            M03.validate_minimum_graph([],[])

    def test_rechaza_varios_nodos_sin_aristas(self):
        nodes=[{"id":str(i),"pop":1} for i in range(1463)]
        with self.assertRaises(SystemExit) as caught:
            M03.validate_minimum_graph(nodes,[])
        self.assertIn("1463 nodos y cero aristas",str(caught.exception))

    def test_admite_unidad_unica_y_grafo_con_relacion(self):
        M03.validate_minimum_graph([{"id":"a","pop":1}],[])
        M03.validate_minimum_graph([{"id":"a","pop":1},{"id":"b","pop":1}],[{"u":"a","v":"b"}])

if __name__=="__main__":unittest.main()
