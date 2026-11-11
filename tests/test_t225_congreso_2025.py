# -*- coding: utf-8 -*-
"""PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-11 · ANTERIOR: ninguna (fichero nuevo)
Tests de T-225 (D-65, D-80): contratos de la edición 2026 de las 52 circunscripciones del Congreso con el par INE
2025/2025, su decisión, los inventarios insulares 2025 y la equivalencia seccionado INE 2026 → 2025."""
import hashlib
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
IDS = sorted(p.name for p in (ROOT / "territorios").iterdir() if p.name.startswith("congreso_"))
DECISION = ROOT / "configuracion/decisiones/congreso_referencia_territorial_2025_2026.json"
TABLA = ROOT / "configuracion/equivalencia_seccionado_ine_2026_a_2025.csv"


def _c(t: str, edicion: str) -> dict:
    return yaml.safe_load((ROOT / f"territorios/{t}/config/{t}_{edicion}.yaml").read_text(encoding="utf-8"))


class Contratos2026(unittest.TestCase):
    def test_52_contratos_2026_con_par_2025(self):
        self.assertEqual(len(IDS), 52)
        for t in IDS:
            with self.subTest(territorio=t):
                c = _c(t, "2026")
                self.assertEqual((c["meta"]["year"], c["meta"]["run_name"]), (2026, f"{t}_2026"))
                self.assertEqual((c["meta"]["source_population_year"], c["meta"]["source_section_year"]), (2025, 2025))
                self.assertEqual(c["io"]["input"]["seccionado"]["path"], "inputs/seccionado_2025.zip")
                self.assertEqual(c["io"]["input"]["population_cip"]["filters"]["year_value"], 2025)
                self.assertEqual(c["validation"]["source_baseline"]["edition"], "2026")
                self.assertIs(c["generation_state"]["generation_enabled"], False)
                self.assertNotIn("POP_2023", json.dumps(c))
                self.assertNotIn(f"{t}_2025", json.dumps(c))

    def test_contratos_admitidos_por_la_puerta_estructural(self):
        from ddd_core.territory_contract import validate_production_contract
        for t in IDS:
            with self.subTest(territorio=t):
                r = validate_production_contract(ROOT / f"territorios/{t}/config/{t}_2026.yaml", expected_territory=t)
                self.assertEqual(r.get("status"), "ADMITTED", r.get("errors"))

    def test_legislatura_vigente_sigue_en_2023(self):
        # D-80: los mapas van por legislatura; la vigente (elección de 2023) conserva sus contratos 2025 en 2023.
        for t in IDS:
            with self.subTest(territorio=t):
                self.assertEqual(_c(t, "2025")["meta"]["source_population_year"], 2023)

    def test_puentes_del_seccionado_2025(self):
        # Tremp: la sección 2523403001 no existe en el seccionado INE 2025; Herrera de Duero (Tudela, 47175) sí.
        def puentes(t):
            m02 = _c(t, "2026")["modulos"]["modulo_02_construir_adyacencias"]
            return {(str(b["u"]), str(b["v"])) for b in m02["topology_bridges"]}
        self.assertNotIn(("2523401002", "2523403001"), puentes("congreso_lerida"))
        self.assertIn(("4717501004", "4717501003"), puentes("congreso_valladolid"))

    def test_decision(self):
        d = json.loads(DECISION.read_text(encoding="utf-8"))
        self.assertEqual(d["territory_ids"], IDS)
        self.assertEqual((d["selected_population_year"], d["selected_section_year"], d["election_year"]), (2025, 2025, 2026))
        self.assertIs(d["generation_authorized_by_this_decision"], False)
        self.assertIn("D-65", d["approval_basis"])
        self.assertIn("D-80", d["approval_basis"])

    def test_inventario_insular_2025(self):
        p = json.loads((ROOT / "configuracion/particiones_insulares_2025.json").read_text(encoding="utf-8"))["territories"]
        inv = {t: [i for i in p[t]["inventories"] if i["section_year"] == 2025] for t in
               ("congreso_baleares", "congreso_las_palmas", "congreso_santa_cruz_de_tenerife", "illes_balears")}
        self.assertTrue(all(len(v) == 1 for v in inv.values()))
        # el universo de Baleares coincide con el inventario 2025 acreditado de illes_balears (literal del JSON)
        self.assertEqual(inv["congreso_baleares"][0]["universe_cusec_set_sha256"],
                         "9840bcfa657cbd05b0e04fefa99316c7fb8f9d085d030eea6060796b22ef9f8c")
        self.assertEqual(inv["congreso_las_palmas"][0]["component_sections"], {"35-C01": 589, "35-C02": 56, "35-G01": 78})


class Equivalencia2026(unittest.TestCase):
    def test_tabla_con_sha256_y_fuentes(self):
        meta = json.loads(TABLA.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(TABLA.read_bytes()).hexdigest(), meta["csv"]["sha256"])
        self.assertEqual(meta["fuentes"]["seccionado_2025"]["sha256"],
                         "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4")
        self.assertEqual(meta["fuentes"]["seccionado_2026"]["sha256"],
                         "3132a7ea07eaf6183b59f66bfbbf7d379662e9cf2759284358e88cedcc035ed2")
        self.assertEqual(len(meta["provincias"]), 52)
        # literal: la única sección nueva de Soria cae entera en una sección 2025
        self.assertIn("4217302016,4217302014,contenida,1.000000,1.000000", TABLA.read_text(encoding="utf-8").splitlines())

    def test_medir_contenida_y_partida(self):
        from shapely.geometry import box
        sys.path.insert(0, str(ROOT / "herramientas"))
        import equivalencia_seccionado_2026_2025 as eq
        s2025 = {"A": box(0, 0, 2, 1), "B": box(2, 0, 4, 1)}
        nuevas = {"N1": box(0, 0, 1, 1), "N2": box(1, 0, 3, 1)}  # N1 dentro de A; N2 mitad en A, mitad en B
        _, r = eq.medir(nuevas, s2025, {"A": 100, "B": 50})
        self.assertEqual((r["tipo_contenida"], r["tipo_partida"]), (1, 1))
        self.assertEqual(r["poblacion_afectada_partidas"], 75)  # 0,5 × 100 + 0,5 × 50


if __name__ == "__main__":
    unittest.main()
