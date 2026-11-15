#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de las tablas año→2023 del histórico y de los identificadores BOE (T-328)
VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: provincia sintética (valores a mano: sección partida entera a la mayor población, sin repartir votos); la tabla de
  sha256 coincide con la auditoría T-85; la herramienta para sin escribir si falta un ZIP; las 5 tablas escritas llevan su
  sha256 correcto y sus ZIP de origen; los 4 identificadores BOE llevan sha256 y el título de la elección esperada.
"""
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
try:
    from shapely.geometry import box
    import equivalencia_historico_2023 as h
except ImportError:  # pragma: no cover
    h = None


@unittest.skipIf(h is None, "shapely no instalado")
class Tablas(unittest.TestCase):
    def test_partida_va_entera_al_distrito_mayor_poblacion_sin_repartir_votos(self):
        vig = {"0100100001": box(0, 0, 10, 10), "0100100002": box(10, 0, 20, 10)}
        hist = {"0100100001": box(0, 0, 10, 10), "0100100009": box(5, 0, 15, 10)}  # H9 mitad en V1, mitad en V2
        filas, prov = h.tabla_anio({"01": hist}, {"01": vig}, {"0100100001": 100, "0100100002": 300})
        self.assertEqual([f[:3] for f in filas], [["0100100009", "0100100001", "partida"], ["0100100009", "0100100002", "partida"]])
        self.assertEqual([f[4] for f in filas], ["0.250000", "0.750000"])  # peso de población: V2 recibe la sección
        self.assertEqual(prov["01"]["tipo_partida"], 1)
        self.assertEqual(prov["01"]["secciones_hist_sin_2023"], 1)

    def test_fuentes_coinciden_con_la_auditoria_t85(self):
        informe = json.loads((ROOT / "docs/AUDITORIAS/T85_EQUIVALENCIA_SECCIONADOS/informe.json").read_text("utf-8"))
        for anio, (_, sha) in h.TABLA_FUENTES.items():
            self.assertEqual(informe["fuentes"]["historicos"][anio]["sha256"], sha)

    def test_para_sin_escribir_si_falta_un_zip(self):
        with tempfile.TemporaryDirectory() as d:
            vacio = Path(d)
            antes = {p.name for p in (ROOT / "configuracion").iterdir()}
            rc = h.main(["--historicos", str(vacio), "--s2023", str(vacio / "x.zip"), "--padron", str(vacio / "p.zip")])
            self.assertEqual(rc, 2)
            self.assertEqual(antes, {p.name for p in (ROOT / "configuracion").iterdir()})


@unittest.skipIf(h is None, "shapely no instalado")
class TablasEscritas(unittest.TestCase):
    def test_csv_y_json_de_cada_anio(self):
        for anio, (eleccion, sha) in h.TABLA_FUENTES.items():
            meta = json.loads(h.salida_csv(anio).with_suffix(".json").read_text("utf-8"))
            cuerpo = h.salida_csv(anio).read_bytes()
            self.assertEqual(meta["csv"]["sha256"], hashlib.sha256(cuerpo).hexdigest())
            self.assertEqual(meta["eleccion"], eleccion)
            self.assertEqual(meta["fuentes"][f"seccionado_{anio}"]["sha256"], sha)
            self.assertEqual(meta["fuentes"]["seccionado_2023"]["sha256"], h.SHA_2023)
            self.assertEqual(cuerpo.decode("utf-8").splitlines()[0], ",".join(h.cabecera(anio)))
            self.assertEqual(meta["nacional"]["poblacion_2023"] > 4.5e7, True)


class IdentificadoresBoe(unittest.TestCase):
    def test_cuatro_elecciones_con_huella_y_titulo(self):
        d = json.loads((ROOT / "configuracion/identificadores_boe_resultados_congreso.json").read_text("utf-8"))
        esperado = {"2011-11": "20 de noviembre de 2011", "2015-12": "20 de diciembre de 2015",
                    "2016-06": "26 de junio de 2016", "2019-04": "28 de abril de 2019"}
        self.assertEqual(set(d["elecciones"]), set(esperado))
        for e, fecha in esperado.items():
            x = d["elecciones"][e]
            self.assertRegex(x["boe"], r"^BOE-A-\d{4}-\d+$")
            self.assertTrue(x["url"].endswith(x["boe"]))
            self.assertRegex(x["sha256_xml"], r"^[0-9a-f]{64}$")
            self.assertIn(f"celebradas el {fecha}", x["titulo"])
            self.assertIn("Junta Electoral Central", x["titulo"])
            self.assertTrue(re.match(r"^\d{4}-\d{2}-\d{2}$", x["fecha_publicacion"]))


if __name__ == "__main__":
    unittest.main()
