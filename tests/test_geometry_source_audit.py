from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import shapely
import yaml
from shapely.geometry import Polygon, box

from ddd_core.territorial_validation import TerritorialDataError, validate_geodataframe
from herramientas.adquirir_fuentes_oficiales import (
    _collect_live_sections,
    _raw_ogc_capture,
    _write_shapefile_zip,
)
from herramientas.resolver_fuentes_territorio import build_declaration


ROOT = Path(__file__).resolve().parents[1]
CATALOG = yaml.safe_load(
    (ROOT / "fuentes/catalogo_oficial.yaml").read_text(encoding="utf-8")
)


class GeometryAuditTests(unittest.TestCase):
    def test_invalid_geometry_reports_identity_reason_hash_and_versions_without_repair(self):
        bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
        gdf = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"], "population": [123]},
            geometry=[bowtie],
            crs="EPSG:4326",
        )
        before_wkb = shapely.to_wkb(gdf.geometry.iloc[0], hex=False)

        with self.assertRaises(TerritorialDataError) as first:
            validate_geodataframe(gdf, label="seccionado a materializar")
        with self.assertRaises(TerritorialDataError) as second:
            validate_geodataframe(gdf, label="seccionado a materializar")

        message = str(first.exception)
        self.assertEqual(message, str(second.exception))
        self.assertIn("GEOMETRY_INVALID", message)
        self.assertIn('"feature_id": "0100101001"', message)
        self.assertIn('"geometry_type": "Polygon"', message)
        self.assertIn("Self-intersection", message)
        self.assertIn('"parsed_geometry_wkb_sha256"', message)
        self.assertIn('"shapely"', message)
        self.assertIn('"geos"', message)
        self.assertEqual(
            shapely.to_wkb(gdf.geometry.iloc[0], hex=False),
            before_wkb,
        )
        self.assertEqual(gdf["population"].tolist(), [123])

    def test_valid_geometry_is_not_changed_by_validation(self):
        gdf = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"], "population": [0]},
            geometry=[box(0, 0, 1, 1)],
            crs="EPSG:4326",
        )
        before = shapely.to_wkb(gdf.geometry.iloc[0], hex=False)
        validate_geodataframe(gdf, label="valid")
        after = shapely.to_wkb(gdf.geometry.iloc[0], hex=False)
        self.assertEqual(before, after)
        self.assertEqual(gdf["CUSEC"].tolist(), ["0100101001"])
        self.assertEqual(gdf["population"].tolist(), [0])

    def test_raw_ogc_bytes_are_preserved_before_geometry_conversion_and_block_survives(self):
        declaration = build_declaration(
            "Islas Baleares",
            2025,
            population_year=2023,
            section_year=2023,
        )
        source = CATALOG["sources"]["secciones_censales"]
        provinces = declaration["territory"]["territorial_codes"]
        bowtie_geojson = {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]],
        }
        payload = json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "CPRO": "07",
                            "CUSEC": "0700101001",
                            "CSEC": "001",
                            "TIPO": "SECCION",
                        },
                        "geometry": bowtie_geojson,
                    }
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td)
            capture = _raw_ogc_capture(evidence, "secciones_censales", 2023)
            features, urls, checks, crs = _collect_live_sections(
                source,
                2023,
                provinces,
                lambda _url: payload,
                raw_capture=capture,
            )

            self.assertEqual(len(urls), 1)
            self.assertEqual(checks["sections"], 1)
            self.assertEqual(len(checks["raw_responses"]), 1)
            raw = checks["raw_responses"][0]
            self.assertEqual(raw["province"], "07")
            self.assertEqual(raw["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(raw["bytes"], len(payload))
            self.assertEqual(
                raw["preservation"],
                "exact_response_bytes_before_json_or_geometry_conversion",
            )
            self.assertEqual((evidence / raw["path"]).read_bytes(), payload)

            with self.assertRaisesRegex(
                TerritorialDataError,
                r"GEOMETRY_INVALID.*0700101001.*Self-intersection",
            ):
                _write_shapefile_zip(features, crs=crs)

            self.assertEqual((evidence / raw["path"]).read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
