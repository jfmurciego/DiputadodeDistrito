import unittest
from pathlib import Path

from herramientas.generar_estado_operativo import (
    _source_readiness_row,
    build,
)
from herramientas.resolver_preparacion_legislatura import (
    _electoral_admissibility,
    _source_next_steps,
    _sources_status,
    _territorial_admissibility,
    resolve,
)

ROOT = Path(__file__).resolve().parents[1]


def plan_fixture(
    *,
    territorial_action="REUSE",
    territorial_reason="TERRITORIAL_DURABLE_CANDIDATE",
    electoral_action="REUSE",
    electoral_reason="ELECTORAL_DURABLE_CANDIDATE",
):
    territorial_candidate = {
        "reason": territorial_reason,
        "population_year": 2024,
        "section_year": 2024,
        "run_id": 42,
        "receipt_path": "territorios/demo/evidencia/fuentes_territoriales/receipt.json",
    }
    electoral_candidate = {"reason": electoral_reason}
    territorial_admissibility = _territorial_admissibility(
        territorial_action,
        territorial_candidate,
    )
    electoral_admissibility = _electoral_admissibility(
        electoral_action,
        electoral_candidate,
    )
    return {
        "territory_id": "demo",
        "name": "Demo",
        "election_id": "demo_election_2024",
        "election_date": "2024-05-12",
        "population_year_required": 2024,
        "population_year_selected": 2024,
        "section_year_required": 2024,
        "section_year_selected": 2024,
        "territorial_action": territorial_action,
        "territorial_admissibility": territorial_admissibility,
        "territorial_reason": territorial_reason,
        "territorial_candidate": territorial_candidate,
        "electoral_action": electoral_action,
        "electoral_admissibility": electoral_admissibility,
        "sources_status": _sources_status(
            territorial_admissibility,
            electoral_admissibility,
        ),
        "source_next_steps": _source_next_steps(
            territorial_action,
            territorial_candidate,
            electoral_action,
            electoral_candidate,
        ),
        "electoral_reason": electoral_reason,
        "electoral_source": "Fuente oficial",
        "electoral_granularity": "section_party",
    }


class ResolverSourceAdmissibilityTests(unittest.TestCase):
    def test_controlled_status_scenarios(self):
        self.assertEqual(
            _territorial_admissibility(
                "REUSE",
                {"reason": "TERRITORIAL_DURABLE_CANDIDATE"},
            ),
            "ADMISSIBLE",
        )
        self.assertEqual(
            _territorial_admissibility(
                "REUSE_TEMPORAL_SUBSTITUTION",
                {"reason": "TERRITORIAL_DURABLE_CANDIDATE"},
            ),
            "ADMISSIBLE_TEMPORAL_SUBSTITUTION",
        )
        self.assertEqual(
            _territorial_admissibility(
                "ACQUIRE",
                {"reason": "TERRITORIAL_PACKAGE_MISSING"},
            ),
            "NOT_ACCREDITED",
        )
        self.assertEqual(
            _territorial_admissibility(
                "ACQUIRE",
                {"reason": "TERRITORIAL_POPULATION_YEAR_MISMATCH"},
            ),
            "INCOMPATIBLE",
        )
        self.assertEqual(
            _electoral_admissibility(
                "BLOCKED_PROVISIONAL",
                {"reason": "PROVISIONAL_NOT_PRODUCTION_ELIGIBLE"},
            ),
            "BLOCKED",
        )
        self.assertEqual(
            _sources_status("ADMISSIBLE", "BLOCKED"),
            "BLOCKED",
        )


class DashboardSourceReadinessTests(unittest.TestCase):
    def test_admissible_depends_on_resolver_dictamen_not_year_comparison(self):
        plan = plan_fixture()
        row = _source_readiness_row(plan, "99 · Demo")
        self.assertEqual(row["territorial"]["status"], "ADMISSIBLE")
        self.assertEqual(row["electoral"]["status"], "ADMISSIBLE")
        self.assertEqual(row["status"], "ADMISSIBLE")
        self.assertEqual(row["next_steps"], [])

    def test_temporal_substitution_can_still_be_admissible(self):
        plan = plan_fixture(territorial_action="REUSE_TEMPORAL_SUBSTITUTION")
        plan["population_year_required"] = 2026
        plan["population_year_selected"] = 2025
        plan["territorial_candidate"]["population_year"] = 2025
        row = _source_readiness_row(plan, "99 · Demo")
        self.assertEqual(
            row["territorial"]["status"],
            "ADMISSIBLE_TEMPORAL_SUBSTITUTION",
        )
        self.assertEqual(row["status"], "ADMISSIBLE")

    def test_not_accredited_is_distinct_from_incompatible(self):
        missing = plan_fixture(
            territorial_action="ACQUIRE",
            territorial_reason="TERRITORIAL_PACKAGE_MISSING",
        )
        incompatible = plan_fixture(
            territorial_action="ACQUIRE",
            territorial_reason="TERRITORIAL_POPULATION_YEAR_MISMATCH",
        )
        self.assertEqual(
            _source_readiness_row(missing, "99 · Demo")["territorial"]["status"],
            "NOT_ACCREDITED",
        )
        self.assertEqual(
            _source_readiness_row(incompatible, "99 · Demo")["territorial"]["status"],
            "INCOMPATIBLE",
        )

    def test_electoral_block_makes_overall_sources_blocked(self):
        plan = plan_fixture(
            electoral_action="BLOCKED_PROVISIONAL",
            electoral_reason="PROVISIONAL_NOT_PRODUCTION_ELIGIBLE",
        )
        row = _source_readiness_row(plan, "99 · Demo")
        self.assertEqual(row["electoral"]["status"], "BLOCKED")
        self.assertEqual(row["status"], "BLOCKED")
        self.assertEqual(
            row["next_steps"][0]["planner_action"],
            "BLOCKED_PROVISIONAL",
        )

    def test_activity_is_not_inferred_from_planner_action(self):
        plan = plan_fixture(
            territorial_action="ACQUIRE",
            territorial_reason="TERRITORIAL_PACKAGE_MISSING",
        )
        row = _source_readiness_row(plan, "99 · Demo")
        self.assertEqual(row["activity"]["status"], "NOT_OBSERVED")
        self.assertEqual(row["activity"]["source"], "repository_durable_state")

    def test_real_19_dashboard_source_readiness_matches_current_resolver(self):
        payload = build(ROOT, "2025")
        resolved = resolve(ROOT, "Todos")
        plans = {p["territory_id"]: p for p in resolved["plans"]}
        readiness = payload["source_readiness"]
        self.assertEqual(readiness["schema"], "ddd-source-readiness/1.0")
        self.assertEqual(readiness["status"], "READY")
        self.assertEqual(len(readiness["territories"]), 19)
        self.assertEqual(set(plans), {r["territory_id"] for r in readiness["territories"]})
        for row in readiness["territories"]:
            plan = plans[row["territory_id"]]
            self.assertEqual(row["election"]["election_id"], plan["election_id"])
            self.assertEqual(row["election"]["election_date"], plan["election_date"])
            self.assertEqual(row["territorial"]["action"], plan["territorial_action"])
            self.assertEqual(row["electoral"]["action"], plan["electoral_action"])
            self.assertEqual(
                row["territorial"]["selected"]["population_year"],
                plan["population_year_selected"],
            )
            self.assertEqual(
                row["territorial"]["selected"]["section_year"],
                plan["section_year_selected"],
            )


if __name__ == "__main__":
    unittest.main()
