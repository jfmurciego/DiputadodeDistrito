#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de duplicidades en R2 (T-420)
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: bucket simulado; md5 simple verificado, multiparte solo por sha256 de metadatos, resto no verificable.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "herramientas"))
import listar_r2 as lr  # noqa: E402


def o(k, s, e):
    return {"Key": k, "Size": s, "ETag": f'"{e}"'}


BUCKET = [
    o("arc-e/paquetes-p10/a.zip", 100, "aaa"), o("arc-e/paquetes-p10/b.zip", 100, "aaa"),      # md5 igual
    o("zz-a/x.zip", 50, "aaa"),                                                              # mismo etag, otro tamaño: no es grupo
    o("arc-e/m1.zip", 1000, "bbb-3"), o("zz-b/m1.zip", 1000, "bbb-3"),                    # multiparte no metadato
    o("arc-e/fuentes/INDEX.json", 10, "ccc-2"), o("arc-p/INDEX.json", 10, "ccc-2"),           # multiparte metadato
    o("arc-e/archivo_r2.json", 20, "ddd-2"), o("zz-c/archivo_r2.json", 20, "ddd-2"),     # multiparte metadato distinto
    o("solo/uno.zip", 5, "eee"),
]


class Duplicados(unittest.TestCase):
    def test_sin_verificar_multiparte(self):
        d = lr.duplicados(BUCKET)
        est = {g["claves"][0]: g["estado"] for g in d["grupos"]}
        self.assertEqual(d["grupos_total"], 4)
        self.assertEqual(est["arc-e/paquetes-p10/a.zip"], "verificado_md5")
        self.assertEqual(est["arc-e/m1.zip"], "no_verificable")
        self.assertEqual(d["bytes_recuperables"], 100)
        self.assertEqual(d["bytes_no_verificables"], 1000 + 10 + 20)
        self.assertEqual(d["sobran_total"], 4)

    def test_verificar_sha256_de_metadatos(self):
        huella = {"arc-e/fuentes/INDEX.json": "h1", "arc-p/INDEX.json": "h1",
                  "arc-e/archivo_r2.json": "h2", "zz-c/archivo_r2.json": "h3"}
        d = lr.duplicados(BUCKET, huella.__getitem__)
        est = {g["claves"][0]: g["estado"] for g in d["grupos"]}
        self.assertEqual(est["arc-e/fuentes/INDEX.json"], "verificado_sha256")
        self.assertEqual(est["arc-e/archivo_r2.json"], "discrepante")
        self.assertEqual(est["arc-e/m1.zip"], "no_verificable")  # no es metadato: nunca se asume
        self.assertEqual(d["bytes_recuperables"], 110)

    def test_arc_e_primero_y_claves_fuera(self):
        d = lr.duplicados(BUCKET)
        self.assertTrue(all("arc-e" in g["carpetas"] for g in d["grupos"][:3]))
        g = [g for g in d["grupos"] if "zz-b" in g["carpetas"]][0]
        self.assertIn("zz-b/m1.zip", g["claves"])
        self.assertIn("zz-b", d["por_carpeta"])

    def test_resumen_legible_y_sin_duplicados(self):
        self.assertIn("4 grupos", lr.resumen_duplicados(lr.duplicados(BUCKET)))
        self.assertEqual(lr.duplicados([o("a", 1, "x")])["grupos_total"], 0)


if __name__ == "__main__":
    unittest.main()
