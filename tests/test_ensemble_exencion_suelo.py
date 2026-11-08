"""Versión 1.0.0; 2026-11-08; candidato. ANTERIOR: ninguna (fichero nuevo).
T-98: el ensemble respeta validation.population_floor_exempt_municipalities como M05 7.8.5 (caso San Fernando, Cádiz):
el distrito con el municipio exento puede quedar bajo el suelo; techo, límite superior, K y atomicidad no cambian.
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

import yaml

from ddd_core.m05_gerrychain_engine import Contract, adapt_inputs, hard_constraint_violations, run_gerrychain

ROOT = Path(__file__).resolve().parents[1]
EXENTO = "11031"


def _datos():
    """San Fernando sintético (80 hab., una unidad atómica) y una rejilla 2x11 de secciones de 10 hab.

    K=3, objetivo 100: el distrito exento (80) queda bajo el suelo 0,85 y bajo la tolerancia 0,16; los otros, en 110.
    """
    nodes = [{"id": "SF", "pop": 80}]
    edges = [{"u": "SF", "v": "0-0"}, {"u": "SF", "v": "1-0"}]
    features = [{"type": "Feature", "geometry": None, "properties": {
        "CUSEC_KEY": "SF", "district_id": 1, "CUMUN": EXENTO, "CPRO": "11", "ddd_unit_id": f"11:{EXENTO}:M"}}]
    for row in range(2):
        for col in range(11):
            sid = f"{row}-{col}"
            nodes.append({"id": sid, "pop": 10})
            if col < 10:
                edges.append({"u": sid, "v": f"{row}-{col + 1}"})
            if row == 0:
                edges.append({"u": sid, "v": f"1-{col}"})
            features.append({"type": "Feature", "geometry": None, "properties": {
                "CUSEC_KEY": sid, "district_id": 2 if row == 0 else 3, "CUMUN": f"11{100 + row * 11 + col}",
                "CPRO": "11", "ddd_unit_id": sid}})
    graph = {"nodes": nodes, "edges": [(e["u"], e["v"]) for e in edges]}
    return adapt_inputs({"nodes": nodes, "edges": edges}, {"type": "FeatureCollection", "features": features}), graph


def _contrato(exentos=()):
    return Contract(k=3, target_tolerance_ratio=0.16, population_floor_ratio=0.85, population_cap_ratio=1.16,
                    municipality_atomicity_limit_ratio=1.15, province_districts={"11": 3},
                    population_floor_exempt_municipalities=tuple(exentos))


class ExencionSueloEnsembleTests(unittest.TestCase):
    def setUp(self):
        self.data, _ = _datos()

    def test_sin_exencion_la_particion_inicial_es_invalida(self):
        v = hard_constraint_violations(self.data, self.data.initial_assignment, _contrato())
        self.assertEqual(v, ["population_floor:1", "population_tolerance:1"])

    def test_con_exencion_la_particion_inicial_es_valida(self):
        self.assertEqual(hard_constraint_violations(self.data, self.data.initial_assignment, _contrato([EXENTO])), [])

    def test_la_exencion_no_alcanza_a_otros_distritos_ni_al_techo(self):
        a = dict(self.data.initial_assignment)
        for col in range(3):  # 2 baja a 80 (sin exento) y 3 sube a 140 (sobre techo y tolerancia)
            a[f"0-{col}"] = 3
        a["SF"] = 1
        v = hard_constraint_violations(self.data, a, _contrato([EXENTO]))
        self.assertIn("population_floor:2", v)
        self.assertIn("population_cap:3", v)
        self.assertNotIn("population_floor:1", v)

    @unittest.skipUnless(importlib.util.find_spec("gerrychain"), "gerrychain no instalado")
    def test_la_cadena_recom_arranca_y_no_parte_el_municipio_exento(self):
        _, report = run_gerrychain(self.data, _contrato([EXENTO]), total_steps=60, seed=98)
        self.assertTrue(report["hard_constraints"]["all_pass"], report["hard_constraints"])
        self.assertEqual(list(report["configuration"]["contract"]["population_floor_exempt_municipalities"]), [EXENTO])
        self.assertGreater(report["telemetry"]["unique_states"], 1)

    def test_config_de_cadiz_hereda_la_exencion_gobernada(self):
        cfg = json.loads((ROOT / "configuracion/ensemble/congreso_cadiz.json").read_text(encoding="utf-8"))
        contrato = yaml.safe_load((ROOT / "territorios/congreso_cadiz/config/congreso_cadiz_2025.yaml").read_text(encoding="utf-8"))
        val = contrato["validation"]
        self.assertEqual(cfg["contract"]["population_floor_exempt_municipalities"], val["population_floor_exempt_municipalities"])
        self.assertEqual(cfg["contract"]["population_cap_ratio"], val["population_cap_ratio"])
        self.assertEqual(cfg["contract"]["target_tolerance_ratio"], val["target_tolerance_ratio"])
        decisiones = cfg["decisions"]
        for clave in ("population_cap_ratio", f"population_floor_exempt_municipalities:{EXENTO}"):
            self.assertTrue({"decided_at", "decided_by", "reason", "evidence"} <= set(decisiones[clave]), clave)


if __name__ == "__main__":
    unittest.main()
