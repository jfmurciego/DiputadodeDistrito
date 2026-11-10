# -*- coding: utf-8 -*-
"""PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-08 · ANTERIOR: ninguna (fichero nuevo)
Tests de T-112: candidaturas proclamadas 2026 (BOE-A-2026-23103) y su homologación de siglas."""
import csv
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import homologacion_candidaturas_2026 as h  # noqa: E402


def _csv(ruta):
    with (ROOT / ruta).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(l for l in fh if not l.startswith("#")))


class Candidaturas2026(unittest.TestCase):
    def test_cada_candidatura_proclamada_llena_los_escanos_del_rd(self):
        esc = {r["codigo"]: int(r["escanos_2026"]) for r in _csv("configuracion/escanos_oficiales_congreso_2026.csv")}
        c = _csv(h.CAND)
        self.assertEqual({r["codigo"] for r in c}, set(esc))  # 52 circunscripciones
        for r in c:
            if r["proclamada"] == "SI":
                self.assertEqual(int(r["candidatos"]), esc[r["codigo"]], (r["provincia"], r["siglas"]))

    def test_cifras_del_boe(self):
        c = _csv(h.CAND)
        self.assertEqual(len(c), 551)
        self.assertEqual(sum(r["proclamada"] == "NO" for r in c), 21)
        self.assertEqual(sum(r["siglas"] == "VOX" for r in c), 51)  # BOE: 51 listas de VOX
        self.assertEqual({r["siglas"] for r in c if r["codigo"] == "31"} & {"EH BILDU", "EH BILDU-ERC"}, {"EH BILDU"})

    def test_sha256_del_csv(self):
        import json
        meta = json.loads((ROOT / h.CAND_JSON).read_text(encoding="utf-8"))
        self.assertEqual(meta["sha256_csv"], hashlib.sha256((ROOT / h.CAND).read_bytes()).hexdigest())


class Homologacion2026(unittest.TestCase):
    def test_familias_d20(self):
        t = {(r["sigla_boe"]): (r["partido_homologado"], r["nivel_certeza"]) for r in _csv(h.SALIDA)}
        self.assertEqual(t["PODEMOS"], ("Podemos–Sumar", "DECIDIDA"))
        self.assertEqual(t["JxCat"][0], "CiU–Junts")
        self.assertEqual(t["UPN-PP"], ("UPN y coaliciones", "DECIDIDA"))
        self.assertEqual(t["CHA-IU-MS-FRENTE AMPLIO"][0], "CHA-IU")

    def test_baja_no_se_decide_y_es_corta(self):
        bajas = {r["sigla_boe"] for r in _csv(h.SALIDA) if r["nivel_certeza"] == "BAJA"}
        self.assertEqual(bajas, {"FA", "FRENTE AMPLIO - FRONTE AMPLA", "FRENTE AMPLIO-FRONTE AMPLA",
                                 "FRENTE AMPLIO-FRONTE ZABALA", "COMUNS-FRONT AMPLI", "ARAMÉS-EU-MS",
                                 "COMPROMIS-EUPV-PODEM-ERPV", "NC-BC, PODEMOS, IU, SUMAR", "CNV", "PAZ,CASA Y TRABAJO"})

    def test_tabla_reproducible(self):
        self.assertEqual(h.main(["comprobar"]), 0)


class SiglasDelZip(unittest.TestCase):
    """T-200: siglas de Interior (ENSAYO T-197, ZIP 2023) frente a las reglas y a las candidaturas BOE."""

    def test_variantes_de_interior_sin_regla_fallan(self):
        sin = h.siglas_sin_regla(["PSE-EE (PSOE)", "SUMAR - ECP", "JxCAT - JUNTS", "U.P.N."], "48")
        self.assertEqual(sin, ["JxCAT - JUNTS", "PSE-EE (PSOE)", "SUMAR - ECP", "U.P.N."])
        with self.assertRaisesRegex(ValueError, "SIGLAS_SIN_REGLA"):
            h.exigir_siglas_zip(["PSE-EE (PSOE)"], "48")

    def test_candidatura_boe_de_la_provincia_pasa(self):
        # La Coruña (15): PACMA es candidatura BOE; en Soria (42) no.
        self.assertEqual(h.siglas_sin_regla(["VOX", "PACMA"], "15"), [])
        self.assertEqual(h.siglas_sin_regla(["PACMA"], "42"), ["PACMA"])

    def test_tabla_interior_de_la_eleccion(self):
        # reglas_generales.json["interior"]["202307"]["JUNTS"] = «CiU–Junts» (literal del fichero, no recalculado)
        self.assertEqual(h.siglas_sin_regla(["JUNTS"], "08", eleccion="202307"), [])
        self.assertEqual(h.siglas_sin_regla(["JUNTS"], "08"), ["JUNTS"])  # 202611 aún sin tabla de Interior

    def test_regla_2026_explicita_gana(self):
        import json
        reglas = json.loads((ROOT / h.REGLAS).read_text(encoding="utf-8"))
        self.assertEqual(h.resolver_zip(reglas, {}, "PODEMOS", "08", {}), ("Podemos–Sumar", "DECIDIDA", "PODEMOS"))

    def test_regla_2026_pasa_por_exigir(self):
        h.exigir_siglas_zip(["PODEMOS", "JxCat", "UPN-PP"], "08")  # sin error

    def test_otra_eleccion_no_usa_reglas_ni_candidaturas_2026(self):
        # PACMA es candidatura BOE de La Coruña (15) en 2026, pero no vale para 2023
        self.assertEqual(h.siglas_sin_regla(["PACMA"], "15"), [])
        self.assertEqual(h.siglas_sin_regla(["PACMA", "PODEMOS"], "15", eleccion="202307"), ["PACMA", "PODEMOS"])


if __name__ == "__main__":
    unittest.main()
