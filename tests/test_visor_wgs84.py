"""Pruebas de inmutabilidad y CRS para las copias GeoJSON del visor."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ddd_ensemble.gallery import _write_web_geojson, build_gallery
from herramientas.preparar_visor_ejecucion import add_ensemble


def projected_collection(geometry: dict, *, source: str = "analytical") -> dict:
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}},
        "features": [{
            "type": "Feature",
            "properties": {"district_id": "D-01", "source": source, "label": "sin cambios"},
            "geometry": geometry,
        }],
    }


def assert_wgs84(test: unittest.TestCase, payload: dict) -> None:
    def walk(value):
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2]):
            yield value[0], value[1]
        elif isinstance(value, list):
            for item in value:
                yield from walk(item)
    points = []
    for feature in payload["features"]:
        geometry = feature["geometry"]
        if geometry.get("type") == "GeometryCollection":
            for child in geometry.get("geometries", []):
                points.extend(walk(child.get("coordinates", [])))
        else:
            points.extend(walk(geometry.get("coordinates", [])))
    test.assertTrue(points)
    for x, y in points:
        test.assertGreaterEqual(x, -10.0)
        test.assertLessEqual(x, 5.0)
        test.assertGreaterEqual(y, 35.0)
        test.assertLessEqual(y, 44.5)


class ViewerWgs84Tests(unittest.TestCase):
    def test_gallery_keeps_projected_original_and_writes_wgs84_copy(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "candidate.geojson"
            original = projected_collection({
                "type": "Polygon",
                "coordinates": [[[676000, 4613000], [677000, 4613000], [677000, 4614000], [676000, 4613000]]],
            })
            source.write_text(json.dumps(original), encoding="utf-8")
            before = source.read_bytes()
            summary = root / "summary.json"
            summary.write_text(json.dumps({
                "territory_id": "aragon",
                "candidates": [{"candidate_id": "balanced-01", "geojson": str(source)}],
            }), encoding="utf-8")

            build_gallery(str(summary), str(root / "site"))

            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(json.loads(source.read_text(encoding="utf-8"))["crs"]["properties"]["name"], "urn:ogc:def:crs:EPSG::25830")
            web = json.loads((root / "site/assets/balanced-01.geojson").read_text(encoding="utf-8"))
            self.assertNotIn("crs", web)
            self.assertEqual(web["features"][0]["properties"], original["features"][0]["properties"])
            self.assertEqual(web["features"][0]["properties"]["district_id"], "D-01")
            assert_wgs84(self, web)

    def test_geometry_collection_is_transformed_without_touching_properties(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "collection.geojson"
            payload = projected_collection({
                "type": "GeometryCollection",
                "geometries": [
                    {"type": "Point", "coordinates": [676000, 4613000]},
                    {"type": "LineString", "coordinates": [[676000, 4613000], [677000, 4614000]]},
                ],
            })
            source.write_text(json.dumps(payload), encoding="utf-8")
            destination = root / "web.geojson"

            _write_web_geojson(source, destination)

            web = json.loads(destination.read_text(encoding="utf-8"))
            self.assertNotIn("crs", web)
            self.assertEqual(web["features"][0]["properties"], payload["features"][0]["properties"])
            self.assertNotEqual(web["features"][0]["geometry"]["geometries"][0]["coordinates"], [676000, 4613000])
            assert_wgs84(self, web)

    def test_execution_viewer_prefers_ensemble_web_copy_over_projected_original(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "ensemble"
            analytical = root / "results/balanced-01/candidate.geojson"
            analytical.parent.mkdir(parents=True)
            analytical.write_text(json.dumps(projected_collection({"type": "Point", "coordinates": [676000, 4613000]})), encoding="utf-8")

            web_payload = projected_collection({"type": "Point", "coordinates": [-0.88647, 41.64932]}, source="web")
            web_payload.pop("crs")
            web_asset = root / "site/assets/balanced-01.geojson"
            web_asset.parent.mkdir(parents=True)
            web_asset.write_text(json.dumps(web_payload), encoding="utf-8")
            summary = root / "site/data/summary.json"
            summary.parent.mkdir(parents=True)
            summary.write_text(json.dumps({
                "territory_id": "aragon",
                "candidates": [{
                    "candidate_id": "balanced-01",
                    "asset": "assets/balanced-01.geojson",
                    "geojson": str(analytical),
                    "metrics": {"population": {"district_count": 67}},
                }],
            }), encoding="utf-8")

            output = Path(raw) / "viewer"
            results = []
            add_ensemble(root, output, results)

            copied = json.loads((output / "data/ensemble/aragon/ensemble/balanced-01.geojson").read_text(encoding="utf-8"))
            self.assertEqual(copied["features"][0]["properties"]["source"], "web")
            self.assertNotIn("crs", copied)
            assert_wgs84(self, copied)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["viewer_path"], "data/ensemble/aragon/ensemble/balanced-01.geojson")


if __name__ == "__main__":
    unittest.main()
