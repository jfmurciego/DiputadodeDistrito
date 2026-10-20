import unittest

from ddd_core.congreso_bounded_tree_search import search_tree_partition


class BoundedTreeSearchTests(unittest.TestCase):
    def test_path_population_witness_returns_digest_without_partition(self):
        nodes = ["a", "b", "c", "d"]
        graph = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c"}}
        result = search_tree_partition(nodes, graph, {n: 40 for n in nodes},
                                       k=2, floor=80, cap=80)
        self.assertEqual("TREE_WITNESS_FOUND_CONDITIONAL", result.status)
        self.assertIsNotNone(result.witness_sha256)
        self.assertNotIn("groups", result.__dict__)
        self.assertEqual(result, search_tree_partition(nodes, graph, {n: 40 for n in nodes},
                                                        k=2, floor=80, cap=80))

    def test_disconnected_components_are_never_artificially_joined(self):
        nodes = ["a", "b", "c", "d"]
        graph = {"a": {"b"}, "b": {"a"}, "c": {"d"}, "d": {"c"}}
        result = search_tree_partition(nodes, graph, {n: 40 for n in nodes},
                                       k=1, floor=160, cap=160)
        self.assertEqual("TREE_WITNESS_NOT_FOUND", result.status)
        self.assertEqual(2, result.spanning_forest_components)
        self.assertIsNone(result.witness_sha256)

    def test_independent_components_can_each_form_a_district_without_a_bridge(self):
        nodes = ["a", "b", "c", "d"]
        graph = {"a": {"b"}, "b": {"a"}, "c": {"d"}, "d": {"c"}}
        result = search_tree_partition(nodes, graph, {n: 40 for n in nodes},
                                       k=2, floor=80, cap=80)
        self.assertEqual("TREE_WITNESS_FOUND_CONDITIONAL", result.status)
        self.assertEqual(2, result.spanning_forest_components)
        self.assertIsNotNone(result.witness_sha256)

    def test_budget_exhaustion_is_not_infeasibility(self):
        nodes = [str(i) for i in range(8)]
        graph = {n: set() for n in nodes}
        for i in range(7):
            graph[str(i)].add(str(i + 1)); graph[str(i + 1)].add(str(i))
        result = search_tree_partition(nodes, graph, {n: 1 for n in nodes},
                                       k=2, floor=4, cap=4, max_states=1)
        self.assertEqual("SEARCH_EXHAUSTED", result.status)
        self.assertNotEqual("PROVEN_INFEASIBLE", result.status)

    def test_boolean_population_rejected(self):
        with self.assertRaisesRegex(ValueError, "WEIGHTS_INVALID"):
            search_tree_partition(["a"], {"a": set()}, {"a": True},
                                  k=1, floor=0, cap=1)

    def test_unhashable_node_rejected_as_input_error(self):
        with self.assertRaisesRegex(ValueError, "NODES_INVALID"):
            search_tree_partition([[]], {"unused": set()}, {}, k=1, floor=0, cap=1)


if __name__ == "__main__":
    unittest.main()
