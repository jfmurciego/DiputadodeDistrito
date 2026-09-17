from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas" / "generar_informe_ejecucion.py"
ROUTER = ROOT / ".github" / "workflows" / "_reutilizable-operacion-territorial.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("ddd_execution_report", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ExecutionReportSyntheticTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def _context(self, result: str = "success") -> dict:
        return {"schema": "ddd-execution-context/1.0", "territory_id": "synthetic", "operation": "producir_resultado_m01_m08", "requested_from": "M01", "requested_to": "M08", "workflow_run_id": "123", "workflow_run_attempt": "1", "production_job_result": result}

    def _complete_fixture(self, root: Path) -> None:
        write_json(root / "ddd-fuentes-123" / "inventario_fuentes.json", {"territory_id": "synthetic", "edition": 2025, "acquisition_mode": "verified_snapshot", "sources": [{"source_id": "official.population", "edition": 2025, "path": "inputs/pop.csv", "sha256": "a" * 64, "bytes": 1234, "urls": ["https://official.example/pop.csv"], "acquired_at": "2026-09-17", "publisher": "Official Authority"}]})
        write_json(root / "ddd-fuentes-123" / "manifiesto_procedencia.json", {"sources": [{"source_id": "official.population", "edition": 2025, "path": "inputs/pop.csv", "sha256": "a" * 64, "bytes": 1234, "urls": ["https://official.example/pop.csv"], "acquired_at": "2026-09-17", "publisher": "Official Authority"}]})
        write_json(root / "ddd-fuentes-123" / "decision_preparacion.json", {"decision": "READY", "checks": {"population_valid": True, "province_coverage_exact": True}})
        write_json(root / "ddd-state-123-M01" / "run" / "synthetic_m01_informe.json", {"sections": 100, "population_total": 100000, "checks": {"unique_sections": True, "population_complete": True}})
        write_json(root / "ddd-state-123-M04" / "run" / "synthetic_m04_informe.json", {"K": 10, "district_count": 10})
        write_json(root / "ddd-state-123-M05" / "run" / "synthetic_m05_informe.json", {"district_count": 10, "population_repair": {"result": "TARGET_MET", "outside_tolerance_after": 0}})
        write_json(root / "ddd-state-123-M06" / "run" / "synthetic_m06_informe.json", {"expected_districts": 10})
        write_json(root / "ddd-audit-123" / "synthetic_m06_contiguedad_geometrica.json", {"schema": "ddd.geometric-components-audit/2.0", "decision": "PASS", "blocked_districts": 0, "governed_exceptions": 1})
        write_json(root / "ddd-audit-123" / "production_status.json", {"decision": "PASS", "population_decision": "TARGET_MET", "population_outcome": "success", "geometric_decision": "PASS"})
        write_json(root / "ddd-electoral-source-123" / "decision_fuente_electoral.json", {"decision": "READY", "selected_source": {"id": "official.election", "url": "https://official.example/election.csv", "sha256": "b" * 64, "bytes": 5678, "declared_resolution": "section"}})
        write_json(root / "ddd-state-123-M07" / "run" / "synthetic_m07_reconciliacion.json", {"decision": "PASS", "unassigned_votes": 0})
        write_json(root / "ddd-state-123-M08" / "run" / "synthetic_m08_resultados.json", {"districts": 10})
        write_json(root / "ddd-publication-123" / "publicacion_visor.json", {"status": "SUCCESS", "viewer_url": "https://example.github.io/ddd/", "result_count": 1, "maps_generated": ["data/map.geojson", "data/viewer-results.json"]})

    def test_complete_execution_is_reported_from_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); self._complete_fixture(root); inv = self.mod.build_inventory(root, self._context())
            self.assertEqual(inv["decision_final"]["decision"], "COMPLETE")
            self.assertEqual(inv["base_territorial_y_poblacion"]["unidades_territoriales"], 100)
            self.assertEqual(inv["base_territorial_y_poblacion"]["poblacion_total"], 100000)
            self.assertEqual(inv["creacion_y_equilibrado_de_distritos"]["distritos_equilibrados"], 10)
            self.assertEqual(inv["control_geografico"]["decision"], "PASS")
            self.assertEqual(inv["incorporacion_electoral"]["votos_no_asignados"], 0)
            self.assertEqual(inv["publicacion_y_visor"]["estado"], "SUCCESS")
            md = self.mod.render_markdown(inv)
            self.assertIn("Fuentes oficiales", md); self.assertIn("Base territorial y población", md); self.assertIn("Publicación y visor", md)

    def test_missing_official_source_blocks_and_explains_stop(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_json(root / "ddd-fuentes-123" / "decision_preparacion.json", {"decision": "BLOCK", "reasons": ["Fuente oficial no disponible"]}); inv = self.mod.build_inventory(root, self._context("failure"))
            self.assertEqual(inv["decision_final"]["decision"], "BLOCK"); self.assertIn("Fuente oficial no disponible", inv["decision_final"]["causas_de_bloqueo"]); self.assertEqual(inv["decision_final"]["hasta_donde_llego"], "Fuentes oficiales")

    def test_invalid_population_is_final_block(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_json(root / "ddd-state-123-M01" / "run" / "synthetic_m01_informe.json", {"sections": 100, "population_total": 100000}); write_json(root / "ddd-audit-123" / "production_status.json", {"decision": "BLOCK", "population_decision": "HARD_BLOCK", "population_outcome": "failure", "block_cause": "POPULATION_TARGET_NOT_MET"}); inv = self.mod.build_inventory(root, self._context("failure"))
            self.assertEqual(inv["decision_final"]["decision"], "BLOCK"); self.assertEqual(inv["creacion_y_equilibrado_de_distritos"]["cumplimiento_poblacional"]["decision"], "HARD_BLOCK"); self.assertIn("POPULATION_TARGET_NOT_MET", inv["decision_final"]["causas_de_bloqueo"])

    def test_blocked_electoral_source_prevents_complete_report(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_json(root / "ddd-electoral-source-123" / "decision_fuente_electoral.json", {"decision": "BLOCK", "reason": "Granularidad insuficiente"}); inv = self.mod.build_inventory(root, self._context("failure"))
            self.assertEqual(inv["decision_final"]["decision"], "BLOCK"); self.assertEqual(inv["incorporacion_electoral"]["decision_fuente"], "BLOCK"); self.assertIn("Granularidad insuficiente", inv["decision_final"]["causas_de_bloqueo"])

    def test_correct_publication_records_viewer_and_maps(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); write_json(root / "ddd-publication-123" / "publicacion_visor.json", {"status": "SUCCESS", "viewer_url": "https://example.github.io/ddd/", "result_count": 2, "maps_generated": ["data/a.geojson", "data/b.geojson"]}); inv = self.mod.build_inventory(root, self._context())
            self.assertEqual(inv["decision_final"]["decision"], "COMPLETE"); self.assertEqual(inv["publicacion_y_visor"]["url_visor"], "https://example.github.io/ddd/"); self.assertEqual(len(inv["publicacion_y_visor"]["mapas_generados"]), 2)

    def test_workflow_has_visible_always_running_business_report_job(self):
        jobs = yaml.safe_load(ROUTER.read_text(encoding="utf-8"))["jobs"]; report = jobs["informe_ejecucion"]
        self.assertEqual(report["name"], "Informe de ejecución"); self.assertIn("always()", report["if"])
        text = ROUTER.read_text(encoding="utf-8")
        self.assertIn("inventario_ejecucion.json", text); self.assertIn("informe_ejecucion.md", text); self.assertIn("pattern: ddd-*", text); self.assertNotIn("gh run view", text)


if __name__ == "__main__":
    unittest.main()
