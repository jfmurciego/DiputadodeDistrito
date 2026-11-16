"""T-361: el catálogo de procedencia se publica por lista blanca, determinista y con fallo cerrado."""
from __future__ import annotations

import copy
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import catalogo_procedencia_publico as cpp  # noqa: E402

ORIGEN = ROOT / "orchestracion" / "catalogo_procedencia.json"
PUB = ROOT / ".github/workflows/p40-publicacion.yml"
PROHIBIDAS = {"run_id", "receipt_path", "blob_sha", "copias_r2", "copia_r2_prefijo", "asset_id", "copia_git",
              "copia_release", "package_sha256", "artifact_sha256", "territorial_identity_sha256",
              "fuente_electoral", "incoherencias", "entradas", "id", "origen_sha256", "doi", "tag"}


def claves(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from claves(v)
    elif isinstance(o, list):
        for v in o:
            yield from claves(v)


def paso_build():
    d = yaml.safe_load(PUB.read_text(encoding="utf-8"))
    for job in d["jobs"].values():
        for s in job.get("steps") or []:
            if s.get("name") == "Construir sitio candidato completo":
                return s["run"]
    raise AssertionError


class ListaBlanca(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real = json.loads(ORIGEN.read_text(encoding="utf-8"))

    def test_ningun_campo_fuera_de_la_lista_llega_al_publico(self):
        pub = cpp.filtrar(self.real)
        self.assertFalse(PROHIBIDAS & set(claves(pub)))
        permitidas = {"schema", "motor", "nombre", "version", "fuentes_oficiales", "poblacion_por_sexo_y_edad",
                      "secciones_censales", "resultados_electorales", "proveedor", "url", "territorios",
                      "fuente_territorial", "population_year", "section_year", "productos", *cpp.CAMPOS_PRODUCTO}
        ks = set(claves(pub))
        fechas = set(pub["fuentes_oficiales"]["resultados_electorales"]) | set(pub["territorios"])
        self.assertEqual(ks - fechas - permitidas, set())

    def test_control_negativo_inyeccion(self):
        c = copy.deepcopy(self.real)
        t = next(iter(c["territorios"].values()))
        t["run_id"] = "1"; t["productos"][0].update(run_id="2", receipt_path="x", copias_r2=["a"], blob_sha="b", asset_id="c")
        c["fuentes_secundarias"]["x"] = 1
        c["fuentes_oficiales"]["poblacion_por_sexo_y_edad"]["receipt_path"] = "y"
        txt = cpp.serializar(cpp.filtrar(c))
        for k in ("run_id", "receipt_path", "copias_r2", "blob_sha", "asset_id", "fuentes_secundarias"):
            self.assertNotIn(k, txt)

    def test_conserva_lo_que_lee_el_visor(self):
        pub = cpp.filtrar(self.real)
        self.assertEqual(pub["motor"], self.real["motor"])
        self.assertEqual(pub["fuentes_oficiales"]["poblacion_por_sexo_y_edad"]["url"], self.real["fuentes_oficiales"]["poblacion_por_sexo_y_edad"]["url"])
        for tid, t in self.real["territorios"].items():
            self.assertEqual([p["sha256"] for p in pub["territorios"][tid]["productos"]], [p["sha256"] for p in t["productos"]])

    def test_determinismo(self):
        self.assertEqual(cpp.serializar(cpp.filtrar(self.real)), cpp.serializar(cpp.filtrar(copy.deepcopy(self.real))))

    def test_falla_cerrado(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            mal = d / "mal.json"; mal.write_text("{no", encoding="utf-8")
            for origen in (mal, d / "no_existe.json"):
                out = d / "o" / "x.json"
                self.assertEqual(cpp.main(["--origen", str(origen), "--salida", str(out)]), 1)
                self.assertFalse(out.exists())
            for quitar in ("motor", "fuentes_oficiales", "territorios"):
                c = copy.deepcopy(self.real); del c[quitar]
                with self.assertRaises(cpp.ErrorCatalogo):
                    cpp.filtrar(c)
            c = copy.deepcopy(self.real); del c["fuentes_oficiales"]["secciones_censales"]
            with self.assertRaises(cpp.ErrorCatalogo):
                cpp.filtrar(c)

    def test_valores_envenenados_fallan_cerrado(self):
        def con(f):
            c = copy.deepcopy(self.real)
            f(c)
            return c
        def prod(c):
            return next(iter(c["territorios"].values()))["productos"][0]
        venenos = {
            "producto con run id": lambda c: prod(c).update(producto="M06_43204696160"),
            "producto desconocido": lambda c: prod(c).update(producto="otro"),
            "eleccion con ruta": lambda c: prod(c).update(eleccion="territorios/aut01/2023-07-23"),
            "sha256 corto": lambda c: prod(c).update(sha256="abc"),
            "url r2": lambda c: c["fuentes_oficiales"]["poblacion_por_sexo_y_edad"].update(url="r2://bucket/x"),
            "url http": lambda c: c["fuentes_oficiales"]["poblacion_por_sexo_y_edad"].update(url="http://www.ine.es/x"),
            "url dominio ajeno": lambda c: c["fuentes_oficiales"]["secciones_censales"].update(url="https://evil.example/x"),
            "url actions/runs": lambda c: c["fuentes_oficiales"]["secciones_censales"].update(url="https://www.ine.es/actions/runs/1"),
            "motor con ruta": lambda c: c["motor"].update(nombre="../Deslinde"),
            "version con barra": lambda c: c["motor"].update(version="1.1/0"),
            "generado con receipt": lambda c: prod(c).update(generado="receipt.json"),
        }
        for nombre, f in venenos.items():
            with self.subTest(nombre):
                with self.assertRaises(cpp.ErrorCatalogo):
                    cpp.filtrar(con(f))

    def test_ningun_string_publico_lleva_datos_internos(self):
        patron = re.compile(r"\b\d{10,}\b|territorios/|receipt|r2://|actions/runs", re.I)
        def textos(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    yield str(k)
                    yield from textos(v)
            elif isinstance(o, list):
                for v in o:
                    yield from textos(v)
            elif isinstance(o, str):
                yield o
        n = 0
        for s in textos(json.loads(cpp.generar(ORIGEN))):
            n += 1
            self.assertIsNone(patron.search(s), s)
        self.assertGreater(n, 1000)

    def test_cli_escribe_identico(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.json", Path(d) / "b.json"
            self.assertEqual(cpp.main(["--salida", str(a)]), 0)
            self.assertEqual(cpp.main(["--salida", str(b)]), 0)
            self.assertEqual(a.read_bytes(), b.read_bytes())


class PasoDelWorkflow(unittest.TestCase):
    def test_paso_tras_materializar_sin_cp_crudo(self):
        run = paso_build()
        self.assertIn("set -euo pipefail", run)
        self.assertNotIn("cp orchestracion/catalogo_procedencia.json", run)
        i = run.index("herramientas/catalogo_procedencia_publico.py")
        self.assertGreater(i, run.index("--materializar"))
        self.assertIn("--salida /tmp/site-candidate/datos/catalogo_procedencia.json", run)

    def test_el_paso_falla_si_falta_el_catalogo(self):
        with tempfile.TemporaryDirectory() as d:
            linea = [l.strip() for l in paso_build().splitlines() if "catalogo_procedencia_publico" in l][0]
            r = subprocess.run(["bash", "-c", "set -euo pipefail\n" + linea.replace("herramientas/catalogo_procedencia_publico.py", "herramientas/catalogo_procedencia_publico.py --origen " + d + "/no.json").replace("/tmp/site-candidate", d)],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)


class CompatibilidadVisor(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "sin node")
    def test_visor_v3_con_catalogo_filtrado(self):
        src = (ROOT / "tests/test_visor_v3_ui.js").read_text(encoding="utf-8")
        self.assertIn('orchestracion/catalogo_procedencia.json', src)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "catalogo.json"
            f.write_text(cpp.generar(cpp.ORIGEN), encoding="utf-8")
            alt = src.replace('path.join(ROOT,"orchestracion/catalogo_procedencia.json")', json.dumps(str(f)))
            self.assertNotEqual(alt, src)
            tmp = ROOT / "tests" / "_t361_visor_tmp.js"
            tmp.write_text(alt, encoding="utf-8")
            try:
                r = subprocess.run(["node", "--test", str(tmp)], cwd=ROOT, capture_output=True, text=True)
            finally:
                tmp.unlink()
            self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-1000:])


if __name__ == "__main__":
    unittest.main()
