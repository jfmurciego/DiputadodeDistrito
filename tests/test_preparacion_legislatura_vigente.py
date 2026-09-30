from __future__ import annotations

from pathlib import Path
import unittest
import yaml

from herramientas.resolver_fuentes_territorio import build_declaration
from herramientas.resolver_preparacion_legislatura import resolve, validate_matrix

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-legislatura-vigente.yml"
MATRIX = ROOT / "configuracion/preparacion_legislatura_vigente.yaml"
REGISTRY = ROOT / "configuracion/registro_electoral.yaml"


class CurrentLegislaturePreparationTests(unittest.TestCase):
    def test_matrix_has_exactly_19_current_elections(self):
        rows = validate_matrix(ROOT)
        registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))["territories"]
        self.assertEqual(len(rows), 19)
        self.assertEqual({r["territory_id"] for r in rows}, set(registry))
        for row in rows:
            registered = registry[row["territory_id"]]
            self.assertEqual(row["election_id"], registered["election_id"])
            self.assertEqual(str(row["election_date"]), str(registered["election_date"]))

    def test_2023_and_2024_require_contemporary_official_source_year(self):
        rows = validate_matrix(ROOT)
        for row in rows:
            election_year = int(str(row["election_date"])[:4])
            if election_year not in {2023, 2024}:
                continue
            territorial = row["territorial"]
            with self.subTest(territory=row["territory_id"]):
                self.assertEqual(territorial["required_year"], election_year)
                self.assertEqual(territorial["selected_source_year"], election_year)
                self.assertEqual(territorial["lag_years"], 0)
                self.assertEqual(territorial["action"], "ACQUIRE_WRONG_YEAR")
                self.assertNotEqual(territorial["current_package_year"], election_year)

    def test_2026_uses_declared_temporal_substitution_only(self):
        rows = validate_matrix(ROOT)
        rows_2026 = [r for r in rows if str(r["election_date"]).startswith("2026-")]
        self.assertEqual({r["territory_id"] for r in rows_2026}, {"andalucia", "aragon", "castilla_y_leon"})
        for row in rows_2026:
            territorial = row["territorial"]
            with self.subTest(territory=row["territory_id"]):
                self.assertEqual(territorial["required_year"], 2026)
                self.assertEqual(territorial["selected_source_year"], 2025)
                self.assertEqual(territorial["lag_years"], 1)
                self.assertEqual(territorial["action"], "REUSE_TEMPORAL_SUBSTITUTION")
                self.assertIn("2026", territorial["reason"])
                self.assertIn("2025", territorial["reason"])

    def test_extremadura_2025_is_exact_but_electoral_stays_provisional(self):
        plan = resolve(ROOT, "Extremadura")["plans"][0]
        self.assertEqual(plan["population_year_required"], 2025)
        self.assertEqual(plan["population_year_selected"], 2025)
        self.assertEqual(plan["territorial_action"], "REUSE")
        self.assertEqual(plan["electoral_action"], "BLOCKED_PROVISIONAL")
        self.assertEqual(plan["definitive_gap"]["source_candidate_votes"], 522418)
        self.assertEqual(plan["definitive_gap"]["definitive_candidate_votes"], 524837)
        self.assertEqual(plan["definitive_gap"]["gap_candidate_votes"], 2419)

    def test_andalucia_preserves_provisional_gap_without_filling_votes(self):
        plan = resolve(ROOT, "Andalucía")["plans"][0]
        self.assertEqual(plan["territorial_action"], "REUSE_TEMPORAL_SUBSTITUTION")
        self.assertEqual(plan["electoral_action"], "BLOCKED_PROVISIONAL")
        self.assertEqual(plan["definitive_gap"]["source_candidate_votes"], 4128575)
        self.assertEqual(plan["definitive_gap"]["definitive_candidate_votes"], 4157539)
        self.assertEqual(plan["definitive_gap"]["gap_candidate_votes"], 28964)

    def test_partial_acquisition_reuses_electoral_but_replaces_wrong_year_territorial(self):
        for territory in ("Comunidad de Madrid", "Galicia"):
            plan = resolve(ROOT, territory)["plans"][0]
            with self.subTest(territory=territory):
                self.assertEqual(plan["territorial_action"], "ACQUIRE")
                self.assertEqual(plan["electoral_action"], "REUSE")

    def test_both_sources_are_acquired_when_both_are_missing_or_wrong(self):
        plan = resolve(ROOT, "Canarias")["plans"][0]
        self.assertEqual(plan["territorial_action"], "ACQUIRE")
        self.assertEqual(plan["electoral_action"], "ACQUIRE")

    def test_legacy_electoral_provenance_is_not_a_reusable_package(self):
        plan = resolve(ROOT, "Castilla y León")["plans"][0]
        self.assertEqual(plan["territorial_action"], "REUSE_TEMPORAL_SUBSTITUTION")
        self.assertEqual(plan["electoral_action"], "ACQUIRE")
        self.assertEqual(
            plan["electoral_candidate"]["reason"],
            "ELECTORAL_PACKAGE_IDENTITY_NOT_DURABLE",
        )

    def test_source_year_is_separate_from_project_edition(self):
        declaration = build_declaration("Comunidad de Madrid", 2025, source_year=2023)
        self.assertEqual(declaration["territory"]["edition"], 2025)
        self.assertEqual(declaration["territory"]["source_year"], 2023)
        self.assertEqual(
            declaration["source_bindings"]["secciones_censales"]["materialized_path"],
            "inputs/seccionado_2023.zip",
        )
        legacy_default = build_declaration("Comunidad de Madrid", 2025)
        self.assertEqual(legacy_default["territory"]["source_year"], 2025)

    def test_workflow_keeps_01_and_03_independent_and_never_runs_all_19(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("uses: ./.github/workflows/preparacion-fuentes.yml", workflow)
        self.assertIn("uses: ./.github/workflows/preparacion-resultados-electorales.yml", workflow)
        self.assertIn("prepare_one exige un territorio concreto", workflow)
        self.assertNotIn("ejecucion-completa-proyecto.yml", workflow)
        self.assertNotIn("_reutilizable-generacion-territorial.yml", workflow)
        self.assertNotIn("incorpor", workflow.lower())
        self.assertNotIn("publicar visor", workflow.lower())

    def test_matrix_does_not_invent_unknown_definitive_vote_gaps(self):
        matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
        for row in matrix["territories"]:
            electoral = row["electoral"]
            status = electoral.get("definitive_gap_status")
            if status in {"NOT_DECLARED", "NOT_EVALUATED"}:
                with self.subTest(territory=row["territory_id"]):
                    self.assertNotIn("gap_candidate_votes", electoral)
                    self.assertNotIn("definitive_candidate_votes", electoral)
                    self.assertNotIn("source_candidate_votes", electoral)


if __name__ == "__main__":
    unittest.main()
