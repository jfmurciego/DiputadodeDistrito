"""Versión 1.1.0; 2026-11-08; candidato. T-34: configuraciones de ensemble por territorio coherentes con su contrato.
T-98: la exención municipal de suelo se admite si la config la copia del contrato con su decisión gobernada."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from ddd_ensemble.runner import ensure_plan, load_config
from herramientas.leer_config_ensemble import describe

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = sorted(p for p in (ROOT / "configuracion/ensemble").glob("*.json") if p.stem != "aragon")


class ConfigsEnsembleTerritorialesTests(unittest.TestCase):
    def test_hay_piloto_y_provincias_adicionales(self):
        names = {p.stem for p in CONFIGS}
        self.assertTrue({"congreso_salamanca", "congreso_la_rioja", "congreso_sevilla"} <= names, names)

    def test_cada_config_es_coherente_con_su_contrato(self):
        for path in CONFIGS:
            with self.subTest(path.stem):
                tid = path.stem
                info = describe(tid, "ensemble_10", ROOT, resolve_sources=False)
                self.assertEqual(info["kind"], "territorial")
                config, _ = load_config(str(path))
                contract = yaml.safe_load((ROOT / info["contract"]).read_text(encoding="utf-8"))
                val, tc = contract["validation"], contract["territory_contract"]
                self.assertEqual(config["territory_id"], tid)
                self.assertEqual(config["contract"]["k"], tc["k_districts"])
                self.assertEqual(int(info["expected_districts"]), tc["k_districts"])
                self.assertEqual(config["contract"]["province_districts"], {str(k): v for k, v in val["province_districts"].items()})
                for key in ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio", "municipality_atomicity_limit_ratio"):
                    self.assertEqual(config["contract"][key], val[key], key)
                m02 = contract["modulos"]["modulo_02_construir_adyacencias"]
                self.assertEqual(info["working_crs"], m02["working_crs"])
                self.assertEqual(config["topology"]["working_crs"], m02["working_crs"])
                self.assertEqual(config["fields"]["population"], contract["modulos"]["modulo_03_construir_grafo"]["pop_field"])
                run = contract["meta"]["run_name"]
                self.assertIn(run, info["cache_dir"])
                self.assertIn(f"{run}_m03_grafo.json", config["inputs"]["m03_graph"])
                self.assertIn(f"{run}_m05_distritos_optimizados.geojson.zip", config["inputs"]["initial_geojson"])
                # T-31/T-33: metros, aristas débiles y piezas de secciones MultiPolygon como M06
                self.assertIs(config["topology"]["prune_weak_adjacencies"], True)
                self.assertIs(config["topology"]["preserve_atomic_multipart_sections"], True)
                self.assertEqual(config["ensemble"]["candidate_count"], 10)

    def test_el_motor_del_ensemble_no_modela_puentes_ni_exenciones_por_particion(self):
        # Una config solo es válida si el contrato no depende de lo que el ensemble no sabe aplicar.
        for path in CONFIGS:
            with self.subTest(path.stem):
                contract = yaml.safe_load((ROOT / f"territorios/{path.stem}/config/{path.stem}_2025.yaml").read_text(encoding="utf-8"))
                val = contract["validation"]
                config, _ = load_config(str(path))
                self.assertFalse(val.get("population_floor_exempt_partitions"))
                exentos = [str(c) for c in val.get("population_floor_exempt_municipalities") or []]
                self.assertEqual(config["contract"].get("population_floor_exempt_municipalities", []), exentos)
                for code in exentos:  # T-98: el ensemble la modela (m05_gerrychain_engine 1.3.0) si está gobernada
                    self.assertEqual(config["decisions"][f"population_floor_exempt_municipalities:{code}"],
                                     val["population_floor_exempt_decisions"][code])
                self.assertFalse(contract["modulos"]["modulo_02_construir_adyacencias"].get("topology_bridges"))

    def test_cada_config_planifica_diez_candidatos(self):
        for path in CONFIGS:
            with self.subTest(path.stem):
                config, _ = load_config(str(path))
                config["prepared_bundle_id"] = "sha256:prueba"
                with tempfile.TemporaryDirectory() as td:
                    plan = ensure_plan(config, Path(td), count_override=10)
                self.assertEqual((plan["territory_id"], plan["candidate_count"], len(plan["shards"])), (path.stem, 10, 5))

    def test_el_lote_de_50_sigue_bloqueado(self):
        for path in CONFIGS:
            with self.assertRaises(SystemExit):
                describe(path.stem, "ensemble_50", ROOT, resolve_sources=False)


if __name__ == "__main__":
    unittest.main()
