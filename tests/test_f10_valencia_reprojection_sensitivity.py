"""Diagnóstico F10: estabilidad de intersección bajo reproyección con densificación.

No modifica el seccionado oficial, la política M02 ni las puertas. 
La segmentización es SOLO una simulación analítica del trazado proyectado.
"""
from __future__ import annotations
import json
from pathlib import Path
import unittest

from pyproj import Transformer
from shapely import segmentize
from shapely.geometry import shape
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "docs/AUDITORIAS/CIERRE_FUENTES_20261017/INE_WFS_VALENCIA_2023_TRES_CUSEC.geojson"

class ValenciaProjectionArtifacts(unittest.TestCase):
    def test_reprojection_vertex_density_sensitivity(self):
        data = json.loads(FILE.read_text(encoding="utf-8"))
        geometry = {f["properties"]["CUSEC"]: shape(f["geometry"]) for f in data["features"]}
        self.assertEqual(set(geometry), {"4617201001", "4619401008", "4619401013"})
        transformer = Transformer.from_crs("EPSG:25830", "EPSG:3035", always_xy=True).transform
        a = geometry["4617201001"]
        for key in ("4619401008", "4619401013"):
            with self.subTest(neighbor=key):
                b = geometry[key]
                self.assertTrue(a.is_valid and b.is_valid)
                self.assertTrue(a.touches(b))
                self.assertEqual(float(a.intersection(b).area), 0.0)
                rows = []
                for step in (None, 1000.0, 500.0, 250.0, 100.0, 50.0):
                    raw_a = a if step is None else segmentize(a, max_segment_length=step)
                    raw_b = b if step is None else segmentize(b, max_segment_length=step)
                    pa = transform(transformer, raw_a)
                    pb = transform(transformer, raw_b)
                    rows.append({"segment_max_m": step,
                                 "overlap_3035_m2": round(float(pa.intersection(pb).area), 9),
                                 "reprojected_touches": bool(pa.touches(pb)),
                                 "a_valid": bool(pa.is_valid), "b_valid": bool(pb.is_valid)})
                print("DDD_F10_VALENCIA_REPROJECTION_DENSIFICATION=" +
                      json.dumps({"pair": ["4617201001",key],
                                  "source_crs": "EPSG:25830",
                                  "test_crs": "EPSG:3035",
                                  "original_source_overlap_m2": 0.0,
                                  "runs": rows}, sort_keys=True))
