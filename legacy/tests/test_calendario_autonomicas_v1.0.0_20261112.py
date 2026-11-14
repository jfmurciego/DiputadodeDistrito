#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del calendario de autonómicas (T-121)
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: valores escritos a mano desde la tabla pública del Observatorio (iturriak.html); el CSV real debe estar al día.
"""
import csv
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import calendario_autonomicas as cal  # noqa: E402


def filas():
    with (ROOT / cal.SALIDA).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


class Parseo(unittest.TestCase):
    def test_fila_de_tabla(self):
        h = ('<tr><th>Galiza</th><td class="data">octubre de 2012</td><td><a href="https://x/y" rel="n">Xunta</a></td>'
             '<td>por mesa</td><td>completos</td><td>la misma fuente</td></tr>')
        r = cal.parsear_iturriak(h)
        self.assertEqual(r, [{"etiqueta": "Galiza", "mes": "201210", "proveedor": "Xunta", "url": "https://x/y",
                              "granularidad": "por mesa", "completitud": "completos", "verificacion": ""}])


class CalendarioReal(unittest.TestCase):
    def meses(self, c):
        return [f["mes"] for f in filas() if f["comunidad"] == c]

    def test_al_dia(self):
        self.assertEqual(cal.main(["comprobar"]), 0)

    def test_sha256_de_las_fuentes(self):
        for f in filas():
            h = [hashlib.sha256((ROOT / cal.FUENTE_DIR / n).read_bytes()).hexdigest() for n in ("index.json", "iturriak.html")]
            self.assertEqual(f["fuente_sha256"], " ; ".join(h))

    def test_galicia_calendario_propio(self):
        self.assertEqual(self.meses("galicia"), ["2009-03", "2012-10", "2016-09", "2020-07", "2024-02"])
        g = {f["mes"]: f for f in filas() if f["comunidad"] == "galicia"}
        self.assertEqual(g["2012-10"]["duracion_meses"], "47")
        self.assertEqual(g["2016-09"]["duracion_meses"], "46")
        self.assertEqual(g["2020-07"]["duracion_meses"], "43")
        self.assertEqual(g["2024-02"]["vigente"], "si")
        self.assertEqual(g["2024-02"]["fecha"], "2024-02-18")

    def test_castilla_y_leon_adelantos(self):
        self.assertEqual(self.meses("castilla_y_leon"), ["2011-05", "2015-05", "2019-05", "2022-02", "2026-03"])

    def test_cantabria_2011_sin_datos(self):
        c = {f["mes"]: f for f in filas() if f["comunidad"] == "cantabria"}
        self.assertEqual(c["2011-05"]["completitud"], "sin datos")

    def test_17_comunidades_sin_ceuta_ni_melilla(self):
        ids = {f["comunidad"] for f in filas()}
        self.assertEqual(len(ids), 17)
        for c in cal.SIN_PARLAMENTO:
            self.assertNotIn(c, ids)

    def test_una_vigente_por_comunidad_y_orden(self):
        for c in {f["comunidad"] for f in filas()}:
            fs = [f for f in filas() if f["comunidad"] == c]
            self.assertEqual(sum(f["vigente"] == "si" for f in fs), 1, c)
            self.assertEqual(fs[-1]["vigente"], "si", c)


if __name__ == "__main__":
    unittest.main()
