"""No-network tests for IGN historical date-selected vector request."""
import json
import unittest
from ddd_core.congreso_ign_historical_wms import (
    HISTORIC_TIME, request_url, inspect_historical_response, probe,
)


def example():
    return json.dumps({"type":"FeatureCollection","totalFeatures":"unknown","features":[
       {"type":"Feature","id":"LimitesTime.sample-001",
        "geometry":{"type":"LineString","coordinates":[[-4.04,42.41],[-4.03,42.42]]},
        "properties":{"nationalcode":"M340100M340200T0123",
                      "date_boundary":"2009-07-05Z",
                      "endlifespanversion":"2998-12-31Z","legalstatus":"agreed"}}
    ]},separators=(",",":")).encode()


class HistoricalWMSProbeTests(unittest.TestCase):
    def test_url_explicit_layer_time_and_crs(self):
        url=request_url((-4.05,42.4,-3.95,42.5))
        self.assertTrue(url.startswith("https://www.ign.es/wms-inspire/unidades-administrativas?"))
        self.assertIn("LimitesTime",url)
        self.assertIn("2025-01-01",url)
        self.assertIn("CRS%3A84",url)

    def test_bounded_probe_preserves_bytes_and_denies_accreditation(self):
        raw,receipt=probe((-4.05,42.4,-3.95,42.5),lambda url:example())
        self.assertEqual(raw,example())
        self.assertEqual(receipt["features_in_view"],1)
        self.assertEqual(len(receipt["raw_sha256"]),64)
        self.assertEqual(receipt["time_requested"],HISTORIC_TIME)
        for field in ("complete_52_province_coverage_verified",
                      "temporal_legal_coverage_verified",
                      "municipality_code_crosswalk_verified",
                      "eligible_for_NAT_C_056_accreditation",
                      "generation_authorized"):
            self.assertFalse(receipt[field])

    def test_rejects_wide_or_other_time_requests(self):
        for bbox in ((-20,27,5,44),(-4,42,-2.9,42.5),(10,42,11,43),(-4,44,-3,45)):
            with self.subTest(bbox=bbox),self.assertRaises(ValueError):
                request_url(bbox)
        with self.assertRaisesRegex(ValueError,"ONLY_APPROVED"):
            request_url((-4.05,42.4,-3.95,42.5),"2026-01-01")

    def test_rejects_duplicate_json_keys_at_every_nesting_level(self):
        url = request_url((-4.05, 42.4, -3.95, 42.5))
        base = example().decode("utf-8")
        payloads = (
            base.replace('"type":"FeatureCollection"', '"type":"FeatureCollection","type":"FeatureCollection"', 1),
            base.replace('"totalFeatures":"unknown"', '"totalFeatures":"unknown","totalFeatures":"500"', 1),
            base.replace('"nationalcode":"M340100M340200T0123"', '"nationalcode":"M340100M340200T0123","nationalcode":"altered"', 1),
        )
        for raw in payloads:
            with self.subTest(sample=raw[:95]), self.assertRaisesRegex(ValueError, "SOURCE_WMS_GEOJSON_INVALID"):
                inspect_historical_response(raw.encode("utf-8"), url)

    def test_malformed_document_or_null_geometry_fails_closed(self):
        url = request_url((-4.05, 42.4, -3.95, 42.5))
        null_geometry = json.loads(example())
        null_geometry["features"][0]["geometry"] = None
        for raw in (b"[]", b"null", json.dumps(null_geometry).encode("utf-8")):
            with self.subTest(raw=raw[:40]), self.assertRaises(ValueError):
                inspect_historical_response(raw, url)

    def test_rejects_forged_view_or_missing_temporal_fields(self):
        url=request_url((-4.05,42.4,-3.95,42.5))
        bad=[b"<html>error</html>",json.dumps({"type":"FeatureCollection","features":[
          {"type":"Feature","id":"a","properties":{"nationalcode":"x"},
           "geometry":{"type":"LineString","coordinates":[]}}]}).encode()]
        for payload in bad:
            with self.subTest(payload=payload[:20]),self.assertRaises(ValueError):
                inspect_historical_response(payload,url)


if __name__=="__main__":
    unittest.main()
