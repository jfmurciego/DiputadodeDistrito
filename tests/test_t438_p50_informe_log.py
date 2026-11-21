# -*- coding: utf-8 -*-
"""T-438: P50 1.2.1 — el informe del depósito en Zenodo sale en el log (`| tee`), sin token; el resto no cambia (copia 1.2.0).

Los pasos de shell se EJECUTAN con un `python3` simulado (no se buscan solo cadenas)."""
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.test_t388_zenodo_deposito import Base, TOKEN

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github/workflows/p50-publicacion-academica.yml"
ANT = ROOT / "tests/fixtures/t438_p50-publicacion-academica_1.2.0.yml"  # copia congelada (en CI no hay legacy/)
INFORME = {"destino": "prueba", "deposito_id": 123, "concepto_nuevo": False, "publicado": True, "doi": "10.5072/zenodo.123",
           "url": "https://sandbox.zenodo.org/records/123", "url_borrador": "https://sandbox.zenodo.org/deposit/123"}


def carga(p):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def paso(wf, nombre):
    return next(s for s in wf["jobs"]["zenodo"]["steps"] if s.get("name", "").startswith(nombre))


class Log(unittest.TestCase):
    def ejecuta(self, nombre, rc):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "bin").mkdir()
            py = d / "bin" / "python3"
            py.write_text(f"#!/bin/bash\ncat <<'J'\n{json.dumps(INFORME, indent=2)}\nJ\nexit {rc}\n")
            py.chmod(py.stat().st_mode | stat.S_IEXEC)
            (d / "zen").mkdir()
            (d / "zen" / "a.tar.gz").write_text("x")
            resumen = d / "resumen.md"
            env = {**os.environ, "PATH": f"{d / 'bin'}:{os.environ['PATH']}", "V": "1.0.0", "TAG": "mapas-v1.0.0",
                   "GITHUB_REPOSITORY": "o/r", "GITHUB_STEP_SUMMARY": str(resumen), "CONCEPTO_NUEVO": "false"}
            p = subprocess.run(["bash", "-c", paso(carga(WF), nombre)["run"]], cwd=d, env=env, capture_output=True, text=True)
            fichero = (d / "informe_zenodo.json").read_text() if (d / "informe_zenodo.json").exists() else ""
        return p, fichero

    def test_informe_en_log_y_en_fichero(self):
        for nombre in ("Depositar en Zenodo (prueba)", "Depositar en Zenodo (real)"):
            p, fichero = self.ejecuta(nombre, 0)
            self.assertEqual(0, p.returncode, p.stderr)
            for clave in ("deposito_id", "doi", "url", "url_borrador"):
                self.assertIn(str(INFORME[clave]), p.stdout, (nombre, clave))
            self.assertEqual(INFORME, json.loads(fichero))  # el fichero que lee el resumen sigue igual

    def test_un_fallo_del_deposito_sigue_fallando(self):
        for nombre in ("Depositar en Zenodo (prueba)", "Depositar en Zenodo (real)"):
            self.assertNotEqual(0, self.ejecuta(nombre, 1)[0].returncode, nombre)

    def test_resto_del_workflow_no_cambia(self):
        a, w = carga(ANT), carga(WF)
        self.assertEqual(a["on"] if "on" in a else a[True], w["on"] if "on" in w else w[True])
        self.assertEqual(set(a["jobs"]), set(w["jobs"]))
        for n in a["jobs"]:
            if n != "zenodo":
                self.assertEqual(a["jobs"][n], w["jobs"][n], n)
        sa, sw = a["jobs"]["zenodo"]["steps"], w["jobs"]["zenodo"]["steps"]
        self.assertEqual(len(sa), len(sw))
        cambiados = [x["name"] for x, y in zip(sa, sw) if x != y]
        self.assertEqual(["Depositar en Zenodo (prueba)", "Depositar en Zenodo (real)"], cambiados)
        for x, y in zip(sa, sw):
            if x != y:
                self.assertEqual({k: v for k, v in x.items() if k != "run"}, {k: v for k, v in y.items() if k != "run"})
                self.assertEqual(x["run"].replace("> informe_zenodo.json", "| tee informe_zenodo.json"), y["run"])


class SinToken(Base):
    def test_el_informe_no_lleva_el_token(self):
        for kw in ({"publicar": True}, {"publicar": False, "version": "1.0.1", "tag": "mapas-v1.0.1"}):
            inf = self.dep(**kw)
            self.assertNotIn(TOKEN, json.dumps(inf))
            self.assertNotIn("token", json.dumps(inf).lower())
            self.assertIn("url_borrador", inf)


if __name__ == "__main__":
    unittest.main()
