"""Versión 1.0.0; 2026-11-02; candidato. T-29: aristas por esquina fuera del grafo de ReCom sin relajar el motor."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ddd_core.m05_gerrychain_engine import InputContractError, adapt_inputs
from ddd_ensemble.graph_preparation import GraphPreparationError, prune_weak_adjacencies
from ddd_ensemble.runner import adapt

FIELDS = dict(section_field="CUSEC_KEY", district_field="district_id", municipality_field="CUMUN",
              province_field="CPRO", population_field="POP_2023", min_shared_border_m=1.0)


def square(key, x0, y0, x1, y1, district):
    ring = [[x0, y0], [x1, y0], [x1, y1], [x0, y1], [x0, y0]]
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]},
            "properties": {"CUSEC_KEY": key, "district_id": district, "CUMUN": key[:5], "CPRO": "37",
                           "POP_2023": 100, "ddd_unit_id": key, "ddd_closed_urban": False}}


def case(connected_without_weak=True):
    # A-B comparten 10 m, B-C 10 m; D toca B por una esquina de 0,04 m (como 3700101001–3706801001) y,
    # si connected_without_weak, comparte 10 m con C.
    feats = [square("3700101001", 0, 0, 10, 10, 1), square("3700201001", 10, 0, 20, 10, 1),
             square("3700301001", 20, 0, 30, 10, 2)]
    if connected_without_weak:
        feats.append(square("3706801001", 19.96, 10, 30, 20, 2))
        edges = [("3700101001", "3700201001"), ("3700201001", "3700301001"),
                 ("3700301001", "3706801001"), ("3700201001", "3706801001")]
    else:
        feats = feats[:2] + [square("3706801001", 19.96, 10, 29, 20, 2)]
        edges = [("3700101001", "3700201001"), ("3700201001", "3706801001")]
    geo = {"type": "FeatureCollection", "features": feats}
    graph = {"nodes": [{"id": f["properties"]["CUSEC_KEY"], "pop": 100} for f in feats],
             "edges": [{"u": u, "v": v} for u, v in edges]}
    return graph, geo


class AristasDebilesTests(unittest.TestCase):
    def test_rojo_el_motor_sigue_rechazando_la_arista_de_esquina(self):
        graph, geo = case()
        with self.assertRaisesRegex(InputContractError, "Arista sin frontera métrica suficiente"):
            adapt_inputs(graph, geo, **FIELDS)

    def test_verde_se_descarta_la_arista_informada_y_el_grafo_sigue_conexo(self):
        graph, geo = case()
        prepared, report = prune_weak_adjacencies(graph, geo, 1.0)
        self.assertEqual(report["edges_pruned"], 1)
        self.assertEqual(report["pruned"][0]["edge"], ["3700201001", "3706801001"])
        self.assertLess(report["pruned"][0]["shared_border_m"], 1.0)
        self.assertTrue(report["connected_preserved"])
        self.assertEqual(len(prepared["edges"]), 3)
        data = adapt_inputs(prepared, geo, **FIELDS)  # el contrato del motor no se relajó
        self.assertEqual(len(data.edges), 3)

    def test_si_deja_de_ser_conexo_se_detiene(self):
        graph, geo = case(connected_without_weak=False)
        with self.assertRaisesRegex(GraphPreparationError, "componentes"):
            prune_weak_adjacencies(graph, geo, 1.0)

    def test_runner_solo_poda_con_la_opcion_y_deja_informe(self):
        graph, geo = case()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "g.json").write_text(json.dumps(graph), encoding="utf-8")
            (base / "m.geojson").write_text(json.dumps(geo), encoding="utf-8")
            config = {"inputs": {"m03_graph": "g.json", "initial_geojson": "m.geojson"},
                      "fields": {"section": "CUSEC_KEY", "district": "district_id", "population": "POP_2023",
                                 "municipality": "CUMUN", "province": "CPRO"},
                      "topology": {"min_shared_border_m": 1.0}}
            with self.assertRaises(InputContractError):  # Aragón y cualquier config sin la opción: idéntico a antes
                adapt(config, base)
            config["topology"]["prune_weak_adjacencies"] = True
            report = base / "telemetry" / "graph-preparation.json"
            data = adapt(config, base, report)
            self.assertEqual(len(data.edges), 3)
            self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["edges_pruned"], 1)

    def test_salamanca_activa_la_opcion_y_aragon_no(self):
        root = Path(__file__).resolve().parents[1] / "configuracion/ensemble"
        self.assertTrue(json.loads((root / "congreso_salamanca.json").read_text())["topology"]["prune_weak_adjacencies"])
        self.assertNotIn("prune_weak_adjacencies", json.loads((root / "aragon.json").read_text())["topology"])


if __name__ == "__main__":
    unittest.main()
