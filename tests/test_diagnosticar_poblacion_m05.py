"""Versión 1.0.0; 2026-10-29; candidato. Diagnóstico de distritos fuera de límites tras fallar M04/M05.
Origen: nuevo, sin predecesor.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

try:
    import geopandas as gpd
    from shapely.geometry import Point
except ImportError:  # pragma: no cover
    gpd = None


@unittest.skipIf(gpd is None, "geopandas requerido")
class DiagnosticoPoblacionTests(unittest.TestCase):
    def test_lists_only_districts_outside_floor_or_cap_and_respects_exemptions(self):
        from herramientas.diagnosticar_poblacion_m05 import diagnose
        with tempfile.TemporaryDirectory() as td:
            cache = Path(td) / "cache"
            cache.mkdir()
            gdf = gpd.GeoDataFrame(
                {"CUSEC_KEY": ["a", "b", "c", "d", "e"], "POP": [100, 100, 10, 190, 5],
                 "district_id": [1, 1, 2, 3, 4], "CPRO": ["01", "01", "02", "01", "03"],
                 "CUMUN": ["01001"] * 5},
                geometry=[Point(i, 0) for i in range(5)], crs="EPSG:25830")
            gdf.to_file(cache / "x_m05_distritos_optimizados.geojson", driver="GeoJSON")
            cfg = {"meta": {"territory_id": "demo", "run_name": "demo", "year": 2025},
                   "territory_contract": {"k_districts": 4},
                   "validation": {"population_floor_ratio": 0.8, "population_cap_ratio": 1.75,
                                  "population_floor_exempt_partitions": ["03"]},
                   "modulos": {"modulo_05_optimizar_distritos": {
                       "in_geojson": str(cache / "seeds.geojson"), "pop_field": "POP",
                       "district_field": "district_id", "province_field": "CPRO",
                       "municipality_field": "CUMUN"}}}
            params = Path(td) / "p.yaml"
            params.write_text(yaml.safe_dump(cfg), encoding="utf-8")
            report = diagnose(params)
            self.assertEqual("M05", report["stage"])
            found = {r["district"]: r["violation"] for r in report["violations"]}
            # objetivo 101,25: suelo 81, techo 177,2; el distrito 4 (5 hab.) está en partición exenta.
            self.assertEqual({"1": "ABOVE_CAP", "2": "BELOW_FLOOR", "3": "ABOVE_CAP"}, found)


if __name__ == "__main__":
    unittest.main()
