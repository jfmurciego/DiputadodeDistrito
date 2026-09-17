from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from ddd_ensemble.gallery import build_gallery

ROOT = Path(__file__).resolve().parents[1]


class EnsembleWebCrsTests(unittest.TestCase):
    def test_gallery_reprojects_only_web_copy_from_epsg25830(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "candidate.geojson"
            original = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}},
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"district_id": 1},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[
                                [710284.5263, 4671203.0561],
                                [710384.5263, 4671203.0561],
                                [710384.5263, 4671303.0561],
                                [710284.5263, 4671203.0561],
                            ]],
                        },
                    }
                ],
            }
            source.write_text(json.dumps(original), encoding="utf-8")
            summary = {
                "territory_id": "aragon",
                "candidate_count_valid": 1,
                "candidate_count_expected": 1,
                "candidates": [{"candidate_id": "balanced-01", "geojson": str(source)}],
            }
            summary_path = root / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")

            build_gallery(str(summary_path), str(root / "site"))

            analytical = json.loads(source.read_text(encoding="utf-8"))
            web = json.loads((root / "site/assets/balanced-01.geojson").read_text(encoding="utf-8"))
            self.assertIn("crs", analytical)
            self.assertGreater(analytical["features"][0]["geometry"]["coordinates"][0][0][0], 100000)
            self.assertNotIn("crs", web)
            lon, lat = web["features"][0]["geometry"]["coordinates"][0][0]
            self.assertAlmostEqual(lon, -0.4543801425, places=7)
            self.assertAlmostEqual(lat, 42.1647294708, places=7)
            self.assertGreaterEqual(lon, -180)
            self.assertLessEqual(lon, 180)
            self.assertGreaterEqual(lat, -90)
            self.assertLessEqual(lat, 90)


class ModularWorkflowContractTests(unittest.TestCase):
    def test_main_interface_exposes_only_resolver_and_selected_route(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/ejecucion-generacion-distritos.yml").read_text(encoding="utf-8"))
        self.assertEqual(list(workflow["jobs"]), ["resolver_interfaz", "ruta"])

    def test_production_workflow_has_visible_m01_m08_audit_and_viewer(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8"))
        jobs = workflow["jobs"]
        expected = [
            "resolve", "official_sources", "m01", "m02", "m03", "internal_units",
            "m04", "m05", "m06", "auditoria", "electoral_source", "m07", "m08", "visor",
        ]
        self.assertEqual(list(jobs), expected)
        self.assertEqual(jobs["official_sources"]["name"], "Fuentes oficiales")
        self.assertEqual(jobs["internal_units"]["name"], "Preparar unidades internas")
        self.assertEqual(jobs["electoral_source"]["name"], "Fuente electoral oficial")
        self.assertEqual(jobs["m04"]["needs"], ["resolve", "internal_units"])
        self.assertIn("electoral_source", jobs["m07"]["needs"])
        names = [jobs[f"m{i:02d}"]["name"] for i in range(1, 9)]
        self.assertTrue(all(f"M{i:02d}" in names[i - 1] for i in range(1, 9)))

    def test_launcher_supports_explicit_chain_state_without_changing_stage_map(self):
        text = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn('CHAIN_STATE="${DDD_CHAIN_STATE:-}"', text)
        for stage in range(1, 9):
            self.assertIn(f"M{stage:02d}) echo {stage}", text)

    def test_checkpoint_audit_and_viewer_share_run_identity(self):
        text = (ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn("name: ddd-state-${{ github.run_id }}-${{ env.STAGE }}", text)
        self.assertIn("name: ddd-state-${{ steps.state.outputs.run_id }}-${{ env.PREVIOUS_STAGE }}", text)
        self.assertIn("name: ddd-state-${{ github.run_id }}-M03U", text)
        self.assertIn("name: ddd-internal-units-${{ github.run_id }}", text)
        self.assertIn("name: ddd-electoral-source-${{ github.run_id }}", text)
        self.assertIn("name: ddd-audit-${{ github.run_id }}", text)
        self.assertIn("production_run_id: ${{ github.run_id }}", text)
        self.assertIn("cache-from: type=gha,scope=ddd-production-${{ github.sha }}", text)


if __name__ == "__main__":
    unittest.main()
