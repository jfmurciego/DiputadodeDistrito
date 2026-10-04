from __future__ import annotations

import json
import unittest

import geopandas as gpd
from shapely.geometry import box

from herramientas.adquirir_fuentes_oficiales import _collect_live_sections
from herramientas.compatibilidad_poblacion_seccionado import (
    normalize_geometry_frames,
    reconcile_population_sectioning,
)


def reconcile(population_rows, target_rows, origin_rows=None, *, population_year=2025, section_year=2025):
    return reconcile_population_sectioning(
        territory_id="demo",
        edition="2025",
        population_year=population_year,
        section_year=section_year,
        population_rows=population_rows,
        target_geometry_rows=target_rows,
        origin_geometry_rows=origin_rows,
        input_identities={
            "population": {
                "role": "population",
                "source_id": "population",
                "path": "population.zip",
                "member": "materialized/population.zip",
                "bytes": 1,
                "sha256": "a" * 64,
            },
            "target_sectioning": {
                "role": "target_sectioning",
                "source_id": "sections",
                "path": "target.zip",
                "member": "materialized/target.zip",
                "bytes": 1,
                "sha256": "b" * 64,
            },
            **(
                {
                    "population_sectioning_origin": {
                        "role": "population_sectioning_origin",
                        "source_id": "sections_origin",
                        "path": "origin.zip",
                        "member": "materialized/origin.zip",
                        "bytes": 1,
                        "sha256": "c" * 64,
                    }
                }
                if origin_rows is not None
                else {}
            ),
        },
        crs_audit={
            "target": {"original": "EPSG:4326", "original_wkt": "fixture"},
            "origin": (
                {"original": "EPSG:4326", "original_wkt": "fixture"}
                if origin_rows is not None
                else None
            ),
            "effective": {
                "crs": "EPSG:4326",
                "wkt": "fixture",
                "policy": "target_sectioning_crs",
                "origin_reprojected": False,
            },
        },
        geometry_audits=(
            geometry_audits()
            if origin_rows is not None
            else None
        ),
    )


def geometry_audits(
    *,
    origin_pairs: list[tuple[str, str]] | None = None,
    target_pairs: list[tuple[str, str]] | None = None,
) -> dict:
    origin_pairs = origin_pairs or []
    target_pairs = target_pairs or []
    return {
        "target_sectioning": {
            "derivation": {
                "path": "geometry_normalization/target.json",
                "sha256": "d" * 64,
                "source_id": "target",
                "source_year": 2025,
                "decision": "READY",
            },
            "audit": {
                "normalization_safety": {"decision": "READY"},
                "source_admissibility": {
                    "decision": "READY",
                    "original_overlap_pairs": [
                        {
                            "section_a": left,
                            "section_b": right,
                            "admissible": True,
                            "measurement_crs": "EPSG:3035",
                        }
                        for left, right in target_pairs
                    ],
                },
            },
        },
        "population_sectioning_origin": {
            "derivation": {
                "path": "geometry_normalization/origin.json",
                "sha256": "e" * 64,
                "source_id": "origin",
                "source_year": 2024,
                "decision": "READY",
            },
            "audit": {
                "normalization_safety": {"decision": "READY"},
                "source_admissibility": {
                    "decision": "DEFERRED_TO_CONSUMER_GATE",
                    "original_overlap_pairs": [
                        {
                            "section_a": left,
                            "section_b": right,
                            "relation_geometry_sha256": "f" * 64,
                        }
                        for left, right in origin_pairs
                    ],
                },
            },
        },
    }


