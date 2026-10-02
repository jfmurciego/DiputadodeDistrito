from __future__ import annotations

from pathlib import Path
import unittest

import yaml

from herramientas.catalogo_territorios import (
    format_territory_label,
    load_master,
    normalize_territory_input,
)
from herramientas.preflight_preparacion_fuente import _state
from herramientas.catalogo_preparacion import resolve as resolve_catalog, rows_for
from herramientas.resolver_preparacion_legislatura import resolve

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"
WORKFLOWS = ROOT / ".github" / "workflows"
PREPARATION_CATALOG = ROOT / "configuracion/catalogo_preparacion.yaml"


def dispatch_inputs(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    triggers = data.get(True, data.get("on", {})) or {}
    return ((triggers.get("workflow_dispatch") or {}).get("inputs") or {})


class CodautoPreparationContractTests(unittest.TestCase):
    def test_canonical_label_has_no_decorative_separator_and_legacy_is_readable(self):
        cantabria = next(
            row for row in load_master(MASTER)
            if row["territory_id"] == "cantabria"
        )
        self.assertEqual(format_territory_label(cantabria), "06 Cantabria")
        self.assertEqual(normalize_territory_input("06 Cantabria", MASTER), "Cantabria")
        self.assertEqual(normalize_territory_input("06 · Cantabria", MASTER), "Cantabria")

    def test_preflight_gate_accepts_canonical_label_legacy_label_and_internal_id(self):
        canonical = _state(ROOT, "06 Cantabria", "2025")
        legacy = _state(ROOT, "06 · Cantabria", "2025")
        internal = _state(ROOT, "cantabria", "2025")
        self.assertEqual(canonical[:2], ("cantabria", "Cantabria"))
        self.assertEqual(canonical, legacy)
        self.assertEqual(canonical, internal)

    def test_cantabria_current_legislature_plan_selects_2023_not_current_2025(self):
        plan = resolve(ROOT, "06 Cantabria")["plans"][0]
        self.assertEqual(plan["territory_id"], "cantabria")
        self.assertEqual(plan["project_edition"], "2025")
        self.assertEqual(plan["population_year_selected"], 2023)
        self.assertEqual(plan["section_year_selected"], 2023)

    def test_01_manual_gate_consumes_authoritative_selected_years_and_internal_id(self):
        workflow = yaml.safe_load(
            (WORKFLOWS / "preparacion-fuentes.yml").read_text(encoding="utf-8")
        )
        resolver = next(
            step for step in workflow["jobs"]["resolver"]["steps"]
            if step.get("id") == "resolve"
        )
        body = resolver["run"]
        self.assertIn(
            'resolver_preparacion_legislatura.py --root-dir . --territory "$TERRITORY"',
            body,
        )
        self.assertIn(".population_year_selected", body)
        self.assertIn(".section_year_selected", body)
        self.assertIn('TERRITORY="$(jq -r .territory_id <<<"$plan")"', body)
        self.assertNotIn("population_current_year", body)
        self.assertNotIn("section_current_year", body)

    def test_all_manual_territory_doors_emit_same_canonical_codauto_labels(self):
        expected = [format_territory_label(row) for row in load_master(MASTER)]
        direct = [
            ("preparacion-fuentes.yml", "territory_id"),
            ("produccion-distritos.yml", "territory_id"),
            ("preparacion-resultados-electorales.yml", "territory_id"),
            ("incorporacion-resultados-electorales.yml", "territory_id"),
            ("ejecucion-completa-proyecto.yml", "territory_id"),
        ]
        for workflow, key in direct:
            with self.subTest(workflow=workflow):
                options = dispatch_inputs(WORKFLOWS / workflow)[key]["options"]
                self.assertEqual(options, expected)
                self.assertTrue(all(" · " not in item for item in options))

        for workflow in ("prueba-fuentes-oficiales.yml", "preparacion-legislatura-vigente.yml"):
            with self.subTest(workflow=workflow):
                options = dispatch_inputs(WORKFLOWS / workflow)["territory"]["options"]
                self.assertEqual(options, ["Todos", *expected])
                self.assertTrue(all(" · " not in item for item in options[1:]))



    def test_generation_and_electoral_application_resolve_all_codauto_forms(self):
        master_by_id = {
            row["territory_id"]: row
            for row in load_master(MASTER)
        }
        for mode in ("generation", "electoral_application"):
            eligible = rows_for(mode, PREPARATION_CATALOG)
            self.assertTrue(eligible, mode)
            for row in eligible:
                territory_id = row["territory_id"]
                edition = row["edition"]
                master = master_by_id[territory_id]
                canonical = format_territory_label(master)
                legacy = canonical.replace(" ", " · ", 1)

                expected = resolve_catalog(mode, territory_id, edition, PREPARATION_CATALOG)
                with self.subTest(mode=mode, territory=canonical):
                    self.assertEqual(
                        resolve_catalog(mode, canonical, edition, PREPARATION_CATALOG),
                        expected,
                    )
                with self.subTest(mode=mode, territory=legacy):
                    self.assertEqual(
                        resolve_catalog(mode, legacy, edition, PREPARATION_CATALOG),
                        expected,
                    )
                with self.subTest(mode=mode, territory=territory_id):
                    self.assertEqual(
                        resolve_catalog(mode, territory_id, edition, PREPARATION_CATALOG),
                        expected,
                    )


    def test_all_manually_dispatchable_workflow_names_are_free_of_middle_dot(self):
        def iter_names(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key == "name" and isinstance(value, str):
                        yield value
                    yield from iter_names(value)
            elif isinstance(node, list):
                for value in node:
                    yield from iter_names(value)

        manual = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            triggers = data.get("on") or data.get(True) or {}
            if "workflow_dispatch" not in triggers:
                continue
            manual.append(path.name)
            for name in iter_names(data):
                with self.subTest(workflow=path.name, name=name):
                    self.assertNotIn("·", name)

        self.assertEqual(
            manual,
            [
                "desplegar-visor-publico.yml",
                "ejecucion-completa-proyecto.yml",
                "gestor-campanas.yml",
                "incorporacion-resultados-electorales.yml",
                "preparacion-fuentes.yml",
                "preparacion-legislatura-vigente.yml",
                "preparacion-resultados-electorales.yml",
                "produccion-distritos.yml",
                "prueba-fuentes-oficiales.yml",
                "prueba-openai.yml",
                "publicar-version-mapa.yml",
                "recuperar-producto-electoral-durable.yml",
                "smoke-gerrychain-galicia.yml",
            ],
        )


if __name__ == "__main__":
    unittest.main()
