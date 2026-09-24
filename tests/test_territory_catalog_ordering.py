from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup
from herramientas.catalogo_territorios import format_territory_label, load_master
from herramientas.preparar_visor_ejecucion import _decorate_and_sort

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"
WORKFLOWS = ROOT / ".github/workflows"
FORM_WORKFLOWS = (
    "ejecucion-completa-proyecto.yml",
    "preparacion-fuentes.yml",
    "produccion-distritos.yml",
    "preparacion-resultados-electorales.yml",
    "incorporacion-resultados-electorales.yml",
    "prueba-fuentes-oficiales.yml",
)


def _territory_options(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    desc = next(i for i, line in enumerate(lines) if re.search(r"description:\s*Territorio\s*$", line))
    options = next(i for i in range(desc + 1, len(lines)) if re.match(r"^\s+options:\s*$", lines[i]))
    indent = len(lines[options]) - len(lines[options].lstrip()) + 2
    result = []
    for line in lines[options + 1:]:
        current = len(line) - len(line.lstrip())
        if current < indent:
            break
        match = re.match(r"^\s{%d}-\s+(.+)$" % indent, line)
        if match:
            result.append(match.group(1).strip())
    return result


class TerritoryCatalogOrderingTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_master(MASTER)
        self.labels = [format_territory_label(row) for row in self.rows]

    def test_master_has_exactly_19_unique_codauto_in_official_sequence(self):
        self.assertEqual(len(self.rows), 19)
        self.assertEqual(
            [row["autonomous_community_code_ine"] for row in self.rows],
            [f"{n:02d}" for n in range(1, 20)],
        )
        self.assertEqual(len({row["territory_id"] for row in self.rows}), 19)
        self.assertEqual(len({row["name"] for row in self.rows}), 19)

    def test_ceuta_melilla_and_castile_order_are_explicit(self):
        by_id = {row["territory_id"]: row for row in self.rows}
        self.assertEqual(by_id["ceuta"]["autonomous_community_code_ine"], "18")
        self.assertEqual(by_id["melilla"]["autonomous_community_code_ine"], "19")
        self.assertEqual(by_id["castilla_y_leon"]["autonomous_community_code_ine"], "07")
        self.assertEqual(by_id["castilla_la_mancha"]["autonomous_community_code_ine"], "08")
        ids = [row["territory_id"] for row in self.rows]
        self.assertLess(ids.index("castilla_y_leon"), ids.index("castilla_la_mancha"))

    def test_source_registry_mirrors_master_identity_but_not_code_authority(self):
        registry = yaml.safe_load((ROOT / "fuentes/territorios_espana.yaml").read_text(encoding="utf-8"))
        rows = registry["territories"]
        self.assertEqual(
            [(row["id"], row["name"]) for row in rows],
            [(row["territory_id"], row["name"]) for row in self.rows],
        )
        self.assertTrue(all("autonomous_community_code_ine" not in row for row in rows))

    def test_all_workflow_choices_match_master_and_order(self):
        for filename in FORM_WORKFLOWS:
            with self.subTest(workflow=filename):
                options = _territory_options(WORKFLOWS / filename)
                if filename == "prueba-fuentes-oficiales.yml":
                    self.assertEqual(options[0], "Todos")
                    options = options[1:]
                self.assertEqual(options, self.labels)

    def test_legacy_unprefixed_inputs_still_resolve(self):
        catalog = ROOT / "configuracion/catalogo_preparacion.yaml"
        old = lookup("Castilla y León", "2025", catalog)
        prefixed = lookup("07 · Castilla y León", "2025", catalog)
        machine = lookup("castilla_y_leon", "2025", catalog)
        self.assertEqual(old["territory_id"], "castilla_y_leon")
        self.assertEqual(prefixed["territory_id"], old["territory_id"])
        self.assertEqual(machine["territory_id"], old["territory_id"])

    def test_viewer_orders_by_codauto_before_mixed_product_type(self):
        results = [
            {"territory_id": "galicia", "territory_label": "WRONG", "kind": "canonical_m08", "label": "M08"},
            {"territory_id": "aragon", "territory_label": "WRONG", "kind": "static", "label": "Histórico"},
            {"territory_id": "castilla_la_mancha", "territory_label": "WRONG", "kind": "canonical_m06", "label": "M06"},
            {"territory_id": "castilla_y_leon", "territory_label": "WRONG", "kind": "ensemble_candidate", "label": "Ensemble"},
            {"territory_id": "aragon", "territory_label": "WRONG", "kind": "canonical_m08", "label": "M08"},
        ]
        ordered = _decorate_and_sort(results, ROOT)
        self.assertEqual(
            [(row["autonomous_community_code_ine"], row["kind"]) for row in ordered],
            [
                ("02", "canonical_m08"),
                ("02", "static"),
                ("07", "ensemble_candidate"),
                ("08", "canonical_m06"),
                ("12", "canonical_m08"),
            ],
        )
        self.assertEqual(ordered[0]["territory_display_name"], "02 · Aragón")
        self.assertEqual(ordered[2]["territory_display_name"], "07 · Castilla y León")

    def test_campaign_contract_order_and_slots_remain_unchanged(self):
        manifest = yaml.safe_load((ROOT / "configuracion/campanas/campana_cinco_territorios_v1.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [(row["slot"], row["territory_id"]) for row in manifest["territories"]],
            [
                ("01", "aragon"),
                ("02", "principado_de_asturias"),
                ("03", "galicia"),
                ("04", "castilla_y_leon"),
                ("05", "extremadura"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
