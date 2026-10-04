import unittest
from pathlib import Path

from herramientas.generar_estado_operativo import (
    _activation_snapshot,
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

    def test_reason_taxonomy_is_exhaustive_and_fail_closed(self):
        territorial_cases = {
            "TERRITORIAL_DURABLE_CANDIDATE": ("REUSE", "ADMISSIBLE"),
            "TERRITORIAL_IDENTITY_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "TERRITORIAL_ARTIFACT_IDENTITY_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "TERRITORIAL_RECEIPT_CONTRADICTORY": ("ACQUIRE", "INCOMPATIBLE"),
            "TERRITORIAL_POPULATION_YEAR_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "TERRITORIAL_SECTION_YEAR_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "TERRITORIAL_PACKAGE_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_DECLARATION_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_TEMPORAL_IDENTITY_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_RUN_INVALID": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_DIGEST_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_COMPATIBILITY_REPORT_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_RECEIPT_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "TERRITORIAL_PROVENANCE_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
        }
        for reason, (action, expected) in territorial_cases.items():
            with self.subTest(domain="territorial", reason=reason):
                self.assertEqual(
                    _territorial_admissibility(action, {"reason": reason}),
                    expected,
                )

        electoral_cases = {
            "ELECTORAL_DURABLE_CANDIDATE": ("REUSE", "ADMISSIBLE"),
            "ELECTORAL_IDENTITY_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "ELECTORAL_ELECTION_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "ELECTORAL_ARTIFACT_IDENTITY_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "ELECTORAL_PROVENANCE_MISMATCH": ("ACQUIRE", "INCOMPATIBLE"),
            "ELECTORAL_PACKAGE_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_RECEIPT_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_RECEIPT_KIND": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_RUN_INVALID": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_DIGEST_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_PROVENANCE_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_PROVENANCE_REFERENCE_MISSING": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_LEGACY_PROVENANCE_INCOMPLETE": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_PACKAGE_IDENTITY_NOT_DURABLE": ("ACQUIRE", "NOT_ACCREDITED"),
            "ELECTORAL_RECEIPT_SCHEMA": ("ACQUIRE", "NOT_ACCREDITED"),
            "OFFICIAL_SPECIAL_ACQUISITION_AVAILABLE": (
                "ACQUIRE",
                "ACQUISITION_REQUIRED",
            ),
            "PROVISIONAL_NOT_PRODUCTION_ELIGIBLE": (
                "BLOCKED_PROVISIONAL",
                "BLOCKED",
            ),
        }
        for reason, (action, expected) in electoral_cases.items():
            with self.subTest(domain="electoral", reason=reason):
                self.assertEqual(
                    _electoral_admissibility(action, {"reason": reason}),
                    expected,
                )

        with self.assertRaisesRegex(ValueError, "reason no clasificado"):
            _territorial_admissibility(
                "ACQUIRE",
                {"reason": "TERRITORIAL_REASON_NUEVO_SIN_MAPEAR"},
            )
        with self.assertRaisesRegex(ValueError, "reason no clasificado"):
            _electoral_admissibility(
                "ACQUIRE",
                {"reason": "ELECTORAL_REASON_NUEVO_SIN_MAPEAR"},
            )


class ActivationSnapshotPrecedenceTests(unittest.TestCase):
    def setUp(self):
        self.current_pair = {
            "current": True,
            "receipt_path": "territorios/demo/evidencia/pares_fuentes/2025/demo.json",
            "pair_sha256": "a" * 64,
            "reason": "CURRENT_DURABLE_PAIR",
        }

    def test_current_pair_and_admissible_sources_is_activated(self):
        plan = plan_fixture()
        activation = _activation_snapshot(plan, self.current_pair)
        self.assertEqual(activation["state"], "ACTIVATED")
        self.assertTrue(activation["pair"]["current"])

    def test_current_pair_never_overrides_not_accredited_sources(self):
        plan = plan_fixture(
            territorial_action="ACQUIRE",
            territorial_reason="TERRITORIAL_PACKAGE_MISSING",
        )
        self.assertEqual(plan["territorial_admissibility"], "NOT_ACCREDITED")
        activation = _activation_snapshot(plan, self.current_pair)
        self.assertEqual(activation["state"], "NOT_ACCREDITED")
        self.assertTrue(activation["pair"]["current"])

    def test_current_pair_never_overrides_incompatible_sources(self):
        plan = plan_fixture(
            territorial_action="ACQUIRE",
            territorial_reason="TERRITORIAL_POPULATION_YEAR_MISMATCH",
        )
        self.assertEqual(plan["territorial_admissibility"], "INCOMPATIBLE")
        activation = _activation_snapshot(plan, self.current_pair)
        self.assertEqual(activation["state"], "ACTION_REQUIRED")
        self.assertTrue(activation["pair"]["current"])

    def test_current_pair_never_overrides_blocked_sources(self):
        plan = plan_fixture(
            electoral_action="BLOCKED_PROVISIONAL",
            electoral_reason="PROVISIONAL_NOT_PRODUCTION_ELIGIBLE",
        )
        self.assertEqual(plan["sources_status"], "BLOCKED")
        activation = _activation_snapshot(plan, self.current_pair)
        self.assertEqual(activation["state"], "BLOCKED")
        self.assertTrue(activation["pair"]["current"])


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
        self.assertEqual(readiness["as_of"], resolved["as_of"])
        self.assertEqual(readiness["project_edition"], resolved["project_edition"])
        self.assertEqual(
            readiness["temporal_evidence"],
            resolved["temporal_evidence"],
        )
        self.assertEqual(len(readiness["territories"]), 19)
        self.assertEqual(
            set(plans),
            {r["territory_id"] for r in readiness["territories"]},
        )

        for row in readiness["territories"]:
            plan = plans[row["territory_id"]]
            territorial_candidate = plan["territorial_candidate"]

            self.assertEqual(
                row["election"],
                {
                    "election_id": plan["election_id"],
                    "election_date": plan["election_date"],
                },
                row["territory_id"],
            )
            self.assertEqual(
                row["territorial"],
                {
                    "status": plan["territorial_admissibility"],
                    "action": plan["territorial_action"],
                    "reason": plan["territorial_reason"],
                    "required": {
                        "population_year": plan["population_year_required"],
                        "section_year": plan["section_year_required"],
                    },
                    "selected": {
                        "population_year": plan["population_year_selected"],
                        "section_year": plan["section_year_selected"],
                    },
                    "accredited": {
                        "population_year": territorial_candidate.get(
                            "population_year",
                            territorial_candidate.get("observed_population_year"),
                        ),
                        "section_year": territorial_candidate.get(
                            "section_year",
                            territorial_candidate.get("observed_section_year"),
                        ),
                        "run_id": territorial_candidate.get("run_id"),
                        "receipt_path": territorial_candidate.get("receipt_path"),
                    },
                },
                row["territory_id"],
            )
            self.assertEqual(
                row["electoral"],
                {
                    "status": plan["electoral_admissibility"],
                    "action": plan["electoral_action"],
                    "reason": plan["electoral_reason"],
                    "source": plan["electoral_source"],
                    "granularity": plan["electoral_granularity"],
                },
                row["territory_id"],
            )
            self.assertEqual(
                row["status"],
                plan["sources_status"],
                row["territory_id"],
            )
            self.assertEqual(
                row["next_steps"],
                plan["source_next_steps"],
                row["territory_id"],
            )

            self.assertIn(
                row["activation"]["state"],
                {
                    "ACTIVATED",
                    "ACTIVABLE",
                    "ACTION_REQUIRED",
                    "BLOCKED",
                    "NOT_ACCREDITED",
                },
                row["territory_id"],
            )
            if row["activation"]["state"] == "ACTIVATED":
                self.assertEqual(row["status"], "ADMISSIBLE", row["territory_id"])
                self.assertTrue(
                    row["activation"]["pair"]["current"],
                    row["territory_id"],
                )

        summary = readiness["summary"]
        self.assertEqual(
            summary["activated"],
            sum(
                row["activation"]["state"] == "ACTIVATED"
                for row in readiness["territories"]
            ),
        )
        self.assertEqual(
            summary["activable"],
            sum(
                row["activation"]["state"] == "ACTIVABLE"
                for row in readiness["territories"]
            ),
        )
        self.assertEqual(
            readiness["activation_chain"]["durable_pair"],
            summary["activated"],
        )
        self.assertEqual(readiness["activation_chain"]["total"], 19)



if __name__ == "__main__":
    unittest.main()
