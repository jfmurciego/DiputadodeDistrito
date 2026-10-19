"""Pruebas sintéticas del auditor de paginación IGN; no representan datos oficiales."""
import json
import unittest
from unittest.mock import patch

from ddd_core.congreso_ign_api_snapshot import audit_captured_pages


BASE = "https://api-features.ign.es/collections/administrativeboundary/items?f=json&limit=1"
NEXT = BASE + "&offset=1"


def feature(ident, code, start, end=None, geometry=None):
    return {
        "type": "Feature", "id": ident,
        "properties": {"nationalcode": code, "date_boundary": start,
                       "endlifespanversion": end},
        "geometry": geometry or {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
    }


def page(features, *, matched, next_url=None):
    links = [{"rel": "next", "href": next_url}] if next_url else []
    return json.dumps({"type": "FeatureCollection", "numberMatched": matched,
                       "numberReturned": len(features), "features": features,
                       "links": links}, separators=(",", ":")).encode()


class IGNApiSnapshotTests(unittest.TestCase):
    def test_complete_pagination_is_only_temporal_candidate(self):
        raw1 = page([feature(10, "M01001001001M01001001002T0001", "2020-01-01")],
                    matched=2, next_url=NEXT)
        raw2 = page([feature(11, "M01001001001M01001001002T0002", "2025-01-01", "2026-01-01")],
                    matched=2)
        result = audit_captured_pages([{"url": BASE, "raw": raw1}, {"url": NEXT, "raw": raw2}])
        self.assertEqual(2, result["number_returned_total"])
        self.assertEqual(2, result["time_window_candidates"])
        self.assertEqual(2, result["distinct_nationalcodes_in_candidates"])
        self.assertEqual("CAPTURE_COMPLETE_TEMPORAL_CANDIDATE_ONLY_NOT_ACCREDITATION", result["status"])
        self.assertFalse(result["historical_2025_source_accredited"])
        self.assertFalse(result["generation_authorized"])
        self.assertEqual(2, len(result["page_receipts"]))

    def test_incomplete_next_page_rejected(self):
        raw = page([feature(1, "x", "2020-01-01")], matched=2, next_url=NEXT)
        with self.assertRaisesRegex(ValueError, "API_PAGINATION_CAPTURE_INCOMPLETE"):
            audit_captured_pages([{"url": BASE, "raw": raw}])

    def test_missing_next_link_rejected(self):
        first = page([feature(1, "x", "2020-01-01")], matched=2)
        second = page([feature(2, "y", "2020-01-01")], matched=2)
        with self.assertRaisesRegex(ValueError, "API_NEXT_PAGE_LINK_MISSING"):
            audit_captured_pages([{"url": BASE, "raw": first}, {"url": NEXT, "raw": second}])

    def test_duplicate_feature_id_rejected_across_pages(self):
        first = page([feature(7, "x", "2020-01-01")], matched=2, next_url=NEXT)
        second = page([feature(7, "y", "2020-01-01")], matched=2)
        with self.assertRaisesRegex(ValueError, "API_FEATURE_ID_DUPLICATE"):
            audit_captured_pages([{"url": BASE, "raw": first}, {"url": NEXT, "raw": second}])

    def test_official_host_required_for_next(self):
        raw = page([feature(1, "x", "2020-01-01")], matched=2,
                   next_url="https://evil.example/collections/administrativeboundary/items?f=json")
        with self.assertRaisesRegex(ValueError, "API_PAGE_URL_OUTSIDE_OFFICIAL_COLLECTION"):
            audit_captured_pages([{"url": BASE, "raw": raw}, {"url": "https://evil.example/collections/administrativeboundary/items?f=json", "raw": b"{}"}])

    def test_next_link_requires_string_href(self):
        raw = json.dumps({"type": "FeatureCollection", "numberMatched": 0,
                          "numberReturned": 0, "features": [],
                          "links": [{"rel": "next", "href": None}]}).encode()
        with self.assertRaisesRegex(ValueError, "API_NEXT_LINK_HREF_REQUIRED"):
            audit_captured_pages([{"url": BASE, "raw": raw}])

    def test_query_selection_must_not_change_across_pages(self):
        first_url = BASE + "&filter=municipality%3D001"
        next_url = BASE + "&offset=1&filter=municipality%3D002"
        raw1 = page([feature(1, "x", "2020-01-01")], matched=2, next_url=next_url)
        raw2 = page([feature(2, "y", "2020-01-01")], matched=2)
        with self.assertRaisesRegex(ValueError, "API_QUERY_SELECTION_CHANGED"):
            audit_captured_pages([{"url": first_url, "raw": raw1}, {"url": next_url, "raw": raw2}])

    def test_query_parameter_names_are_case_sensitive(self):
        first_url = BASE + "&filter=municipality%3D001"
        next_url = BASE + "&offset=1&FILTER=municipality%3D001"
        raw1 = page([feature(1, "x", "2020-01-01")], matched=2, next_url=next_url)
        raw2 = page([feature(2, "y", "2020-01-01")], matched=2)
        with self.assertRaisesRegex(ValueError, "API_QUERY_SELECTION_CHANGED"):
            audit_captured_pages([{"url": first_url, "raw": raw1}, {"url": next_url, "raw": raw2}])

    def test_count_mismatch_rejected(self):
        raw = json.dumps({"type": "FeatureCollection", "numberMatched": 1,
                          "numberReturned": 4, "features": []}).encode()
        with self.assertRaisesRegex(ValueError, "API_PAGE_COUNT_METADATA_INVALID"):
            audit_captured_pages([{"url": BASE, "raw": raw}])

    def test_polygon_not_boundary_line_rejected(self):
        raw = page([feature(1, "x", "2020-01-01", geometry={
            "type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]
        })], matched=1)
        with self.assertRaisesRegex(ValueError, "API_ADMINISTRATIVE_BOUNDARY_LINE_REQUIRED"):
            audit_captured_pages([{"url": BASE, "raw": raw}])

    def test_non_finite_or_malformed_positions_rejected(self):
        for position in ([float("nan"), 0], [0, float("inf")], [0, 1, "bad"], [0, 1, 2, 3]):
            with self.subTest(position=position):
                raw = page([feature(1, "x", "2020-01-01", geometry={
                    "type": "LineString", "coordinates": [[0, 0], position]
                })], matched=1)
                with self.assertRaisesRegex(ValueError, "API_ADMINISTRATIVE_BOUNDARY_LINE_REQUIRED"):
                    audit_captured_pages([{"url": BASE, "raw": raw}])

    def test_page_limit_does_not_consume_unbounded_iterable(self):
        consumed = []
        def pages():
            for i in range(100):
                consumed.append(i)
                url = BASE + "&page=" + str(i)
                raw = page([feature(i, "code" + str(i), "2020-01-01")], matched=100,
                           next_url=BASE + "&page=" + str(i + 1))
                yield {"url": url, "raw": raw}
        with patch("ddd_core.congreso_ign_api_snapshot.MAX_PAGES", 2):
            with self.assertRaisesRegex(ValueError, "API_PAGE_COUNT_OUT_OF_RANGE"):
                audit_captured_pages(pages())
        self.assertEqual([0, 1], consumed)

    def test_pages_are_processed_before_consuming_the_next_page(self):
        consumed = []
        bad_first = {"url": BASE, "raw": b"{}"}
        def pages():
            consumed.append(0)
            yield bad_first
            consumed.append(1)
            yield {"url": NEXT, "raw": b"{}"}
        with self.assertRaisesRegex(ValueError, "API_PAGE_NOT_FEATURE_COLLECTION"):
            audit_captured_pages(pages())
        self.assertEqual([0], consumed)

    def test_only_approved_target_date(self):
        raw = page([feature(1, "x", "2020-01-01")], matched=1)
        with self.assertRaisesRegex(ValueError, "ONLY_APPROVED_HISTORICAL_REFERENCE_2025_01_01"):
            audit_captured_pages([{"url": BASE, "raw": raw}], target_date="2025-01-02")


if __name__ == "__main__":
    unittest.main()
