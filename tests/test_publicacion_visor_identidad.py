from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "herramientas" / "evaluar_publicacion_visor.py"
WORKFLOW = ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("ddd_publication_identity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class PublicationIdentityTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def _production(self, root: Path, workflow_run: str = "123", territory: str = "synthetic") -> None:
        write_json(root / "ddd-audit" / "production_status.json", {
            "schema": "ddd.production-status/1.2",
            "decision": "PASS",
            "territory_id": territory,
            "run_id": f"production-{workflow_run}-1",
        })

    def _registry(self, path: Path, run_id: str = "123", territory: str = "synthetic", maps: int = 2) -> None:
        results = [{
            "id": "static-aragon",
            "territory_id": "aragon",
            "kind": "static",
            "viewer_path": "data/static/aragon.geojson",
        }]
        for index in range(maps):
            results.append({
                "id": f"m0{6 + index}-{run_id}",
                "territory_id": territory,
                "kind": "canonical_m06" if index == 0 else "canonical_m08",
                "run_id": run_id,
                "viewer_path": f"data/results/map-{index}.geojson",
            })
        write_json(path, {"schema": "ddd.viewer-results/1.0", "results": results})

    def test_historical_only_viewer_is_not_complete_execution(self):
        with tempfile.TemporaryDirectory() as td:
            registry = Path(td) / "viewer-results.json"
            write_json(registry, {"schema": "ddd.viewer-results/1.0", "results": [{
                "id": "static-aragon", "territory_id": "aragon", "kind": "static", "viewer_path": "data/static/aragon.geojson"
            }]})
            result = self.mod.evaluate_publication(
                requested_run_id="", registry_path=registry, viewer_url="https://example.test/", deployment_outcome="success", phase="final"
            )
            self.assertEqual(result["status"], "BLOCK")
            self.assertEqual(result["deployment_status"], "BLOCK")
            self.assertTrue(result["historical_only"])
            self.assertIsNone(result["requested_run_id"])
            self.assertIsNone(result["loaded_run_id"])
            self.assertEqual(result["new_map_count"], 0)
            self.assertIn("VISOR_SOLO_HISTORICO_SIN_EJECUCION_SOLICITADA", result["reasons"])

    def test_requested_execution_absent_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "production"
            registry = Path(td) / "viewer-results.json"
            self._registry(registry, run_id="999")
            result = self.mod.evaluate_publication(
                requested_run_id="123", production_root=root, registry_path=registry, phase="prepared"
            )
            self.assertEqual(result["status"], "BLOCK")
            self.assertFalse(result["same_execution"])
            self.assertIn("EXECUCION_SOLICITADA_SIN_EVIDENCIA_GENERADA", result["reasons"])
            self.assertIn("EJECUCION_SOLICITADA_NO_CARGADA_EN_VISOR", result["reasons"])

    def test_wrong_execution_identifier_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "production"
            registry = Path(td) / "viewer-results.json"
            self._production(root, workflow_run="999")
            self._registry(registry, run_id="123")
            result = self.mod.evaluate_publication(
                requested_run_id="123", production_root=root, registry_path=registry, phase="prepared"
            )
            self.assertEqual(result["status"], "BLOCK")
            self.assertEqual(result["generated_run_id"], "999")
            self.assertEqual(result["loaded_run_id"], "123")
            self.assertIn("IDENTIFICADOR_EJECUCION_GENERADA_NO_COINCIDE", result["reasons"])

    def test_correct_publication_records_identity_territory_maps_and_link(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "production"
            registry = Path(td) / "viewer-results.json"
            self._production(root, workflow_run="123", territory="synthetic")
            self._registry(registry, run_id="123", territory="synthetic", maps=2)
            result = self.mod.evaluate_publication(
                requested_run_id="123",
                production_root=root,
                registry_path=registry,
                viewer_url="https://example.test/visor/",
                deployment_outcome="success",
                phase="final",
            )
            self.assertEqual(result["status"], "SUCCESS")
            self.assertEqual(result["deployment_status"], "SUCCESS")
            self.assertTrue(result["same_execution"])
            self.assertEqual(result["requested_run_id"], "123")
            self.assertEqual(result["generated_run_id"], "123")
            self.assertEqual(result["loaded_run_id"], "123")
            self.assertEqual(result["territory_id"], "synthetic")
            self.assertEqual(result["new_map_count"], 2)
            self.assertEqual(len(result["new_maps"]), 2)
            self.assertEqual(result["viewer_url"], "https://example.test/visor/")

    def test_workflow_cannot_silently_fall_back_for_requested_run(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('gh run download "$PRODUCTION_RUN_ID"', text)
        self.assertNotIn("se publicará el registro estático", text)
        self.assertIn("Acreditar identidad de la ejecución descargada", text)
        self.assertIn("Acreditar resultado realmente cargado", text)
        self.assertIn("--strict-request", text)
        self.assertIn("publicacion_visor.json", text)


if __name__ == "__main__":
    unittest.main()
