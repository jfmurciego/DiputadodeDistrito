#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de resultados ligeros (T-53)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: M08 sintético de dos territorios: CSV por distrito, manifiesto con sha256, idempotencia byte a byte, sha256
  de origen erróneo y lectura de ganadores desde el CSV.
"""
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import resultados_ligeros as rl  # noqa: E402


def m08(ganadores):
    feats = [{"properties": {"district_id": str(i), "district_pop": 1000 + i, "total_votes": 500,
                             "winner_party": g, "winner_votes": 200, "winner_share": 0.4}} for i, g in enumerate(ganadores)]
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w") as z:
        z.writestr("x_m08_distritos_resultados.geojson", json.dumps({"features": feats[::-1]}))
    return b.getvalue()


class Ligeros(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.zips = self.d / "zips"
        self.zips.mkdir()
        prods = []
        for t, run, gan in (("nac42", "10", ["PP", "PSOE"]), ("nac42", "20", ["PP", "PP"]),
                            ("nac44", "5", ["PSOE"])):
            datos = m08(gan)
            (self.zips / f"{t}_{run}.zip").write_bytes(datos)
            prods.append({"kind": "canonical_m08", "territory_id": t, "run_id": run, "blob_sha": f"b{run}",
                          "sha256": rl.sha256(datos)})
        prods.append({"kind": "canonical_m06", "territory_id": "nac42", "run_id": "99"})
        self.reg = self.d / "reg.json"
        self.reg.write_text(json.dumps({"products": prods}))
        self.out = self.d / "out"

    def gen(self):
        return rl.generar(self.out, self.reg, m08_dir=self.zips)

    def test_csv_y_manifiesto(self):
        man = self.gen()
        self.assertEqual(sorted(man["territorios"]), ["nac42", "nac44"])
        self.assertEqual(man["territorios"]["nac42"]["run_id"], "20")
        lineas = (self.out / "congreso_soria.csv").read_text().splitlines()
        self.assertEqual(lineas[0], ",".join(rl.CABECERA))
        self.assertEqual(lineas[1], "0,1000,500,PP,200,40.0000")
        for t, m in man["territorios"].items():
            self.assertEqual(m["sha256_csv"], rl.sha256((self.out / f"{t}.csv").read_bytes()))

    def test_idempotente(self):
        self.gen()
        a = {p.name: p.read_bytes() for p in self.out.iterdir()}
        self.gen()
        self.assertEqual(a, {p.name: p.read_bytes() for p in self.out.iterdir()})

    def test_conserva_claves_y_ficheros_ajenos(self):
        # T-114: «partidos_runs» y contraste_2023.csv los escriben otras herramientas; no se pierden al regenerar.
        self.gen()
        man = json.loads((self.out / "MANIFEST.json").read_text())
        man["partidos"] = {"nac42": {"x": 1}}
        man["partidos_runs"] = {"congreso_soria/10": {"run_territorial": "7"}}
        (self.out / "MANIFEST.json").write_text(json.dumps(man))
        (self.out / "contraste_2023.csv").write_text("a\n")
        (self.out / "congreso_soria_partidos.csv").write_text("b\n")
        reg = json.loads(self.reg.read_text())
        reg["products"] = [p for p in reg["products"] if p.get("territory_id") != "nac44"]
        self.reg.write_text(json.dumps(reg))
        nuevo = self.gen()
        self.assertEqual({"nac42": {"x": 1}}, nuevo["partidos"])
        self.assertEqual({"congreso_soria/10": {"run_territorial": "7"}}, nuevo["partidos_runs"])
        self.assertTrue((self.out / "contraste_2023.csv").exists())
        self.assertTrue((self.out / "congreso_soria_partidos.csv").exists())
        self.assertFalse((self.out / "congreso_teruel.csv").exists())  # ya no vigente

    def test_sha_erroneo(self):
        (self.zips / "congreso_teruel_5.zip").write_bytes(m08(["XX"]))
        with self.assertRaises(ValueError):
            self.gen()

    def test_ganadores_desde_csv(self):
        self.gen()
        p = rl.vigentes(self.reg)["nac42"]
        self.assertEqual(rl.ganadores(self.out, "nac42", p), ["PP", "PP"])
        self.assertIsNone(rl.ganadores(self.out, "nac42", {**p, "blob_sha": "otro"}))
        (self.out / "congreso_soria.csv").write_text("alterado")
        self.assertIsNone(rl.ganadores(self.out, "nac42", p))


if __name__ == "__main__":
    unittest.main()
