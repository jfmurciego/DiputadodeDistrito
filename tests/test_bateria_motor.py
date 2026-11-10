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

    def test_credenciales_r2_solo_en_el_paso_de_entradas(self):
        job = self.wf["jobs"]["competicion"]
        self.assertFalse([k for k in job["env"] if k.startswith(("AWS_", "R2_"))])
        con = [s["name"] for s in job["steps"] if any(k.startswith("AWS_") for k in s.get("env", {}))]
        self.assertEqual(con, ["Entradas (R2 o fuente INE)"])

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
        cs = lambda *ts: {t: {"candidatos": 5, "exhaustivo": True, "cadenas": 3, "evaluables": 3, "fallos_generador": 0,  # noqa: E731
                              "no_evaluados": [], "invalidas_sin_motivo": []} for t in ts}
        parcial = b.criterio_aceptacion([ok("congreso_soria"), ok("madrid", "mejora")], hu, esp, cs(*esp), 3)
        self.assertTrue(parcial["parcial"])
        self.assertFalse(parcial["aceptacion"])  # sin Álava ni Melilla no hay verde por omisión
        todas = ["congreso_soria", "congreso_alava", "melilla", "madrid"]
        h3 = {t: {"igual": True, "huella_1": t} for t in todas[:3]}
        vg = {t: {"estado": "OK"} for t in todas}
        c = b.criterio_aceptacion([ok(t) for t in todas], h3, todas, cs(*todas), 3, vg)
        self.assertTrue(c["aceptacion"])
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, cs(*todas), 3)["aceptacion"])  # sin vigente, NO
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas)["aceptacion"])  # sin datos de cadenas, NO
        c5 = cs(*todas)
        c5["madrid"]["candidatos"] = 4  # 1 + 3 + exhaustivo = 5 esperados
        self.assertEqual(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, c5, 3)["candidatos_incompletos"], ["madrid"])
        c5["madrid"].update(candidatos=5, no_evaluados=["ponderado-s1"])
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, c5, 3)["aceptacion"])
        c5["madrid"].update(no_evaluados=[], invalidas_sin_motivo=["ponderado-s2"])
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, c5, 3)["aceptacion"])
        self.assertFalse(c["parcial"])
        self.assertEqual(b.criterio_aceptacion([ok("congreso_soria")], hu, esp)["faltan"], ["madrid"])
        self.assertEqual(b.criterio_aceptacion([ok("congreso_soria"), ok("madrid", "empeora")], hu, esp)["empeoran"], ["madrid"])
        malo = [ok("congreso_soria"), {**ok("madrid"), "estado": "INVALIDO"}]
        self.assertEqual(b.criterio_aceptacion(malo, hu, esp)["no_validos"], ["madrid"])
        sin = b.criterio_aceptacion([ok("congreso_soria"), ok("madrid")], {"congreso_soria": {"igual": False}}, esp)
        self.assertEqual(sin["huella_real_mal"], ["congreso_soria"])
        self.assertFalse(sin["aceptacion"])

    def test_paso_fallido_sin_resumen_deja_el_territorio_en_faltan(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / "competicion" / "madrid").mkdir(parents=True)  # el job de congreso_soria no dejó RESUMEN.json
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(b.main(["aceptacion", "--out", d, "congreso_soria"]), 1)
            res = json.loads((out / "ACEPTACION.json").read_text())
            self.assertEqual(res["faltan"], ["congreso_soria"])
            self.assertFalse(res["aceptacion"])

    def test_aceptacion_parcial_no_es_aceptacion(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(b.main(["aceptacion", "--out", d, "--cadenas", "2", "madrid"]), 0)
            self.assertIn("PARCIAL", buf.getvalue())
            self.assertFalse(json.loads((out / "ACEPTACION.json").read_text())["aceptacion"])

    def test_aceptacion_une_la_matriz(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            for t in ("congreso_soria", "madrid"):
                self._competir_real(out, t, cadena_ok=True)
            hr = out / "competicion" / "congreso_soria" / "HUELLA_REAL.json"
            hr.write_text(json.dumps({"territorio": "congreso_soria", "huella_1": "ab", "huella_2": "ab", "igual": True}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(b.main(["aceptacion", "--out", str(out), "--cadenas", "2", "congreso_soria", "madrid"]), 0)
                self.assertEqual(b.main(["aceptacion", "--out", str(out), "--cadenas", "2", "congreso_soria", "madrid", "melilla"]), 1)
            self.assertFalse(json.loads((out / "ACEPTACION.json").read_text())["aceptacion"])

    def _competir_real(self, out: Path, t: str, cadena_ok: bool, vigente="bueno", canonico="bueno", pob=None):
        """Salida real de competir_territorio + escribir_resumen (generadores sintéticos); la cadena falla o no.
        T-212: deja también INDICADORES.json con el vigente indicado (`bueno` | `malo` | None = sin composición vigente |
        "no_escribir" = sin INDICADORES.json), tal como lo hace el paso `indicadores` del job."""
        from ddd_motor2.competicion import EntradaTerritorio
        from ddd_motor2.competir import competir_territorio, escribir_resumen
        from ddd_motor2.semilla import semillas
        from tests.test_motor2_competicion import POB, Fijo
        from tests.test_motor2_semilla import cfg as cfg_con_ancla
        secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
        grafo = out / "grafo.json"
        grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
            {"u": secc[a], "v": secc[c]} for a, c in (("A", "B"), ("B", "C"), ("C", "D"))]}))
        e = EntradaTerritorio(t, cfg_con_ancla(), grafo)
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        malo = {"A": "1", "B": "2", "C": "2", "D": "2"}  # 100 / 300 con objetivo 200: dos distritos fuera de tolerancia
        planes = {x: (bueno if cadena_ok else None) for x in semillas(e.cfg, t, 2)}
        can = {"bueno": bueno, "malo": malo}[canonico]
        pob = pob or POB
        fila = competir_territorio(t, out, 2, generadores=(Fijo("canonico", {None: can}, pob), Fijo("ponderado", planes, pob)), entrada=e)
        escribir_resumen([fila], out / "competicion")
        shutil.copy(out / "competicion" / "RESUMEN.json", out / "competicion" / t / "RESUMEN.json")
        if vigente != "no_escribir":
            pub = None
            if vigente:
                pub = out / "vigente.csv"
                plan_v = vigente if isinstance(vigente, dict) else {"bueno": bueno, "malo": malo}[vigente]
                pub.write_text("seccion,distrito,poblacion\n" + "".join(
                    f"{secc[u]},{plan_v[u]},{pob[u]}\n" for u in sorted(secc)), encoding="utf-8")
            r = b.indicadores_territorio(t, out, cfg=e.cfg, grafo=grafo, vigente=(pub, "123" if pub else None))
            b.escribir_indicadores(r, out)
        return fila

    def _aceptar(self, out: Path, t: str, n: int = 2) -> dict:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc = b.main(["aceptacion", "--out", str(out), "--cadenas", str(n), t])
        return {"rc": rc, **json.loads((out / "ACEPTACION.json").read_text())}

    def test_t212_ganador_igual_al_vigente_no_es_peor_y_el_resumen_trae_los_indicadores(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True)
            i = json.loads((out / "competicion" / "madrid" / "INDICADORES.json").read_text())
            self.assertEqual((i["estado"], i["run_vigente"]), ("OK", "123"))
            for k in ("vigente", "canonico", "ganador_indicadores"):  # literales: 2 distritos de 200, uno por mitad
                self.assertEqual((i[k]["distritos"], i[k]["fuera_tolerancia"], i[k]["desvio_max"]), (2, 0, 0.0), k)
                self.assertEqual({x: i[k][x] for x in ("partidos_judiciales_partidos", "comarcas_partidas", "frontera_cortada_km")},
                                 {x: i["vigente"][x] for x in ("partidos_judiciales_partidos", "comarcas_partidas", "frontera_cortada_km")}, k)
                self.assertTrue(i[k]["valido_reglas_actuales"])
            md = (out / "competicion" / "madrid" / "INDICADORES.md").read_text()
            for texto in ("(recuento bruto) frente al vigente: **OK**", "Comprobación 1", "| Vigente |", "| Canónico (canonico) |", "| Ganador (", "Part. judiciales", "PP medio"):
                self.assertIn(texto, md)
            r = self._aceptar(out, "madrid")
            self.assertEqual((r["vigente_peor"], r["vigente_sin"]), ([], []))
            self.assertIn("Frente al vigente", (out / "ACEPTACION.md").read_text())

    def test_t212_ganador_con_mas_fuera_de_tolerancia_que_el_vigente_es_no(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            pob = {"A": 100, "B": 130, "C": 100, "D": 70}  # total 400, objetivo 200, tolerancia 10 %
            # el vigente (B+D / A+C, discontinuo: no valdría hoy) tiene 0 distritos fuera; el mejor contiguo, A+B / C+D (230 / 170), 2
            self._competir_real(out, "madrid", cadena_ok=True, pob=pob, vigente={"A": "1", "B": "2", "C": "1", "D": "2"})
            i = json.loads((out / "competicion" / "madrid" / "INDICADORES.json").read_text())
            self.assertEqual((i["estado"], i["vigente"]["fuera_tolerancia"], i["vigente"]["valido_reglas_actuales"]), ("PEOR", 0, False))
            self.assertEqual(i["ganador_indicadores"]["fuera_tolerancia"], 2)
            self.assertIn("más distritos fuera de tolerancia (2 > 0)", i["motivo"])
            self.assertIn("Comprobación 2", (out / "competicion" / "madrid" / "INDICADORES.md").read_text())
            r = self._aceptar(out, "madrid")
            self.assertEqual((r["rc"], r["vigente_peor"], r["aceptacion"]), (1, ["madrid"], False))
            md = (out / "ACEPTACION.md").read_text()
            self.assertIn("Comprobación 2 · más distritos fuera de tolerancia (recuento bruto) que el mapa vigente publicado: ['madrid']", md)
            self.assertIn("Comprobación 1 · clave de elección peor que la del canónico: ninguno", md)  # son comprobaciones separadas

    def test_t212_mayor_desvio_maximo_solo_avisa(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            pob = {"A": 100, "B": 120, "C": 100, "D": 80}  # vigente discontinuo con desvío 0; mejor contiguo 10 % (dentro de tolerancia)
            self._competir_real(out, "madrid", cadena_ok=True, pob=pob, vigente={"A": "1", "B": "2", "C": "1", "D": "2"})
            i = json.loads((out / "competicion" / "madrid" / "INDICADORES.json").read_text())
            self.assertEqual((i["estado"], i["vigente"]["desvio_max"], round(i["ganador_indicadores"]["desvio_max"], 6)), ("OK", 0.0, 0.1))
            self.assertEqual(i["aviso_desvio"], ["mayor desvío máximo (10.00 % > 0.00 %)"])
            self.assertEqual(i["clave_frente_canonico"], "empata")
            r = self._aceptar(out, "madrid")
            self.assertEqual((r["vigente_peor"], r["vigente_aviso_desvio"]), ([], ["madrid"]))

    def test_t212_forma_con_la_m01_de_las_entradas(self):
        import zipfile
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            dx = 0.01 / 0.7431  # 1 grado de longitud a 42° mide 0,7431 de uno de latitud: secciones cuadradas
            feats = [{"type": "Feature", "properties": {"CUSEC_KEY": f"220010100{i}"}, "geometry": {
                "type": "Polygon", "coordinates": [[[dx * i, 42.0], [dx * (i + 1), 42.0], [dx * (i + 1), 42.01],
                                                     [dx * i, 42.01], [dx * i, 42.0]]]}} for i in range(4)]
            with zipfile.ZipFile(out / "x_m01_secciones_poblacion.geojson.zip", "w") as z:
                z.writestr("m01.geojson", json.dumps({"type": "FeatureCollection", "features": feats}))
            self._competir_real(out, "madrid", cadena_ok=True)  # distritos A+B y C+D: dos rectángulos 2:1
            i = json.loads((out / "competicion" / "madrid" / "INDICADORES.json").read_text())
            for k in ("vigente", "canonico", "ganador_indicadores"):
                self.assertNotIn("pp_error", i[k], i[k])
                self.assertAlmostEqual(i[k]["pp_medio"], 4 * 3.14159265 * 2 / 36, delta=0.03)  # rectángulo 2:1 ≈ 0,70
            self.assertIn("0.7", (out / "competicion" / "madrid" / "INDICADORES.md").read_text())

    def test_t212_peor_es_el_recuento_bruto_de_fuera_de_tolerancia(self):
        g = {"fuera_tolerancia": 1, "desvio_max": 0.3}
        self.assertEqual(b.peor_que(g, {"fuera_tolerancia": 1, "desvio_max": 0.3}), [])
        self.assertEqual(b.peor_que(g, {"fuera_tolerancia": 2, "desvio_max": 0.1}), [])
        self.assertEqual(b.peor_que(g, {"fuera_tolerancia": 1, "desvio_max": 0.2}), [])  # el desvío no bloquea
        self.assertEqual(len(b.peor_que(g, {"fuera_tolerancia": 0, "desvio_max": 0.9})), 1)
        self.assertIn("mayor desvío máximo", b.aviso_desvio(g, {"fuera_tolerancia": 1, "desvio_max": 0.2})[0])
        self.assertEqual(b.aviso_desvio(g, {"fuera_tolerancia": 1, "desvio_max": 0.3}), [])

    def test_t212_sin_vigente_consta_y_no_es_verde(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True, vigente=None)
            self.assertEqual(json.loads((out / "competicion" / "madrid" / "INDICADORES.json").read_text())["estado"], "SIN_VIGENTE")
            r = self._aceptar(out, "madrid")
            self.assertEqual((r["rc"], r["vigente_sin"], r["aceptacion"]), (1, ["madrid"], False))
            self.assertIn("sin composición vigente", r["vigente_motivos"]["madrid"])

    def test_t212_sin_indicadores_o_no_evaluable_no_es_verde_por_omision(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True, vigente="no_escribir")
            r = self._aceptar(out, "madrid")
            self.assertEqual((r["rc"], r["vigente_sin"]), (1, ["madrid"]))
            self.assertEqual(r["vigente_motivos"]["madrid"], "sin INDICADORES.json")
        ok = lambda t: {"territorio": t, "estado": "VALIDO", "frente_al_canonico": "empata"}  # noqa: E731
        c = b.criterio_aceptacion([ok("x")], {}, ["x"], vigentes={"x": {"territorio": "x", "estado": "NO_EVALUABLE", "motivo": "KeyError: z"}})
        self.assertEqual((c["vigente_sin"], c["vigente_motivos"]), (["x"], {"x": "KeyError: z"}))
        u = b.criterio_aceptacion([ok("c")], {}, ["c"], vigentes={"c": {"territorio": "c", "estado": "UN_DISTRITO"}})
        self.assertEqual((u["vigente_sin"], u["vigente_un_distrito"]), ([], ["c"]))  # el único plan posible: consta y no bloquea

    def test_t212_vigente_con_otras_secciones_no_es_evaluable(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True)
            pub = out / "otro.csv"
            pub.write_text("seccion,distrito,poblacion\n2200101000,0,100\n", encoding="utf-8")
            from tests.test_motor2_semilla import cfg as cfg_con_ancla
            r = b.indicadores_territorio("madrid", out, cfg=cfg_con_ancla(), grafo=out / "grafo.json", vigente=(pub, "1"))
            self.assertEqual(r["estado"], "NO_EVALUABLE")
            self.assertIn("secciones distintas", r["motivo"])

    def test_t181_generador_fallido_da_no_aunque_gane_el_canonico(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            fila = self._competir_real(out, "madrid", cadena_ok=False)
            self.assertEqual((fila["estado"], fila["ganador"]), ("VALIDO", "canonico"))  # el caso de T-208: todo «válido»
            r = self._aceptar(out, "madrid")
            self.assertEqual(r["rc"], 1)
            self.assertEqual((r["sin_cadenas"], r["fallo_generador"]), (["madrid"], ["madrid"]))
            self.assertFalse(r["aceptacion"])

    def test_t181_cadenas_evaluables_no_bloquean(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True)
            r = self._aceptar(out, "madrid")
            self.assertEqual((r["rc"], r["sin_cadenas"], r["fallo_generador"]), (0, [], []))  # PARCIAL: sin huellas, pero sin fallos

    def test_t181_numero_de_candidatos_distinto_de_1_mas_n_es_no(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True)  # 2 cadenas + canónico + exhaustivo
            self.assertEqual(self._aceptar(out, "madrid", 2)["candidatos_incompletos"], [])
            self.assertEqual(self._aceptar(out, "madrid", 10)["candidatos_incompletos"], ["madrid"])

    def test_t181_sin_competicion_json_es_no(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "madrid", cadena_ok=True)
            (out / "competicion" / "madrid" / "COMPETICION.json").unlink()
            self.assertEqual(self._aceptar(out, "madrid")["sin_cadenas"], ["madrid"])

    def test_t212_el_job_escribe_los_indicadores_en_el_resumen_del_paso(self):
        pasos = self.wf["jobs"]["competicion"]["steps"]
        nombres = [p.get("name", "") for p in pasos]
        i_comp = nombres.index("Competición del motor 2")
        i_ind = next(i for i, n in enumerate(nombres) if n.startswith("Indicadores frente al vigente"))
        self.assertGreater(i_ind, i_comp)
        run = pasos[i_ind]["run"]
        self.assertIn("bateria_motor.py indicadores", run)
        self.assertIn("GITHUB_STEP_SUMMARY", run)  # sin depender de bajar artefactos (403 desde la nube)
        self.assertEqual(pasos[i_ind]["if"], "${{ !cancelled() }}")

    def test_t181_el_job_de_competicion_instala_y_comprueba_lo_que_importa_ponderado(self):
        pasos = self.wf["jobs"]["competicion"]["steps"]
        ix = lambda pre: next(i for i, p in enumerate(pasos) if p.get("name", "").startswith(pre))  # noqa: E731
        i_dep, i_ent, i_comp = ix("Dependencias de las cadenas"), ix("Entradas"), ix("Competición del motor 2")
        self.assertLess(i_ent, i_dep)  # las entradas usan el lock base; las cadenas, el del laboratorio
        self.assertLess(i_dep, i_comp)  # falla en ~1 min, antes de gastar minutos de competición
        txt = pasos[i_dep]["run"]
        self.assertIn("requirements-ensemble.lock", txt)
        for imp in ("import networkx", "from gerrychain import Graph, MarkovChain, Partition, updaters",
                    "from gerrychain.proposals import recom", "from gerrychain.tree import bipartition_tree",
                    "_ordered_edge_ids", "naturalidad_competicion import cadena", 'm.version(nombre) == lab[nombre]',
                    "--no-deps", "pip freeze --all", "comm -23", 'pins("requirements.lock")'):
            self.assertIn(imp, txt)
        # lo que Ponderado importa de gerrychain (fuente) está en la comprobación
        src = (ROOT / "ddd_motor2/naturalidad_competicion.py").read_text(encoding="utf-8")
        for linea in ("from gerrychain.tree.spanning_tree import _ordered_edge_ids", "from gerrychain import Graph, MarkovChain, Partition, updaters",
                      "from gerrychain.proposals import recom", "from gerrychain.tree import bipartition_tree"):
            self.assertIn(linea, src)
        lock = (ROOT / "requirements-ensemble.lock").read_text().lower()
        self.assertNotIn("pip install --requirement requirements-ensemble.lock", txt)  # T-181b: subía pandas 3 y rompía M04-M06
        self.assertIn("gerrychain==", lock)
        self.assertIn("networkx==", lock)
        self.assertIn("--cadenas", self.wf["jobs"]["aceptacion"]["steps"][-2]["run"])


if __name__ == "__main__":
    unittest.main()
