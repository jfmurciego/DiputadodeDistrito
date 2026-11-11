#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-256: la poda con constantes precalculadas (enumerar 1.2.0) es idéntica a la 1.1.0 (fixture, copia de legacy): mismas violaciones
en el mismo orden para parciales aleatorios, y la enumeración visita y poda exactamente los mismos nodos."""
from __future__ import annotations

import importlib
import importlib.util
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from ddd_motor2.reglas import Criterio, Reglas  # noqa: E402
from test_motor2_reglas import _contrato_aleatorio, _rejilla  # noqa: E402


# Copia de la 1.1.0 dentro de tests/: la imagen Docker de la CI excluye legacy/ (.dockerignore).
FIXTURE = ROOT / "tests/fixtures/motor2_enumerar_v1_1_0/enumerar_v1_1_0.py"
LEGACY = ROOT / "legacy/ddd_motor2/reglas/enumerar_v1.1.0_20261110.py"


def _cargar_anterior():
    nombre = "ddd_motor2.reglas._enumerar_v110"  # dentro del paquete para que resuelvan los imports relativos
    spec = importlib.util.spec_from_file_location(nombre, FIXTURE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


nuevo = importlib.import_module("ddd_motor2.reglas.enumerar")  # el módulo, no la función reexportada
anterior = _cargar_anterior()


def _caso(rng, caso):
    p = _rejilla(rng, filas=rng.choice([2, 3]), cols=rng.choice([3, 4]), nucleos=caso % 3 == 0)
    k = rng.choice([2, 3, 4])
    r = Reglas.desde_contrato(_contrato_aleatorio(rng, k, permisivo=caso % 2 == 0),
                              Criterio(tolerancia=rng.choice(["metrica", "dura"])))
    return p, r, k


def _traza(mod, p, r, presupuesto):
    """Enumera con mod y anota cada llamada a podar: (parcial, violaciones)."""
    traza, original = [], mod.podar

    def espia(*a, **kw):
        res = original(*a, **kw)
        traza.append((tuple(sorted(a[2].items())), tuple(res)))
        return res
    mod.podar = espia
    try:
        res = mod.enumerar(p, r, presupuesto=presupuesto, max_planes=10**6,
                           clave=lambda plan: tuple(sorted(plan.items())))
    finally:
        mod.podar = original
    return res, traza


class PodaConstantes(unittest.TestCase):
    def test_fixture_es_la_copia_legacy(self):
        if not LEGACY.is_file():
            self.skipTest("legacy/ no está en la imagen")
        cuerpo = FIXTURE.read_text(encoding="utf-8").split("\n", 1)[1]
        self.assertEqual(cuerpo, LEGACY.read_text(encoding="utf-8"))

    def test_misma_poda_en_parciales_aleatorios(self):
        rng = random.Random(256)
        n_podados = 0
        for caso in range(150):
            p, r, k = _caso(rng, caso)
            ids = [u.id for u in p.unidades]
            ctx = nuevo.Contexto.de(p, r)
            pre = nuevo._Constantes(p, r, ctx)
            for _ in range(40):
                fijas = rng.sample(ids, rng.randint(0, len(ids)))
                parcial = {u: f"B{rng.randrange(k + 1)}" for u in fijas}
                viejo = anterior.podar(p, r, parcial)
                self.assertEqual(nuevo.podar(p, r, parcial), viejo, f"caso {caso}")
                self.assertEqual(nuevo.podar(p, r, parcial, ctx, pre), viejo, f"caso {caso}")
                n_podados += bool(viejo)
        self.assertGreater(n_podados, 500)  # no vacuo

    def test_enumeracion_mismos_nodos_y_podas(self):
        rng = random.Random(4)
        n_nodos = n_completos = n_agotados = 0
        for caso in range(80):
            p, r, _ = _caso(rng, caso)
            presupuesto = rng.choice([50, 500, 10**6])
            res_v, traza_v = _traza(anterior, p, r, presupuesto)
            res_n, traza_n = _traza(nuevo, p, r, presupuesto)
            self.assertEqual(traza_n, traza_v, f"caso {caso}")
            self.assertEqual(res_n, res_v, f"caso {caso}")
            n_nodos += len(traza_v)
            n_completos += res_v["completo"]
            n_agotados += not res_v["completo"]
        self.assertGreater(n_nodos, 5_000)
        self.assertGreater(n_completos, 0)
        self.assertGreater(n_agotados, 0)


if __name__ == "__main__":
    unittest.main()
