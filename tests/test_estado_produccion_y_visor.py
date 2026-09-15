"""Pruebas de estado verificable entre producción, contrato y visor."""
from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml

from herramientas.preparar_visor_ejecucion import add_production


ROOT = Path(__file__).resolve().parents[1]


def write_product(path: Path, district_count: int) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"district_id": district_id},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[district_id, 0], [district_id + 1, 0], [district_id + 1, 1], [district_id, 0]]],
                },
            }
            for district_id in range(district_count)
        ],
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("districts.geojson", json.dumps(payload))


class ProductionViewerStateTests(unittest.TestCase):
    def fixture(self, raw: str, *, expected: int = 2, audit: str = "PASS", status: str | None = "PASS"):
        root = Path(raw) / "artifact"
        site = Path(raw) / "site"
        root.mkdir()
        config = Path(raw) / "territory.yaml"
        config.write_text(yaml.safe_dump({
            "meta": {"territory_id": "castilla_y_leon", "territory": "Castilla y León"},
            "modulos": {"modulo_06_consolidar_distritos": {"expected_districts": expected}},
        }), encoding="utf-8")
        (root / "decision.json").write_text(json.dumps({
            "territory_id": "castilla_y_leon", "params": str(config),
        }), encoding="utf-8")
        if status:
            (root / "production_status.json").write_text(json.dumps({
                "schema": "ddd.production-status/1.0",
                "decision": status,
                "territory_id": "castilla_y_leon",
                "params": str(config),
            }), encoding="utf-8")
        (root / "result_m06_contiguedad_geometrica.json").write_text(json.dumps({
            "decision": audit, "gate_statement": f"geometry={audit}",
        }), encoding="utf-8")
        write_product(root / "result_m06_distritos.geojson.zip", 2)
        return root, site

    def test_identity_expected_k_and_pass_come_from_contract_and_status(self):
        with tempfile.TemporaryDirectory() as raw:
            root, site = self.fixture(raw)
            results = []
            add_production(root, site, "123", results)
            self.assertEqual(len(results), 1)
            result = results[0]
            self.assertEqual(result["territory_id"], "castilla_y_leon")
            self.assertEqual(result["territory_label"], "Castilla y León")
            self.assertEqual(result["expected_districts"], 2)
            self.assertEqual(result["observed_districts"], 2)
            self.assertEqual(result["technical_status"], "PASS")
            self.assertEqual(result["status_reasons"], [])

    def test_geometry_and_count_override_a_claimed_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            root, site = self.fixture(raw, expected=3, audit="BLOCK", status="PASS")
            results = []
            add_production(root, site, "456", results)
            result = results[0]
            self.assertEqual(result["technical_status"], "BLOCK")
            self.assertEqual(result["expected_districts"], 3)
            self.assertEqual(result["observed_districts"], 2)
            self.assertEqual(
                result["status_reasons"],
                ["GEOMETRIC_CONTIGUITY_BLOCK", "DISTRICT_COUNT_MISMATCH"],
            )

    def test_old_artifact_without_status_is_never_inferred_as_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            root, site = self.fixture(raw, status=None)
            results = []
            add_production(root, site, "789", results)
            self.assertEqual(results[0]["technical_status"], "UNKNOWN")
            self.assertIn("MISSING_PRODUCTION_STATUS", results[0]["status_reasons"])


class WorkflowGateTests(unittest.TestCase):
    def test_production_emits_status_manifest_in_artifact(self):
        text = (ROOT / ".github/workflows/producir-territorio-por-contrato.yml").read_text(encoding="utf-8")
        self.assertIn('"schema": "ddd.production-status/1.0"', text)
        self.assertIn("production_status.json", text)
        self.assertIn('"PASS" if passed else "BLOCK"', text)

    def test_aragon_regression_requires_independent_geometry(self):
        text = (ROOT / ".github/workflows/regresion-m06-aragon.yml").read_text(encoding="utf-8")
        self.assertIn("auditar_componentes_geometricos.py", text)
        self.assertIn("--expected-districts 67", text)

    def test_aragon_contract_is_executable_but_not_canonical(self):
        config = yaml.safe_load((ROOT / "territorios/aragon/config/aragon_2025.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["meta"]["contract_level"], "production_m01_m06")
        self.assertEqual(config["meta"]["status"], "candidate_blocked_geometric_contiguity")


if __name__ == "__main__":
    unittest.main()
