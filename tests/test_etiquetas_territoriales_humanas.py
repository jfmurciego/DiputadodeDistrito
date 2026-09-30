from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from herramientas.catalogo_preparacion import lookup
from herramientas.catalogo_territorios import (
    format_country_label,
    format_territory_label,
    load_master,
    normalize_country_input,
    normalize_territory_input,
    resolve_master,
)
from herramientas.generar_estado_operativo import build as build_operational_state
from herramientas.preparar_visor_ejecucion import _decorate_and_sort
from herramientas.resolver_ejecucion_completa import build_plan
from herramientas.resolver_fuentes_territorio import build_declaration

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
MASTER = ROOT / "configuracion" / "catalogo_territorios_espana_2025.yaml"
CATALOG = ROOT / "configuracion" / "catalogo_preparacion.yaml"

EXPECTED = [
    "01 · Andalucía",
    "02 · Aragón",
    "03 · Principado de Asturias",
    "04 · Islas Baleares",
    "05 · Canarias",
    "06 · Cantabria",
    "07 · Castilla y León",
    "08 · Castilla-La Mancha",
    "09 · Cataluña",
    "10 · Comunidad Valenciana",
    "11 · Extremadura",
    "12 · Galicia",
    "13 · Comunidad de Madrid",
    "14 · Región de Murcia",
    "15 · Comunidad Foral de Navarra",
    "16 · País Vasco",
    "17 · La Rioja",
    "18 · Ceuta",
    "19 · Melilla",
]


