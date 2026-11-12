"""Versión 1.0.0; 2026-11-02; candidato. T-33: Salamanca une las piezas de una sección MultiPolygon como M06 (ATOMIC_MULTIPART)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from ddd_core.m05_gerrychain_engine import Contract, adapt_inputs, hard_constraint_violations

ROOT = Path(__file__).resolve().parents[1]
FIELDS = dict(section_field="CUSEC_KEY", district_field="district_id", municipality_field="CUMUN",
              province_field="CPRO", population_field="POP_2023")


def ring(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]


def feature(key, geometry, district):
    return {"type": "Feature", "geometry": geometry,
            "properties": {"CUSEC_KEY": key, "district_id": district, "CUMUN": key[:5], "CPRO": "37",
                           "POP_2023": 100, "ddd_unit_id": key, "ddd_closed_urban": False}}


def poly(*args):
    return {"type": "Polygon", "coordinates": [ring(*args)]}


def inputs():
    # Distrito 1 = M (MultiPolygon: pieza izquierda y pieza derecha separadas) + B; la pieza derecha de M solo toca
    # secciones del distrito 2. Es el caso de un exclave rural dentro de otro distrito.
    m = {"type": "MultiPolygon", "coordinates": [[ring(0, 0, 10, 10)], [ring(30, 0, 40, 10)]]}
    features = [feature("3700101001", m, 1), feature("3700201001", poly(10, 0, 20, 10), 1),
                feature("3700301001", poly(20, 0, 30, 10), 2), feature("3700401001", poly(20, 10, 30, 20), 2)]
    geo = {"type": "FeatureCollection", "features": features}
    edges = [("3700101001", "3700201001"), ("3700201001", "3700301001"), ("3700301001", "3700101001"),
             ("3700301001", "3700401001")]
    graph = {"nodes": [{"id": f["properties"]["CUSEC_KEY"], "pop": 100} for f in features],
             "edges": [{"u": u, "v": v} for u, v in edges]}
    return graph, geo


CONTRACT = Contract(k=2, target_tolerance_ratio=0.5, population_floor_ratio=0.1, population_cap_ratio=5.0,
                    municipality_atomicity_limit_ratio=5.0, require_single_province=True,
                    require_municipality_discipline=False, preserve_closed_urban=False)


class MultipartSalamancaTests(unittest.TestCase):
    def violations(self, preserve):
        graph, geo = inputs()
        data = adapt_inputs(graph, geo, preserve_atomic_multipart_sections=preserve, **FIELDS)
        assignment = {f["properties"]["CUSEC_KEY"]: f["properties"]["district_id"] for f in geo["features"]}
        return hard_constraint_violations(data, assignment, CONTRACT)

    def test_rojo_sin_la_opcion_la_pieza_suelta_rompe_la_contigüidad_geométrica(self):
        self.assertIn("geometric_contiguity:1", self.violations(False))

    def test_verde_con_la_opcion_las_piezas_de_la_misma_seccion_se_unen(self):
        self.assertNotIn("geometric_contiguity:1", self.violations(True))
        self.assertEqual([v for v in self.violations(True) if v.startswith("geometric_contiguity")], [])

    def test_salamanca_tiene_la_opcion_activada(self):
        cfg = json.loads((ROOT / "configuracion/ensemble/nac37.json").read_text(encoding="utf-8"))
        self.assertIs(cfg["topology"]["preserve_atomic_multipart_sections"], True)
        aragon = json.loads((ROOT / "configuracion/ensemble/aut02.json").read_text(encoding="utf-8"))
        self.assertIs(aragon["topology"]["preserve_atomic_multipart_sections"], True)


if __name__ == "__main__":
    unittest.main()
