from __future__ import annotations

import unittest

from shapely.geometry import box

from herramientas.compatibilidad_poblacion_seccionado import reconcile_population_sectioning


def reconcile(population_rows, target_rows, origin_rows=None, *, population_year=2025, section_year=2025):
    return reconcile_population_sectioning(
        territory_id="demo",
        edition="2025",
        population_year=population_year,
        section_year=section_year,
        population_rows=population_rows,
        target_geometry_rows=target_rows,
        origin_geometry_rows=origin_rows,
        input_identities={
            "population": {"path": "population.zip", "sha256": "a" * 64},
            "target_sectioning": {"path": "target.zip", "sha256": "b" * 64},
            "origin_sectioning": (
                {"path": "origin.zip", "sha256": "c" * 64} if origin_rows is not None else None
            ),
        },
    )


class PopulationSectioningCompatibilityTests(unittest.TestCase):
    def test_valid_cross_year_correspondence_requires_geometric_equality(self):
        geom = box(0, 0, 1, 1)
        report = reconcile(
            [("0100101001", 100)],
            [("0100101999", geom)],
            [("0100101001", geom)],
            population_year=2024,
            section_year=2025,
        )
        self.assertEqual(report["decision"], "READY")
        self.assertEqual(report["population"]["input_total"], 100)
        self.assertEqual(report["population"]["assigned_total"], 100)
        self.assertTrue(report["population"]["exact_conservation"])
        self.assertEqual(report["correspondences"][0]["kind"], "ONE_TO_ONE_CODE_CHANGE")

    def test_same_code_with_changed_boundaries_is_blocked(self):
        report = reconcile(
            [("0100101001", 100)],
            [("0100101001", box(0, 0, 2, 1))],
            [("0100101001", box(0, 0, 1, 1))],
            population_year=2024,
            section_year=2025,
        )
        self.assertEqual(report["decision"], "BLOCKED")
        self.assertIn("SAME_CODE_BOUNDARY_CHANGED", report["causes"])

    def test_disappearance_and_addition_without_geometric_correspondence_block(self):
        report = reconcile(
            [("0100101001", 100)],
            [("0100102001", box(10, 10, 11, 11))],
            [("0100101001", box(0, 0, 1, 1))],
            population_year=2024,
            section_year=2025,
        )
        self.assertIn("UNACCREDITED_SECTIONING_CHANGE", report["causes"])
        self.assertIn("POPULATION_WITHOUT_DESTINATION", report["causes"])

    def test_split_is_detected_geometrically_but_never_used_to_redistribute_population(self):
        report = reconcile(
            [("0100101001", 100)],
            [
                ("0100102001", box(0, 0, 0.5, 1)),
                ("0100102002", box(0.5, 0, 1, 1)),
            ],
            [("0100101001", box(0, 0, 1, 1))],
            population_year=2024,
            section_year=2025,
        )
        self.assertIn("NON_BIJECTIVE_GEOMETRIC_CORRESPONDENCE", report["causes"])
        self.assertTrue(any(x["kind"] == "SPLIT" for x in report["correspondences"]))
        self.assertEqual(report["population"]["assigned_total"], 0)

    def test_fusion_is_detected_geometrically_but_remains_blocked(self):
        report = reconcile(
            [("0100101001", 40), ("0100101002", 60)],
            [("0100102001", box(0, 0, 1, 1))],
            [
                ("0100101001", box(0, 0, 0.5, 1)),
                ("0100101002", box(0.5, 0, 1, 1)),
            ],
            population_year=2024,
            section_year=2025,
        )
        self.assertIn("NON_BIJECTIVE_GEOMETRIC_CORRESPONDENCE", report["causes"])
        self.assertTrue(any(x["kind"] == "FUSION" for x in report["correspondences"]))

    def test_duplicate_population_key_blocks_before_any_overwrite(self):
        geom = box(0, 0, 1, 1)
        report = reconcile(
            [("0100101001", 40), ("0100101001", 60)],
            [("0100101001", geom)],
        )
        self.assertIn("DUPLICATE_POPULATION_KEYS", report["causes"])

    def test_duplicate_geometry_key_blocks(self):
        geom = box(0, 0, 1, 1)
        report = reconcile(
            [("0100101001", 100)],
            [("0100101001", geom), ("0100101001", geom)],
        )
        self.assertIn("DUPLICATE_TARGET_GEOMETRY_KEYS", report["causes"])

    def test_population_without_destination_and_geometry_without_population_block(self):
        report = reconcile(
            [("0100101001", 100)],
            [
                ("0100101001", box(0, 0, 1, 1)),
                ("0100101002", box(1, 0, 2, 1)),
            ],
        )
        self.assertIn("GEOMETRY_WITHOUT_POPULATION", report["causes"])
        self.assertIn("TARGET_GEOMETRY_WITHOUT_POPULATION", report["causes"])

    def test_exact_total_conservation_is_mandatory(self):
        report = reconcile(
            [("0100101001", 100), ("0100101002", 50)],
            [("0100101001", box(0, 0, 1, 1))],
        )
        self.assertFalse(report["population"]["exact_conservation"])
        self.assertEqual(report["population"]["input_total"], 150)
        self.assertEqual(report["population"]["assigned_total"], 100)
        self.assertIn("POPULATION_TOTAL_NOT_CONSERVED", report["causes"])


if __name__ == "__main__":
    unittest.main()
