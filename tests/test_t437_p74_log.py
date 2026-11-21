# -*- coding: utf-8 -*-
"""T-437: P74 Listar imprime el inventario en el log (grupo ::group::); el resto de P70 no cambia (control contra la copia 1.1.4)."""
import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/p70-archivo.yml"
ANT = ROOT / "tests/fixtures/t437_p70-archivo_1.1.4.yml"  # copia congelada (en CI no hay legacy/)


def carga(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


class P74Log(unittest.TestCase):
    def setUp(self):
        self.w, self.a = carga(WF), carga(ANT)
        self.j, self.ja = self.w["jobs"]["listar"], self.a["jobs"]["listar"]

    def test_paso_de_impresion(self):
        paso = self.j["steps"][-1]
        self.assertEqual("Imprimir el inventario en el log", paso["name"])
        self.assertEqual("Conservar el inventario de R2", self.j["steps"][-2]["name"])
        run = paso["run"]
        self.assertLess(run.index("::group::"), run.index("cat salida_p74/inventario_r2.csv"))
        self.assertLess(run.index("cat salida_p74/inventario_r2.csv"), run.index("::endgroup::"))
        for prohibido in ("rm ", "delete", "put-object", "s3 ", "aws ", "git push", "secrets."):
            self.assertNotIn(prohibido, run)
        self.assertNotIn("env", paso)

    def test_resto_del_workflow_no_cambia(self):
        self.assertEqual(self.a["on"] if "on" in self.a else self.a[True], self.w["on"] if "on" in self.w else self.w[True])
        self.assertEqual(self.a.get("permissions"), self.w.get("permissions"))
        for n in self.a["jobs"]:
            if n != "listar":
                self.assertEqual(self.a["jobs"][n], self.w["jobs"][n], n)
        self.assertEqual(set(self.a["jobs"]), set(self.w["jobs"]))
        self.assertEqual({k: v for k, v in self.ja.items() if k != "steps"}, {k: v for k, v in self.j.items() if k != "steps"})
        self.assertEqual(self.ja["steps"], self.j["steps"][:-1])  # los pasos anteriores, idénticos
        self.assertEqual({"contents": "read"}, self.j["permissions"])

    def test_control_negativo(self):
        self.assertNotEqual(self.ja["steps"], self.j["steps"])
        self.assertTrue(hashlib.sha256(ANT.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
