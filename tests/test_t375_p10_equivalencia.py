# -*- coding: utf-8 -*-
"""T-375 (D-136, paso 6): P10 Fuentes sustituye a `preparacion-fuentes.yml` y `preparacion-resultados-electorales.yml`.

PROYECTO: Diputado de Distrito · VERSIÓN: 1.0.0 · FECHA: 2026-11-16 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
Equivalencia contra COPIAS CONGELADAS (`tests/fixtures/t375_workflows/`, sha256; en CI no hay `legacy/`): si falta una o cambia su huella el test FALLA
(no se salta). Por tipo (P11 y P12): jobs, comandos, permisos, concurrencias, salidas y registro. Controles negativos al final.
"""
import copy
import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t375_workflows"
SHAS = {
    "preparacion-fuentes_1.4.14.yml": "dfdf81addc11a342d1a15640848926e454fa8c0924a7b8a8aef27ec0f09bafb3",
    "preparacion-resultados-electorales_1.0.17.yml": "efe7637d042707f5e266edb71d6899b940d9d5baaf2763adf385c8ac3dacbd4d",
}
# Las ÚNICAS diferencias de comandos permitidas dentro de los jobs (todo lo demás, idéntico paso a paso).
P11_RESUELVE_VIEJO = "            reuse_enabled=true\n            persist_requested=true\n"
P11_RESUELVE_NUEVO = ("            reuse_enabled=true\n"
                      "            [[ \"$REUSE_INPUT\" == false ]] && reuse_enabled=false  # T-375: «regenerar aunque exista» de P10\n"
                      "            persist_requested=true\n")
P12_PREVIO_VIEJO = """          [[ -n "$match" ]] || { echo "::error::Artefacto electoral registrado no disponible"; exit 44; }"""
P12_PREVIO_NUEVO = """          # T-375 (D-136, reutilizar automático): caducado o eliminado no contradice la identidad registrada: se prepara de nuevo.
          [[ -n "$match" ]] || { echo "::warning::Artefacto electoral registrado no disponible (caducado o eliminado): $REGISTERED_ARTIFACT_NAME (run $REGISTERED_RUN_ID); se prepara de nuevo."; { echo "### Paquete electoral: PREPARARÁ (registrado no disponible)"; echo "- Registrado: $REGISTERED_ARTIFACT_NAME (run $REGISTERED_RUN_ID), caducado o eliminado"; } >> "$GITHUB_STEP_SUMMARY"; exit 0; }"""


def _d(t):
    """Quita la sangría de bloque (10 espacios) que el YAML elimina al leer un `run: |`."""
    return "\n".join(l[10:] if l.startswith(" " * 10) else l for l in t.split("\n"))


P11_RESUELVE_VIEJO, P11_RESUELVE_NUEVO = _d(P11_RESUELVE_VIEJO), _d(P11_RESUELVE_NUEVO)
P12_PREVIO_VIEJO, P12_PREVIO_NUEVO = _d(P12_PREVIO_VIEJO), _d(P12_PREVIO_NUEVO)


def on(d):
    return d.get("on") or d.get(True)


def cargar(ruta):
    return yaml.safe_load(Path(ruta).read_text(encoding="utf-8"))


def viejo(nombre):
    p = FIX / nombre
    if not p.is_file():
        raise AssertionError(f"falta la copia congelada {nombre}")
    if hashlib.sha256(p.read_bytes()).hexdigest() != SHAS[nombre]:
        raise AssertionError(f"la copia congelada {nombre} cambió de huella")
    return cargar(p)


def paso(job, nombre=None, id_=None):
    return next(s for s in job["steps"] if (nombre and s.get("name") == nombre) or (id_ and s.get("id") == id_))


def aplicar(workflow, job, id_paso, a, b):
    """Copia del workflow con `a`→`b` en el run del paso `id_paso` del job (para neutralizar la diferencia permitida)."""
    w = copy.deepcopy(workflow)
    s = paso(w["jobs"][job], id_=id_paso)
    assert a in s["run"], (job, id_paso)
    s["run"] = s["run"].replace(a, b, 1)
    return w


