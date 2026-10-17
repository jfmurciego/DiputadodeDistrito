"""Synthetic tests for national candidate composition; no territorial run."""
from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path

from ddd_core.congreso_national_composer import (
    NationalCandidateComposer, TRUSTED_CONTRACT_SHA256,
    _read_trusted_bytes, _validate_topology_unit_quota,
)


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


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _product_bundle(root: Path, composer, code: str, rows):
    unit = composer.identity["units"][code]
    artifact_path = root / code / "assignments.json"
    manifest_path = root / code / "manifest.json"
    artifact_path.parent.mkdir(parents=True)
    artifact_bytes = _canonical(rows) + b"\n"
    artifact_path.write_bytes(artifact_bytes)
    manifest = {
        "schema": "ddd.congreso-provincial-candidate-product/1.0",
        "scope": "congreso", "province": code, "module": "M06",
        "synthetic_fixture": True, "generation_authorized": False,
        "certification_status": "NOT_PERFORMED",
        "contract_sha256": composer.identity["contract_sha256"],
        "source_manifest_sha256": composer.identity["source_manifest_sha256"],
        "topology_manifest_sha256": composer.identity["topology_manifest_sha256"],
        "topology_unit_sha256": unit["input_sha256"],
        "universe_sha256": unit["universe_sha256"],
        "quota": unit["quota"], "cusec_count": len(unit["cusecs"]),
        "district_count": len({row["district_id"] for row in rows}),
        "artifact": {"name": "assignments.json",
                     "sha256": hashlib.sha256(artifact_bytes).hexdigest(),
                     "bytes": len(artifact_bytes)},
        "producer": {"tool_path": "modulos/06_consolidar_distritos.py",
                     "tool_sha256": "f" * 64, "commit_sha": "1" * 40,
                     "run_id": "synthetic-fixture-run"},
    }
    manifest["manifest_sha256"] = hashlib.sha256(_canonical(manifest)).hexdigest()
    manifest_path.write_bytes(json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n")
    return manifest_path, artifact_path, manifest


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
            ], synthetic_fixture=True)
            composer.record_province("01", [
                {"cusec": "0100101002", "district_id": "one"},
                {"cusec": "0100101001", "district_id": "one"},
            ], synthetic_fixture=True)
            candidate = composer.compose()
            self.assertEqual(candidate["province_count"], 2)
            self.assertEqual(candidate["district_count"], 3)
            self.assertEqual(candidate["cusec_count"], 5)
            self.assertEqual(candidate["assignments"][0],
                             {"cusec": "0100101001", "district_id": "DDD-01-001"})
            self.assertEqual(candidate["generation_authorized"], False)
            self.assertTrue(candidate["synthetic_fixture"])
            self.assertEqual(candidate["certification_status"], "NOT_PERFORMED")
            self.assertEqual(candidate["candidate_sha256"], _composer(root).compose()["candidate_sha256"])

    def test_resume_binds_checkpoint_and_per_province_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root)
            composer.record_province("01", [
                {"cusec": "0100101001", "district_id": "x"},
                {"cusec": "0100101002", "district_id": "x"},
            ], synthetic_fixture=True)
            resumed = _composer(root)
            with self.assertRaisesRegex(ValueError, "COMPOSITION_UNITS_INCOMPLETE"):
                resumed.compose()
            resumed.record_province("02", [
                {"cusec": "0200201001", "district_id": "x"},
                {"cusec": "0200201002", "district_id": "x"},
                {"cusec": "0200201003", "district_id": "y"},
            ], synthetic_fixture=True)
            resumed.compose()
            artifact = root / "01.json"
            artifact.write_text(artifact.read_text().replace("DDD-01-001", "tampered"))
            with self.assertRaisesRegex(ValueError, "COMPOSITION_ARTIFACT_HASH"):
                _composer(root)

    def test_compose_revalidates_artifact_after_it_was_loaded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root)
            composer.record_province("01", [
                {"cusec": "0100101001", "district_id": "x"},
                {"cusec": "0100101002", "district_id": "x"},
            ], synthetic_fixture=True)
            composer.record_province("02", [
                {"cusec": "0200201001", "district_id": "x"},
                {"cusec": "0200201002", "district_id": "x"},
                {"cusec": "0200201003", "district_id": "y"},
            ], synthetic_fixture=True)
            artifact = root / "01.json"
            artifact.write_text(artifact.read_text().replace("DDD-01-001", "DDD-01-002"))
            with self.assertRaisesRegex(ValueError, "COMPOSITION_ARTIFACT_HASH:01"):
                composer.compose()

    def test_rejects_missing_duplicate_wrong_province_and_quota_mismatches(self):
        with tempfile.TemporaryDirectory() as temporary:
            composer = _composer(Path(temporary))
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_CUSEC_COVERAGE_MISMATCH"):
                composer.record_province("01", [{"cusec": "0100101001", "district_id": "x"}],
                                         synthetic_fixture=True)
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_ASSIGNMENT_VALUE_INVALID"):
                composer.record_province("01", [
                    {"cusec": "0100101001", "district_id": "x"},
                    {"cusec": "0100101001", "district_id": "y"},
                ], synthetic_fixture=True)
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_QUOTA_MISMATCH"):
                composer.record_province("02", [
                    {"cusec": "0200201001", "district_id": "only"},
                    {"cusec": "0200201002", "district_id": "only"},
                    {"cusec": "0200201003", "district_id": "only"},
                ], synthetic_fixture=True)

    def test_rejects_partial_non_synthetic_and_bad_national_quota(self):
        kwargs = dict(contract_sha256="a" * 64, source_manifest_sha256="b" * 64,
                      topology_manifest_sha256="c" * 64,
                      quotas={"01": 1},
                      input_universes={"01": {"cusecs": ["0100101001"],
                                               "input_sha256": "d" * 64}})
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "ACCREDITED_INPUTS_REQUIRED"):
                NationalCandidateComposer(Path(temporary), **kwargs)
        kwargs["synthetic_fixture"] = True
        kwargs["quotas"] = {f"{i:02d}": 1 for i in range(1, 53)}
        kwargs["input_universes"] = {
            f"{i:02d}": {"cusecs": [f"{i:02d}00101001"], "input_sha256": f"{i:064x}"}
            for i in range(1, 53)}
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "NATIONAL_K_MUST_EQUAL_407"):
                NationalCandidateComposer(Path(temporary), **kwargs)

    def test_accredited_path_rejects_caller_supplied_quota_and_fake_contract_sha(self):
        # The accredited factory has no caller-provided quota/hash parameters;
        # a self-consistent-looking quota change cannot replace the approved
        # contract identity.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            contract = root / "contract.json"
            original = json.loads((Path(__file__).resolve().parents[1]
                                   / "territorios/congreso/contrato_congreso_2026.json").read_text())
            rows = original["quotas_by_origin_unit"]
            row01, row02 = next(row for row in rows if row["code"] == "01"), next(
                row for row in rows if row["code"] == "02")
            row01["k"] += 1
            row02["k"] -= 1
            contract.write_text(json.dumps(original))
            with self.assertRaisesRegex(ValueError, "TRUSTED_INPUT_SHA256_MISMATCH:contract"):
                NationalCandidateComposer.from_accredited_inputs(
                    root / "checkpoint", contract_path=contract,
                    source_dir=root, source_parts_dir=root, topology_product_dir=root)
            with self.assertRaises(TypeError):
                NationalCandidateComposer.from_accredited_inputs(
                    root / "checkpoint", contract_path=contract,
                    source_dir=root, source_parts_dir=root, topology_product_dir=root,
                    quotas={"01": 1})

    def test_fake_sha_is_rejected_against_pinned_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "contract.json"
            path.write_bytes(b"{}");
            with self.assertRaisesRegex(ValueError, "TRUSTED_INPUT_SHA256_MISMATCH:contract"):
                _read_trusted_bytes(path, TRUSTED_CONTRACT_SHA256, "contract")

    def test_topology_quota_must_match_the_contract_derived_quota(self):
        _validate_topology_unit_quota("01", 3, {"CPRO": "01", "k": 3})
        with self.assertRaisesRegex(ValueError, "TOPOLOGY_UNIT_QUOTA_MISMATCH:01"):
            _validate_topology_unit_quota("01", 3, {"CPRO": "01", "k": 4})

    def test_memory_staging_requires_explicit_synthetic_fixture_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            composer = _composer(Path(temporary))
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_FIXTURE_REQUIRED"):
                composer.record_province("01", [
                    {"cusec": "0100101001", "district_id": "x"},
                    {"cusec": "0100101002", "district_id": "x"},
                ])

    def test_ingests_existing_synthetic_product_bundle_through_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root / "checkpoint")
            p1 = _product_bundle(root, composer, "01", [
                {"cusec": "0100101001", "district_id": "p"},
                {"cusec": "0100101002", "district_id": "p"},
            ])
            p2 = _product_bundle(root, composer, "02", [
                {"cusec": "0200201001", "district_id": "q"},
                {"cusec": "0200201002", "district_id": "q"},
                {"cusec": "0200201003", "district_id": "r"},
            ])
            composer.record_province_from_product("01", manifest_path=p1[0], artifact_path=p1[1])
            composer.record_province_from_product("02", manifest_path=p2[0], artifact_path=p2[1])
            candidate = composer.compose()
            self.assertTrue(candidate["synthetic_fixture"])
            self.assertEqual(candidate["district_count"], 3)
            self.assertFalse(candidate["generation_authorized"])
            self.assertEqual(candidate["certification_status"], "NOT_PERFORMED")

    def test_compose_revalidates_snapshotted_upstream_product_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root / "checkpoint")
            products = {
                "01": _product_bundle(root, composer, "01", [
                    {"cusec": "0100101001", "district_id": "p"},
                    {"cusec": "0100101002", "district_id": "p"},
                ]),
                "02": _product_bundle(root, composer, "02", [
                    {"cusec": "0200201001", "district_id": "q"},
                    {"cusec": "0200201002", "district_id": "q"},
                    {"cusec": "0200201003", "district_id": "r"},
                ]),
            }
            for code, (manifest_path, artifact_path, _) in products.items():
                composer.record_province_from_product(code, manifest_path=manifest_path,
                                                      artifact_path=artifact_path)
            snapshot = root / "checkpoint/upstream/01.assignments.json"
            snapshot.write_bytes(snapshot.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_PRODUCT_SNAPSHOT_HASH:01"):
                composer.compose()

    def test_upstream_product_rejects_artifact_sha_and_quota_mismatches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            composer = _composer(root / "checkpoint")
            manifest_path, artifact_path, manifest = _product_bundle(root, composer, "01", [
                {"cusec": "0100101001", "district_id": "x"},
                {"cusec": "0100101002", "district_id": "x"},
            ])
            artifact_path.write_bytes(artifact_path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_PRODUCT_ARTIFACT_HASH:01"):
                composer.record_province_from_product("01", manifest_path=manifest_path,
                                                      artifact_path=artifact_path)
            artifact_path.write_bytes(_canonical([
                {"cusec": "0100101001", "district_id": "x"},
                {"cusec": "0100101002", "district_id": "x"},
            ]) + b"\n")
            manifest["quota"] = 2
            body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
            manifest["manifest_sha256"] = hashlib.sha256(_canonical(body)).hexdigest()
            manifest_path.write_bytes(json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n")
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_PRODUCT_IDENTITY_OR_POLICY:01"):
                composer.record_province_from_product("01", manifest_path=manifest_path,
                                                      artifact_path=artifact_path)

    def test_caller_cannot_create_non_synthetic_composer_from_asserted_national_hashes(self):
        quotas = {f"{i:02d}": 1 for i in range(1, 53)}
        quotas["01"] = 356
        input_universes = {
            f"{i:02d}": {"cusecs": [f"{i:02d}00101001"], "input_sha256": f"{i:064x}"}
            for i in range(1, 53)}
        kwargs = dict(contract_sha256="a" * 64, source_manifest_sha256="b" * 64,
                      topology_manifest_sha256="c" * 64, quotas=quotas,
                      input_universes=input_universes)
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "ACCREDITED_INPUTS_REQUIRED"):
                NationalCandidateComposer(Path(temporary), **kwargs)


if __name__ == "__main__":
    unittest.main()
