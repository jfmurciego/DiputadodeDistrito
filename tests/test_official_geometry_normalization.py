from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box, mapping, shape

from ddd_core.official_geometry import (
    _classify_spatial_change,
    _pairwise_topology_evidence,
    normalize_official_features,
    normalize_official_geometry,
    persist_geometry_normalization_evidence,
    persist_raw_ogc_response,
)
from herramientas.adquirir_fuentes_oficiales import (
    _geometry_declared_use,
    _materialize_sections_with_evidence,
    _normalize_sections_or_block,
    _write_shapefile_zip,
)


ROOT = Path(__file__).resolve().parents[1]


def target_use(
    *,
    crs: str = "EPSG:3035",
    min_shared: float = 1.0,
    max_overlap: float = 1.0,
) -> dict:
    return {
        "role": "target_sectioning",
        "consumer": "modulo_02_construir_adyacencias",
        "adjacency": {
            "predicate": "contact",
            "working_crs": crs,
            "min_shared_border_m": min_shared,
            "max_precision_overlap_area_m2": max_overlap,
        },
    }


class OfficialGeometryNormalizationTests(unittest.TestCase):
    def test_valid_geometry_is_unchanged(self):
        geom = box(0, 0, 1, 1)
        candidate, audit = normalize_official_geometry("0100101001", geom)
        self.assertEqual(audit["status"], "UNCHANGED")
        self.assertEqual(
            audit["before"]["geometry_sha256"],
            audit["after"]["geometry_sha256"],
        )
        self.assertTrue(candidate.equals_exact(geom, 0.0))

    def test_valid_nonpolygonal_point_and_line_are_explicit_individual_issues(self):
        features = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101007", "CPRO": "01"},
                "geometry": mapping(Point(0, 0)),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101008", "CPRO": "01"},
                "geometry": mapping(LineString([(0, 0), (1, 1)])),
            },
        ]

        _, report = normalize_official_features(
            features,
            "CUSEC",
            crs="EPSG:4326",
            coverage_field="CPRO",
        )

        self.assertEqual(report["decision"], "BLOCKED")
        self.assertEqual(report["blocked"], 2)
        self.assertEqual(len(report["issues"]), 2)
        by_id = {
            issue["before"]["section_id"]: issue
            for issue in report["issues"]
        }
        self.assertEqual(
            by_id["0100101007"]["before"]["geometry_type"],
            "Point",
        )
        self.assertEqual(
            by_id["0100101008"]["before"]["geometry_type"],
            "LineString",
        )
        for section_id in ("0100101007", "0100101008"):
            issue = by_id[section_id]
            self.assertEqual(issue["status"], "BLOCKED")
            self.assertEqual(issue["reason"], "NON_POLYGONAL_GEOMETRY")
            self.assertEqual(issue["before"]["crs"], "EPSG:4326")
            self.assertEqual(
                issue["before"]["stage"],
                "RAW_SOURCE_FEATURE_AFTER_JSON_DECODE_BEFORE_GEOMETRY_TRANSFORMATION",
            )
            self.assertTrue(issue["before"]["geometry_sha256"])
            self.assertEqual(
                issue["before"]["validity_reason"],
                "Valid Geometry",
            )

    def test_exact_duplicate_multipolygon_component_has_exact_proof(self):
        part = box(0, 0, 1, 1)
        raw = MultiPolygon([part, part])
        self.assertFalse(raw.is_valid)

        candidate, audit = normalize_official_geometry("0100101001", raw)

        self.assertEqual(audit["status"], "NORMALIZED")
        self.assertEqual(
            audit["method"],
            "DEDUPLICATE_EXACT_MULTIPOLYGON_COMPONENTS",
        )
        self.assertEqual(audit["before_component_count"], 2)
        self.assertEqual(audit["after_component_count"], 1)
        self.assertTrue(audit["proof"]["point_set_equal"])
        self.assertTrue(audit["proof"]["boundary_set_equal"])
        self.assertTrue(audit["proof"]["symmetric_difference_empty"])
        self.assertEqual(audit["proof"]["symmetric_difference_area"], 0.0)
        self.assertIsNone(audit["proof"]["tolerance"])
        self.assertTrue(candidate.is_valid)

    def test_exact_duplicate_hole_has_exact_proof(self):
        shell = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        hole = [(2, 2), (4, 2), (4, 4), (2, 4), (2, 2)]
        raw = Polygon(shell, [hole, hole])
        self.assertFalse(raw.is_valid)

        candidate, audit = normalize_official_geometry("0100101002", raw)

        self.assertEqual(audit["status"], "NORMALIZED")
        self.assertEqual(
            audit["method"],
            "DEDUPLICATE_EXACT_INTERIOR_RINGS",
        )
        self.assertEqual(audit["before_hole_count"], 2)
        self.assertEqual(audit["after_hole_count"], 1)
        self.assertTrue(audit["proof"]["point_set_equal"])
        self.assertTrue(audit["proof"]["boundary_set_equal"])
        self.assertEqual(audit["proof"]["symmetric_difference_area"], 0.0)
        self.assertTrue(candidate.is_valid)
        self.assertEqual(
            audit["raw_polygon_area_comparison"]["status"],
            "NOT_USED_FOR_ACCEPTANCE",
        )

    def test_self_intersection_requires_dual_consensus_and_boundary_preservation(self):
        bowtie = Polygon(
            [(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]
        )
        candidate, audit = normalize_official_geometry(
            "0100101003",
            bowtie,
        )

        self.assertEqual(audit["status"], "NORMALIZED")
        self.assertEqual(
            audit["method"],
            "MAKE_VALID_DUAL_CONSENSUS_BOUNDARY_PRESERVING",
        )
        self.assertTrue(audit["independent_candidate_equal"])
        self.assertTrue(audit["source_boundary_set_equal"])
        self.assertTrue(audit["candidate_symmetric_difference_empty"])
        self.assertEqual(
            audit["candidate_symmetric_difference_area_source_units"],
            0.0,
        )
        self.assertTrue(candidate.is_valid)
        self.assertIn(candidate.geom_type, {"Polygon", "MultiPolygon"})
        self.assertEqual(
            audit["raw_polygon_area_comparison"]["status"],
            "NOT_USED_FOR_ACCEPTANCE",
        )

    def test_overlapping_multipolygon_blocks_when_repair_algorithms_disagree(self):
        raw = MultiPolygon(
            [box(0, 0, 2, 2), box(1, 1, 3, 3)]
        )
        self.assertFalse(raw.is_valid)

        candidate, audit = normalize_official_geometry("0100101004", raw)

        self.assertEqual(audit["status"], "BLOCKED")
        self.assertEqual(
            audit["reason"],
            "INDEPENDENT_REPAIR_DISAGREEMENT",
        )
        self.assertTrue(candidate.equals_exact(raw, 0.0))

    def test_nonpolygonal_repair_output_is_never_silently_discarded(self):
        raw = Polygon(
            [(0, 0), (1, 0), (0, 0), (1, 0), (0, 0)]
        )
        self.assertFalse(raw.is_valid)

        _, audit = normalize_official_geometry("0100101005", raw)

        self.assertEqual(audit["status"], "BLOCKED")
        self.assertEqual(
            audit["reason"],
            "NON_POLYGONAL_COMPONENT_AFTER_REPAIR",
        )
        self.assertIn(
            "LineString",
            audit["repair_attempt"]["linework_leaf_types"],
        )

    def test_unapproved_invalidity_class_remains_blocked(self):
        shell = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        outside = [(20, 20), (21, 20), (21, 21), (20, 21), (20, 20)]
        raw = Polygon(shell, [outside])
        self.assertFalse(raw.is_valid)

        _, audit = normalize_official_geometry("0100101006", raw)

        self.assertEqual(audit["status"], "BLOCKED")
        self.assertEqual(
            audit["reason"],
            "INVALIDITY_CLASS_NOT_AUTO_NORMALIZABLE_BY_POLICY",
        )

    def test_feature_pipeline_preserves_identity_attributes_coverage_and_contacts(self):
        bowtie = Polygon(
            [(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]
        )
        neighbor = box(1, 0, 2, 1)
        raw = [
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101001",
                    "CPRO": "01",
                    "POP": 123,
                    "name": "changed-geometry-only",
                },
                "geometry": mapping(bowtie),
            },
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101002",
                    "CPRO": "01",
                    "POP": 456,
                    "name": "neighbor",
                },
                "geometry": mapping(neighbor),
            },
        ]
        snapshot = json.dumps(raw, sort_keys=True)

        out, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:4326",
            coverage_field="CPRO",
            declared_use=target_use(),
        )

        self.assertEqual(json.dumps(raw, sort_keys=True), snapshot)
        self.assertEqual(report["decision"], "READY")
        self.assertEqual(report["normalized"], 1)
        self.assertEqual(report["blocked"], 0)
        self.assertTrue(
            report["identity_and_attributes"]["section_order_and_identity_equal"]
        )
        self.assertTrue(report["identity_and_attributes"]["properties_exact"])
        self.assertTrue(report["identity_and_attributes"]["coverage_exact"])
        self.assertEqual(
            report["identity_and_attributes"]["population_fields_present"],
            ["POP"],
        )
        self.assertEqual(report["topology"]["candidate_overlap_count"], 0)
        self.assertTrue(
            report["topology"]["contacts"]["all_contact_id_sets_preserved"]
        )
        self.assertTrue(
            report["topology"]["contacts"]["all_contact_geometries_preserved"]
        )
        self.assertEqual(
            report["topology"]["global_gap_validation"]["status"],
            "LIMITED",
        )
        self.assertEqual(
            report["topology"]["candidate_gap_diagnostics"]["status"],
            "OBSERVED_NOT_CLASSIFIED",
        )
        self.assertEqual(
            report["topology"]["candidate_gap_diagnostics"][
                "interior_gap_count"
            ],
            0,
        )
        self.assertIsNone(
            report["normalization_policy"]["numeric_acceptance_tolerance"]
        )
        self.assertEqual(out[0]["properties"], raw[0]["properties"])
        self.assertEqual(out[1]["properties"], raw[1]["properties"])

    def test_dataset_without_modifications_keeps_original_overlap_as_source_defect(self):
        raw = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101001", "CPRO": "01"},
                "geometry": mapping(box(0, 0, 2, 2)),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101002", "CPRO": "01"},
                "geometry": mapping(box(1, 1, 3, 3)),
            },
        ]

        _, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:3035",
            coverage_field="CPRO",
        )

        self.assertEqual(report["blocked"], 0)
        self.assertEqual(report["topology"]["candidate_overlap_count"], 1)
        self.assertEqual(report["normalization_safety"]["decision"], "READY")
        self.assertEqual(report["source_admissibility"]["decision"], "NOT_EVALUATED")
        self.assertFalse(report["source_admissibility"]["allows_staging"])
        self.assertEqual(report["decision"], "BLOCKED")
        pair = report["topology"]["pairwise"]["overlaps"][0]
        self.assertEqual(
            (pair["section_a"], pair["section_b"]),
            ("0100101001", "0100101002"),
        )
        self.assertEqual(pair["classification"], "PRESERVED")
        self.assertEqual(pair["before"], pair["after"])

    def test_original_overlap_is_admissible_only_by_declared_consumer_rule(self):
        raw = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101001", "CPRO": "01"},
                "geometry": mapping(box(0, 0, 2, 2)),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101002", "CPRO": "01"},
                "geometry": mapping(box(1.5, 0, 3.5, 2)),
            },
        ]
        declared_use = {
            "role": "target_sectioning",
            "consumer": "modulo_02_construir_adyacencias",
            "adjacency": {
                "predicate": "contact",
                "working_crs": "EPSG:3035",
                "min_shared_border_m": 1.0,
                "max_precision_overlap_area_m2": 1.0,
            },
        }

        _, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:3035",
            coverage_field="CPRO",
            declared_use=declared_use,
        )

        self.assertEqual(report["normalization_safety"]["decision"], "READY")
        self.assertEqual(report["source_admissibility"]["decision"], "READY")
        self.assertEqual(report["decision"], "READY")
        assessed = report["source_admissibility"]["original_overlap_pairs"]
        self.assertEqual(len(assessed), 1)
        self.assertEqual(assessed[0]["overlap_area_m2"], 1.0)
        self.assertTrue(assessed[0]["admissible"])

    def test_precision_overlap_without_m02_edge_is_still_explicitly_admissible(self):
        raw = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101001", "CPRO": "01"},
                "geometry": mapping(box(0, 0, 2, 2)),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101002", "CPRO": "01"},
                "geometry": mapping(box(1.999, 1.0, 3.0, 1.5)),
            },
        ]
        declared_use = target_use(
            crs="EPSG:3035",
            min_shared=1.0,
            max_overlap=1.0,
        )

        _, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:3035",
            coverage_field="CPRO",
            declared_use=declared_use,
        )

        self.assertEqual(report["decision"], "READY")
        pair = report["source_admissibility"][
            "original_overlap_pairs"
        ][0]
        self.assertLess(pair["overlap_area_m2"], 1.0)
        self.assertLess(pair["shared_boundary_m"], 1.0)
        self.assertFalse(pair["would_form_m02_edge"])
        self.assertEqual(
            pair["adjacency_effect"],
            "NO_EDGE_UNDER_DECLARED_CONSUMER",
        )
        self.assertTrue(pair["admissible"])

    def test_original_overlap_remains_blocked_when_declared_use_rejects_it(self):
        raw = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101001", "CPRO": "01"},
                "geometry": mapping(box(0, 0, 2, 2)),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101002", "CPRO": "01"},
                "geometry": mapping(box(1, 0, 3, 2)),
            },
        ]
        declared_use = {
            "role": "target_sectioning",
            "consumer": "modulo_02_construir_adyacencias",
            "adjacency": {
                "predicate": "contact",
                "working_crs": "EPSG:3035",
                "min_shared_border_m": 1.0,
                "max_precision_overlap_area_m2": 1.0,
            },
        }

        _, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:3035",
            coverage_field="CPRO",
            declared_use=declared_use,
        )

        self.assertEqual(report["normalization_safety"]["decision"], "READY")
        self.assertEqual(report["source_admissibility"]["decision"], "BLOCKED")
        self.assertEqual(report["decision"], "BLOCKED")
        violation = report["source_admissibility"]["inadmissible_overlap_pairs"][0]
        self.assertEqual(violation["overlap_area_m2"], 2.0)
        self.assertFalse(violation["admissible"])

    def test_pairwise_overlap_detects_new_and_increased_defects(self):
        raw = [box(0, 0, 1, 1), box(1, 0, 2, 1)]
        new_overlap = [box(0, 0, 1.2, 1), box(1, 0, 2, 1)]
        evidence = _pairwise_topology_evidence(
            ["A", "B"],
            raw,
            new_overlap,
            [],
            source_crs="EPSG:3035",
            metric_crs="EPSG:3035",
        )
        self.assertEqual(evidence["overlap_change_count"], 1)
        self.assertEqual(
            evidence["overlap_changes"][0]["classification"],
            "NEW",
        )

        before = box(0, 0, 2, 1).intersection(box(1, 0, 3, 1))
        after = box(0, 0, 2.5, 1).intersection(box(1, 0, 3, 1))
        self.assertEqual(
            _classify_spatial_change(before, after, relation="overlap"),
            "INCREASED",
        )

    def test_pairwise_change_with_equal_area_but_different_location_is_displaced(self):
        before = box(0, 0, 1, 1)
        after = box(2, 0, 3, 1)
        self.assertEqual(before.area, after.area)
        self.assertEqual(
            _classify_spatial_change(before, after, relation="overlap"),
            "DISPLACED_OR_RESHAPED",
        )
        self.assertEqual(
            _classify_spatial_change(
                before.boundary,
                after.boundary,
                relation="contact",
            ),
            "DISPLACED_OR_RESHAPED",
        )

    def test_pairwise_contact_change_is_detected_end_to_end(self):
        raw = [box(0, 0, 1, 1), box(1, 0, 2, 1)]
        derived = [box(0, 0, 1, 1), box(1.1, 0, 2.1, 1)]
        evidence = _pairwise_topology_evidence(
            ["A", "B"],
            raw,
            derived,
            [],
            source_crs="EPSG:3035",
            metric_crs="EPSG:3035",
        )
        self.assertEqual(evidence["contact_change_count"], 1)
        self.assertEqual(
            evidence["contact_changes"][0]["classification"],
            "REMOVED",
        )

    def test_pairwise_increased_overlap_is_detected_end_to_end(self):
        raw = [box(0, 0, 2, 1), box(1, 0, 3, 1)]
        derived = [box(0, 0, 2.5, 1), box(1, 0, 3, 1)]
        evidence = _pairwise_topology_evidence(
            ["A", "B"],
            raw,
            derived,
            [],
            source_crs="EPSG:3035",
            metric_crs="EPSG:3035",
        )
        self.assertEqual(evidence["overlap_change_count"], 1)
        self.assertEqual(
            evidence["overlap_changes"][0]["classification"],
            "INCREASED",
        )

    def test_pairwise_equal_area_spatial_move_is_detected_end_to_end(self):
        raw = [box(0, 0, 2, 1), box(1, 0, 3, 1)]
        derived = [box(0, 0, 2, 1), box(-1, 0, 1, 1)]
        evidence = _pairwise_topology_evidence(
            ["A", "B"],
            raw,
            derived,
            [],
            source_crs="EPSG:3035",
            metric_crs="EPSG:3035",
        )
        change = evidence["overlap_changes"][0]
        self.assertEqual(
            change["before"]["area_m2"],
            change["after"]["area_m2"],
        )
        self.assertEqual(
            change["classification"],
            "DISPLACED_OR_RESHAPED",
        )

    def test_unevaluable_raw_baseline_without_pair_evidence_blocks(self):
        invalid = Polygon(
            [(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)]
        )
        derived = box(0, 0, 2, 2)
        neighbor = box(0, 0, 1, 1)

        def relation(left, right, kind):
            if not left.is_valid or not right.is_valid:
                return None, "forced invalid raw baseline"
            if kind == "overlap":
                value = left.intersection(right)
                return (
                    (None, None)
                    if value.is_empty or float(value.area) == 0.0
                    else (value, None)
                )
            value = left.boundary.intersection(right.boundary)
            return (None if value.is_empty else value), None

        with patch(
            "ddd_core.official_geometry._safe_pair_relation",
            side_effect=relation,
        ):
            evidence = _pairwise_topology_evidence(
                ["A", "B"],
                [invalid, neighbor],
                [derived, neighbor],
                [],
                source_crs="EPSG:3035",
                metric_crs="EPSG:3035",
            )

        self.assertGreater(evidence["unresolved_baseline_count"], 0)
        self.assertTrue(evidence["baseline_limitations"])
        self.assertEqual(
            evidence["baseline_limitations"][0]["reason"],
            "PAIR_BASELINE_NOT_EVALUABLE",
        )
        self.assertEqual(
            evidence["baseline_limitations"][0][
                "alternative_baseline_evidence"
            ]["status"],
            "NOT_AVAILABLE",
        )

    def test_consumer_fallback_crs_is_replayed_not_compared_to_policy_crs(self):
        declared = _geometry_declared_use(
            ROOT,
            territory_id="castilla_y_leon",
            edition=2025,
            role="target_sectioning",
        )
        self.assertEqual(
            declared["adjacency"]["working_crs"],
            "EPSG:25830",
        )
        self.assertEqual(
            declared["adjacency"]["max_precision_overlap_area_m2"],
            1.0,
        )
        raw = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0900101001", "CPRO": "09"},
                "geometry": mapping(box(0, 0, 2, 2)),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0900101002", "CPRO": "09"},
                "geometry": mapping(box(1.5, 0, 3.5, 2)),
            },
        ]
        _, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:25830",
            coverage_field="CPRO",
            declared_use=declared,
        )
        self.assertEqual(report["decision"], "READY")
        pair = report["source_admissibility"][
            "original_overlap_pairs"
        ][0]
        self.assertEqual(pair["measurement_crs"], "EPSG:25830")
        self.assertEqual(pair["overlap_area_m2"], 1.0)
        self.assertGreaterEqual(pair["shared_boundary_m"], 1.0)

    def test_invalid_raw_baseline_uses_verifiable_alternative_not_zero(self):
        bowtie = Polygon(
            [(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)]
        )
        neighbor = box(0, 0, 1, 1)
        raw = [
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101001", "CPRO": "01"},
                "geometry": mapping(bowtie),
            },
            {
                "type": "Feature",
                "properties": {"CUSEC": "0100101002", "CPRO": "01"},
                "geometry": mapping(neighbor),
            },
        ]

        _, report = normalize_official_features(
            raw,
            "CUSEC",
            crs="EPSG:3035",
            coverage_field="CPRO",
        )

        rows = [
            row
            for row in report["topology"]["pairwise"]["overlaps"]
            if row["section_a"] == "0100101001"
            and row["section_b"] == "0100101002"
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertIn("before_error", row)
        self.assertEqual(
            row["baseline_method"],
            "ALTERNATIVE_PAIR_EVIDENCE",
        )
        self.assertEqual(
            row["alternative_baseline_evidence"]["status"],
            "AVAILABLE",
        )
        self.assertIsNotNone(row["before"])
        self.assertNotEqual(row["before"]["area_m2"], 0.0)
        self.assertEqual(
            report["normalization_safety"]["unresolved_baseline_count"],
            0,
        )

    def test_feature_pipeline_is_idempotent_after_exact_normalization(self):
        part = box(0, 0, 1, 1)
        raw = [
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101001",
                    "CPRO": "01",
                    "POP": 123,
                    "name": "preserved",
                },
                "geometry": mapping(MultiPolygon([part, part])),
            }
        ]

        first, report1 = normalize_official_features(
            raw,
            "CUSEC",
            coverage_field="CPRO",
            declared_use=target_use(),
        )
        second, report2 = normalize_official_features(
            first,
            "CUSEC",
            coverage_field="CPRO",
            declared_use=target_use(),
        )

        self.assertEqual(report1["normalized"], 1)
        self.assertEqual(report1["blocked"], 0)
        self.assertEqual(report1["decision"], "READY")
        self.assertEqual(report2["normalized"], 0)
        self.assertEqual(report2["blocked"], 0)
        self.assertEqual(report2["decision"], "READY")
        self.assertEqual(first[0]["properties"], raw[0]["properties"])
        self.assertEqual(second[0]["properties"], raw[0]["properties"])
        self.assertTrue(
            shape(first[0]["geometry"]).equals_exact(
                shape(second[0]["geometry"]),
                0.0,
            )
        )
        self.assertTrue(
            report1["normalization_policy"][
                "make_valid_used_only_with_independent_consensus"
            ]
        )
        self.assertIsNone(
            report1["normalization_policy"]["numeric_acceptance_tolerance"]
        )

    def test_common_preparation_helper_persists_blocking_evidence(self):
        source = {
            "section_id_field": "CUSEC",
            "territorial_filter_field": "CPRO",
        }
        shell = [(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]
        outside = [(20, 20), (21, 20), (21, 21), (20, 21), (20, 20)]
        features = [
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101006",
                    "CPRO": "01",
                },
                "geometry": mapping(Polygon(shell, [outside])),
            }
        ]
        checks = {
            "raw_responses": [
                {
                    "source_id": "sections",
                    "source_year": 2024,
                    "province_code": "01",
                    "url": "https://official.example/01",
                    "path": "raw/sections/2024/01.geojson",
                    "sha256": "b" * 64,
                    "bytes": 123,
                }
            ]
        }

        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td)
            with self.assertRaisesRegex(
                ValueError,
                "GEOMETRY_INVALID_AUDITED",
            ):
                _normalize_sections_or_block(
                    features,
                    source,
                    checks,
                    crs="EPSG:4326",
                    evidence_dir=evidence,
                    source_id="sections",
                    source_year=2024,
                )

            report = checks["geometry_normalization"]
            self.assertEqual(report["blocked"], 1)
            self.assertEqual(report["decision"], "BLOCKED")
            ref = checks["geometry_normalization_evidence"]
            self.assertEqual(ref["decision"], "BLOCKED")
            document = json.loads(
                (evidence / ref["path"]).read_text(encoding="utf-8")
            )
            self.assertEqual(
                document["normalization"]["issues"][0]["before"]["section_id"],
                "0100101006",
            )
            issue = document["normalization"]["issues"][0]
            self.assertEqual(
                issue["reason"],
                "INVALIDITY_CLASS_NOT_AUTO_NORMALIZABLE_BY_POLICY",
            )
            self.assertEqual(issue["before"]["crs"], "EPSG:4326")
            self.assertEqual(
                issue["before"]["raw_source_response_sha256"],
                "b" * 64,
            )
            self.assertEqual(
                issue["before"]["raw_source_response_path"],
                "raw/sections/2024/01.geojson",
            )

    def test_materialization_roundtrip_validates_derived_product(self):
        features = [
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101001",
                    "CPRO": "01",
                    "POP": 0,
                    "name": "preserved",
                },
                "geometry": mapping(box(0, 0, 1, 1)),
            }
        ]
        checks = {}

        payload = _write_shapefile_zip(
            features,
            crs="EPSG:4326",
            section_id_field="CUSEC",
            materialization_checks=checks,
        )

        self.assertTrue(zipfile.is_zipfile(Path(self._write_temp(payload))))
        self.assertEqual(checks["decision"], "READY")
        self.assertTrue(checks["section_identity_exact"])
        self.assertTrue(checks["attributes_exact"])
        self.assertTrue(checks["geometry_topologically_equal"])

    def _write_temp(self, payload: bytes) -> str:
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        try:
            tmp.write(payload)
            return tmp.name
        finally:
            tmp.close()

    def test_shapefile_write_failure_keeps_exact_failure_stage(self):
        features = [
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101001",
                    "CPRO": "01",
                },
                "geometry": mapping(box(0, 0, 1, 1)),
            }
        ]
        checks = {}

        with patch(
            "geopandas.GeoDataFrame.to_file",
            side_effect=ValueError("forced write failure"),
        ):
            with self.assertRaisesRegex(
                ValueError,
                "forced write failure",
            ):
                _write_shapefile_zip(
                    features,
                    crs="EPSG:4326",
                    section_id_field="CUSEC",
                    materialization_checks=checks,
                )

        self.assertEqual(checks["decision"], "BLOCKED")
        self.assertEqual(checks["stage"], "SHAPEFILE_WRITE")
        self.assertIn("forced write failure", checks["error"])

    def test_real_invalid_post_shapefile_readback_has_structured_lineage(self):
        features = [
            {
                "type": "Feature",
                "properties": {
                    "CUSEC": "0100101001",
                    "CPRO": "01",
                    "name": "source",
                },
                "geometry": mapping(box(0, 0, 1, 1)),
            }
        ]
        source = {
            "section_id_field": "CUSEC",
            "territorial_filter_field": "CPRO",
        }
        checks = {
            "raw_responses": [
                {
                    "source_id": "sections",
                    "source_year": 2024,
                    "province_code": "01",
                    "url": "https://official.example/01",
                    "path": "raw/sections/2024/01.geojson",
                    "sha256": "c" * 64,
                    "bytes": 456,
                }
            ]
        }
        invalid_after = Polygon(
            [(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]
        )
        readback = gpd.GeoDataFrame(
            {
                "CUSEC": ["0100101001"],
                "CPRO": ["01"],
                "name": ["source"],
            },
            geometry=[invalid_after],
            crs="EPSG:4326",
        )

        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td)
            normalized = _normalize_sections_or_block(
                features,
                source,
                checks,
                crs="EPSG:4326",
                evidence_dir=evidence,
                source_id="sections",
                source_year=2024,
                declared_use=target_use(),
            )
            self.assertEqual(
                checks["geometry_normalization_evidence"]["decision"],
                "PENDING_MATERIALIZATION",
            )

            with patch("geopandas.read_file", return_value=readback):
                with self.assertRaisesRegex(
                    ValueError,
                    "GEOMETRY_POST_MATERIALIZATION_BLOCKED",
                ):
                    _materialize_sections_with_evidence(
                        normalized,
                        crs="EPSG:4326",
                        section_id_field="CUSEC",
                        source_partition_field="CPRO",
                        evidence_dir=evidence,
                        source_id="sections",
                        source_year=2024,
                        content_checks=checks,
                        derived_path="inputs/sections.zip",
                    )

            ref = checks["geometry_normalization_evidence"]
            self.assertEqual(ref["decision"], "BLOCKED")
            document = json.loads(
                (evidence / ref["path"]).read_text(encoding="utf-8")
            )
            validation = document["materialization_validation"]
            self.assertEqual(validation["decision"], "BLOCKED")
            self.assertEqual(
                validation["stage"],
                "POST_SHAPEFILE_WRITE_READBACK",
            )
            self.assertEqual(len(validation["defects"]), 1)
            defect = validation["defects"][0]
            self.assertEqual(defect["section_id"], "0100101001")
            self.assertEqual(
                defect["reason"],
                "GEOMETRY_POST_MATERIALIZATION_INVALID",
            )
            self.assertEqual(
                defect["stage"],
                "POST_SHAPEFILE_WRITE_READBACK",
            )
            self.assertEqual(defect["raw_source"]["crs"], "EPSG:4326")
            self.assertEqual(
                defect["raw_source"]["response_sha256"],
                "c" * 64,
            )
            self.assertEqual(
                defect["raw_source"]["response_path"],
                "raw/sections/2024/01.geojson",
            )
            self.assertEqual(
                defect["raw_source"]["geometry_sha256"],
                defect["pre_materialization"]["geometry_sha256"],
            )
            self.assertNotEqual(
                defect["pre_materialization"]["geometry_sha256"],
                defect["post_materialization"]["geometry_sha256"],
            )
            self.assertIn(
                "Self-intersection",
                defect["post_materialization"]["validity_reason"],
            )
            self.assertEqual(
                defect["post_materialization"]["crs"],
                "EPSG:4326",
            )
            self.assertIsNone(document["derived"])

    def test_evidence_records_raw_and_derived_hashes(self):
        report = {
            "schema": "ddd.official-geometry-normalization/2.0",
            "decision": "READY",
        }
        raw = [
            {
                "source_id": "sections",
                "source_year": 2024,
                "province_code": "01",
                "url": "https://official.example/01",
                "path": "raw/sections/2024/01.geojson",
                "sha256": "a" * 64,
                "bytes": 123,
            }
        ]
        derived = b"derived-payload"

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ref = persist_geometry_normalization_evidence(
                root,
                source_id="sections",
                source_year=2024,
                report=report,
                raw_records=raw,
                derived_path="inputs/sections.zip",
                derived_payload=derived,
                materialization_validation={"decision": "READY"},
            )
            document = json.loads(
                (root / ref["path"]).read_text(encoding="utf-8")
            )
            self.assertTrue(document["source_identity"]["raw_preserved"])
            self.assertEqual(
                document["source_identity"]["records"][0]["sha256"],
                "a" * 64,
            )
            self.assertEqual(
                document["derived"]["sha256"],
                hashlib.sha256(derived).hexdigest(),
            )
            self.assertEqual(
                document["materialization_validation"]["decision"],
                "READY",
            )
            self.assertEqual(document["decision"], "READY")
            self.assertEqual(ref["decision"], "READY")
            self.assertEqual(document["derived"]["decision"], "READY")

    def test_raw_official_response_is_byte_exact_and_idempotent(self):
        payload = b'{"type":"FeatureCollection","features":[]}'
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            record = persist_raw_ogc_response(
                root,
                source_id="secciones_censales",
                source_year=2024,
                province_code="08",
                url="https://official.example/08",
                payload=payload,
            )

            self.assertEqual(
                (root / record["path"]).read_bytes(),
                payload,
            )
            self.assertEqual(
                record["sha256"],
                hashlib.sha256(payload).hexdigest(),
            )
            self.assertEqual(record["bytes"], len(payload))

            manifest = json.loads(
                (root / "raw_official_responses.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest["responses"], [record])

            again = persist_raw_ogc_response(
                root,
                source_id="secciones_censales",
                source_year=2024,
                province_code="08",
                url="https://official.example/08",
                payload=payload,
            )
            self.assertEqual(again, record)
            manifest2 = json.loads(
                (root / "raw_official_responses.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(manifest2["responses"], [record])


if __name__ == "__main__":
    unittest.main()