def diferencias(viejo_wf, nuevo_wf):
    """Diferencias NO permitidas entre los jobs del reutilizable y los del workflow viejo (vacía = equivalente)."""
    d = []
    if set(viejo_wf["jobs"]) != set(nuevo_wf["jobs"]):
        d.append("conjunto de jobs")
    for k, j in viejo_wf["jobs"].items():
        n = nuevo_wf["jobs"].get(k)
        if n != j:
            d.append(f"job {k}")
    if viejo_wf["permissions"] != nuevo_wf["permissions"]:
        d.append("permisos")
    if viejo_wf.get("env") != nuevo_wf.get("env"):
        d.append("env")
    if on(viejo_wf)["workflow_call"].get("outputs") != on(nuevo_wf)["workflow_call"].get("outputs"):
        d.append("salidas")
    return d


class P11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = viejo("preparacion-fuentes_1.4.14.yml")
        cls.b = cargar(WF / "_p11-territoriales.yml")

    def test_jobs_permisos_salidas_identicos(self):
        neutral = aplicar(self.b, "resolver", "resolve", P11_RESUELVE_NUEVO, P11_RESUELVE_VIEJO)
        self.assertEqual(diferencias(self.a, neutral), [])

    def test_los_cinco_jobs_y_su_registro(self):
        self.assertEqual(list(self.b["jobs"]), ["resolver", "territoriales", "registrar", "generation_pending", "resultado"])
        reg = self.b["jobs"]["registrar"]
        self.assertEqual(reg["concurrency"], {"group": "ddd-catalog-promotion", "cancel-in-progress": False, "queue": "max"})
        self.assertEqual(reg["concurrency"], self.a["jobs"]["registrar"]["concurrency"])
        for j in ("registrar", "generation_pending"):
            self.assertTrue(any(s.get("name") == "Credencial de registro" for s in self.b["jobs"][j]["steps"]), j)

    def test_entradas_de_llamada_iguales_salvo_edicion_opcional(self):
        ia, ib = on(self.a)["workflow_call"]["inputs"], on(self.b)["workflow_call"]["inputs"]
        self.assertEqual(set(ia), set(ib))
        for k in ia:
            if k == "data_edition":
                self.assertEqual(ia[k], {"required": True, "type": "string"})
                self.assertEqual(ib[k], {"required": False, "type": "string", "default": ""})
            else:
                self.assertEqual(ia[k], ib[k], k)

    def test_sin_boton_ni_concurrencia_de_workflow(self):
        self.assertNotIn("workflow_dispatch", on(self.b))
        self.assertNotIn("concurrency", self.b)

    def test_regenerar_se_respeta_con_edicion_vacia(self):
        run = paso(self.b["jobs"]["resolver"], id_="resolve")["run"]
        self.assertIn('[[ "$REUSE_INPUT" == false ]] && reuse_enabled=false', run)
        # El resto del cuerpo, idéntico: quitar la línea nueva devuelve el viejo.
        self.assertEqual(run.replace(P11_RESUELVE_NUEVO, P11_RESUELVE_VIEJO), paso(self.a["jobs"]["resolver"], id_="resolve")["run"])


class P12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = viejo("preparacion-resultados-electorales_1.0.17.yml")
        cls.b = cargar(WF / "_p12-electorales.yml")

    def test_jobs_permisos_salidas_identicos(self):
        neutral = aplicar(self.b, "electorales", "previous", P12_PREVIO_NUEVO, P12_PREVIO_VIEJO)
        self.assertEqual(diferencias(self.a, neutral), [])

    def test_los_cuatro_jobs_y_su_registro(self):
        self.assertEqual(list(self.b["jobs"]), ["resolver", "electorales", "registrar", "resultado"])
        reg = self.b["jobs"]["registrar"]
        self.assertEqual(reg["concurrency"], {"group": "ddd-catalog-promotion", "cancel-in-progress": False, "queue": "max"})
        self.assertTrue(any(s.get("name") == "Credencial de registro" for s in reg["steps"]))
        self.assertEqual(reg["if"], self.a["jobs"]["registrar"]["if"])

    def test_entradas_y_salidas_iguales(self):
        self.assertEqual(on(self.a)["workflow_call"]["inputs"], on(self.b)["workflow_call"]["inputs"])
        self.assertEqual(self.a["env"], self.b["env"])

    def test_sin_boton_ni_concurrencia_de_workflow(self):
        self.assertNotIn("workflow_dispatch", on(self.b))
        self.assertNotIn("concurrency", self.b)

    def test_caducado_ya_no_falla_pero_el_digest_distinto_si(self):
        run = paso(self.b["jobs"]["electorales"], id_="previous")["run"]
        self.assertNotIn("exit 44", run)
        self.assertIn("exit 0; }", run)
        self.assertIn("Digest de artefacto electoral no coincide con el registro.", run)
        self.assertEqual(run.replace(P12_PREVIO_NUEVO, P12_PREVIO_VIEJO), paso(self.a["jobs"]["electorales"], id_="previous")["run"])


