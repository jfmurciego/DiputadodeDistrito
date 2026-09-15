import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ddd_core.m05_gerrychain_engine import (
    Contract, InputContractError, adapt_inputs, assignment_hash,
    comarca_metrics, geometric_shape_metrics, hard_constraint_violations, load_comarca_lookup,
    output_geojson, run_gerrychain, select_best_state,
)


def synthetic(comarcas=("A", "A", "B", "B")):
    graph = {
        "nodes": [{"id": str(i), "pop": 10} for i in range(4)],
        "edges": [{"u": "0", "v": "1"}, {"u": "1", "v": "2"}, {"u": "2", "v": "3"}],
    }
    features = []
    for i in range(4):
        features.append({
            "type": "Feature",
            "properties": {
                "CUSEC_KEY": str(i), "district_id": 0 if i < 2 else 1,
                "CUMUN": f"M{i}", "CPRO": "P", "POP": 10,
                "ddd_unit_id": f"U{i}", "COMARCA_COD": comarcas[i],
                "COMARCA_NOM": f"Comarca {comarcas[i]}",
            },
            "geometry": None,
        })
    return graph, {"type": "FeatureCollection", "features": features}


def contract(**changes):
    values = dict(k=2, target_tolerance_ratio=0.01, population_floor_ratio=0.8, population_cap_ratio=1.75)
    values.update(changes)
    return Contract(**values)


