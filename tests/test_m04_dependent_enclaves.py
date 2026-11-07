"""T-44: el residual de un municipio dividido debe caber con sus enclaves dependientes (Elche + Santa Pola)."""
import unittest
from unittest import mock

from ddd_core import m04_seed_engine as m04

ADJ = {
    "a1": {"a2", "e"}, "a2": {"a1", "a3"}, "a3": {"a2", "f"},
    "e": {"a1"}, "f": {"a3", "g"}, "g": {"f"},
}
MUN = ({"a1": "A", "a2": "A", "a3": "A", "e": "E", "f": "F", "g": "G"},
       {"A": {"a1", "a2", "a3"}, "E": {"e"}, "F": {"f"}, "G": {"g"}})
W = {"a1": 60, "a2": 100, "a3": 40, "e": 30, "f": 10, "g": 10}


class DependentEnclaves(unittest.TestCase):
    def test_only_enclaves_bordering_just_the_municipality_count(self):
        self.assertEqual(m04._dependent_enclave_population({"a1", "a2", "a3"}, ADJ, W, MUN), 30)

    def test_extra_core_when_residual_plus_enclave_exceeds_cap(self):
        base = ([{"a2"}], {"a1", "a3"}, "global_q_partition", {"a1", "a3"})
        # rojo: residual 100 + enclave 30 > techo 100
        candidate = ([{"a2"}, {"a3"}], {"a1"}, "sequential_core_residual")
        with mock.patch.object(m04.core.previous, "_sequential_count",
                               return_value=(candidate, "")) as seq:
            closed, residual, mode, _ = m04._with_dependent_enclaves(
                base, {"a1", "a2", "a3"}, 100, 50, 100, ADJ, W, set(), MUN)
        self.assertEqual(seq.call_args.args[1], 2)  # un núcleo más
        self.assertEqual(len(closed), 2)
        self.assertIn("dependent_enclaves:30", mode)

    def test_unchanged_when_residual_and_enclaves_fit(self):
        base = ([{"a2"}], {"a1", "a3"}, "global_q_partition", {"a1", "a3"})
        with mock.patch.object(m04.core.previous, "_sequential_count") as seq:
            result = m04._with_dependent_enclaves(base, {"a1", "a2", "a3"}, 100, 50, 130, ADJ, W, set(), MUN)
        seq.assert_not_called()
        self.assertIs(result, base)


if __name__ == "__main__":
    unittest.main()
