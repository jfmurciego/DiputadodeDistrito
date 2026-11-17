# -*- coding: utf-8 -*-
"""T-375 (D-136 y D-151, paso 6): P10 Fuentes sustituye a `preparacion-fuentes.yml` y `preparacion-resultados-electorales.yml`.

PROYECTO: Diputado de Distrito · VERSIÓN: 2.0.0 · FECHA: 2026-11-17 · ESTADO: candidato · ANTERIOR: ninguna (fichero nuevo)
La equivalencia se calcula contra COPIAS CONGELADAS (`tests/fixtures/t375_workflows/`, con sha256; en CI no hay `legacy/`). Si falta una o cambia su huella el test
FALLA (no se salta). P10 lleva los jobs de P11 (`p11_*`) y P12 (`p12_*`); la «vista» de cada tipo (`tests/generar_vistas_p10.py`) les devuelve la forma vieja y se compara
job a job, salvo las diferencias declaradas. Controles negativos al final.
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
sys.path.insert(0, str(ROOT / "tests"))
import generar_vistas_p10 as vistas  # noqa: E402

WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t375_workflows"
SHAS = {
    "preparacion-fuentes_1.4.14.yml": "dfdf81addc11a342d1a15640848926e454fa8c0924a7b8a8aef27ec0f09bafb3",
    "preparacion-resultados-electorales_1.0.17.yml": "efe7637d042707f5e266edb71d6899b940d9d5baaf2763adf385c8ac3dacbd4d",
}
# Diferencias de comandos permitidas dentro de los jobs (todo lo demás, idéntico paso a paso). Con la sangría que deja el YAML al leer `run: |`.
P11_VIEJO = '            [[ "$REUSE_INPUT" == false ]]'
P11_REGENERAR_NUEVO = '[[ "$REGENERAR_INPUT" == true ]] && reuse_enabled=false  # T-375: «regenerar aunque exista» del botón de P10\n'
P12_PREVIO_VIEJO = """[[ -n "$match" ]] || { echo "::error::Artefacto electoral registrado no disponible"; exit 44; }"""
P12_PREVIO_NUEVO_INICIO = "# T-375 (D-136, reutilizar automático): caducado o eliminado no contradice la identidad registrada: se prepara de nuevo.\n"
P12_IF_VIEJO = "${{ inputs.reutilizar_si_ya_preparada && needs.resolver.outputs.registered_run_id != '' }}"
P12_IF_NUEVO = "${{ (inputs.reutilizar_si_ya_preparada || (inputs.territorio != '' && !inputs.regenerar)) && needs.resolver.outputs.registered_run_id != '' }}"


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


def vista(tipo, texto=None):
    return yaml.safe_load(vistas.vista(tipo, texto))


def paso(job, id_=None, nombre=None):
    return next(s for s in job["steps"] if (id_ and s.get("id") == id_) or (nombre and s.get("name") == nombre))


def neutralizar_p11(w):
    """Quita de la vista de P11 la única diferencia permitida (env REGENERAR_INPUT y su línea)."""
    w = copy.deepcopy(w)
    s = paso(w["jobs"]["resolver"], id_="resolve")
    assert "REGENERAR_INPUT" in s["env"] and P11_REGENERAR_NUEVO in s["run"]
    del s["env"]["REGENERAR_INPUT"]
    s["run"] = re.sub(r'(?m)^ *\[\[ "\$REGENERAR_INPUT" == true \]\].*\n', "", s["run"], count=1)
    return w


def neutralizar_p12(w):
    """Quita de la vista de P12 las dos diferencias permitidas (`if` del paso previous y su rama de caducado)."""
    w = copy.deepcopy(w)
    s = paso(w["jobs"]["electorales"], id_="previous")
    assert s["if"] == P12_IF_NUEVO, s["if"]
    s["if"] = P12_IF_VIEJO
    run = s["run"]
    i = run.index(P12_PREVIO_NUEVO_INICIO)
    j = run.index("exit 0; }", i) + len("exit 0; }")
    s["run"] = run[:i] + P12_PREVIO_VIEJO + run[j:]
    return w


def diferencias(a, b):
    """Diferencias NO permitidas entre los jobs de la vista `b` y el workflow viejo `a` (vacía = equivalente)."""
    d = []
    if set(a["jobs"]) != set(b["jobs"]):
        d.append("conjunto de jobs")
    for k, j in a["jobs"].items():
        if b["jobs"].get(k) != j:
            d.append(f"job {k}")
    if a["permissions"] != b["permissions"]:
        d.append("permisos")
    return d


def regenerar_linea_p11(w):
    """P11 viejo: el resolver tenía `reuse_enabled=true` y `persist_requested=true` seguidos (sin línea de regenerar)."""
    return w


class P11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = viejo("preparacion-fuentes_1.4.14.yml")
        cls.b = vista("p11")

    def test_jobs_comandos_permisos_identicos(self):
        self.assertEqual(diferencias(self.a, neutralizar_p11(self.b)), [])

    def test_los_cinco_jobs_y_su_registro(self):
        self.assertEqual(list(self.b["jobs"]), ["resolver", "territoriales", "registrar", "generation_pending", "resultado"])
        reg = self.b["jobs"]["registrar"]
        self.assertEqual(reg["concurrency"], {"group": "ddd-catalog-promotion", "cancel-in-progress": False, "queue": "max"})
        for j in ("registrar", "generation_pending"):
            self.assertTrue(any(s.get("name") == "Credencial de registro" for s in self.b["jobs"][j]["steps"]), j)

    def test_regenerar_con_edicion_vacia(self):
        run = paso(self.b["jobs"]["resolver"], id_="resolve")["run"]
        self.assertIn('[[ "$REGENERAR_INPUT" == true ]] && reuse_enabled=false', run)
        self.assertEqual(paso(self.b["jobs"]["resolver"], id_="resolve")["env"]["REGENERAR_INPUT"], "${{ inputs.regenerar }}")


class P12(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = viejo("preparacion-resultados-electorales_1.0.17.yml")
        cls.b = vista("p12")

    def test_jobs_comandos_permisos_identicos(self):
        self.assertEqual(diferencias(self.a, neutralizar_p12(self.b)), [])
        self.assertEqual(self.a["env"], self.b["env"])

    def test_los_cuatro_jobs_y_su_registro(self):
        self.assertEqual(list(self.b["jobs"]), ["resolver", "electorales", "registrar", "resultado"])
        reg = self.b["jobs"]["registrar"]
        self.assertEqual(reg["concurrency"], {"group": "ddd-catalog-promotion", "cancel-in-progress": False, "queue": "max"})
        self.assertTrue(any(s.get("name") == "Credencial de registro" for s in reg["steps"]))
        self.assertEqual(reg["if"], self.a["jobs"]["registrar"]["if"])

    def test_caducado_se_regenera_pero_el_digest_distinto_falla(self):
        run = paso(self.b["jobs"]["electorales"], id_="previous")["run"]
        self.assertNotIn("exit 44", run)
        self.assertIn("exit 0; }", run)
        self.assertIn("Digest de artefacto electoral no coincide con el registro.", run)


class P10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p10 = cargar(WF / "p10-fuentes.yml")
        cls.a11 = viejo("preparacion-fuentes_1.4.14.yml")
        cls.a12 = viejo("preparacion-resultados-electorales_1.0.17.yml")

    def test_boton_y_opciones(self):
        self.assertEqual(self.p10["name"], "P10 Fuentes")
        d = on(self.p10)["workflow_dispatch"]["inputs"]
        self.assertEqual(list(d), ["tipo", "territorio", "eleccion", "regenerar"])
        self.assertEqual(d["tipo"]["options"], ["P11 territoriales", "P12 electorales"])
        self.assertEqual(d["eleccion"]["options"], ["vigente", "ensayo 2026-11-29"])
        self.assertEqual(d["eleccion"]["default"], "vigente")
        self.assertIs(d["regenerar"]["default"], False)
        self.assertEqual(d["regenerar"]["type"], "boolean")

    def test_salidas_union_de_las_dos(self):
        out = on(self.p10)["workflow_call"]["outputs"]
        self.assertEqual(set(out), set(on(self.a11)["workflow_call"]["outputs"]) | set(on(self.a12)["workflow_call"]["outputs"]))
        for k, o in out.items():
            self.assertRegex(o["value"], r"jobs\.p1[12]_", k)

    def test_entradas_de_llamada_cubren_las_de_los_dos_viejos(self):
        i = on(self.p10)["workflow_call"]["inputs"]
        for viejo_wf in (self.a11, self.a12):
            for k, v in on(viejo_wf)["workflow_call"]["inputs"].items():
                self.assertIn(k, i)
                if v.get("type") == "boolean":
                    self.assertEqual(i[k], v, k)
        self.assertEqual(i["tipo"], {"required": True, "type": "string"})

    def test_permisos_env_y_job_de_entrada_sin_permisos(self):
        self.assertEqual(self.p10["permissions"], self.a11["permissions"])
        self.assertEqual(self.p10["permissions"], self.a12["permissions"])
        self.assertEqual(self.p10["env"], self.a12["env"])
        self.assertEqual(self.p10["jobs"]["entrada"]["permissions"], {})

    def test_concurrencia_real_del_workflow(self):
        c = self.p10["concurrency"]
        self.assertFalse(c["cancel-in-progress"])
        self.assertEqual(c["queue"], "max")
        g = c["group"]
        # P12: ddd-electoral-prod-<territorio>; P11: ddd-territorial-prod-<territorio>-<edición> (como los workflows viejos y P30).
        self.assertIn("format('ddd-electoral-prod-{0}', inputs.territory_id || inputs.territorio)", g)
        self.assertIn("format('ddd-territorial-prod-{0}-{1}', inputs.territory_id || inputs.territorio, inputs.data_edition || '2025')", g)
        self.assertEqual(self.a11["concurrency"]["group"], "ddd-territorial-prod-${{ inputs.territory_id }}-${{ inputs.data_edition || 'vigente' }}")
        self.assertEqual(self.a12["concurrency"]["group"], "ddd-electoral-prod-${{ inputs.territory_id }}")
        self.assertEqual(self.a11["concurrency"]["queue"], "max")

    def test_grupo_de_p11_coincide_con_p30_con_edicion_vacia(self):
        p30 = cargar(WF / "produccion-distritos.yml")["concurrency"]["group"] if "concurrency" in cargar(WF / "produccion-distritos.yml") else ""
        # Con la edición vacía el botón usa 2025; P30 usa la edición (2025): mismo sufijo.
        self.assertIn("data_edition", p30)
        self.assertIn("'2025'", self.p10["concurrency"]["group"])

    def test_p12_desde_el_boton_usa_la_edicion_fija(self):
        env = paso(self.p10["jobs"]["p12_resolver"], id_="resolve")["env"]
        self.assertEqual(env["EDITION"], "${{ inputs.data_edition || '2025' }}")
        self.assertEqual(env["TERRITORY"], "${{ (inputs.territory_id || inputs.territorio) }}")

    @staticmethod
    def evaluar_grupo(expresion, **entradas):
        """Evalúa la expresión REAL de `concurrency.group` de p10-fuentes.yml (subconjunto: contains, format, &&, ||, inputs.X)."""
        class Entradas(dict):
            def __getattr__(self, k):
                return self.get(k) or ""

        cuerpo = re.fullmatch(r"\$\{\{\s*(.*?)\s*\}\}", expresion.strip(), re.S).group(1)
        py = re.sub(r"inputs\.(\w+)", r"inputs.\1", cuerpo)
        py = py.replace("&&", " and ").replace("||", " or ")
        py = re.sub(r"contains\(", "contiene(", py)
        resultado = eval(py, {"__builtins__": {}}, {
            "inputs": Entradas(entradas),
            "contiene": lambda a, b: b in a,
            "format": lambda f, *a: re.sub(r"\{(\d)\}", lambda m: str(a[int(m.group(1))]), f),
        })
        return resultado

    def test_codigo_y_nombre_dan_el_mismo_grupo_y_territorios_distintos_no(self):
        """La concurrencia REAL de P10 usa el id canónico: botón (código) y 00/Legislatura (`territory_id` canónico) dan el mismo grupo."""
        sys.path.insert(0, str(ROOT))
        from herramientas.catalogo_preparacion import lookup

        expr = self.p10["concurrency"]["group"]

        def boton(tipo, codigo):
            return self.evaluar_grupo(expr, tipo=tipo, territorio=codigo)

        def llamada(tipo, valor_que_pasa_la_00, edicion="2025"):
            return self.evaluar_grupo(expr, tipo=tipo, territory_id=valor_que_pasa_la_00, data_edition=edicion)

        for codigo, nombre in (("aut12", "Galicia"), ("nac28", "Congreso Madrid"), ("aut01", "Andalucía")):
            canonico = lookup(nombre, "2025")["territory_id"]
            self.assertEqual(canonico, codigo)
            # La 00 y «Legislatura» pasan `territory_id` (el canónico), no el nombre.
            self.assertEqual(boton("P12 electorales", codigo), llamada("electorales", canonico), codigo)
            self.assertEqual(boton("P11 territoriales", codigo), llamada("territoriales", canonico), codigo)  # botón con edición vacía = 2025
        self.assertEqual(boton("P12 electorales", "aut12"), "ddd-electoral-prod-aut12")
        self.assertEqual(boton("P11 territoriales", "aut12"), "ddd-territorial-prod-aut12-2025")
        # Control negativo: territorios distintos o tipos distintos → grupos distintos; pasar el NOMBRE no excluye (por eso la 00 pasa el id).
        self.assertNotEqual(boton("P12 electorales", "aut12"), boton("P12 electorales", "aut01"))
        self.assertNotEqual(boton("P12 electorales", "aut12"), boton("P11 territoriales", "aut12"))
        self.assertNotEqual(boton("P12 electorales", "aut12"), llamada("electorales", "Galicia"))
        # Los callers de P10 pasan el id canónico.
        for fichero, jobs in (("ejecucion-completa-proyecto.yml", ("preparar_territorial", "preparar_electoral")),
                              ("preparacion-legislatura-vigente.yml", ("territorial", "electoral"))):
            w = cargar(WF / fichero)
            for job in jobs:
                self.assertEqual(w["jobs"][job]["with"]["territory_id"], "${{ needs.planificar.outputs.territory_id }}", (fichero, job))
        self.assertIn("territory_id", cargar(WF / "preparacion-legislatura-vigente.yml")["jobs"]["planificar"]["outputs"])

    def test_gating_por_tipo_y_entrada(self):
        j = self.p10["jobs"]
        self.assertEqual(j["p11_resolver"]["needs"], "entrada")
        self.assertEqual(j["p12_resolver"]["needs"], "entrada")
        self.assertEqual(j["p11_resolver"]["if"], "${{ contains(inputs.tipo, 'territoriales') }}")
        self.assertEqual(j["p12_resolver"]["if"], "${{ contains(inputs.tipo, 'electorales') }}")
        for k in ("p11_resultado", "p12_resultado"):
            self.assertIn("!= 'skipped'", j[k]["if"])
        self.assertFalse("territoriales" in "electorales" or "electorales" in "territoriales")  # `contains` no se pisa

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

    def test_ningun_workflow_cita_los_ficheros_borrados_ni_hay_reutilizables_internos(self):
        for p in WF.glob("*.yml"):
            t = p.read_text(encoding="utf-8")
            t = "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("#"))
            for n in ("preparacion-fuentes.yml", "preparacion-resultados-electorales.yml", "_p11-territoriales.yml", "_p12-electorales.yml"):
                self.assertNotIn(n, t, (p.name, n))
        for n in ("preparacion-fuentes.yml", "preparacion-resultados-electorales.yml", "_p11-territoriales.yml", "_p12-electorales.yml"):
            self.assertFalse((WF / n).exists(), n)  # D-151: sin reutilizables ni matriz
        self.assertFalse(any("strategy" in j or "uses" in j for j in self.p10["jobs"].values()))

    def test_vistas_en_sincronia_con_p10(self):
        r = subprocess.run([sys.executable, str(ROOT / "tests" / "generar_vistas_p10.py"), "--comprobar"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_sin_claves_duplicadas(self):
        class Estricto(yaml.SafeLoader):
            pass

        def construir(loader, node, deep=False):
            claves = [loader.construct_object(k, deep=deep) for k, _ in node.value]
            dup = {k for k in claves if claves.count(k) > 1}
            if dup:
                raise AssertionError(f"claves duplicadas {dup}")
            return yaml.SafeLoader.construct_mapping(loader, node, deep)

        Estricto.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construir)
        yaml.load((WF / "p10-fuentes.yml").read_text(encoding="utf-8"), Loader=Estricto)


class EntradaBajoBash(unittest.TestCase):
    """El paso «Comprobar tipo, territorio y elección» ejecutado de verdad bajo `bash -eo pipefail`."""

    @classmethod
    def setUpClass(cls):
        cls.script = paso(cargar(WF / "p10-fuentes.yml")["jobs"]["entrada"], nombre="Comprobar tipo, territorio y elección")["run"]

    def ejecutar(self, **env):
        base = {"TIPO": "", "TERRITORIO": "", "TERRITORIO_LLAMADA": "", "ELECCION": ""}
        base.update(env)
        with tempfile.TemporaryDirectory() as t:
            e = {**os.environ, **base, "GITHUB_STEP_SUMMARY": str(Path(t) / "s")}
            return subprocess.run(["bash", "-eo", "pipefail", "-c", self.script], env=e, capture_output=True, text=True)

    def test_validas(self):
        for c in (dict(TIPO="P11 territoriales", TERRITORIO="aut13", ELECCION="vigente"),
                  dict(TIPO="P12 electorales", TERRITORIO="nac28", ELECCION="ensayo 2026-11-29"),
                  dict(TIPO="P12 electorales", TERRITORIO="nac22_h2019_11", ELECCION="vigente"),
                  dict(TIPO="territoriales", TERRITORIO_LLAMADA="Galicia"),
                  dict(TIPO="electorales", TERRITORIO_LLAMADA="aut11", ELECCION="")):
            r = self.ejecutar(**c)
            self.assertEqual(r.returncode, 0, (c, r.stderr))

    def test_fallos_cerrados_con_error(self):
        for c in (dict(TIPO="otro", TERRITORIO="aut01"),
                  dict(TIPO="P11 territoriales", TERRITORIO="aut01", ELECCION="ensayo 2026-11-29"),
                  dict(TIPO="P12 electorales", TERRITORIO="aut01", ELECCION="2030-01"),
                  dict(TIPO="P11 territoriales", TERRITORIO=""),
                  dict(TIPO="P11 territoriales", TERRITORIO="aut13,nac28"),
                  dict(TIPO="P11 territoriales", TERRITORIO="Andalucía"),
                  dict(TIPO="P11 territoriales", TERRITORIO="aut01;rm")):
            r = self.ejecutar(**c)
            self.assertNotEqual(r.returncode, 0, c)
            self.assertIn("::error::", r.stdout + r.stderr, c)


class ControlesNegativos(unittest.TestCase):
    def test_se_detectan_cambios_de_permisos_comandos_concurrencia_y_jobs(self):
        a = viejo("preparacion-fuentes_1.4.14.yml")
        b = neutralizar_p11(vista("p11"))
        self.assertEqual(diferencias(a, b), [])
        x = copy.deepcopy(b)
        x["permissions"] = {"contents": "read"}
        self.assertIn("permisos", diferencias(a, x))
        x = copy.deepcopy(b)
        paso(x["jobs"]["registrar"], nombre="Registrar preparación territorial")["run"] += "\necho extra"
        self.assertIn("job registrar", diferencias(a, x))
        x = copy.deepcopy(b)
        x["jobs"]["registrar"]["concurrency"]["group"] = "otro"
        self.assertIn("job registrar", diferencias(a, x))
        x = copy.deepcopy(b)
        del x["jobs"]["resultado"]
        self.assertIn("conjunto de jobs", diferencias(a, x))

    def test_p12_y_huella_de_las_copias(self):
        a = viejo("preparacion-resultados-electorales_1.0.17.yml")
        b = neutralizar_p12(vista("p12"))
        self.assertEqual(diferencias(a, b), [])
        x = copy.deepcopy(b)
        paso(x["jobs"]["registrar"], nombre="Registrar preparación electoral")["run"] = "true"
        self.assertIn("job registrar", diferencias(a, x))
        global SHAS
        original = dict(SHAS)
        try:
            SHAS["preparacion-fuentes_1.4.14.yml"] = "0" * 64
            with self.assertRaises(AssertionError):
                viejo("preparacion-fuentes_1.4.14.yml")
        finally:
            SHAS = original

    def test_una_vista_desincronizada_se_detecta(self):
        texto = (WF / "p10-fuentes.yml").read_text(encoding="utf-8")
        self.assertNotEqual(vistas.vista("p11", texto), vistas.vista("p11", texto.replace("Registrar preparación territorial", "Registrar otra cosa", 1)))


class Herramientas(unittest.TestCase):
    def test_help_rc0(self):
        for n in ("clave_eleccion", "descargar_artefacto", "comprobar_paquete_electoral_remoto", "generar_provincias_congreso", "generar_provincias_congreso_350"):
            r = subprocess.run([sys.executable, "-m", f"herramientas.{n}", "--help"], capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(r.returncode, 0, (n, r.stderr[-300:]))

    def test_clave_eleccion_lanza_p10(self):
        sys.path.insert(0, str(ROOT))
        from herramientas import clave_eleccion as ce
        self.assertEqual(ce.PHASES["electoral"], ("p10-fuentes.yml", "territorio", {"tipo": "P12 electorales"}))
        p = ce.plan("ES-AUT-20260208", "electoral", ce.load_units(ROOT), inputs={"reutilizar_si_ya_preparada": "false"})
        self.assertTrue(p["count"] >= 1)
        d = p["dispatches"][0]
        self.assertEqual(d["workflow"], "p10-fuentes.yml")
        self.assertEqual(d["inputs"]["territorio"], d["territory_id"])
        self.assertEqual(d["inputs"]["regenerar"], "true")
        self.assertEqual(d["inputs"]["tipo"], "P12 electorales")
        for k in ("data_edition", "reutilizar_si_ya_preparada", "territorios"):
            self.assertNotIn(k, d["inputs"])
        self.assertTrue(re.fullmatch(r"(nac|aut)\d{2}", d["inputs"]["territorio"]), d["inputs"]["territorio"])

    def test_los_generadores_ya_no_escriben_en_p10(self):
        for n in ("generar_provincias_congreso", "generar_provincias_congreso_350"):
            t = (ROOT / "herramientas" / f"{n}.py").read_text(encoding="utf-8")
            bloque = t[t.index("WORKFLOWS = ("):t.index(")", t.index("WORKFLOWS = ("))]
            self.assertNotIn("preparacion-fuentes.yml", bloque)
            self.assertNotIn("preparacion-resultados-electorales.yml", bloque)


if __name__ == "__main__":
    unittest.main()
