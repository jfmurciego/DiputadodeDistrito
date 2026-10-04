#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas sintéticas reutilizables del preflight topológico territorial."""
import json
import sys
import tempfile
import unittest
import importlib.util
from pathlib import Path
from unittest.mock import patch

import geopandas as gpd
import yaml
from shapely.geometry import Polygon

from ddd_core.topology_preflight import evaluate_topology_preflight, validate_topology_accreditation_binding
from ddd_core.config import load_params_yaml
from herramientas._resolver_ejecucion_completa_core import _contract_generation_binding


_M02_SPEC = importlib.util.spec_from_file_location("ddd_m02", Path(__file__).resolve().parents[1] / "modulos" / "02_construir_adyacencias.py")
_M02 = importlib.util.module_from_spec(_M02_SPEC)
_M02_SPEC.loader.exec_module(_M02)
_relation_ok = _M02._relation_ok
ROOT = Path(__file__).resolve().parents[1]


def unit(province="01", municipality="001", multipart=False):
    return {"province": province, "municipality": municipality, "multipart": multipart}


def administrative_components(municipality, components, **extra):
    data = {
        "admin_scope": f"municipality:{municipality}",
        "components": components,
        "reason": "synthetic accredited administrative discontinuity",
        "source": "synthetic source edition",
    }
    data.update(extra)
    return data


def bridge(u, v, **extra):
    data = {
        "u": u,
        "v": v,
        "admin_scope": "province:01",
        "edge_type": "administrative_exclave",
        "reason": "synthetic diagnosed disconnection",
        "source": "synthetic fixture",
    }
    data.update(extra)
    return data


