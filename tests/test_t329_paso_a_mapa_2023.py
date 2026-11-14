#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba del paso A del histórico sobre el mapa 2023 (T-329, D-105)
VERSIÓN: 1.0.0 · FECHA: 2026-11-14 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: una provincia (Álava, elección 2011-11, seccionado 2012) contra la tabla de T-328: los destinos esperados están
  escritos a mano desde las filas de la tabla y la composición del M06; el paquete lleva los votos por sección histórica
  (sin reagregar), declara la tabla en el contrato y la participación va al mapa 2023; la regla coincide con la que
  aplica M07 7.4.0 a las mismas secciones. El camino anterior (reagregación a 2025) ya no es el predeterminado.
"""
import csv
import importlib.util
import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
sys.path.insert(0, str(ROOT))
try:
    import pandas as pd
    import historico_campana as hc
except ImportError:  # pragma: no cover
    hc = None

CLAVE, TERR = "201111", "congreso_alava"


def composicion():
    with open(ROOT / "datos/composicion/congreso_alava.csv", encoding="utf-8", newline="") as f:
        return {r["seccion"]: (r["distrito"], int(r["poblacion"])) for r in csv.DictReader(f)}


@unittest.skipIf(hc is None, "dependencias no instaladas")
class PasoAMapa2023(unittest.TestCase):
    def test_destino_de_secciones_partidas_a_mano(self):
        t, d = hc.leer_tabla(hc.tabla_2023(CLAVE)), {s: x for s, (x, _) in composicion().items()}
        # 0105901008 → 0,19 al distrito 1 y 0,81 al 2; 0105901009 → 0,47 al 1 (5 y 10) y 0,53 al 2; 0105902023 → 0,31 al 0 y 0,69 al 1
        self.assertEqual(hc.seccion_destino(t["0105901008"], d), "0105901008")
        self.assertEqual(hc.seccion_destino(t["0105901009"], d), "0105901008")
        self.assertEqual(hc.seccion_destino(t["0105902023"], d), "0105902023")

    def test_paquete_por_seccion_historica_con_tabla_en_el_contrato(self):
        comp = composicion()
        votos = {s: {"censo": 10, "votantes": 8, "votos_candidaturas": 7, "votos": {"PP": 4, "PSOE": 3}}
                 for s in ("0105901008", "0105901009", "0105902023", "0100101001")}
        with tempfile.TemporaryDirectory() as tmp:
            carpeta = Path(tmp) / CLAVE / TERR
            hc.paquete_2023(carpeta, TERR, CLAVE, votos, comp, "data/201111/sekzioa/01.json", "0" * 64, None)
            filas = list(csv.DictReader(open(carpeta / "secciones.csv", encoding="utf-8")))
            self.assertEqual({r["section_id"] for r in filas}, set(votos))  # sin reagregar: secciones históricas
            self.assertEqual(sum(int(r["votes"]) for r in filas), 28)  # sin repartir ni perder votos
            part = {r["section_id"]: int(r["votos_candidaturas"]) for r in csv.DictReader(open(carpeta / "participacion.csv"))}
            self.assertEqual(part, {"0105901008": 14, "0105902023": 7, "0100101001": 7})  # 08 y 09 → 0105901008
            con = json.loads((carpeta / "contrato.json").read_text(encoding="utf-8"))
            rec = con["section_reconciliation"]["equivalence_table"]
            self.assertEqual(rec["path"], "configuracion/equivalencia_seccionado_ine_2012_a_2023.csv")
            self.assertEqual(rec["sha256"], hc.sha256(hc.tabla_2023(CLAVE)))
            self.assertEqual((rec["source_column"], rec["target_column"]), ("seccion_2012", "seccion_2023"))

    def test_la_regla_coincide_con_m07(self):
        spec = importlib.util.spec_from_file_location("m07", ROOT / "modulos/07_agregar_resultados_electorales.py")
        m07 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m07)
        comp = composicion()
        tabla = hc.tabla_2023(CLAVE)
        tm, _ = m07.load_section_equivalence(hc.registro_tabla(tabla), project_root=ROOT)
        fuentes = sorted(s for s in tm if s.startswith("01") and tm[s]["tipo"] != "sin_vigente")
        mapa = pd.DataFrame({"sec": list(comp), "dist": [d for d, _ in comp.values()]})
        entrada = pd.DataFrame({"sec": fuentes, "party": "PP", "votes": 1})
        out, _ = m07.apply_section_equivalence(entrada, mapa, section_field="sec", district_field="dist", table=tm)
        esperado = {}
        for s in fuentes:
            k = hc.seccion_destino(hc.leer_tabla(tabla)[s], {x: d for x, (d, _) in comp.items()})
            esperado[k or s] = esperado.get(k or s, 0) + 1
        self.assertEqual(dict(zip(out["sec"], out["votes"])), esperado)

    def test_el_mapa_por_defecto_es_2023(self):
        self.assertEqual(inspect.signature(hc.ejecutar).parameters["mapa"].default, "2023")
        with self.assertRaises(SystemExit):
            hc.ejecutar(TERR, "01", CLAVE, Path("/nonexistent"), Path("/nonexistent"), mapa="2024")


if __name__ == "__main__":
    unittest.main()