class P10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p10 = cargar(WF / "p10-fuentes.yml")
        cls.p11 = cargar(WF / "_p11-territoriales.yml")
        cls.p12 = cargar(WF / "_p12-electorales.yml")
        cls.a11 = viejo("preparacion-fuentes_1.4.14.yml")
        cls.a12 = viejo("preparacion-resultados-electorales_1.0.17.yml")

    def test_nombre_boton_y_opciones(self):
        self.assertEqual(self.p10["name"], "P10 Fuentes")
        d = on(self.p10)["workflow_dispatch"]["inputs"]
        self.assertEqual(set(d), {"tipo", "territorios", "eleccion", "regenerar"})
        self.assertEqual(d["tipo"]["options"], ["P11 territoriales", "P12 electorales"])
        self.assertEqual(d["eleccion"]["options"], ["vigente", "ensayo 2026-11-29"])
        self.assertEqual(d["eleccion"]["default"], "vigente")
        self.assertIs(d["regenerar"]["default"], False)
        self.assertEqual(d["regenerar"]["type"], "boolean")
        for k in ("edition", "data_edition", "territory_id", "source_ref", "persist_state", "recover_run_id"):
            self.assertNotIn(k, d)

    def test_salidas_son_la_union_de_las_dos(self):
        out = on(self.p10)["workflow_call"]["outputs"]
        viejas = set(on(self.a11)["workflow_call"]["outputs"]) | set(on(self.a12)["workflow_call"]["outputs"])
        self.assertEqual(set(out), viejas)
        # Cada salida lee del job de su tipo (las dos del mismo nombre, con `||`).
        for k, o in out.items():
            self.assertTrue("jobs.p11.outputs." in o["value"] or "jobs.p12.outputs." in o["value"], k)

    def test_entradas_de_llamada_cubren_las_de_los_dos_viejos(self):
        i = on(self.p10)["workflow_call"]["inputs"]
        for viejo_wf in (self.a11, self.a12):
            for k, v in on(viejo_wf)["workflow_call"]["inputs"].items():
                self.assertIn(k, i)
                if v.get("type") == "boolean":
                    self.assertEqual(i[k], v, k)
        self.assertEqual(i["tipo"], {"required": True, "type": "string"})

    def test_permisos_y_plan_sin_permisos(self):
        self.assertEqual(self.p10["permissions"], self.a11["permissions"])
        self.assertEqual(self.p10["permissions"], self.a12["permissions"])
        self.assertEqual(self.p10["jobs"]["plan"]["permissions"], {})
        for j in ("p11", "p12"):
            self.assertNotIn("permissions", self.p10["jobs"][j])

    def test_concurrencias_por_tipo_iguales_a_las_de_antes(self):
        n = {k: self.p10["jobs"][k]["concurrency"] for k in ("p11", "p12")}
        c11, c12 = self.a11["concurrency"], self.a12["concurrency"]
        sust = lambda g: g.replace("inputs.territory_id", "matrix.territorio").replace("inputs.data_edition", "needs.plan.outputs.edicion")
        self.assertEqual(n["p11"], {**c11, "group": sust(c11["group"])})
        self.assertEqual(n["p12"], {**c12, "group": sust(c12["group"])})
        self.assertEqual(n["p11"]["queue"], "max")
        self.assertEqual(n["p12"]["queue"], "max")
        self.assertTrue(n["p11"]["group"].startswith("ddd-territorial-prod-"))
        self.assertTrue(n["p12"]["group"].startswith("ddd-electoral-prod-"))
        self.assertFalse(n["p11"]["cancel-in-progress"] or n["p12"]["cancel-in-progress"])

    def test_matriz_independiente_por_territorio(self):
        for j in ("p11", "p12"):
            job = self.p10["jobs"][j]
            self.assertIs(job["strategy"]["fail-fast"], False)
            self.assertLessEqual(job["strategy"]["max-parallel"], 6)
            self.assertIn("fromJSON(needs.plan.outputs.territorios)", job["strategy"]["matrix"]["territorio"])
            self.assertEqual(job["secrets"], "inherit")
            self.assertEqual(job["needs"], "plan")
        self.assertEqual(self.p10["jobs"]["p11"]["uses"], "./.github/workflows/_p11-territoriales.yml")
        self.assertEqual(self.p10["jobs"]["p12"]["uses"], "./.github/workflows/_p12-electorales.yml")

    def test_with_solo_entradas_que_existen_y_cubren_las_obligatorias(self):
        for j, h in (("p11", self.p11), ("p12", self.p12)):
            ins = on(h)["workflow_call"]["inputs"]
            w = self.p10["jobs"][j]["with"]
            self.assertTrue(set(w) <= set(ins), (j, set(w) - set(ins)))
            for k, v in ins.items():
                if v.get("required"):
                    self.assertIn(k, w, (j, k))
        # P12 no recibe las entradas exclusivas de P11 y viceversa.
        self.assertNotIn("recover_run_id", self.p10["jobs"]["p12"]["with"])
        self.assertNotIn("allow_source_gap_success", self.p10["jobs"]["p11"]["with"])

    def test_los_callers_pasan_tipo_y_entradas_validas(self):
        entradas = on(self.p10)["workflow_call"]["inputs"]
        for fichero, jobs in (("ejecucion-completa-proyecto.yml", {"preparar_territorial": "territoriales", "preparar_electoral": "electorales"}),
                              ("preparacion-legislatura-vigente.yml", {"territorial": "territoriales", "electoral": "electorales"})):
            w = cargar(WF / fichero)
            for job, tipo in jobs.items():
                j = w["jobs"][job]
                self.assertEqual(j["uses"], "./.github/workflows/p10-fuentes.yml", (fichero, job))
                self.assertEqual(j["with"]["tipo"], tipo)
                self.assertTrue(set(j["with"]) <= set(entradas), (fichero, job, set(j["with"]) - set(entradas)))
                for k, v in entradas.items():
                    if v.get("required"):
                        self.assertIn(k, j["with"])

    def test_ningun_workflow_cita_los_ficheros_borrados(self):
        for p in WF.glob("*.yml"):
            t = p.read_text(encoding="utf-8")
            if p.name == "p10-fuentes.yml":  # solo en la cabecera de historia
                t = "\n".join(l for l in t.splitlines() if not l.startswith("#"))
            for viejo_nombre in ("preparacion-fuentes.yml", "preparacion-resultados-electorales.yml"):
                self.assertNotIn(f"workflows/{viejo_nombre}", t, p.name)
        self.assertFalse((WF / "preparacion-fuentes.yml").exists())
        self.assertFalse((WF / "preparacion-resultados-electorales.yml").exists())

    def test_ninguna_clave_duplicada_ni_booleanos_mal_tipados(self):
        for n in ("p10-fuentes.yml", "_p11-territoriales.yml", "_p12-electorales.yml"):
            class Estricto(yaml.SafeLoader):
                pass

            def construir(loader, node, deep=False):
                claves = [loader.construct_object(k, deep=deep) for k, _ in node.value]
                dup = {k for k in claves if claves.count(k) > 1}
                if dup:
                    raise AssertionError(f"{n}: claves duplicadas {dup}")
                return yaml.SafeLoader.construct_mapping(loader, node, deep)

            Estricto.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construir)
            yaml.load((WF / n).read_text(encoding="utf-8"), Loader=Estricto)


