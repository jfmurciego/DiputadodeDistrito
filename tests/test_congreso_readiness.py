"""Regresiones de puertas nacionales aisladas con dos unidades N08 reales."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from ddd_core.congreso_readiness import (
    execution_authorization, inspect_three_gates,
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
        self.assertEqual(province["policy_status"], "BLOCKED")
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

    def test_generation_flag_cannot_be_pretended_approved(self):
        changed = copy.deepcopy(self.contract)
        changed["accreditation"]["generation_authorized"] = True
        with self.assertRaisesRegex(ValueError, "PRODUCTION_MUST_REMAIN_DISABLED"):
            provincial_preflight(changed, PRODUCT, "10")


if __name__ == "__main__":
    unittest.main()
