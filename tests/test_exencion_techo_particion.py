#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-235 (D-83): exención de techo de una partición atómica con K=1 (Lanzarote y La Graciosa, Las Palmas 2026)."""
from __future__ import annotations

import copy
import math
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ddd_core.population_cap_exemptions import CapExemptionError, cap_exempt_partitions, district_cap  # noqa: E402

CONTRATO_2026 = ROOT / "territorios/nac35/config/nac35_2026.yaml"
DECISION = {"decided_at": "2026-11-11", "decided_by": "propietario", "decision": "D-83",
            "reason": "isla entera", "evidence": "docs/PLAN.md D-83"}


def _cfg(exentas=None, cuotas=None, decisiones=None):
    val = {"province_districts": cuotas if cuotas is not None else {"35-C01": 8, "35-C02": 1, "35-G01": 1}}
    if exentas is not None:
        val["population_cap_exempt_partitions"] = exentas
    if decisiones is not None:
        val["population_cap_exempt_partition_decisions"] = decisiones
    return {"validation": val}


class ReglaComun(unittest.TestCase):
    def test_sin_clave_nada_cambia(self):
        for cfg in (_cfg(), _cfg(exentas=[]), {}, None):
            self.assertEqual(cap_exempt_partitions(cfg), frozenset())
        self.assertEqual(district_cap(164016.58, ["35-G01"], frozenset()), 164016.58)

    def test_k_mayor_que_uno_rechazada(self):
        with self.assertRaisesRegex(CapExemptionError, "K=8"):
            cap_exempt_partitions(_cfg(["35-C01"], decisiones={"35-C01": DECISION}))

    def test_particion_desconocida_rechazada(self):
        with self.assertRaisesRegex(CapExemptionError, "province_districts"):
            cap_exempt_partitions(_cfg(["38-C01"], decisiones={"38-C01": DECISION}))

    def test_decision_obligatoria_y_del_propietario(self):
        with self.assertRaisesRegex(CapExemptionError, "falta su decisión"):
            cap_exempt_partitions(_cfg(["35-G01"]))
        sin_motivo = dict(DECISION, reason="")
        with self.assertRaisesRegex(CapExemptionError, "reason"):
            cap_exempt_partitions(_cfg(["35-G01"], decisiones={"35-G01": sin_motivo}))
        otro = dict(DECISION, decided_by="planificador")
        with self.assertRaisesRegex(CapExemptionError, "propietario"):
            cap_exempt_partitions(_cfg(["35-G01"], decisiones={"35-G01": otro}))
        with self.assertRaisesRegex(CapExemptionError, "sin exención"):
            cap_exempt_partitions(_cfg(["35-G01"], decisiones={"35-G01": DECISION, "35-C02": DECISION}))

    def test_techo_efectivo_solo_del_distrito_exento(self):
        exentas = cap_exempt_partitions(_cfg(["35-G01"], decisiones={"35-G01": DECISION}))
        self.assertEqual(exentas, frozenset({"35-G01"}))
        self.assertTrue(math.isinf(district_cap(164016.58, ["35-G01", "35-G01"], exentas)))
        self.assertEqual(district_cap(164016.58, ["35-C02"], exentas), 164016.58)
        self.assertEqual(district_cap(164016.58, ["35-C01"], exentas), 164016.58)
        self.assertEqual(district_cap(164016.58, ["35-G01", "35-C02"], exentas), 164016.58)