def dispatch_inputs(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    triggers = data.get(True, data.get("on", {})) or {}
    return ((triggers.get("workflow_dispatch") or {}).get("inputs") or {})


class HumanTerritoryLabelsTests(unittest.TestCase):
    def test_master_has_exact_19_codauto_and_canonical_spanish_labels(self):
        rows = load_master(MASTER)
        self.assertEqual([row["autonomous_community_code_ine"] for row in rows], [f"{n:02d}" for n in range(1, 20)])
        self.assertEqual([format_territory_label(row) for row in rows], EXPECTED)
        self.assertEqual(rows[2]["territory_id"], "principado_de_asturias")
        self.assertEqual(rows[2]["name"], "Principado de Asturias")
        self.assertEqual(rows[3]["territory_id"], "illes_balears")
        self.assertEqual(rows[3]["name"], "Islas Baleares")
        self.assertEqual(rows[6]["territory_id"], "castilla_y_leon")
        self.assertEqual(rows[7]["territory_id"], "castilla_la_mancha")

    def test_country_label_is_es_espana_and_never_00(self):
        self.assertEqual(format_country_label(), "ES · España")
        self.assertEqual(normalize_country_input("ES · España"), "ES")
        self.assertEqual(normalize_country_input("España"), "ES")
        with self.assertRaises(KeyError):
            normalize_country_input("00 · España")

    def test_visible_label_resolves_to_existing_internal_identity(self):
        self.assertEqual(normalize_territory_input("01 · Andalucía", MASTER), "Andalucía")
        self.assertEqual(normalize_territory_input("04 · Islas Baleares", MASTER), "Islas Baleares")
        self.assertEqual(resolve_master("04 · Islas Baleares", MASTER)["territory_id"], "illes_balears")
        self.assertEqual(resolve_master("03 · Principado de Asturias", MASTER)["territory_id"], "principado_de_asturias")
        self.assertEqual(resolve_master("19 · Melilla", MASTER)["territory_id"], "melilla")

        rows = load_master(MASTER)
        self.assertEqual(
            [resolve_master(label, MASTER)["territory_id"] for label in EXPECTED],
            [row["territory_id"] for row in rows],
        )

        plain = lookup("Islas Baleares", "2025", CATALOG)
        visible = lookup("04 · Islas Baleares", "2025", CATALOG)
        self.assertEqual(visible, plain)
        self.assertEqual(visible["territory_id"], "illes_balears")

    def test_historical_plain_names_and_internal_ids_keep_their_previous_treatment(self):
        for value in ("Andalucía", "andalucia", "Islas Baleares", "illes_balears", "Comunidad de Madrid", "madrid"):
            with self.subTest(value=value):
                self.assertEqual(normalize_territory_input(value, MASTER), value)

    def test_coded_label_rejects_mismatched_or_out_of_range_identity(self):
        cases = [
            ("04 · Andalucía", "Etiqueta territorial contradictoria"),
            ("07 · Castilla-La Mancha", "Etiqueta territorial contradictoria"),
            ("20 · Andalucía", "CODAUTO territorial fuera de 01..19"),
            ("00 · España", "CODAUTO territorial fuera de 01..19"),
        ]
        for value, reason in cases:
            with self.subTest(value=value):
                with self.assertRaisesRegex(KeyError, reason):
                    normalize_territory_input(value, MASTER)
        self.assertEqual(normalize_country_input("ES · España"), "ES")

    def test_invalid_coded_label_is_rejected_before_planning_or_source_acquisition(self):
        kwargs = dict(
            edition="2025",
            execution_mode="reuse",
            catalog=CATALOG,
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=False,
        )
        with patch("herramientas.catalogo_preparacion.load_catalog") as load_catalog:
            with self.assertRaisesRegex(KeyError, "Etiqueta territorial contradictoria"):
                build_plan(territory="04 · Andalucía", **kwargs)
            load_catalog.assert_not_called()

        with patch("herramientas.resolver_fuentes_territorio.territories") as source_registry:
            with self.assertRaisesRegex(KeyError, "Etiqueta territorial contradictoria"):
                build_declaration("07 · Castilla-La Mancha", 2025)
            source_registry.assert_not_called()

    def test_all_human_territory_selectors_use_same_labels_and_order(self):
        selectors = [
            ("preparacion-fuentes.yml", "territory_id"),
            ("produccion-distritos.yml", "territory_id"),
            ("preparacion-resultados-electorales.yml", "territory_id"),
            ("incorporacion-resultados-electorales.yml", "territory_id"),
            ("ejecucion-completa-proyecto.yml", "territory_id"),
        ]
        for workflow, key in selectors:
            with self.subTest(workflow=workflow):
                self.assertEqual(dispatch_inputs(WORKFLOWS / workflow)[key]["options"], EXPECTED)

        source_test = dispatch_inputs(WORKFLOWS / "prueba-fuentes-oficiales.yml")["territory"]["options"]
        self.assertEqual(source_test, ["Todos", *EXPECTED])

    def test_planning_accepts_visible_label_without_changing_plan(self):
        kwargs = dict(
            edition="2025",
            execution_mode="reuse",
            catalog=CATALOG,
            root_dir=ROOT,
            optimization_algorithm="Canónico",
            force_selected_algorithm=False,
        )
        plain = build_plan(territory="Galicia", **kwargs)
        visible = build_plan(territory="12 · Galicia", **kwargs)
        self.assertEqual(visible, plain)
        self.assertEqual(visible["territory_id"], "galicia")
        self.assertEqual(visible["territory_name"], "Galicia")

    def test_acquisition_accepts_visible_label_without_changing_declaration(self):
        plain = build_declaration("Andalucía", 2025)
        visible = build_declaration("01 · Andalucía", 2025)
        self.assertEqual(visible, plain)
        self.assertEqual(visible["territory"]["id"], "andalucia")

    def test_dashboard_state_uses_display_label_but_preserves_name_and_id(self):
        state = build_operational_state(ROOT, "2025")
        self.assertEqual(state["country_display_name"], "ES · España")
        self.assertEqual(
            [row["display_name"] for row in state["territories"]],
            EXPECTED,
        )
        balears = next(row for row in state["territories"] if row["territory_id"] == "illes_balears")
        self.assertEqual(balears["name"], "Islas Baleares")
        self.assertEqual(balears["display_name"], "04 · Islas Baleares")
        self.assertEqual(balears["autonomous_community_code_ine"], "04")

    def test_viewer_decorates_and_orders_without_changing_result_identity(self):
        rows = [
            {"id": "m06-balears-1", "territory_id": "illes_balears", "territory_label": "Illes Balears", "label": "M06", "kind": "canonical_m06"},
            {"id": "m06-andalucia-1", "territory_id": "andalucia", "territory_label": "Andalucía", "label": "M06", "kind": "canonical_m06"},
            {"id": "m06-asturias-1", "territory_id": "principado_de_asturias", "territory_label": "Asturias", "label": "M06", "kind": "canonical_m06"},
        ]
        decorated = _decorate_and_sort(rows, ROOT)
        self.assertEqual([row["id"] for row in decorated], ["m06-andalucia-1", "m06-asturias-1", "m06-balears-1"])
        self.assertEqual(
            [row["territory_label"] for row in decorated],
            ["01 · Andalucía", "03 · Principado de Asturias", "04 · Islas Baleares"],
        )
        self.assertTrue(all(row["country_display_name"] == "ES · España" for row in decorated))
        self.assertEqual(decorated[2]["territory_id"], "illes_balears")

    def test_dashboard_and_viewer_consume_central_display_fields(self):
        dashboard = (ROOT / "dashboard" / "app.js").read_text(encoding="utf-8")
        published_dashboard = (ROOT / "publicado" / "dashboard" / "app.js").read_text(encoding="utf-8")
        viewer = (ROOT / "visor" / "app.js").read_text(encoding="utf-8")
        for js in (dashboard, published_dashboard):
            self.assertIn("r.display_name || r.name", js)
            self.assertIn('data.country_display_name || "ES · España"', js)
        self.assertIn("r.territory_display_name||r.territory_label", viewer)
        self.assertIn("spec.territory_display_name||spec.territory_label", viewer)

    def test_technical_recovery_inputs_remain_canonical_internal_ids(self):
        recovery = dispatch_inputs(WORKFLOWS / "recuperar-producto-electoral-durable.yml")
        self.assertEqual(recovery["territory_id"]["type"], "string")
        self.assertNotIn("options", recovery["territory_id"])
        self.assertIn("Identificador canónico", recovery["territory_id"]["description"])

        publication = dispatch_inputs(WORKFLOWS / "publicar-version-mapa.yml")
        self.assertEqual(publication["territory_id"]["type"], "string")
        self.assertNotIn("options", publication["territory_id"])


if __name__ == "__main__":
    unittest.main()
