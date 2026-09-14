from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from ddd_ensemble.candidate_metrics import measure_candidate
from ddd_ensemble.ensemble_assembler import assemble
from ddd_ensemble.ensemble_plan import build_plan
from ddd_ensemble.gallery import build_gallery
from ddd_ensemble.prepared_bundle import BundleValidationError, validate_prepared_bundle


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_bundle(path: Path, coverage: float = 1.0, corrupt: bool = False) -> None:
    files = {
        "M01/secciones.geojson.zip": b"sections",
        "M02/adyacencias.jsonl": b"edges",
        "M03/grafo.json": b"graph",
    }
    manifest = {
        "schema": "ddd.prepared-bundle/1.0",
        "territory_id": "synthetic",
        "territory_year": 2026,
        "bundle_id": "prepared-synthetic-2026-deadbeef",
        "fields": {
            "section_id": "section_id", "population": "population", "province": "province",
            "municipality": "municipality", "comarca_code": "comarca", "comarca_name": "comarca_name",
        },
        "products": {
            "m01_sections": {"path": "M01/secciones.geojson.zip", "sha256": sha(files["M01/secciones.geojson.zip"])},
            "m02_edges": {"path": "M02/adyacencias.jsonl", "sha256": sha(files["M02/adyacencias.jsonl"])},
            "m03_graph": {"path": "M03/grafo.json", "sha256": "0" * 64 if corrupt else sha(files["M03/grafo.json"])},
        },
        "quality": {"section_count": 4, "population_total": 400, "isolated_nodes": 0, "comarca_coverage_ratio": coverage, "status": "PASS"},
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("manifest.json", json.dumps(manifest))
        for name, content in files.items():
            archive.writestr(name, content)


def make_geojson(path: Path) -> None:
    features = []
    cells = [
        ("A", "M1", "C1", 0, 0), ("A", "M2", "C1", 1, 0),
        ("B", "M3", "C2", 0, 1), ("B", "M4", "C2", 1, 1),
    ]
    for index, (district, municipality, comarca, x, y) in enumerate(cells):
        features.append({
            "type": "Feature",
            "properties": {"section_id": str(index), "district_id": district, "population": 100, "municipality": municipality, "comarca": comarca},
            "geometry": {"type": "Polygon", "coordinates": [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]]},
        })
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")


class PreparedBundleTests(unittest.TestCase):
    def test_valid_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prepared.zip"
            make_bundle(path)
            result = validate_prepared_bundle(str(path), "synthetic")
            self.assertEqual(result.manifest["bundle_id"], "prepared-synthetic-2026-deadbeef")
            self.assertEqual(len(result.verified_products), 3)

    def test_corrupt_hash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prepared.zip"
            make_bundle(path, corrupt=True)
            with self.assertRaises(BundleValidationError):
                validate_prepared_bundle(str(path))

    def test_incomplete_comarca_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "prepared.zip"
            make_bundle(path, coverage=0.75)
            with self.assertRaises(BundleValidationError):
                validate_prepared_bundle(str(path))

    def test_zip_slip_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unsafe.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../manifest.json", "{}")
            with self.assertRaises(BundleValidationError):
                validate_prepared_bundle(str(path))


class PlanTests(unittest.TestCase):
    def test_plan_is_deterministic_and_balanced(self):
        first = build_plan("synthetic", "bundle-1")
        second = build_plan("synthetic", "bundle-1")
        self.assertEqual(first, second)
        self.assertEqual(first["candidate_count"], 50)
        self.assertEqual([len(item["candidate_ids"]) for item in first["shards"]], [10] * 5)
        self.assertEqual(len({item["seed"] for item in first["candidates"]}), 50)

    def test_invalid_size_rejected(self):
        with self.assertRaises(ValueError):
            build_plan("synthetic", "bundle-1", 12)


