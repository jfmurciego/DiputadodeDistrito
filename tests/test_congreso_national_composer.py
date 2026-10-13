"""Synthetic tests for national candidate composition; no territorial run."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ddd_core.congreso_national_composer import NationalCandidateComposer


def _composer(root: Path):
    return NationalCandidateComposer(
        root, contract_sha256="a" * 64, source_manifest_sha256="b" * 64,
        topology_manifest_sha256="c" * 64,
        quotas={"01": 1, "02": 2},
        input_universes={
            "01": {"cusecs": ["0100101001", "0100101002"], "input_sha256": "d" * 64},
            "02": {"cusecs": ["0200201001", "0200201002", "0200201003"],
                   "input_sha256": "e" * 64},
        }, synthetic_fixture=True)


class NationalCompositionTests(unittest.TestCase):
    def test_composes_provincial_candidates_deterministically(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root)
            with self.assertRaisesRegex(ValueError, "COMPOSITION_UNITS_INCOMPLETE"):
                composer.compose()
            composer.record_province("02", [
                {"cusec": "0200201003", "district_id": "z"},
                {"cusec": "0200201001", "district_id": "a"},
                {"cusec": "0200201002", "district_id": "a"},
            ])
            composer.record_province("01", [
                {"cusec": "0100101002", "district_id": "one"},
                {"cusec": "0100101001", "district_id": "one"},
            ])
            candidate = composer.compose()
            self.assertEqual(candidate["province_count"], 2)
            self.assertEqual(candidate["district_count"], 3)
            self.assertEqual(candidate["cusec_count"], 5)
            self.assertEqual(candidate["assignments"][0],
                             {"cusec": "0100101001", "district_id": "DDD-01-001"})
            self.assertEqual(candidate["generation_authorized"], False)
            self.assertEqual(candidate["certification_status"], "NOT_PERFORMED")
            self.assertEqual(candidate["candidate_sha256"], _composer(root).compose()["candidate_sha256"])

    def test_resume_binds_checkpoint_and_per_province_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root)
            composer.record_province("01", [
                {"cusec": "0100101001", "district_id": "x"},
                {"cusec": "0100101002", "district_id": "x"},
            ])
            resumed = _composer(root)
            with self.assertRaisesRegex(ValueError, "COMPOSITION_UNITS_INCOMPLETE"):
                resumed.compose()
            resumed.record_province("02", [
                {"cusec": "0200201001", "district_id": "x"},
                {"cusec": "0200201002", "district_id": "x"},
                {"cusec": "0200201003", "district_id": "y"},
            ])
            resumed.compose()
            artifact = root / "01.json"
            artifact.write_text(artifact.read_text().replace("DDD-01-001", "tampered"))
            with self.assertRaisesRegex(ValueError, "COMPOSITION_CHECKPOINT_ARTIFACT_HASH"):
                _composer(root)

    def test_rejects_missing_duplicate_wrong_province_and_quota_mismatches(self):
        with tempfile.TemporaryDirectory() as temporary:
            composer = _composer(Path(temporary))
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_CUSEC_COVERAGE_MISMATCH"):
                composer.record_province("01", [{"cusec": "0100101001", "district_id": "x"}])
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_ASSIGNMENT_VALUE_INVALID"):
                composer.record_province("01", [
                    {"cusec": "0100101001", "district_id": "x"},
                    {"cusec": "0100101001", "district_id": "y"},
                ])
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_QUOTA_MISMATCH"):
                composer.record_province("02", [
                    {"cusec": "0200201001", "district_id": "only"},
                    {"cusec": "0200201002", "district_id": "only"},
                    {"cusec": "0200201003", "district_id": "only"},
                ])

    def test_rejects_partial_non_synthetic_and_bad_national_quota(self):
        kwargs = dict(contract_sha256="a" * 64, source_manifest_sha256="b" * 64,
                      topology_manifest_sha256="c" * 64,
                      quotas={"01": 1},
                      input_universes={"01": {"cusecs": ["0100101001"],
                                               "input_sha256": "d" * 64}})
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "NATIONAL_52_UNITS_REQUIRED"):
                NationalCandidateComposer(Path(temporary), **kwargs)
        kwargs["synthetic_fixture"] = True
        kwargs["quotas"] = {f"{i:02d}": 1 for i in range(1, 53)}
        kwargs["input_universes"] = {
            f"{i:02d}": {"cusecs": [f"{i:02d}00101001"], "input_sha256": f"{i:064x}"}
            for i in range(1, 53)}
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "NATIONAL_K_MUST_EQUAL_407"):
                NationalCandidateComposer(Path(temporary), **kwargs)

    def test_non_synthetic_full_quota_universe_requires_all_national_cusecs(self):
        quotas = {f"{i:02d}": 1 for i in range(1, 53)}
        quotas["01"] = 356
        input_universes = {
            f"{i:02d}": {"cusecs": [f"{i:02d}00101001"], "input_sha256": f"{i:064x}"}
            for i in range(1, 53)}
        kwargs = dict(contract_sha256="a" * 64, source_manifest_sha256="b" * 64,
                      topology_manifest_sha256="c" * 64, quotas=quotas,
                      input_universes=input_universes)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "NATIONAL_CUSEC_COVERAGE_MUST_EQUAL_36554"):
                NationalCandidateComposer(Path(temporary), **kwargs)


if __name__ == "__main__":
    unittest.main()
