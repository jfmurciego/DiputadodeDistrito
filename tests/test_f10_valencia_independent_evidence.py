"""Regresión de evidencia INE 2023 valenciana; no promueve fuentes ni estados."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/AUDITORIAS/F10_CIERRE_VALENCIA_20261012/evidencia_2023.json"


class ValenciaIndependentEvidenceTests(unittest.TestCase):
    def test_independent_population_with_unobserved_sections_remains_blocked(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        population = evidence["population"]
        self.assertEqual(population["source"], "INE 65034")
        self.assertEqual(population["province_rows"], {"03": 1236, "12": 444, "46": 1823})
        self.assertEqual(sum(population["province_population"].values()), 5216195)
        self.assertEqual(population["selected_population"], 5216195)
        self.assertEqual(population["unobserved_section_count"], len(population["unobserved_section_ids"]))
        self.assertGreater(population["unobserved_section_count"], 0)
        self.assertIn("no equivale a poblacion cero", population["interpretation"])
        self.assertEqual(population["status"], "BLOCKED_INCOMPLETE_SECTION_OBSERVATIONS")
        self.assertEqual(evidence["overall_consumer_status"], "BLOCKED")

    def test_alternative_geometry_is_not_admitted_on_partial_topology_result(self):
        evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        geometry = evidence["geometry_alternative"]
        self.assertEqual(geometry["known_overlap_tests_m2"], {
            "4617201001/4619401008": 0.0,
            "4617201001/4619401013": 0.0,
        })
        self.assertEqual(geometry["features"], 2183)
        self.assertEqual(geometry["reference_sectioning_count"], 1823)
        self.assertEqual(geometry["invalid_geometry_count"], 6)
        self.assertEqual(geometry["status"], "REJECTED_AS_SUBSTITUTE_COVERAGE_AND_VALIDITY_DIFFER")
