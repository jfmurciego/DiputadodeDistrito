"""CNIG byte receipt never opens national accreditation merely from a ZIP."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ddd_core.congreso_cnig_receipt import prepare_candidate_receipt, BLOCKED_STATE

SOURCE = {
    "authority": "CNIG/IGN",
    "product": "LILIM",
    "source_url": "https://centrodedescargas.cnig.es/CentroDescargas/limites-municipales-provinciales-autonomicos",
    "edition_issued_on": "2025-01-20",
    "intended_valid_at": "2025-01-01",
    "license": "compatible CC BY 4.0, attribution required",
    "acquired_at": "2026-10-19T10:00:00+02:00",
}


class CNIGReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "official_candidate.zip"
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("boundary/limits.gml", '<gml />')

    def test_receipt_checks_bytes_without_approving_2025(self):
        result = prepare_candidate_receipt(self.path, SOURCE)
        self.assertEqual(result["source_status"], BLOCKED_STATE)
        self.assertEqual(len(result["file_sha256"]), 64)
        self.assertEqual(result["zip_member_count"], 1)
        self.assertEqual(result["requested_valid_at"], "2025-01-01")
        for key in ("official_temporal_evidence_verified",
                    "official_2025_01_01_snapshot_accredited",
                    "administrative_code_mapping_verified",
                    "crs_and_layer_schema_verified",
                    "independent_review_completed",
                    "eligible_for_52_province_audits", "generation_authorized"):
            self.assertIs(result[key], False, key)

    def test_2026_edition_still_not_proven_for_2025(self):
        meta = dict(SOURCE, edition_issued_on="2026-08-10")
        self.assertFalse(prepare_candidate_receipt(self.path, meta)["eligible_for_52_province_audits"])

    def test_official_url_and_authority_are_required(self):
        for metadata in (dict(SOURCE, source_url="https://example.com/fake.zip"),
                         dict(SOURCE, source_url="http://centrodedescargas.cnig.es/x"),
                         dict(SOURCE, authority="INE"),
                         dict(SOURCE, product="INE2025")):
            with self.subTest(metadata=metadata):
                with self.assertRaises(ValueError):
                    prepare_candidate_receipt(self.path, metadata)

    def test_never_accept_wrong_effective_target(self):
        with self.assertRaisesRegex(ValueError, "CNIG_HISTORICAL_TARGET_MISMATCH"):
            prepare_candidate_receipt(self.path, dict(SOURCE, intended_valid_at="2024-01-01"))

    def test_rejects_malicious_archive_names(self):
        for name in ("../escape.gml", "/root/escape.gml", "dir\\escape.gml"):
            with self.subTest(name=name):
                with zipfile.ZipFile(self.path, "w") as z:
                    z.writestr(name, "bad")
                with self.assertRaisesRegex(ValueError, "UNSAFE_ZIP_MEMBER_NAME"):
                    prepare_candidate_receipt(self.path, SOURCE)

    def test_rejects_duplicates_and_missing_vectors(self):
        with zipfile.ZipFile(self.path, "w") as z:
            z.writestr("README.txt", "none")
        with self.assertRaisesRegex(ValueError, "SOURCE_VECTOR_LAYER_NOT_FOUND"):
            prepare_candidate_receipt(self.path, SOURCE)

    def test_missing_and_corrupted_bytes_do_not_get_receipt(self):
        self.path.write_bytes(b"garbage")
        with self.assertRaisesRegex(ValueError, "SOURCE_ZIP_INVALID"):
            prepare_candidate_receipt(self.path, SOURCE)
        self.path.unlink()
        with self.assertRaisesRegex(ValueError, "SOURCE_BYTES_ABSENT"):
            prepare_candidate_receipt(self.path, SOURCE)

    def test_metadata_date_and_timezone_are_strict(self):
        with self.assertRaisesRegex(ValueError, "ACQUISITION_TIMEZONE_REQUIRED"):
            prepare_candidate_receipt(self.path, dict(SOURCE, acquired_at="2026-10-19T10:00:00"))
        with self.assertRaisesRegex(ValueError, "DATE_INVALID"):
            prepare_candidate_receipt(self.path, dict(SOURCE, edition_issued_on="2025-99-99"))


if __name__ == "__main__":
    unittest.main()
