#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-449 (D-183, D-188): espejo de solo lectura de una fuente oficial desde el runner.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.1
FECHA: 2026-11-23
CAMBIOS: 1.0.1: candidatas en orden (`downloadURL` antes que `accessURL`) y salto de la portada a la siguiente (run 45158272014). 1.0.0: fichero nuevo.
MOTIVO: fija la elección de la distribución del año, el rechazo de la portada HTML, la clave de D-188 y que nunca sobrescribe.
ANTERIOR: legacy/tests/test_t449_espejo_fuente_oficial_v1.0.0_20261123.py
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import espejo_fuente_oficial as ef  # noqa: E402

API = {"result": {"items": [{"distribution": [
    {"accessURL": "https://ejemplo.invalid/files/2019.xlsx", "format": {"value": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
     "title": [{"_value": "Resultados 2019", "_lang": "es"}]},
    {"accessURL": "https://ejemplo.invalid/files/Resultados_CLM_2023.xlsx", "format": {"value": "XLSX"},
     "title": [{"_value": "Resultados 2023", "_lang": "es"}, {"_value": "Results 2023", "_lang": "en"}]},
    {"accessURL": "https://ejemplo.invalid/files/Resultados_CLM_2023.csv", "format": "text/csv", "title": "Resultados 2023"},
    {"accessURL": "https://ejemplo.invalid/files/informe_2023.pdf", "format": "PDF", "title": "Informe 2023"},
    {"accessURL": "https://ejemplo.invalid/files/12023.csv", "format": "text/csv", "title": "Otro"},
]}]}}


try:
    import openpyxl
except ImportError:  # la CI no instala openpyxl: el volcado real se prueba solo donde está
    openpyxl = None


def _volcado_falso(datos, destino):
    (destino / "hoja-1.csv").write_text("Municipio,PSOE,PP\nAlbacete,10,20\n", encoding="utf-8")
    return [{"hoja": "Municipios", "csv": "hoja-1.csv", "filas": 2}]


def _xlsx() -> bytes:
    wb = openpyxl.Workbook()
    wb.active.title = "Municipios"
    wb.active.append(["Municipio", "PSOE", "PP"])
    wb.active.append(["Albacete", 10, 20])
    b = io.BytesIO()
    wb.save(b)
    return b.getvalue()


class Eleccion(unittest.TestCase):
    def test_elige_el_xlsx_del_anyo(self):
        d = ef.elegir_distribucion(API, 2023)
        self.assertEqual(d["url"], "https://ejemplo.invalid/files/Resultados_CLM_2023.xlsx")
        self.assertEqual(d["extension"], "xlsx")

    def test_sin_anyo_falla(self):
        with self.assertRaises(ef.ErrorEspejo) as c:
            ef.elegir_distribucion(API, 2015)
        self.assertEqual(c.exception.codigo, "ESPEJO_SIN_DISTRIBUCION")

    def test_dos_del_mismo_formato_es_ambigua(self):
        api = json.loads(json.dumps(API))
        api["result"]["items"][0]["distribution"].append(
            {"accessURL": "https://ejemplo.invalid/otra/2023.xlsx", "format": "XLSX", "title": "2023 bis"})
        with self.assertRaises(ef.ErrorEspejo) as c:
            ef.elegir_distribucion(api, 2023)
        self.assertEqual(c.exception.codigo, "ESPEJO_DISTRIBUCION_AMBIGUA")


class Candidatas(unittest.TestCase):
    """1.0.1: run 45158272014 (ESPEJO_ES_HTML): `downloadURL` antes que `accessURL` y se prueban todas las candidatas del año."""

    API2 = {"result": {"items": [{"distribution": [
        {"accessURL": "https://ejemplo.invalid/portal/resultados-2023", "downloadURL": "https://ejemplo.invalid/files/Resultados_CLM_2023.xlsx",
         "format": "XLSX", "title": "Resultados 2023"},
        {"accessURL": "https://ejemplo.invalid/files/Resultados_CLM_2023.csv", "format": "text/csv", "title": "Resultados 2023"},
    ]}]}}

    def test_orden_descarga_antes_que_acceso_y_xlsx_antes_que_csv(self):
        self.assertEqual([c["url"] for c in ef.candidatas_del_anyo(self.API2, 2023)],
                         ["https://ejemplo.invalid/files/Resultados_CLM_2023.xlsx", "https://ejemplo.invalid/portal/resultados-2023",
                          "https://ejemplo.invalid/files/Resultados_CLM_2023.csv"])

    def _espejar(self, respuestas):
        decl = json.loads(ef.DECLARACION.read_text(encoding="utf-8"))
        decl["espejos"]["aut08"]["hosts_permitidos"].append("ejemplo.invalid")
        decl["espejos"]["aut08"].pop("verificacion")
        pedidas = []

        def get(url, hosts, tope, intentos=4):
            ef.comprobar_url(url, hosts)
            pedidas.append(url)
            return json.dumps(self.API2).encode() if url.endswith(".json") else respuestas[url]

        with tempfile.TemporaryDirectory() as td, mock.patch.object(ef, "volcar_xlsx", _volcado_falso):
            r = Path(td) / "d.json"
            r.write_text(json.dumps(decl), encoding="utf-8")
            try:
                return ef.espejar("aut08", Path(td) / "s", get=get, ruta_decl=r), pedidas
            except ef.ErrorEspejo as exc:
                return exc, pedidas

    def test_portada_en_la_primera_pasa_a_la_siguiente(self):
        html = b"<!DOCTYPE html><html>portal en obras</html>"
        m, pedidas = self._espejar({"https://ejemplo.invalid/files/Resultados_CLM_2023.xlsx": html,
                                    "https://ejemplo.invalid/portal/resultados-2023": html,
                                    "https://ejemplo.invalid/files/Resultados_CLM_2023.csv": b"Municipio;PSOE\nAlbacete;1\n"})
        self.assertEqual(m["piezas"][0]["origen_url"], "https://ejemplo.invalid/files/Resultados_CLM_2023.csv")
        self.assertEqual(m["piezas"][0]["clave"], "fuentes/junta-castilla-la-mancha/2023/autonomicas-por-municipio.csv")
        self.assertEqual(len(pedidas), 4)  # API + 3 candidatas

    def test_ninguna_vale_da_el_motivo_y_lo_probado(self):
        html = b"<html>portal</html>"
        exc, _ = self._espejar({u: html for u in ("https://ejemplo.invalid/files/Resultados_CLM_2023.xlsx",
                                                  "https://ejemplo.invalid/portal/resultados-2023",
                                                  "https://ejemplo.invalid/files/Resultados_CLM_2023.csv")})
        self.assertIsInstance(exc, ef.ErrorEspejo)
        self.assertEqual(exc.codigo, "ESPEJO_ES_HTML")
        self.assertIn("portal/resultados-2023", str(exc))


class Contenido(unittest.TestCase):
    def test_portada_html_se_rechaza(self):
        with self.assertRaises(ef.ErrorEspejo) as c:
            ef.comprobar_contenido(b"\n<!DOCTYPE html><html><body>Portal en obras</body></html>", "xlsx")
        self.assertEqual(c.exception.codigo, "ESPEJO_ES_HTML")

    def test_firma_xlsx(self):
        ef.comprobar_contenido(b"PK\x03\x04resto", "xlsx")
        with self.assertRaises(ef.ErrorEspejo):
            ef.comprobar_contenido(b"Municipio;PSOE", "xlsx")


@unittest.skipUnless(openpyxl, "sin openpyxl")
class VolcadoReal(unittest.TestCase):
    def test_hoja_a_csv(self):
        with tempfile.TemporaryDirectory() as td:
            h = ef.volcar_xlsx(_xlsx(), Path(td))
            self.assertEqual(h[0]["hoja"], "Municipios")
            self.assertEqual((Path(td) / "hoja-1.csv").read_text(encoding="utf-8").splitlines()[1], "Albacete,10,20")


class Clave(unittest.TestCase):
    def test_arbol_d188(self):
        self.assertEqual(ef.clave_r2("junta-castilla-la-mancha", 2023, "autonomicas-por-municipio.xlsx"),
                         "fuentes/junta-castilla-la-mancha/2023/autonomicas-por-municipio.xlsx")

    def test_prohibe_codigos_y_mayusculas(self):
        for organismo, nombre in (("junta-castilla-la-mancha", "aut08-municipios.xlsx"), ("JCCM", "a.xlsx"),
                                  ("junta-castilla-la-mancha", "datos-4475123456.xlsx")):
            with self.assertRaises(ef.ErrorEspejo):
                ef.clave_r2(organismo, 2023, nombre)

    def test_declaracion_aut08(self):
        e = ef.declaracion("aut08")
        self.assertEqual((e["organismo"], e["anyo"], e["fecha"]), ("junta-castilla-la-mancha", 2023, "2023-05-28"))
        self.assertIn("datos.gob.es/apidata/catalog/dataset/", e["api_url"])


class R2Falso:
    """R2 en memoria con la semántica que usa la herramienta: head-object, put-object con If-None-Match y cp de lectura."""

    def __init__(self):
        self.objetos, self.escrituras = {}, []

    def __call__(self, args, capturar=False):
        if args[:2] == ["s3api", "head-object"]:
            clave = args[args.index("--key") + 1]
            if clave in self.objetos:
                return subprocess.CompletedProcess(args, 0, json.dumps({"Metadata": {"sha256": self.objetos[clave][1]}}), "")
            return subprocess.CompletedProcess(args, 255, "", "An error occurred (404) when calling the HeadObject operation: Not Found")
        if args[:2] == ["s3api", "put-object"]:
            self.assertIn_ifnm(args)
            clave = args[args.index("--key") + 1]
            if clave in self.objetos:
                return subprocess.CompletedProcess(args, 254, "", "An error occurred (PreconditionFailed) when calling the PutObject operation")
            huella = args[args.index("--metadata") + 1].split("=", 1)[1]
            self.objetos[clave] = (Path(args[args.index("--body") + 1]).read_bytes(), huella)
            self.escrituras.append(clave)
            return subprocess.CompletedProcess(args, 0, "{}", "")
        if args[:2] == ["s3", "cp"] and args[2].startswith("s3://"):
            clave = args[2].split("/", 3)[3]
            Path(args[3]).write_bytes(self.objetos[clave][0])
            return subprocess.CompletedProcess(args, 0, "", "")
        raise AssertionError(f"orden de R2 no prevista: {args}")

    @staticmethod
    def assertIn_ifnm(args):
        if args[args.index("--if-none-match") + 1] != "*":
            raise AssertionError("put-object sin --if-none-match '*'")


class Espejar(unittest.TestCase):
    def setUp(self):
        self.xlsx = b"PK\x03\x04" + b"x" * 100
        self.pdf = b"%PDF-1.4 resultados"
        p = mock.patch.object(ef, "volcar_xlsx", _volcado_falso)
        p.start()
        self.addCleanup(p.stop)
        e = mock.patch.dict(os.environ, {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"})
        e.start()
        self.addCleanup(e.stop)

    def _get(self, url, hosts, tope, intentos=4):
        ef.comprobar_url(url, hosts)
        if url.endswith(".json"):
            return json.dumps(API).encode()
        if url.endswith("Resultados_CLM_2023.xlsx"):
            return self.xlsx
        if url.endswith(".pdf"):
            return self.pdf
        raise AssertionError(url)

    def _decl(self, td):
        d = json.loads(ef.DECLARACION.read_text(encoding="utf-8"))
        d["espejos"]["aut08"]["hosts_permitidos"].append("ejemplo.invalid")
        r = Path(td) / "decl.json"
        r.write_text(json.dumps(d), encoding="utf-8")
        return r

    def test_espejar_no_toca_r2_y_mide(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(ef, "_aws", side_effect=AssertionError("R2 en espejar")):
            m = ef.espejar("aut08", Path(td) / "s", get=self._get, ruta_decl=self._decl(td))
            datos = m["piezas"][0]
            self.assertEqual(datos["clave"], "fuentes/junta-castilla-la-mancha/2023/autonomicas-por-municipio.xlsx")
            self.assertEqual(datos["sha256"], ef.hashlib.sha256(self.xlsx).hexdigest())
            self.assertEqual(datos["bytes"], len(self.xlsx))
            self.assertEqual(datos["volcado_csv"][0]["hoja"], "Municipios")
            self.assertEqual(m["piezas"][1]["clave"], "fuentes/junta-castilla-la-mancha/2023/resultados-oficiales.pdf")
            self.assertNotIn("r2", datos)

    def test_host_no_declarado_no_se_descarga(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar("aut08", Path(td), get=self._get)  # ejemplo.invalid no está en la declaración real
        self.assertEqual(c.exception.codigo, "ESPEJO_HOST_NO_PERMITIDO")

    def test_subir_condicional_completa_y_no_sobrescribe(self):
        r2 = R2Falso()
        with tempfile.TemporaryDirectory() as td:
            decl, sal = self._decl(td), Path(td) / "s"
            ef.espejar("aut08", sal, get=self._get, ruta_decl=decl)
            # Falla la 2.ª pieza tras subir la 1.ª: no queda manifiesto.
            real = r2.__call__
            fallo = {"n": 0}

            def con_fallo(args, capturar=False):
                if args[:2] == ["s3api", "put-object"] and args[args.index("--key") + 1].endswith(".pdf") and not fallo["n"]:
                    fallo["n"] = 1
                    return subprocess.CompletedProcess(args, 1, "", "connection reset")
                return real(args, capturar)

            with self.assertRaises(ef.ErrorEspejo):
                ef.subir_espejo("aut08", sal, aws=con_fallo, ruta_decl=decl)
            self.assertEqual(r2.escrituras, ["fuentes/junta-castilla-la-mancha/2023/autonomicas-por-municipio.xlsx"])
            # Reintento: completa lo que falta, manifiesto el último.
            res = ef.subir_espejo("aut08", sal, aws=r2, ruta_decl=decl)
            self.assertEqual([p["r2"] for p in res["piezas"]], ["ya_estaba", "subido"])
            self.assertEqual(r2.escrituras[-1], "fuentes/junta-castilla-la-mancha/2023/manifiesto.json")
            # Tercera vez, otro `medido`: nada se escribe.
            n = len(r2.escrituras)
            ef.espejar("aut08", sal, get=self._get, ruta_decl=decl)
            res = ef.subir_espejo("aut08", sal, aws=r2, ruta_decl=decl)
            self.assertEqual(set(res["estado"].values()), {"ya_estaba"})
            self.assertEqual(len(r2.escrituras), n)
            # Otra huella en origen: falla sin escribir.
            self.xlsx = b"PK\x03\x04" + b"y" * 100
            ef.espejar("aut08", sal, get=self._get, ruta_decl=decl)
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.subir_espejo("aut08", sal, aws=r2, ruta_decl=decl)
            self.assertEqual(c.exception.codigo, "ESPEJO_HUELLA_DISTINTA")
            self.assertEqual(len(r2.escrituras), n)

    def test_carrera_put_412_compara(self):
        r2 = R2Falso()
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "a"
            f.write_bytes(b"x")
            h = ef.sha256(b"x")

            def carrera(args, capturar=False):  # el head no lo ve; el put encuentra que otro lo escribió con la misma huella
                if args[:2] == ["s3api", "head-object"] and not r2.objetos:
                    r2.objetos["k"] = (b"x", h)
                    return subprocess.CompletedProcess(args, 255, "", "(404) Not Found")
                return r2(args, capturar)

            self.assertEqual(ef.poner_si_no_existe(f, "k", h, aws=carrera), "ya_estaba")
            self.assertEqual(r2.escrituras, [])

    def test_manifiesto_remoto_distinto_falla(self):
        r2 = R2Falso()
        with tempfile.TemporaryDirectory() as td:
            decl, sal = self._decl(td), Path(td) / "s"
            ef.espejar("aut08", sal, get=self._get, ruta_decl=decl)
            r2.objetos["fuentes/junta-castilla-la-mancha/2023/manifiesto.json"] = (json.dumps({"piezas": []}).encode(), "z")
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.subir_espejo("aut08", sal, aws=r2, ruta_decl=decl)
            self.assertEqual(c.exception.codigo, "ESPEJO_MANIFIESTO_DISTINTO")

    def test_portada_en_obras_no_deja_manifiesto(self):
        def get(url, hosts, tope, intentos=4):
            return json.dumps(API).encode() if url.endswith(".json") else b"<html><body>En obras</body></html>"

        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar("aut08", Path(td), get=get, ruta_decl=self._decl(td))
            self.assertFalse((Path(td) / "manifiesto.json").exists())
        self.assertEqual(c.exception.codigo, "ESPEJO_ES_HTML")


class Descarga(unittest.TestCase):
    HOSTS = ["datos.gob.es"]

    def test_solo_https_y_hosts_exactos(self):
        for url in ("http://datos.gob.es/a", "https://datos.gob.es.evil.invalid/a", "https://evil.invalid/datos.gob.es"):
            with self.assertRaises(ef.ErrorEspejo):
                ef.comprobar_url(url, self.HOSTS)
        ef.comprobar_url("https://datos.gob.es/apidata/x.json", self.HOSTS)

    def test_tope_de_bytes(self):
        class R(io.BytesIO):
            def __exit__(self, *a):
                return False

        with self.assertRaises(ef.ErrorEspejo) as c:
            ef._get("https://datos.gob.es/a", self.HOSTS, 10, abrir=lambda u, h: R(b"x" * 11))
        self.assertEqual(c.exception.codigo, "ESPEJO_DEMASIADO_GRANDE")
        self.assertEqual(ef._get("https://datos.gob.es/a", self.HOSTS, 10, abrir=lambda u, h: R(b"x" * 10)), b"x" * 10)

    def test_redireccion_a_otro_host(self):
        h = ef._Redirecciones(self.HOSTS)
        req = urllib.request.Request("https://datos.gob.es/a")
        with self.assertRaises(ef.ErrorEspejo) as c:
            h.redirect_request(req, None, 302, "Found", {}, "https://evil.invalid/b")
        self.assertEqual(c.exception.codigo, "ESPEJO_HOST_NO_PERMITIDO")
        h = ef._Redirecciones(self.HOSTS)
        with self.assertRaises(ef.ErrorEspejo) as c:
            for _ in range(ef.MAX_REDIRECCIONES + 1):
                h.redirect_request(req, None, 302, "Found", {}, "https://datos.gob.es/b")
        self.assertEqual(c.exception.codigo, "ESPEJO_REDIRECCIONES")


class JobP10(unittest.TestCase):
    """El job `p13_espejo` de P10 1.0.3: solo desde el botón, sin campaña, secretos en el paso y sin escribir en main."""

    @classmethod
    def setUpClass(cls):
        import yaml

        cls.w = yaml.safe_load((ROOT / ".github" / "workflows" / "p10-fuentes.yml").read_text(encoding="utf-8"))
        cls.j = cls.w["jobs"]["p13_espejo"]

    def test_opcion_y_condicion(self):
        tipo = (self.w.get("on") or self.w[True])["workflow_dispatch"]["inputs"]["tipo"]
        self.assertEqual(tipo["options"], ["P11 territoriales", "P12 electorales", "Espejo de fuente oficial"])
        self.assertEqual(self.j["if"], "${{ inputs.tipo == 'Espejo de fuente oficial' && github.ref == 'refs/heads/main' && !inputs.campana }}")
        g = self.w["concurrency"]["group"]
        self.assertTrue(g.startswith("${{ inputs.tipo == 'Espejo de fuente oficial' && format('ddd-espejo-fuente-{0}', inputs.territorio) || "), g)
        self.assertEqual(self.j["needs"], "entrada")

    def test_bajada_sin_secretos_y_subida_aparte(self):
        self.assertNotIn("env", self.j)
        bajar = next(s for s in self.j["steps"] if s.get("name") == "Bajar y medir (sin secretos)")
        subir = next(s for s in self.j["steps"] if s.get("name") == "Subir a R2 sin sobrescribir")
        self.assertEqual(set(bajar["env"]), {"TERRITORIO"})
        self.assertNotIn("secrets.", json.dumps(bajar))
        self.assertIn('herramientas/espejo_fuente_oficial.py espejar --territorio "$TERRITORIO"', bajar["run"])
        self.assertEqual(subir["env"]["AWS_SECRET_ACCESS_KEY"], "${{ secrets.R2_SECRET_ACCESS_KEY }}")
        self.assertIn('herramientas/espejo_fuente_oficial.py subir --territorio "$TERRITORIO"', subir["run"])
        self.assertLess(self.j["steps"].index(bajar), self.j["steps"].index(subir))
        self.assertEqual(sum("secrets." in json.dumps(s) for s in self.j["steps"]), 1)
        texto = json.dumps(self.j)
        for prohibido in ("git push", "DDD_REGISTRO_APP", "contents: write"):
            self.assertNotIn(prohibido, texto)

    def test_entrada_acepta_el_tipo(self):
        paso = next(s for s in self.w["jobs"]["entrada"]["steps"] if s.get("name") == "Comprobar tipo, territorio y elección")
        with tempfile.TemporaryDirectory() as t:
            env = {**os.environ, "TIPO": "Espejo de fuente oficial", "TERRITORIO": "aut08", "TERRITORIO_LLAMADA": "",
                   "ELECCION": "vigente", "GITHUB_STEP_SUMMARY": str(Path(t) / "s")}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", paso["run"]], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_territorio_sin_declaracion_falla(self):
        with self.assertRaises(ef.ErrorEspejo) as c:
            ef.declaracion("aut13")
        self.assertEqual(c.exception.codigo, "ESPEJO_SIN_DECLARACION")


if __name__ == "__main__":
    unittest.main()
