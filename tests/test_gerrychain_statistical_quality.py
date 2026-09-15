from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ddd_ensemble.statistical_quality import (
    DegeneracyPolicy,
    MetricReservoir,
    aggregate_statistical_results,
    empirical_percentile_rank,
    exploration_diagnostics,
    summarize_distribution,
)


def state_record(step: int, value: float) -> dict:
    return {
        "schema": "ddd.statistical-state/1.0",
        "step": step,
        "assignment_sha256": f"hash-{step}",
        "population_max_abs_deviation": value,
        "polsby_popper_min": 0.20 + value,
        "polsby_popper_mean": 0.30 + value,
        "polsby_popper_median": 0.25 + value,
        "comarca_population_retention": 0.90 - value,
        "comarca_split_communities": step % 3,
        "assignment_churn": value,
        "cut_edges": 10 + step,
        "optimization_score": value,
    }


class DegeneracyGateTests(unittest.TestCase):
    def test_degenerate_chain_fails_below_ten_percent_unique_states(self):
        result = exploration_diagnostics(
            steps_requested=100,
            states_observed=100,
            unique_states=9,
            self_loops=0,
        )
        self.assertFalse(result["all_pass"])
        self.assertEqual(result["status"], "FAIL_DEGENERATE_CHAIN")
        self.assertIn("unique_state_ratio_below_minimum", result["reasons"])
        self.assertAlmostEqual(result["unique_state_ratio"], 0.09)

    def test_sufficiently_exploratory_chain_passes_minimum_gate(self):
        result = exploration_diagnostics(
            steps_requested=100,
            states_observed=100,
            unique_states=25,
            self_loops=40,
        )
        self.assertTrue(result["all_pass"])
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["unique_state_ratio"], 0.10)
        self.assertLessEqual(result["self_loop_rate"], 0.90)

    def test_sticky_chain_fails_self_loop_gate_even_with_unique_floor(self):
        result = exploration_diagnostics(
            steps_requested=100,
            states_observed=100,
            unique_states=10,
            self_loops=90,
            policy=DegeneracyPolicy(min_unique_state_ratio=0.10, max_self_loop_rate=0.90),
        )
        self.assertFalse(result["all_pass"])
        self.assertIn("self_loop_rate_above_maximum", result["reasons"])


class DistributionTests(unittest.TestCase):
    def test_midrank_percentile_and_reference_position_are_correct(self):
        self.assertAlmostEqual(empirical_percentile_rank([1.0, 2.0, 3.0, 4.0], 2.0), 37.5)
        records = [state_record(index, value) for index, value in enumerate((0.01, 0.02, 0.03, 0.04))]
        reference = state_record(-1, 0.02)
        summary = summarize_distribution(records, reference)
        population = summary["distributions"]["population_max_abs_deviation"]
        position = summary["reference_position"]["population_max_abs_deviation"]
        self.assertAlmostEqual(population["p50"], 0.025)
        self.assertAlmostEqual(position["raw_percentile"], 37.5)
        self.assertAlmostEqual(position["favorability_percentile"], 62.5)

    def test_candidate_count_is_not_statistical_state_count(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            reference = state_record(-1, 0.02)
            for candidate_index in range(2):
                candidate = root / f"candidate-{candidate_index}"
                candidate.mkdir()
                records = [state_record(step, 0.01 * (step + 1)) for step in range(3)]
                (candidate / "statistical-states.jsonl").write_text(
                    "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
                )
                engine = {
                    "chain_quality": {"all_pass": True},
                    "run": {"states_observed": 100},
                    "statistical_sample": {
                        "stored_state_count": 3,
                        "reference_map": reference,
                    },
                }
                (candidate / "engine-report.json").write_text(json.dumps(engine), encoding="utf-8")

            summary = aggregate_statistical_results(
                root,
                candidate_count_expected=2,
                candidate_gallery_count=2,
            )
            self.assertTrue(summary["complete"])
            self.assertEqual(summary["candidate_gallery_count"], 2)
            self.assertEqual(summary["statistical_chain_count"], 2)
            self.assertEqual(summary["statistical_state_count"], 6)
            self.assertEqual(summary["states_observed_total"], 200)
            self.assertNotEqual(summary["candidate_gallery_count"], summary["statistical_state_count"])

    def test_reservoir_is_reproducible_with_fixed_seed(self):
        def sample(seed: int):
            reservoir = MetricReservoir(max_samples=10, seed=seed)
            for step in range(100):
                reservoir.observe(state_record(step, step / 1000.0))
            return [record["step"] for record in reservoir.records()]

        first = sample(20260915)
        second = sample(20260915)
        different = sample(20260916)
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertEqual(len(first), 10)


if __name__ == "__main__":
    unittest.main()