class ContratoLasPalmas2026(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = yaml.safe_load(CONTRATO_2026.read_text(encoding="utf-8"))
        cls.val = cls.cfg["validation"]

    def test_solo_lanzarote_y_la_graciosa(self):
        self.assertEqual(cap_exempt_partitions(self.cfg), frozenset({"35-G01"}))
        self.assertEqual(self.val["population_cap_exempt_partition_decisions"]["35-G01"]["decision"], "D-83")

    def test_techo_general_sigue_en_1_40(self):
        self.assertEqual(self.val["population_cap_ratio"], 1.4)
        self.assertEqual(self.cfg["territory_contract"]["population_cap_ratio"], 1.4)

    def test_la_isla_excede_el_techo_y_es_un_distrito(self):
        # Padrón INE 2025 (65034, inputs/partes): 166.878 hab. en 35-G01 y 1.171.547 en la provincia (T-225).
        self.assertEqual(self.val["partition_populations"]["35-G01"], 166878)
        self.assertEqual(self.val["source_baseline"]["population_total"], 1171547)
        self.assertEqual(self.val["province_districts"]["35-G01"], 1)
        objetivo = 1171547 / 10
        self.assertAlmostEqual(166878 / objetivo, 1.4244, places=4)
        self.assertGreater(166878, objetivo * 1.4)
        # Las demás particiones caben bajo el techo general y no están exentas.
        for p in ("35-C01", "35-C02"):
            media = self.val["partition_populations"][p] / self.val["province_districts"][p]
            self.assertLess(media, objetivo * 1.4)

    def test_sin_la_exencion_el_contrato_no_exime(self):
        cfg = copy.deepcopy(self.cfg)
        del cfg["validation"]["population_cap_exempt_partitions"]
        del cfg["validation"]["population_cap_exempt_partition_decisions"]
        self.assertEqual(cap_exempt_partitions(cfg), frozenset())

    def test_exenciones_gobernadas(self):
        from herramientas.comprobar_exenciones_gobernadas import check_contract
        self.assertEqual(check_contract("las_palmas_2026", self.cfg), [])
        malo = copy.deepcopy(self.cfg)
        malo["validation"]["province_districts"]["35-G01"] = 2
        self.assertTrue(any("K=2" in e for e in check_contract("x", malo)))


class Validador(unittest.TestCase):
    def test_sobre_techo_salvo_exentos(self):
        import pandas as pd
        from herramientas.validar_ejecucion import cap_exempt_districts, districts_above_cap
        cfg = _cfg(["35-G01"], decisiones={"35-G01": DECISION})
        sec = pd.DataFrame({"district_id": [0, 0, 9, 9], "DDD_PARTITION": ["35-C01", "35-C01", "35-G01", "35-G01"]})
        ids = cap_exempt_districts(cfg, {"province_field": "DDD_PARTITION"}, cfg["validation"], sec, "district_id")
        self.assertEqual(ids, {"9"})
        summ = pd.DataFrame({"district_id": [0, 9], "district_pop": [170000, 166878]})
        self.assertEqual(districts_above_cap(summ, "district_pop", 164016.58, ids),
                         [{"district_id": 0, "district_pop": 170000}])
        self.assertEqual(len(districts_above_cap(summ, "district_pop", 164016.58, set())), 2)
        self.assertEqual(cap_exempt_districts(_cfg(), {"province_field": "DDD_PARTITION"}, {}, sec, "district_id"), set())


class Motor2(unittest.TestCase):
    """motor2 (ddd_motor2.reglas) lee la misma regla común que M04-M06 y el validador."""

    @staticmethod
    def _caso(exentas=None, cuotas=None):
        from ddd_motor2.reglas.modelo import Problema, Unidad
        val = {"expected_districts": 2, "population_floor_ratio": 0.85, "population_cap_ratio": 1.15,
               "target_tolerance_ratio": 0.15, "require_single_province_per_district": False,
               "require_municipality_discipline": False,
               "province_districts": cuotas or {"35-G01": 1, "35-C01": 1}}
        if exentas is not None:
            val["population_cap_exempt_partitions"] = exentas
            val["population_cap_exempt_partition_decisions"] = {p: DECISION for p in exentas}
        us = (Unidad("isla", 150, municipio="35024", provincia="35", particion="35-G01"),
              Unidad("a", 60, municipio="35001", provincia="35", particion="35-C01"),
              Unidad("b", 40, municipio="35002", provincia="35", particion="35-C01"))
        return Problema(us, (("a", "b"),)), {"validation": val}

    def test_sin_clave_viola_techo_y_huella_igual(self):
        from ddd_motor2.reglas import Reglas
        from ddd_motor2.reglas.evaluar import evaluar
        problema, cfg = self._caso()
        reglas = Reglas.desde_contrato(cfg)
        self.assertEqual(reglas.exentas_techo, frozenset())
        self.assertNotIn("exentas_techo", reglas.forma_canonica())
        inf = evaluar(problema, reglas, {"isla": "D0", "a": "D1", "b": "D1"})
        self.assertIn("R-POB-TECHO", inf.codigos())

    def test_con_exencion_solo_el_distrito_de_la_isla(self):
        from ddd_motor2.reglas import Reglas
        from ddd_motor2.reglas.evaluar import evaluar
        problema, cfg = self._caso(["35-G01"])
        reglas = Reglas.desde_contrato(cfg)
        self.assertEqual(reglas.exentas_techo, frozenset({"35-G01"}))
        self.assertNotEqual(reglas.huella(), Reglas.desde_contrato(self._caso()[1]).huella())
        inf = evaluar(problema, reglas, {"isla": "D0", "a": "D1", "b": "D1"})
        self.assertNotIn("R-POB-TECHO", inf.codigos())
        # Un distrito que mezcla la isla con otra partición no está exento.
        inf = evaluar(problema, reglas, {"isla": "D0", "a": "D0", "b": "D1"})
        self.assertIn("R-POB-TECHO", inf.codigos())

    def test_k_mayor_que_uno_es_error_de_contrato(self):
        from ddd_motor2.reglas import Reglas
        from ddd_motor2.reglas.modelo import ErrorContrato
        _, cfg = self._caso(["35-C01"], cuotas={"35-G01": 0, "35-C01": 2})
        with self.assertRaisesRegex(ErrorContrato, "K=2"):
            Reglas.desde_contrato(cfg)


if __name__ == "__main__":
    unittest.main()
