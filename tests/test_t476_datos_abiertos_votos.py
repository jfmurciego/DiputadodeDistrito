#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de votos por partido y distrito, doble vuelta y composición (T-476)
VERSIÓN: 1.0.0 · FECHA: 2026-11-28 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: genera en un directorio temporal y valida con `--comprobar` (sha256, cuadre BOE, ganador 2023); valores esperados
  literales de fuentes independientes (M08 ligero de nac01, BOE, recuentos del traspaso); detecta salidas alteradas.
"""
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import datos_abiertos_votos as dav  # noqa: E402

NAC_CON_HISTORICO = ["nac01", "nac05", "nac07", "nac34", "nac40", "nac42", "nac44", "nac49", "nac50", "nac51", "nac52"]


class Votos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.man = dav.generar(cls.tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def filas(self, f):
        with open(self.tmp / f, encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh))

    def test_comprobar_sin_errores(self):
        self.assertEqual(dav.comprobar(self.tmp), [])

    def test_recuentos_del_traspaso(self):
        r = self.man["resumen"]
        self.assertEqual(r["nac_2023"], 52)
        self.assertEqual(r["nac_con_historico"], NAC_CON_HISTORICO)
        self.assertEqual(r["filas_no_construible"], 41 * 5)  # 41 nac × 5 elecciones, motivo: mapa anterior
        self.assertEqual({x["territorio"] for x in self.filas("no_construible.csv")}, set(dav.vigentes()) - set(NAC_CON_HISTORICO))

    def test_valor_literal_nac01_2023(self):
        # M08 ligero: el ganador del distrito 1 de Álava es PSE-EE (PSOE) con 18146 votos (datos/resultados/nac01.csv)
        v = {(r["distrito"], r["partido"]): int(r["votos"]) for r in self.filas("votos_partido_distrito.csv")
             if r["territorio"] == "nac01" and r["eleccion"] == "202307"}
        self.assertEqual(v[("1", "PSE-EE (PSOE)")], 18146)
        self.assertEqual({d for d, _ in v}, {"1", "2", "3"})

    def test_doble_vuelta_tres_escenarios_por_distrito(self):
        f = [r for r in self.filas("doble_vuelta.csv") if r["territorio"] == "nac01" and r["eleccion"] == "202307"]
        self.assertEqual(sorted({r["escenario"] for r in f}), ["dv_A", "dv_B", "dv_base"])
        self.assertEqual(len(f), 3 * 3)

    def test_salida_fuera_de_datos_abiertos(self):
        self.assertNotIn("datos_abiertos", dav.SALIDA.relative_to(dav.ROOT).parts)

    def test_generar_es_determinista(self):
        otro = Path(tempfile.mkdtemp())
        try:
            self.assertEqual(dav.generar(otro)["salidas"], self.man["salidas"])
        finally:
            shutil.rmtree(otro, ignore_errors=True)

    def test_detecta_salida_alterada_y_exceso_sobre_el_boe(self):
        otro = Path(tempfile.mkdtemp())
        try:
            dav.generar(otro)
            p = otro / "votos_partido_distrito.csv"
            texto = p.read_text(encoding="utf-8").replace("nac01,202307,1,PSE-EE (PSOE),18146", "nac01,202307,1,PSE-EE (PSOE),918146", 1)
            p.write_text(texto, encoding="utf-8")
            err = dav.comprobar(otro)
            self.assertTrue(any("sha256 de la salida votos_partido_distrito.csv" in e for e in err))
            self.assertTrue(any("nac01 202307" in e and "secundaria" in e for e in err))  # más votos que el BOE: error
        finally:
            shutil.rmtree(otro, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