class TopologyPreflightSyntheticCases(unittest.TestCase):
    def run_case(self, units, contacts, bridges=None, threshold=1.0, components=None, accreditation_error=None):
        return evaluate_topology_preflight(
            units=units,
            contacts=contacts,
            bridges=bridges or [],
            min_shared_border_m=threshold,
            productive_continental=True,
            administrative_components=components or [],
            accreditation_error=accreditation_error,
        )

    def test_01_point_contact(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 0.0}],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertEqual(1, len(r["point_contacts_removed"]))

    def test_02_border_below_threshold(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 0.5}],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertEqual(1, len(r["edges_below_threshold"]))

    def test_03_enclave_or_exclave_without_policy(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002"), "c": unit(municipality="003")},
            [{"u": "a", "v": "b", "shared_border_m": 10.0}],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertIn("c", r["isolated_sections"])

    def test_04_multipart_section(self):
        r = self.run_case(
            {"a": unit(multipart=True), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 10.0}],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(["a"], r["multipart_sections"])

    def test_05_valid_bridge(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [],
            [bridge("a", "b")],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(1, len(r["bridges"]["accepted"]))

    def test_06_missing_endpoint(self):
        r = self.run_case(
            {"a": unit()},
            [],
            [bridge("a", "missing")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertEqual(1, len(r["bridges"]["rejected"]))

    def test_07_cross_province_bridge(self):
        r = self.run_case(
            {"a": unit(province="01"), "b": unit(province="02", municipality="002")},
            [],
            [bridge("a", "b")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("declared scope", r["bridges"]["rejected"][0]["rejection_reason"])

    def test_08_unnecessary_bridge(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002")},
            [{"u": "a", "v": "b", "shared_border_m": 10.0}],
            [bridge("a", "b")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("does not resolve", r["bridges"]["rejected"][0]["rejection_reason"])

    def test_09_unresolved_disconnection(self):
        r = self.run_case(
            {"a": unit(), "b": unit(municipality="002"), "c": unit(municipality="003")},
            [],
            [bridge("a", "b")],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertEqual(2, len(r["components"]["territorial_operational"]))

    def test_10_province_bridge_ignores_path_through_other_province(self):
        r = self.run_case(
            {
                "a": unit(province="01", municipality="001"),
                "b": unit(province="01", municipality="002"),
                "x": unit(province="02", municipality="003"),
            },
            [
                {"u": "a", "v": "x", "shared_border_m": 10.0},
                {"u": "x", "v": "b", "shared_border_m": 10.0},
            ],
            [bridge("a", "b", admin_scope="province:01")],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(1, len(r["bridges"]["accepted"]))
        self.assertEqual([], r["bridges"]["rejected"])

    def test_11_province_scope_code_must_match_endpoints(self):
        r = self.run_case(
            {"a": unit(province="01"), "b": unit(province="01", municipality="002")},
            [],
            [bridge("a", "b", admin_scope="province:02")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("declared scope province:02", r["bridges"]["rejected"][0]["rejection_reason"])

    def test_12_municipality_scope_requires_same_municipality(self):
        r = self.run_case(
            {
                "a": unit(province="01", municipality="00001"),
                "b": unit(province="01", municipality="00002"),
            },
            [],
            [bridge("a", "b", admin_scope="municipality:00001")],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("declared scope municipality:00001", r["bridges"]["rejected"][0]["rejection_reason"])

    def test_13_connected_municipality_needs_no_exception(self):
        r = self.run_case(
            {"a": unit(municipality="00001"), "b": unit(municipality="00001")},
            [{"u": "a", "v": "b", "shared_border_m": 12.0}],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual([], r["administrative_components"]["accepted"])

    def test_14_accredited_discontinuous_municipality_keeps_physical_graph(self):
        units = {
            "a": unit(municipality="00001"),
            "b": unit(municipality="00001"),
            "x": unit(municipality="00002"),
        }
        contacts = [
            {"u": "a", "v": "x", "shared_border_m": 8.0},
            {"u": "b", "v": "x", "shared_border_m": 9.0},
        ]
        r = self.run_case(
            units,
            contacts,
            components=[administrative_components("00001", [["a"], ["b"]])],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(2, r["physical_edges"])
        self.assertEqual(2, r["operational_edges"])
        self.assertEqual([["a"], ["b"]], r["components"]["municipal"]["00001"])
        self.assertEqual(1, len(r["administrative_components"]["accepted"]))

    def test_15_unknown_discontinuous_municipality_remains_needs_policy(self):
        r = self.run_case(
            {
                "a": unit(municipality="00001"),
                "b": unit(municipality="00001"),
                "x": unit(municipality="00002"),
            },
            [
                {"u": "a", "v": "x", "shared_border_m": 8.0},
                {"u": "b", "v": "x", "shared_border_m": 9.0},
            ],
        )
        self.assertEqual("NEEDS_POLICY", r["decision"])
        self.assertIn("00001", r["reasons"][0])

    def test_16_point_contact_can_be_accredited_but_never_becomes_edge(self):
        r = self.run_case(
            {
                "a": unit(municipality="00001"),
                "b": unit(municipality="00001"),
                "x": unit(municipality="00002"),
            },
            [
                {"u": "a", "v": "b", "shared_border_m": 0.0},
                {"u": "a", "v": "x", "shared_border_m": 8.0},
                {"u": "b", "v": "x", "shared_border_m": 9.0},
            ],
            components=[administrative_components("00001", [["a"], ["b"]])],
        )
        self.assertEqual("READY", r["decision"])
        self.assertEqual(1, len(r["point_contacts_removed"]))
        self.assertEqual(2, r["operational_edges"])

    def test_17_component_declaration_is_stale_when_connectivity_changes(self):
        r = self.run_case(
            {"a": unit(municipality="00001"), "b": unit(municipality="00001")},
            [{"u": "a", "v": "b", "shared_border_m": 12.0}],
            components=[administrative_components("00001", [["a"], ["b"]])],
        )
        self.assertEqual("BLOCKED", r["decision"])
        self.assertIn("no longer match observed topology", r["administrative_components"]["rejected"][0]["rejection_reason"])

    def test_18_source_bound_accreditation_becomes_stale_after_source_change(self):
        cfg = {
            "meta": {"year": 2025, "source_section_year": 2024},
            "validation": {
                "source_baseline": {
                    "package_sha256": "b" * 64,
                    "compatibility_identity_sha256": "c" * 64,
                },
                "topology_accreditation": {
                    "schema": "ddd.topology-accreditation.v1",
                    "source_binding": {
                        "edition": "2025",
                        "section_year": 2024,
                        "package_sha256": "a" * 64,
                        "compatibility_identity_sha256": "c" * 64,
                    },
                },
            },
        }
        r = validate_topology_accreditation_binding(cfg)
        self.assertTrue(r["present"])
        self.assertFalse(r["valid"])
        self.assertIn("package_sha256", r["reason"])

    def test_19_real_catalonia_accreditation_survives_config_loader_verbatim(self):
        cfg = load_params_yaml(str(ROOT / "territorios/cataluna/config/cataluna_2025.yaml"))
        accreditation = cfg["validation"]["topology_accreditation"]
        self.assertEqual("ddd.topology-accreditation.v1", accreditation["schema"])
        declaration = accreditation["administrative_components"][0]
        self.assertEqual("municipality:25234", declaration["admin_scope"])
        self.assertTrue(declaration["reason"].startswith("El seccionado oficial 2024"))
        self.assertTrue(declaration["source"].startswith("ddd-source-package-cataluna-2025-37215025861"))
        evidence = declaration["evidence"]
        self.assertEqual("Divisions administratives", evidence["administrative_dataset"]["dataset"])
        self.assertEqual("v2.2", evidence["administrative_dataset"]["specification"])
        self.assertEqual("2026-01-20", evidence["administrative_dataset"]["data_date"])
        correspondence = evidence["section_correspondence"]
        self.assertEqual("2523403001", correspondence["section"])
        self.assertEqual("Puigcercós", correspondence["official_enclave"])
        self.assertEqual(1.59, correspondence["official_area_km2"])
        self.assertAlmostEqual(1.5834613860534748, correspondence["matched_part_area_km2_epsg3035"], places=12)

    def test_20_generation_binding_carries_topology_accreditation(self):
        cfg = {
            "meta": {"year": 2025},
            "territory_contract": {},
            "modulos": {},
            "validation": {
                "source_baseline": {"package_sha256": "a" * 64},
                "topology_accreditation": {
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
                        "reason": "synthetic",
                        "source": "synthetic",
                    }],
                },
            },
        }
        before = json.loads(json.dumps(_contract_generation_binding(cfg)))
        cfg["validation"]["topology_accreditation"]["administrative_components"][0]["components"] = [["a", "b"], ["c"]]
        after = _contract_generation_binding(cfg)
        self.assertIn("topology_accreditation", before)
        self.assertNotEqual(before["topology_accreditation"], after["topology_accreditation"])


class M02ContractInputCases(unittest.TestCase):
    def _write_two_section_geojson(self, path: Path, *, same_province: bool = True) -> None:
        gdf = gpd.GeoDataFrame(
            {
                "CUSEC_KEY": ["a", "b"],
                "CPRO": ["01", "01" if same_province else "02"],
                "CUMUN": ["01001", "01002" if same_province else "02001"],
            },
            geometry=[
                Polygon([(0, 0), (0.01, 0), (0.01, 0.01), (0, 0.01)]),
                Polygon([(0.03, 0), (0.04, 0), (0.04, 0.01), (0.03, 0.01)]),
            ],
            crs="EPSG:4326",
        )
        gdf.to_file(path, driver="GeoJSON")

    def test_archipelago_contracts_run_m02_from_source_fields_before_ddd_partitions_exist(self):
        for territory_id in ("illes_balears", "canarias"):
            with self.subTest(territory=territory_id), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                source = root / "m01.geojson"
                edges = root / "m02.jsonl"
                self._write_two_section_geojson(source)

                cfg = yaml.safe_load(
                    (ROOT / f"territorios/{territory_id}/config/{territory_id}_2025.yaml").read_text(
                        encoding="utf-8"
                    )
                )
                s2 = cfg["modulos"]["modulo_02_construir_adyacencias"]
                self.assertEqual("CPRO", s2["bridge_admin_level_1_field"])
                self.assertEqual("CUMUN", s2["bridge_admin_level_2_field"])
                self.assertEqual("DDD_PARTITION", cfg["validation"]["province_field"])
                self.assertEqual("DDD_MUNICIPALITY_PARTITION", cfg["validation"]["municipality_field"])

                s2["in_geojson"] = str(source)
                s2["out_edges_jsonl"] = str(edges)
                params = root / "params.yaml"
                params.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

                with patch.object(sys, "argv", ["02_construir_adyacencias.py", "--params", str(params)]):
                    _M02.main()
                self.assertTrue(edges.is_file())

    def test_declared_bridge_still_passes_through_m02_validation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "m01.geojson"
            edges = root / "m02.jsonl"
            self._write_two_section_geojson(source)
            cfg = {
                "meta": {"contract_level": "production_m01_m06"},
                "territory_contract": {"topology_mode": "land"},
                "modulos": {
                    "modulo_02_construir_adyacencias": {
                        "in_geojson": str(source),
                        "id_field": "CUSEC_KEY",
                        "out_edges_jsonl": str(edges),
                        "predicate": "contact",
                        "working_crs": "EPSG:3035",
                        "min_shared_border_m": 1.0,
                        "max_precision_overlap_area_m2": 1.0,
                        "buffer_m": 0.0,
                        "simplify_m": 0.0,
                        "max_candidates": 0,
                        "log_every": 10000,
                        "topology_bridges": [bridge("a", "b")],
                        "bridge_admin_level_1_field": "CPRO",
                        "bridge_admin_level_2_field": "CUMUN",
                    },
                    "modulo_04_generar_semillas": {
                        "province_field": "DDD_PARTITION",
                        "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                    },
                },
                "validation": {
                    "province_field": "DDD_PARTITION",
                    "municipality_field": "DDD_MUNICIPALITY_PARTITION",
                },
            }
            params = root / "params.yaml"
            params.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
            with patch.object(sys, "argv", ["02_construir_adyacencias.py", "--params", str(params)]):
                _M02.main()
            rows = [json.loads(line) for line in edges.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(1, len(rows))
            self.assertEqual("administrative_exclave", rows[0]["edge_type"])

class ContactPredicateSyntheticCases(unittest.TestCase):
    def test_micro_overlap_with_shared_border_is_edge(self):
        a=Polygon([(0,0),(10,0),(10,10),(0,10)])
        # Comparte 9 m de borde, pero una cuña de 0,005 m² invade A: no es touches.
        b=Polygon([(10,0),(20,0),(20,10),(10,10),(10,6),(9.99,5.5),(10,5),(10,0)])
        self.assertFalse(a.touches(b))
        self.assertGreaterEqual(a.boundary.intersection(b.boundary).length,1.0)
        self.assertLess(a.intersection(b).area,1.0)
        self.assertTrue(_relation_ok(a,b,"contact",1.0,1.0))

    def test_overlap_above_precision_budget_is_rejected(self):
        a=Polygon([(0,0),(10,0),(10,10),(0,10)]); b=Polygon([(9,0),(20,0),(20,10),(9,10)])
        self.assertFalse(_relation_ok(a,b,"contact",1.0,1.0))

    def test_point_contact_is_rejected(self):
        a=Polygon([(0,0),(10,0),(10,10),(0,10)]); b=Polygon([(10,10),(20,10),(20,20),(10,20)])
        self.assertFalse(_relation_ok(a,b,"contact",1.0,1.0))

    def test_shared_border_below_one_metre_is_rejected(self):
        a=Polygon([(0,0),(10,0),(10,10),(0,10)]); b=Polygon([(10,9.5),(20,9.5),(20,10),(10,10)])
        self.assertFalse(_relation_ok(a,b,"contact",1.0,1.0))


if __name__ == "__main__":
    unittest.main()
