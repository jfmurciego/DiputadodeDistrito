from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herramientas.auditar_componentes_geometricos import audit


CRS = {
    "type": "name",
    "properties": {"name": "urn:ogc:def:crs:EPSG::25830"},
}


def feature(section_id: str, district_id: int, x0: float, y0: float, x1: float, y1: float):
    return {
        "type": "Feature",
        "properties": {
            "CUSEC_KEY": section_id,
            "district_id": district_id,
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [x0, y0],
                [x1, y0],
                [x1, y1],
                [x0, y1],
                [x0, y0],
            ]],
        },
    }


class GeometricComponentsAuditTests(unittest.TestCase):
    def write_sections(self, root: Path, features: list[dict]) -> Path:
        path = root / "sections.geojson"
        path.write_text(
            json.dumps({
                "type": "FeatureCollection",
                "crs": CRS,
                "features": features,
            }),
            encoding="utf-8",
        )
        return path

    def run_audit(self, sections: Path, policy: Path | None = None) -> dict:
        return audit(
            sections,
            section_field="CUSEC_KEY",
            district_field="district_id",
            working_crs="EPSG:25830",
            policy_path=policy,
            expected_districts=1,
        )

    def test_shared_real_border_passes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sections = self.write_sections(root, [
                feature("a", 1, 0, 0, 1, 1),
                feature("b", 1, 1, 0, 2, 1),
            ])
            report = self.run_audit(sections)
            district = report["districts"][0]
            self.assertEqual(report["decision"], "PASS")
            self.assertEqual(district["dissolved_geometry_type"], "Polygon")
            self.assertEqual(district["component_count"], 1)
            self.assertTrue(district["connected"])

    def test_corner_contact_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sections = self.write_sections(root, [
                feature("a", 1, 0, 0, 1, 1),
                feature("b", 1, 1, 1, 2, 2),
            ])
            report = self.run_audit(sections)
            district = report["districts"][0]
            self.assertEqual(report["decision"], "BLOCK")
            self.assertEqual(district["dissolved_geometry_type"], "MultiPolygon")
            self.assertEqual(district["component_count"], 2)
            self.assertEqual(district["status"], "POTENTIAL_DISCONTINUITY")

    def test_separated_polygons_fail(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sections = self.write_sections(root, [
                feature("a", 1, 0, 0, 1, 1),
                feature("b", 1, 3, 0, 4, 1),
            ])
            report = self.run_audit(sections)
            district = report["districts"][0]
            self.assertEqual(report["decision"], "BLOCK")
            self.assertEqual(district["component_count"], 2)
            self.assertFalse(district["connected"])

    def test_multipolygon_passes_only_with_explicit_policy_exception(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            multipart = {
                "type": "Feature",
                "properties": {"CUSEC_KEY": "a", "district_id": 1},
                "geometry": {"type": "MultiPolygon", "coordinates": [
                    [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                    [[[3, 0], [4, 0], [4, 1], [3, 1], [3, 0]]],
                ]},
            }
            sections = self.write_sections(root, [multipart])
            without_policy = self.run_audit(sections)
            self.assertEqual(without_policy["decision"], "BLOCK")

            policy = root / "policy.json"
            policy.write_text(json.dumps({
                "schema": "ddd.geometric-contiguity-policy/1.0",
                "allowed_disconnected_districts": [{
                    "district_id": 1,
                    "expected_components": 2,
                    "kind": "official_atomic_multipart_section",
                    "reason": "Caso sintético: discontinuidad expresamente gobernada.",
                }],
            }), encoding="utf-8")
            with_policy = self.run_audit(sections, policy)
            district = with_policy["districts"][0]
            self.assertEqual(with_policy["decision"], "PASS_WITH_EXCEPTIONS")
            self.assertEqual(district["status"], "GOVERNED_EXCEPTION")
            self.assertTrue(district["policy_applied"])
            self.assertTrue(district["atomic_multipart_cause_proven"])

    def test_policy_cannot_excuse_unrelated_islands(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            sections = self.write_sections(root, [
                feature("a", 1, 0, 0, 1, 1),
                feature("b", 1, 3, 0, 4, 1),
            ])
            policy = root / "policy.json"
            policy.write_text(json.dumps({
                "schema": "ddd.geometric-contiguity-policy/1.0",
                "allowed_disconnected_districts": [{
                    "district_id": 1,
                    "expected_components": 2,
                    "kind": "official_atomic_multipart_section",
                    "reason": "No basta con declararlo: debe probarse.",
                }],
            }), encoding="utf-8")
            report = self.run_audit(sections, policy)
            self.assertEqual(report["decision"], "BLOCK")
            self.assertFalse(report["districts"][0]["atomic_multipart_cause_proven"])

    def test_polygon_with_hole_remains_connected_and_is_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            donut = {
                "type": "Feature",
                "properties": {"CUSEC_KEY": "a", "district_id": 1},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [[0, 0], [4, 0], [4, 4], [0, 4], [0, 0]],
                        [[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]],
                    ],
                },
            }
            sections = self.write_sections(root, [donut])
            report = self.run_audit(sections)
            district = report["districts"][0]
            self.assertEqual(report["decision"], "PASS")
            self.assertEqual(district["component_count"], 1)
            self.assertEqual(district["interior_ring_count"], 1)


if __name__ == "__main__":
    unittest.main()
