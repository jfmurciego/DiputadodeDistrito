import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from connectivity_cut import rooted_cut_terms


def lhs(terms, values):
    return sum(coef * values[var] for var, coef in terms.items())


class RootedConnectivityCutTests(unittest.TestCase):
    def setUp(self):
        self.x = {'A': 'xA', 'B': 'xB', 'C': 'xC'}
        self.r = {'A': 'rA', 'B': 'rB', 'C': 'rC'}

    def test_disconnected_nonroot_component_is_cut(self):
        # Chain A-B-C; district d has A and C, root A, B is outside d.
        terms, upper = rooted_cut_terms(['C'], ['B'], self.x, self.r)
        values = {'xA': 1, 'xB': 0, 'xC': 1, 'rA': 1, 'rB': 0, 'rC': 0}
        self.assertGreater(lhs(terms, values), upper)

    def test_connected_district_equal_to_component_remains_admissible(self):
        # The unrooted cut would wrongly reject this valid singleton district.
        terms, upper = rooted_cut_terms(['C'], ['B'], self.x, self.r)
        values = {'xA': 0, 'xB': 0, 'xC': 1, 'rA': 0, 'rB': 0, 'rC': 1}
        self.assertLessEqual(lhs(terms, values), upper)

    def test_component_joined_to_assigned_boundary_is_not_cut(self):
        terms, upper = rooted_cut_terms(['C'], ['B'], self.x, self.r)
        values = {'xA': 0, 'xB': 1, 'xC': 1, 'rA': 0, 'rB': 1, 'rC': 0}
        self.assertLessEqual(lhs(terms, values), upper)


if __name__ == '__main__':
    unittest.main()
