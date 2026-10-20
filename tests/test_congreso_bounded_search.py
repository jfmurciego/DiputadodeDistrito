import unittest

from herramientas.diagnosticar_factibilidad_congreso_k_multiple import diagnose_graph


class BoundedSearchTests(unittest.TestCase):
    def test_tree_fallback_finds_conditional_witness_without_emitting_partition(self):
        nodes = ["a", "b", "c", "d"]
        adjacency = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c"}}
        result = diagnose_graph(nodes, adjacency, {node: 40 for node in nodes},
                                k=2, floor=80, cap=80, physical_part_components=1,
                                max_extra_groups=100, max_states=1)
        self.assertEqual("TREE_WITNESS_FOUND_CONDITIONAL", result["status"])
        self.assertEqual("SEARCH_EXHAUSTED", result["solver_status"])
        self.assertEqual("TREE_WITNESS_FOUND_CONDITIONAL", result["tree_search"]["status"])
        self.assertIsNotNone(result["witness_sha256"])
        self.assertFalse(result["partition_emitted"])
        self.assertNotIn("groups", result)

    def test_tree_search_exhaustion_never_becomes_infeasibility(self):
        nodes = [str(i) for i in range(8)]
        adjacency = {n: set() for n in nodes}
        for i in range(7):
            adjacency[str(i)].add(str(i + 1)); adjacency[str(i + 1)].add(str(i))
        result = diagnose_graph(nodes, adjacency, {node: 1 for node in nodes},
                                k=2, floor=4, cap=4, physical_part_components=1,
                                max_extra_groups=100, max_states=1,
                                tree_max_states=1, tree_max_transitions=1)
        self.assertEqual("SEARCH_EXHAUSTED", result["status"])
        self.assertEqual("SEARCH_EXHAUSTED", result["tree_search"]["status"])
        self.assertFalse(result["search_exhaustive"])
        self.assertFalse(result["partition_emitted"])

    def test_part_component_bound_blocks_search_conditionally(self):
        nodes = ["a", "b"]
        adjacency = {"a": set(), "b": set()}
        result = diagnose_graph(nodes, adjacency, {"a": 50, "b": 50},
                                k=2, floor=50, cap=50, physical_part_components=3)
        self.assertEqual("NECESSARY_CONDITION_FAILED_CONDITIONAL", result["status"])
        self.assertIsNone(result["input_sha256"])
        self.assertFalse(result["partition_emitted"])

    def test_k_one_is_rejected_as_wrong_diagnostic_scope(self):
        with self.assertRaisesRegex(ValueError, "K_MULTIPLE_REQUIRED"):
            diagnose_graph(["a"], {"a": set()}, {"a": 100}, k=1,
                           floor=100, cap=100, physical_part_components=1)

    def test_multiple_declared_forest_orders_are_recorded_without_partition(self):
        nodes = ["a", "b", "c", "d"]
        adjacency = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c"}}
        result = diagnose_graph(nodes, adjacency, {node: 40 for node in nodes},
                                k=2, floor=80, cap=80, physical_part_components=1,
                                max_extra_groups=100, max_states=1,
                                forest_orderings=("cusec", "degree_desc"))
        self.assertEqual("TREE_WITNESS_FOUND_CONDITIONAL", result["status"])
        self.assertEqual(["cusec"],
                         [row["ordering"] for row in result["tree_search_attempts"]])
        self.assertFalse(result["partition_emitted"])
        self.assertNotIn("groups", result)
        self.assertEqual(result["input_sha256"],
                         result["tree_search_attempts"][0]["input_sha256"])
        self.assertRegex(result["tree_search_attempts"][0]["node_order_sha256"],
                         r"^[0-9a-f]{64}$")

    def test_unknown_forest_order_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "FOREST_ORDERINGS_INVALID"):
            diagnose_graph(["a", "b"], {"a": {"b"}, "b": {"a"}},
                           {"a": 1, "b": 1}, k=2, floor=1, cap=1,
                           physical_part_components=1,
                           forest_orderings=("custom-unreviewed-order",))
        with self.assertRaisesRegex(ValueError, "FOREST_ORDERINGS_INVALID"):
            diagnose_graph(["a", "b"], {"a": {"b"}, "b": {"a"}},
                           {"a": 1, "b": 1}, k=2, floor=1, cap=1,
                           physical_part_components=1, forest_orderings=(["unhashable"],))


if __name__ == "__main__":
    unittest.main()
