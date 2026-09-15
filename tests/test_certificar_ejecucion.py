"""Contrato de certificación técnica consolidada."""
import unittest

from herramientas.certificar_ejecucion import certify


class TechnicalCertificationTests(unittest.TestCase):
    def evidence(self):
        decision = {
            "decision": "ADMITTED", "production_authorization": "AUTHORIZED", "territory_id": "aragon",
            "contract": {"contract_sha256": "abc"},
        }
        status = {
            "decision": "PASS_WITH_EXCEPTIONS", "territory_id": "aragon", "run_id": "production-1",
            "from_stage": "M01", "to_stage": "M08", "execution_outcome": "success",
        }
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

    def test_certifies_governed_exceptions_without_authorizing_publication(self):
        result = certify(*self.evidence(), source_commit="a" * 40, workflow_run_id="123")
        self.assertEqual(result["decision"], "CERTIFIED_WITH_GOVERNED_EXCEPTIONS")
        self.assertEqual(result["publication"]["status"], "BLOCKED")
        self.assertEqual(result["errors"], [])

    def test_blocks_unproven_geometric_exception(self):
        evidence = list(self.evidence())
        evidence[2]["districts"][0]["atomic_multipart_cause_proven"] = False
        result = certify(*evidence, source_commit="a" * 40, workflow_run_id="123")
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertIn("GEOMETRIC_EXCEPTION_NOT_PROVEN", result["errors"])


if __name__ == "__main__":
    unittest.main()
