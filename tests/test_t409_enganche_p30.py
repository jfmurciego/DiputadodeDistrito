#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: enganche de la doble vuelta a P30 y archivo en origen de la tabla por partido (T-409, D-171)
VERSIÓN: 1.0.0 · FECHA: 2026-11-19 · ESTADO: candidato
ANTERIOR: ninguna (fichero nuevo)
FUNCIÓN: fija (1) que el paquete de R2 ya incluye la tabla por partido y distrito de M07; (2) que la doble vuelta en P30 es no fatal,
  solo con persistir y sin campaña, y sin escritura en main; (3) que sin la doble vuelta P30 es igual que la 1.0.1; (4) la cobertura
  de la tabla de bloques (sin casar ≠ sin bloque) con valores a mano.
"""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))
import archivar_artefactos_r2 as ar  # noqa: E402
import doble_vuelta_cobertura as cob  # noqa: E402

WF = ROOT / ".github/workflows/p30-resultados-electorales.yml"
WF_ANTES = ROOT / "tests/fixtures/t409_workflows/p30-resultados-electorales_1.0.1.yml"  # copia congelada (en CI no hay legacy/)
PASO_DV = "Doble vuelta con coaliciones (D-171; no fatal)"
PASO_ARCHIVO = "Archivo en origen — M08 a R2 y votos por partido a git"
EXTRA = '''          extra=(); [[ -d "$GITHUB_WORKSPACE/doble_vuelta" ]] && extra=(--extra "$GITHUB_WORKSPACE/doble_vuelta")\n'''


def pasos(texto: str) -> list[dict]:
    return yaml.safe_load(texto)["jobs"]["incorporar"]["steps"]


class ArchivoEnOrigen(unittest.TestCase):
    def test_paquete_r2_incluye_la_tabla_por_partido_y_distrito(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "cache").mkdir()
            for n in ("run_m07_resultados_partido.csv", "run_m07_resumen_electoral.csv", "otro.csv"):
                (d / "cache" / n).write_text("x\n", encoding="utf-8")
            nombres = [f.name for f in ar.seleccionar_paquete(d)]
        self.assertIn("run_m07_resultados_partido.csv", nombres)
        self.assertNotIn("otro.csv", nombres)

    def test_paso_de_archivo_sube_el_paquete_a_r2_solo_sin_campana(self):
        p = next(s for s in pasos(WF.read_text(encoding="utf-8")) if s.get("name") == PASO_ARCHIVO)
        self.assertIn("archivo_origen.py r2", p["run"])
        self.assertIn("!inputs.campana", p["if"])


class DobleVueltaEnP30(unittest.TestCase):
    def setUp(self):
        self.texto = WF.read_text(encoding="utf-8")
        self.paso = next(s for s in pasos(self.texto) if s.get("name") == PASO_DV)

    def test_no_fatal_y_sin_campana(self):
        self.assertIs(self.paso.get("continue-on-error"), True)
        self.assertIn("!inputs.campana", self.paso["if"])
        self.assertIn("persistir == 'true'", self.paso["if"])

    def test_no_escribe_en_main_ni_sube_nada(self):
        run = self.paso["run"]
        for prohibido in ("git push", "registrar_en_main", "upload-artifact", "aws ", "archivo_origen"):
            self.assertNotIn(prohibido, run)
        self.assertIn("doble_vuelta.py", run)
        self.assertIn("doble_vuelta_cobertura.py", run)

    def test_el_directorio_solo_queda_si_ambas_herramientas_terminan_bien(self):
        run = self.paso["run"]
        i = {k: run.index(k) for k in ("rm -rf doble_vuelta\n", "trap '", "mkdir -p doble_vuelta", "doble_vuelta_cobertura.py", "herramientas/doble_vuelta.py", "ok=1")}
        self.assertEqual(sorted(i, key=i.get), ["rm -rf doble_vuelta\n", "trap '", "mkdir -p doble_vuelta", "doble_vuelta_cobertura.py", "herramientas/doble_vuelta.py", "ok=1"])
        self.assertIn('[[ "$ok" == 1 ]] || rm -rf doble_vuelta', run)

    def test_ambas_herramientas_pasan_el_alias(self):
        run = self.paso["run"]
        self.assertEqual(run.count('--alias "$alias"'), 2)
        self.assertIn("alias=configuracion/alias_partidos_generales.csv", run)
        self.assertTrue((ROOT / "configuracion/alias_partidos_generales.csv").is_file())

    def test_va_despues_de_m08_y_antes_del_archivo(self):
        n = [s.get("name") for s in pasos(self.texto)]
        self.assertLess(n.index("Generar producto electoral territorial"), n.index(PASO_DV))
        self.assertLess(n.index(PASO_DV), n.index(PASO_ARCHIVO))

    def test_la_salida_va_al_paquete_de_r2_con_extra(self):
        self.assertIn(EXTRA, self.texto)

    def test_sin_la_doble_vuelta_p30_es_igual_que_la_1_0_1(self):
        self.assertTrue(WF_ANTES.is_file(), WF_ANTES)
        from tests._t379_2a import deshacer as sin_2a  # T-379 PR 2a: sin el entorno `registro`
        nuevo, antes = sin_2a("p30-resultados-electorales", yaml.safe_load(self.texto)), yaml.safe_load(WF_ANTES.read_text(encoding="utf-8"))
        n = copy.deepcopy(nuevo)
        n["jobs"]["incorporar"]["steps"] = [s for s in n["jobs"]["incorporar"]["steps"] if s.get("name") != PASO_DV]
        for s in n["jobs"]["incorporar"]["steps"]:
            if s.get("name") == PASO_ARCHIVO:
                s["run"] = s["run"].replace(EXTRA.lstrip(), "").replace(' "${extra[@]}"', "")
        self.assertEqual(n, antes)


class Cobertura(unittest.TestCase):
    def test_normalizar_eleccion(self):
        self.assertEqual(cob.normalizar_eleccion("2023-07"), "2023-07")
        self.assertEqual(cob.normalizar_eleccion("congreso_2023-07-23"), "2023-07")
        for malo in ("", "galicia_2024", "2023-13"):
            with self.assertRaises(ValueError):
                cob.normalizar_eleccion(malo)

    def test_sin_casar_distinto_de_sin_bloque(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n1,PP,50,\n1,PSE-EE (PSOE),30,\n2,Cs,20,\n", encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n"
                                     "2023-07,PP,PP,Derecha nacional,x\n2023-07,PSOE,PSOE,Izquierdas,x\n2023-07,Cs,Cs,,x\n"
                                     "2019-11,PSE-EE (PSOE),x,Izquierdas,x\n", encoding="utf-8")
            c = cob.cobertura(d / "v.csv", d / "b.csv", "congreso_2023-07-23")
            # 100 votos: PSE-EE (PSOE) no casa (30 %), Cs casa sin bloque (20 %), PP casa con bloque
            self.assertEqual((c["votos_total"], c["votos_sin_casar"], c["pct_sin_casar"]), (100, 30, 30.0))
            self.assertEqual((c["votos_sin_bloque"], c["pct_sin_bloque"]), (20, 20.0))
            self.assertEqual(c["partidos_sin_casar"], [{"partido": "PSE-EE (PSOE)", "votos": 30}])

    def test_cli_avisa_si_hay_votos_sin_casar_y_sale_0(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n1,PP,60,\n1,SUMAR,40,\n", encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n2023-07,PP,PP,Derecha nacional,x\n", encoding="utf-8")
            sys.argv = ["x", "--votos", str(d / "v.csv"), "--bloques", str(d / "b.csv"), "--eleccion", "2023-07", "--salida", str(d / "c.json")]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cob.main()
            self.assertIn("::warning title=DOBLE_VUELTA_COBERTURA::40.0 %", out.getvalue())
            self.assertEqual(json.loads((d / "c.json").read_text())["votos_sin_casar"], 40)

    def test_con_alias_los_ids_de_la_fuente_casan(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n1,PP-EU,60,\n1,SUMAR,40,\n", encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n2023-07,PP,PP,Derecha nacional,x\n"
                                     "2023-07,Podemos–Sumar,x,Izquierdas,x\n", encoding="utf-8")
            (d / "a.csv").write_text("eleccion,id_fuente,partido_homologado,origen,fuente\n202307,PP-EU,PP,H,x\n202307,SUMAR,Podemos–Sumar,H,x\n", encoding="utf-8")
            sin = cob.cobertura(d / "v.csv", d / "b.csv", "2023-07")
            con = cob.cobertura(d / "v.csv", d / "b.csv", "2023-07", d / "a.csv")
            self.assertEqual((sin["votos_sin_casar"], con["votos_sin_casar"]), (100, 0))
            self.assertEqual(con["entradas"]["alias"]["sha256"], cob.sha256(d / "a.csv"))

    def test_sin_aviso_con_cobertura_total(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "v.csv").write_text("district_id,party,votes,bloc\n1,PP,60,\n", encoding="utf-8")
            (d / "b.csv").write_text("eleccion,siglas,denominacion,bloque_propuesto,motivo\n2023-07,PP,PP,Derecha nacional,x\n", encoding="utf-8")
            sys.argv = ["x", "--votos", str(d / "v.csv"), "--bloques", str(d / "b.csv"), "--eleccion", "2023-07", "--salida", str(d / "c.json")]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                cob.main()
            self.assertNotIn("::warning", out.getvalue())


if __name__ == "__main__":
    unittest.main()
