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


if __name__ == "__main__":
    unittest.main()
