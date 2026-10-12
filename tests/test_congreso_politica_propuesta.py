"""Contrato inmutable y trazabilidad del paquete de siete decisiones sin aprobar."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/ESTUDIOS/N08_POLITICA_INSTITUCIONAL_20261013"
N08 = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012"
CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
REQUIRED = {
    "minimum_unit", "contiguity", "population_limits",
    "municipal_indivisibility", "islands", "enclaves",
    "physical_discontinuities",
}


class CongressInstitutionalPolicyCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = json.loads((DOCS / "PROPUESTA_DECISIONES.json").read_text())
        cls.contract = json.loads(CONTRACT.read_text())
        cls.options = json.loads((N08 / "FACTIBILIDAD_OPCIONES.json").read_text())

    def test_no_owner_approval_or_generation_is_inferred(self):
        self.assertEqual(self.proposal["status"], "NOT_APPROVED")
        self.assertFalse(self.proposal["generation_authorized"])
        self.assertFalse(self.proposal["production_contract_modified"])
        self.assertEqual(set(self.proposal["decisions"]), REQUIRED)
        self.assertTrue(all(
            item["status"] == "NOT_APPROVED"
            for item in self.proposal["decisions"].values()
        ))
        self.assertEqual(self.proposal["exception_registry"]["approved_cases"], [])

    def test_live_contract_still_waits_for_seven_owner_decisions(self):
        self.assertEqual(self.contract["k_decision"]["total"], 407)
        self.assertEqual(self.contract["k_decision"]["status"], "APPROVED_BY_OWNER")
        self.assertFalse(self.contract["accreditation"]["generation_authorized"])
        self.assertTrue(all(
            self.contract["decisions"][name]["status"] == "WAIT_OWNER"
            for name in REQUIRED
        ))

    def test_selected_scenario_matches_existing_n08_options(self):
        chosen = next(
            option for option in self.options["options"]
            if option["basis"] == "provincial_mean" and option["tolerance"] == "3/20"
        )
        impact = self.proposal["national_impact_under_proposed_limits"]
        self.assertEqual(
            impact["section_graph_arithmetic_blocked_codes"],
            chosen["component_arithmetic_blocked"],
        )
        self.assertEqual(impact["section_graph_arithmetic_blocked_origin_units"], 16)
        self.assertEqual(
            impact["absolute_municipal_indivisibility_incompatible_units"],
            len(chosen["municipal_indivisibility_blocked"]),
        )
        self.assertEqual(
            impact["municipalities_above_ordinary_upper_bound"],
            chosen["municipalities_requiring_split"],
        )
        self.assertEqual(
            impact["sections_above_ordinary_upper_bound"],
            chosen["sections_above_upper"],
        )
        self.assertEqual(len(impact["physical_part_components_exceed_K_codes"]), 9)

    def test_integer_bounds_are_exact_on_both_cases(self):
        proposed = self.proposal["decisions"]["population_limits"]
        self.assertEqual(proposed["tolerance_fraction"], "3/20")
        self.assertEqual(
            proposed["proposed_contract_value"],
            {
                "population_floor_ratio": 0.85,
                "population_cap_ratio": 1.15,
                "target_tolerance_ratio": 0.15,
            },
        )
        chosen = next(
            option for option in self.options["options"]
            if option["basis"] == "provincial_mean" and option["tolerance"] == "3/20"
        )
        for name, code in [("caceres", "10"), ("cantabria", "39")]:
            case = self.proposal["pilot_diagnostics"][name]
            official = next(r for r in chosen["units"] if r["CPRO"] == code)
            self.assertEqual(case["K"], int(self.contract["quotas_by_origin_unit"][
                [row["code"] for row in self.contract["quotas_by_origin_unit"]].index(code)
            ]["k"]))
            pop, k = case["population"], case["K"]
            floor = (17 * pop + 20 * k - 1) // (20 * k)
            cap = (23 * pop) // (20 * k)
            self.assertEqual((case["integer_floor"], case["integer_cap"]), (floor, cap))
            self.assertFalse(official["feasibility_proven"])
            self.assertEqual(case["arithmetic_component_impossibility_detected"],
                             official["arithmetic_impossibility_section_graph"])

    def test_exception_policy_never_silently_creates_legal_or_physical_edges(self):
        registry = self.proposal["exception_registry"]
        fields = set(registry["required_identity_fields"])
        self.assertTrue({
            "CPRO", "source_sha256", "topology_unit_sha256",
            "owner_decision_id", "official_administrative_evidence",
        } <= fields)
        self.assertEqual(registry["status"], "NOT_APPROVED")
        self.assertTrue(self.proposal["electoral_districts_are_uninominal"])


if __name__ == "__main__":
    unittest.main()