class PlanBajoBash(unittest.TestCase):
    """El paso «Resolver tipo, territorios y opciones» ejecutado de verdad bajo `bash -eo pipefail`."""

    @classmethod
    def setUpClass(cls):
        cls.script = paso(cargar(WF / "p10-fuentes.yml")["jobs"]["plan"], id_="plan")["run"]

    def ejecutar(self, **env):
        base = {"TIPO": "", "TERRITORIOS": "", "TERRITORIO_LLAMADA": "", "DATA_EDITION": "", "ELECCION": "", "REGENERAR": "",
                "REUTILIZAR_LLAMADA": "", "PERSISTIR_LLAMADA": "", "HUECO_LLAMADA": ""}
        base.update(env)
        with tempfile.TemporaryDirectory() as t:
            out, summ = Path(t) / "out", Path(t) / "summary"
            out.write_text("")
            e = {**os.environ, **base, "GITHUB_OUTPUT": str(out), "GITHUB_STEP_SUMMARY": str(summ)}
            r = subprocess.run(["bash", "-eo", "pipefail", "-c", self.script], env=e, capture_output=True, text=True)
            salida = dict(l.split("=", 1) for l in out.read_text().splitlines() if "=" in l)
        return r, salida

    def test_boton_territoriales(self):
        r, o = self.ejecutar(TIPO="P11 territoriales", TERRITORIOS="aut13, nac28,aut13", ELECCION="vigente", REGENERAR="false")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(o["tipo"], "territoriales")
        self.assertEqual(o["territorios"], '["aut13","nac28"]')
        self.assertEqual((o["edicion"], o["reutilizar"], o["persistir"], o["hueco_fuente"], o["eleccion"]), ("", "true", "true", "false", "vigente"))

    def test_boton_electorales_regenerar_y_ensayo(self):
        r, o = self.ejecutar(TIPO="P12 electorales", TERRITORIOS="aut11", ELECCION="ensayo 2026-11-29", REGENERAR="true")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((o["tipo"], o["edicion"], o["reutilizar"], o["eleccion"]), ("electorales", "2025", "false", "ensayo 2026-11-29"))

    def test_llamada_de_la_00(self):
        r, o = self.ejecutar(TIPO="territoriales", TERRITORIO_LLAMADA="aut11", DATA_EDITION="2025", REUTILIZAR_LLAMADA="false",
                             PERSISTIR_LLAMADA="true", HUECO_LLAMADA="false")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual((o["territorios"], o["edicion"], o["reutilizar"], o["eleccion"]), ('["aut11"]', "2025", "false", "vigente"))
        r, o = self.ejecutar(TIPO="electorales", TERRITORIO_LLAMADA="aut11", DATA_EDITION="2025", REUTILIZAR_LLAMADA="true",
                             PERSISTIR_LLAMADA="false", HUECO_LLAMADA="true", ELECCION="vigente")
        self.assertEqual((o["persistir"], o["hueco_fuente"]), ("false", "true"))

    def test_fallos_cerrados_con_error_a_stderr(self):
        casos = [
            dict(TIPO="otro", TERRITORIOS="aut01"),
            dict(TIPO="P11 territoriales", TERRITORIOS="aut01", ELECCION="ensayo 2026-11-29"),
            dict(TIPO="P12 electorales", TERRITORIOS="aut01", ELECCION="2030-01"),
            dict(TIPO="P11 territoriales", TERRITORIOS=" "),
            dict(TIPO="P11 territoriales", TERRITORIOS="Andalucía"),
            dict(TIPO="P11 territoriales", TERRITORIOS="aut01;rm"),
            dict(TIPO="electorales", TERRITORIO_LLAMADA="aut11", DATA_EDITION="", REUTILIZAR_LLAMADA="true", PERSISTIR_LLAMADA="true", HUECO_LLAMADA="false"),
            dict(TIPO="territoriales", TERRITORIO_LLAMADA="aut11", DATA_EDITION="2025", REUTILIZAR_LLAMADA="null", PERSISTIR_LLAMADA="true", HUECO_LLAMADA="false"),
        ]
        for c in casos:
            r, o = self.ejecutar(**c)
            self.assertNotEqual(r.returncode, 0, c)
            self.assertIn("::error::", r.stdout + r.stderr, c)
            self.assertNotIn("territorios", o, c)


