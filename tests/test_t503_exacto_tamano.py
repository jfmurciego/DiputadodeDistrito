#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: tests de T-503 (Deslinde 1.2): el exacto se aplica por tamaño (átomos × K ≤ 2.000) y huella_resultado
  no lleva las cotas de las etapas de CP-SAT que no cierran
VERSIÓN: 1.1.0
FECHA: 2026-11-26
ANTERIOR: ninguna (fichero nuevo; 1.0.0 en #1035)
CAMBIOS: 1.1.0 — (T-507, revisión de #1035) con TAMANO_MAX = 0, `aplicable` e `info` iguales a los de la 1.0.0 archivada
  (legacy/ddd_motor2/exacto_v1.0.0_20261114.py) en varios casos; se salta si la copia no está (la imagen de CI excluye legacy/).
MOTIVO: T-502 (#1029): con K=16 (Sevilla) el exacto no se aplicaba por K_MAX=4; y la cota de una etapa abierta cambia
  entre ejecuciones, así que la huella no se repetía. Sintéticos.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_motor2.reglas import Criterio, Problema, Reglas, Unidad, evaluar  # noqa: E402
from tests.test_t297_deslinde_1_1 import _Natural, contrato  # noqa: E402


def linea(n):
    us = tuple(Unidad(f"u{i}", 100, municipio=f"30{i:03d}", provincia="30") for i in range(n))
    return Problema(us, tuple((f"u{i}", f"u{i + 1}") for i in range(n - 1)))


class AplicaPorTamano(unittest.TestCase):
    def test_k_mayor_que_4_aplica_y_da_el_optimo(self):
        from deslinde.exacto import resolver
        p = linea(12)
        r = Reglas.desde_contrato(contrato(6), Criterio())
        nat = _Natural({u.id: None for u in p.unidades}, {u.id: None for u in p.unidades}, {})
        plan, info = resolver(p, r, nat, None)
        self.assertEqual(info["estado"], "OPTIMO", info)
        self.assertEqual((info["atomos"], info["tamano"], info["tamano_max"]), (12, 72, 2000))
        self.assertEqual(info["version"], "1.0.0")  # el modelo CP-SAT no cambia: misma huella donde ya aplicaba
        self.assertTrue(evaluar(p, r, plan).valido)
        self.assertEqual(len(set(plan.values())), 6)

    def test_por_encima_del_tope_no_aplica(self):
        from unittest import mock
        from deslinde.exacto import resolver
        p = linea(12)
        with mock.patch("deslinde.exacto.TAMANO_MAX", 71):
            plan, info = resolver(p, Reglas.desde_contrato(contrato(6), Criterio()), _Natural({}, {}, {}), None)
        self.assertIsNone(plan)
        self.assertEqual(info["estado"], "NO_APLICA")
        self.assertEqual(info["motivo"], "K=6 fuera de 2..4")  # literal de la 1.0.0: la huella no cambia

    def test_k_hasta_4_aplica_siempre_y_tope_0_es_la_1_0_0(self):
        from unittest import mock
        from deslinde.exacto import resolver
        p = linea(12)
        nat = _Natural({u.id: None for u in p.unidades}, {u.id: None for u in p.unidades}, {})
        with mock.patch("deslinde.exacto.TAMANO_MAX", 0):
            _, i4 = resolver(p, Reglas.desde_contrato(contrato(4), Criterio()), nat, None)
            _, i6 = resolver(p, Reglas.desde_contrato(contrato(6), Criterio()), nat, None)
            _, i1 = resolver(p, Reglas.desde_contrato(contrato(1), Criterio()), nat, None)
        self.assertEqual(i4["estado"], "OPTIMO")  # 12 × 4 = 48 > 0: con K ≤ 4 aplica aunque no quepa
        self.assertEqual((i6["estado"], i6["motivo"]), ("NO_APLICA", "K=6 fuera de 2..4"))
        self.assertEqual((i1["estado"], i1["motivo"]), ("NO_APLICA", "K=1 fuera de 2..4"))


LEGACY_100 = ROOT / "legacy" / "ddd_motor2" / "exacto_v1.0.0_20261114.py"


def _exacto_100():
    """La 1.0.0 archivada, cargada como submódulo de deslinde (usa imports relativos)."""
    import importlib.util
    import deslinde  # noqa: F401
    spec = importlib.util.spec_from_file_location("deslinde._exacto_v100", LEGACY_100)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "deslinde"
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(LEGACY_100.is_file(), "sin legacy/ (imagen de CI)")
class TopeCeroEsLa100(unittest.TestCase):
    """Con TAMANO_MAX = 0 la 1.1.0 decide y devuelve lo mismo que la 1.0.0 (salvo las claves nuevas de info)."""
    NUEVAS = {"version_fichero", "tamano_max", "tamano", "k_max"}

    def casos(self):
        p = linea(12)
        nat = _Natural({u.id: None for u in p.unidades}, {u.id: None for u in p.unidades}, {})
        exento = contrato(6)
        exento["validation"]["population_floor_exempt_municipalities"] = ["30001"]
        for k in (1, 2, 3, 4, 5, 6, 12):
            for funcion in ("D8", "A"):
                yield f"K={k} {funcion}", p, contrato(k), nat, funcion
        yield "K=6 exento", p, exento, nat, "D8"

    def test_aplicable_e_info_iguales(self):
        from unittest import mock
        import deslinde.exacto as nuevo
        viejo = _exacto_100()
        for nombre, p, cfg, nat, funcion in self.casos():
            with self.subTest(nombre):
                r = Reglas.desde_contrato(cfg, Criterio())
                with mock.patch("deslinde.exacto.TAMANO_MAX", 0):
                    self.assertEqual(nuevo.aplicable(p, r, funcion), viejo.aplicable(p, r, funcion))
                    pn, inn = nuevo.resolver(p, r, nat, None, funcion=funcion)
                pv, iv = viejo.resolver(p, r, nat, None, funcion=funcion)
                self.assertEqual(pn, pv)
                self.assertEqual({k: v for k, v in inn.items() if k not in self.NUEVAS},
                                 {k: v for k, v in iv.items() if k not in self.NUEVAS})


class HuellaSinCotasAbiertas(unittest.TestCase):
    def resultado(self, etapas):
        from deslinde.competicion import Candidato, Resultado
        g = Candidato("exacto", "exacto", None, 0)
        return Resultado("t", [g], g, g, "h", {}, 0.0, funcion="D8",
                         exacto={"version": "1.0.0", "aplicable": True, "estado": "MEJOR_VALIDO", "etapas": etapas,
                                 "ortools": "9.14"})

    def test_la_cota_de_una_etapa_abierta_no_cambia_la_huella(self):
        base = [["fuera", "OPTIMAL", 0, 0], ["exceso_8", "CONSTANTE", 5, 5], ["partidas", "OPTIMAL", 6, 6]]
        a = self.resultado(base + [["frontera_mm", "FEASIBLE", 785968300, 345072575]]).huella()
        b = self.resultado(base + [["frontera_mm", "FEASIBLE", 785968300, 355377584]]).huella()
        self.assertEqual(a, b)
        c = self.resultado(base + [["frontera_mm", "FEASIBLE", 785968301, 345072575]]).huella()
        self.assertNotEqual(a, c)  # el valor sí entra
        d = self.resultado([["fuera", "OPTIMAL", 0, 1]] + base[1:] + [["frontera_mm", "FEASIBLE", 785968300, 1]]).huella()
        self.assertNotEqual(a, d)  # la cota de una etapa cerrada sigue entrando (como en 1.5.0)


if __name__ == "__main__":
    unittest.main()
