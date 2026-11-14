"""T-132: batería del motor (herramientas/bateria_motor.py)."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import bateria_motor as b
from ddd_core.territorio_ids import es_nacional, ids_nuevos, id_legacy  # noqa: E402  (T-220)

ROOT = Path(__file__).resolve().parents[1]


class BateriaMotor(unittest.TestCase):
    def test_territorios_son_52_congreso_y_19_comunidades(self):
        ts = b.territorios()
        self.assertEqual(len([t for t in ts if es_nacional(t)]), 52)
        self.assertEqual(len([t for t in ts if not es_nacional(t)]), 19)

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
        # T-247: raíz sintética; antes leía datos/composicion/congreso_huesca.csv vivo, pero la función compara con
        # la composición del run canonical_m06 del visor (runs/<t>_<run>.csv), que la campaña cambia sin tocar código.
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "orchestracion").mkdir()
            (root / "orchestracion/publicaciones_visor.json").write_text(json.dumps({"products": [
                {"kind": "canonical_m06", "territory_id": "congreso_demo", "run_id": "7"},
                {"kind": "canonical_m06", "territory_id": "congreso_demo", "run_id": "9"}]}), encoding="utf-8")
            (root / "datos/composicion/runs").mkdir(parents=True)
            cab = "seccion,distrito,poblacion\n"
            (root / "datos/composicion/runs/congreso_demo_9.csv").write_text(
                cab + "s1,0,10\ns2,0,10\ns3,1,10\ns4,1,10\n", encoding="utf-8")
            # La canónica (de otro run) tiene otra partición: no debe usarse si existe la del run publicado.
            (root / "datos/composicion/congreso_demo.csv").write_text(
                cab + "s1,0,10\ns3,0,10\ns2,1,10\ns4,1,10\n", encoding="utf-8")
            comp = root / "c.csv"
            with mock.patch.object(b, "ROOT", root):
                comp.write_text("CUSEC_KEY,district_id\ns1,1\ns2,1\ns3,0\ns4,0\n", encoding="utf-8")
                r = b._comparar_publicado("congreso_demo", comp)
                self.assertTrue(r["igual"], r)  # mismas particiones con etiquetas intercambiadas
                self.assertEqual(r["run_publicado"], "9")
                comp.write_text("CUSEC_KEY,district_id\ns1,0\ns3,0\ns2,1\ns4,1\n", encoding="utf-8")
                r = b._comparar_publicado("congreso_demo", comp)
                self.assertFalse(r["igual"], r)  # otra partición (la de la canónica) no es igual a la publicada
                self.assertEqual(r["distritos_iguales"], 0)

    def test_declaracion_temporal_completa_anos_desde_contrato(self):
        nac = {n: {"sha256": "0" * 64} for n in ("65034_totales.csv.zip", "seccionado_2023.zip",
                                                  "seccionado_2024.zip", "seccionado_2025.zip")}
        for modo in ("ogc", "shapefile"):
            p = b._declaracion_temporal("aut10", nac, modo)
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
        self.assertEqual(self.wf["name"], "VER Verificación del motor")  # T-215, corte 5.0.0 paso 4

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
        for t in ("nac42", "nac01", "aut19"):
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
            self.assertEqual(b.main(["lista", "nac42", "aut19"]), 0)
        self.assertEqual(json.loads(buf.getvalue()), {"include": [{"t": "nac42"}, {"t": "aut19"}]})
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(b.main(["lista", "atlantida"]), 2)

    def test_criterio_de_aceptacion(self):
        ok = lambda t, f="empata": {"territorio": t, "estado": "VALIDO", "frente_al_canonico": f}  # noqa: E731
        esp = ["nac42", "aut13"]
        hu = {"nac42": {"igual": True, "huella_1": "x"}}
        cs = lambda *ts: {t: {"candidatos": 5, "exhaustivo": True, "cadenas": 3, "evaluables": 3, "fallos_generador": 0,  # noqa: E731
                              "no_evaluados": [], "invalidas_sin_motivo": []} for t in ts}
        parcial = b.criterio_aceptacion([ok("nac42"), ok("aut13", "mejora")], hu, esp, cs(*esp), 3)
        self.assertTrue(parcial["parcial"])
        self.assertFalse(parcial["aceptacion"])  # sin Álava ni Melilla no hay verde por omisión
        todas = ["nac42", "nac01", "aut19", "aut13"]
        h3 = {t: {"igual": True, "huella_1": t} for t in todas[:3]}
        vg = {t: {"estado": "OK"} for t in todas}
        c = b.criterio_aceptacion([ok(t) for t in todas], h3, todas, cs(*todas), 3, vg)
        self.assertTrue(c["aceptacion"])
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, cs(*todas), 3)["aceptacion"])  # sin vigente, NO
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas)["aceptacion"])  # sin datos de cadenas, NO
        c5 = cs(*todas)
        c5["aut13"]["candidatos"] = 4  # 1 + 3 + exhaustivo = 5 esperados
        self.assertEqual(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, c5, 3)["candidatos_incompletos"], ["aut13"])
        c5["aut13"].update(candidatos=5, no_evaluados=["ponderado-s1"])
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, c5, 3)["aceptacion"])
        c5["aut13"].update(no_evaluados=[], invalidas_sin_motivo=["ponderado-s2"])
        self.assertFalse(b.criterio_aceptacion([ok(t) for t in todas], h3, todas, c5, 3)["aceptacion"])
        self.assertFalse(c["parcial"])
        self.assertEqual(b.criterio_aceptacion([ok("nac42")], hu, esp)["faltan"], ["aut13"])
        self.assertEqual(b.criterio_aceptacion([ok("nac42"), ok("aut13", "empeora")], hu, esp)["empeoran"], ["aut13"])
        malo = [ok("nac42"), {**ok("aut13"), "estado": "INVALIDO"}]
        self.assertEqual(b.criterio_aceptacion(malo, hu, esp)["no_validos"], ["aut13"])
        sin = b.criterio_aceptacion([ok("nac42"), ok("aut13")], {"nac42": {"igual": False}}, esp)
        self.assertEqual(sin["huella_real_mal"], ["nac42"])
        self.assertFalse(sin["aceptacion"])

    def test_paso_fallido_sin_resumen_deja_el_territorio_en_faltan(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            (out / "competicion" / "aut13").mkdir(parents=True)  # el job de congreso_soria no dejó RESUMEN.json
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(b.main(["aceptacion", "--out", d, "nac42"]), 1)
            res = json.loads((out / "ACEPTACION.json").read_text())
            self.assertEqual(res["faltan"], ["nac42"])
            self.assertFalse(res["aceptacion"])

    def test_aceptacion_parcial_no_es_aceptacion(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(b.main(["aceptacion", "--out", d, "--cadenas", "2", "aut13"]), 0)
            self.assertIn("PARCIAL", buf.getvalue())
            self.assertFalse(json.loads((out / "ACEPTACION.json").read_text())["aceptacion"])

    def test_aceptacion_une_la_matriz(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            for t in ("nac42", "aut13"):
                self._competir_real(out, t, cadena_ok=True)
            hr = out / "competicion" / "nac42" / "HUELLA_REAL.json"
            hr.write_text(json.dumps({"territorio": "nac42", "huella_1": "ab", "huella_2": "ab", "igual": True}))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(b.main(["aceptacion", "--out", str(out), "--cadenas", "2", "nac42", "aut13"]), 0)
                self.assertEqual(b.main(["aceptacion", "--out", str(out), "--cadenas", "2", "nac42", "aut13", "aut19"]), 1)
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

    # ------------------------------------------------------------------ T-222: el vigente que compite cuenta
    @staticmethod
    def _competicion_json(out: Path, t: str, n: int, vigente: dict | None, con_candidato: bool, exhaustivo=False):
        """COMPETICION.json con la forma de competicion 1.4.0 (T-217): canónico, vigente (orden 1) si compite, n cadenas."""
        cands = [{"id": "canonico", "generador": "canonico", "estado": "VALIDO"}]
        if con_candidato:
            cands.append({"id": "vigente", "generador": "vigente", "estado": "VALIDO"})
        cands += [{"id": f"ponderado-s{i}", "generador": "ponderado", "estado": "VALIDO"} for i in range(n)]
        if exhaustivo:
            cands.append({"id": "exhaustivo", "generador": "exhaustivo", "estado": "VALIDO"})
        d = {"territorio": t, "canonico": "canonico", "ganador": "ponderado-s0", "candidatos": cands,
             **({"vigente": vigente} if vigente is not None else {})}
        (out / "competicion" / t).mkdir(parents=True, exist_ok=True)
        (out / "competicion" / t / "COMPETICION.json").write_text(json.dumps(d), encoding="utf-8")
        return b.cadenas_de(out / "competicion" / t)

    def test_t222_r4_fase1_madrid_y_navarra_12_de_12_con_vigente_es_completo(self):
        # run 42913861593: «candidatos_validos: 12, candidatos: 12», vigente VALIDO y compite, --cadenas 10, sin exhaustivo
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            cs = {t: self._competicion_json(out, t, 10, {"estado": "VALIDO", "detalle": "", "compite": True}, True)
                  for t in ("aut13", "aut15")}
        for c in cs.values():
            self.assertEqual((c["candidatos"], c["cadenas"], c["evaluables"]), (12, 10, 10))
            self.assertTrue(c["vigente_compite"])
        ok = lambda t: {"territorio": t, "estado": "VALIDO", "frente_al_canonico": "mejora"}  # noqa: E731
        esp = list(cs)
        r = b.criterio_aceptacion([ok(t) for t in esp], {}, esp, cs, 10, {t: {"estado": "OK"} for t in esp})
        self.assertEqual(r["candidatos_incompletos"], [])
        self.assertEqual(r["vigente_excluido"], {})
        self.assertTrue(r["parcial"])  # sin las tres huellas reales sigue sin ser aceptación
        self.assertFalse(r["aceptacion"])
        h3 = {t: {"igual": True, "huella_1": t} for t in ("nac42", "nac01", "aut19")}
        cs3 = {**cs, **{t: {**cs["aut13"], "vigente_compite": False} | {"candidatos": 11} for t in h3}}
        todos = esp + list(h3)
        r = b.criterio_aceptacion([ok(t) for t in todos], h3, todos, cs3, 10, {t: {"estado": "OK"} for t in todos})
        self.assertTrue(r["aceptacion"])
        cs3["aut13"] = {**cs["aut13"], "candidatos": 11}  # falta una cadena: 11 ≠ 12
        self.assertEqual(b.criterio_aceptacion([ok(t) for t in todos], h3, todos, cs3, 10, {t: {"estado": "OK"} for t in todos})
                         ["candidatos_incompletos"], ["aut13"])

    def test_t222_vigente_excluido_consta_con_motivo_y_no_cuenta(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            ex = self._competicion_json(out, "aut13", 3, {"estado": "INVALIDO", "detalle": "núcleo partido en 28079",
                                                           "compite": False}, False, exhaustivo=True)
            sin = self._competicion_json(out, "aut19", 3, None, False)  # pre-T-217 o reanudado sin vigente
            con = self._competicion_json(out, "nac42", 3, {"estado": "VALIDO", "compite": True}, True, exhaustivo=True)
            # incoherentes: dice que compite y no está entre los candidatos, o al revés
            inc1 = self._competicion_json(out, "nac01", 3, {"estado": "VALIDO", "compite": True}, False)
            inc2 = self._competicion_json(out, "aut18", 3, {"estado": "INVALIDO", "compite": False}, True)
        self.assertEqual((ex["candidatos"], ex["vigente_compite"], ex["vigente_excluido"]), (5, False, "INVALIDO; núcleo partido en 28079"))
        self.assertEqual(sin["candidatos"], 4)
        self.assertIn("sin bloque", sin["vigente_excluido"])
        self.assertEqual((con["candidatos"], con["cadenas"]), (6, 3))
        self.assertTrue(inc1["vigente_incoherente"] and inc2["vigente_incoherente"])
        ok = lambda t: {"territorio": t, "estado": "VALIDO", "frente_al_canonico": "empata"}  # noqa: E731
        cs = {"aut13": ex, "aut19": sin, "nac42": con, "nac01": inc1, "aut18": inc2}
        esp = list(cs)
        r = b.criterio_aceptacion([ok(t) for t in esp], {}, esp, cs, 3, {t: {"estado": "OK"} for t in esp})
        self.assertEqual(r["candidatos_incompletos"], ["aut18", "nac01"])
        self.assertEqual(r["vigente_excluido"]["aut13"], "INVALIDO; núcleo partido en 28079")
        self.assertEqual(sorted(r["vigente_excluido"]), ["aut13", "aut19"])
        self.assertFalse(r["aceptacion"])
        # un excluido que además «cuenta» (5 + 1 = 6 candidatos) no cuadra: sin verde por omisión
        self.assertEqual(b.criterio_aceptacion([ok("aut13")], {}, ["aut13"], {"aut13": {**ex, "candidatos": 6}}, 3)
                         ["candidatos_incompletos"], ["aut13"])

    def test_t222_solo_el_vigente_valido_no_es_cadena_evaluable(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            c = self._competicion_json(out, "aut13", 0, {"estado": "VALIDO", "compite": True}, True)
        self.assertEqual((c["cadenas"], c["evaluables"]), (0, 0))
        r = b.criterio_aceptacion([{"territorio": "aut13", "estado": "VALIDO"}], {}, ["aut13"], {"aut13": c}, 0)
        self.assertEqual(r["sin_cadenas"], ["aut13"])

    def test_t222_competicion_real_con_vigente_y_reanudacion_de_la_aceptacion(self):
        from ddd_motor2.competicion import EntradaTerritorio
        from ddd_motor2.competir import competir_territorio, escribir_resumen
        from ddd_motor2.semilla import semillas
        from tests.test_motor2_competicion import POB, Fijo
        from tests.test_motor2_semilla import cfg as cfg_con_ancla
        bueno = {"A": "1", "B": "1", "C": "2", "D": "2"}
        partido = {"A": "1", "B": "2", "C": "1", "D": "2"}  # distritos no conexos: no cumple el núcleo
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            secc = {u: f"220010100{i}" for i, u in enumerate(sorted(POB))}
            grafo = out / "grafo.json"
            grafo.write_text(json.dumps({"nodes": list(secc.values()), "edges": [
                {"u": secc[a], "v": secc[c]} for a, c in (("A", "B"), ("B", "C"), ("C", "D"))]}))
            filas = []
            for t, plan_v in (("aut13", bueno), ("aut15", partido)):
                e = EntradaTerritorio(t, cfg_con_ancla(), grafo)
                planes = {x: bueno for x in semillas(e.cfg, t, 2)}
                filas.append(competir_territorio(t, out, 2, generadores=(Fijo("canonico", {None: bueno}), Fijo("ponderado", planes)),
                                                 entrada=e, vigente=Fijo("vigente", {None: plan_v})))
            escribir_resumen(filas, out / "competicion")
            cm = b.cadenas_de(out / "competicion" / "aut13")
            cn = b.cadenas_de(out / "competicion" / "aut15")
            self.assertTrue(cm["vigente_compite"])
            self.assertEqual(cm["candidatos"] - (1 if cm["exhaustivo"] else 0), 1 + 2 + 1)
            self.assertFalse(cn["vigente_compite"])
            self.assertTrue(cn["vigente_excluido"])
            self.assertEqual(cn["candidatos"] - (1 if cn["exhaustivo"] else 0), 1 + 2)
            for t in ("aut13", "aut15"):
                (out / "competicion" / t / "INDICADORES.json").write_text(json.dumps({"territorio": t, "estado": "OK"}))
            import contextlib
            import io
            res = []
            for _ in range(2):  # reanudación: la aceptación sobre la misma carpeta da lo mismo
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    b.main(["aceptacion", "--out", d, "--cadenas", "2", "aut13", "aut15"])
                res.append(json.loads((out / "ACEPTACION.json").read_text()))
            self.assertEqual(res[0], res[1])
            self.assertEqual(res[0]["candidatos_incompletos"], [])
            self.assertEqual(list(res[0]["vigente_excluido"]), ["aut15"])
            self.assertIn("Vigente excluido", buf.getvalue())

    def _aceptar(self, out: Path, t: str, n: int = 2) -> dict:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            rc = b.main(["aceptacion", "--out", str(out), "--cadenas", str(n), t])
        return {"rc": rc, **json.loads((out / "ACEPTACION.json").read_text())}

    def test_t212_ganador_igual_al_vigente_no_es_peor_y_el_resumen_trae_los_indicadores(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            i = json.loads((out / "competicion" / "aut13" / "INDICADORES.json").read_text())
            self.assertEqual((i["estado"], i["run_vigente"]), ("OK", "123"))
            for k in ("vigente", "canonico", "ganador_indicadores"):  # literales: 2 distritos de 200, uno por mitad
                self.assertEqual((i[k]["distritos"], i[k]["fuera_tolerancia"], i[k]["desvio_max"]), (2, 0, 0.0), k)
                self.assertEqual({x: i[k][x] for x in ("partidos_judiciales_partidos", "comarcas_partidas", "frontera_cortada_km")},
                                 {x: i["vigente"][x] for x in ("partidos_judiciales_partidos", "comarcas_partidas", "frontera_cortada_km")}, k)
                self.assertTrue(i[k]["valido_reglas_actuales"])
            md = (out / "competicion" / "aut13" / "INDICADORES.md").read_text()
            for texto in ("(recuento bruto) frente al vigente: **OK**", "Comprobación 1", "| Vigente |", "| Canónico (canonico) |", "| Ganador (", "Part. judiciales", "PP medio"):
                self.assertIn(texto, md)
            r = self._aceptar(out, "aut13")
            self.assertEqual((r["vigente_peor"], r["vigente_sin"]), ([], []))
            self.assertIn("Frente al vigente", (out / "ACEPTACION.md").read_text())

    def test_t212_ganador_con_mas_fuera_de_tolerancia_que_el_vigente_es_no(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            pob = {"A": 100, "B": 130, "C": 100, "D": 70}  # total 400, objetivo 200, tolerancia 10 %
            # el vigente (B+D / A+C, discontinuo: no valdría hoy) tiene 0 distritos fuera; el mejor contiguo, A+B / C+D (230 / 170), 2
            self._competir_real(out, "aut13", cadena_ok=True, pob=pob, vigente={"A": "1", "B": "2", "C": "1", "D": "2"})
            i = json.loads((out / "competicion" / "aut13" / "INDICADORES.json").read_text())
            self.assertEqual((i["estado"], i["vigente"]["fuera_tolerancia"], i["vigente"]["valido_reglas_actuales"]), ("PEOR", 0, False))
            self.assertEqual(i["ganador_indicadores"]["fuera_tolerancia"], 2)
            self.assertIn("más distritos fuera de tolerancia (2 > 0)", i["motivo"])
            self.assertIn("Comprobación 2", (out / "competicion" / "aut13" / "INDICADORES.md").read_text())
            r = self._aceptar(out, "aut13")
            self.assertEqual((r["rc"], r["vigente_peor"], r["aceptacion"]), (1, ["aut13"], False))
            md = (out / "ACEPTACION.md").read_text()
            self.assertIn("Comprobación 2 · más distritos fuera de tolerancia (recuento bruto) que el mapa vigente publicado: ['aut13']", md)
            self.assertIn("Comprobación 1 · clave de elección peor que la del canónico: ninguno", md)  # son comprobaciones separadas

    def test_t212_mayor_desvio_maximo_solo_avisa(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            pob = {"A": 100, "B": 120, "C": 100, "D": 80}  # vigente discontinuo con desvío 0; mejor contiguo 10 % (dentro de tolerancia)
            self._competir_real(out, "aut13", cadena_ok=True, pob=pob, vigente={"A": "1", "B": "2", "C": "1", "D": "2"})
            i = json.loads((out / "competicion" / "aut13" / "INDICADORES.json").read_text())
            self.assertEqual((i["estado"], i["vigente"]["desvio_max"], round(i["ganador_indicadores"]["desvio_max"], 6)), ("OK", 0.0, 0.1))
            self.assertEqual(i["aviso_desvio"], ["mayor desvío máximo (10.00 % > 0.00 %)"])
            self.assertEqual(i["clave_frente_canonico"], "empata")
            r = self._aceptar(out, "aut13")
            self.assertEqual((r["vigente_peor"], r["vigente_aviso_desvio"]), ([], ["aut13"]))

    # Extracto mínimo de la batería r3 (run 42886114842; PR #685, datos/CANDIDATOS.csv, fuera_tolerancia BRUTO del ganador) y el
    # vigente publicado que da `composicion_publicada`: (run del vigente publicado, fuera del ganador, fuera esperado del vigente, veredicto de la comprobación 2). Si el vigente
    # cambia de run (una 00 publica otro), la fila se salta con aviso: hay que actualizar el extracto, no es un fallo del criterio.
    # El vigente se calcula aquí desde la composición publicada con el contrato; donde el laboratorio de T-179 (COMPARACION.csv,
    # lab_fuera_tol_A) tiene dato, coincide (Cantabria 9, CLM 5, CyL 1, Galicia 6, Cataluña 33, Navarra 11, C. Valenciana 29,
    # Extremadura 0, Madrid 26, País Vasco 8, Asturias 4, Murcia 10, La Rioja 1, Melilla 6). Andalucía y Aragón no tienen dato del laboratorio: solo el cálculo.
    REALES_R3 = {
        "aut01": ("42495072594", 21, 43, "OK"),                   # el canónico recalculado (20) es mejor que el ganador (21), pero el vigente tiene 43
        "aut02": ("42497101869", 2, 1, "PEOR"),                      # canónico recalculado 0
        "aut06": ("41037133327", 9, 9, "OK"),
        "aut08": ("40241650464", 8, 5, "PEOR"),
        "aut07": ("42521090842", 4, 1, "PEOR"),
        "aut09": ("41062562553", 41, 33, "PEOR"),
        "aut15": ("41049986588", 14, 11, "PEOR"),
        "aut10": ("41062567297", 31, 29, "PEOR"),
        "aut11": ("41042675119", 1, 0, "PEOR"),
        "aut12": ("40241719200", 8, 6, "PEOR"),
        "aut13": ("40787900559", 21, 26, "OK"),
        "aut16": ("40951146225", 9, 8, "PEOR"),
        "aut03": ("40132061626", 3, 4, "OK"),
        "aut14": ("42504383790", 10, 10, "OK"),
    }

    def _fuera_vigente(self, t: str) -> int:
        """Distritos fuera de tolerancia del vigente publicado, desde su composición (circunscripciones por provincia INE)."""
        from collections import defaultdict
        from fractions import Fraction
        from ddd_motor2.reglas import Criterio, Reglas
        pub, run = b.composicion_publicada(t)
        reglas = Reglas.desde_contrato(b._cfg(t), Criterio())
        pop, prov, pp = defaultdict(int), {}, defaultdict(int)
        with open(pub, encoding="utf-8") as fh:
            for f in csv.DictReader(fh):
                pop[f["distrito"]] += int(f["poblacion"])
                prov[f["distrito"]] = f["seccion"][:2]
                pp[f["seccion"][:2]] += int(f["poblacion"])
        objetivo, _, _, tol = reglas.limites(sum(pop.values()))
        cuotas = dict(reglas.cuotas)
        obj = {c: Fraction(pp[c], k) for c, k in cuotas.items() if k > 0} if len(cuotas) > 1 else None
        rel = [abs(Fraction(p) - (obj[prov[d]] if obj else objetivo)) / (obj[prov[d]] if obj else objetivo) for d, p in pop.items()]
        return sum(1 for x in rel if x > tol / objetivo)

    def test_t212_filas_reales_de_la_bateria_r3_frente_al_vigente_publicado(self):
        for t, (run, gan, vig, veredicto) in self.REALES_R3.items():
            with self.subTest(t=t):
                if b.composicion_publicada(t)[1] != run:
                    self.skipTest(f"{t}: el vigente publicado ya no es el run {run}; actualizar el extracto REALES_R3")
                self.assertEqual(self._fuera_vigente(t), vig)
                causas = b.peor_que({"fuera_tolerancia": gan, "desvio_max": 0.0}, {"fuera_tolerancia": vig, "desvio_max": 0.0})
                self.assertEqual("PEOR" if causas else "OK", veredicto)
        # Canarias (campo de partición DDD_PARTITION: el vigente solo se evalúa en el job, con los atributos del canónico): el
        # laboratorio da 22 y el ganador r3 21 → OK aunque el canónico recalculado (20) sea mejor que el ganador.
        self.assertEqual(b.peor_que({"fuera_tolerancia": 21, "desvio_max": 0}, {"fuera_tolerancia": 22, "desvio_max": 0}), [])
        from ddd_motor2.generadores import Vigente
        from ddd_motor2.vigente import vigente_publicado
        for t in b.territorios():  # T-258: un único vigente (el del visor) o el motivo explícito, nunca otro mapa
            v = vigente_publicado(t)
            self.assertTrue(v.ruta is not None or "no tiene composición versionada" in v.motivo, (t, v))
            self.assertEqual((b.composicion_publicada(t)[0], Vigente().ruta(t)[0]), (v.ruta, v.ruta), t)

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
            self._competir_real(out, "aut13", cadena_ok=True)  # distritos A+B y C+D: dos rectángulos 2:1
            i = json.loads((out / "competicion" / "aut13" / "INDICADORES.json").read_text())
            for k in ("vigente", "canonico", "ganador_indicadores"):
                self.assertNotIn("pp_error", i[k], i[k])
                self.assertAlmostEqual(i[k]["pp_medio"], 4 * 3.14159265 * 2 / 36, delta=0.03)  # rectángulo 2:1 ≈ 0,70
            self.assertIn("0.7", (out / "competicion" / "aut13" / "INDICADORES.md").read_text())

    def test_t212_peor_es_el_recuento_bruto_de_fuera_de_tolerancia(self):
        g = {"fuera_tolerancia": 1, "desvio_max": 0.3}
        self.assertEqual(b.peor_que(g, {"fuera_tolerancia": 1, "desvio_max": 0.3}), [])
        self.assertEqual(b.peor_que(g, {"fuera_tolerancia": 2, "desvio_max": 0.1}), [])
        self.assertEqual(b.peor_que(g, {"fuera_tolerancia": 1, "desvio_max": 0.2}), [])  # el desvío no bloquea
        self.assertEqual(len(b.peor_que(g, {"fuera_tolerancia": 0, "desvio_max": 0.9})), 1)
        self.assertIn("mayor desvío máximo", b.aviso_desvio(g, {"fuera_tolerancia": 1, "desvio_max": 0.2})[0])
        self.assertEqual(b.aviso_desvio(g, {"fuera_tolerancia": 1, "desvio_max": 0.3}), [])

    def test_t224_sin_vigente_comparable_consta_y_no_bloquea(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True, vigente=None)
            self.assertEqual(json.loads((out / "competicion" / "aut13" / "INDICADORES.json").read_text())["estado"], "SIN_VIGENTE")
            r = self._aceptar(out, "aut13")  # T-224/T-258: consta con su motivo y no bloquea (PARCIAL solo por las huellas)
            self.assertEqual((r["rc"], r["vigente_sin"], r["aceptacion"]), (0, [], False))
            self.assertIn("sin composición vigente", r["vigente_no_comparable"]["aut13"])
            self.assertIn("Sin vigente comparable", (out / "ACEPTACION.md").read_text())

    def _con_bloque_vigente(self, out: Path, t: str, bloque: dict) -> dict:
        """T-258: reescribe el bloque «vigente» del COMPETICION.json y vuelve a medir con el vigente publicado."""
        f = out / "competicion" / t / "COMPETICION.json"
        d = json.loads(f.read_text())
        d["vigente"] = bloque
        f.write_text(json.dumps(d))
        from tests.test_motor2_semilla import cfg as cfg_con_ancla
        r = b.indicadores_territorio(t, out, cfg=cfg_con_ancla(), grafo=out / "grafo.json", vigente=(out / "vigente.csv", "123"))
        b.escribir_indicadores(r, out)
        return r

    def test_t258_la_aceptacion_mide_el_mismo_vigente_que_la_competicion(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            h = hashlib.sha256((out / "vigente.csv").read_bytes()).hexdigest()
            self.assertEqual(self._con_bloque_vigente(out, "aut13", {"estado": "VALIDO", "sha256_origen": h})["estado"], "OK")
            r = self._con_bloque_vigente(out, "aut13", {"estado": "VALIDO", "sha256_origen": "f" * 64,
                                                          "origen": "datos/composicion/madrid.csv"})
            self.assertEqual(r["estado"], "NO_EVALUABLE")  # otro vigente en la competición: nunca se compara en silencio
            self.assertIn("vigente distinto del publicado", r["motivo"])
            self.assertEqual((self._aceptar(out, "aut13")["rc"], self._aceptar(out, "aut13")["vigente_sin"]), (1, ["aut13"]))

    def test_t258_otro_seccionado_es_sin_vigente_comparable_y_no_bloquea(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            motivo = "vigente excluido: otro seccionado (madrid.csv): 3 secciones de la entrada sin distrito vigente"
            r = self._con_bloque_vigente(out, "aut13", {"estado": "VIGENTE_OTRO_SECCIONADO", "compite": False,
                                                          "detalle": motivo})
            self.assertEqual((r["estado"], r["motivo"]), ("SIN_VIGENTE", motivo))
            a = self._aceptar(out, "aut13")
            self.assertEqual((a["rc"], a["vigente_sin"], a["vigente_no_comparable"]), (0, [], {"aut13": motivo}))

    def test_t212_sin_indicadores_o_no_evaluable_no_es_verde_por_omision(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True, vigente="no_escribir")
            r = self._aceptar(out, "aut13")
            self.assertEqual((r["rc"], r["vigente_sin"]), (1, ["aut13"]))
            self.assertEqual(r["vigente_motivos"]["aut13"], "sin INDICADORES.json")
        ok = lambda t: {"territorio": t, "estado": "VALIDO", "frente_al_canonico": "empata"}  # noqa: E731
        c = b.criterio_aceptacion([ok("x")], {}, ["x"], vigentes={"x": {"territorio": "x", "estado": "NO_EVALUABLE", "motivo": "KeyError: z"}})
        self.assertEqual((c["vigente_sin"], c["vigente_motivos"]), (["x"], {"x": "KeyError: z"}))
        u = b.criterio_aceptacion([ok("c")], {}, ["c"], vigentes={"c": {"territorio": "c", "estado": "UN_DISTRITO"}})
        self.assertEqual((u["vigente_sin"], u["vigente_un_distrito"]), ([], ["c"]))  # el único plan posible: consta y no bloquea

    def test_t212_vigente_con_otras_secciones_no_es_evaluable(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            pub = out / "otro.csv"
            pub.write_text("seccion,distrito,poblacion\n2200101000,0,100\n", encoding="utf-8")
            from tests.test_motor2_semilla import cfg as cfg_con_ancla
            r = b.indicadores_territorio("aut13", out, cfg=cfg_con_ancla(), grafo=out / "grafo.json", vigente=(pub, "1"))
            self.assertEqual(r["estado"], "NO_EVALUABLE")
            self.assertIn("secciones distintas", r["motivo"])

    def test_t181_generador_fallido_da_no_aunque_gane_el_canonico(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            fila = self._competir_real(out, "aut13", cadena_ok=False)
            self.assertEqual((fila["estado"], fila["ganador"]), ("VALIDO", "canonico"))  # el caso de T-208: todo «válido»
            r = self._aceptar(out, "aut13")
            self.assertEqual(r["rc"], 1)
            self.assertEqual((r["sin_cadenas"], r["fallo_generador"]), (["aut13"], ["aut13"]))
            self.assertFalse(r["aceptacion"])

    def test_t181_cadenas_evaluables_no_bloquean(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            r = self._aceptar(out, "aut13")
            self.assertEqual((r["rc"], r["sin_cadenas"], r["fallo_generador"]), (0, [], []))  # PARCIAL: sin huellas, pero sin fallos

    def test_t181_numero_de_candidatos_distinto_de_1_mas_n_es_no(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)  # 2 cadenas + canónico + exhaustivo
            self.assertEqual(self._aceptar(out, "aut13", 2)["candidatos_incompletos"], [])
            self.assertEqual(self._aceptar(out, "aut13", 10)["candidatos_incompletos"], ["aut13"])

    def test_t181_sin_competicion_json_es_no(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            self._competir_real(out, "aut13", cadena_ok=True)
            (out / "competicion" / "aut13" / "COMPETICION.json").unlink()
            self.assertEqual(self._aceptar(out, "aut13")["sin_cadenas"], ["aut13"])

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
        src = (ROOT / "paquetes/deslinde/src/deslinde/ponderado.py").read_text(encoding="utf-8")  # T-257: Deslinde
        for linea in ("from gerrychain.tree.spanning_tree import _ordered_edge_ids", "from gerrychain import Graph, MarkovChain, Partition, updaters",
                      "from gerrychain.proposals import recom", "from gerrychain.tree import bipartition_tree"):
            self.assertIn(linea, src)
        lock = (ROOT / "requirements-ensemble.lock").read_text().lower()
        self.assertNotIn("pip install --requirement requirements-ensemble.lock", txt)  # T-181b: subía pandas 3 y rompía M04-M06
        self.assertIn("gerrychain==", lock)
        self.assertIn("networkx==", lock)
        self.assertIn("--cadenas", self.wf["jobs"]["aceptacion"]["steps"][-2]["run"])


class LectorVigenteT229(unittest.TestCase):
    """T-229: casos de la fase 2 de r5 (run 42927322822) que quedaron «sin comparación» por el lector del vigente."""

    COL = "CUSEC_KEY,district_id,section_pop,CUMUN,ddd_unit_id\n"

    def _montar(self, out: Path, t: str, filas_can: list[tuple], pub_map: dict, *, ganador="canonico",
                fino: list[tuple] | None = None, sha_ok=True):
        """COMPETICION.json con canónico (con GeoJSON) y vigente (sin GeoJSON, como lo deja el generador)."""
        import hashlib
        carpeta = out / "competicion" / t
        (carpeta / "canonico").mkdir(parents=True)
        (carpeta / "vigente").mkdir(parents=True)
        nombre = f"{t}_2025_m06_composicion_distritos.csv"
        can = carpeta / "canonico" / nombre
        can.write_text(self.COL + "".join(",".join(map(str, f)) + "\n" for f in filas_can), encoding="utf-8")
        (carpeta / "canonico" / f"{t}_2025_m06_secciones.geojson.zip").write_bytes(b"x")
        pub = out / f"{t}.csv"
        pub.write_text("seccion,distrito,poblacion\n" + "".join(f"{s},{d},1\n" for s, d in pub_map.items()), encoding="utf-8")
        vig = carpeta / "vigente" / nombre
        vig.write_text(self.COL + "".join(",".join(map(str, f)) + "\n" for f in (fino or filas_can)), encoding="utf-8")
        sha = hashlib.sha256(pub.read_bytes()).hexdigest() if sha_ok else "0" * 64
        d = {"territorio": t, "canonico": "canonico", "ganador": ganador, "vigente": {"estado": "VALIDO", "sha256_origen": sha},
             "candidatos": [{"id": "canonico", "composicion": str(can)}, {"id": "vigente", "composicion": str(vig)}]}
        (carpeta / "COMPETICION.json").write_text(json.dumps(d), encoding="utf-8")
        return pub, can, vig

    def _indicadores(self, out, t, pub, falso):
        from unittest import mock
        cfg = {"validation": {"expected_districts": 2}}
        with mock.patch.object(b, "_indicadores_plan", side_effect=falso):
            return b.indicadores_territorio(t, out, cfg=cfg, grafo=out / "grafo.json", vigente=(pub, "1"))

    @staticmethod
    def _plan(ft=0):
        return {"distritos": 2, "fuera_tolerancia": ft, "desvio_max": 0.1, "partidos_judiciales_partidos": 0,
                "comarcas_partidas": 0, "frontera_cortada_km": 0.0, "valido_reglas_actuales": True}

    def test_unidades_internas_ganador_vigente_usa_los_atributos_del_canonico(self):
        # Extremadura (unidad «74») y Asturias («33:33044#P01:M»): el ganador es el vigente, sin GeoJSON propio;
        # antes se evaluaba sin atributos y faltaba unidad_r012 (M04_PARTITION_UNIT).
        from ddd_motor2.adaptadores import ErrorDatos
        for t, u in (("aut11", "74"), ("aut03", "33:33044#P01:M")):
            with tempfile.TemporaryDirectory() as d:
                out = Path(d)
                filas = [("0601801001", 0, 771, "06018", u), ("0601801002", 1, 700, "06018", "75")]
                pub, can, vig = self._montar(out, t, filas, {"0601801001": "10", "0601801002": "11"}, ganador="vigente")
                attrs_can = next((out / "competicion" / t / "canonico").glob("*_m06_secciones.geojson*"))

                def falso(comp, cfg, grafo, ref, attrs):
                    if attrs is None:
                        raise ErrorDatos(f"faltan campos requeridos por las reglas activas: unidad_r012: 1 unidades (p. ej. {u})")
                    self.assertEqual(attrs, attrs_can)
                    return self._plan()
                r = self._indicadores(out, t, pub, falso)
                self.assertEqual(r["estado"], "OK", r["motivo"])
                self.assertEqual(r["ganador"], "vigente")

    def _partido(self, t, s1, s2, uid):
        """Unidad M04 `uid` (dos secciones) que el vigente publicado reparte entre los distritos 1 y 2."""
        filas = [(s1, 0, 500, s1[:5], uid), (s2, 0, 500, s1[:5], uid)]
        fino = [(s1, 1, 500, s1[:5], f"{uid}~v1"), (s2, 2, 500, s1[:5], f"{uid}~v2")]
        return filas, fino, {s1: "1", s2: "2"}

    def _falso_atomico(self, can_vig_m04):
        from ddd_motor2.adaptadores import ErrorDatos

        def falso(comp, cfg, grafo, ref, attrs):
            if Path(comp).name == "vigente_m06_composicion_distritos.csv":
                raise ErrorDatos("unidades repartidas entre distritos (atomicidad): 1 (p. ej. " + can_vig_m04 + ")")
            return self._plan()
        return falso

    def test_unidad_m04_repartida_usa_el_vigente_de_piezas_finas(self):
        # Canarias (38-C01:38023:38-C01:R) y Cataluña (08:08200:U1): el vigente reparte una unidad M04 de un
        # municipio divisible; el generador lo representa con piezas finas y esa composición es la que se compara.
        for t, s1, s2, uid in (("aut05", "3802301001", "3802301002", "38-C01:38023:38-C01:R"),
                               ("aut09", "0820001001", "0820001002", "08:08200:U1")):
            with tempfile.TemporaryDirectory() as d:
                out = Path(d)
                filas, fino, pub_map = self._partido(t, s1, s2, uid)
                pub, _, vig = self._montar(out, t, filas, pub_map, fino=fino)
                r = self._indicadores(out, t, pub, self._falso_atomico(uid))
                self.assertEqual(r["estado"], "OK", r["motivo"])
                self.assertIn("piezas finas", r["vigente_lectura"])

    def test_sin_vigente_fino_fiel_sigue_sin_comparacion(self):
        # nunca verde por omisión: si la composición de la competición no es la del publicado, «sin comparación»
        t, s1, s2, uid = "aut05", "3802301001", "3802301002", "38-C01:38023:38-C01:R"
        filas, fino, pub_map = self._partido(t, s1, s2, uid)
        casos = {"otro sha256": dict(sha_ok=False, fino=fino),
                 "otros distritos": dict(fino=[(s1, 1, 500, s1[:5], f"{uid}~v1"), (s2, 1, 500, s1[:5], f"{uid}~v1")])}
        for caso, kw in casos.items():
            with tempfile.TemporaryDirectory() as d:
                out = Path(d)
                pub, _, _ = self._montar(out, t, filas, pub_map, **kw)
                r = self._indicadores(out, t, pub, self._falso_atomico(uid))
                self.assertEqual(r["estado"], "NO_EVALUABLE", caso)  # T-258: otro sha256 = vigente distinto del publicado
                self.assertIn("distinto del publicado" if caso == "otro sha256" else "atomicidad", r["motivo"], caso)

    def test_vigente_fino_peor_sigue_siendo_peor(self):
        # el criterio no cambia: si el vigente (piezas finas) tiene menos fuera de tolerancia, el ganador es PEOR
        t, s1, s2, uid = "aut09", "0820001001", "0820001002", "08:08200:U1"
        filas, fino, pub_map = self._partido(t, s1, s2, uid)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            pub, _, vig = self._montar(out, t, filas, pub_map, fino=fino)
            base = self._falso_atomico(uid)
            r = self._indicadores(out, t, pub, lambda c, *a: self._plan(0) if Path(c) == vig else (base(c, *a) and self._plan(3)))
            self.assertEqual(r["estado"], "PEOR")
class RecuentoDelContrato(unittest.TestCase):
    """T-228: la comprobación 2 cuenta como el contrato y la competición (objetivo regional), no por circunscripción.
    r5 fase 2 (run 42927322822): Castilla-La Mancha, ganador 5 del contrato (= vigente) y 6 por circunscripción: PEOR falso."""

    @staticmethod
    def _natural():
        from fractions import Fraction
        from ddd_motor2.naturalidad_clave import Natural
        n = Natural()
        n.fuera_contrato = True
        n.pob_u = {"a": 122, "b": 158, "c": 120, "d": 120}
        n.circ_u = {"a": "01", "b": "01", "c": "02", "d": "02"}
        n.objetivo, n.tol = Fraction(520, 4), Fraction(520, 4) * Fraction(12, 100)  # 130, tolerancia 12 %
        n.obj_circ = {"01": Fraction(280, 2), "02": Fraction(240, 2)}  # 140 y 120
        n.pj = n.ca = {u: None for u in n.pob_u}
        n.largo = {}
        return n

    def test_t228_recuento_regional_igual_al_primer_termino_de_la_clave_d8(self):
        n = self._natural()
        plan = {u: u for u in n.pob_u}  # un distrito por unidad
        r = b.recuento_contrato(n, plan)
        # objetivo regional 130: solo 158 (21,5 %) fuera; por circunscripción, 122 y 158 (12,9 % de 140) fuera
        self.assertEqual((r["fuera_tolerancia"], r["fuera_tolerancia_circunscripcion"]), (1, 2))
        self.assertEqual(r["fuera_tolerancia"], n.clave(plan, "D8", "x")[0])  # la misma medida que elige la competición
        self.assertAlmostEqual(r["desvio_max"], 28 / 130)
        self.assertAlmostEqual(r["desvio_max_circunscripcion"], 18 / 140)
        # un ganador igual que el vigente en el contrato no es PEOR aunque difiera por circunscripción
        vig = {**r, "fuera_tolerancia_circunscripcion": 1}
        self.assertEqual(b.peor_que(r, vig), [])
        self.assertEqual(len(b.peor_que(r, {**r, "fuera_tolerancia": 0})), 1)  # y uno peor del contrato sigue siendo NO


class T233VolcadoDelLog(unittest.TestCase):
    """T-233: si entradas_uno falla, la cola de log.txt y un ::error salen en la salida del paso."""

    def _uno(self, rc_adq: int, rc_m: int = 0) -> tuple[dict, str]:
        import contextlib
        import io
        from unittest import mock
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        decl = tmp / "decl.yaml"
        decl.write_text("x: 1\n", encoding="utf-8")
        cache = tmp / "cache"

        def run(cmd, log, env):
            with open(log, "a", encoding="utf-8") as fh:
                fh.write("".join(f"linea {i}\n" for i in range(100)))
                if "-c" in cmd:
                    if rc_adq:
                        fh.write("Traceback (most recent call last):\nRuntimeError: OGC no responde\n")
                        return rc_adq, 1.0
                    mat = tmp / "out" / "_trabajo" / "t" / "ev" / "materialized" / "inputs"
                    mat.mkdir(parents=True, exist_ok=True)
                    return 0, 1.0
            cache.mkdir(exist_ok=True)
            return rc_m, 1.0

        buf = io.StringIO()
        with mock.patch.object(b, "_run", run), mock.patch.object(b, "_declaracion_temporal", lambda *a: decl), \
                mock.patch.object(b, "_huellas_contrato", lambda c: {}), mock.patch.object(b, "_cfg", lambda t: {}), \
                mock.patch.object(b, "_cache", lambda t: cache), mock.patch.object(b, "contrato", lambda t: b.ROOT / "c.yaml"), \
                mock.patch.object(b, "_guardar_minima", lambda *a: None), contextlib.redirect_stdout(buf):
            r = b.entradas_uno("t", tmp / "out", {}, "ogc")
        return r, buf.getvalue()

    def test_fallo_de_adquisicion_vuelca_la_cola_y_el_motivo(self):
        r, salida = self._uno(rc_adq=1)
        self.assertEqual(r["estado"], "FALLO_ADQUISICION")
        self.assertIn("RuntimeError: OGC no responde", salida)
        self.assertIn("linea 99", salida)
        self.assertNotIn("linea 41\n", salida)  # solo las últimas 60 líneas
        self.assertIn("::error title=entradas t::FALLO_ADQUISICION rc=1: RuntimeError: OGC no responde", salida)

    def test_fallo_de_m01_tambien_vuelca(self):
        r, salida = self._uno(rc_adq=0, rc_m=2)
        self.assertEqual(r["estado"], "FALLO_M01")
        self.assertIn("::error title=entradas t::FALLO_M01 rc=2:", salida)

    def test_exito_sin_ruido(self):
        r, salida = self._uno(rc_adq=0)
        self.assertEqual(r["estado"], "OK")
        self.assertEqual(salida, "")


if __name__ == "__main__":
    unittest.main()
