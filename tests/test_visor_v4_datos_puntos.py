"""Datos de la situación actual del Congreso 2023 para el visor V5 (T-500, diseño T-499 1.0.1).

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-25 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: visor/v4/mapa/puntos_v5_2023.json trae 52 circunscripciones y 350 escaños, con los valores literales del BOE-A-2023-18907 (Madrid 37
  escaños, PP 1 463 183 votos; 24 487 414 votos a candidaturas), y declara las huellas del CSV y del XML que son las de configuracion/;
  la herramienta para sin escribir si una huella no casa. Si existe el XML del BOE (variable DDD_BOE_2023_XML), regenera el JSON y lo compara byte a byte.
"""
import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import datos_puntos_v5 as h  # noqa: E402

JSON_ = ROOT / "visor/v4/mapa/puntos_v5_2023.json"


class DatosPuntos(unittest.TestCase):
    def setUp(self):
        self.d = json.loads(JSON_.read_text(encoding="utf-8"))

    def test_valores_literales_del_boe(self):
        p = self.d["provincias"]
        self.assertEqual(len(p), 52)
        self.assertEqual(sum(x["escanos"] for x in p.values()), 350)
        self.assertEqual(self.d["votos_candidaturas_estatal"], 24487414)  # fila «Total estatal» de los cuadros II y III
        self.assertEqual(sum(x["votos_candidaturas"] for x in p.values()), 24487414)
        self.assertEqual((p["28"]["nombre"], p["28"]["escanos"], p["28"]["votos_candidaturas"]), ("Madrid", 37, 3579713))
        self.assertEqual(p["28"]["partidos"][0], {"p": "PP", "votos": 1463183, "escanos": 16})
        self.assertEqual((p["08"]["escanos"], p["46"]["escanos"], p["48"]["nombre"]), (32, 16, "Vizcaya"))
        total = {}
        for x in p.values():
            for q in x["partidos"]:
                total[q["p"]] = total.get(q["p"], 0) + q["escanos"]
        self.assertEqual(total, {"PP": 137, "PSOE": 121, "VOX": 33, "SUMAR": 31, "ERC": 7, "JUNTS": 7, "EH Bildu": 6, "EAJ-PNV": 5, "BNG": 1, "CCa": 1, "UPN": 1})

    def test_huellas_declaradas(self):
        meta = json.loads(h.META.read_text(encoding="utf-8"))
        self.assertEqual(self.d["sha256_xml"], meta["sha256_xml"])
        self.assertEqual(self.d["sha256_csv"], meta["sha256_csv"])
        self.assertEqual(hashlib.sha256(h.CSV.read_bytes()).hexdigest(), meta["sha256_csv"])
        self.assertIn("sin votos en blanco", self.d["denominador"])

    def test_para_si_la_huella_no_casa(self):
        meta = json.loads(h.META.read_text(encoding="utf-8"))
        with self.assertRaisesRegex(ValueError, "sha256_xml"):
            h.generar(b"<xml/>", h.CSV.read_bytes(), meta)
        with self.assertRaisesRegex(ValueError, "sha256_csv"):
            xml = b"<xml/>"
            h.generar(xml, b"x", {**meta, "sha256_xml": hashlib.sha256(xml).hexdigest()})

    @unittest.skipUnless(os.environ.get("DDD_BOE_2023_XML"), "sin el XML del BOE (https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-18907)")
    def test_regenera_igual(self):
        meta = json.loads(h.META.read_text(encoding="utf-8"))
        nuevo = h.serializar(h.generar(Path(os.environ["DDD_BOE_2023_XML"]).read_bytes(), h.CSV.read_bytes(), meta))
        self.assertEqual(nuevo, JSON_.read_bytes())


if __name__ == "__main__":
    unittest.main()