class AdapterAndMetricsTests(unittest.TestCase):
    def test_join_uses_section_not_repeated_atomic_unit(self):
        graph, geo = synthetic()
        geo["features"][0]["properties"]["ddd_unit_id"] = "SAME"
        geo["features"][1]["properties"]["ddd_unit_id"] = "SAME"
        data = adapt_inputs(graph, geo, population_field="POP", comarca_enabled=True)
        self.assertEqual(set(data.nodes), {"0", "1", "2", "3"})
        self.assertEqual(data.nodes["0"]["atomic_unit"], "SAME")
        self.assertEqual(data.nodes["1"]["atomic_unit"], "SAME")

    def test_universe_mismatch_blocks_before_engine(self):
        graph, geo = synthetic(); geo["features"].pop()
        with self.assertRaisesRegex(InputContractError, "Universos"):
            adapt_inputs(graph, geo)

    def test_population_mismatch_blocks(self):
        graph, geo = synthetic(); geo["features"][0]["properties"]["POP"] = 11
        with self.assertRaisesRegex(InputContractError, "Población"):
            adapt_inputs(graph, geo, population_field="POP")

    def test_comarca_missing_blocks_only_when_enabled(self):
        graph, geo = synthetic()
        del geo["features"][0]["properties"]["COMARCA_COD"]
        del geo["features"][0]["properties"]["COMARCA_NOM"]
        adapt_inputs(graph, geo, comarca_enabled=False)
        with self.assertRaisesRegex(InputContractError, "Cobertura comarcal"):
            adapt_inputs(graph, geo, comarca_enabled=True)

    def test_atomic_unit_split_is_hard_violation(self):
        graph, geo = synthetic()
        geo["features"][0]["properties"]["ddd_unit_id"] = "SAME"
        geo["features"][1]["properties"]["ddd_unit_id"] = "SAME"
        data = adapt_inputs(graph, geo)
        broken = {"0": 0, "1": 1, "2": 1, "3": 0}
        self.assertIn("atomic_unit:SAME", hard_constraint_violations(data, broken, contract()))

    def test_small_municipality_split_is_hard_violation(self):
        graph, geo = synthetic()
        geo["features"][0]["properties"]["CUMUN"] = "M"
        geo["features"][1]["properties"]["CUMUN"] = "M"
        data = adapt_inputs(graph, geo)
        broken = {"0": 0, "1": 1, "2": 1, "3": 0}
        self.assertIn("municipality:M", hard_constraint_violations(data, broken, contract()))

    def test_province_apportionment_is_hard_constraint(self):
        graph, geo = synthetic()
        geo["features"][2]["properties"]["CPRO"] = "Q"
        geo["features"][3]["properties"]["CPRO"] = "Q"
        data = adapt_inputs(graph, geo)
        violations = hard_constraint_violations(
            data, data.initial_assignment, contract(province_districts={"P": 2, "Q": 0})
        )
        self.assertIn("province_count:P", violations)
        self.assertIn("province_count:Q", violations)

    def test_split_municipality_allows_only_one_mixed_district(self):
        graph, geo = synthetic()
        for feature in geo["features"]:
            section = feature["properties"]["CUSEC_KEY"]
            feature["properties"]["CUMUN"] = "BIG" if section in {"0", "2"} else f"OTHER-{section}"
        data = adapt_inputs(graph, geo)
        violations = hard_constraint_violations(data, data.initial_assignment, contract())
        self.assertIn("municipality_mixed:BIG", violations)

    def test_closed_urban_district_is_frozen(self):
        graph, geo = synthetic()
        for feature in geo["features"][:2]:
            feature["properties"]["ddd_closed_urban"] = True
        data = adapt_inputs(graph, geo)
        changed = {"0": 0, "1": 1, "2": 0, "3": 1}
        self.assertIn("closed_urban:0", hard_constraint_violations(data, changed, contract()))

    def test_non_contiguous_district_blocks(self):
        graph, geo = synthetic(); data = adapt_inputs(graph, geo)
        broken = {"0": 0, "1": 1, "2": 1, "3": 0}
        self.assertIn("contiguity:0", hard_constraint_violations(data, broken, contract()))

    def test_comarca_metrics_reward_aligned_boundaries(self):
        graph, geo = synthetic(); data = adapt_inputs(graph, geo, comarca_enabled=True)
        aligned = comarca_metrics(data, data.initial_assignment)
        crossed = comarca_metrics(data, {"0": 0, "1": 1, "2": 1, "3": 0})
        self.assertEqual(aligned["split_communities"], 0)
        self.assertEqual(aligned["population_retention"], 1)
        self.assertEqual(crossed["split_communities"], 2)
        self.assertEqual(crossed["population_retention"], 0.5)

    def test_best_state_is_not_necessarily_last(self):
        graph, geo = synthetic(); data = adapt_inputs(graph, geo, comarca_enabled=True)
        worse = {"0": 1, "1": 1, "2": 0, "3": 0}
        selected, metrics, step = select_best_state(data, [data.initial_assignment, worse], contract())
        self.assertEqual(selected, data.initial_assignment)
        self.assertEqual(step, 0)
        self.assertEqual(metrics["comarca"]["population_retention"], 1)

    def test_output_preserves_geometry_and_changes_only_assignment(self):
        graph, geo = synthetic()
        geo["features"][0]["geometry"] = {"type": "Point", "coordinates": [0, 0]}
        data = adapt_inputs(graph, geo)
        changed = {"0": 1, "1": 1, "2": 0, "3": 0}
        out = output_geojson(data, changed)
        self.assertEqual(out["features"][0]["geometry"], geo["features"][0]["geometry"])
        self.assertEqual(out["features"][0]["properties"]["district_id"], 1)
        self.assertEqual(geo["features"][0]["properties"]["district_id"], 0)

    def test_output_materializes_comarca_from_lookup(self):
        graph, geo = synthetic()
        for feature in geo["features"]:
            feature["properties"].pop("COMARCA_COD")
            feature["properties"].pop("COMARCA_NOM")
        lookup = {f"M{i}": ("A" if i < 2 else "B", "Comarca") for i in range(4)}
        data = adapt_inputs(graph, geo, comarca_lookup=lookup, comarca_enabled=True)
        out = output_geojson(data, data.initial_assignment)
        self.assertEqual(out["features"][0]["properties"]["ddd_comarca_codigo"], "A")

    def test_assignment_hash_independent_of_dict_order(self):
        self.assertEqual(assignment_hash({"a": 1, "b": 2}), assignment_hash({"b": 2, "a": 1}))

    def test_metric_border_rejects_corner_only_graph_edge(self):
        graph = {"nodes": [{"id": "0", "pop": 10}, {"id": "1", "pop": 10}], "edges": [{"u": "0", "v": "1"}]}
        features = []
        for index, (x, y) in enumerate(((0, 0), (1, 1))):
            features.append({
                "type": "Feature",
                "properties": {"CUSEC_KEY": str(index), "district_id": index, "CUMUN": f"M{index}", "CPRO": "P", "POP": 10},
                "geometry": {"type": "Polygon", "coordinates": [[[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]]},
            })
        geo = {"type": "FeatureCollection", "features": features}
        with self.assertRaisesRegex(InputContractError, "frontera métrica"):
            adapt_inputs(graph, geo, population_field="POP", min_shared_border_m=0.5)

    def test_initial_partition_is_checked_before_chain(self):
        graph, geo = synthetic()
        data = adapt_inputs(graph, geo)
        data.initial_assignment = {"0": 0, "1": 1, "2": 1, "3": 0}
        with self.assertRaisesRegex(InputContractError, "partición inicial"):
            run_gerrychain(data, contract(), total_steps=2, seed=1)

    def test_shape_metric_uses_real_area_and_shared_border(self):
        graph, geo = synthetic()
        for index, feature in enumerate(geo["features"]):
            feature["geometry"] = {
                "type": "Polygon",
                "coordinates": [[[index, 0], [index + 1, 0], [index + 1, 1], [index, 1], [index, 0]]],
            }
        data = adapt_inputs(graph, geo)
        metrics = geometric_shape_metrics(data, data.initial_assignment)
        self.assertTrue(metrics["available"])
        self.assertGreater(metrics["polsby_popper_min"], 0.6)

    def test_real_comarca_lookup_rejects_ambiguity(self):
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "c.csv"
            path.write_text("Municipio código,Comarca código,Comarca nombre\n22001,01,A\n22001,02,B\n", encoding="utf-8")
            with self.assertRaisesRegex(InputContractError, "dos comarcas"):
                load_comarca_lookup(path)

    @unittest.skipUnless(importlib.util.find_spec("gerrychain"), "GerryChain no instalado")
    def test_real_gerrychain_recom_smoke(self):
        graph, geo = synthetic()
        data = adapt_inputs(graph, geo, comarca_enabled=True)
        out, report = run_gerrychain(
            data, contract(), total_steps=5, seed=2026, comarca_surcharge=0.3
        )
        self.assertEqual(len(out["features"]), 4)
        self.assertTrue(report["hard_constraints"]["all_pass"])
        self.assertEqual(report["run"]["states_observed"], 5)
        self.assertEqual(report["selected_metrics"]["comarca"]["population_retention"], 1)


if __name__ == "__main__":
    unittest.main()
