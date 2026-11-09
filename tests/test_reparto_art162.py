"""Oráculo del reparto art. 162 y D'Hondt (T-129). Los valores esperados son oficiales y de fuente independiente:
- escaños 2026: anexo del RD 806/2026 (BOE-A-2026-20742) en configuracion/escanos_oficiales_congreso_2026.csv;
- escaños y votos 2023: BOE-A-2023-18907 en configuracion/resultados_oficiales_congreso_2023.csv;
- población: RD 1117/2025 (BOE-A-2025-25362, 1-1-2025) y RD 1037/2022 (BOE-A-2022-21724, 1-1-2022), transcritos en
  configuracion/poblacion_oficial_provincias_*.csv con el sha256 del XML del BOE en la cabecera."""
import csv
import hashlib
import json
import unittest
from collections import defaultdict
from pathlib import Path

from herramientas.reparto_art162 import dhondt, repartir

R = Path(__file__).resolve().parents[1]
C = R / "configuracion"
POB25, POB22 = (C / f"poblacion_oficial_provincias_{f}-01-01.csv" for f in ("2025", "2022"))
POB65034 = R / "docs/ESTUDIOS/modelo_nacional_2025_120000/fuente_poblacion.json"
CSV26 = C / "escanos_oficiales_congreso_2026.csv"
RES23 = C / "resultados_oficiales_congreso_2023.csv"


def _csv(p):
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(l for l in f if not l.startswith("#")))


def _pob(p):
    return {r["codigo"]: int(r["poblacion"]) for r in _csv(p)}


def _sha_cabecera(p):
    return next(l.split(":", 1)[1].strip() for l in p.open(encoding="utf-8") if l.startswith("# SHA256_XML"))


class Reparto(unittest.TestCase):
    def test_fuentes_con_huella(self):
        self.assertEqual(_sha_cabecera(POB25), "c557f3932692291d19956e05748ca5f0aeaeeb5947bf56eeacc361bd11ae3d69")
        self.assertEqual(_sha_cabecera(POB22), "681d56a76ad304fff94724d956abfd3d405bd983204ca3589d5e5e013f31d340")
        self.assertEqual(hashlib.sha256(CSV26.read_bytes()).hexdigest(),
                         "9c9b48c1dcefe1aac327aa0211fc5f7c57130f83e5929dab25cbac352d182b8f")

    def test_2026_cifras_oficiales_50_de_50_mas_ceuta_melilla(self):
        oficial = {r["codigo"]: int(r["escanos_2026"]) for r in _csv(CSV26)}
        calc = repartir(_pob(POB25))
        self.assertEqual(len(calc), 52)
        self.assertEqual(calc, oficial)
        self.assertEqual((calc["28"], calc["11"], calc["13"], calc["38"]), (38, 8, 5, 7))

    def test_2026_padron_65034_difiere_en_ciudad_real_y_tenerife(self):
        # Otra publicación del INE (padrón por secciones, tabla 65034): 241 habitantes deciden el último escaño.
        rows = json.loads(POB65034.read_text("utf-8"))["rows"]
        calc = repartir({r["province_code"]: r["population"] for r in rows})
        oficial = {r["codigo"]: int(r["escanos_2026"]) for r in _csv(CSV26)}
        self.assertEqual({k for k in oficial if calc[k] != oficial[k]}, {"13", "38"})

    def test_2023_cifras_oficiales_reproducen_escanos(self):
        oficial = {}
        for r in _csv(RES23):
            oficial[r["codigo"]] = int(r["escanos_circunscripcion"])
        self.assertEqual(len(oficial), 52)
        self.assertEqual(repartir(_pob(POB22)), oficial)

    def test_2023_dhondt_punta_a_punta_huesca(self):
        # población oficial -> escaños (reparto) -> D'Hondt con los votos oficiales -> escaños por partido oficiales
        esc = repartir(_pob(POB22))["22"]
        votos = {r["partido"]: int(r["votos"]) for r in _csv(RES23) if r["codigo"] == "22"}
        oficial = {r["partido"]: int(r["escanos"]) for r in _csv(RES23) if r["codigo"] == "22"}
        self.assertEqual(esc, 3)
        self.assertEqual(dhondt(votos, esc), oficial)

    def test_2023_dhondt_todas_las_provincias(self):
        por_prov = defaultdict(list)
        for r in _csv(RES23):
            por_prov[r["codigo"]].append(r)
        malas = []
        for cod, filas in por_prov.items():
            votos = {r["partido"]: int(r["votos"]) for r in filas}
            oficial = {r["partido"]: int(r["escanos"]) for r in filas}
            if dhondt(votos, int(filas[0]["escanos_circunscripcion"])) != oficial:
                malas.append(cod)
        self.assertEqual(malas, [])


if __name__ == "__main__":
    unittest.main()
