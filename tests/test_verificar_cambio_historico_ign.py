"""Synthetic tamper tests, independent of the live official-service smoke."""
import copy
import json
import unittest

from herramientas.verificar_cambio_historico_ign import (
    BOUNDARY_ID, START_OF_NEW_BOUNDARY, build_url, compare, inspect,
)


def sample(including_new: bool):
    old = {"type": "Feature", "properties": {"nationalcode": "OTHER"},
           "geometry": {"type": "LineString", "coordinates": [[-0.4,39.2], [-0.39,39.21]]}}
    item = {"type": "Feature",
            "properties": {"nationalcode": BOUNDARY_ID, "date_boundary": START_OF_NEW_BOUNDARY},
            "geometry": {"type":"LineString","coordinates":[[-0.403,39.199], [-0.404,39.198]]}}
    doc = {"type": "FeatureCollection", "features": [old, item] if including_new else [old]}
    return json.dumps(doc, separators=(",", ":")).encode()


class HistoricTransitionTests(unittest.TestCase):
    def test_direct_comparison_is_fail_closed_not_admission(self):
        result = compare(sample(False), sample(True))
        self.assertTrue(result["target_excluded_at_2025_01_01"])
        self.assertTrue(result["target_included_at_2026_01_01"])
        self.assertFalse(result["coverage_52_verified"])
        self.assertFalse(result["generation_authorized"])
        self.assertFalse(result["official_temporal_source_edition_accredited"])

    def test_different_time_queries_are_explicit(self):
        self.assertIn("2025-01-01", build_url("2025-01-01"))
        self.assertIn("2026-01-01", build_url("2026-01-01"))
        with self.assertRaises(ValueError):
            build_url("2024-01-01")

    def test_no_false_temporal_positive(self):
        for old, later in ((sample(True),sample(True)),(sample(False),sample(False))):
            with self.assertRaisesRegex(ValueError, "NOT_REPRODUCED"):
                compare(old,later)

    def test_changing_boundary_provenance_must_reject(self):
        malicious = json.loads(sample(True))
        malicious["features"][1]["properties"]["date_boundary"] = "2024-01-01"
        with self.assertRaisesRegex(ValueError, "EXPECTED_BOUNDARY_START_DATE_CHANGED"):
            inspect(json.dumps(malicious).encode(), "2026-01-01")

    def test_reject_non_geojson_and_duplicate_codes(self):
        with self.assertRaisesRegex(ValueError, "WMS_INVALID_JSON"):
            inspect(b"<html>Error</html>", "2025-01-01")
        doc = json.loads(sample(True))
        doc["features"][1]["properties"]["nationalcode"] = "OTHER"
        with self.assertRaisesRegex(ValueError, "WMS_DUPLICATE_OR_MISSING_CODE"):
            inspect(json.dumps(doc).encode(), "2025-01-01")


if __name__ == "__main__":
    unittest.main()
