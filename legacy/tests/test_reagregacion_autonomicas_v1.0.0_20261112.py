#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: prueba de la reagregación autonómica (T-121)
VERSIÓN: 1.0.0 · FECHA: 2026-11-09 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: casos sintéticos con valores a mano y comprobación del resultado real contra literales de la fuente del Observatorio.
"""
import csv
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import reagregacion_autonomicas as ra  # noqa: E402

SAL = ROOT / "datos/resultados/historico/autonomicas"


class Sinteticos(unittest.TestCase):
    def test_total_autonomico(self):
        doc = {"s": ["PP", "BNG"], "autonomia": [100, 80, 70, [[0, 40], [1, 30]]]}
        self.assertEqual(ra.total_autonomico(doc), {"votos_candidaturas": 70, "votos": {"PP": 40, "BNG": 30}})

    def test_completar_composicion_asigna_al_distrito_contiguo(self):
        from shapely.geometry import box
        vig = {"a": box(0, 0, 10, 10), "b": box(10, 0, 20, 10), "c": box(20, 0, 30, 10), "n": box(11, 10, 19, 12)}
        comp, asg = ra.completar_composicion({"a": "1", "b": "2", "c": "2"}, vig)
        self.assertEqual(asg, [("n", "2")])
        self.assertEqual(comp["n"], "2")

    def test_composicion_completa_no_cambia(self):
        from shapely.geometry import box
        comp = {"a": "1"}
        self.assertEqual(ra.completar_composicion(comp, {"a": box(0, 0, 1, 1)}), (comp, []))

    def test_homologacion_ausente_deja_la_sigla(self):
        self.assertEqual(ra.ganador_h({"X": 5, "Y": 3}, {}, "c", "201105", set()), "X")

    def test_homologacion_suma_familia(self):
        hom = {("c", "e", "A1"): "A", ("c", "e", "A2"): "A", ("c", "e", "B"): "B"}
        self.assertEqual(ra.ganador_h({"A1": 3, "A2": 3, "B": 5}, hom, "c", "e", set()), "A")


class Cera(unittest.TestCase):
    def test_pseudoseccion_cera_se_identifica_por_su_total(self):
        votos = {"a": {"votos_candidaturas": 500}, "cera": {"votos_candidaturas": 998}}
        self.assertEqual(ra.cera_en_secciones(votos, {"a": 1}, 998), ["cera"])

    def test_seccion_real_sin_geometria_no_es_cera(self):
        votos = {"a": {"votos_candidaturas": 500}, "x": {"votos_candidaturas": 998}}
        self.assertEqual(ra.cera_en_secciones(votos, {"a": 1, "x": 1}, 998), [])
        self.assertEqual(ra.cera_en_secciones(votos, {"a": 1}, 0), [])


class Resultado(unittest.TestCase):
    def test_galicia_2024_suma_literal_de_la_fuente(self):
        # total de votos a candidaturas de Galicia 2024-02 en data/autonomikoak/hauteskundea/12-202402.json (Observatorio)
        with open(SAL / "galicia/202402/galicia.csv", encoding="utf-8", newline="") as f:
            filas = list(csv.DictReader(f))
        self.assertEqual(sum(int(r["votos_candidaturas"]) for r in filas), 1466201)
        self.assertEqual(sum(int(r["votantes"]) for r in filas), 1492984)

    def test_las_comunidades_entregadas_cuadran(self):
        esperadas = {"galicia": 4, "madrid": 5, "castilla_y_leon": 5, "cataluna": 5, "comunidad_valenciana": 4,
                     "comunidad_foral_de_navarra": 4, "pais_vasco": 4, "la_rioja": 4, "canarias": 4}
        for com, n in esperadas.items():
            m = json.loads((SAL / com / "MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(len(m["elecciones"]), n, com)
            self.assertEqual(m["no_cuadran"], [], com)
            for e, x in m["elecciones"].items():
                self.assertLessEqual(x["perdida_frente_fuente"], ra.TOPE_D17, f"{com} {e}")

    def test_elecciones_coinciden_con_el_calendario(self):
        cal = ra.leer_calendario()
        for com in ("galicia", "madrid", "castilla_y_leon", "cataluna", "pais_vasco", "la_rioja", "canarias"):
            self.assertEqual(sorted(p.name for p in (SAL / com).iterdir() if p.is_dir()),
                             sorted(f["mes"].replace("-", "") for f in cal[com]), com)


if __name__ == "__main__":
    unittest.main()
