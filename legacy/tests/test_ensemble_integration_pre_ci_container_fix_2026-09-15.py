from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "herramientas" / "exportar_matriz_ensemble.py"
RUN_KEY = ROOT / "herramientas" / "calcular_clave_ensemble.py"
PREPARE_M04 = ROOT / "herramientas" / "preparar_m04_ensemble.py"


def write_fixture(root: Path) -> Path:
    graph = {
        "nodes": [{"id": str(i), "pop": 10} for i in range(4)],
        "edges": [{"u": "0", "v": "1"}, {"u": "1", "v": "2"}, {"u": "2", "v": "3"}],
    }
    features = []
    for index in range(4):
        x, y = index, 0
        features.append({
            "type": "Feature",
            "properties": {
                "CUSEC_KEY": str(index),
                "district_id": 0 if index < 2 else 1,
                "CUMUN": f"M{index}",
                "CPRO": "P",
                "POP": 10,
                "ddd_unit_id": f"U{index}",
                "COMARCA_COD": "A" if index < 2 else "B",
                "COMARCA_NOM": "Comarca A" if index < 2 else "Comarca B",
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]],
            },
        })
    (root / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    (root / "initial.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8"
    )
    config = {
        "schema": "ddd.ensemble-runner/1.0",
        "territory_id": "synthetic",
        "prepared_bundle_id": "prepared-synthetic-v1",
        "inputs": {"m03_graph": "graph.json", "m04_initial_geojson": "initial.geojson"},
        "fields": {
            "section": "CUSEC_KEY", "district": "district_id", "population": "POP",
            "municipality": "CUMUN", "province": "CPRO", "atomic_unit": "ddd_unit_id",
            "comarca": "COMARCA_COD", "comarca_code_candidates": ["COMARCA_COD"],
            "comarca_name_candidates": ["COMARCA_NOM"],
        },
        "comarca": {"enabled": True},
        "contract": {
            "k": 2, "target_tolerance_ratio": 0.01, "population_floor_ratio": 0.8,
            "population_cap_ratio": 1.75, "municipality_atomicity_limit_ratio": 1.75,
            "require_single_province": True, "require_contiguity": True,
        },
        "engine": {"id": "gerrychain_recom", "steps": 5, "churn_weight": 0.05},
        "ensemble": {"candidate_count": 5, "shortlist_size": 5},
        "output": "output",
    }
    path = root / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def invoke(config: Path, *extra: str) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "ddd_ensemble.runner", "--config", str(config), *extra],
        check=True,
        text=True,
        capture_output=True,
        cwd=ROOT,
    )
    return json.loads(completed.stdout)


class IntegratedRunnerTests(unittest.TestCase):
    def test_aragon_config_and_comarca_source_are_pinned(self):
        source = ROOT / "inputs/COMARCAS.csv"
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            "ac750499cc180c1241465a42b089044cd3095850b078113bc900b1a33538899a",
        )
        with source.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 731)
        self.assertEqual(len({row["Municipio código"] for row in rows}), 731)
        self.assertEqual(len({row["Comarca código"] for row in rows}), 33)
        config = json.loads((ROOT / "configuracion/ensemble/aragon.json").read_text(encoding="utf-8"))
        self.assertEqual(config["contract"]["province_districts"], {"22": 11, "44": 7, "50": 49})
        self.assertEqual(config["prepared_bundle_id"], "AUTO")
        self.assertTrue(config["inputs"]["initial_geojson"].endswith("_m05_distritos_optimizados.geojson.zip"))
        self.assertEqual(config["topology"]["min_shared_border_m"], 1.0)

    @unittest.skipUnless(importlib.util.find_spec("gerrychain"), "GerryChain no instalado")
    def test_real_recom_fifty_candidate_lot(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = write_fixture(root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["ensemble"] = {"candidate_count": 50, "shortlist_size": 10}
            config.write_text(json.dumps(payload), encoding="utf-8")
            result = invoke(config, "--mode", "all")
            self.assertEqual(result["run"], {"executed": 50, "skipped": 0, "failed": 0})
            self.assertTrue(result["summary"]["complete"])
            self.assertEqual(result["summary"]["candidate_count_valid"], 50)
            self.assertEqual(len(list((root / "output/site/assets").glob("*.geojson"))), 50)
            profiles = {
                item["profile"] for item in result["summary"]["candidates"]
                if item["candidate_id"] in result["summary"]["shortlist"]
            }
            self.assertEqual(profiles, {"balanced", "comarca", "comarca_strong", "shape", "exploratory"})

    @unittest.skipUnless(importlib.util.find_spec("gerrychain"), "GerryChain no instalado")
    def test_end_to_end_and_resume(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            config = write_fixture(root)
            first = invoke(config, "--mode", "all")
            self.assertEqual(first["run"], {"executed": 5, "skipped": 0, "failed": 0})
            self.assertTrue(first["summary"]["complete"])
            self.assertEqual(first["summary"]["candidate_count_valid"], 5)
            self.assertTrue((root / "output/site/index.html").is_file())
            self.assertTrue((root / "output/analysis/retry-matrix.json").is_file())

            prepared = subprocess.run(
                [sys.executable, str(PREPARE_M04), "--config", str(config)],
                check=True, text=True, capture_output=True, cwd=ROOT,
            )
            self.assertEqual(json.loads(prepared.stdout)["status"], "REUSED")
            matrix = subprocess.run(
                [sys.executable, str(MATRIX), str(root / "output/plan.json")],
                check=True, text=True, capture_output=True, cwd=ROOT,
            ).stdout.strip()
            self.assertTrue(matrix.startswith("value="))
            self.assertEqual(len(json.loads(matrix.removeprefix("value="))["include"]), 5)
            run_key = subprocess.run(
                [sys.executable, str(RUN_KEY), str(root / "output/plan.json")],
                check=True, text=True, capture_output=True, cwd=ROOT,
            ).stdout.strip()
            self.assertRegex(run_key, r"^value=synthetic-[0-9a-f]{12}$")

            second = invoke(config, "--mode", "all")
            self.assertEqual(second["run"], {"executed": 0, "skipped": 5, "failed": 0})

            candidate = root / "output/results/balanced-01/report.json"
            report = json.loads(candidate.read_text(encoding="utf-8"))
            report["hard_constraints"]["all_pass"] = False
            candidate.write_text(json.dumps(report), encoding="utf-8")
            resumed = invoke(config, "--mode", "run", "--profile", "balanced")
            self.assertEqual(resumed["run"], {"executed": 1, "skipped": 0, "failed": 0})

    def test_workflow_has_single_visible_entry_and_five_profile_parallelism(self):
        workflow = (ROOT / ".github/workflows/generar-alternativas-territoriales.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", workflow)
        self.assertIn("max-parallel: 5", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("--draft", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("PROMOVER_ARAGON_50", workflow)
        self.assertIn("artifact-manifest.json", workflow)
        self.assertIn("needs: synthetic", workflow)
        self.assertIn("DDD_TO_STAGE=M05", workflow)
        self.assertIn("--entrypoint /bin/bash", workflow)
        self.assertIn("auditar_topologia_geometrica.py", workflow)
        interface = (ROOT / ".github/workflows/picadora-territorial.yml").read_text(encoding="utf-8")
        self.assertIn("generar_alternativas_gerrychain", interface)


if __name__ == "__main__":
    unittest.main()
