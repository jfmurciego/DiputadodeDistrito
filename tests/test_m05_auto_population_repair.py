from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "modulos" / "05_optimizar_distritos.py"

spec = importlib.util.spec_from_file_location("ddd_m05_wrapper_auto_repair", MODULE_PATH)
m05 = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(m05)


def frame(populations):
    return pd.DataFrame(
        [
            {
                "CUSEC_KEY": "a",
                "district_id": 1,
                "CPRO": "01",
                "ddd_unit_id": "u1",
                "ddd_closed_urban": False,
            },
            {
                "CUSEC_KEY": "b",
                "district_id": 2,
                "CPRO": "01",
                "ddd_unit_id": "u2",
                "ddd_closed_urban": False,
            },
        ]
    )


class AutoPopulationRepairActivationTests(unittest.TestCase):
    def make_files(self, root: Path, populations):
        graph = root / "graph.json"
        graph.write_text(
            json.dumps(
                {
                    "nodes": [
                        {"id": "a", "pop": populations[0]},
                        {"id": "b", "pop": populations[1]},
                    ],
                    "edges": [{"u": "a", "v": "b"}],
                }
            ),
            encoding="utf-8",
        )
        report = root / "report.json"
        report.write_text(
            json.dumps({"objective_start": [0, 0, 0, 0, 0], "objective_final": [0, 0, 0, 0, 0]}),
            encoding="utf-8",
        )
        out = root / "out.geojson.zip"
        out.write_bytes(b"placeholder")
        return graph, report, out

    def s5(self, graph, extra=None):
        data = {
            "in_graph_json": str(graph),
            "id_field": "CUSEC_KEY",
            "district_field": "district_id",
            "province_field": "CPRO",
        }
        if extra is not None:
            data["population_repair"] = extra
        return data

    def test_absent_contract_block_auto_activates_on_structurally_valid_hard_violations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph, report, out = self.make_files(root, [40, 160])
            repaired = {
                "result": "REPAIRED",
                "assignments": {"u1": 1, "u2": 2},
                "hard_limits_met": True,
                "final_hard_population_violations": 0,
            }
            with (
                patch.object(m05, "load_geo", return_value=frame([40, 160])),
                patch.object(m05, "write_geo"),
                patch.object(m05, "hard_limits", return_value=(100, 50, 150, 10)),
                patch.object(m05, "repair", return_value=repaired) as repair_mock,
            ):
                result = m05._apply_population_repair({}, self.s5(graph), out, report)

            self.assertTrue(result["enabled"])
            self.assertEqual(result["activation"], "AUTO_HARD_VIOLATIONS")
            self.assertEqual(result["hard_population_violations_before"], 2)
            self.assertEqual(result["result"], "REPAIRED")
            limits = repair_mock.call_args.kwargs["limits"]
            self.assertEqual(limits.max_depth, 3)
            self.assertEqual(limits.max_transfer_set, 2)
            self.assertEqual(limits.max_candidates, 5000)
            self.assertEqual(limits.max_seconds, 5.0)
            saved = json.loads(report.read_text(encoding="utf-8"))["population_repair"]
            self.assertEqual(saved["activation"], "AUTO_HARD_VIOLATIONS")

    def test_explicit_false_wins_and_reports_disabled_without_search(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph, report, out = self.make_files(root, [40, 160])
            cfg = {
                "enabled": False,
                "max_depth": 9,
                "max_transfer_set": 9,
                "max_candidates": 9,
                "max_seconds": 9,
                "seed": 9,
            }
            with patch.object(m05, "repair") as repair_mock:
                result = m05._apply_population_repair({}, self.s5(graph, cfg), out, report)

            repair_mock.assert_not_called()
            self.assertFalse(result["enabled"])
            self.assertEqual(result["activation"], "EXPLICITLY_DISABLED")
            self.assertEqual(result["result"], "DISABLED")

    def test_absent_contract_block_with_no_hard_violations_is_disabled_not_no_feasible(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph, report, out = self.make_files(root, [100, 100])
            with (
                patch.object(m05, "load_geo", return_value=frame([100, 100])),
                patch.object(m05, "hard_limits", return_value=(100, 50, 150, 10)),
                patch.object(m05, "repair") as repair_mock,
            ):
                result = m05._apply_population_repair({}, self.s5(graph), out, report)

            repair_mock.assert_not_called()
            self.assertFalse(result["enabled"])
            self.assertEqual(result["activation"], "NOT_NEEDED")
            self.assertEqual(result["result"], "DISABLED")

    def test_structurally_invalid_partition_does_not_auto_activate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            graph, report, out = self.make_files(root, [40, 160])
            broken = frame([40, 160])
            broken.loc[1, "CPRO"] = "02"
            with (
                patch.object(m05, "load_geo", return_value=broken),
                patch.object(m05, "hard_limits", return_value=(100, 50, 150, 10)),
                patch.object(m05, "repair") as repair_mock,
            ):
                with self.assertRaisesRegex(SystemExit, "baseline estructuralmente inválido"):
                    m05._apply_population_repair({}, self.s5(graph), out, report)
            repair_mock.assert_not_called()


if __name__ == "__main__":
    unittest.main()
