# PROYECTO: Diputado de Distrito
# PRUEBA: Aragón 2025 - admisibilidad geométrica ligada al consumidor M02
# FECHA: 2026-10-11
# ORIGEN: run 38086465532, artefacto de diagnóstico 11683685832
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

import yaml
from shapely.geometry import Polygon, box

from ddd_core.official_geometry import _source_admissibility

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "territorios/aragon/config/aragon_2025.yaml"
LEGACY = ROOT / "legacy/configuracion/aragon_2025_v7.14.0.yaml"
M02 = runpy.run_path(str(ROOT / "modulos/02_construir_adyacencias.py"))["_relation_ok"]


def _wedge(overlap_m: float):
    """Dos secciones con ocho metros de frontera y una cuña submétrica."""
    left = box(0, 0, 10, 10)
    right = Polygon([
        (10, 0), (20, 0), (20, 10), (10, 10),
        (10, 6), (10 - overlap_m, 5), (10, 4), (10, 0)
    ])
    assert left.is_valid and right.is_valid
    return left, right


def _source_decision(left, right, *, threshold: float, predicate: str = "contact"):
    pairwise = {
        "overlap_change_count": 0,
        "contact_change_count": 0,
        "unresolved_baseline_count": 0,
        "overlaps": [{
            "section_a": "A", "section_b": "B",
            "classification": "PRESERVED",
            "after": {"geometry_sha256": "unchanged-official-source"},
        }],
    }
    return _source_admissibility(
        pairwise,
        declared_use={
            "role": "target_sectioning",
            "consumer": "modulo_02_construir_adyacencias",
            "adjacency": {
                "predicate": predicate,
                "working_crs": "EPSG:25830",
                "min_shared_border_m": 1.0,
                "max_precision_overlap_area_m2": threshold,
            },
        },
        section_ids=["A", "B"],
        derived_geometries=[left, right],
        source_crs="EPSG:25830",
    )


class AragonPrecisionContactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
        cls.m02 = cls.cfg["modulos"]["modulo_02_construir_adyacencias"]

    def test_policy_is_narrow_explicit_and_versioned(self):
        self.assertEqual(self.cfg["meta"]["schema_version"], "7.15.0")
        self.assertEqual(self.m02["predicate"], "contact")
        self.assertEqual(float(self.m02["min_shared_border_m"]), 1.0)
        self.assertEqual(float(self.m02["max_precision_overlap_area_m2"]), 0.025)
        self.assertEqual(float(self.m02["buffer_m"]), 0.0)
        self.assertEqual(float(self.m02["simplify_m"]), 0.0)
        historical = yaml.safe_load(LEGACY.read_text(encoding="utf-8"))
        self.assertEqual(historical["meta"]["schema_version"], "7.14.0")
        self.assertEqual(historical["modulos"]["modulo_02_construir_adyacencias"]["predicate"], "touches")
        self.assertNotIn(
            "max_precision_overlap_area_m2",
            historical["modulos"]["modulo_02_construir_adyacencias"],
        )

    def test_genuine_border_remains_an_edge(self):
        left, right = box(0, 0, 10, 10), box(10, 0, 20, 10)
        self.assertTrue(left.touches(right))
        self.assertTrue(M02(left, right, "contact", 1, 0.025))

    def test_official_scale_wedge_is_accepted_by_same_m02_predicate(self):
        left, right = _wedge(0.001)
        self.assertFalse(left.touches(right))
        self.assertAlmostEqual(left.intersection(right).area, 0.001)
        self.assertAlmostEqual(left.boundary.intersection(right.boundary).length, 8)
        self.assertTrue(M02(left, right, "contact", 1, 0.025))
        result = _source_decision(left, right, threshold=0.025)
        self.assertEqual(result["decision"], "READY")
        pair = result["original_overlap_pairs"][0]
        self.assertEqual(pair["adjacency_effect"], "GEOMETRIC_EDGE")
        self.assertTrue(pair["admissible"])

    def test_old_touches_contract_does_not_create_an_overlap_edge(self):
        left, right = _wedge(0.001)
        self.assertFalse(M02(left, right, "touches", 1, 0.025))
        result = _source_decision(left, right, threshold=0.025, predicate="touches")
        self.assertEqual(result["decision"], "BLOCKED")

    def test_larger_overlap_blocks_both_consumer_and_source(self):
        left, right = _wedge(0.05)
        self.assertAlmostEqual(left.intersection(right).area, 0.05)
        self.assertFalse(M02(left, right, "contact", 1, 0.025))
        result = _source_decision(left, right, threshold=0.025)
        self.assertEqual(result["decision"], "BLOCKED")
        self.assertEqual(len(result["inadmissible_overlap_pairs"]), 1)

    def test_point_contact_never_creates_an_edge(self):
        left, right = box(0, 0, 10, 10), box(10, 10, 20, 20)
        self.assertTrue(left.touches(right))
        self.assertEqual(left.boundary.intersection(right.boundary).length, 0.0)
        self.assertFalse(M02(left, right, "contact", 1, 0.025))
        result = _source_decision(left, right, threshold=0.025)
        self.assertEqual(result["decision"], "READY")
        self.assertEqual(
            result["original_overlap_pairs"][0]["adjacency_effect"],
            "NO_EDGE_UNDER_DECLARED_CONSUMER",
        )


if __name__ == "__main__":
    unittest.main()
