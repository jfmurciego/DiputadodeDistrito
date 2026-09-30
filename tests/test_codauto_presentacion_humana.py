from __future__ import annotations

import copy
import unittest
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup
from herramientas.catalogo_territorios import (
    country_identity,
    format_country_label,
    format_territory_label,
    load_master,
    resolve_master,
)
from herramientas.generar_estado_operativo import build, render_readme_block
from herramientas.preparar_visor_ejecucion import _decorate_and_sort
from herramientas.resolver_fuentes_territorio import resolve_territory
from herramientas.resolver_ejecucion_completa import build_plan

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"

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


def _load_workflow(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _dispatch_inputs(path: Path) -> dict:
    data = _load_workflow(path)
    triggers = data.get(True, data.get("on", {})) or {}
    return ((triggers.get("workflow_dispatch") or {}).get("inputs") or {})


class HumanTerritoryLabelsTests(unittest.TestCase):
    def test_master_has_exact_19_codauto_in_canonical_order(self):
        rows = load_master(ROOT / "configuracion/catalogo_territorios_espana_2025.yaml")
        self.assertEqual([format_territory_label(row) for row in rows], EXPECTED)
        self.assertEqual([row["autonomous_community_code_ine"] for row in rows], [f"{i:02d}" for i in range(1, 20)])
        self.assertEqual(rows[2]["name"], "Principado de Asturias")
        self.assertEqual(rows[3]["name"], "Islas Baleares")
        self.assertTrue(all(" · " not in row["territory_id"] for row in rows))

    def test_country_is_es_not_00(self):
        self.assertEqual(format_country_label(), "ES · España")
        self.assertEqual(
            country_identity(),
            {"code": "ES", "name": "España", "display_name": "ES · España"},
        )
        self.assertNotEqual(format_country_label(), "00 · España")

    def test_old_and_new_inputs_resolve_to_same_internal_identity(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        for old, visible, territory_id in (
            ("Aragón", "02 · Aragón", "aragon"),
            ("Principado de Asturias", "03 · Principado de Asturias", "principado_de_asturias"),
            ("Islas Baleares", "04 · Islas Baleares", "illes_balears"),
        ):
            with self.subTest(territory=old):
                plain = lookup(old, "2025", catalog)
                coded = lookup(visible, "2025", catalog)
                self.assertEqual(plain["territory_id"], territory_id)
                self.assertEqual(coded["territory_id"], territory_id)
                self.assertEqual(plain["contract_path"], coded["contract_path"])
                self.assertEqual(resolve_master(visible, ROOT / "configuracion/catalogo_territorios_espana_2025.yaml")["territory_id"], territory_id)

    def test_source_acquisition_resolution_is_invariant(self):
        plain = resolve_territory("Islas Baleares")
        visible = resolve_territory("04 · Islas Baleares")
        self.assertEqual(plain["id"], visible["id"])
        self.assertEqual(plain["province_codes"], visible["province_codes"])

    def test_planning_is_identical_for_plain_and_visible_label(self):
        kwargs = {
            "edition": "2025",
            "execution_mode": "reuse",
            "catalog": ROOT / "configuracion/catalogo_preparacion.yaml",
            "root_dir": ROOT,
            "optimization_algorithm": "Canónico",
        }
        plain = build_plan(territory="Ceuta", **kwargs)
        visible = build_plan(territory="18 · Ceuta", **kwargs)
        self.assertEqual(visible, plain)

    def test_human_workflow_selectors_share_one_canonical_list(self):
        for name in (
            "preparacion-fuentes.yml",
            "produccion-distritos.yml",
            "preparacion-resultados-electorales.yml",
            "incorporacion-resultados-electorales.yml",
            "ejecucion-completa-proyecto.yml",
        ):
            with self.subTest(workflow=name):
                self.assertEqual(_dispatch_inputs(WF / name)["territory_id"]["options"], EXPECTED)

        source_test = _dispatch_inputs(WF / "prueba-fuentes-oficiales.yml")
        self.assertEqual(source_test["territory"]["options"], ["ES · España", *EXPECTED])
        self.assertEqual(source_test["territory"]["default"], "17 · La Rioja")

    def test_dashboard_and_readme_use_display_name_without_changing_identity(self):
        state = build(ROOT, "2025")
        self.assertEqual(state["country"]["display_name"], "ES · España")
        self.assertEqual(
            [row["display_name"] for row in state["territories"]],
            EXPECTED,
        )
        by_id = {row["territory_id"]: row for row in state["territories"]}
        self.assertEqual(by_id["illes_balears"]["name"], "Islas Baleares")
        self.assertEqual(by_id["illes_balears"]["display_name"], "04 · Islas Baleares")
        self.assertEqual(by_id["principado_de_asturias"]["display_name"], "03 · Principado de Asturias")
        rendered = render_readme_block(state)
        self.assertIn("País: **ES · España**", rendered)
        self.assertIn("| **01 · Andalucía** |", rendered)
        self.assertIn("| **19 · Melilla** |", rendered)

    def test_viewer_decoration_changes_only_human_metadata_and_order(self):
        original = [
            {
                "id": "m06-aragon",
                "territory_id": "aragon",
                "territory_label": "Aragón",
                "label": "M06 territorial",
                "kind": "canonical_m06",
                "viewer_path": "data/results/aragon/123/m06.geojson",
                "source_url": "https://example.invalid/aragon",
            },
            {
                "id": "m06-andalucia",
                "territory_id": "andalucia",
                "territory_label": "Andalucía",
                "label": "M06 territorial",
                "kind": "canonical_m06",
                "viewer_path": "data/results/andalucia/456/m06.geojson",
                "source_url": "https://example.invalid/andalucia",
            },
        ]
        before = copy.deepcopy(original)
        decorated = _decorate_and_sort(original, ROOT)
        self.assertEqual([row["territory_display_name"] for row in decorated], ["01 · Andalucía", "02 · Aragón"])
        by_id = {row["id"]: row for row in decorated}
        before_by_id = {row["id"]: row for row in before}
        for item_id in before_by_id:
            self.assertEqual(by_id[item_id]["territory_id"], before_by_id[item_id]["territory_id"])
            self.assertEqual(by_id[item_id]["viewer_path"], before_by_id[item_id]["viewer_path"])
            self.assertEqual(by_id[item_id]["source_url"], before_by_id[item_id]["source_url"])

    def test_dashboard_and_viewer_clients_prefer_canonical_display_field(self):
        for path in (ROOT / "dashboard/app.js", ROOT / "publicado/dashboard/app.js"):
            text = path.read_text(encoding="utf-8")
            self.assertIn("r.display_name || r.name", text)
            self.assertIn('data.country?.display_name || "ES · España"', text)
        viewer = (ROOT / "visor/app.js").read_text(encoding="utf-8")
        self.assertIn("spec.territory_display_name||spec.territory_label", viewer)
        self.assertIn("r.territory_display_name||r.territory_label", viewer)


if __name__ == "__main__":
    unittest.main()
