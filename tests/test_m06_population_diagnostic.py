from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import geopandas as gpd
import yaml
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]


def write_input(path: Path, populations):
    rows = len(populations)
    gdf = gpd.GeoDataFrame(
        {
            "CUSEC_KEY": [f"01001010{i:02d}" for i in range(rows)],
            "district_id": list(range(1, rows + 1)),
            "POP_2025": populations,
            "CPRO": ["01"] * rows,
            "NPRO": ["Sintética"] * rows,
            "CUMUN": [f"0100{i}" for i in range(rows)],
            "NMUN": [f"M{i}" for i in range(rows)],
            "CUDIS": ["01"] * rows,
            "ddd_unit_id": [f"u{i}" for i in range(rows)],
            "ddd_closed_urban": [False] * rows,
        },
        geometry=[box(i, 0, i + 0.9, 0.9) for i in range(rows)],
        crs="EPSG:4326",
    )
    tmp = path.with_suffix("")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(tmp, arcname="input.geojson")
    tmp.unlink()


def config(root: Path, input_path: Path):
    return {
        "meta": {"run_name": "m06-population", "year": 2025},
        "io": {"project_root": {"path": str(root)}},
        "modulos": {
            "modulo_06_consolidar_distritos": {
                "in_geojson": str(input_path),
                "id_field": "CUSEC_KEY",
                "district_field": "district_id",
                "pop_field": "POP_2025",
                "province_field": "CPRO",
                "province_name_field": "NPRO",
                "municipality_field": "CUMUN",
                "municipality_name_field": "NMUN",
                "cudis_field": "CUDIS",
                "metric_crs": "EPSG:3035",
                "expected_districts": 2,
                "strict_expected_k": True,
                "out_summary_csv": str(root / "summary.csv"),
                "out_catalog_csv": str(root / "catalog.csv"),
                "out_composition_csv": str(root / "composition.csv"),
                "out_geojson": str(root / "sections.geojson.zip"),
                "out_district_geojson": str(root / "districts.geojson.zip"),
                "out_diagnostic_json": str(root / "diagnostic.json"),
            }
        },
        "validation": {
            "expected_districts": 2,
            "population_floor_ratio": 0.50,
            "population_cap_ratio": 1.50,
            "target_tolerance_ratio": 0.10,
            "province_districts": {"01": 2},
            "province_field": "CPRO",
            "municipality_field": "CUMUN",
            "require_single_province_per_district": True,
        },
    }


class M06PopulationDiagnosticTests(unittest.TestCase):
    def run_m06(self, populations):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        input_path = root / "m05.geojson.zip"
        write_input(input_path, populations)
        params = root / "params.yaml"
        params.write_text(yaml.safe_dump(config(root, input_path), sort_keys=False), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(ROOT / "modulos/06_consolidar_distritos.py"), "--params", str(params)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        return td, root, completed

    def test_nonconforming_population_still_writes_complete_m06_and_diagnostic(self):
        td, root, completed = self.run_m06([40, 160])
        try:
            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertTrue((root / "districts.geojson.zip").is_file())
            self.assertTrue((root / "sections.geojson.zip").is_file())
            self.assertTrue((root / "summary.csv").is_file())
            diagnostic = json.loads((root / "diagnostic.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["structural_status"], "PASS")
            self.assertEqual(diagnostic["population_conformance"], "NON_CONFORMING")
            self.assertFalse(diagnostic["conformance_declared"])
            self.assertEqual(diagnostic["hard_population_violations"], 2)
            self.assertEqual(
                {row["population_status"] for row in diagnostic["violations"]},
                {"BELOW_FLOOR", "ABOVE_CEILING"},
            )
        finally:
            td.cleanup()

    def test_conforming_population_is_declared_conforming(self):
        td, root, completed = self.run_m06([100, 100])
        try:
            self.assertEqual(completed.returncode, 0, completed.stdout)
            diagnostic = json.loads((root / "diagnostic.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["population_conformance"], "PASS")
            self.assertTrue(diagnostic["conformance_declared"])
            self.assertEqual(diagnostic["hard_population_violations"], 0)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
