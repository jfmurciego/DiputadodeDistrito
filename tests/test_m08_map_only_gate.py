from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"modulos/08_integrar_resultados.py"
spec=importlib.util.spec_from_file_location("m08_integrar_resultados",MODULE)
m08=importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m08)


def _sections():
    return gpd.GeoDataFrame(
        {
            "CUSEC_KEY":["A","B","C"],
            "district_id":[39,39,1],
            "POP_2025":[1200,900,1500],
        },
        geometry=[Point(0,0),Point(1,0),Point(2,0)],
        crs="EPSG:25830",
    )


class MapOnlyPopulationGateTests(unittest.TestCase):
    def test_requires_explicit_population_threshold(self):
        report={"map_only_sections":[{"section_id":"A"},{"section_id":"B"}]}
        with self.assertRaisesRegex(ValueError,"max_map_only_population"):
            m08.derive_declared_missing_districts(
                _sections(),report,
                section_field="CUSEC_KEY",district_field="district_id",
                population_field="POP_2025",max_map_only_population=None,
            )

    def test_blocks_when_declared_population_exceeds_threshold(self):
        report={"map_only_sections":[{"section_id":"A"},{"section_id":"B"}]}
        with self.assertRaisesRegex(ValueError,"2100 > 2000"):
            m08.derive_declared_missing_districts(
                _sections(),report,
                section_field="CUSEC_KEY",district_field="district_id",
                population_field="POP_2025",max_map_only_population=2000,
            )

    def test_can_authorize_only_wholly_declared_district_below_threshold(self):
        report={"map_only_sections":[{"section_id":"A"},{"section_id":"B"}]}
        allowed=m08.derive_declared_missing_districts(
            _sections(),report,
            section_field="CUSEC_KEY",district_field="district_id",
            population_field="POP_2025",max_map_only_population=2200,
        )
        self.assertEqual(allowed,["39"])

    def test_runtime_materializer_does_not_enable_map_only_by_default(self):
        text=(ROOT/"herramientas/materializar_contrato_electoral_runtime.py").read_text(encoding="utf-8")
        self.assertIn('"allow_declared_map_only_districts": False',text)
        self.assertNotIn('"allow_declared_map_only_districts": True',text)


if __name__=="__main__":
    unittest.main()
