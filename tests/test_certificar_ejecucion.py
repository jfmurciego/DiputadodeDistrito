"""Contrato de certificación técnica consolidada, incluidos informes M06 v1/v2."""
import copy
import unittest

from herramientas.certificar_ejecucion import certify


class TechnicalCertificationTests(unittest.TestCase):
    def evidence(self, *, v2=False):
        decision = {
            "decision": "ADMITTED", "production_authorization": "AUTHORIZED", "territory_id": "aragon",
            "contract": {"contract_sha256": "abc"},
        }
        status = {
            "decision": "PASS_WITH_EXCEPTIONS", "territory_id": "aragon", "run_id": "production-1",
            "from_stage": "M01", "to_stage": "M08", "execution_outcome": "success",
        }
        if v2:
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

    def test_certifies_legacy_v1_governed_exceptions_without_recertification(self):
        result = certify(*self.evidence(), source_commit="a" * 40, workflow_run_id="123")
        self.assertEqual(result["decision"], "CERTIFIED_WITH_GOVERNED_EXCEPTIONS")
        self.assertEqual(result["publication"]["status"], "BLOCKED")
        self.assertEqual(result["errors"], [])

    def test_m06_v2_to_certification_is_certified_with_governed_exceptions(self):
        result = certify(*self.evidence(v2=True), source_commit="a" * 40, workflow_run_id="123")
        self.assertEqual(result["decision"], "CERTIFIED_WITH_GOVERNED_EXCEPTIONS")
        self.assertEqual(result["errors"], [])

    def test_m06_v2_invalid_cause_is_not_proven(self):
        evidence = list(self.evidence(v2=True))
        evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["districts"][0]["causal_exceptions"][0]["type"] = "DISTRICT_ID_POLICY"
        result = certify(*evidence, source_commit="a" * 40, workflow_run_id="123")
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])

    def test_m06_v2_rejects_declared_exception_count_mismatch(self):
        evidence = list(self.evidence(v2=True)); evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["governed_exceptions"] = 2
        result = certify(*evidence, source_commit="a" * 40, workflow_run_id="123")
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])

    def test_m06_v2_rejects_unexplained_component(self):
        evidence = list(self.evidence(v2=True)); evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["districts"][0]["unexplained_components"] = [3]
        result = certify(*evidence, source_commit="a" * 40, workflow_run_id="123")
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])

    def test_m06_v2_rejects_district_based_embedded_policy(self):
        evidence = list(self.evidence(v2=True)); evidence[2] = copy.deepcopy(evidence[2])
        evidence[2]["policy"] = {"allowed": [{"district_id": "7"}]}
        result = certify(*evidence, source_commit="a" * 40, workflow_run_id="123")
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])


if __name__ == "__main__":
    unittest.main()
