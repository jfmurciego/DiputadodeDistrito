import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from ddd_core.m04_partition_contract import validate_and_annotate_partition
from ddd_core import m05_opt_engine_v741 as m05


class M04PopulationContractTests(unittest.TestCase):
    def test_under_floor_and_above_ceiling_are_diagnostic_not_structural_failures(self):
        frame = pd.DataFrame(
            [
                {"sid": "a", "district_id": 1, "CPRO": "01", "district_pop_section": 20},
                {"sid": "b", "district_id": 1, "CPRO": "01", "district_pop_section": 20},
                {"sid": "c", "district_id": 2, "CPRO": "01", "district_pop_section": 80},
                {"sid": "d", "district_id": 2, "CPRO": "01", "district_pop_section": 80},
            ]
        )
        adjacency = {"a": {"b"}, "b": {"a"}, "c": {"d"}, "d": {"c"}}
        diagnostic = validate_and_annotate_partition(
            frame,
            id_field="sid",
            district_field="district_id",
            province_field="CPRO",
            expected_k=2,
            province_quota={"01": 2},
            adjacency=adjacency,
            floor=50,
            cap=150,
        )
        self.assertEqual(diagnostic["hard_population_violations"], 2)
        self.assertEqual(diagnostic["districts_below_floor"], 1)
        self.assertEqual(diagnostic["districts_above_ceiling"], 1)
        self.assertEqual(
            frame.groupby("district_id")["ddd_population_status"].first().to_dict(),
            {1: "BELOW_FLOOR", 2: "ABOVE_CEILING"},
        )

    def test_structurally_disconnected_partition_still_fails(self):
        frame = pd.DataFrame(
            [
                {"sid": "a", "district_id": 1, "CPRO": "01", "district_pop_section": 50},
                {"sid": "b", "district_id": 1, "CPRO": "01", "district_pop_section": 50},
                {"sid": "c", "district_id": 2, "CPRO": "01", "district_pop_section": 50},
                {"sid": "d", "district_id": 2, "CPRO": "01", "district_pop_section": 50},
            ]
        )
        adjacency = {"a": set(), "b": set(), "c": {"d"}, "d": {"c"}}
        with self.assertRaisesRegex(SystemExit, "desconectado"):
            validate_and_annotate_partition(
                frame,
                id_field="sid",
                district_field="district_id",
                province_field="CPRO",
                expected_k=2,
                province_quota={"01": 2},
                adjacency=adjacency,
                floor=50,
                cap=150,
            )


class M05ImperfectBaselineTests(unittest.TestCase):
    def test_m05_emits_output_when_population_hard_violations_remain(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph_path = root / "graph.json"
            out_path = root / "out.geojson.zip"
            report_path = root / "report.json"
            graph_path.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"id": "a", "pop": 20},
                            {"id": "b", "pop": 20},
                            {"id": "c", "pop": 80},
                            {"id": "d", "pop": 80},
                        ],
                        "edges": [
                            {"u": "a", "v": "b"},
                            {"u": "b", "v": "c"},
                            {"u": "c", "v": "d"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            cfg = {
                "validation": {"province_districts": {"01": 2}},
                "modulos": {
                    "modulo_05_optimizar_distritos": {
                        "in_graph_json": str(graph_path),
                        "in_geojson": str(root / "in.geojson.zip"),
                        "id_field": "sid",
                        "pop_field": "POP",
                        "district_field": "district_id",
                        "province_field": "CPRO",
                        "out_geojson": str(out_path),
                        "out_report": str(report_path),
                        "greedy_moves_limit": 0,
                        "anneal_iters": 0,
                    }
                },
            }
            frame = pd.DataFrame(
                [
                    {"sid": "a", "district_id": 1, "CPRO": "01", "ddd_unit_id": "u1", "ddd_closed_urban": False},
                    {"sid": "b", "district_id": 1, "CPRO": "01", "ddd_unit_id": "u2", "ddd_closed_urban": False},
                    {"sid": "c", "district_id": 2, "CPRO": "01", "ddd_unit_id": "u3", "ddd_closed_urban": False},
                    {"sid": "d", "district_id": 2, "CPRO": "01", "ddd_unit_id": "u4", "ddd_closed_urban": False},
                ]
            )
            written = {}

            def capture_write(gdf, path):
                written["frame"] = gdf.copy()
                written["path"] = str(path)

            argv = ["m05", "--params", str(root / "params.yaml")]
            with (
                patch.object(m05, "load_params_yaml", return_value=cfg),
                patch.object(m05, "load_geo", return_value=frame.copy()),
                patch.object(m05, "write_geo", side_effect=capture_write),
                patch.object(m05, "hard_limits", return_value=(100, 50, 150, 10)),
                patch.object(sys, "argv", argv),
            ):
                m05.main()

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertGreater(report["objective_final"][0], 0)
            self.assertEqual(report["population_baseline_status"], "PASS_WITH_EXCEPTIONS")
            self.assertIn("frame", written)
            statuses = written["frame"].groupby("district_id")["ddd_population_status"].first().to_dict()
            self.assertEqual(statuses, {1: "BELOW_FLOOR", 2: "ABOVE_CEILING"})


if __name__ == "__main__":
    unittest.main()
