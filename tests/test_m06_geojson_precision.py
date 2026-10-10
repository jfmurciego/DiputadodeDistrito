"""Regresión M06: un anillo casi degenerado conserva vértices al exportarse en GeoJSON."""
from __future__ import annotations

import ast
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[1]


class M06GeoJSONPrecisionTests(unittest.TestCase):
    def test_diagnostic_version_matches_module_header(self) -> None:
        """Evita atribuir productos nuevos a un predecesor archivado."""
        module_path = ROOT / "modulos" / "06_consolidar_distritos.py"
        syntax = ast.parse(module_path.read_text(encoding="utf-8"))
        header = ast.get_docstring(syntax) or ""
        versions = [
            line.removeprefix("VERSIÓN: ").strip()
            for line in header.splitlines()
            if line.startswith("VERSIÓN: ")
        ]
        self.assertEqual(len(versions), 1)
        diagnostic_dicts = [
            node.value for node in ast.walk(syntax)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "diagnostic" for target in node.targets)
            and isinstance(node.value, ast.Dict)
        ]
        self.assertEqual(len(diagnostic_dicts), 1)
        diagnostic = diagnostic_dicts[0]
        emitted_versions = [
            value.value
            for key, value in zip(diagnostic.keys, diagnostic.values)
            if isinstance(key, ast.Constant) and key.value == "version"
            and isinstance(value, ast.Constant)
        ]
        self.assertEqual(emitted_versions, versions)

    def test_near_coincident_multipart_ring_survives_geojson_roundtrip(self) -> None:
        # Coordenadas del anillo fino representativo del distrito 116 (Madrid).
        shell = [(-4.0, 40.0), (-3.0, 40.0), (-3.0, 41.0), (-4.0, 41.0), (-4.0, 40.0)]
        tiny_hole = [
            (-3.907190520080785, 40.28023225994291),
            (-3.9071905200807855, 40.28023225994291),
            (-3.90778885, 40.27980946),
            (-3.907190520080785, 40.28023225994291),
        ]
        geometry = Polygon(shell, holes=[tiny_hole])
        self.assertTrue(geometry.is_valid)
        source = gpd.GeoDataFrame({"district_id": [116]}, geometry=[geometry], crs="EPSG:4326")

        module_path = ROOT / "modulos" / "06_consolidar_distritos.py"
        spec = importlib.util.spec_from_file_location("ddd_m06_precision_regression", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "precision_regression.geojson.zip"
            module.ensure_geojson_zip(source, path)
            with zipfile.ZipFile(path) as z:
                entries = [entry for entry in z.namelist() if entry.endswith(".geojson")]
                self.assertEqual(len(entries), 1)
                result = gpd.read_file(io.BytesIO(z.read(entries[0])))

        self.assertEqual(len(result), 1)
        self.assertTrue(result.geometry.iloc[0].is_valid)
        self.assertEqual(result.geometry.iloc[0].wkb, geometry.wkb)


if __name__ == "__main__":
    unittest.main()
