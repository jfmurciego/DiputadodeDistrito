import unittest
from pathlib import Path

from herramientas.selector_campana_nacional import CANONICAL_IDS, build_selection_manifest, matrix_from_manifest

ROOT = Path(__file__).resolve().parents[1]
SHA = "0" * 40


class SelectorCampanaNacionalTest(unittest.TestCase):
    def build(self, ids):
        return build_selection_manifest(
            ROOT, list(ids), edition="2025", execution_mode="Reutilizar progreso existente",
            strategy="GerryChain 50", source_sha=SHA, campaign_instance="campaign-test-1",
        )

    def test_cero_territorios_se_rechaza(self):
        with self.assertRaisesRegex(ValueError, "entre 1 y 19"):
            self.build([])

    def test_selecciones_1_5_12_19_conservan_orden_e_identidad_canonica(self):
        for count in (1, 5, 12, 19):
            with self.subTest(count=count):
                chosen = list(reversed(CANONICAL_IDS[:count]))
                manifest = self.build(chosen)
                observed = [x["territory_id"] for x in manifest["territories"]]
                self.assertEqual(observed, list(CANONICAL_IDS[:count]))
                self.assertEqual(len(observed), count)
                self.assertEqual([x["slot"] for x in manifest["territories"]], [f"{n:02d}" for n in range(1, count + 1)])
                self.assertTrue(all(x["territory_name"] for x in manifest["territories"]))
                self.assertTrue(all(x["contract_path"].endswith(".yaml") for x in manifest["territories"]))

    def test_manifiesto_no_duplica_parametros_territoriales(self):
        manifest = self.build(CANONICAL_IDS)
        forbidden = {"k", "population", "population_total", "sections", "section_count", "expected_district_count"}
        for row in manifest["territories"]:
            self.assertFalse(forbidden.intersection(row))
        self.assertFalse(manifest["fail_fast"])
        self.assertEqual(manifest["max_parallel"], 5)
        self.assertFalse(manifest["publish_result"])
        self.assertFalse(manifest["persist_state"])
        self.assertFalse(manifest["production_execution_enabled"])

    def test_matrix_deriva_del_manifiesto_inmutable(self):
        manifest = self.build(CANONICAL_IDS[:5])
        matrix = matrix_from_manifest(manifest)
        self.assertEqual(len(matrix["include"]), 5)
        self.assertTrue(all(r["manifest_sha256"] == manifest["manifest_sha256"] for r in matrix["include"]))
        self.assertTrue(all(r["publish_result"] is False and r["persist_state"] is False for r in matrix["include"]))

    def test_gestor_productivo_actual_no_publica_desde_hijos_y_conserva_concurrencia(self):
        text = (ROOT / ".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
        self.assertIn("fail-fast: false", text)
        self.assertIn("max-parallel: 5", text)
        self.assertIn("uses: ./.github/workflows/ejecucion-completa-proyecto.yml", text)
        self.assertIn("publish_result: false", text)
        self.assertIn("persist_state: false", text)


if __name__ == "__main__":
    unittest.main()
