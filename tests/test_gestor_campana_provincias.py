"""T-06: el Gestor de Campañas admite las 52 provincias nacionales (INE, matrícula en español o nombre)."""
from pathlib import Path
import unittest

import yaml

from herramientas.gestor_campana_nacional import (
    CONFIRMATION, build_manifest, build_matrix, canonical_selection, parse_selection,
)

ROOT = Path(__file__).resolve().parents[1]
NAC = "Nacional 2023"


class GestorProvincias(unittest.TestCase):
    def test_selector_lista_las_52_provincias(self):
        ids = parse_selection("todos", campaign=NAC)
        self.assertEqual(len(ids), 52)
        self.assertTrue(all(t.startswith("congreso_") for t in ids))
        self.assertEqual(len(parse_selection("todos")), 19)  # la autonómica no cambia

    def test_ine_matricula_y_nombre(self):
        self.assertEqual(parse_selection("22, HU, Huesca, Nacional Huesca", campaign=NAC), ["congreso_huesca"])
        self.assertEqual(parse_selection("GE, 7, la coruña", campaign=NAC),
                         ["congreso_gerona", "congreso_baleares", "congreso_la_coruna"])
        for bad in ("GI", "OU", "Aragón"):
            with self.assertRaises(ValueError):
                parse_selection(bad, campaign=NAC)
        with self.assertRaises(ValueError):
            parse_selection("Huesca", campaign="Municipal 2027")

    def test_no_mezcla_y_hasta_52(self):
        with self.assertRaises(ValueError):
            canonical_selection(["aragon", "congreso_huesca"], ROOT)
        self.assertEqual(len(canonical_selection(parse_selection("todos", campaign=NAC), ROOT)), 52)

    def test_huesca_completa_reutiliza_su_producto(self):
        manifest = build_manifest(selected=["congreso_huesca"], publication_mode="electoral", source_sha="a" * 40,
                                  strategy="Canónico", campaign_instance="t06")
        row = manifest["territories"][0]
        self.assertEqual((row["slot"], row["territory_display_name"]), ("C22", "Nacional Huesca"))
        self.assertEqual(row["execution_route"], "PRODUCT_REUSE_READY")
        include = build_matrix(manifest, CONFIRMATION)["include"]
        self.assertEqual([r["territory_name"] for r in include], ["Congreso Huesca"])  # valor que acepta el 00

    def test_workflow_ofrece_la_campana_nacional(self):
        data = yaml.safe_load((ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8"))
        inputs = data.get(True, data.get("on"))["workflow_dispatch"]["inputs"]
        self.assertEqual(inputs["campana"]["options"], ["Autonómica 2025", "Nacional 2023"])


if __name__ == "__main__":
    unittest.main()
