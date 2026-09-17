"""Contrato de certificación técnica consolidada, incluidos población M05 e informes M06 v1/v2."""
import copy
import unittest

from herramientas.certificar_ejecucion import certify


class TechnicalCertificationTests(unittest.TestCase):
    def evidence(self, *, v2=False, geometric_decision="PASS_WITH_EXCEPTIONS"):
        decision = {
            "decision": "ADMITTED", "production_authorization": "AUTHORIZED", "territory_id": "aragon",
            "contract": {"contract_sha256": "abc"},
        }
        status = {
            "decision": geometric_decision, "territory_id": "aragon", "run_id": "production-1",
            "from_stage": "M01", "to_stage": "M08", "execution_outcome": "success",
            "population_outcome": "success", "population_decision": "TARGET_MET",
            "population_repair_result": "REPAIRED", "population_outliers_before": 1,
            "population_outliers_after": 0, "population_max_deviation_before": 0.13,
            "population_max_deviation_after": 0.11, "population_termination_reason": "REPAIRED",
            "population_baseline_restored": False, "population_hard_constraints_before": 0,
            "population_hard_constraints_after": 0,
        }
        if v2:
            if geometric_decision == "PASS":
                audit = {
                    "schema": "ddd.geometric-components-audit/2.0", "decision": "PASS",
                    "connected_districts": 67, "governed_exceptions": 0, "blocked_districts": 0,
                    "policy_mismatches": 0, "contract_blockers": [], "districts": [],
                }
            else:
                audit = {
                    "schema": "ddd.geometric-components-audit/2.0",
                    "decision": "PASS_WITH_EXCEPTIONS", "connected_districts": 66,
                    "governed_exceptions": 1, "blocked_districts": 0, "policy_mismatches": 0,
                    "contract_blockers": [], "districts": [{
                        "district_id": "renumberable-label", "decision": "PASS_WITH_EXCEPTIONS",
                        "geometry_sha256": "g" * 64, "contract_sha256": "c" * 64,
                        "unexplained_components": [],
                        "causal_exceptions": [{
                            "type": "GOVERNED_BRIDGE", "endpoints": ["001", "002"],
                            "components": [1, 2], "source": "contract:topology_bridges[0]",
                            "geometry_sha256": "g" * 64, "contract_sha256": "c" * 64,
                        }],
                    }],
                }
        else:
            audit = {
                "decision": "PASS_WITH_EXCEPTIONS", "connected_districts": 60,
                "governed_exceptions": 1, "blocked_districts": 0, "policy_mismatches": 0,
                "contract_blockers": [], "districts": [{
                    "status": "GOVERNED_EXCEPTION", "policy_applied": True,
                    "atomic_multipart_cause_proven": True,
                }],
            }
        manifest = {"run_id": "production-1", "outputs": {
            "x_m06_distritos.geojson.zip": {"sha256": "1"},
            "x_m07_reconciliacion.json": {"sha256": "2"},
            "x_m08_distritos_resultados.geojson.zip": {"sha256": "3"},
        }}
        validation = {
            "run_id": "production-1", "estado": "PASS", "failures": [],
            "expected_districts": 67, "districts_found": 67,
        }
        reconciliation = {
            "status": "PASS_WITH_DECLARED_EXCEPTIONS", "input_votes": 100,
            "assigned_votes": 99, "unassigned_votes": 1, "errors": [],
        }
        return decision, status, audit, manifest, validation, reconciliation

    def certify_evidence(self, evidence):
        return certify(*evidence, source_commit="a" * 40, workflow_run_id="123")

    def test_population_met_geometry_pass_is_certifiable(self):
        result = self.certify_evidence(self.evidence(v2=True, geometric_decision="PASS"))
        self.assertNotEqual(result["decision"], "BLOCKED")
        self.assertEqual(result["errors"], [])

    def test_population_met_geometry_causal_is_certifiable_with_exceptions(self):
        result = self.certify_evidence(self.evidence(v2=True))
        self.assertEqual(result["decision"], "CERTIFIED_WITH_GOVERNED_EXCEPTIONS")
        self.assertEqual(result["errors"], [])

    def test_population_improved_not_met_is_blocked(self):
        evidence = list(self.evidence(v2=True))
        evidence[1] = copy.deepcopy(evidence[1])
        evidence[1].update(decision="BLOCK", population_decision="TARGET_IMPROVED_NOT_MET", population_outliers_after=3)
        result = self.certify_evidence(evidence)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("POPULATION_TARGET_NOT_MET", result["errors"])

    def test_population_not_improved_is_blocked(self):
        evidence = list(self.evidence(v2=True))
        evidence[1] = copy.deepcopy(evidence[1])
        evidence[1].update(decision="BLOCK", population_decision="TARGET_NOT_MET", population_outliers_after=4)
        result = self.certify_evidence(evidence)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("POPULATION_TARGET_NOT_MET", result["errors"])

    def test_population_hard_limit_is_blocked(self):
        evidence = list(self.evidence(v2=True))
        evidence[1] = copy.deepcopy(evidence[1])
        evidence[1].update(decision="BLOCK", population_decision="HARD_BLOCK", population_hard_constraints_after=1)
        result = self.certify_evidence(evidence)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("POPULATION_HARD_BLOCK", result["errors"])
        self.assertIn("POPULATION_HARD_CONSTRAINTS", result["errors"])

    def test_execution_failed_is_blocked(self):
        evidence = list(self.evidence(v2=True))
        evidence[1] = copy.deepcopy(evidence[1])
        evidence[1].update(decision="BLOCK", execution_outcome="failure")
        result = self.certify_evidence(evidence)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("EXECUTION_FAILED", result["errors"])

    def test_certifies_legacy_v1_governed_exceptions_when_population_met(self):
        result = self.certify_evidence(self.evidence())
        self.assertEqual(result["decision"], "CERTIFIED_WITH_GOVERNED_EXCEPTIONS")
        self.assertEqual(result["publication"]["status"], "BLOCKED")
        self.assertEqual(result["errors"], [])

    def test_m06_v2_invalid_cause_is_not_proven(self):
        evidence = list(self.evidence(v2=True))
        evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["districts"][0]["causal_exceptions"][0]["type"] = "DISTRICT_ID_POLICY"
        result = self.certify_evidence(evidence)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])

    def test_m06_v2_rejects_declared_exception_count_mismatch(self):
        evidence = list(self.evidence(v2=True)); evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["governed_exceptions"] = 2
        result = self.certify_evidence(evidence)
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])

    def test_m06_v2_rejects_unexplained_component(self):
        evidence = list(self.evidence(v2=True)); evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["districts"][0]["unexplained_components"] = [3]
        result = self.certify_evidence(evidence)
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])

    def test_m06_v2_rejects_district_based_embedded_policy(self):
        evidence = list(self.evidence(v2=True)); evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["policy"] = {"allowed": [{"district_id": "7"}]}
        result = self.certify_evidence(evidence)
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])


if __name__ == "__main__":
    unittest.main()
