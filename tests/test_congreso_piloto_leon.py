"""Regresión del modo opt-in de asignaciones; nunca habilita generación."""
import unittest

from ddd_core.congreso_bounded_tree_search import search_tree_partition
from herramientas.preparar_visor_congreso_leon import strict_json_loads


class CongressLeonPilotTests(unittest.TestCase):
    def test_viewer_input_rejects_duplicate_json_keys_and_nonfinite_values(self):
        with self.assertRaisesRegex(ValueError, "JSON_DUPLICATE_KEY"):
            strict_json_loads('{"cpro":"24","cpro":"10"}')
        with self.assertRaisesRegex(ValueError, "JSON_NONFINITE_VALUE"):
            strict_json_loads('{"population":NaN}')

    def test_pilot_workflow_isolated_from_publication_and_pages(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        workflow = (root / ".github/workflows/congreso-piloto-leon.yml").read_text(encoding="utf-8")
        self.assertNotIn("pages: write", workflow)
        self.assertNotIn("deploy-pages", workflow)
        self.assertNotIn("_reutilizable-publicar-sitio", workflow)
        self.assertIn("actions/upload-artifact", workflow)
        self.assertNotIn("visor/index.html", workflow)
        self.assertNotIn("visor/styles.css", workflow)
        self.assertIn('if cpro == "24":', workflow)
        self.assertIn("CACERES: diagnostic only", workflow)
        self.assertIn('report.get("product_certification") != "NOT_PERFORMED"', workflow)


    def test_opt_in_assignments_are_valid_and_digest_unchanged(self):
        nodes = ["a", "b", "c", "d"]
        adjacency = {"a": {"b"}, "b": {"a", "c"}, "c": {"b", "d"}, "d": {"c"}}
        weights = dict.fromkeys(nodes, 40)
        base = search_tree_partition(nodes, adjacency, weights, k=2, floor=80, cap=80)
        pilot = search_tree_partition(nodes, adjacency, weights, k=2, floor=80,
                                      cap=80, return_groups=True)
        self.assertEqual(base.status, "TREE_WITNESS_FOUND_CONDITIONAL")
        self.assertEqual(base.witness_sha256, pilot.witness_sha256)
        self.assertEqual(base.input_sha256, pilot.input_sha256)
        self.assertEqual(base.groups, ())
        self.assertEqual(len(pilot.groups), 2)
        self.assertEqual(sorted(x for g in pilot.groups for x in g), sorted(nodes))
        self.assertEqual([sum(weights[n] for n in g) for g in pilot.groups], [80, 80])

    def test_failed_search_cannot_emit_assignments(self):
        nodes = ["a", "b"]
        result = search_tree_partition(nodes, {"a": set(), "b": set()},
                                       {"a": 50, "b": 50}, k=1, floor=100, cap=100,
                                       return_groups=True)
        self.assertNotEqual(result.status, "TREE_WITNESS_FOUND_CONDITIONAL")
        self.assertEqual(result.groups, ())

    def test_return_groups_flag_must_be_boolean(self):
        with self.assertRaisesRegex(ValueError, "RETURN_GROUPS_MUST_BE_BOOLEAN"):
            search_tree_partition(["a"], {"a": set()}, {"a": 1},
                                  k=1, floor=1, cap=1, return_groups="yes")


if __name__ == "__main__":
    unittest.main()
