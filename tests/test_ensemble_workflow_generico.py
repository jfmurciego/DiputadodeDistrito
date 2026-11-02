"""Versión 1.0.0; 2026-11-02; candidato. T-26: ensemble genérico por territorio sin registrar nada en el catálogo."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from ddd_ensemble.runner import ensure_plan, load_config
from herramientas.leer_config_ensemble import describe

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/generar-alternativas-territoriales.yml"
TEXT = WF.read_text(encoding="utf-8")
DOC = yaml.safe_load(TEXT)
JOBS = DOC["jobs"]


class EnsembleWorkflowGenericoTests(unittest.TestCase):
    def test_base_territorial_no_registra_nada(self):
        job = JOBS["base_territorial"]
        self.assertEqual(job["uses"], "./.github/workflows/_reutilizable-generacion-territorial.yml")
        w = job["with"]
        self.assertIs(w["persist_state"], False)
        self.assertTrue(w["artifact_namespace"].startswith("ensemble-"))
        self.assertEqual((w["from_stage"], w["to_stage"]), ("M01", "M05"))
        self.assertIn("inputs.execution_confirmed", job["if"])
        self.assertIn("'territorial'", job["if"])

    def test_el_workflow_no_toca_catalogo_ni_estado_operativo(self):
        for forbidden in ("promover_catalogo", "catalogo_preparacion.yaml", "estado_operativo", "territorial_product",
                          "publicaciones_visor", "registro_publicaciones_visor", "git push", "git commit"):
            self.assertNotIn(forbidden, TEXT, forbidden)

    def test_pasos_de_aragon_solo_con_kind_aragon(self):
        base = JOBS["base"]["steps"]
        for name in ("Reconstruir fuentes canónicas", "Preparar M01–M05 una sola vez con topología métrica"):
            step = next(s for s in base if s.get("name") == name)
            self.assertEqual(step["if"], "${{ env.KIND == 'aragon' }}")
        territorial = [s for s in base if "territorial" in str(s.get("if", ""))]
        self.assertGreaterEqual(len(territorial), 3)

    def test_sin_rutas_ni_distritos_fijos_fuera_de_la_rama_aragon(self):
        # Fuera de pasos con kind aragon y de la republicación (limitada a Aragón) no queda «aragon» ni 67.
        for job_name in ("generate", "publish", "config", "base_territorial"):
            self.assertNotIn("aragon.json", json.dumps(JOBS[job_name]), job_name)
        for step in JOBS["base"]["steps"]:
            if "aragon'" in str(step.get("if", "")):
                continue
            blob = json.dumps(step)
            if "aragon_10" in blob or "aragon_50" in blob:  # compuerta de fase
                continue
            self.assertNotIn("aragon_2025", blob, step.get("name"))
            self.assertNotIn("--expected-districts 67", blob, step.get("name"))

    def test_el_lote_de_50_sigue_bloqueado_fuera_de_aragon(self):
        with self.assertRaises(SystemExit):
            describe("congreso_salamanca", "ensemble_50", ROOT, resolve_sources=False)
        with self.assertRaises(SystemExit):
            describe("congreso_salamanca", "aragon_10", ROOT, resolve_sources=False)
        self.assertEqual(describe("aragon", "aragon_10", ROOT)["kind"], "aragon")
        gate = next(s for s in JOBS["base"]["steps"] if s.get("id") == "gate")["run"]
        self.assertIn("ensemble_10) test \"$KIND\" = territorial; count=10", gate)
        self.assertNotIn("ensemble_50", gate)

    def test_configuracion_de_salamanca_valida_y_planifica(self):
        info = describe("congreso_salamanca", "ensemble_10", ROOT, resolve_sources=False)
        self.assertEqual((info["kind"], info["expected_districts"], info["working_crs"]), ("territorial", "3", "EPSG:3035"))
        config, _ = load_config(str(ROOT / "configuracion/ensemble/congreso_salamanca.json"))
        self.assertEqual(config["contract"]["k"], 3)
        self.assertEqual(config["contract"]["province_districts"], {"37": 3})
        contract = yaml.safe_load((ROOT / info["contract"]).read_text(encoding="utf-8"))
        self.assertEqual(contract["territory_contract"]["k_districts"], 3)
        for key in ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio", "municipality_atomicity_limit_ratio"):
            self.assertEqual(config["contract"][key], contract["validation"][key], key)
        config["prepared_bundle_id"] = "sha256:prueba"
        with tempfile.TemporaryDirectory() as td:
            plan = ensure_plan(config, Path(td), count_override=10)
        self.assertEqual((plan["territory_id"], plan["candidate_count"], len(plan["shards"])), ("congreso_salamanca", 10, 5))

    def test_tiene_disparador_manual_con_las_mismas_entradas(self):
        on = DOC.get("on") or DOC.get(True)
        self.assertEqual(set(on["workflow_dispatch"]["inputs"]), set(on["workflow_call"]["inputs"]))
        self.assertIs(on["workflow_dispatch"]["inputs"]["deploy_pages"]["default"], False)

    def test_tiene_disparador_manual_visible_con_las_mismas_entradas(self):
        on = DOC.get("on") or DOC.get(True)
        self.assertEqual(DOC["name"], "06 Escenarios y Ensembles")
        self.assertEqual(set(on["workflow_dispatch"]["inputs"]), set(on["workflow_call"]["inputs"]))
        self.assertIs(on["workflow_dispatch"]["inputs"]["deploy_pages"]["default"], False)

    def test_aragon_conserva_su_configuracion(self):
        config, _ = load_config(str(ROOT / "configuracion/ensemble/aragon.json"))
        self.assertEqual(config["contract"]["k"], 67)
        self.assertIn("workflow", json.loads((ROOT / "configuracion/ensemble/congreso_salamanca.json").read_text()))


if __name__ == "__main__":
    unittest.main()
