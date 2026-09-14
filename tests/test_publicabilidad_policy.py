#!/usr/bin/env python3
"""Pruebas Paquete B v1.0.0: evidencia y clasificación de publicabilidad."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "resultados/fase1/EVIDENCIA_PUBLICABILIDAD.json"
REGISTRY = ROOT / "orchestracion/productos_publicos.json"


class PublicationPolicy(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    def test_defines_nine_criteria_and_no_publicable_map(self):
        self.assertEqual(len(self.evidence["criteria"]), 9)
        self.assertEqual(self.evidence["decision"]["publicable_maps"], 0)

    def test_shape_statistics_recompute_from_existing_catalogues(self):
        for territory, record in self.evidence["territories"].items():
            frame = pd.read_csv(ROOT / record["source"])
            field = "compactness_polsby_popper" if territory == "aragon" else "polsby_popper"
            compactness = frame[field].astype(float)
            expected = record["polsby_popper"]
            self.assertEqual(len(frame), record["districts"])
            self.assertAlmostEqual(compactness.min(), expected["min"], places=11)
            self.assertAlmostEqual(compactness.median(), expected["median"], places=11)
            self.assertEqual(int((compactness < 0.15).sum()), expected["below_0_15"])

    def test_c03_direction_is_not_misstated(self):
        record = self.evidence["territories"]["castilla_y_leon"]
        frame = pd.read_csv(ROOT / record["source"])
        correlation = frame["relative_deviation"].abs().corr(frame["polsby_popper"])
        self.assertAlmostEqual(correlation, record["pearson_abs_population_deviation_vs_shape"], places=11)
        quartiles = record["population_deviation_quartiles"]
        self.assertGreater(quartiles[0]["mean_polsby_popper"], quartiles[-1]["mean_polsby_popper"])
        self.assertEqual(record["c03_causal_claim"], "NOT_SUPPORTED_BY_OBSERVED_CORRELATION")

    def test_public_registry_labels_every_product_as_blocked_preview(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(registry["registry_role"], "technical_preview_distribution")
        for product in registry["products"]:
            self.assertEqual(product["technical_status"], "PASS")
            self.assertEqual(product["publication_status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
