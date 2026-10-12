"""N08: políticas generales aprobadas, esquema estricto y bloqueos conservados."""
import copy
import json
import math
import unittest
from decimal import Decimal
from pathlib import Path

from ddd_core.config import hard_limits
from ddd_core.congreso_contract import (
    production_blockers, validate_congress_identity, validate_production_admission,
)
from ddd_core.congreso_readiness import national_readiness, execution_authorization

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
DOSSIER = ROOT / "docs/ESTUDIOS/N08_POLITICA_INSTITUCIONAL_20261013"
SOURCE_MANIFEST = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto/manifest.json"
POLICIES = (
    "minimum_unit", "contiguity", "population_limits",
    "municipal_indivisibility", "islands", "enclaves",
    "physical_discontinuities",
)
DECISION_ID = "N08-OWNER-20261013-7RULES"


class CongressOwnerPolicyApprovalTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_approved_contract_retains_n06_sources_and_blocks_production(self):
        info = validate_congress_identity(self.contract)
        self.assertEqual(info["electoral_district_count"], 407)
        self.assertFalse(info["generation_authorized"])
        self.assertEqual(self.contract["metadata"]["version"], "0.4.0")
        self.assertTrue(all(
            self.contract["decisions"][name]["status"] == "APPROVED"
            and self.contract["decisions"][name]["decision_id"] == DECISION_ID
            for name in POLICIES
        ))
        self.assertEqual(self.contract["minimum_unit"]["value"],
                         self.contract["decisions"]["minimum_unit"]["value"])
        self.assertEqual(self.contract["population_reference"]["year"], 2025)
        self.assertEqual(self.contract["sources"]["geometry"]["edition"], 2025)
        self.assertEqual(self.contract["sources"]["population"]["edition"], 2025)
        self.assertFalse(self.contract["accreditation"]["generation_authorized"])
        self.assertIn("CIRCUMSCRIPTION_COVERAGE_NOT_ACCREDITED_52_OF_52",
                      production_blockers(self.contract))
        self.assertEqual(national_readiness(self.contract)["status"], "BLOCKED")
        with self.assertRaisesRegex(ValueError, "CONGRESS_PRODUCTION_BLOCKED"):
            validate_production_admission(self.contract)

    def test_owner_acta_is_separate_from_unchanged_historical_proposal(self):
        acta = json.loads((DOSSIER / "ACTA_APROBACION.json").read_text())
        proposal = json.loads((DOSSIER / "PROPUESTA_DECISIONES.json").read_text())
        self.assertEqual(acta["status"], "APPROVED_BY_OWNER")
        self.assertEqual(acta["decision_id"], DECISION_ID)
        self.assertEqual(proposal["status"], "NOT_APPROVED")
        self.assertEqual(set(acta["approved_rules"]), set(POLICIES))
        self.assertEqual(acta["explicitly_not_approved"]["case_specific_exceptions"], [])
        self.assertFalse(acta["generation_authorized"])
        for name in POLICIES:
            self.assertEqual(self.contract["decisions"][name]["value"],
                             proposal["decisions"][name]["proposed_contract_value"])
        self.assertEqual(self.contract["k_decision"]["decision_id"], "N06-OWNER-20261012-K")

    def test_hard_limits_use_declared_provincial_mean(self):
        policy = self.contract["decisions"]["population_limits"]["value"]
        for population, k in ((388190, 3), (593623, 5)):
            target, floor, cap, tol = hard_limits(
                {"validation": policy}, k=k, total_pop=population)
            self.assertAlmostEqual(target, population/k)
            self.assertAlmostEqual(floor, target * .85)
            self.assertAlmostEqual(cap, target * 1.15)
            self.assertAlmostEqual(tol, target * .15)
            exact_lower = (17*population + 20*k - 1) // (20*k)
            exact_upper = (23*population) // (20*k)
            self.assertEqual(exact_lower, math.ceil(Decimal(17)*population/(20*k)))
            self.assertEqual(exact_upper, math.floor(Decimal(23)*population/(20*k)))

    def test_any_missing_or_corrupt_population_coefficient_fails_closed(self):
        invalid = [
            {},
            {"population_floor_ratio": .85, "population_cap_ratio": 1.15},
            {"population_floor_ratio": .85, "population_cap_ratio": 1.15,
             "target_tolerance_ratio": .15, "regional_k": 19},
            {"population_floor_ratio": True, "population_cap_ratio": 1.15,
             "target_tolerance_ratio": .15},
            {"population_floor_ratio": "0.85", "population_cap_ratio": 1.15,
             "target_tolerance_ratio": .15},
            {"population_floor_ratio": float("nan"), "population_cap_ratio": 1.15,
             "target_tolerance_ratio": .15},
            {"population_floor_ratio": .85, "population_cap_ratio": float("inf"),
             "target_tolerance_ratio": .15},
            {"population_floor_ratio": .8, "population_cap_ratio": 1.15,
             "target_tolerance_ratio": .15},
            {"population_floor_ratio": 1.15, "population_cap_ratio": .85,
             "target_tolerance_ratio": .15},
        ]
        for value in invalid:
            bad = copy.deepcopy(self.contract)
            bad["decisions"]["population_limits"]["value"] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
                    validate_congress_identity(bad)
                self.assertTrue(production_blockers(bad))

    def test_approved_policy_requires_value_provenance_and_consistency(self):
        mutations = []
        for policy in POLICIES:
            for field, value in (("decision_id", ""), ("value", None)):
                bad = copy.deepcopy(self.contract)
                bad["decisions"][policy][field] = value
                mutations.append(bad)
        bad = copy.deepcopy(self.contract)
        bad["minimum_unit"]["value"] = "municipio"
        mutations.append(bad)
        for bad in mutations:
            with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
                validate_congress_identity(bad)

    def test_published_n08_provenance_stays_historical(self):
        product = json.loads(SOURCE_MANIFEST.read_text())
        self.assertFalse(product["generation_authorized"])
        self.assertNotEqual(
            product["evidence"]["contract_sha256"],
            __import__("hashlib").sha256(CONTRACT.read_bytes()).hexdigest(),
            "Changed owner policy must not impersonate pre-existing N08 product accreditation.",
        )

    def test_evidence_only_cannot_activate_generation(self):
        privileged = {
            "input_status": "PASS_INPUTS_ONLY", "policy_status": "POLICY_DECLARED",
            "territorial_cautions": [], "structural_necessary_condition": True,
        }
        gate = execution_authorization(privileged, {"status": "CONTRACT_ADMITTED_ONLY"})
        self.assertEqual(gate["status"], "DENIED")
        self.assertFalse(gate["generation_authorized"])
        self.assertIn("EXPRESS_OWNER_EXECUTION_ORDER_ABSENT", gate["blockers"])


if __name__ == "__main__":
    unittest.main()
