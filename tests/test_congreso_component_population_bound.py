"""National N08 necessary district budgets from connected section components.

These checks reject impossible strict partitions but cannot accredit exceptions,
a viable territorial assignment, or production authorisation.
"""
import unittest
from ddd_core.congreso_preflight_adapter import structural_component_bound

CASES = (
    # (CPRO, K, component populations, exact N08 floor and cap)
    ("07", 10, [971068, 102821, 11690, 164265], 106237, 143732),
    ("09", 3, [360447, 2034, 144, 38], 102755, 139020),
    ("17", 7, [828857, 1572], 100838, 136427),
    ("34", 1, [158557, 45, 100], 134897, 182507),
    ("36", 8, [943005, 4813], 100706, 136248),
)

class N08ConnectedPopulationBudgetTests(unittest.TestCase):
    def test_all_five_original_graph_provinces_fail_necessary_condition(self):
        for cpro, k, populations, floor, cap in CASES:
            with self.subTest(CPRO=cpro):
                result = structural_component_bound(populations, k, floor=floor, cap=cap)
                self.assertFalse(result["necessary_condition"])
                self.assertFalse(result["feasibility_proven"])
                self.assertNotEqual(result["reason"], "NO_IMPOSSIBILITY_FROM_COMPONENT_COUNT_OR_POPULATION")
                self.assertEqual(result["minimum_districts_total"], sum(result["minimum_districts_by_component"]))

    def test_connected_component_budget_can_pass_without_claiming_feasibility(self):
        result = structural_component_bound([770554], 6, floor=109162, cap=147689)
        self.assertTrue(result["necessary_condition"])
        self.assertFalse(result["feasibility_proven"])
        self.assertEqual(result["reason"], "NO_IMPOSSIBILITY_FROM_COMPONENT_COUNT_OR_POPULATION")

    def test_population_gap_between_one_cap_and_two_floors(self):
        # Ibizan component cannot form one in-cap or two above-floor districts.
        result = structural_component_bound([164265], 2, floor=106237, cap=143732)
        self.assertFalse(result["necessary_condition"])
        self.assertEqual(result["minimum_districts_by_component"], [2])
        self.assertEqual(result["maximum_districts_by_component"], [1])

    def test_aggregate_group_budget_can_fail_even_if_each_component_is_viable(self):
        result = structural_component_bound([100, 100], 3, floor=100, cap=200)
        self.assertEqual(result["reason"], "COMPONENT_MAXIMUM_DISTRICT_BUDGET_BELOW_K")
        self.assertFalse(result["necessary_condition"])

    def test_legacy_count_only_callers_remain_count_only(self):
        self.assertTrue(structural_component_bound([770554], 6)["necessary_condition"])
        self.assertFalse(structural_component_bound([100, 100], 1)["necessary_condition"])

    def test_generator_population_input_preserves_component_count(self):
        result = structural_component_bound((p for p in (100, 100)), 1)
        self.assertFalse(result["necessary_condition"])
        result = structural_component_bound((p for p in (100,)), 1, floor=90, cap=120)
        self.assertTrue(result["necessary_condition"])

    def test_invalid_budget_is_rejected(self):
        for kwargs in ({"floor": 0, "cap": 100},
                       {"floor": 200, "cap": 100},
                       {"floor": 100}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(ValueError, "COMPONENT_POPULATION_BOUNDS_INVALID"):
                    structural_component_bound([100], 1, **kwargs)

if __name__ == "__main__":
    unittest.main()
