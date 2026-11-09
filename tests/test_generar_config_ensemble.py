"""Versión 1.2.0; 2026-11-09; candidato. T-92: el generador de configs de ensemble respeta el contrato de cada provincia.
T-98: Cádiz entra con el techo aprobado y la exención de San Fernando; el resto de exenciones sigue fuera.
T-120: Barcelona entra con la exención de Cornellà (08073)."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import yaml

from herramientas.generar_config_ensemble import EXCLUIDOS_POR_ORDEN, EXENCION, MOLDE, construir, motivo_no_apto

ROOT = Path(__file__).resolve().parents[1]


def _contrato(tid):
    return yaml.safe_load((ROOT / f"territorios/{tid}/config/{tid}_2025.yaml").read_text(encoding="utf-8"))


class GeneradorConfigEnsembleTests(unittest.TestCase):
    def setUp(self):
        self.molde = json.loads((ROOT / f"configuracion/ensemble/{MOLDE}.json").read_text(encoding="utf-8"))

    def test_reproduce_las_configs_existentes(self):
        for tid in ("congreso_jaen", "congreso_cordoba", "congreso_sevilla"):
            real = json.loads((ROOT / f"configuracion/ensemble/{tid}.json").read_text(encoding="utf-8"))
            self.assertEqual(construir(_contrato(tid), self.molde), real, tid)

    def test_rechaza_puentes_exenciones_y_k1(self):
        self.assertIn("topology_bridges", motivo_no_apto(_contrato("congreso_badajoz"), self.molde))
        self.assertIn("K=1", motivo_no_apto(_contrato("congreso_soria"), self.molde))

    def test_rechaza_limite_distinto(self):
        c = copy.deepcopy(_contrato("congreso_lugo"))
        c["validation"]["population_cap_ratio"] = 1.2
        self.assertIn("population_cap_ratio", motivo_no_apto(c, self.molde))

    def test_excluidos_sin_config(self):
        for tid in EXCLUIDOS_POR_ORDEN:
            self.assertFalse((ROOT / f"configuracion/ensemble/{tid}.json").exists(), tid)

    def test_cadiz_aprobado_reproduce_su_config(self):
        c = _contrato("congreso_cadiz")
        self.assertIsNone(motivo_no_apto(c, self.molde))
        real = json.loads((ROOT / "configuracion/ensemble/congreso_cadiz.json").read_text(encoding="utf-8"))
        self.assertEqual(construir(c, self.molde), real)
        self.assertEqual(real["contract"]["population_cap_ratio"], 1.16)

    def test_aprobacion_no_cubre_exencion_sin_decision(self):
        c = copy.deepcopy(_contrato("congreso_cadiz"))
        c["validation"]["population_floor_exempt_decisions"] = {}
        self.assertIn("sin decisión", motivo_no_apto(c, self.molde))

    def test_barcelona_aprobado_reproduce_su_config(self):
        c = _contrato("congreso_barcelona")
        self.assertIsNone(motivo_no_apto(c, self.molde))
        real = json.loads((ROOT / "configuracion/ensemble/congreso_barcelona.json").read_text(encoding="utf-8"))
        self.assertEqual(construir(c, self.molde), real)
        self.assertEqual(real["contract"]["population_floor_exempt_municipalities"], ["08073"])
        self.assertEqual(real["contract"]["population_cap_ratio"], 1.15)
        self.assertEqual(real["decisions"][f"{EXENCION}:08073"]["decided_by"], "propietario")

    def test_rechaza_exencion_no_gobernada(self):
        c = copy.deepcopy(_contrato("congreso_barcelona"))
        c["validation"][EXENCION] = ["08073", "08019"]
        self.assertIn("08019 sin decisión", motivo_no_apto(c, self.molde))
        c = copy.deepcopy(_contrato("congreso_barcelona"))
        c["validation"]["population_floor_exempt_partitions"] = ["X"]
        self.assertIn("exención population_floor_exempt_partitions", motivo_no_apto(c, self.molde))
        c = copy.deepcopy(_contrato("congreso_lugo"))
        c["validation"][EXENCION] = ["27028"]
        self.assertIn("exención", motivo_no_apto(c, self.molde))


if __name__ == "__main__":
    unittest.main()
