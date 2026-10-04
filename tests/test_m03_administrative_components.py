#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regresión M03 para municipios discontinuos acreditados sin aristas ficticias."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import yaml
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location("ddd_m03_admin_components", ROOT / "modulos" / "03_construir_grafo.py")
_M03 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_M03)


class M03AdministrativeComponents(unittest.TestCase):
    def fixture(self, root: Path, *, accredited: bool = True, stale: bool = False):
        geo = root / "m01.geojson"
        edges = root / "m02.jsonl"
        graph = root / "m03.json"
        report = root / "m03_report.json"
        params = root / "params.yaml"

        gdf = gpd.GeoDataFrame(
            {
                "CUSEC_KEY": ["a", "b", "x"],
                "POP_2024": [10, 20, 30],
                "CPRO": ["01", "01", "01"],
                "CUMUN": ["01001", "01001", "01002"],
                "NMUN": ["Discontinuo", "Discontinuo", "Vecino"],
            },
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(3, 0), (4, 0), (4, 1), (3, 1)]),
                Polygon([(1, -1), (3, -1), (3, 2), (1, 2)]),
            ],
            crs="EPSG:3035",
        )
        gdf.to_file(geo, driver="GeoJSON")
        edges.write_text(
            "\n".join([
                json.dumps({"u": "a", "v": "x", "edge_type": "geometric"}),
                json.dumps({"u": "b", "v": "x", "edge_type": "geometric"}),
            ]) + "\n",
            encoding="utf-8",
        )

        package = "d" * 64 if stale else "a" * 64
        validation = {
            "source_baseline": {
                "package_sha256": package,
                "compatibility_identity_sha256": "b" * 64,
            },
            "audit_graph_components": True,
            "audit_admin_level_1_components": True,
            "audit_admin_level_2_components": True,
            "require_one_graph_component_per_province": True,
            "require_connected_municipalities": True,
            "province_field": "CPRO",
            "municipality_field": "CUMUN",
            "municipality_name_field": "NMUN",
        }
        if accredited:
            validation["topology_accreditation"] = {
                "schema": "ddd.topology-accreditation.v1",
                "source_binding": {
                    "edition": "2025",
                    "section_year": 2024,
                    "package_sha256": "a" * 64,
                    "compatibility_identity_sha256": "b" * 64,
                },
                "administrative_components": [{
                    "admin_scope": "municipality:01001",
                    "components": [["a"], ["b"]],
                    "reason": "synthetic source-bound discontinuity",
                    "source": "synthetic official sectioning",
                }],
            }

        cfg = {
            "meta": {"year": 2025, "source_section_year": 2024},
            "modulos": {
                "modulo_03_construir_grafo": {
                    "in_geojson": str(geo),
                    "in_edges_jsonl": str(edges),
                    "id_field": "CUSEC_KEY",
                    "pop_field": "POP_2024",
                    "out_graph_json": str(graph),
                    "out_report": str(report),
                }
            },
            "validation": validation,
        }
        params.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        return params, graph, report

    def invoke(self, params: Path):
        with patch.object(sys, "argv", ["03_construir_grafo.py", "--params", str(params)]):
            _M03.main()

    def test_accredited_discontinuity_preserves_units_population_and_physical_edges(self):
        with tempfile.TemporaryDirectory() as td:
            params, graph_path, report_path = self.fixture(Path(td))
            self.invoke(params)
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(3, report["nodes"])
            self.assertEqual(60, report["total_pop"])
            self.assertEqual(2, report["edges"])
            self.assertEqual(3, len(graph["nodes"]))
            self.assertEqual(60, sum(node["pop"] for node in graph["nodes"]))
            self.assertEqual(2, len(graph["edges"]))
            audit = report["municipality_component_audit"]
            self.assertEqual(1, audit["disconnected"])
            self.assertEqual(1, audit["admitted_disconnected"])
            self.assertEqual(0, audit["unresolved"])
            self.assertEqual(
                [["a"], ["b"]],
                audit["details"]["01/01001"]["component_samples"],
            )

    def test_unknown_discontinuity_still_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            params, _, report_path = self.fixture(Path(td), accredited=False)
            with self.assertRaisesRegex(SystemExit, "sin acreditación vigente"):
                self.invoke(params)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(1, report["municipality_component_audit"]["unresolved"])

    def test_stale_source_binding_blocks_even_when_membership_matches(self):
        with tempfile.TemporaryDirectory() as td:
            params, _, report_path = self.fixture(Path(td), stale=True)
            with self.assertRaisesRegex(SystemExit, "acreditación topológica obsoleta"):
                self.invoke(params)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertFalse(report["topology_accreditation"]["valid"])


if __name__ == "__main__":
    unittest.main()
