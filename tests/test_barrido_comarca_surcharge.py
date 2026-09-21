from pathlib import Path
import unittest
import yaml

from ddd_core.m05_gerrychain_strategy import PreparedProblem, StrategyContract
from herramientas.barrer_comarca_surcharge_aragon import (
    BASELINE_CANONICAL,
    comarca_metrics,
    rows_from_portfolio,
)

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
        self.assertEqual(cfg["baseline"]["source_artifact"], "gh-34599224954-1")
        self.assertEqual(cfg["baseline"]["comarcas_divididas"], 31)
        self.assertEqual(cfg["baseline"]["comarcas_divididas_evitables"], 20)
        self.assertAlmostEqual(cfg["baseline"]["retencion_comarcal"], 0.290)
        self.assertAlmostEqual(cfg["baseline"]["retencion_techo_teorico"], 0.352)
        self.assertAlmostEqual(cfg["baseline"]["retencion_sobre_maximo"], 0.822)
        self.assertEqual(
            cfg["metrics"],
            [
                "comarcas_divididas",
                "comarcas_divididas_evitables",
                "retencion_comarcal",
                "retencion_techo_teorico",
                "retencion_sobre_maximo",
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
        metrics = comarca_metrics(
            problem,
            problem.initial_assignment,
            target_tolerance_ratio=0.12,
        )
        self.assertEqual(metrics["comarcas_divididas"], 1)
        self.assertEqual(metrics["comarcas_divididas_evitables"], 1)
        self.assertAlmostEqual(metrics["retencion_comarcal"], 0.8)
        self.assertAlmostEqual(metrics["retencion_techo_teorico"], 1.0)
        self.assertAlmostEqual(metrics["retencion_sobre_maximo"], 0.8)

    def test_one_metric_row_is_kept_per_seed(self):
        units = {
            "a": {"population": 50.0, "comarca": "C1", "province": "01", "municipality": "m1", "closed_urban": False},
            "b": {"population": 50.0, "comarca": "C1", "province": "01", "municipality": "m2", "closed_urban": False},
            "c": {"population": 50.0, "comarca": "C2", "province": "01", "municipality": "m3", "closed_urban": False},
            "d": {"population": 50.0, "comarca": "C2", "province": "01", "municipality": "m4", "closed_urban": False},
        }
        problem = PreparedProblem(
            sections=None,
            units=units,
            edges=[("a", "b"), ("c", "d")],
            initial_assignment={"a": 1, "b": 1, "c": 2, "d": 2},
            frozen_districts={},
            target_population=100.0,
        )
        contract = StrategyContract(
            expected_k=2,
            target_tolerance_ratio=0.12,
            population_floor_ratio=0.0,
            population_cap_ratio=10.0,
            require_single_province=False,
            require_contiguity=False,
            require_municipality_discipline=False,
            preserve_closed_urban=False,
        )
        runs = [
            {"seed": seed, "assignment_hash": f"h{seed}", "assignment": dict(problem.initial_assignment)}
            for seed in (101, 102, 103, 104)
        ]
        portfolio = {"runs": runs, "selected": runs[2]}
        rows = rows_from_portfolio(problem, contract, 0.5, portfolio)
        self.assertEqual(len(rows), 4)
        self.assertEqual([row["seed"] for row in rows], [101, 102, 103, 104])
        self.assertEqual(sum(bool(row["selected_for_surcharge"]) for row in rows), 1)
        self.assertEqual({row["comarca_surcharge"] for row in rows}, {0.5})
        self.assertEqual({row["row_type"] for row in rows}, {"barrido"})

    def test_canonical_baseline_is_preserved_verbatim(self):
        self.assertEqual(BASELINE_CANONICAL["source_artifact"], "gh-34599224954-1")
        self.assertEqual(BASELINE_CANONICAL["comarcas_divididas"], 31)
        self.assertEqual(BASELINE_CANONICAL["comarcas_divididas_evitables"], 20)
        self.assertAlmostEqual(BASELINE_CANONICAL["retencion_comarcal"], 0.290)
        self.assertAlmostEqual(BASELINE_CANONICAL["retencion_techo_teorico"], 0.352)
        self.assertAlmostEqual(BASELINE_CANONICAL["retencion_sobre_maximo"], 0.822)

    def test_retention_ceiling_accounts_for_unavoidable_large_comarca(self):
        problem = PreparedProblem(
            sections=None,
            units={
                "big1": {"population": 100.0, "comarca": "BIG"},
                "big2": {"population": 100.0, "comarca": "BIG"},
                "small": {"population": 100.0, "comarca": "SMALL"},
            },
            edges=[],
            initial_assignment={"big1": 1, "big2": 2, "small": 3},
            frozen_districts={},
            target_population=100.0,
        )
        metrics = comarca_metrics(
            problem,
            problem.initial_assignment,
            target_tolerance_ratio=0.12,
        )
        self.assertEqual(metrics["comarcas_divididas"], 1)
        self.assertEqual(metrics["comarcas_divididas_evitables"], 0)
        self.assertAlmostEqual(metrics["retencion_comarcal"], 2 / 3)
        self.assertAlmostEqual(metrics["retencion_techo_teorico"], 212 / 300)
        self.assertAlmostEqual(metrics["retencion_sobre_maximo"], (2 / 3) / (212 / 300))


if __name__ == "__main__":
    unittest.main()
