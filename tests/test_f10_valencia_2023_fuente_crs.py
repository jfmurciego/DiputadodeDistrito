"""Control F10 acotado: dos contactos oficiales INE 2023 en CRS nativo.

Solo tres geometrías WFS oficialmente preservadas; no certifica universo 3503,
ni crea receipt ni modifica el contrato M02.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from shapely.geometry import shape
from pyproj import Transformer
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/AUDITORIAS/CIERRE_FUENTES_20261017/INE_WFS_VALENCIA_2023_TRES_CUSEC.geojson"


class Valencia2023OfficialPairCrsTests(unittest.TestCase):
    def test_two_2023_source_contacts_not_overlaps_in_native_crs(self):
        payload = json.loads(SOURCE.read_text(encoding="utf-8"))
        self.assertEqual(payload["crs"]["properties"]["name"], "urn:ogc:def:crs:EPSG::25830")
        geometries = {f["properties"]["CUSEC"]: shape(f["geometry"])
                      for f in payload["features"]}
        self.assertEqual(set(geometries), {"4617201001", "4619401008", "4619401013"})
        reference = geometries["4617201001"]
        self.assertTrue(reference.is_valid)
        projected = Transformer.from_crs("EPSG:25830", "EPSG:3035", always_xy=True).transform
        for code in ("4619401008", "4619401013"):
            with self.subTest(code=code):
                neighbor = geometries[code]
                self.assertTrue(neighbor.is_valid)
                self.assertTrue(reference.touches(neighbor))
                self.assertEqual(reference.intersection(neighbor).area, 0.0)
                # Comparison only: EPSG:3035 creates a precision artefact.
                overlap_3035 = transform(projected, reference).intersection(
                    transform(projected, neighbor)).area
                self.assertGreater(overlap_3035, 1.0)
