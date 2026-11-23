# -*- coding: utf-8 -*-
"""T-448 (D-202): espejo de 1mun00.csv (INE, Censo 2011) en R2 con el «Espejo de fuente oficial» de P10, modo URL directa.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-23 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: D-202. Sin red: la descarga se simula con bytes sintéticos y se comprueba la huella declarada (valores literales de D-185).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import espejo_fuente_oficial as ef  # noqa: E402

CLAVE = "ine-censo2011-1mun00"
SHA = "ad95479c07ce4ae37ed03732025d7039b1338f43ead181bb2c450fcac64f8267"  # D-185, medido en www.ine.es el 20-11 y el 23-11
BYTES = 105319154


def _decl(d: Path, datos: bytes) -> Path:
    """Copia de la declaración real con la huella de `datos` (los 105 MB no se generan en el test)."""
    real = json.loads((ROOT / "configuracion/espejos_fuentes_oficiales.json").read_text(encoding="utf-8"))
    e = dict(real["espejos"][CLAVE], sha256_esperado=hashlib.sha256(datos).hexdigest(), bytes_esperados=len(datos))
    ruta = d / "espejos.json"
    ruta.write_text(json.dumps({"espejos": {CLAVE: e}}), encoding="utf-8")
    return ruta


class Declaracion(unittest.TestCase):
    def test_entrada_real_coincide_con_d185_y_el_indice(self):
        e = ef.declaracion(CLAVE)
        tm = json.loads((ROOT / "configuracion/historico_epoca/total_municipal_censo_2011.json").read_text(encoding="utf-8"))["fuente"]
        self.assertEqual((e["sha256_esperado"], e["bytes_esperados"], e["url"]), (SHA, BYTES, tm["url"]))
        self.assertEqual((tm["sha256"], tm["bytes"]), (SHA, BYTES))
        self.assertEqual(e["hosts_permitidos"], ["www.ine.es"])
        self.assertTrue(BYTES < e["max_bytes"] <= BYTES * 1.05)
        self.assertNotIn("api_url", e)
        clave = ef.clave_r2(e["organismo"], e["anyo"], f"{e['fichero']}.{e['extension']}")
        self.assertEqual(clave, "fuentes/ine/2011/1mun00.csv")
        idx = json.loads((ROOT / "orchestracion/fuentes_r2.json").read_text(encoding="utf-8"))["fuentes"]["1mun00.csv"]
        self.assertEqual((idx["clave"], idx["sha256"], idx["bytes"]), (clave, SHA, BYTES))


class EspejarUrlDirecta(unittest.TestCase):
    DATOS = "Municipios;Sexo;Edad;Total\n08047 Cardona;Ambos sexos;Total;5.057\n".encode("utf-8")

    def _get(self, datos):
        pedidas = []

        def get(url, hosts, tope, *a):
            pedidas.append((url, tuple(hosts), tope))
            return datos
        return get, pedidas

    def test_huella_correcta_da_la_pieza_y_el_manifiesto(self):
        with tempfile.TemporaryDirectory() as d:
            decl = _decl(Path(d), self.DATOS)
            get, pedidas = self._get(self.DATOS)
            m = ef.espejar(CLAVE, Path(d) / "s", get=get, ruta_decl=decl)
            self.assertEqual(len(pedidas), 1)  # solo la URL directa: ni API de catálogo ni PDF
            self.assertEqual(pedidas[0][1], ("www.ine.es",))
            self.assertEqual([(p["nombre"], p["clave"], p["sha256"], p["bytes"]) for p in m["piezas"]],
                             [("1mun00.csv", "fuentes/ine/2011/1mun00.csv", hashlib.sha256(self.DATOS).hexdigest(), len(self.DATOS))])
            self.assertEqual(m["territorio"], CLAVE)
            self.assertEqual((Path(d) / "s" / "1mun00.csv").read_bytes(), self.DATOS)

    def test_huella_distinta_falla_cerrado_sin_escribir(self):
        with tempfile.TemporaryDirectory() as d:
            decl = _decl(Path(d), self.DATOS)
            get, _ = self._get(self.DATOS + b"x")
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar(CLAVE, Path(d) / "s", get=get, ruta_decl=decl)
            self.assertEqual(c.exception.codigo, "ESPEJO_HUELLA_INESPERADA")
            self.assertFalse((Path(d) / "s").exists())

    def test_html_falla(self):
        with tempfile.TemporaryDirectory() as d:
            html = b"<!DOCTYPE html><html>en obras</html>"
            decl = _decl(Path(d), html)
            get, _ = self._get(html)
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar(CLAVE, Path(d) / "s", get=get, ruta_decl=decl)
            self.assertEqual(c.exception.codigo, "ESPEJO_ES_HTML")

    def test_sin_huella_declarada_falla(self):
        with tempfile.TemporaryDirectory() as d:
            decl = _decl(Path(d), self.DATOS)
            j = json.loads(decl.read_text(encoding="utf-8"))
            j["espejos"][CLAVE].pop("sha256_esperado")
            decl.write_text(json.dumps(j), encoding="utf-8")
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar(CLAVE, Path(d) / "s", get=self._get(self.DATOS)[0], ruta_decl=decl)
            self.assertEqual(c.exception.codigo, "ESPEJO_DECLARACION")

    def test_otro_host_rechazado_antes_de_bajar(self):
        with self.assertRaises(ef.ErrorEspejo) as c:
            ef._get("https://servicios.ine.es/x.csv", ["www.ine.es"], 10, abrir=lambda *a: self.fail("no debe abrir"))
        self.assertEqual(c.exception.codigo, "ESPEJO_HOST_NO_PERMITIDO")

    def test_subir_comprueba_la_clave_y_no_sobrescribe(self):
        with tempfile.TemporaryDirectory() as d:
            decl = _decl(Path(d), self.DATOS)
            ef.espejar(CLAVE, Path(d) / "s", get=self._get(self.DATOS)[0], ruta_decl=decl)
            otro = "0" * 64

            class R:
                def __init__(self, rc=0, out="", err=""):
                    self.returncode, self.stdout, self.stderr = rc, out, err

            def aws(args, capturar=False):  # el objeto ya existe en R2 con otra huella
                if args[:2] == ["s3api", "head-object"]:
                    return R(0, json.dumps({"Metadata": {"sha256": otro}}))
                self.fail(f"no debe escribir: {args}")
            env = {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}
            with unittest.mock.patch.dict(os.environ, env):
                with self.assertRaises(ef.ErrorEspejo) as c:
                    ef.subir_espejo(CLAVE, Path(d) / "s", aws=aws, ruta_decl=decl)
            self.assertEqual(c.exception.codigo, "ESPEJO_HUELLA_DISTINTA")


class EntradaP10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        w = yaml.safe_load((ROOT / ".github/workflows/p10-fuentes.yml").read_text(encoding="utf-8"))
        cls.script = next(s for s in w["jobs"]["entrada"]["steps"] if s.get("name") == "Comprobar tipo, territorio y elección")["run"]

    def _rc(self, tipo, territorio):
        with tempfile.TemporaryDirectory() as t:
            env = {**os.environ, "TIPO": tipo, "TERRITORIO": territorio, "TERRITORIO_LLAMADA": "", "ELECCION": "vigente",
                   "GITHUB_STEP_SUMMARY": str(Path(t) / "s")}
            return subprocess.run(["bash", "-eo", "pipefail", "-c", self.script], env=env, capture_output=True, text=True)

    def test_clave_de_espejo_valida(self):
        for t in (CLAVE, "aut08"):
            r = self._rc("Espejo de fuente oficial", t)
            self.assertEqual(r.returncode, 0, (t, r.stdout + r.stderr))

    def test_rechazos(self):
        for tipo, t in (("Espejo de fuente oficial", "Ine;rm"), ("Espejo de fuente oficial", ""), ("Espejo de fuente oficial", "a b"),
                        ("P11 territoriales", CLAVE), ("P12 electorales", CLAVE)):
            r = self._rc(tipo, t)
            self.assertNotEqual(r.returncode, 0, (tipo, t))
            self.assertIn("::error::", r.stdout + r.stderr)


import unittest.mock  # noqa: E402

if __name__ == "__main__":
    unittest.main()
