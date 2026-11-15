#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la puerta del histórico (T-342)
VERSIÓN: 1.0.0 · FECHA: 2026-11-15 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: puerta por territorio y elección con fixtures congelados (tests/fixtures/t342_puerta; nada vivo): M07 PASS,
  excepciones declaradas ≤ 0,1 %, > 0,1 % falla, 2011 con D-70, contraste BOE fuera de tolerancia y sin CSV fallan.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import historico_campana as hc  # noqa: E402

FX = ROOT / "tests/fixtures/t342_puerta"
RAIZ = FX / "raiz"


def puerta(caso, clave, t, prov, ra=0):
    return hc.puerta_json(t, clave, "2023", ra, None, FX / caso, None, prov, RAIZ, FX / caso / "espejo.json")


class Puerta(unittest.TestCase):
    def test_pass_con_contraste_dentro_de_tolerancia(self):
        p = puerta("pass", "201911", "nac01", "01")
        self.assertEqual(p["estado"], "PASS")
        self.assertEqual(p["contraste_boe"]["diferencia"], 0.025)  # mayor defecto por partido: BBB (400000 → 390000); OTROS no está en el BOE
        self.assertEqual(p["contraste_boe"]["tolerancia"], 0.10)
        self.assertIn("informativo_ganador", p)

    def test_excepcion_declarada_hasta_una_milesima(self):
        p = puerta("exc_ok", "201911", "nac01", "01")
        self.assertEqual((p["m07"], p["estado"]), ("PASS_WITH_DECLARED_EXCEPTIONS", "PASS"))
        self.assertAlmostEqual(p["perdidos_pct"], 900 / 980000)

    def test_excepcion_sobre_una_milesima_falla(self):
        self.assertEqual(puerta("exc_alta", "201911", "nac01", "01")["estado"], "FAIL")

    def test_2011_hereda_d70_solo_en_sus_provincias(self):
        self.assertEqual(puerta("d70", "201111", "nac27", "27")["estado"], "PASS")
        self.assertTrue(puerta("d70", "201111", "nac27", "27")["excepcion_d70"])
        self.assertEqual(puerta("d70", "201111", "nac27", "01")["estado"], "FAIL")  # otra provincia: tope 0,1 %
        self.assertEqual(puerta("d70_alta", "201111", "nac27", "27")["estado"], "FAIL")  # por encima de lo documentado

    def test_contraste_fuera_de_tolerancia_falla(self):
        p = puerta("fuera_tol", "201911", "nac01", "01")
        self.assertEqual((p["estado"], p["contraste_boe"]["ok"]), ("FAIL", False))
        self.assertEqual(p["contraste_boe"]["motivo"], "DEFECTO_SOBRE_TOLERANCIA")

    def test_espejo_no_supera_a_la_oficial(self):
        self.assertEqual(puerta("supera", "201911", "nac01", "01")["contraste_boe"]["motivo"], "ESPEJO_SUPERA_BOE")

    def test_sin_csv_boe_falla_cerrado(self):
        p = puerta("sin_csv", "201512", "nac01", "01")
        self.assertEqual((p["estado"], p["contraste_boe"]["motivo"]), ("FAIL", "SIN_CSV_BOE"))

    def test_cobertura_parcial_falla_y_completa_pasa(self):
        # el BOE trae AAA, BBB y CCC; el espejo "pass" no trae CCC → sin homologar → falla; "cobertura_completa" sí → pasa
        cob = FX / "raiz_cobertura"
        c = hc.contraste_boe("201911", "01", FX / "pass/espejo.json", cob)
        self.assertEqual((c["ok"], c["motivo"], c["sin_homologar"]), (False, "PARTIDOS_SIN_HOMOLOGAR", ["CCC"]))
        c = hc.contraste_boe("201911", "01", FX / "cobertura_completa/espejo.json", cob)
        self.assertEqual((c["ok"], c["comparados"], c["sin_homologar"]), (True, 3, []))
        self.assertIn("NO equivale al total provincial", c["metodo"])
        p = hc.puerta_json("nac01", "201911", "2023", 0, None, FX / "pass", None, "01", cob, FX / "pass/espejo.json")
        self.assertEqual(p["estado"], "FAIL")

    def test_m07_pass_sin_source_votes_falla(self):
        self.assertEqual(puerta("sin_source", "201911", "nac01", "01")["estado"], "FAIL")

    def test_sin_reconciliacion_falla(self):
        self.assertEqual(puerta("no_existe", "201911", "nac01", "01")["estado"], "FAIL")

    def test_sin_espejo_o_sin_partidos_comparables_falla(self):
        c = hc.contraste_boe("201911", "01", FX / "no_existe/espejo.json", RAIZ)
        self.assertEqual((c["ok"], c["motivo"]), (False, "SIN_DATOS_ESPEJO"))
        c = hc.contraste_boe("201911", "99", FX / "pass/espejo.json", RAIZ)
        self.assertEqual((c["ok"], c["motivo"]), (False, "PROVINCIA_SIN_OFICIAL"))

    def test_m07_con_error_falla(self):
        self.assertEqual(puerta("pass", "201911", "nac01", "01", ra=1)["estado"], "FAIL")


if __name__ == "__main__":
    unittest.main()