class EndToEndTests(unittest.TestCase):
    def test_complete_fifty_candidate_assembly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = build_plan("synthetic", "bundle-50")
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            results = root / "results"
            for index, candidate in enumerate(plan["candidates"]):
                candidate_dir = results / candidate["candidate_id"]
                candidate_dir.mkdir(parents=True)
                quality = (index % 10) / 100
                report = {
                    "schema": "ddd.candidate-report/1.0",
                    "candidate_id": candidate["candidate_id"],
                    "profile": candidate["profile"],
                    "seed": candidate["seed"],
                    "hard_constraints": {"all_pass": True},
                    "metrics": {
                        "population": {"max_deviation": 0.04 + quality},
                        "shape": {"polsby_popper_median": 0.30 + quality, "corridor_alerts": []},
                        "comarca": {"retention_ratio": 0.90 - quality, "split_count": index % 4},
                        "stability": {"assignment_delta": quality},
                    },
                }
                (candidate_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")
            summary = assemble(str(plan_path), str(results), shortlist_size=10)
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["candidate_count_valid"], 50)
            self.assertEqual(summary["retry_matrix"], {"include": []})
            shortlisted_profiles = {
                next(item["profile"] for item in plan["candidates"] if item["candidate_id"] == candidate_id)
                for candidate_id in summary["shortlist"]
            }
            self.assertEqual(shortlisted_profiles, set(plan["profiles"]))

    def test_metrics_assembler_resume_pareto_and_gallery(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            geojson = root / "candidate.geojson"
            make_geojson(geojson)
            report = measure_candidate(
                str(geojson), "balanced-01", "balanced", 101,
                hard_constraints={"all_pass": True},
            )
            self.assertEqual(report["metrics"]["comarca"]["split_count"], 0)
            self.assertEqual(report["metrics"]["comarca"]["retention_ratio"], 1.0)
            self.assertAlmostEqual(report["metrics"]["population"]["max_deviation"], 0.0)

            plan = build_plan("synthetic", "bundle-1", 5)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            results = root / "results"
            for index, candidate in enumerate(plan["candidates"]):
                candidate_dir = results / candidate["candidate_id"]
                candidate_dir.mkdir(parents=True)
                candidate_report = measure_candidate(
                    str(geojson), candidate["candidate_id"], candidate["profile"], candidate["seed"],
                    hard_constraints={"all_pass": True},
                )
                candidate_report["metrics"]["population"]["max_deviation"] = index * 0.01
                candidate_report["metrics"]["comarca"]["retention_ratio"] = 1.0 - index * 0.01
                (candidate_dir / "report.json").write_text(json.dumps(candidate_report), encoding="utf-8")

            summary = assemble(str(plan_path), str(results), shortlist_size=5)
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["candidate_count_valid"], 5)
            self.assertEqual(len(summary["shortlist"]), 5)
            summary_path = root / "summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            index_path = build_gallery(str(summary_path), str(root / "site"))
            self.assertTrue(index_path.is_file())
            self.assertTrue((root / "site/data/summary.json").is_file())
            self.assertEqual(len(list((root / "site/assets").glob("*.geojson"))), 5)
            html = index_path.read_text(encoding="utf-8")
            self.assertIn("maplibre-gl", html)
            self.assertIn("Mapa A", html)
            self.assertIn("Mapa B", html)

    def test_incomplete_and_invalid_results_generate_targeted_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = build_plan("synthetic", "bundle-1", 5)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            results = root / "results"
            results.mkdir()
            first = plan["candidates"][0]
            first_dir = results / first["candidate_id"]
            first_dir.mkdir()
            report = {
                "candidate_id": first["candidate_id"], "hard_constraints": {"all_pass": False},
                "metrics": {},
            }
            (first_dir / "report.json").write_text(json.dumps(report), encoding="utf-8")
            summary = assemble(str(plan_path), str(results))
            self.assertFalse(summary["complete"])
            self.assertEqual(summary["candidate_count_valid"], 0)
            self.assertEqual(len(summary["missing_candidates"]), 4)
            retried = sum(len(item["candidate_ids"]) for item in summary["retry_matrix"]["include"])
            self.assertEqual(retried, 5)


if __name__ == "__main__":
    unittest.main()
