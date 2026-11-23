#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-449 (D-183, D-188): espejo de solo lectura de una fuente oficial desde el runner.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0
FECHA: 2026-11-23
CAMBIOS: 1.0.0: fichero nuevo.
MOTIVO: fija la elección de la distribución del año, el rechazo de la portada HTML, la clave de D-188 y que nunca sobrescribe.
ANTERIOR: ninguna (fichero nuevo)
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
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


class Espejar(unittest.TestCase):
    def setUp(self):
        self.xlsx = b"PK\x03\x04" + b"x" * 100
        p = mock.patch.object(ef, "volcar_xlsx", _volcado_falso)
        p.start()
        self.addCleanup(p.stop)
        self.pdf = b"%PDF-1.4 resultados"

    def _get(self, url, intentos=4):
        if url.endswith(".json"):
            return json.dumps(API).encode()
        if url.endswith("Resultados_CLM_2023.xlsx"):
            return self.xlsx
        if url.endswith(".pdf"):
            return self.pdf
        raise AssertionError(url)

    def test_mide_vuelca_y_no_sobrescribe(self):
        llamadas = []
        remoto = {}

        def aws(args, capturar=False):
            llamadas.append(args)
            if args[:2] == ["s3api", "head-object"]:
                clave = args[args.index("--key") + 1]
                if clave in remoto:
                    return subprocess.CompletedProcess(args, 0, json.dumps({"Metadata": {"sha256": remoto[clave]}}), "")
                return subprocess.CompletedProcess(args, 255, "", "An error occurred (404) when calling the HeadObject operation: Not Found")
            return subprocess.CompletedProcess(args, 0, "", "")

        with tempfile.TemporaryDirectory() as td, mock.patch.dict(os.environ, {"R2_BUCKET": "b", "R2_ACCOUNT_ID": "a"}):
            m = ef.espejar("aut08", Path(td), True, get=self._get, aws=aws)
            datos = m["piezas"][0]
            self.assertEqual(datos["clave"], "fuentes/junta-castilla-la-mancha/2023/autonomicas-por-municipio.xlsx")
            self.assertEqual(datos["sha256"], ef.hashlib.sha256(self.xlsx).hexdigest())
            self.assertEqual(datos["bytes"], len(self.xlsx))
            self.assertEqual(datos["r2"], "subido")
            self.assertEqual(datos["volcado_csv"][0]["hoja"], "Municipios")
            self.assertEqual((Path(td) / "volcado" / "hoja-1.csv").read_text(encoding="utf-8").splitlines()[1], "Albacete,10,20")
            self.assertEqual(m["piezas"][1]["clave"], "fuentes/junta-castilla-la-mancha/2023/resultados-oficiales.pdf")
            self.assertTrue(json.loads((Path(td) / "manifiesto.json").read_text(encoding="utf-8"))["piezas"])
            # Misma huella ya en R2: no se vuelve a subir.
            remoto[datos["clave"]] = datos["sha256"]
            remoto[m["piezas"][1]["clave"]] = m["piezas"][1]["sha256"]
            llamadas.clear()
            m2 = ef.espejar("aut08", Path(td), True, get=self._get, aws=aws)
            self.assertEqual([p["r2"] for p in m2["piezas"]], ["ya_estaba", "ya_estaba"])
            self.assertFalse([a for a in llamadas if a[:2] == ["s3", "cp"]])  # ni piezas ni manifiesto
            # Otra huella en R2: falla sin escribir.
            remoto[datos["clave"]] = "0" * 64
            llamadas.clear()
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar("aut08", Path(td), True, get=self._get, aws=aws)
            self.assertEqual(c.exception.codigo, "ESPEJO_HUELLA_DISTINTA")
            self.assertFalse([a for a in llamadas if a[:2] == ["s3", "cp"]])

    def test_portada_en_obras_no_llega_a_r2(self):
        def get(url, intentos=4):
            return json.dumps(API).encode() if url.endswith(".json") else b"<html><body>En obras</body></html>"

        aws = mock.Mock()
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ef.ErrorEspejo) as c:
                ef.espejar("aut08", Path(td), True, get=get, aws=aws)
        self.assertEqual(c.exception.codigo, "ESPEJO_ES_HTML")
        aws.assert_not_called()


class JobP10(unittest.TestCase):
    """El job `p13_espejo` de P10 1.0.2: solo desde el botón, sin campaña, secretos en el paso y sin escribir en main."""

    @classmethod
    def setUpClass(cls):
        import yaml

        cls.w = yaml.safe_load((ROOT / ".github" / "workflows" / "p10-fuentes.yml").read_text(encoding="utf-8"))
        cls.j = cls.w["jobs"]["p13_espejo"]

    def test_opcion_y_condicion(self):
        tipo = (self.w.get("on") or self.w[True])["workflow_dispatch"]["inputs"]["tipo"]
        self.assertEqual(tipo["options"], ["P11 territoriales", "P12 electorales", "Espejo de fuente oficial"])
        self.assertEqual(self.j["if"], "${{ inputs.tipo == 'Espejo de fuente oficial' && !inputs.campana }}")
        self.assertEqual(self.j["needs"], "entrada")

    def test_secretos_en_el_paso_y_herramienta(self):
        self.assertNotIn("env", self.j)
        paso = next(s for s in self.j["steps"] if s.get("name") == "Bajar, medir y subir a R2 en solo lectura")
        self.assertEqual(paso["env"]["AWS_SECRET_ACCESS_KEY"], "${{ secrets.R2_SECRET_ACCESS_KEY }}")
        self.assertIn('herramientas/espejo_fuente_oficial.py espejar --territorio "$TERRITORIO"', paso["run"])
        self.assertIn("--subir", paso["run"])
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
