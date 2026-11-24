#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-449 (D-183, propietario 24-11): autonómicas de Castilla-La Mancha 2023 por municipio, desde la copia archivada del xlsx oficial.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-24
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: fija el cuadre EXACTO contra el Observatorio (fuente no oficial; no hay totales oficiales en fichero) con sus cifras literales de
  hauteskundea/08-202305.json (sha256 0443c79e…): votos a candidaturas sin CERA 1.070.325 (PSOE 489.302, PP 365.705, VOX 139.278),
  CERA por provincia 457/505/222/435/939 y escaños 17/12/4 (Albacete 3-3-1, Ciudad Real 4-2-1, Cuenca 3-2, Guadalajara 2-2-1, Toledo 5-3-1).
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import csv
import json
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import adaptador_clm_2023 as a  # noqa: E402

DV = ROOT / "datos/resultados/doble_vuelta_autonomicas/aut08/202305"


class AdaptadorClm2023(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.m = a.construir(Path(cls.td.name))
        with (Path(cls.td.name) / "municipios.csv").open(encoding="utf-8", newline="") as f:
            cls.filas = list(csv.DictReader(f))

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_municipios_y_cuadre(self):
        self.assertEqual(self.m["municipios"], 919)
        self.assertTrue(self.m["cuadra"])
        self.assertEqual(self.m["fallos"], [])

    def test_totales_literales_del_observatorio(self):
        suma = {}
        for r in self.filas:
            suma[r["partido"]] = suma.get(r["partido"], 0) + int(r["votos"])
        self.assertEqual(sum(suma.values()), 1070325)
        self.assertEqual((suma["PSOE"], suma["PP"], suma["VOX"]), (489302, 365705, 139278))

    def test_literales_por_provincia(self):
        # Observatorio 08-202305.json: `probintzia[p][2]` (votos a candidaturas sin CERA) y `cera[p][4]`
        self.assertEqual(self.m["votos_por_provincia"], {"02": 204971, "13": 264611, "16": 110909, "19": 128150, "45": 361684})
        self.assertEqual(self.m["cera_por_provincia"], {"02": 457, "13": 505, "16": 222, "19": 435, "45": 939})

    def test_cera_fuera_de_distritos(self):
        aus = self.m["votos_ausentes_no_repartidos"]
        self.assertEqual(sum(aus.values()), 457 + 505 + 222 + 435 + 939)
        self.assertFalse([r for r in self.filas if r["municipio"].endswith("990")])

    def test_escanos_literales(self):
        self.assertEqual(self.m["escanos_dhondt"], {"02": {"PP": 3, "PSOE": 3, "VOX": 1}, "13": {"PP": 2, "PSOE": 4, "VOX": 1},
                                                   "16": {"PP": 2, "PSOE": 3}, "19": {"PP": 2, "PSOE": 2, "VOX": 1},
                                                   "45": {"PP": 3, "PSOE": 5, "VOX": 1}})
        self.assertEqual(self.m["escanos_total"], 33)

    def test_origen_declarado_no_oficial(self):
        f = self.m["fuente"]
        self.assertEqual((f["tipo"], f["oficial"], f["sha256"], f["captura"]),
                         ("copia_archivada", False, "7591997d17c65586bd5d8ac68776e9946e233997f86cbe1c22e08018c16347ca", "20261023040608"))
        self.assertIn("NO oficial", self.m["cuadre_contra"]["nota"])

    def test_dhondt_literal(self):
        # a mano: 5 escaños, A 100 / B 80 / C 30 / D 5 → cocientes 100, 80, 50 (A/2), 40 (B/2), 33,3 (A/3) → A 3, B 2
        self.assertEqual(a.dhondt({"A": 100, "B": 80, "C": 30, "D": 5}, 5), {"A": 3, "B": 2})
        # la barrera del 3 % decide: 34 escaños, A 971 / C 29 (2,9 %); el cociente 34.º de A es 971/34 = 28,56 < 29, así que sin
        # barrera C tendría 1; con ella, ninguno
        self.assertEqual(a.dhondt({"A": 971, "C": 29}, 34, barrera=0), {"A": 33, "C": 1})
        self.assertEqual(a.dhondt({"A": 971, "C": 29}, 34), {"A": 34})


class HuellasYNoCuadre(unittest.TestCase):
    def _raiz(self, td: Path) -> Path:
        for rel in (a.VOLCADO, a.OBSERVATORIO):
            (td / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, td / rel)
        return td

    def test_volcado_alterado_falla(self):
        with tempfile.TemporaryDirectory() as t:
            r = self._raiz(Path(t))
            p = r / a.VOLCADO
            p.write_bytes(p.read_bytes().replace(b",248,", b",249,", 1))
            with self.assertRaises(ValueError):
                a.construir(Path(t) / "s", raiz=r)

    def test_si_no_cuadra_falla(self):
        with tempfile.TemporaryDirectory() as t, unittest.mock.patch.object(a, "OBSERVATORIO_SHA256", None):
            r = self._raiz(Path(t))
            o = json.loads((r / a.OBSERVATORIO).read_text(encoding="utf-8"))
            o["probintzia"]["02"][3][0][1] += 1  # un voto más al primer partido de Albacete
            (r / a.OBSERVATORIO).write_text(json.dumps(o), encoding="utf-8")
            with unittest.mock.patch.object(a, "OBSERVATORIO_SHA256", a.sha256(r / a.OBSERVATORIO)), \
                    self.assertRaisesRegex(ValueError, "no cuadra"):
                a.construir(Path(t) / "s", raiz=r)


class DobleVueltaAut08(unittest.TestCase):
    """El resultado versionado (doble_vuelta_votos_aut.py, nivel municipio, run 43745006294) conserva los votos y declara el origen."""

    def test_votos_y_manifiesto(self):
        man = json.loads((DV / "MANIFEST.json").read_text(encoding="utf-8"))
        with (DV / "aut08_partidos.csv").open(encoding="utf-8", newline="") as f:
            total = sum(int(r["votos"]) for r in csv.DictReader(f))
        self.assertEqual(total, 1070325)
        self.assertEqual((man["run_m08"], man["nivel"], man["aproximado_en_distrito"], man["cuadre"]["distritos"]),
                         ("43745006294", "municipio", True, 33))
        self.assertEqual(man["fuentes"]["fuente"]["tipo"], "copia_archivada")
        self.assertIs(man["fuentes"]["fuente"]["oficial"], False)
        self.assertTrue(man["fuentes"]["cuadre_observatorio"]["cuadra"])
        self.assertEqual(sum(man["cuadre"]["fuera_de_distritos"]["votos_ausentes_no_repartidos"].values()), 2558)


if __name__ == "__main__":
    unittest.main()
