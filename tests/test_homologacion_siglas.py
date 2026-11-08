#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la homologación de siglas de las generales (T-97)
VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: provincia sintética en el formato compacto (valores escritos a mano): precedencia sigla > familia > identidad,
  votos nulos fuera, sha256 contra el manifiesto, cobertura de Interior; y la tabla versionada pasa `comprobar`
  con los casos acordados (PP-EU → PP; PSC y PSdeG → PSOE; UPN-PP y NA+ en Navarra → UPN, certeza BAJA).
"""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import homologacion_siglas as hs  # noqa: E402

REGLAS = {
    "familias": {"a4": {"homologado": "PSOE", "certeza": "ALTA"},
                 "a5": {"homologado": "PP", "certeza": "ALTA"},
                 "a1": {"homologado": "SUMAR", "certeza": "MEDIA", "por_eleccion": {"201512": {"certeza": "BAJA"}}}},
    "siglas": [
        {"id": "X", "siglas": ["PP-EU"], "elecciones": "*", "provincias": "*", "homologado": "PP", "certeza": "MEDIA"},
        {"id": "N", "siglas": ["UPN-PP"], "elecciones": "*", "provincias": ["31"], "homologado": "UPN", "certeza": "BAJA"},
        {"id": "N15", "siglas": ["UPN-PP"], "elecciones": ["201512"], "provincias": ["31"], "homologado": "UPN", "certeza": "MEDIA"},
    ],
    "interior": {"201911": {"PSC": "PSOE"}},
}
DOC = {"s": ["PSOE", "PSC-PSOE", "PP-EU", "NUEVO", "CERO"], "f": ["a4", "a4", "a5", "NUEVO", "CERO"], "k": [], "b": [],
       "r": {"1": [10, 9, 9, [[0, 5], [1, 2], [2, 1], [3, 1], [4, 0]]]}}


class Resolver(unittest.TestCase):
    def test_precedencia(self):
        r = hs.resolver
        self.assertEqual(r(REGLAS, "201111", "06", "PP-EU", "a5"), ("PP", "MEDIA", "SIGLA:X"))
        self.assertEqual(r(REGLAS, "201111", "06", "PSC-PSOE", "a4"), ("PSOE", "ALTA", "FAMILIA:a4"))
        self.assertEqual(r(REGLAS, "201111", "06", "NUEVO", "NUEVO"), ("NUEVO", "ALTA", "IDENTIDAD"))
        self.assertEqual(r(REGLAS, "201111", "31", "UPN-PP", "a5")[1:], ("BAJA", "SIGLA:N"))
        self.assertEqual(r(REGLAS, "201512", "31", "UPN-PP", "a5")[1:], ("MEDIA", "SIGLA:N15"))  # más específica
        self.assertEqual(r(REGLAS, "201111", "06", "UPN-PP", "a5")[0], "PP")  # fuera de Navarra, la familia
        self.assertEqual(r(REGLAS, "201512", "08", "PODEMOS", "a1")[1], "BAJA")
        self.assertEqual(r(REGLAS, "201606", "08", "PODEMOS", "a1")[1], "MEDIA")

    def test_familia_sin_regla_falla(self):
        with self.assertRaises(KeyError):
            hs.resolver(REGLAS, "201111", "06", "ZZ", "a99")


class Construir(unittest.TestCase):
    def test_filas_sha_e_interior(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            ruta = "data/201911/sekzioa/22.json"
            (d / ruta).parent.mkdir(parents=True)
            raw = json.dumps(DOC).encode()
            (d / ruta).write_bytes(raw)
            man = {"ficheros": {ruta: {"sha256": hashlib.sha256(raw).hexdigest()}}}
            interior = {"201911": {"22": {"PSC", "PP"}}}
            filas, err = hs.construir_filas(d, REGLAS, man, interior)
            self.assertEqual(err, [])
            por = {f["sigla_fuente"]: f for f in filas}
            self.assertEqual(set(por), {"PSOE", "PSC-PSOE", "PP-EU", "NUEVO"})  # CERO tiene 0 votos
            self.assertEqual(por["PSC-PSOE"]["partido_homologado"], "PSOE")
            self.assertEqual(por["PSC-PSOE"]["interior"], "COINCIDE")
            self.assertEqual(por["PP-EU"]["interior"], "COINCIDE")
            self.assertEqual(por["NUEVO"]["interior"], "SIN_ESCAÑO_EN_INTERIOR")
            self.assertEqual(por["PP-EU"]["sha256_fuente"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(hs.cobertura_interior(REGLAS, interior, filas), [])
            interior["201911"]["22"].add("OTRO")
            self.assertIn("OTRO", hs.cobertura_interior(REGLAS, interior, filas)[0])
            man["ficheros"][ruta]["sha256"] = "0" * 64
            self.assertIn("sha256 distinto", hs.construir_filas(d, REGLAS, man, interior)[1][0])


class TablaVersionada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / hs.SALIDA_CSV).open(encoding="utf-8", newline="") as fh:
            cls.filas = list(csv.DictReader(fh))

    def test_comprobar_sin_errores(self):
        self.assertEqual(hs.comprobar(), [])

    def test_casos_acordados(self):
        def una(e, p, s):
            x = [f for f in self.filas if (f["eleccion"], f["provincia"], f["sigla_fuente"]) == (e, p, s)]
            self.assertEqual(len(x), 1, (e, p, s))
            return x[0]
        self.assertEqual(una("201111", "06", "PP-EU")["partido_homologado"], "PP")
        self.assertEqual(una("202307", "08", "PSC")["partido_homologado"], "PSOE")
        self.assertEqual(una("201911", "27", "PSdeG-PSOE")["partido_homologado"], "PSOE")
        for e, s in (("201111", "UPN-PP"), ("201904", "NA+")):
            f = una(e, "31", s)
            self.assertEqual((f["partido_homologado"], f["nivel_certeza"]), ("UPN", "BAJA"))
        self.assertEqual(una("202307", "31", "U.P.N.")["partido_homologado"], "UPN")
        self.assertEqual(una("201911", "51", "MDyC")["partido_homologado"], "MDyC")


if __name__ == "__main__":
    unittest.main()
