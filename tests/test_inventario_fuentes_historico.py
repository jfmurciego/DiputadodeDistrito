#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del inventario de fuentes del histórico (T-81)
VERSIÓN: 1.0.0 · FECHA: 2026-11-07 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: raíz sintética con valores escritos a mano; comprueba sha256, cobertura, Infoelectoral solo en 2023-07 y contraste.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import inventario_fuentes_historico as inv  # noqa: E402

H = "a" * 64


class Inventario(unittest.TestCase):
    def raiz(self, tmp):
        (tmp / "orchestracion").mkdir()
        (tmp / "configuracion").mkdir()
        man = {"copia_r2_prefijo": "fuentes/x/",
               "elecciones": [{"clave": "201111", "seccionado": 2012}, {"clave": "202307", "seccionado": 2024}],
               "contraste": {"202307": {"comparadas": 3, "defecto_max": 0.05, "errores": []}},
               "ficheros": {"data/201111/sekzioa/22.json": {"bytes": 5, "sha256": H},
                            "geo/sekzioak/2012/22.json": {"bytes": 6, "sha256": "b" * 64},
                            "data/202307/sekzioa/22.json": {"bytes": 7, "sha256": "c" * 64}}}
        (tmp / "orchestracion/fuente_nazioenbehatokia.json").write_text(json.dumps(man))
        (tmp / "configuracion/contratos_infoelectoral.yaml").write_text(
            "contracts:\n  a:\n    province: '22'\n    election_date: '2023-07-23'\n    source_sha256: " + H +
            "\n    source_bytes: 9\n    mirror: {release_tag: r, asset: z}\n")
        return tmp

    def test_inventario(self):
        with tempfile.TemporaryDirectory() as t:
            d = inv.construir(self.raiz(Path(t)))["elecciones"]
        p11, p23 = d["201111"]["provincias"]["22"], d["202307"]["provincias"]["22"]
        self.assertEqual(p11["nazioenbehatokia"]["datos"]["sha256"], H)
        self.assertTrue(p11["cobertura"]["provincia"])
        self.assertEqual(p11["infoelectoral"]["estado"], "no_adquirida")
        self.assertIsNone(d["201111"]["contraste"])
        self.assertEqual(p23["infoelectoral"]["sha256"], H)
        self.assertFalse(p23["cobertura"]["provincia"])  # falta la geometría
        self.assertEqual(d["202307"]["contraste"]["comparadas"], 3)
        self.assertEqual(d["202307"]["fecha"], "2023-07-23")

    def test_real_al_dia(self):
        self.assertEqual(inv.main(["--comprobar"]), 0)


if __name__ == "__main__":
    unittest.main()
