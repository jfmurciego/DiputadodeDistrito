"""T-107: el M05 canónico no aumenta los municipios partidos con más de un distrito mixto (R012)."""
import collections
import unittest

from ddd_core import m05_opt_engine_v741 as m05


def C(**kw):
    return collections.Counter(kw)


class MunicipalDisciplineTests(unittest.TestCase):
    def setUp(self):
        # Ávila (A) partida: distrito 0 puro de A; distrito 2 = residual de A + B (mixto); distrito 1 = C + D.
        self.units = {"a0": C(A=20), "aR": C(A=16), "aF": C(A=1), "b": C(B=3), "c": C(C=4), "d": C(D=2)}
        self.dist = {"a0": 0, "aR": 2, "aF": 2, "b": 2, "c": 1, "d": 1}

    def test_flex_unit_to_rural_district_is_rejected(self):
        disc = m05.MunicipalDiscipline(self.units, self.dist)
        self.assertEqual(disc.violations(), 0)
        self.assertTrue(disc.worsens("aF", 2, 1))
        self.assertEqual(disc.violations(), 0)  # la evaluación no altera el estado

    def test_moves_that_keep_one_mixed_district_are_allowed(self):
        disc = m05.MunicipalDiscipline(self.units, self.dist)
        self.assertFalse(disc.worsens("b", 2, 1))  # el residual queda puro de A
        disc.apply("b", 2, 1)
        self.assertFalse(disc.worsens("aF", 2, 1))  # sigue habiendo un solo mixto (1)
        disc.apply("aF", 2, 1)
        self.assertEqual(disc.violations(), 0)

    def test_field_follows_validation(self):
        cfg = {"validation": {"require_municipality_discipline": True, "municipality_field": "CUMUN"}}
        self.assertEqual(m05.municipality_discipline_field(cfg, {}, ["CUSEC", "CUMUN"], "CUSEC"), "CUMUN")
        self.assertEqual(m05.municipality_discipline_field(cfg, {}, ["CUSEC"], "CUSEC"), "CUSEC")
        self.assertIsNone(m05.municipality_discipline_field({"validation": {}}, {}, ["CUMUN"], "CUSEC"))


if __name__ == "__main__":
    unittest.main()
