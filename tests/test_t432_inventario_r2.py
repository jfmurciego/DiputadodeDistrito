# -*- coding: utf-8 -*-
"""T-432: `listar_r2.py --inventario` (bucket simulado vía `aws`) y P74 Listar; el resto de P70 no cambia (control contra la copia 1.1.3)."""
import copy
import csv
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import listar_r2  # noqa: E402

WF = ROOT / ".github/workflows/p70-archivo.yml"
ANT = ROOT / "tests/fixtures/t432_p70-archivo_1.1.3.yml"
HUELLA = hashlib.sha256(ANT.read_bytes()).hexdigest()
BUCKET = [
    {"Key": "b/z.bin", "Size": 2_500_000, "ETag": '"aa-3"', "LastModified": "2026-11-02T10:00:00+00:00"},
    {"Key": "a/x.json", "Size": 999, "ETag": '"bb"', "LastModified": "2026-11-01T09:30:00+00:00"},
    {"Key": "raiz.txt", "Size": 1_000, "ETag": '"cc"', "LastModified": "2026-11-03T00:00:00+00:00"},
]


def aws_simulado(cmd, **kw):
    return SimpleNamespace(returncode=0, stdout=json.dumps(BUCKET), stderr="")


class Inventario(unittest.TestCase):
    def ejecuta(self, *args):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "c"}), \
                mock.patch("subprocess.run", side_effect=aws_simulado) as run, redirect_stdout(io.StringIO()) as out:
            ruta = os.path.join(d, "inv.csv")
            rc = listar_r2.main([*args, "--inventario", ruta] if args != ("sin",) else [])
            filas = list(csv.reader(open(ruta, encoding="utf-8"))) if os.path.exists(ruta) else None
        return rc, filas, out.getvalue(), run

    def test_csv_ordenado_con_total(self):
        rc, f, _, run = self.ejecuta("--duplicados")
        self.assertEqual(0, rc)
        self.assertEqual(["clave", "bytes", "tamano_legible", "ultima_modificacion", "etag"], f[0])
        self.assertEqual(["a/x.json", "b/z.bin", "raiz.txt"], [x[0] for x in f[1:-1]])
        self.assertEqual(["a/x.json", "999", "999 B", "2026-11-01T09:30:00+00:00", "bb"], f[1])
        self.assertEqual(["b/z.bin", "2500000", "2.50 MB", "2026-11-02T10:00:00+00:00", "aa-3"], f[2])
        self.assertEqual(["TOTAL (3 objetos)", "2501999", "2.50 MB", "", ""], f[-1])
        self.assertIn("LastModified", " ".join(run.call_args_list[0].args[0]))
        self.assertEqual(1, run.call_count)  # un solo listado, solo lectura

    def test_bucket_vacio(self):
        with tempfile.TemporaryDirectory() as d:
            ruta = os.path.join(d, "v.csv")
            self.assertEqual(0, listar_r2.escribir_inventario([], ruta))
            self.assertEqual(["TOTAL (0 objetos)", "0", "0 B", "", ""], list(csv.reader(open(ruta)))[-1])

    def test_sin_bandera_no_escribe(self):
        rc, f, out, _ = self.ejecuta("sin")
        self.assertEqual(0, rc)
        self.assertIsNone(f)
        self.assertNotIn("Inventario:", out)


def carga(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


class P74Inventario(unittest.TestCase):
    def setUp(self):
        self.w = carga(WF)
        self.j = self.w["jobs"]["listar"]

    def test_llamada_y_artefactos(self):
        run = "\n".join(s.get("run", "") for s in self.j["steps"])
        self.assertIn("--duplicados --json salida_p74/duplicados_r2.json --inventario salida_p74/inventario_r2.csv", run)
        subidas = {s["with"]["name"]: s["with"]["path"] for s in self.j["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact@")}
        self.assertEqual({"p74-duplicados-${{ github.run_id }}": "salida_p74/duplicados_r2.json",
                          "p74-inventario-${{ github.run_id }}": "salida_p74/inventario_r2.csv"}, subidas)

    def test_resto_del_workflow_no_cambia(self):
        a = carga(ANT)
        self.assertEqual(a["on"] if "on" in a else a[True], self.w["on"] if "on" in self.w else self.w[True])
        self.assertEqual(a.get("permissions"), self.w.get("permissions"))
        self.assertEqual(set(a["jobs"]), set(self.w["jobs"]))
        for n in a["jobs"]:
            if n != "listar":
                self.assertEqual(a["jobs"][n], self.w["jobs"][n], n)
        la = a["jobs"]["listar"]
        self.assertEqual({k: v for k, v in la.items() if k != "steps"}, {k: v for k, v in self.j.items() if k != "steps"})
        self.assertEqual({"contents": "read"}, self.j["permissions"])
        self.assertNotIn("concurrency", self.j)
        self.assertEqual(la["steps"][0], self.j["steps"][0])
        self.assertEqual(la["steps"][2], self.j["steps"][2])  # subida de duplicados intacta
        antes = copy.deepcopy(la["steps"][1])
        antes["run"] = antes["run"].replace("duplicados_r2.json\n", "duplicados_r2.json --inventario salida_p74/inventario_r2.csv\n")
        self.assertEqual(antes, self.j["steps"][1])

    def test_control_negativo(self):
        a = carga(ANT)
        a["jobs"]["archivar_r2"]["timeout-minutes"] = 1
        self.assertNotEqual(a["jobs"]["archivar_r2"], self.w["jobs"]["archivar_r2"])


if __name__ == "__main__":
    unittest.main()