class ControlesNegativos(unittest.TestCase):
    def test_se_detectan_cambios_de_permisos_comandos_concurrencia_y_salidas(self):
        a = viejo("preparacion-fuentes_1.4.14.yml")
        b = cargar(WF / "_p11-territoriales.yml")
        b = aplicar(b, "resolver", "resolve", P11_RESUELVE_NUEVO, P11_RESUELVE_VIEJO)
        self.assertEqual(diferencias(a, b), [])
        x = copy.deepcopy(b)
        x["permissions"] = {"contents": "read"}
        self.assertIn("permisos", diferencias(a, x))
        x = copy.deepcopy(b)
        paso(x["jobs"]["registrar"], "Registrar preparación territorial")["run"] += "\necho extra"
        self.assertIn("job registrar", diferencias(a, x))
        x = copy.deepcopy(b)
        x["jobs"]["registrar"]["concurrency"]["group"] = "otro"
        self.assertIn("job registrar", diferencias(a, x))
        x = copy.deepcopy(b)
        on(x)["workflow_call"]["outputs"]["territory_id"]["value"] = "x"
        self.assertIn("salidas", diferencias(a, x))
        x = copy.deepcopy(b)
        del x["jobs"]["resultado"]
        self.assertIn("conjunto de jobs", diferencias(a, x))

    def test_p12_y_huella_de_las_copias(self):
        a = viejo("preparacion-resultados-electorales_1.0.17.yml")
        b = cargar(WF / "_p12-electorales.yml")
        with self.assertRaises(AssertionError):
            aplicar(b, "electorales", "previous", "texto que no existe", "x")
        x = copy.deepcopy(aplicar(b, "electorales", "previous", P12_PREVIO_NUEVO, P12_PREVIO_VIEJO))
        paso(x["jobs"]["registrar"], "Registrar preparación electoral")["run"] = "true"
        self.assertIn("job registrar", diferencias(a, x))
        global SHAS
        original = dict(SHAS)
        try:
            SHAS["preparacion-fuentes_1.4.14.yml"] = "0" * 64
            with self.assertRaises(AssertionError):
                viejo("preparacion-fuentes_1.4.14.yml")
        finally:
            SHAS = original


