"""T-366 (D-129/D-130): P90 Automático sustituye a «Pruebas de la Plataforma», «Forense de la 00» y el job `metricas` de
«Mantenimiento» sin perder disparadores, jobs, condiciones ni permisos.

La equivalencia antes → después se calcula contra COPIAS CONGELADAS de las versiones sustituidas, en `tests/fixtures/t366_workflows/`
(con su sha256; la imagen de CI las trae, no dependen de `legacy/`). Si falta un fichero o cambia su huella el test FALLA (no se salta).
Cada comparación lleva un control negativo: cambiar un permiso, un `if`, un paso o una concurrencia hace fallar la comparación.

No entran en P90 (decisión pendiente del propietario, ver la cabecera del workflow): `revisor-pr.yml` y `auto-merge.yml`, que siguen
aparte, y `archivar_r2`/`extraer_m06`, que pasaron a `p70-archivo.yml` (T-368).
"""
import copy
import hashlib
import re
import unittest
from pathlib import Path

import yaml

from tests._uses_sin_version import cargar as cargar_sin_version

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FIX = ROOT / "tests" / "fixtures" / "t366_workflows"
HUELLAS = {  # sha256 de las versiones sustituidas (las mismas que `legacy/workflows/*_20261116.yml`)
    "pruebas": ("pruebas-plataforma_1.10.4.yml", "cc97d5093f8c832eb2dd70af41643e4a69530a4849722aef750555bfe6391bc9"),
    "forense": ("forense-00_1.0.2.yml", "86b6a3608b6b4edca1db46e9fbae1fc904f4a20c3fc38715a7137a4fd18382d1"),
    "mant": ("mantenimiento-programado_1.0.3.yml", "0a93e324c4cc257c1bf4d8b6df6524b2d42a7d778d43a19f8938f107e55986ac"),
    "merge": ("auto-merge_1.2.1.yml", "4d78624f3c99d9b44d081e3199a3ca046ef6cc79132a98d4185d44f80b0588e3"),
}
# (workflow viejo, job viejo) -> job nuevo en P90
MAPA = {
    **{("pruebas", j): j for j in ("cambios", "guardian", "suite", "contratos", "docs", "productos", "pruebas", "catalogo",
                                   "resultados", "numeracion", "estado_vivo", "aviso_nocturna")},
    # forense viejo (comprobar/diagnosticar/issue): sustituido en P90 1.1.0 por la IA de cierre (T-379 PR 4, tests/test_t379_p90_ia_cierre.py)
    ("mant", "metricas"): "metricas",
}
# jobs de pruebas cuya concurrencia cambia a propósito: la cancelación por PR (antes de workflow) pasa al job
CONC_CAMBIA = {("pruebas", j) for j in ("guardian", "suite", "contratos", "productos", "pruebas", "cambios")}
# jobs cuyo `if` se amplía con el evento (se comprueba que el viejo sigue contenido en el nuevo)
IF_PROPIO = {("mant", "metricas"), ("pruebas", "aviso_nocturna")}


def cargar_texto(t):
    return cargar_sin_version(t)  # sin versión de acciones de terceros


def on(d):
    return d.get("on") or d.get(True)


def efectivos(d, job):
    return d["jobs"][job].get("permissions", d.get("permissions"))


def norm(s):
    return re.sub(r"\s+", " ", str(s)).replace("${{ ", "").replace(" }}", "").strip()


RENOMBRES = {"comprobar": "forense_comprobar"}  # colisión de ids con el revisor


def _ren(needs):
    if isinstance(needs, list):
        return [RENOMBRES.get(n, n) for n in needs]
    return RENOMBRES.get(needs, needs)


def diferencias(viejo, job_viejo, nuevo, job_nuevo, *, cambios=False, conc_cambia=False, if_propio=False):
    """Lista de diferencias NO permitidas entre un job viejo y el nuevo (vacía = equivalente)."""
    a, b = viejo["jobs"][job_viejo], nuevo["jobs"][job_nuevo]
    d = []
    if efectivos(viejo, job_viejo) != efectivos(nuevo, job_nuevo):
        d.append(f"permisos {efectivos(viejo, job_viejo)} != {efectivos(nuevo, job_nuevo)}")
    for clave in ("runs-on", "timeout-minutes", "continue-on-error", "strategy", "env", "outputs", "name"):
        if a.get(clave) != b.get(clave):
            d.append(f"{clave} difiere")
    if "steps" in a:
        pasos_nuevos = b["steps"]
        if cambios:  # `cambios` solo cambia la ruta que se dispara a sí misma
            pasos_nuevos = yaml.safe_load(yaml.safe_dump(pasos_nuevos).replace("p90-automatico", "pruebas-plataforma"))
        if a["steps"] != pasos_nuevos:
            d.append("pasos difieren")
    if "concurrency" in a and not conc_cambia and a["concurrency"] != b.get("concurrency"):
        d.append("concurrencia difiere")
    if "if" in a and not if_propio and norm(a["if"]) not in norm(b.get("if", "")):
        d.append("el `if` de antes no está en el de ahora")
    if "needs" in a and _ren(a["needs"]) != b.get("needs"):
        d.append("needs difiere")
    return d


class Fixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.viejos = {}
        for k, (nombre, sha) in HUELLAS.items():
            ruta = FIX / nombre
            assert ruta.is_file(), f"falta la copia congelada {ruta}"  # nunca se salta
            datos = ruta.read_bytes()
            assert hashlib.sha256(datos).hexdigest() == sha, f"{nombre}: la copia congelada cambió"
            cls.viejos[k] = cargar_texto(datos.decode("utf-8"))
        cls.p90 = cargar_texto((WF / "p90-automatico.yml").read_text(encoding="utf-8"))


class Disparadores(Fixtures):
    def test_nombre_sin_boton_manual_y_disparadores(self):
        self.assertEqual(self.p90["name"], "P90 Automático")
        d = on(self.p90)
        self.assertEqual(set(d), {"push", "pull_request", "schedule", "workflow_run"})
        self.assertNotIn("workflow_dispatch", d)
        self.assertEqual(d["push"], {"branches": ["main"]})
        # igual que pruebas-plataforma: `pull_request` sin types = opened/synchronize/reopened (labeled/ready_for_review crearían
        # un check-run `pruebas` skipped sobre el HEAD)
        self.assertEqual(on(self.viejos["pruebas"])["pull_request"], d["pull_request"])
        self.assertIsNone(d["pull_request"])
        self.assertEqual(d["schedule"], [{"cron": "23 2 * * *"}, {"cron": "17 5 * * 1"}])
        self.assertEqual(d["workflow_run"], {"workflows": ["P00 Campaña"], "types": ["completed"]})  # sin autorreferencia (inválida)
        self.assertEqual(on(self.viejos["forense"])["workflow_run"], d["workflow_run"])
        self.assertNotIn(self.p90["name"], d["workflow_run"]["workflows"])

    def test_ningun_job_de_revisor_ni_fusion_en_p90(self):
        for j in ("veredicto", "revisar", "revisor_comprobar", "fusionar"):
            self.assertNotIn(j, self.p90["jobs"])
        self.assertEqual(set(self.p90["jobs"]), set(MAPA.values()) | {"cierre_comprobar", "cierre_ia", "cierre_comentario"})

    def test_checks_intocables_conservan_nombre(self):
        jobs = self.p90["jobs"]
        for j in ("pruebas", "guardian", "suite"):
            self.assertIn(j, jobs)
            self.assertNotIn("name", jobs[j], j)
        self.assertEqual(jobs["suite"]["strategy"]["matrix"]["grupo"], [1, 2, 3, 4, 5])

    def test_cada_job_se_ata_a_su_evento(self):
        j = self.p90["jobs"]
        for nombre in ("cambios", "guardian", "pruebas"):
            cond = j[nombre]["if"]
            self.assertIn("github.event.schedule == '23 2 * * *'", cond, nombre)
            self.assertIn("github.event.action == 'synchronize'", cond, nombre)
            self.assertNotIn("labeled", cond, nombre)
        self.assertIn("github.event.schedule == '17 5 * * 1'", j["metricas"]["if"])
        self.assertIn("github.event_name == 'workflow_run' && github.event.workflow_run.name == 'P00 Campaña'", norm(j["cierre_comprobar"]["if"]))
        self.assertIn("github.event.workflow_run.conclusion == 'failure'", j["cierre_comprobar"]["if"])
        for nombre in ("catalogo", "resultados", "numeracion", "estado_vivo"):
            self.assertIn("github.event_name == 'push'", j[nombre]["if"], nombre)
        self.assertIn("github.event.schedule == '23 2 * * *'", j["aviso_nocturna"]["if"])  # no con las métricas del lunes

    def test_fusion_sigue_aparte_y_mantenimiento_ya_no_existe(self):
        self.assertFalse((WF / "mantenimiento-programado.yml").exists())  # T-368: lo recoge P70 Archivo (test_t368_p70_equivalencia)
        am = cargar_texto((WF / "auto-merge.yml").read_text(encoding="utf-8"))
        self.assertEqual(on(am), {"workflow_run": {"workflows": ["P90 Automático"], "types": ["completed"]}})
        f, v = am["jobs"]["fusionar"], self.viejos["merge"]["jobs"]["fusionar"]
        self.assertIn("github.event.workflow_run.path == '.github/workflows/p90-automatico.yml'", f["if"])
        self.assertEqual(am["permissions"], self.viejos["merge"]["permissions"])  # ningún job gana permisos
        self.assertEqual(f["steps"], v["steps"])  # el cuerpo de la fusión no cambia (ref: main, decidir_auto_merge.py, --match-head-commit)
        self.assertEqual(f["steps"][0]["with"]["ref"], "main")
        # concurrencia: sin cancelar y en cola (otro run del mismo SHA no cancela la fusión buena)
        self.assertEqual(am["concurrency"]["group"], self.viejos["merge"]["concurrency"]["group"])
        self.assertFalse(am["concurrency"]["cancel-in-progress"])
        self.assertEqual(am["concurrency"]["queue"], "max")
        self.assertNotIn(am["name"], on(am)["workflow_run"]["workflows"])


