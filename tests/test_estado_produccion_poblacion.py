"""Matriz sintética de la puerta poblacional del estado de producción."""
import unittest
from pathlib import Path

from herramientas.estado_produccion import (
    HARD_BLOCK,
    TARGET_IMPROVED_NOT_MET,
    TARGET_MET,
    TARGET_NOT_MET,
    build_production_status,
    population_dimension,
)


def m05(*, before=(0, 1, 0.13, 0.13, 10), after=(0, 0, 0.11, 0.11, 9), result="REPAIRED", baseline=False, termination="REPAIRED"):
    return {"population_repair": {
        "result": result,
        "objective_before": list(before),
        "objective_after": list(after),
        "termination_reason": termination,
        "baseline_restored": baseline,
    }}


def geometry(decision="PASS"):
    if decision == "PASS":
        return {
            "schema": "ddd.geometric-components-audit/2.0", "decision": "PASS",
            "governed_exceptions": 0, "blocked_districts": 0,
            "policy_mismatches": 0, "contract_blockers": [], "districts": [],
        }
    return {
        "schema": "ddd.geometric-components-audit/2.0", "decision": "PASS_WITH_EXCEPTIONS",
        "governed_exceptions": 1, "blocked_districts": 0,
        "policy_mismatches": 0, "contract_blockers": [],
        "districts": [{
            "district_id": "fixture", "decision": "PASS_WITH_EXCEPTIONS",
            "unexplained_components": [],
            "causal_exceptions": [{
                "type": "GOVERNED_BRIDGE", "components": [1, 2],
                "endpoints": ["a", "b"], "contract_sha256": "c" * 64,
                "source": "contract:topology_bridges[0]",
            }],
        }],
    }


def status(report, *, geo="PASS", execution="success"):
    return build_production_status(
        territory_id="fixture", params="fixture.yaml", run_id="production-fixture",
        from_stage="M05", to_stage="M06", execution_outcome=execution,
        geometric_outcome="success" if execution == "success" else "failure",
        geometric_decision=geo, m05_report=report, geometric_audit=geometry(geo),
    )


class ProductionPopulationGateTests(unittest.TestCase):
    def test_population_decision_matrix(self):
        self.assertEqual(population_dimension(m05())["population_decision"], TARGET_MET)
        improved = m05(before=(0, 4, .25, 1.0, 10), after=(0, 3, .25, .9, 9), result="IMPROVED_NOT_REPAIRED")
        self.assertEqual(population_dimension(improved)["population_decision"], TARGET_IMPROVED_NOT_MET)
        not_met = m05(before=(0, 4, .25, 1.0, 10), after=(0, 4, .25, .9, 9), result="NO_FEASIBLE_REPAIR_FOUND", baseline=True)
        self.assertEqual(population_dimension(not_met)["population_decision"], TARGET_NOT_MET)
        hard = m05(before=(1, 1, .13, .13, 10), after=(1, 0, .11, .11, 9))
        self.assertEqual(population_dimension(hard)["population_decision"], HARD_BLOCK)

    def test_population_met_and_geometry_pass_is_certifiable(self):
        result = status(m05(), geo="PASS")
        self.assertEqual(result["decision"], "PASS")
        self.assertNotIn("block_cause", result)

    def test_population_met_and_causal_geometry_is_certifiable_with_exceptions(self):
        result = status(m05(), geo="PASS_WITH_EXCEPTIONS")
        self.assertEqual(result["decision"], "PASS_WITH_EXCEPTIONS")

    def test_population_improved_but_not_met_blocks(self):
        report = m05(before=(0, 4, .25, 1.0, 10), after=(0, 3, .25, .9, 9), result="IMPROVED_NOT_REPAIRED")
        result = status(report)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "POPULATION_TARGET_NOT_MET")

    def test_population_not_improved_blocks(self):
        report = m05(before=(0, 4, .25, 1.0, 10), after=(0, 4, .25, .9, 9), result="NO_FEASIBLE_REPAIR_FOUND", baseline=True)
        result = status(report)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["population_decision"], TARGET_NOT_MET)

    def test_hard_limit_blocks(self):
        report = m05(before=(1, 1, .13, .13, 10), after=(1, 0, .11, .11, 9))
        result = status(report)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "POPULATION_HARD_BLOCK")

    def test_execution_failure_blocks(self):
        result = status(m05(), execution="failure")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "EXECUTION_FAILED")

    def test_run_35199668216_regression(self):
        report = m05(
            before=(0, 4, 0.255430466417, 4.096682479455, 2026),
            after=(0, 3, 0.255430466417, 4.096682479455, 2016),
            result="IMPROVED_NOT_REPAIRED",
            baseline=False,
            termination="CANDIDATE_BUDGET_EXHAUSTED",
        )
        result = build_production_status(
            territory_id="castilla_y_leon", params="fixture.yaml", run_id="production-35199668216-1",
            from_stage="M05", to_stage="M06", execution_outcome="success",
            geometric_outcome="success", geometric_decision="PASS_WITH_EXCEPTIONS",
            m05_report=report, geometric_audit=geometry("PASS_WITH_EXCEPTIONS"),
        )
        self.assertEqual(result["population_decision"], TARGET_IMPROVED_NOT_MET)
        self.assertEqual(result["geometric_decision"], "PASS_WITH_EXCEPTIONS")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "POPULATION_TARGET_NOT_MET")

    def test_m06_execution_is_not_gated_by_population_certification(self):
        workflow = Path(".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        m06_block = workflow.split("  m06:\n", 1)[1].split("\n  auditoria:\n", 1)[0]
        self.assertIn("needs.m05.result != 'failure'", m06_block)
        self.assertNotIn("population_decision", m06_block)


if __name__ == "__main__":
    unittest.main()
