#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la numeración pública de distritos 1..K (T-135)
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: la función única convierte 0..K-1 -> 1..K y ningún producto público contiene un distrito 0.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import numeracion_publica as n  # noqa: E402


class Funcion(unittest.TestCase):
    def test_conversion(self):
        self.assertEqual([n.numero_publico(i) for i in range(3)], [1, 2, 3])
        self.assertEqual(n.id_interno(1), 0)
        with self.assertRaises(ValueError):
            n.id_interno(0)
        with self.assertRaises(ValueError):
            n.numero_publico(-1)

    def test_csv(self):
        out = n.csv_publico(b"distrito,x\n0,a\n1,b\n").decode()
        self.assertEqual(out, "distrito,x\n1,a\n2,b\n")
        self.assertEqual(n.ceros_en_csv(b"distrito,x\n0,a\n"), 1)
        self.assertEqual(n.ceros_en_csv(out.encode()), 0)


class ProductosPublicos(unittest.TestCase):
    """Cada zona publicada se añade aquí; falla si aparece un distrito 0."""

    def test_datos_abiertos_sin_distrito_cero(self):
        base = ROOT / "datos_abiertos"
        csvs = sorted(base.glob("*/resultados.csv"))
        self.assertTrue(csvs)
        for c in csvs:
            self.assertEqual(n.ceros_en_csv(c.read_bytes()), 0, f"{c}: distrito 0")
            ids = [int(l.split(",")[0]) for l in c.read_text(encoding="utf-8").splitlines()[1:]]
            self.assertEqual(ids, list(range(1, len(ids) + 1)), f"{c}: no es 1..K")
            fichas = sorted(int(re.search(r"distrito-(\d+)", f.name).group(1)) for f in c.parent.glob("distrito-*.html"))
            self.assertEqual(fichas, ids, f"{c.parent.name}: fichas distintas de 1..K")
            self.assertNotIn("Distrito 0", (c.parent / "index.html").read_text(encoding="utf-8"))
        idx = json.loads((base / "INDEX.json").read_text(encoding="utf-8"))
        for t, e in idx["territorios"].items():
            self.assertEqual([d["distrito"] for d in e["distritos"]], list(range(1, e["n_distritos"] + 1)), t)

    def test_generadores_del_visor_usan_la_funcion(self):
        for f in ("generar_rotacion_visor", "generar_territorial_visor", "generar_secciones_visor"):
            self.assertIn("numero_publico", (ROOT / "herramientas" / f"{f}.py").read_text(encoding="utf-8"), f)
        for js in ("visor/v2/v2.js",):
            self.assertNotRegex((ROOT / js).read_text(encoding="utf-8"), r"\.d\s*\)?\s*\+\s*1")


if __name__ == "__main__":
    unittest.main()
