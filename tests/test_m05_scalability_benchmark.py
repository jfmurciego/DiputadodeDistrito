import unittest

from herramientas.benchmark_m05_escalabilidad_sintetico import fixture_summary


class M05ScalabilityFixtureTests(unittest.TestCase):
    def test_chain_fixture_has_deterministic_size_and_no_geographic_identity(self):
        assignments, units, adjacency, edges = fixture_summary(40, block_size=10)
        self.assertEqual(len(units), 40)
        self.assertEqual(edges, 39)
        self.assertEqual(len(set(assignments.values())), 4)
        self.assertEqual(sum(len(v) for v in adjacency.values()), 2 * edges)
        self.assertTrue(all(unit.startswith("u") for unit in units))
        self.assertTrue(all(row["province"] == "SYNTHETIC" for row in units.values()))
        self.assertEqual(
            [sum(1 for district in assignments.values() if district == d)
             for d in sorted(set(assignments.values()))],
            [10, 10, 10, 10],
        )

    def test_fixture_rejects_nonintegral_partition_sizes(self):
        with self.assertRaises(ValueError):
            fixture_summary(41, block_size=10)


if __name__ == "__main__":
    unittest.main()
