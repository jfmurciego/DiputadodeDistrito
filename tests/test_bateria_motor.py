"""T-132: batería del motor (herramientas/bateria_motor.py)."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import bateria_motor as b

ROOT = Path(__file__).resolve().parents[1]


class BateriaMotor(unittest.TestCase):
    def test_territorios_son_52_congreso_y_19_comunidades(self):
        ts = b.territorios()
        self.assertEqual(len([t for t in ts if t.startswith("congreso_")]), 52)
        self.assertEqual(len([t for t in ts if not t.startswith("congreso_")]), 19)

    def test_reglas_salen_del_informe_de_validar_ejecucion(self):
        ok = {"estado": "PASS", "districts_found": 2, "failures": []}
        self.assertTrue(all(b._reglas(ok).values()))
        mal = {"estado": "FAIL", "districts_found": 3, "below_floor": [{"district_id": 1}],
               "graph_disconnected": [{"district_id": 2, "components": 2}],
               "municipality_violations": [{"municipality_id": "22125"}],
               "failures": ["distritos=3, esperados=2", "distritos bajo límite poblacional=1",
                            "distritos desconectados en grafo=1", "municipios con fragmentación inválida=1",
                            "algo nuevo"]}
        r = b._reglas(mal)
        self.assertEqual({k for k, v in r.items() if not v}, {"K", "poblacion", "contiguidad", "municipal", "otras"})
        self.assertTrue(r["provincia"] and r["atomicidad"])

    def test_versiones_del_motor_m05_existen(self):
        # La imagen de CI excluye legacy/ (.dockerignore): allí solo se exige el motor vigente; las legacy, en el árbol.
        self.assertTrue(b.M05_BASE["7.4.4"].is_file())
        for v, p in b.M05_BASE.items():
            if (ROOT / ".git").exists():  # árbol completo (la imagen de CI no lleva .git ni todo legacy/)
                self.assertTrue(p.is_file(), v)

    def test_comparacion_con_publicado_ignora_etiquetas(self):
        with tempfile.TemporaryDirectory() as td:
            comp = Path(td) / "c.csv"
            pub = Path(ROOT / "datos" / "composicion" / "congreso_huesca.csv")
            filas = pub.read_text(encoding="utf-8").splitlines()[1:]
            # mismas particiones con etiquetas intercambiadas
            comp.write_text("CUSEC_KEY,district_id\n" + "\n".join(
                f"{s},{1 - int(d)}" for s, d, _ in (x.split(",") for x in filas)) + "\n", encoding="utf-8")
            r = b._comparar_publicado("congreso_huesca", comp)
            self.assertTrue(r["igual"])

    def test_declaracion_temporal_completa_anos_desde_contrato(self):
        nac = {n: {"sha256": "0" * 64} for n in ("65034_totales.csv.zip", "seccionado_2023.zip",
                                                  "seccionado_2024.zip", "seccionado_2025.zip")}
        for modo in ("ogc", "shapefile"):
            p = b._declaracion_temporal("comunidad_valenciana", nac, modo)
            try:
                d = yaml.safe_load(p.read_text(encoding="utf-8"))
            finally:
                p.unlink()
            self.assertEqual((d["territory"]["population_year"], d["territory"]["section_year"]), (2023, 2023))
            self.assertEqual(d["source_bindings"]["secciones_censales"]["materialized_path"], "inputs/seccionado_2023.zip")
            self.assertEqual("snapshot" in d["source_bindings"]["secciones_censales"], modo == "shapefile")

    def test_estados_r2_prefieren_el_run_mas_reciente_y_m03(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "archivo_r2.json"
            arts = {str(i): {"territorio": "x", "artefacto": a, "run_id": r, "url": "r2://b/k", "sha256": "0"}
                    for i, (a, r) in enumerate([("ddd-state-1-M03", "1"), ("ddd-state-2-M03U", "2"),
                                                ("ddd-state-2-M03", "2"), ("ddd-state-2-M04", "2")])}
            f.write_text(json.dumps({"artefactos": arts}), encoding="utf-8")
            viejo, b.ARCHIVO_R2 = b.ARCHIVO_R2, f
            try:
                self.assertEqual([a["artefacto"] for a in b.estados_r2("x")],
                                 ["ddd-state-2-M03", "ddd-state-2-M03U", "ddd-state-1-M03"])
            finally:
                b.ARCHIVO_R2 = viejo

    def test_entrada_minima_es_m01_y_grafo_m03(self):
        self.assertEqual(b.ENTRADA_MINIMA, ("_m01_secciones_poblacion.geojson.zip", "_m03_grafo.json"))


if __name__ == "__main__":
    unittest.main()


class BateriaMotor2EnActions(unittest.TestCase):
    """T-208 (D-72): la batería del motor 2 en Actions."""

    @classmethod
    def setUpClass(cls):
        cls.wf = yaml.safe_load((ROOT / ".github/workflows/bateria-motor.yml").read_text(encoding="utf-8"))

    def test_entradas_y_defectos(self):
        ent = self.wf[True]["workflow_dispatch"]["inputs"]
        self.assertEqual(ent["motor"]["default"], "m05")
        self.assertEqual(ent["funcion"]["default"], "D8")
        self.assertEqual(ent["cadenas"]["default"], "10")
        self.assertEqual(self.wf["name"], "Auxiliar — Batería del Motor")  # sin renombrar (corte 5.0.0)

    def test_modo_m05_intacto_y_motor2_en_matriz(self):
        j = self.wf["jobs"]
        self.assertEqual(j["bateria"]["timeout-minutes"], 300)
        self.assertEqual(j["bateria"]["if"], "${{ inputs.motor != 'motor2' }}")
        self.assertEqual(j["competicion"]["timeout-minutes"], 360)
        self.assertFalse(j["competicion"]["strategy"]["fail-fast"])
        self.assertEqual(j["competicion"]["env"]["PYTHONHASHSEED"], "0")
        self.assertEqual(j["aceptacion"]["needs"], ["plan", "competicion"])
        txt = (ROOT / ".github/workflows/bateria-motor.yml").read_text(encoding="utf-8")
        self.assertIn("--desde-r2", txt)
        for t in ("congreso_soria", "congreso_alava", "melilla"):
            self.assertIn(f"matrix.t == '{t}'", txt)
        self.assertIn('cp bateria/competicion/RESUMEN.json "bateria/competicion/$T/RESUMEN.json"', txt)

    def test_lista_valida_territorios(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(b.main(["lista"]), 0)
        self.assertEqual(len(json.loads(buf.getvalue())["include"]), 71)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(b.main(["lista", "congreso_soria", "melilla"]), 0)
        self.assertEqual(json.loads(buf.getvalue()), {"include": [{"t": "congreso_soria"}, {"t": "melilla"}]})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(b.main(["lista", "atlantida"]), 2)

    def test_criterio_de_aceptacion(self):
        ok = lambda t, f="empata": {"territorio": t, "estado": "VALIDO", "frente_al_canonico": f}  # noqa: E731
        esp = ["congreso_soria", "madrid"]
        hu = {"congreso_soria": {"igual": True, "huella_1": "x"}}
        self.assertTrue(b.criterio_aceptacion([ok("congreso_soria"), ok("madrid", "mejora")], hu, esp)["aceptacion"])
        self.assertEqual(b.criterio_aceptacion([ok("congreso_soria")], hu, esp)["faltan"], ["madrid"])
        self.assertEqual(b.criterio_aceptacion([ok("congreso_soria"), ok("madrid", "empeora")], hu, esp)["empeoran"], ["madrid"])
        malo = [ok("congreso_soria"), {**ok("madrid"), "estado": "INVALIDO"}]
        self.assertEqual(b.criterio_aceptacion(malo, hu, esp)["no_validos"], ["madrid"])
        sin = b.criterio_aceptacion([ok("congreso_soria"), ok("madrid")], {"congreso_soria": {"igual": False}}, esp)
        self.assertEqual(sin["huella_real_mal"], ["congreso_soria"])
        self.assertFalse(sin["aceptacion"])

    def test_aceptacion_une_la_matriz(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            for t, h in (("congreso_soria", "ab"), ("madrid", "cd")):
                fila = {"territorio": t, "estado": "VALIDO", "ganador": "g", "valido": True, "frente_al_canonico": "empata",
                        "canonico": "VALIDO", "candidatos_validos": 3, "candidatos": 3, "desvio_max": 0.01,
                        "desvio_max_canonico": 0.01, "fuera_tolerancia": 0, "huella_resultado": h, "tiempo_s": 1.0}
                # disposición real: competir.main escribe el agregado en competicion/RESUMEN.json y el workflow lo copia
                # junto a COMPETICION.json del territorio (artefacto por territorio)
                from ddd_motor2.competir import escribir_resumen
                escribir_resumen([fila], out / "x" / "competicion")
                (out / "x" / "competicion" / t).mkdir(parents=True)
                shutil.copy(out / "x" / "competicion" / "RESUMEN.json", out / "x" / "competicion" / t / "RESUMEN.json")
            hr = out / "x" / "competicion" / "congreso_soria" / "HUELLA_REAL.json"
            hr.write_text(json.dumps({"territorio": "congreso_soria", "huella_1": "ab", "huella_2": "ab", "igual": True}))
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(b.main(["aceptacion", "--out", str(out), "congreso_soria", "madrid"]), 0)
                self.assertEqual(b.main(["aceptacion", "--out", str(out), "congreso_soria", "madrid", "melilla"]), 1)
            self.assertFalse(json.loads((out / "ACEPTACION.json").read_text())["aceptacion"])
