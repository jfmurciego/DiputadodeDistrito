from __future__ import annotations

import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from ddd_core.m05_gerrychain_engine import (
    Contract,
    _epsilon_schedule,
    population_target_quality,
)
from ddd_core.m05_gerrychain_strategy import contract_from_params, run_strategy

ROOT = Path(__file__).resolve().parents[1]
GALICIA = ROOT / "territorios/galicia/config/galicia_2025.yaml"


class GerryChainStrategyContractTests(unittest.TestCase):
    def test_galicia_contract_is_derived_without_aragon_literals(self):
        import yaml
        cfg = yaml.safe_load(GALICIA.read_text(encoding="utf-8"))
        contract = contract_from_params(cfg)
        self.assertEqual(contract.k, 75)
        self.assertEqual(contract.province_districts, {"15": 31, "27": 9, "32": 9, "36": 26})
        self.assertAlmostEqual(contract.target_tolerance_ratio, 0.12)
        self.assertTrue(contract.require_municipality_discipline)

    def test_epsilon_schedule_ratchets_to_target(self):
        values = _epsilon_schedule(0.3579, 0.12, 4)
        self.assertEqual(values[-1], 0.12)
        self.assertGreater(values[0], values[-1])
        self.assertEqual(values, sorted(values, reverse=True))

    def test_tolerance_is_quality_target_not_structural_gate(self):
        class Data:
            nodes = {"a": {"population": 60}, "b": {"population": 40}}
        contract = Contract(
            k=2,
            target_tolerance_ratio=0.12,
            population_floor_ratio=0.5,
            population_cap_ratio=1.5,
            require_single_province=False,
            require_contiguity=False,
            require_municipality_discipline=False,
            preserve_closed_urban=False,
        )
        quality = population_target_quality(Data(), {"a": 0, "b": 1}, contract)
        self.assertEqual(quality["districts_outside_tolerance"], 2)


@unittest.skipUnless(os.environ.get("DDD_GALICIA_GERRYCHAIN_E2E"), "requiere artefacto Galicia y GerryChain real")
class GaliciaGerryChainE2E(unittest.TestCase):
    def test_full_galicia_m04_to_gerrychain_strategy(self):
        artifact = Path(os.environ["DDD_GALICIA_GERRYCHAIN_E2E"])
        graph = artifact / "cache/galicia_2025_m03_grafo.json"
        initial = artifact / "cache/galicia_2025_m04_semillas.geojson.zip"
        self.assertTrue(graph.is_file())
        self.assertTrue(initial.is_file())
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            output = root / "galicia_gerrychain_m05.geojson.zip"
            report_path = root / "galicia_gerrychain_m05_report.json"
            report = run_strategy(
                GALICIA,
                graph_override=graph,
                initial_override=initial,
                output_override=output,
                report_override=report_path,
                steps_per_stage=int(os.environ.get("DDD_GERRYCHAIN_STEPS", "120")),
                warmup_rounds=4,
                seed=20260920,
            )
            self.assertTrue(report["hard_constraints"]["all_pass"])
            self.assertTrue(report["objective"]["non_degrading"])
            self.assertEqual(report["target_tolerance"]["before"]["districts_outside_tolerance"], 4)
            self.assertLessEqual(
                report["target_tolerance"]["after"]["districts_outside_tolerance"],
                report["target_tolerance"]["before"]["districts_outside_tolerance"],
            )
            self.assertEqual(len(report["strategy"]["declared_topology_bridges"]), 2)
            self.assertGreater(sum(stage["states_observed"] for stage in report["stages"]), 0)
            self.assertGreaterEqual(max(stage["unique_states"] for stage in report["stages"]), 2)
            self.assertTrue(output.is_file())
            with zipfile.ZipFile(output) as archive:
                geo = json.loads(archive.read(archive.namelist()[0]))
            self.assertEqual(len(geo["features"]), 2134)
            self.assertEqual(len({f["properties"]["district_id"] for f in geo["features"]}), 75)


if __name__ == "__main__":
    unittest.main()
