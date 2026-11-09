# -*- coding: utf-8 -*-
"""T-126: el registro de publicaciones no contiene el mapa 350 y conserva el Valladolid de 407.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from herramientas import registro_publicaciones_visor as rpv  # noqa: E402

RETIRADAS = {"m06-congreso350_valladolid-42613899978", "m08-congreso350_valladolid-42613899978"}


class RegistroSinMapa350(unittest.TestCase):
    def setUp(self):
        self.ruta = ROOT / "orchestracion/publicaciones_visor.json"
        self.registro = json.loads(self.ruta.read_text("utf-8"))

    def test_sin_entradas_congreso350(self):
        todas = self.registro["products"] + self.registro.get("ensembles", [])
        self.assertEqual([e["id"] for e in todas if str(e.get("territory_id", "")).startswith("congreso350_")], [])
        self.assertFalse(RETIRADAS & {e["id"] for e in self.registro["products"]})

    def test_el_valladolid_de_407_sigue_publicado(self):
        ids = {e["id"] for e in self.registro["products"] if e["territory_id"] == "congreso_valladolid"}
        self.assertEqual(ids, {"m06-congreso_valladolid-41299313598", "m08-congreso_valladolid-41299313598"})

    def test_el_registro_valida_y_su_formato_es_el_de_la_herramienta(self):
        rpv.validate_registry(self.registro)
        import tempfile
        t = Path(tempfile.mkdtemp()) / "r.json"
        rpv.save_registry(t, rpv._sorted_registry(self.registro))
        self.assertEqual(t.read_text("utf-8"), self.ruta.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
