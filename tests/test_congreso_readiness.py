"""Regresiones de puertas nacionales aisladas con dos unidades N08 reales."""
import copy
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ddd_core.congreso_readiness import (
    N08_TRUSTED_MANIFEST_SHA256, execution_authorization, inspect_three_gates,
    national_readiness, provincial_preflight,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
PRODUCT = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"


class CongressThreeGatesTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_caceres_real_topology_and_independent_national_block(self):
        gates = inspect_three_gates(self.contract, PRODUCT, "10")
        province = gates["provincial"]
        self.assertEqual(
            (province["province"], province["sections"], province["population"],
             province["k"], province["edges"]),
            ("10", 411, 388190, 3, 1125),
        )
        self.assertEqual(province["input_status"], "PASS_INPUTS_ONLY")
        self.assertEqual(province["policy_status"], "POLICY_DECLARED")
        self.assertFalse(province["structural_feasibility_proven"])
        self.assertEqual(gates["national"]["status"], "BLOCKED")
        self.assertIn("CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52",
                      gates["national"]["blockers"])
        self.assertEqual(gates["execution"]["status"], "DENIED")
        self.assertFalse(gates["execution"]["generation_authorized"])

    def test_second_real_province_not_hardcoded_to_caceres(self):
        province = provincial_preflight(self.contract, PRODUCT, "01")
        self.assertEqual(
            (province["province"], province["sections"], province["population"],
             province["k"], province["edges"]),
            ("01", 240, 341961, 3, 628),
        )
        self.assertEqual(province["input_status"], "PASS_INPUTS_ONLY")
        self.assertTrue(province["structural_necessary_condition"])
        self.assertFalse(province["generation_authorized"])

    def test_five_original_cpro_products_fail_connected_population_budget(self):
        expected = {
            "07": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
            "09": "PHYSICAL_COMPONENTS_EXCEED_K",
            "17": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
            "34": "PHYSICAL_COMPONENTS_EXCEED_K",
            "36": "COMPONENT_POPULATION_BOUNDS_IMPOSSIBLE",
        }
        for cpro, reason in expected.items():
            with self.subTest(CPRO=cpro):
                province = provincial_preflight(self.contract, PRODUCT, cpro)
                self.assertFalse(province["structural_necessary_condition"])
                self.assertFalse(province["structural_feasibility_proven"])
                self.assertEqual(province["structural_necessary_reason"], reason)
                self.assertIn(reason, province["territorial_cautions"])
                self.assertFalse(province["generation_authorized"])
                national = national_readiness(self.contract)
                execution = execution_authorization(province, national)
                self.assertEqual(execution["status"], "DENIED")
                self.assertIn("PROVINCIAL_STRUCTURAL_BLOCK", execution["blockers"])
        # A positive necessary bound is not a generated or certified district.
        almeria = provincial_preflight(self.contract, PRODUCT, "04")
        self.assertTrue(almeria["structural_necessary_condition"])
        self.assertFalse(almeria["structural_feasibility_proven"])
        self.assertFalse(almeria["generation_authorized"])

    def test_missing_national_coverage_does_not_veto_input_diagnostics(self):
        local = copy.deepcopy(self.contract)
        local["circumscription_accreditation"] = []
        provincial = provincial_preflight(local, PRODUCT, "10")
        national = national_readiness(local)
        self.assertEqual(provincial["input_status"], "PASS_INPUTS_ONLY")
        self.assertEqual(national["status"], "BLOCKED")
        self.assertFalse(execution_authorization(provincial, national)["generation_authorized"])

    def test_any_execution_order_is_still_absent(self):
        provincial = {
            "input_status": "PASS_INPUTS_ONLY", "policy_status": "POLICY_DECLARED",
            "territorial_cautions": [], "structural_necessary_condition": True,
        }
        national = {"status": "CONTRACT_ADMITTED_ONLY"}
        gate = execution_authorization(provincial, national)
        self.assertEqual(gate["status"], "DENIED")
        self.assertIn("EXPRESS_OWNER_EXECUTION_ORDER_ABSENT", gate["blockers"])
        self.assertFalse(gate["generation_authorized"])

    def test_bad_province_and_quota_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "PROVINCE_CODE_INVALID"):
            provincial_preflight(self.contract, PRODUCT, "99")
        changed = copy.deepcopy(self.contract)
        next(row for row in changed["quotas_by_origin_unit"] if row["code"] == "10")["k"] = 4
        with self.assertRaisesRegex(ValueError, "N06_QUOTAS_INVALID|PROVINCIAL_K_MISMATCH"):
            provincial_preflight(changed, PRODUCT, "10")

    def test_corrupted_unit_rejected_by_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            (temporary / "unidades").mkdir()
            (temporary / "manifest.json").write_bytes((PRODUCT / "manifest.json").read_bytes())
            original = (PRODUCT / "unidades/10.json.gz").read_bytes()
            (temporary / "unidades/10.json.gz").write_bytes(original + b"tampered")
            with self.assertRaisesRegex(ValueError, "PROVINCIAL_ARTIFACT_HASH"):
                provincial_preflight(self.contract, temporary, "10")

    def test_n08_manifest_uses_external_trust_anchor_not_its_own_hashes(self):
        manifest_bytes = (PRODUCT / "manifest.json").read_bytes()
        self.assertEqual(hashlib.sha256(manifest_bytes).hexdigest(),
                         N08_TRUSTED_MANIFEST_SHA256)
        self.assertFalse(self.contract["accreditation"]["generation_authorized"])

    def test_forged_caceres_population_rehashed_manifest_still_rejected(self):
        """An internally coherent malicious manifest must not self-authorize."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "unidades").mkdir()
            manifest = json.loads((PRODUCT / "manifest.json").read_bytes())
            original = gzip.decompress((PRODUCT / "unidades/10.json.gz").read_bytes())
            unit = json.loads(original)
            unit["nodes"][0]["pop"] += 1
            unit["summary"]["population"] += 1
            # Attackers can recompute the blob hash, canonical hash, size,
            # self-declared manifest identity and all local receipts.
            forged_raw = (json.dumps(unit, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False)
                          .encode("utf-8") + b"\\n")
            forged_blob = gzip.compress(forged_raw, mtime=0)
            (root / "unidades/10.json.gz").write_bytes(forged_blob)
            ref = manifest["artifacts"]["unidades/10.json.gz"]
            ref["sha256"] = hashlib.sha256(forged_blob).hexdigest()
            ref["bytes"] = len(forged_blob)
            ref["canonical_json_sha256"] = hashlib.sha256(forged_raw).hexdigest()
            plain = json.dumps({k: v for k, v in manifest.items()
                                if k != "identity_sha256"},
                               sort_keys=True, ensure_ascii=False,
                               separators=(",", ":"), allow_nan=False).encode("utf-8")
            manifest["identity_sha256"] = hashlib.sha256(plain).hexdigest()
            (root / "manifest.json").write_bytes(
                json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\\n")
            self.assertNotEqual(hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
                                N08_TRUSTED_MANIFEST_SHA256)
            with self.assertRaisesRegex(ValueError, "N08_MANIFEST_TRUST_ANCHOR_MISMATCH"):
                provincial_preflight(self.contract, root, "10")

    def test_reformatted_manifest_even_with_unchanged_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = json.loads((PRODUCT / "manifest.json").read_bytes())
            (root / "manifest.json").write_text(json.dumps(original, indent=2) + "\\n")
            with self.assertRaisesRegex(ValueError, "N08_MANIFEST_TRUST_ANCHOR_MISMATCH"):
                provincial_preflight(self.contract, root, "10")

    def test_generation_flag_cannot_be_pretended_approved(self):
        changed = copy.deepcopy(self.contract)
        changed["accreditation"]["generation_authorized"] = True
        with self.assertRaisesRegex(ValueError, "GENERATION_AUTHORIZATION_MUST_REMAIN_FALSE"):
            provincial_preflight(changed, PRODUCT, "10")


if __name__ == "__main__":
    unittest.main()
