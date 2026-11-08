"""Versión 1.0.0; 2026-11-08; candidato. T-92: el generador de configs de ensemble respeta el contrato de cada provincia."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import yaml

from herramientas.generar_config_ensemble import EXCLUIDOS_POR_ORDEN, MOLDE, construir, motivo_no_apto

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
        self.assertIn("exención", motivo_no_apto(_contrato("congreso_barcelona"), self.molde))
        self.assertIn("K=1", motivo_no_apto(_contrato("congreso_soria"), self.molde))

    def test_rechaza_limite_distinto(self):
        c = copy.deepcopy(_contrato("congreso_lugo"))
        c["validation"]["population_cap_ratio"] = 1.2
        self.assertIn("population_cap_ratio", motivo_no_apto(c, self.molde))

    def test_madrid_y_cadiz_sin_config(self):
        for tid in EXCLUIDOS_POR_ORDEN:
            self.assertFalse((ROOT / f"configuracion/ensemble/{tid}.json").exists(), tid)


if __name__ == "__main__":
    unittest.main()
