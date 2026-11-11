# -*- coding: utf-8 -*-
"""PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-10 · ANTERIOR: ninguna (fichero nuevo)
Tests de T-225 (D-65): las 52 circunscripciones del Congreso con el par INE 2025/2025 y la equivalencia de las
secciones del ZIP de Interior de 2023 con el seccionado 2025."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import resultados_partidos as rp  # noqa: E402

TABLA_2025 = ROOT / "configuracion/equivalencia_secciones_congreso_2023_seccionado2025.csv"


class Contratos(unittest.TestCase):
    def test_52_contratos_y_declaraciones_en_2025(self):
        ids = sorted(p.name for p in (ROOT / "territorios").iterdir() if p.name.startswith("congreso_"))
        self.assertEqual(len(ids), 52)
        for t in ids:
            with self.subTest(territorio=t):
                c = yaml.safe_load((ROOT / f"territorios/{t}/config/{t}_2025.yaml").read_text(encoding="utf-8"))
                self.assertEqual(c["meta"]["source_population_year"], 2025)
                self.assertEqual(c["meta"]["source_section_year"], 2025)
                self.assertEqual(c["io"]["input"]["seccionado"]["path"], "inputs/seccionado_2025.zip")
                self.assertEqual(c["io"]["input"]["population_cip"]["filters"]["year_value"], 2025)
                self.assertEqual(c["validation"]["source_baseline"]["population_year"], 2025)
                self.assertNotIn("POP_2023", json.dumps(c))
                f = yaml.safe_load((ROOT / f"territorios/{t}/config/fuentes_oficiales.yaml").read_text(encoding="utf-8"))
                self.assertEqual((f["territory"]["population_year"], f["territory"]["section_year"]), (2025, 2025))
                self.assertEqual(f["source_bindings"]["secciones_censales"]["materialized_path"], "inputs/seccionado_2025.zip")

    def test_gemelos_350_siguen_en_2023(self):
        c = yaml.safe_load((ROOT / "territorios/congreso350_soria/config/congreso350_soria_2025.yaml").read_text(encoding="utf-8"))
        self.assertEqual(c["meta"]["source_population_year"], 2023)

    def test_puentes_2025(self):
        # Tremp: la sección 2523403001 no existe en el seccionado INE 2025; Herrera de Duero (Tudela, 47175) sí.
        def puentes(t):
            c = yaml.safe_load((ROOT / f"territorios/{t}/config/{t}_2025.yaml").read_text(encoding="utf-8"))
            return {(str(b["u"]), str(b["v"])) for b in c["modulos"]["modulo_02_construir_adyacencias"]["topology_bridges"]}
        self.assertNotIn(("2523401002", "2523403001"), puentes("congreso_lerida"))
        self.assertIn(("4717501004", "4717501003"), puentes("congreso_valladolid"))


class Equivalencia2025(unittest.TestCase):
    def test_tabla_2025_con_sha256(self):
        t = rp.leer_equivalencia(TABLA_2025)  # comprueba el sha256 del CSV contra su JSON
        # literal de configuracion/equivalencia_secciones_congreso_2023_seccionado2025.csv (Madrid)
        self.assertIn({"seccion_m06": "2807901123", "tipo": "reparto", "peso_area": 1.0, "frac_m06": 0.659114},
                      t["2807901124"])
        meta = json.loads(TABLA_2025.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(len(meta["provincias"]), 52)
        self.assertTrue(all(k.startswith("congreso_") for k in meta["provincias"]))
        self.assertEqual(meta["fuentes"]["seccionado_m06"]["sha256"],
                         "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4")

    def _tablas(self, d: Path, huella: str) -> Path:
        csv_ = d / "eq2025.csv"
        csv_.write_text("seccion_zip,seccion_m06,tipo,peso_area,frac_m06\n", encoding="utf-8")
        csv_.with_suffix(".json").write_text(json.dumps({"csv": {"sha256": rp.sha256(csv_.read_bytes())}, "provincias": {
            "congreso_soria": {"provincia": "42", "sha256_secciones_m06": huella}}}), encoding="utf-8")
        return csv_

    def test_elige_la_tabla_del_seccionado_de_la_composicion(self):
        with tempfile.TemporaryDirectory() as td:
            # sha256 de «4200101001\n4200101002» (sha256sum)
            t = self._tablas(Path(td), "74404f062d2b1a14880614094efe0fb2d9d87417695eeb0de52921bc5558b5bc")
            self.assertEqual(rp.elegir_equivalencia({"4200101002": 1, "4200101001": 1}, (t,)), t)

    def test_otro_seccionado_usa_la_tabla_2023(self):
        with tempfile.TemporaryDirectory() as td:
            t = self._tablas(Path(td), "74404f062d2b1a14880614094efe0fb2d9d87417695eeb0de52921bc5558b5bc")
            self.assertEqual(rp.elegir_equivalencia({"4200101001": 1, "4200101003": 1}, (t,)), rp.EQUIVALENCIA)
            self.assertEqual(rp.elegir_equivalencia({"4200101001": 1}, (Path(td) / "no_existe.csv",)), rp.EQUIVALENCIA)


if __name__ == "__main__":
    unittest.main()
