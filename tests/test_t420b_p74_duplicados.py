# -*- coding: utf-8 -*-
"""T-420b: P74 Listar pasa `--duplicados --json` y sube el JSON; el resto de P70 no cambia (control contra la copia 1.1.1)."""
import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/p70-archivo.yml"
ANT = ROOT / "tests/fixtures/t420b_workflows/p70-archivo_1.1.1.yml"  # copia congelada (en CI no hay legacy/)
HUELLA = "43b9f2a93dabc013723515cd6c6831e99e40c8cf7bf0ff5331932b9d858cb2d3"


def carga(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


class P74Duplicados(unittest.TestCase):
    def setUp(self):
        self.w = carga(WF)
        self.j = self.w["jobs"]["listar"]

    def test_llamada_y_artefacto(self):
        run = "\n".join(s.get("run", "") for s in self.j["steps"])
        self.assertIn("python3 herramientas/listar_r2.py --duplicados --json salida_p74/duplicados_r2.json", run)
        subida = [s for s in self.j["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact@")]
        self.assertEqual(1, len(subida))
        self.assertEqual("p74-duplicados-${{ github.run_id }}", subida[0]["with"]["name"])
        self.assertEqual("salida_p74/duplicados_r2.json", subida[0]["with"]["path"])
        self.assertEqual({"contents": "read"}, self.j["permissions"])
        self.assertNotIn("concurrency", self.j)
        for prohibido in ("rm ", "delete", "put-object", "s3 cp", "git push", "--ejecutar"):
            self.assertNotIn(prohibido, run)

    def test_resto_del_workflow_no_cambia(self):
        self.assertEqual(HUELLA, hashlib.sha256(ANT.read_bytes()).hexdigest())
        a = carga(ANT)
        self.assertEqual(a["on"] if "on" in a else a[True], self.w["on"] if "on" in self.w else self.w[True])
        self.assertEqual(a.get("permissions"), self.w.get("permissions"))
        self.assertEqual(set(a["jobs"]), set(self.w["jobs"]))
        for n in a["jobs"]:
            if n != "listar":
                self.assertEqual(a["jobs"][n], self.w["jobs"][n], n)
        self.assertEqual({k: v for k, v in a["jobs"]["listar"].items() if k != "steps"},
                         {k: v for k, v in self.j.items() if k != "steps"})
        self.assertEqual(a["jobs"]["listar"]["steps"][0], self.j["steps"][0])

    def test_control_negativo(self):
        j = carga(WF)
        j["jobs"]["archivar_r2"]["timeout-minutes"] = 1
        self.assertNotEqual(carga(WF)["jobs"]["archivar_r2"], j["jobs"]["archivar_r2"])


if __name__ == "__main__":
    unittest.main()
