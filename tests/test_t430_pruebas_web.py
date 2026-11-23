"""T-430 paso 3a (D-193/D-194): vista de pruebas de la web por rama en R2 y su limpieza (P90 `pruebas_web` y `limpiar_pruebas`)."""
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import pruebas_web_r2 as p

RAIZ = Path(__file__).resolve().parents[1]
WF = RAIZ / ".github/workflows/p90-automatico.yml"


class Hecho:
    def __init__(self, stdout="", rc=0):
        self.stdout, self.returncode, self.stderr = stdout, rc, ""


class PruebasWeb(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("R2_ACCOUNT_ID", "cuenta")

    def test_rama_a_carpeta_sin_colisiones(self):
        import re
        c = p.rama_a_carpeta("T442/Portada_Ligera")
        self.assertTrue(c.startswith("t442-portada-ligera-"), c)
        parecidas = ["feature/a", "feature_a", "Feature-A", "x" * 70 + "1", "x" * 70 + "2", "ñ", "///"]
        carpetas = [p.rama_a_carpeta(r) for r in parecidas]
        self.assertEqual(len(set(carpetas)), len(parecidas), carpetas)
        for x in carpetas:
            self.assertRegex(x, r"^[a-z0-9-]{1,60}$")
        self.assertEqual(p.rama_a_carpeta("feature/a"), p.rama_a_carpeta("feature/a"))  # estable
        with self.assertRaises(p.PruebasError):
            p.rama_a_carpeta("  ")

    def test_montar_v4_real_sin_buscadores_ni_paginas_internas(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "m"
            n = p.montar(dst, datos_actual="https://datos.diputadodedistrito.es/web/actual/actual.json")
            self.assertGreaterEqual(n, 3)
            for h in dst.rglob("*.html"):
                self.assertIn(p.NOINDEX, h.read_text(encoding="utf-8"), h)
            self.assertFalse((dst / "auditoria-registro.html").exists())  # en NO_PUBLICAR.txt
            self.assertTrue((dst / "v2/vendor/maplibre-gl/5.7.0/maplibre-gl.js").is_file())  # Explorar lo pide con ../v2/
            self.assertEqual(json.loads((dst / "mapa/datos.json").read_text())["actual"], "https://datos.diputadodedistrito.es/web/actual/actual.json")
            self.assertNotIn(p.NOINDEX, (RAIZ / "visor/v4/index.html").read_text(encoding="utf-8"))  # el repositorio no cambia
            with self.assertRaises(p.PruebasError):
                p.montar(dst, datos_actual="http://otra/actual.json")

    def test_subir_solo_en_su_carpeta(self):
        llamadas = []
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "index.html").write_text("<head>")
            c = p.subir(Path(d), "pruebas", "T430/x", lambda a, **_: llamadas.append(a) or Hecho())
        self.assertEqual(c, p.rama_a_carpeta("T430/x"))
        self.assertEqual(llamadas[0][2:5], ["sync", d, f"s3://pruebas/{c}/"])
        self.assertIn("--delete", llamadas[0])

    def test_limpiar_borra_solo_ramas_cerradas_con_tope(self):
        ab, ce = p.rama_a_carpeta("Abierta/1"), p.rama_a_carpeta("cerrada/2")
        ls = f"                           PRE {ab}/\n                           PRE {ce}/\n2026-11-23 00:00:00  10 suelto.txt\n"
        llamadas = []

        def ej(a, **_):
            llamadas.append(a)
            return Hecho(ls if a[2] == "ls" else "")
        self.assertEqual(p.limpiar("pruebas", ["Abierta/1", "ñ"], ej), [ce])  # una rama rara no rompe la limpieza
        self.assertEqual([a[2:5] for a in llamadas if a[2] == "rm"], [["rm", f"s3://pruebas/{ce}/", "--recursive"]])
        muchas = "".join(f"  PRE r{i}/\n" for i in range(p.TOPE_LIMPIEZA + 1))
        llamadas.clear()
        with self.assertRaises(p.PruebasError):
            p.limpiar("pruebas", [], lambda a, **_: llamadas.append(a) or Hecho(muchas))
        self.assertFalse(any(a[2] == "rm" for a in llamadas))
        with self.assertRaises(p.PruebasError):
            p.limpiar("pruebas", [], lambda a, **_: Hecho("  PRE Rara_X/\n"))

    def test_bucket_ajeno_rechazado(self):
        from unittest import mock
        with mock.patch.dict(os.environ, {"R2_SITIO_BUCKET": "sitio"}):
            self.assertEqual(p.main(["limpiar", "--abiertas", "", "--bucket", "sitio"]), 1)
        self.assertEqual(p.main(["limpiar", "--abiertas", "", "--bucket", ""]), 0)


class JobsP90(unittest.TestCase):
    def setUp(self):
        self.wf = yaml.safe_load(WF.read_text(encoding="utf-8"))

    def test_condiciones_permisos_y_secretos(self):
        j = self.wf["jobs"]
        co = j["pruebas_web"]["steps"][1]
        self.assertEqual((co["with"]["ref"], co["with"]["path"], co["with"]["persist-credentials"]), ("main", "_main", False))
        self.assertEqual(j["pruebas_web"]["if"], "${{ github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository }}")
        self.assertEqual(j["limpiar_pruebas"]["if"], "${{ github.event_name == 'push' }}")
        for n in ("pruebas_web", "limpiar_pruebas"):
            self.assertEqual(j[n]["permissions"], {"contents": "read", "pull-requests": "read"})
            self.assertIs(j[n]["steps"][0]["with"]["persist-credentials"], False)
            env = j[n]["steps"][-1]["env"]
            self.assertEqual(env["AWS_ACCESS_KEY_ID"], "${{ secrets.R2_PRUEBAS_ACCESS_KEY_ID }}")
            self.assertNotIn(n, j["pruebas"].get("needs", []))  # no condiciona el check `pruebas`

    def _correr(self, job, gh_salida, pr=""):
        bloque = self.wf["jobs"][job]["steps"][-1]["run"]
        with tempfile.TemporaryDirectory() as d:
            b = Path(d)
            reg = b / "llamadas.txt"
            for nombre, cuerpo in (("gh", f'printf "%s\\n" {gh_salida}'), ("python3", f'echo "$@" >> "{reg}"')):
                f = b / nombre
                f.write_text("#!/bin/bash\n" + cuerpo + "\n")
                f.chmod(f.stat().st_mode | stat.S_IEXEC)
            env = {**os.environ, "PATH": f"{b}:{os.environ['PATH']}", "R2_PRUEBAS_BUCKET": "pruebas", "PR": "1", "RAMA": "t430/x",
                   "GITHUB_REPOSITORY": "o/r"}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", bloque], env=env, capture_output=True, text=True)
            return r.returncode, (reg.read_text() if reg.exists() else ""), r.stdout

    def test_bloques_bajo_pipefail(self):
        rc, llamadas, _ = self._correr("pruebas_web", "README.md visor/v4/index.html")
        self.assertEqual(rc, 0)
        self.assertIn("_main/herramientas/pruebas_web_r2.py montar --raiz . --destino /tmp/pruebas-web", llamadas)  # script de main
        self.assertIn("_main/herramientas/pruebas_web_r2.py subir --origen /tmp/pruebas-web --rama t430/x", llamadas)
        rc, llamadas, salida = self._correr("pruebas_web", "README.md herramientas/x.py")
        self.assertEqual((rc, llamadas), (0, ""))
        self.assertIn("no toca visor/v4/", salida)
        rc, llamadas, _ = self._correr("limpiar_pruebas", "rama-a rama-b")
        self.assertEqual(rc, 0)
        self.assertIn("limpiar --abiertas rama-a,rama-b", llamadas)


if __name__ == "__main__":
    unittest.main()