class Equivalencia(Fixtures):
    def test_job_a_job_sin_diferencias(self):
        for (w, j), nuevo in MAPA.items():
            with self.subTest(antes=f"{w}:{j}", ahora=nuevo):
                self.assertEqual([], diferencias(self.viejos[w], j, self.p90, nuevo, cambios=(w, j) == ("pruebas", "cambios"),
                                                 conc_cambia=(w, j) in CONC_CAMBIA, if_propio=(w, j) in IF_PROPIO))

    def test_ningun_job_gana_permisos_y_workflow_solo_lectura(self):
        self.assertEqual(self.p90["permissions"], {"contents": "read"})
        for (w, j), nuevo in MAPA.items():
            viejo = efectivos(self.viejos[w], j)
            self.assertEqual(viejo, efectivos(self.p90, nuevo), f"{w}:{j}")

    def test_concurrencia_de_pruebas_conserva_main_y_run_unico(self):
        for j in ("guardian", "suite", "contratos", "productos", "pruebas"):
            v = self.viejos["pruebas"]["jobs"][j]["concurrency"]
            c = self.p90["jobs"][j]["concurrency"]
            self.assertTrue(c["cancel-in-progress"] and v["cancel-in-progress"], j)
            for trozo in re.findall(r"'ddd-main-[^']*'|format\('ddd-main-[^)]*\)|format\('ddd-run-[^)]*\)", v["group"]):
                self.assertIn(trozo, c["group"], j)
            self.assertIn(f"format('ddd-pr-{{0}}-{j}", c["group"], j)  # antes: cancelación por PR a nivel de workflow
        self.assertNotIn("concurrency", self.p90)
        for nombre, job in self.p90["jobs"].items():
            c = job.get("concurrency")
            if c and c["cancel-in-progress"] is False:
                self.assertEqual(c.get("queue"), "max", nombre)
        a, b = self.viejos["forense"]["concurrency"], self.p90["jobs"]["cierre_ia"]["concurrency"]
        self.assertEqual((a["group"], a["cancel-in-progress"], a["queue"]), (b["group"], b["cancel-in-progress"], b["queue"]))

    def test_nocturna_cae_en_grupo_unico_por_run(self):
        for j in ("guardian", "suite", "contratos", "productos", "pruebas", "cambios"):
            self.assertIn("format('ddd-run-{0}-", self.p90["jobs"][j]["concurrency"]["group"], j)


class ControlesNegativos(Fixtures):
    """Si alguien cambia un permiso, un `if`, un paso o una concurrencia, la comparación debe detectarlo."""

    def mutar(self, job, f):
        nuevo = copy.deepcopy(self.p90)
        f(nuevo["jobs"][job])
        return nuevo

    def test_detecta_permiso_ganado(self):
        n = self.mutar("catalogo", lambda j: j.__setitem__("permissions", {"contents": "write", "actions": "write"}))
        self.assertTrue(diferencias(self.viejos["pruebas"], "catalogo", n, "catalogo"))
        n = self.mutar("catalogo", lambda j: j.__setitem__("permissions", {"contents": "read"}))
        self.assertTrue(diferencias(self.viejos["pruebas"], "catalogo", n, "catalogo"))

    def test_detecta_if_perdido(self):
        n = self.mutar("estado_vivo", lambda j: j.__setitem__("if", "${{ true }}"))
        self.assertTrue(diferencias(self.viejos["pruebas"], "estado_vivo", n, "estado_vivo"))

    def test_detecta_paso_cambiado_y_concurrencia(self):
        n = self.mutar("numeracion", lambda j: j["steps"][-1].__setitem__("run", "echo hola"))
        self.assertTrue(diferencias(self.viejos["pruebas"], "numeracion", n, "numeracion"))
        n = self.mutar("numeracion", lambda j: j["concurrency"].__setitem__("cancel-in-progress", True))
        self.assertTrue(diferencias(self.viejos["pruebas"], "numeracion", n, "numeracion"))

    def test_detecta_permiso_a_nivel_de_workflow(self):
        n = copy.deepcopy(self.p90)
        n["permissions"] = {"contents": "write"}
        self.assertTrue(diferencias(self.viejos["pruebas"], "guardian", n, "guardian", conc_cambia=True))

    def test_la_huella_de_las_copias_congeladas_es_obligatoria(self):
        self.assertEqual(len(HUELLAS), 4)
        for nombre, sha in HUELLAS.values():
            self.assertEqual(hashlib.sha256((FIX / nombre).read_bytes()).hexdigest(), sha)


if __name__ == "__main__":
    unittest.main()