class Herramientas(unittest.TestCase):
    def test_help_rc0(self):
        for n in ("clave_eleccion", "descargar_artefacto", "comprobar_paquete_electoral_remoto", "generar_provincias_congreso", "generar_provincias_congreso_350"):
            r = subprocess.run([sys.executable, "-m", f"herramientas.{n}", "--help"], capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(r.returncode, 0, (n, r.stderr[-300:]))

    def test_clave_eleccion_lanza_p10(self):
        sys.path.insert(0, str(ROOT))
        from herramientas import clave_eleccion as ce
        w, campo, fijo = ce.PHASES["electoral"]
        self.assertEqual((w, campo, fijo), ("p10-fuentes.yml", "territorios", {"tipo": "P12 electorales"}))
        unidades = ce.load_units(ROOT)
        p = ce.plan("ES-AUT-20260208", "electoral", unidades, inputs={"reutilizar_si_ya_preparada": "false"})
        self.assertTrue(p["count"] >= 1)
        d = p["dispatches"][0]
        self.assertEqual(d["workflow"], "p10-fuentes.yml")
        self.assertEqual(d["inputs"]["tipo"], "P12 electorales")
        self.assertEqual(d["inputs"]["territorios"], d["territory_id"])
        self.assertEqual(d["inputs"]["regenerar"], "true")
        self.assertNotIn("data_edition", d["inputs"])
        self.assertNotIn("reutilizar_si_ya_preparada", d["inputs"])
        self.assertTrue(re.fullmatch(r"(nac|aut)\d{2}(-350)?", d["inputs"]["territorios"]), d["inputs"]["territorios"])

    def test_los_generadores_ya_no_escriben_en_p10(self):
        for n in ("generar_provincias_congreso", "generar_provincias_congreso_350"):
            t = (ROOT / "herramientas" / f"{n}.py").read_text(encoding="utf-8")
            bloque = t[t.index("WORKFLOWS = ("):t.index(")", t.index("WORKFLOWS = ("))]
            self.assertNotIn("preparacion-fuentes.yml", bloque)
            self.assertNotIn("preparacion-resultados-electorales.yml", bloque)


if __name__ == "__main__":
    unittest.main()
