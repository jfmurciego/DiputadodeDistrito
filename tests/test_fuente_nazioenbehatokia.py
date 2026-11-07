#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la fuente secundaria nazioenbehatokia (T-89)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: provincia sintética en el formato compacto (valores escritos a mano): lector, contraste con la oficial
  (defecto por CERA = AVISO/sin error; superarla = ERROR; sigla distinta = sin_homologar), espejo con descarga simulada
  y sha256, y manifiesto versionado.
"""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import fuente_nazioenbehatokia as fn  # noqa: E402
import catalogo_procedencia as cp  # noqa: E402

DOC = {"s": ["PP", "PSOE", "XYZ"], "k": [], "f": [], "b": [],
       "r": {"2200101001": [200, 150, 140, [[0, 70], [1, 50], [2, 20]]],
             "2200201001": [100, 80, 80, [[0, 30], [1, 40], [2, 10]]]}}
INDEX = {"hauteskundeak": [{"k": "202307", "sekzioUrtea": 2024}], "goikoak": {"probintzia": {"22": "02"}}}


class Lector(unittest.TestCase):
    def test_secciones_y_totales(self):
        s = fn.leer_provincia(DOC)
        self.assertEqual(s["2200101001"], {"censo": 200, "votantes": 150, "votos_candidaturas": 140,
                                           "votos": {"PP": 70, "PSOE": 50, "XYZ": 20}})
        self.assertEqual(fn.totales_provincia(DOC), {"PP": 100, "PSOE": 90, "XYZ": 30})


class Contraste(unittest.TestCase):
    def test_defecto_cera_sin_error(self):
        r = fn.contrastar_provincia({"PP": 100, "PSOE": 90}, {"PP": 104, "PSOE": 90, "PSC": 7})
        self.assertEqual(r["errores"], [])
        self.assertEqual(r["sin_homologar"], ["PSC"])
        self.assertEqual(r["comparaciones"]["PP"]["defecto"], round(4 / 104, 5))

    def test_superar_a_la_oficial_es_error(self):
        self.assertEqual(len(fn.contrastar_provincia({"PP": 101}, {"PP": 100})["errores"]), 1)

    def test_defecto_grande_es_aviso(self):
        self.assertEqual(len(fn.contrastar_provincia({"PP": 80}, {"PP": 100})["avisos"]), 1)


class Espejo(unittest.TestCase):
    def test_manifiesto_con_sha256(self):
        cuerpos = {"data/index.json": json.dumps(INDEX).encode(),
                   "data/202307/sekzioa/22.json": json.dumps(DOC).encode(),
                   "geo/sekzioak/2024/22.json": b"{}"}
        with tempfile.TemporaryDirectory() as t:
            m = fn.espejar(Path(t), descargar=lambda u: cuerpos[u[len(fn.BASE):]])
            self.assertEqual(sorted(m["ficheros"]), sorted(cuerpos))
            self.assertEqual(m["ficheros"]["geo/sekzioak/2024/22.json"],
                             {"bytes": 2, "sha256": hashlib.sha256(b"{}").hexdigest()})
            of = Path(t) / "of.csv"
            of.write_text("codigo,provincia,escanos_circunscripcion,partido,votos,escanos\n"
                          "22,Huesca,3,PP,104,2\n22,Huesca,3,PSC,7,0\n", encoding="utf-8")
            c = fn.contrastar(Path(t), raiz=Path("/"), oficiales={"202307": str(of)[1:]})
            self.assertEqual(c["202307"]["errores"], [])
            self.assertEqual(c["202307"]["sin_homologar"], {"PSC": 1})


class Repositorio(unittest.TestCase):
    def test_manifiesto_versionado_y_contraste_sin_errores(self):
        m = json.loads((ROOT / fn.SALIDA).read_text(encoding="utf-8"))
        self.assertEqual(len(m["ficheros"]), 625)  # index + 6 elecciones x 52 provincias x (datos + geo)
        self.assertTrue(all(len(f["sha256"]) == 64 for f in m["ficheros"].values()))
        for v in m["contraste"].values():
            self.assertEqual(v["errores"], [])

    def test_catalogo_incluye_la_fuente(self):
        cat = cp.generar()
        self.assertIn("nazioenbehatokia", cat["fuentes_secundarias"])
        self.assertEqual(cat["resumen"]["errores"], 0)


if __name__ == "__main__":
    unittest.main()
