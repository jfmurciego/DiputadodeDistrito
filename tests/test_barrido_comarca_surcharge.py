from pathlib import Path
import unittest
import yaml

from ddd_core.m05_gerrychain_strategy import PreparedProblem
from herramientas.barrer_comarca_surcharge_aragon import comarca_metrics

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "configuracion/experimentos/barrido_comarca_surcharge_aragon.yaml"


class BarridoComarcaSurchargeTests(unittest.TestCase):
    def test_spec_is_metrics_only_and_fixed_values(self):
        cfg = yaml.safe_load(SPEC.read_text(encoding="utf-8")) or {}
        self.assertEqual(cfg["territory_id"], "aragon")
        self.assertEqual(cfg["comarca_surcharge_values"], [0.3, 0.4, 0.5, 0.6, 0.8])
        self.assertEqual(cfg["promotion"], "forbidden")
        self.assertFalse(cfg["publication"])
        self.assertEqual(cfg["persistence"], "metrics_only")
        self.assertEqual(
            cfg["metrics"],
            [
                "comarcas_divididas",
                "retencion_comarcal",
                "polsby_popper_min",
                "polsby_popper_median",
                "max_relative_deviation",
            ],
        )

    def test_comarca_metrics_count_splits_and_retention(self):
        problem = PreparedProblem(
            sections=None,
            units={
                "a": {"population": 60.0, "comarca": "C1"},
                "b": {"population": 40.0, "comarca": "C1"},
                "c": {"population": 50.0, "comarca": "C2"},
                "d": {"population": 50.0, "comarca": "C2"},
            },
            edges=[],
            initial_assignment={"a": 1, "b": 2, "c": 2, "d": 2},
            frozen_districts={},
            target_population=100.0,
        )
        metrics = comarca_metrics(problem, problem.initial_assignment)
        self.assertEqual(metrics["comarcas_divididas"], 1)
        self.assertAlmostEqual(metrics["retencion_comarcal"], 0.8)


if __name__ == "__main__":
    unittest.main()
