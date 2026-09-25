from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import geopandas as gpd
import yaml
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
M06 = ROOT / "modulos" / "06_consolidar_distritos.py"
STATUS = ROOT / "herramientas" / "estado_produccion.py"
CERTIFY = ROOT / "herramientas" / "certificar_ejecucion.py"


def write_zip_input(path: Path, populations):
    gdf = gpd.GeoDataFrame(
        {
            "CUSEC_KEY": ["0100101001", "0100201001"],
            "district_id": [1, 2],
            "POP_2025": populations,
            "CPRO": ["01", "01"],
            "NPRO": ["Sintética", "Sintética"],
            "CUMUN": ["01001", "01002"],
            "NMUN": ["A", "B"],
            "CUDIS": ["01", "01"],
            "ddd_unit_id": ["u1", "u2"],
            "ddd_closed_urban": [False, False],
        },
        geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)],
        crs="EPSG:4326",
    )
    member = path.with_suffix("")
    gdf.to_file(member, driver="GeoJSON")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(member, arcname="m05.geojson")
    member.unlink()


def write_json(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class ConsolidationStatusCertificationIntegration(unittest.TestCase):
    def build_case(self, root: Path, populations):
        m05_geo = root / "m05.geojson.zip"
        write_zip_input(m05_geo, populations)
        m05_report = root / "m05_report.json"
        # Deliberadamente conforme: la regresión exige que el estado tome la
        # evidencia real de M06 y no dependa únicamente del informe M05.
        write_json(m05_report, {
            "version": "synthetic",
            "objective_start": [0, 0, 0, 0.0, 0.0],
            "objective_final": [0, 0, 0, 0.0, 0.0],
        })

        params = root / "params.yaml"
        cfg = {
            "meta": {"run_name": "integrated", "year": 2025},
            "io": {"project_root": {"path": str(root)}},
            "modulos": {
                "modulo_05_optimizar_distritos": {
                    "out_report": str(m05_report),
                },
                "modulo_06_consolidar_distritos": {
                    "in_geojson": str(m05_geo),
                    "id_field": "CUSEC_KEY",
                    "district_field": "district_id",
                    "pop_field": "POP_2025",
                    "province_field": "CPRO",
                    "province_name_field": "NPRO",
                    "municipality_field": "CUMUN",
                    "municipality_name_field": "NMUN",
                    "cudis_field": "CUDIS",
                    "metric_crs": "EPSG:3035",
                    "expected_districts": 2,
                    "strict_expected_k": True,
                    "out_summary_csv": str(root / "m06_summary.csv"),
                    "out_catalog_csv": str(root / "m06_catalog.csv"),
                    "out_composition_csv": str(root / "m06_composition.csv"),
                    "out_geojson": str(root / "m06_sections.geojson.zip"),
                    "out_district_geojson": str(root / "m06_districts.geojson.zip"),
                    "out_diagnostic_json": str(root / "m06_diagnostic.json"),
                },
            },
            "validation": {
                "expected_districts": 2,
                "population_floor_ratio": 0.50,
                "population_cap_ratio": 1.50,
                "target_tolerance_ratio": 0.10,
                "province_districts": {"01": 2},
                "province_field": "CPRO",
                "municipality_field": "CUMUN",
                "require_single_province_per_district": True,
            },
        }
        params.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

        geometric = root / "geometric.json"
        write_json(geometric, {
            "schema": "ddd.geometric-components-audit/2.0",
            "decision": "PASS",
            "connected_districts": 2,
            "governed_exceptions": 0,
            "blocked_districts": 0,
            "policy_mismatches": 0,
            "contract_blockers": [],
            "districts": [],
        })
        return params, geometric

    def run_chain(self, populations):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        params, geometric = self.build_case(root, populations)

        m06 = subprocess.run(
            [sys.executable, str(M06), "--params", str(params)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(m06.returncode, 0, m06.stdout + m06.stderr)
        self.assertTrue((root / "m06_diagnostic.json").is_file())

        status_path = root / "production_status.json"
        status = subprocess.run(
            [
                sys.executable, str(STATUS),
                "--params", str(params),
                "--territory-id", "synthetic",
                "--run-id", "integration-1",
                "--from-stage", "M01",
                "--to-stage", "M08",
                "--execution-outcome", "success",
                "--geometric-outcome", "success",
                "--geometric-decision", "PASS",
                "--geometric-audit", str(geometric),
                "--output", str(status_path),
            ],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        self.assertEqual(status.returncode, 0, status.stdout + status.stderr)
        production_status = json.loads(status_path.read_text(encoding="utf-8"))
        self.assertEqual(production_status["population_evidence_source"], "M06_DIAGNOSTIC")
        self.assertEqual(production_status["m06_population_diagnostic_status"], "VALID")
        self.assertEqual(
            Path(production_status["m06_population_diagnostic_path"]),
            (root / "m06_diagnostic.json").resolve(),
        )

        decision = root / "decision.json"
        manifest = root / "manifest.json"
        validation = root / "validation.json"
        reconciliation = root / "reconciliation.json"
        certification = root / "certification.json"
        write_json(decision, {
            "decision": "ADMITTED",
            "production_authorization": "AUTHORIZED",
            "territory_id": "synthetic",
            "contract": {"contract_sha256": "c" * 64},
        })
        write_json(manifest, {
            "run_id": "integration-1",
            "outputs": {
                "synthetic_m06_distritos.geojson.zip": {"sha256": "1" * 64},
                "synthetic_m07_reconciliacion.json": {"sha256": "2" * 64},
                "synthetic_m08_distritos_resultados.geojson.zip": {"sha256": "3" * 64},
            },
        })
        write_json(validation, {
            "run_id": "integration-1",
            "estado": "PASS",
            "failures": [],
            "expected_districts": 2,
            "districts_found": 2,
        })
        write_json(reconciliation, {
            "status": "PASS",
            "input_votes": 100,
            "assigned_votes": 100,
            "unassigned_votes": 0,
            "errors": [],
        })

        certify = subprocess.run(
            [
                sys.executable, str(CERTIFY),
                "--decision", str(decision),
                "--production-status", str(status_path),
                "--geometric-audit", str(geometric),
                "--manifest", str(manifest),
                "--validation", str(validation),
                "--reconciliation", str(reconciliation),
                "--source-commit", "a" * 40,
                "--workflow-run-id", "123",
                "--output", str(certification),
            ],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        result = json.loads(certification.read_text(encoding="utf-8"))
        return td, root, production_status, certify, result

    def test_nonconforming_m06_artifacts_flow_to_hard_block_and_blocked_certification(self):
        td, root, status, certify, result = self.run_chain([40, 160])
        try:
            diagnostic = json.loads((root / "m06_diagnostic.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["hard_population_violations"], 2)
            self.assertEqual(status["population_decision"], "HARD_BLOCK")
            self.assertEqual(status["population_hard_constraints_after"], 2)
            self.assertEqual(status["decision"], "BLOCK")
            self.assertNotEqual(certify.returncode, 0)
            self.assertEqual(result["decision"], "BLOCKED")
            self.assertIn("POPULATION_HARD_BLOCK", result["errors"])
            self.assertIn("POPULATION_HARD_CONSTRAINTS", result["errors"])
            self.assertEqual(result["publication"]["status"], "BLOCKED")
        finally:
            td.cleanup()

    def test_conforming_m06_artifacts_flow_through_same_wire_and_can_certify(self):
        td, root, status, certify, result = self.run_chain([100, 100])
        try:
            diagnostic = json.loads((root / "m06_diagnostic.json").read_text(encoding="utf-8"))
            self.assertEqual(diagnostic["hard_population_violations"], 0)
            self.assertEqual(status["population_hard_constraints_after"], 0)
            self.assertNotEqual(status["population_decision"], "HARD_BLOCK")
            self.assertIn(status["decision"], {"PASS", "PASS_WITH_EXCEPTIONS"})
            self.assertEqual(certify.returncode, 0, certify.stdout + certify.stderr)
            self.assertIn(result["decision"], {"CERTIFIED", "CERTIFIED_WITH_GOVERNED_EXCEPTIONS"})
            self.assertEqual(result["errors"], [])
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
