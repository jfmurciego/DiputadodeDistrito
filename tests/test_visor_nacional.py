"""Versión 1.0.0 — Contrato de la vista Nacional del visor (T-84). Fecha: 2026-11-08.
Estado: prueba. Anterior: ninguno (fichero nuevo).
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "visor/nacional/nacional.js").read_text(encoding="utf-8")
HTML = (ROOT / "visor/nacional/index.html").read_text(encoding="utf-8")


class VisorNacionalTests(unittest.TestCase):
    def test_usa_feature_state_y_no_innerhtml(self):
        for s in ("setFeatureState", 'promoteId:"uid"', '"feature-state"', "INDEX.json"):
            self.assertIn(s, JS)
        self.assertNotIn("innerHTML", JS)

    def test_barra_temporal_solo_activa_2023(self):
        for y in ("2011", "2015", "2016", "2019"):
            self.assertIn('{id:"%s",label:"%s",ok:false' % (y, y), JS)
        self.assertIn('{id:"2023",label:"2023",ok:true}', JS)

    def test_capas_sin_datos_desactivadas(self):
        for c in ("ganador-seccion", "rotacion", "participacion"):
            self.assertIn('id:"%s",label' % c, JS)
        self.assertEqual(JS.count("ok:false"), 7)

    def test_paginas_y_vistas(self):
        for s in ("Nacional", "Autonómica", 'id="timebar"', 'id="layers"', "nacional.js"):
            self.assertIn(s, HTML)


if __name__ == "__main__":
    unittest.main()
