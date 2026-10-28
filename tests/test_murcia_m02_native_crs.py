"""Regresión M02 Murcia, versión 1.0.0, 2026-10-26.

Alcance: frontera oficial Yecla–Jumilla de run 40241734290.
Estado: candidato. Origen: fixture exacto M01, sin predecesor.
Motivo: conservar fronteras lineales sin falsos solapes de reproyección.
"""
import importlib.util
import json
from pathlib import Path
import unittest

import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "territorios/region_de_murcia/config/region_de_murcia_2025.yaml"
FIXTURE = ROOT / "tests/fixtures/murcia_m02_native_crs/source_touch_pairs_2023.geojson"
SPEC = importlib.util.spec_from_file_location("m02_murcia", ROOT / "modulos/02_construir_adyacencias.py")
M02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M02)
PAIRS = {("3002202001", "3004301008"), ("3002202001", "3004301031")}


class MurciaM02NativeCrsTests(unittest.TestCase):
    def test_source_frontier_survives_metric_projection_without_relaxation(self):
        config = yaml.safe_load(CONFIG.read_text())
        m02 = config["modulos"]["modulo_02_construir_adyacencias"]
        self.assertEqual(config["meta"]["source_section_year"], 2023)
        self.assertEqual(m02["working_crs"], "EPSG:25830")
        self.assertEqual(m02["min_shared_border_m"], 1.0)
        self.assertEqual(m02["max_precision_overlap_area_m2"], 1.0)
        self.assertEqual(m02["buffer_m"], 0.0)
        self.assertEqual(m02["simplify_m"], 0.0)
        gdf = gpd.read_file(FIXTURE)
        original = gdf.set_index("CUSEC_KEY")
        for left, right in PAIRS:
            self.assertTrue(original.loc[left].geometry.touches(original.loc[right].geometry))
        def edges(crs):
            return set(M02.iter_edges(gdf, "CUSEC_KEY", "contact", 1.0, 1.0, 0.0, 0.0, 0, 0, crs))
        self.assertTrue(PAIRS.isdisjoint(edges("EPSG:3035")))
        self.assertTrue(PAIRS <= edges(m02["working_crs"]))
        metric = gdf.to_crs(m02["working_crs"]).set_index("CUSEC_KEY")
        for left, right in PAIRS:
            a, b = metric.loc[left].geometry, metric.loc[right].geometry
            self.assertTrue(a.touches(b))
            self.assertEqual(a.intersection(b).area, 0.0)
            self.assertGreaterEqual(a.boundary.intersection(b.boundary).length, 1.0)


if __name__ == "__main__":
    unittest.main()
