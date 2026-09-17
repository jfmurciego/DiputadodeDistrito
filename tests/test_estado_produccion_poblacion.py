"""Matriz sintética de la puerta poblacional del estado de producción."""
import unittest
from pathlib import Path

from herramientas.estado_produccion import (
    BASE_M05,
    HARD_BLOCK,
    POPULATION_REPAIR,
    SWAP_POLISH,
    TARGET_IMPROVED_NOT_MET,
    TARGET_MET,
    TARGET_NOT_MET,
    build_production_status,
    population_dimension,
)


def repair_report(*, before=(0, 1, 0.13, 0.13, 10), after=(0, 0, 0.11, 0.11, 9), result="REPAIRED", baseline=False, termination="REPAIRED", enabled=True):
    return {"population_repair": {
        "enabled": enabled,
        "result": result,
        "objective_before": list(before),
        "objective_after": list(after),
        "termination_reason": termination,
        "baseline_restored": baseline,
    }}


def base_report(*, before=(0, 0.0, 1, 0.20, 0.30), after=(0, 0.0, 0, 0.11, 0.18), repair_enabled=False):
    return {
        "objective_start": list(before),
        "objective_final": list(after),
        "population_repair": {"enabled": repair_enabled, "result": "NO_FEASIBLE_REPAIR_FOUND"},
    }


def swap_report(*, base_before=(0, 0.0, 2, 0.30, 0.50), base_after=(0, 0.0, 2, 0.25, 0.45), swap_before=(0, 0.0, 2, 0.25, 0.45), swap_after=(0, 0.0, 0, 0.10, 0.18)):
    report = base_report(before=base_before, after=base_after)
    report["swap_polish"] = {
        "enabled": True,
        "accepted_swaps": 2,
        "objective_start": list(swap_before),
        "objective_final": list(swap_after),
    }
    return report


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
    def test_repair_enabled_target_met_uses_repair_indexes(self):
        population = population_dimension(repair_report())
        self.assertEqual(population["population_decision"], TARGET_MET)
        self.assertEqual(population["population_evidence_source"], POPULATION_REPAIR)
        self.assertEqual(population["population_outliers_before"], 1)
        self.assertEqual(population["population_outliers_after"], 0)
        self.assertAlmostEqual(population["population_max_deviation_after"], 0.11)

    def test_repair_enabled_partial_improvement(self):
        report = repair_report(
            before=(0, 4, .25, 1.0, 10),
            after=(0, 3, .20, .9, 9),
            result="IMPROVED_NOT_REPAIRED",
        )
        population = population_dimension(report)
        self.assertEqual(population["population_decision"], TARGET_IMPROVED_NOT_MET)
        self.assertEqual(population["population_evidence_source"], POPULATION_REPAIR)

    def test_disabled_repair_base_zero_outliers_is_target_met(self):
        population = population_dimension(base_report())
        self.assertEqual(population["population_decision"], TARGET_MET)
        self.assertEqual(population["population_evidence_source"], BASE_M05)
        self.assertEqual(population["population_repair_result"], "DISABLED")
        self.assertEqual(population["population_outliers_after"], 0)

    def test_disabled_repair_base_with_outliers_is_target_not_met(self):
        report = base_report(
            before=(0, 0.0, 2, 0.25, 0.45),
            after=(0, 0.0, 2, 0.25, 0.40),
        )
        population = population_dimension(report)
        self.assertEqual(population["population_decision"], TARGET_NOT_MET)
        self.assertEqual(population["population_evidence_source"], BASE_M05)
        self.assertEqual(population["population_outliers_after"], 2)

    def test_swap_polish_precedes_base_and_uses_base_objective_indexes(self):
        population = population_dimension(swap_report())
        self.assertEqual(population["population_evidence_source"], SWAP_POLISH)
        self.assertEqual(population["population_decision"], TARGET_MET)
        self.assertEqual(population["population_outliers_before"], 2)
        self.assertEqual(population["population_outliers_after"], 0)
        self.assertAlmostEqual(population["population_max_deviation_after"], 0.10)

    def test_malformed_or_missing_population_evidence_blocks_explicitly(self):
        malformed = {
            "population_repair": {"enabled": True, "result": "NO_FEASIBLE_REPAIR_FOUND", "objective_before": [0], "objective_after": [0]},
            "objective_start": [0, 0.0, "bad", 0.2],
            "objective_final": [0, 0.0, 1],
        }
        result = status(malformed)
        self.assertEqual(result["population_outcome"], "failure")
        self.assertIsNone(result["population_evidence_source"])
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "M05_POPULATION_EVIDENCE_MISSING")

    def test_aragon_equivalent_fixture_uses_base_without_recertifying_aragon(self):
        report = {
            "objective_start": [0, 0.0, 1, 0.549676430306, 0.425520891068],
            "objective_final": [0, 0.0, 0, 0.119431695687, 0.182704485064],
            "swap_polish": {"enabled": False, "max_swaps": 0, "accepted_swaps": 0},
            "population_repair": {"enabled": False, "result": "NO_FEASIBLE_REPAIR_FOUND"},
        }
        population = population_dimension(report)
        self.assertEqual(population["population_evidence_source"], BASE_M05)
        self.assertEqual(population["population_repair_result"], "DISABLED")
        self.assertEqual(population["population_decision"], TARGET_MET)

    def test_population_met_and_geometry_pass_is_certifiable(self):
        result = status(repair_report(), geo="PASS")
        self.assertEqual(result["decision"], "PASS")
        self.assertNotIn("block_cause", result)

    def test_population_met_and_causal_geometry_is_certifiable_with_exceptions(self):
        result = status(repair_report(), geo="PASS_WITH_EXCEPTIONS")
        self.assertEqual(result["decision"], "PASS_WITH_EXCEPTIONS")

    def test_population_improved_but_not_met_blocks(self):
        report = repair_report(before=(0, 4, .25, 1.0, 10), after=(0, 3, .25, .9, 9), result="IMPROVED_NOT_REPAIRED")
        result = status(report)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "POPULATION_TARGET_NOT_MET")

    def test_population_not_improved_blocks(self):
        report = repair_report(before=(0, 4, .25, 1.0, 10), after=(0, 4, .25, .9, 9), result="NO_FEASIBLE_REPAIR_FOUND", baseline=True)
        result = status(report)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["population_decision"], TARGET_NOT_MET)

    def test_hard_limit_blocks(self):
        report = repair_report(before=(1, 1, .13, .13, 10), after=(1, 0, .11, .11, 9))
        result = status(report)
        self.assertEqual(result["population_decision"], HARD_BLOCK)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "POPULATION_HARD_BLOCK")

    def test_execution_failure_blocks(self):
        result = status(repair_report(), execution="failure")
        self.assertEqual(result["decision"], "BLOCK")
        self.assertEqual(result["block_cause"], "EXECUTION_FAILED")

    def test_run_35199668216_regression(self):
        report = repair_report(
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
        self.assertEqual(result["population_evidence_source"], POPULATION_REPAIR)
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
