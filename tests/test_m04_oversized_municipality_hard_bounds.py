import hashlib
import json
import unittest
from pathlib import Path

import yaml

from ddd_core import m04_seed_engine_v745 as engine

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "m04_oversized_municipality"


def load_fixture(name, *, reverse=False):
    payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    node_ids = list(payload["node_ids"])
    weights = dict(zip(node_ids, payload["populations"]))
    order = list(reversed(node_ids)) if reverse else node_ids
    adjacency = {node: set() for node in order}
    edges = list(payload["internal_edges"])
    if reverse:
        edges.reverse()
    for left_i, right_i in edges:
        left, right = node_ids[left_i], node_ids[right_i]
        adjacency[left].add(right)
        adjacency[right].add(left)
    gateways = list(payload["gateway_indices"])
    if reverse:
        gateways.reverse()
    for index in gateways:
        node = node_ids[index]
        adjacency[node].add(f"OUT:{index}")
    contract = payload["contract"]
    target = contract["territory_population"] / contract["k"]
    floor = target * contract["population_floor_ratio"]
    cap = target * contract["population_cap_ratio"]
    tolerance = target * contract["target_tolerance_ratio"]
    return payload, set(node_ids), weights, adjacency, target, floor, cap, tolerance


def partition(case, *, reverse=False, quality_band_as_hard=False):
    payload, nodes, weights, adjacency, target, floor, cap, tolerance = load_fixture(case, reverse=reverse)
    if quality_band_as_hard:
        floor, cap = target - tolerance, target + tolerance
    result = engine.partition_oversized_municipality(
        nodes, target, floor, cap, tolerance, adjacency, weights,
        label=payload["provenance"]["municipality_name"], protected=set(),
    )
    return payload, nodes, weights, adjacency, target, floor, cap, tolerance, result


def canonical_hash(cores, residual):
    parts = [sorted(part) for part in cores] + [sorted(residual)]
    parts.sort(key=lambda part: (part[0], len(part), part))
    raw = json.dumps(parts, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def assert_partition_integrity(testcase, nodes, weights, adjacency, floor, cap, result):
    cores, residual, _mode, gateway_nodes = result
    parts = list(cores) + [residual]
    testcase.assertTrue(residual)
    testcase.assertTrue(set(residual) & set(gateway_nodes))
    testcase.assertEqual(set().union(*parts), nodes)
    testcase.assertEqual(sum(len(part) for part in parts), len(nodes))
    testcase.assertEqual(
        sum(sum(weights[node] for node in part) for part in parts),
        sum(weights.values()),
    )
    for part in parts:
        testcase.assertTrue(engine.connected(part, adjacency))
        population = sum(weights[node] for node in part)
        testcase.assertGreaterEqual(population, floor)
        testcase.assertLessEqual(population, cap)


class OversizedMunicipalityHardBounds(unittest.TestCase):
    def test_logrono_fixture_reproduces_old_tight_band_failure(self):
        with self.assertRaisesRegex(SystemExit, "no se puede extraer núcleo municipal factible"):
            partition("logrono_run_35754690537.json", quality_band_as_hard=True)

    def test_logrono_hard_bounds_find_feasible_deterministic_partition(self):
        data = partition("logrono_run_35754690537.json")
        payload, nodes, weights, adjacency, target, floor, cap, tolerance, result = data
        assert_partition_integrity(self, nodes, weights, adjacency, floor, cap, result)
        cores, residual, _mode, _gateways = result
        self.assertEqual(payload["municipality"]["population"], sum(weights.values()))
        self.assertEqual(canonical_hash(cores, residual), "dbf5feca9122a76c1ce72f30bc6907eeff2c58604cb2ce125f5b3c26ed75f918")
        reversed_result = partition("logrono_run_35754690537.json", reverse=True)[-1]
        self.assertEqual(canonical_hash(*result[:2]), canonical_hash(*reversed_result[:2]))

    def test_alcorcon_fixture_reproduces_old_tight_band_failure(self):
        with self.assertRaisesRegex(SystemExit, "no se puede extraer núcleo municipal factible"):
            partition("alcorcon_run_35755083483.json", quality_band_as_hard=True)

    def test_alcorcon_hard_bounds_allow_quality_outlier(self):
        data = partition("alcorcon_run_35755083483.json")
        payload, nodes, weights, adjacency, target, floor, cap, tolerance, result = data
        assert_partition_integrity(self, nodes, weights, adjacency, floor, cap, result)
        cores, residual, _mode, _gateways = result
        populations = [sum(weights[node] for node in part) for part in list(cores) + [residual]]
        self.assertEqual(payload["municipality"]["population"], sum(populations))
        self.assertEqual(sum(abs(pop - target) > tolerance for pop in populations), 1)
        self.assertEqual(canonical_hash(cores, residual), "0b3c3925fd648b20383c188134f8e03ddeefb7c2802e864faf1937acfa076be3")

    def test_aragon_profile_remains_hard_080_175_quality_012(self):
        cfg = yaml.safe_load((ROOT / "territorios/aragon/config/aragon_2025.yaml").read_text(encoding="utf-8"))
        contract = cfg["territory_contract"]
        self.assertEqual(contract["oversized_municipality_rule"], "split_only_above_hard_cap")
        self.assertEqual(contract["population_floor_ratio"], 0.8)
        self.assertEqual(contract["population_cap_ratio"], 1.75)
        self.assertEqual(contract["target_tolerance_ratio"], 0.12)
        self.assertEqual(contract["municipality_atomicity_limit_ratio"], 1.75)
        nodes = {"a", "b", "c", "d"}
        weights = {node: 90 for node in nodes}
        adjacency = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c", "OUT"}}
        result = engine.partition_oversized_municipality(nodes, 100.0, 80.0, 175.0, 12.0, adjacency, weights)
        assert_partition_integrity(self, nodes, weights, adjacency, 80.0, 175.0, result)

    def test_castilla_y_leon_profile_keeps_closed_core_open_residual(self):
        cfg = yaml.safe_load((ROOT / "territorios/castilla_y_leon/config/castilla_y_leon_2025.yaml").read_text(encoding="utf-8"))
        contract = cfg["territory_contract"]
        self.assertEqual(contract["oversized_municipality_rule"], "closed_target_cores_plus_open_residual")
        self.assertEqual(contract["population_floor_ratio"], 0.8)
        self.assertEqual(contract["population_cap_ratio"], 1.75)
        self.assertEqual(contract["target_tolerance_ratio"], 0.12)
        self.assertEqual(contract["municipality_atomicity_limit_ratio"], 1.12)
        nodes = {"a", "b", "c"}
        weights = {"a": 95, "b": 95, "c": 50}
        adjacency = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "OUT"}}
        result = engine.partition_oversized_municipality(nodes, 100.0, 80.0, 175.0, 12.0, adjacency, weights)
        assert_partition_integrity(self, nodes, weights, adjacency, 80.0, 175.0, result)
        cores, residual, _mode, gateway_nodes = result
        self.assertEqual(len(cores), 1)
        self.assertIn("c", residual)
        self.assertIn("c", gateway_nodes)


if __name__ == "__main__":
    unittest.main()