class PopulationSectioningCompatibilityTests(unittest.TestCase):
    def test_valid_cross_year_correspondence_requires_geometric_equality(self):
        geom = box(0, 0, 1, 1)
        report = reconcile(
            [("0100101001", 100)],
            [("0100101999", geom)],
            [("0100101001", geom)],
            population_year=2024,
            section_year=2025,
        )
        self.assertEqual(report["decision"], "READY")
        self.assertEqual(report["population"]["input_total"], 100)
        self.assertEqual(report["population"]["assigned_total"], 100)
        self.assertTrue(report["population"]["exact_conservation"])
        self.assertEqual(report["correspondences"][0]["kind"], "ONE_TO_ONE_CODE_CHANGE")

    def test_equivalent_geometries_in_different_crs_are_compared_in_explicit_common_crs(self):
        origin = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"]},
            geometry=[box(-3.8, 40.3, -3.7, 40.4)],
            crs="EPSG:4326",
        )
        target = origin.to_crs("EPSG:3857")
        target_rows, origin_rows, crs = normalize_geometry_frames(
            target_gdf=target,
            target_id_field="CUSEC",
            origin_gdf=origin,
            origin_id_field="CUSEC",
            cross_year=True,
        )
        report = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2024,
            section_year=2025,
            population_rows=[("0100101001", 100)],
            target_geometry_rows=target_rows,
            origin_geometry_rows=origin_rows,
            input_identities={},
            crs_audit=crs,
            geometry_audits=geometry_audits(),
        )
        self.assertEqual(report["decision"], "READY")
        self.assertEqual(report["crs"]["target"]["original"], "EPSG:3857")
        self.assertEqual(report["crs"]["origin"]["original"], "EPSG:4326")
        self.assertEqual(report["crs"]["effective"]["crs"], "EPSG:3857")
        self.assertTrue(report["crs"]["effective"]["origin_reprojected"])

    def test_same_coordinates_with_different_crs_are_not_treated_as_same_place(self):
        origin = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"]},
            geometry=[box(0, 0, 1, 1)],
            crs="EPSG:4326",
        )
        target = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"]},
            geometry=[box(0, 0, 1, 1)],
            crs="EPSG:3857",
        )
        target_rows, origin_rows, crs = normalize_geometry_frames(
            target_gdf=target,
            target_id_field="CUSEC",
            origin_gdf=origin,
            origin_id_field="CUSEC",
            cross_year=True,
        )
        report = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2024,
            section_year=2025,
            population_rows=[("0100101001", 100)],
            target_geometry_rows=target_rows,
            origin_geometry_rows=origin_rows,
            input_identities={},
            crs_audit=crs,
            geometry_audits=geometry_audits(),
        )
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertIn("SAME_CODE_BOUNDARY_CHANGED", report["causes"])

    def test_missing_or_uninterpretable_crs_blocks_before_comparison(self):
        no_crs = gpd.GeoDataFrame(
            {"CUSEC": ["0100101001"]},
            geometry=[box(0, 0, 1, 1)],
        )
        with self.assertRaisesRegex(ValueError, "CRS_MISSING"):
            normalize_geometry_frames(
                target_gdf=no_crs,
                target_id_field="CUSEC",
                origin_gdf=None,
                origin_id_field=None,
                cross_year=False,
            )

        class InvalidCRSFrame:
            crs = "NOT_A_REAL_CRS"

        with self.assertRaisesRegex(ValueError, "CRS_INVALID"):
            normalize_geometry_frames(
                target_gdf=InvalidCRSFrame(),
                target_id_field="CUSEC",
                origin_gdf=None,
                origin_id_field=None,
                cross_year=False,
            )

    def test_cross_year_without_geometry_evidence_fails_closed(self):
        geom = box(0, 0, 1, 1)
        report = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2024,
            section_year=2025,
            population_rows=[("0100101001", 100)],
            target_geometry_rows=[("0100101001", geom)],
            origin_geometry_rows=[("0100101001", geom)],
            input_identities={},
            crs_audit={},
            geometry_audits=None,
        )
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertIn(
            "GEOMETRY_ADMISSIBILITY_EVIDENCE_MISSING",
            report["causes"],
        )
        self.assertEqual(
            report["geometry_admissibility"]["decision"],
            "NOT_EVALUATED",
        )

    def test_same_code_with_changed_boundaries_is_blocked(self):
        report = reconcile(
            [("0100101001", 100)],
            [("0100101001", box(0, 0, 2, 1))],
            [("0100101001", box(0, 0, 1, 1))],
            population_year=2024,
            section_year=2025,
        )
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertIn("SAME_CODE_BOUNDARY_CHANGED", report["causes"])

    def test_disappearance_and_addition_without_geometric_correspondence_block(self):
        report = reconcile(
            [("0100101001", 100)],
            [("0100102001", box(10, 10, 11, 11))],
            [("0100101001", box(0, 0, 1, 1))],
            population_year=2024,
            section_year=2025,
        )
        self.assertIn("UNACCREDITED_SECTIONING_CHANGE", report["causes"])
        self.assertIn("POPULATION_WITHOUT_DESTINATION", report["causes"])

    def test_split_is_detected_geometrically_but_never_used_to_redistribute_population(self):
        report = reconcile(
            [("0100101001", 100)],
            [
                ("0100102001", box(0, 0, 0.5, 1)),
                ("0100102002", box(0.5, 0, 1, 1)),
            ],
            [("0100101001", box(0, 0, 1, 1))],
            population_year=2024,
            section_year=2025,
        )
        self.assertIn("NON_BIJECTIVE_GEOMETRIC_CORRESPONDENCE", report["causes"])
        self.assertTrue(any(x["kind"] == "SPLIT" for x in report["correspondences"]))
        self.assertEqual(report["population"]["assigned_total"], 0)

    def test_fusion_is_detected_geometrically_but_remains_blocked(self):
        report = reconcile(
            [("0100101001", 40), ("0100101002", 60)],
            [("0100102001", box(0, 0, 1, 1))],
            [
                ("0100101001", box(0, 0, 0.5, 1)),
                ("0100101002", box(0.5, 0, 1, 1)),
            ],
            population_year=2024,
            section_year=2025,
        )
        self.assertIn("NON_BIJECTIVE_GEOMETRIC_CORRESPONDENCE", report["causes"])
        self.assertTrue(any(x["kind"] == "FUSION" for x in report["correspondences"]))

    def test_origin_overlap_requires_bound_target_admissibility(self):
        origin_a = box(0, 0, 2, 2)
        origin_b = box(1.5, 0, 3.5, 2)
        target_a = box(0, 0, 2, 2)
        target_b = box(1.5, 0, 3.5, 2)
        report = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2024,
            section_year=2025,
            population_rows=[
                ("0100101001", 40),
                ("0100101002", 60),
            ],
            target_geometry_rows=[
                ("0100102001", target_a),
                ("0100102002", target_b),
            ],
            origin_geometry_rows=[
                ("0100101001", origin_a),
                ("0100101002", origin_b),
            ],
            input_identities={},
            crs_audit={},
            geometry_audits=geometry_audits(
                origin_pairs=[("0100101001", "0100101002")],
                target_pairs=[],
            ),
        )
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertIn(
            "ORIGIN_GEOMETRY_DEFECT_NOT_ADMISSIBLE",
            report["causes"],
        )
        assessment = report["geometry_admissibility"]
        self.assertEqual(assessment["decision"], "BLOCKED")
        self.assertEqual(assessment["original_overlap_pair_count"], 1)
        self.assertFalse(
            assessment["pair_assessments"][0]["target_pair_admissible"]
        )

    def test_origin_overlap_is_admissible_only_when_exact_mapping_binds_to_admissible_target_pair(self):
        origin_a = box(0, 0, 2, 2)
        origin_b = box(1.5, 0, 3.5, 2)
        report = reconcile_population_sectioning(
            territory_id="demo",
            edition="2025",
            population_year=2024,
            section_year=2025,
            population_rows=[
                ("0100101001", 40),
                ("0100101002", 60),
            ],
            target_geometry_rows=[
                ("0100102001", origin_a),
                ("0100102002", origin_b),
            ],
            origin_geometry_rows=[
                ("0100101001", origin_a),
                ("0100101002", origin_b),
            ],
            input_identities={},
            crs_audit={},
            geometry_audits=geometry_audits(
                origin_pairs=[("0100101001", "0100101002")],
                target_pairs=[("0100102001", "0100102002")],
            ),
        )
        self.assertEqual(report["decision"], "READY")
        assessment = report["geometry_admissibility"]
        self.assertEqual(assessment["decision"], "READY")
        pair = assessment["pair_assessments"][0]
        self.assertTrue(pair["source_geometries_equal_destinations"])
        self.assertTrue(pair["overlap_relation_equal_after_mapping"])
        self.assertTrue(pair["target_pair_admissible"])
        self.assertTrue(pair["admissible"])

    def test_live_geometric_duplicate_is_rejected_before_deduplication(self):
        source = {
            "kind": "ogc_features",
            "crs": "EPSG:4326",
            "endpoint_template": "https://example.invalid/{edition}",
            "territorial_filter_field": "CPRO",
            "section_id_field": "CUSEC",
        }
        payload = json.dumps({
            "features": [
                {"properties": {"CPRO": "01", "CUSEC": "0100101001", "TIPO": "SECCION", "CSEC": "001"}},
                {"properties": {"CPRO": "01", "CUSEC": "01 001 01 001", "TIPO": "SECCION", "CSEC": "001"}},
            ]
        }).encode("utf-8")
        with self.assertRaisesRegex(ValueError, "Clave geométrica duplicada antes de materializar"):
            _collect_live_sections(
                source,
                2025,
                [{"code": "01", "business_name": "Demo"}],
                lambda _url: payload,
            )

    def test_duplicate_population_key_blocks_before_any_overwrite(self):
        geom = box(0, 0, 1, 1)
        report = reconcile(
            [("0100101001", 40), ("0100101001", 60)],
            [("0100101001", geom)],
        )
        self.assertIn("DUPLICATE_POPULATION_KEYS", report["causes"])

    def test_duplicate_geometry_key_blocks(self):
        geom = box(0, 0, 1, 1)
        report = reconcile(
            [("0100101001", 100)],
            [("0100101001", geom), ("0100101001", geom)],
        )
        self.assertIn("DUPLICATE_TARGET_GEOMETRY_KEYS", report["causes"])

    def test_population_without_destination_and_geometry_without_population_block(self):
        report = reconcile(
            [("0100101001", 100)],
            [
                ("0100101001", box(0, 0, 1, 1)),
                ("0100101002", box(1, 0, 2, 1)),
            ],
        )
        self.assertIn("GEOMETRY_WITHOUT_POPULATION", report["causes"])
        self.assertIn("TARGET_GEOMETRY_WITHOUT_POPULATION", report["causes"])

    def test_exact_total_conservation_is_mandatory(self):
        report = reconcile(
            [("0100101001", 100), ("0100101002", 50)],
            [("0100101001", box(0, 0, 1, 1))],
        )
        self.assertFalse(report["population"]["exact_conservation"])
        self.assertEqual(report["population"]["input_total"], 150)
        self.assertEqual(report["population"]["assigned_total"], 100)
        self.assertIn("POPULATION_TOTAL_NOT_CONSERVED", report["causes"])


if __name__ == "__main__":
    unittest.main()
