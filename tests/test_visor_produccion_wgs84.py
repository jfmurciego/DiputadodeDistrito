"""Regresión: las copias M06/M08 del visor deben ser WGS84 sin mutar el ZIP analítico."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.preparar_visor_ejecucion import write_geojson_from_zip


class ProductionViewerWgs84Tests(unittest.TestCase):
    def test_projected_production_zip_is_reprojected_only_in_web_copy(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "aragon_m06_distritos.geojson.zip"
            payload = {
                "type": "FeatureCollection",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25830"}},
                "features": [{
                    "type": "Feature",
                    "properties": {"district_id": "D-01", "label": "sin cambios"},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[676000, 4613000], [677000, 4613000], [677000, 4614000], [676000, 4613000]]],
                    },
                }],
            }
            with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("aragon_m06_distritos.geojson", json.dumps(payload))
            before = source.read_bytes()
            destination = root / "site/data/results/m06-test.geojson"

            count = write_geojson_from_zip(source, destination)

            self.assertEqual(count, 1)
            self.assertEqual(source.read_bytes(), before)
            web = json.loads(destination.read_text(encoding="utf-8"))
            self.assertNotIn("crs", web)
            self.assertEqual(web["features"][0]["properties"], payload["features"][0]["properties"])
            x, y = web["features"][0]["geometry"]["coordinates"][0][0]
            self.assertGreaterEqual(x, -10.0)
            self.assertLessEqual(x, 5.0)
            self.assertGreaterEqual(y, 35.0)
            self.assertLessEqual(y, 44.5)
            self.assertNotEqual([x, y], [676000, 4613000])


if __name__ == "__main__":
    unittest.main()
