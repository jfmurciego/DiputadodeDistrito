import json
import unittest
from pathlib import Path

from ddd_core.congreso_contract import (
    CONGRESS_CODES,
    production_blockers,
    validate_congress_identity,
    validate_production_admission,
)


class CongressContractTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "execution_identity": "congreso",
            "territory_id": "espana_congreso",
            "scope": "congreso",
            "metadata_scope": "national",
            "orchestrator": "congress_contract_validator",
            "circumscription_codes": list(CONGRESS_CODES),
        }

    def test_exact_52_scope_admitted_without_authorizing_generation(self):
        result = validate_congress_identity(self.payload)
        self.assertEqual(result["circumscription_count"], 52)
        self.assertEqual(result["province_codes"], list(CONGRESS_CODES[:50]))
        self.assertEqual(result["autonomous_city_codes"], ["51", "52"])
        self.assertFalse(result["generation_authorized"])

    def test_candidate_json_is_structural_only_and_fail_closed(self):
        path = Path(__file__).parents[1] / "territorios/congreso/contrato_congreso_2026.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(validate_congress_identity(contract)["status"], "STRUCTURAL_SCOPE_ADMITTED")
        blockers = production_blockers(contract)
        self.assertIn("OWNER_DECISION_PENDING", blockers)
        self.assertIn("CONGRESS_K_UNDECIDED_OR_INVALID", blockers)
        with self.assertRaisesRegex(ValueError, "CONGRESS_PRODUCTION_BLOCKED"):
            validate_production_admission(contract)

    def test_missing_duplicate_and_unexpected_codes_rejected(self):
        for codes in (list(CONGRESS_CODES[:-1]), list(CONGRESS_CODES[:-1]) + ["01"],
                      list(CONGRESS_CODES[:-1]) + ["53"]):
            payload = {**self.payload, "circumscription_codes": codes}
            with self.subTest(codes=codes[-1]):
                with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
                    validate_congress_identity(payload)

    def test_national_metadata_does_not_replace_execution_identity(self):
        payload = {**self.payload, "execution_identity": "", "scope": "national"}
        with self.assertRaisesRegex(ValueError, "EXECUTION_IDENTITY_MUST_BE_CONGRESO"):
            validate_congress_identity(payload)

    def test_autonomous_catalog_and_manager_are_rejected(self):
        for changes in (
            {"autonomous_territory_ids": ["andalucia"]},
            {"orchestrator": "gestor_campana_nacional"},
            {"k_decision": {"source_scope": "autonomous_parliament"}},
            {"k_decision": {"source_territory_id": "aragon"}},
            {"k_decision": {"source_scope": "congreso", "source_territory_id": "Aragón"}},
            {"k_decision": {"source_scope": "congreso", "source_territory_id": "COMUNIDAD VALENCIANA"}},
        ):
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
                    validate_congress_identity({**self.payload, **changes})

    def test_alternative_autonomous_contamination_fields_are_rejected_recursively(self):
        contaminants = (
            {"autonomous_territories": ["andalucia"]},
            {"territorial_units": ["andalucia"]},
            {"sources": {"population": {"territorial_units": ["andalucia"]}}},
            {"quotas_by_circumscription": [{"code": code, "k": 1, "regional_k": 19} for code in CONGRESS_CODES]},
            {"k_decision": {"total": 52, "source_scope": "congreso", "decision_id": "D-1", "autonomous_parliament_k": 19}},
        )
        for changes in contaminants:
            with self.subTest(changes=list(changes)):
                with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
                    validate_congress_identity({**self.payload, **changes})

    def test_unknown_contract_fields_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "CONTRACT_FIELDS_UNKNOWN"):
            validate_congress_identity({**self.payload, "regional_input": ["andalucia"]})

    def test_nested_k_and_territory_objects_are_closed(self):
        for value in (
            {"aragon": 19},
            {"x": {"k": 19, "territory": "aragon"}},
            {"project_precedent": {"parlamento_autonomico_k": 19}},
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
                    validate_congress_identity({**self.payload, "k_alternatives": value})

    def test_non_json_tuple_container_cannot_bypass_nested_schema(self):
        payload = {**self.payload, "k_alternatives": {
            "analytical_scenarios_not_decisions": ({"k": 19, "territory": "aragon"},)
        }}
        with self.assertRaisesRegex(ValueError, "CONGRESS_CONTRACT_INVALID"):
            validate_congress_identity(payload)

    def test_non_string_code_rejected_without_type_error(self):
        payload = {**self.payload, "circumscription_codes": list(CONGRESS_CODES[:-1]) + [None]}
        with self.assertRaisesRegex(ValueError, "CIRCUMSCRIPTION_CODES_MUST_BE_STRING_LIST"):
            validate_congress_identity(payload)

    def test_autonomous_cities_cannot_be_mislabeled_as_provinces(self):
        rows = [{"code": code, "class": "province"} for code in CONGRESS_CODES]
        payload = {**self.payload, "circumscription_codes": None, "circumscriptions": rows}
        with self.assertRaisesRegex(ValueError, "CIRCUMSCRIPTION_CLASSIFICATION_INVALID"):
            validate_congress_identity(payload)

    def test_conflicting_universe_representations_are_rejected(self):
        payload = {
            **self.payload,
            "circumscriptions": [{"code": "andalucia", "class": "autonomous_community"}],
        }
        with self.assertRaisesRegex(ValueError, "CIRCUMSCRIPTION_REPRESENTATIONS_CONFLICT"):
            validate_congress_identity(payload)

    def test_invalid_circumscriptions_container_is_rejected(self):
        payload = {**self.payload, "circumscriptions": {"territory_id": "andalucia"}}
        with self.assertRaisesRegex(ValueError, "CIRCUMSCRIPTIONS_MUST_BE_LIST"):
            validate_congress_identity(payload)

    def test_nested_territory_metadata_is_rejected(self):
        rows = [{"code": code, "class": "province"} for code in CONGRESS_CODES]
        rows[0]["territory_id"] = "andalucia"
        payload = {**self.payload, "circumscription_codes": list(CONGRESS_CODES), "circumscriptions": rows}
        with self.assertRaisesRegex(ValueError, "CIRCUMSCRIPTION_CLASSIFICATION_INVALID"):
            validate_congress_identity(payload)

    def test_same_universe_in_different_order_is_admitted(self):
        rows = [{"code": code, "class": "province"} for code in CONGRESS_CODES[:50]]
        rows += [{"code": code, "class": "autonomous_city"} for code in CONGRESS_CODES[50:]]
        rows.reverse()
        payload = {**self.payload, "circumscriptions": rows}
        self.assertEqual(validate_congress_identity(payload)["circumscription_count"], 52)

    def test_bad_quota_types_fail_closed(self):
        contract = {
            **self.payload,
            "institutional_decision": {"status": "APPROVED_BY_OWNER"},
            "k_decision": {"total": 52, "source_scope": "congreso", "decision_id": "D-1"},
            "quotas_by_circumscription": [{"code": []} for _ in range(52)],
        }
        self.assertIn("CIRCUMSCRIPTION_QUOTAS_MUST_COVER_52_CODES_EXACTLY", production_blockers(contract))

    def test_missing_province_barrier_fails_closed(self):
        contract = {
            **self.payload,
            "institutional_decision": {"status": "APPROVED_BY_OWNER"},
            "k_decision": {"total": 52, "source_scope": "congreso", "decision_id": "D-1"},
            "barriers": {"province_circumscription": "soft"},
        }
        self.assertIn("MANDATORY_CIRCUMSCRIPTION_BARRIERS_MISSING_OR_INVALID", production_blockers(contract))


if __name__ == "__main__":
    unittest.main()
