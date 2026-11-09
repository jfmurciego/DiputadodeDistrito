"""VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ANTERIOR: ninguna (fichero nuevo)
T-115: el M05 canónico deja ceder unidades a un distrito que ya está sobre el techo (o bajo el suelo)."""
import unittest

from ddd_core import m05_opt_engine_v741 as m05

FLOOR, CAP = 157868.04, 213586.17


class BoundsMoveTests(unittest.TestCase):
    def test_over_cap_donor_may_shrink_while_still_over_cap(self):
        # congreso350_madrid, run 42522378370: el distrito 33 (303.941) cede Villaviciosa de Odón (28.714).
        self.assertTrue(m05.bounds_move_ok(303941, 303941 - 28714, FLOOR, CAP))

    def test_violation_must_strictly_decrease(self):
        self.assertFalse(m05.bounds_move_ok(303941, 303941 + 1, FLOOR, CAP))
        self.assertFalse(m05.bounds_move_ok(303941, 303941, FLOOR, CAP))
        self.assertTrue(m05.bounds_move_ok(150000, 155000, FLOOR, CAP))
        self.assertFalse(m05.bounds_move_ok(150000, 140000, FLOOR, CAP))

    def test_feasible_district_never_leaves_bounds(self):
        # Mismo comportamiento que 7.4.3 para distritos dentro de límites.
        self.assertTrue(m05.bounds_move_ok(200000, 213000, FLOOR, CAP))
        self.assertFalse(m05.bounds_move_ok(200000, 214000, FLOOR, CAP))
        self.assertFalse(m05.bounds_move_ok(160000, 157000, FLOOR, CAP))

    def test_overshoot_to_other_side_only_if_smaller(self):
        self.assertTrue(m05.bounds_move_ok(300000, 150000, FLOOR, CAP))   # 86.414 → 7.868
        self.assertFalse(m05.bounds_move_ok(220000, 100000, FLOOR, CAP))  # 6.414 → 57.868


if __name__ == "__main__":
    unittest.main()
