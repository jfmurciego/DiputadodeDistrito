"""T-366 (D-129/D-130): P90 Automático sustituye a cinco workflows sin perder disparadores, jobs, condiciones ni permisos.

Equivalencia antes → después, leyendo las copias de `legacy/workflows/` (declaradas en `.dockerignore`) y el workflow vivo.
Intocables: check `veredicto` y `pruebas`, revisor solo con `revisar-ia`, fusión solo con `pruebas` sobre el SHA exacto, forense
al terminar cada P00, ningún job gana permisos.
"""
import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
LEG = ROOT / "legacy" / "workflows"
FECHA = "20261116"
VIEJOS = {
    "pruebas": f"pruebas-plataforma_v1.10.4_{FECHA}.yml",
    "revisor": f"revisor-pr_v1.1.0_{FECHA}.yml",
    "merge": f"auto-merge_v1.2.1_{FECHA}.yml",
    "forense": f"forense-00_v1.0.2_{FECHA}.yml",
    "mant": f"mantenimiento-programado_v1.0.3_{FECHA}.yml",
}
# (workflow viejo, job viejo) -> job nuevo
MAPA = {
    **{("pruebas", j): j for j in ("cambios", "guardian", "suite", "contratos", "docs", "productos", "pruebas", "catalogo",
                                   "resultados", "numeracion", "estado_vivo", "aviso_nocturna")},
    ("revisor", "comprobar"): "revisor_comprobar", ("revisor", "revisar"): "revisar", ("revisor", "veredicto"): "veredicto",
    ("merge", "fusionar"): "fusionar",
    ("forense", "comprobar"): "forense_comprobar", ("forense", "diagnosticar"): "diagnosticar", ("forense", "issue"): "forense_issue",
    ("mant", "metricas"): "metricas",
}
FUERA = {("mant", "archivar_r2"), ("mant", "extraer_m06")}  # pasan a P70 en el paso 2: NO están en P90


def cargar(p):
    return yaml.safe_load(Path(p).read_text(encoding="utf-8"))


def on(d):
    return d.get("on") or d.get(True)


def efectivos(d, job):
    return d["jobs"][job].get("permissions", d.get("permissions"))


class P90(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p90 = cargar(WF / "p90-automatico.yml")
        cls.viejos = {k: cargar(LEG / v) for k, v in VIEJOS.items() if (LEG / v).is_file()}

    # ---- no necesitan las copias de legacy ----
    def test_los_cinco_ficheros_viejos_ya_no_estan_activos(self):
        for f in ("pruebas-plataforma", "revisor-pr", "auto-merge", "forense-00", "mantenimiento-programado"):
            self.assertFalse((WF / f"{f}.yml").exists(), f)

    def test_nombre_sin_boton_manual_y_disparadores(self):
        self.assertEqual(self.p90["name"], "P90 Automático")
        d = on(self.p90)
        self.assertEqual(set(d), {"push", "pull_request", "schedule", "workflow_run"})
        self.assertNotIn("workflow_dispatch", d)
        self.assertEqual(d["push"], {"branches": ["main"]})
        self.assertEqual(set(d["pull_request"]["types"]), {"opened", "synchronize", "reopened", "ready_for_review", "labeled"})
        self.assertEqual(d["schedule"], [{"cron": "23 2 * * *"}, {"cron": "17 5 * * 1"}])  # nocturna y métricas; sin el 05:17 diario de R2
        self.assertEqual(d["workflow_run"], {"workflows": ["P00 Campaña"], "types": ["completed"]})

    def test_checks_intocables_conservan_nombre(self):
        jobs = self.p90["jobs"]
        for j in ("pruebas", "veredicto", "guardian", "suite"):
            self.assertIn(j, jobs)
            self.assertNotIn("name", jobs[j], j)  # el check-run se llama como el id del job
        self.assertEqual(jobs["suite"]["strategy"]["matrix"]["grupo"], [1, 2, 3, 4, 5])

    def test_archivar_r2_y_extraer_m06_fuera_de_p90(self):
        jobs = self.p90["jobs"]
        self.assertNotIn("archivar_r2", jobs)
        self.assertNotIn("extraer_m06", jobs)
        self.assertNotIn("archivar_artefactos_r2.py", (WF / "p90-automatico.yml").read_text(encoding="utf-8"))

    def test_ids_de_job_unicos_y_sin_job_huerfano(self):
        esperados = set(MAPA.values()) | {"fusionar"}
        self.assertEqual(set(self.p90["jobs"]), esperados)

    def test_cada_job_se_ata_a_su_evento(self):
        j = self.p90["jobs"]
        # las puertas de pruebas no corren en labeled/ready_for_review ni en workflow_run ni en la cron de métricas
        for nombre in ("cambios", "guardian", "pruebas"):
            cond = j[nombre]["if"]
            self.assertIn("github.event.schedule == '23 2 * * *'", cond, nombre)
            self.assertIn("github.event.action == 'synchronize'", cond, nombre)
            self.assertNotIn("labeled", cond, nombre)
        self.assertIn("github.event.schedule == '17 5 * * 1'", j["metricas"]["if"])
        self.assertIn("github.event_name == 'workflow_run'", j["forense_comprobar"]["if"])
        self.assertIn("github.event_name == 'pull_request'", j["revisor_comprobar"]["if"])
        for nombre in ("catalogo", "resultados", "numeracion", "estado_vivo"):
            self.assertIn("github.event_name == 'push'", j[nombre]["if"], nombre)

    def test_veredicto_y_revisor_con_etiqueta(self):
        j = self.p90["jobs"]
        cond = " ".join(j["revisor_comprobar"]["if"].split())
        self.assertIn("contains(github.event.pull_request.labels.*.name, 'revisar-ia')", cond)
        self.assertEqual(j["revisar"]["needs"], "revisor_comprobar")
        self.assertEqual(j["veredicto"]["needs"], "revisar")  # sin etiqueta: revisar y veredicto «skipped» = cumplido
        self.assertNotIn("always()", j["veredicto"].get("if", ""))
        self.assertEqual(j["veredicto"]["permissions"], {"pull-requests": "write"})

    def test_forense_al_terminar_cada_p00_solo_si_falla(self):
        cond = self.p90["jobs"]["forense_comprobar"]["if"]
        self.assertIn("github.event.workflow_run.conclusion == 'failure'", cond)  # condición de hoy
        self.assertEqual(self.p90["jobs"]["diagnosticar"]["concurrency"],
                         {"group": "ddd-forense-${{ github.event.workflow_run.id }}", "cancel-in-progress": False, "queue": "max"})

    def test_fusion_solo_con_pruebas_en_verde_de_este_run(self):
        f = self.p90["jobs"]["fusionar"]
        self.assertEqual(f["needs"], "pruebas")
        self.assertIn("needs.pruebas.result == 'success'", f["if"])
        run = f["steps"][1]["run"]
        self.assertIn("decidir_auto_merge.py", run)
        self.assertIn('--match-head-commit "$SHA"', run)
        self.assertLess(run.index("decidir_auto_merge.py"), run.index("gh pr merge"))
        self.assertIn("--suite \"$SUITE\"", run)

    def test_ningun_job_declara_mas_permisos_que_hoy_y_workflow_solo_lectura(self):
        self.assertEqual(self.p90["permissions"], {"contents": "read"})
        for nombre, job in self.p90["jobs"].items():
            for permiso, valor in (job.get("permissions") or {}).items():
                self.assertIn(permiso, {"contents", "actions", "checks", "pull-requests", "issues"}, nombre)
                self.assertIn(valor, {"read", "write"}, nombre)

    def test_todo_grupo_no_cancelante_lleva_queue_max(self):
        for nombre, job in self.p90["jobs"].items():
            c = job.get("concurrency")
            if c and c["cancel-in-progress"] is False:
                self.assertEqual(c.get("queue"), "max", nombre)
        self.assertNotIn("concurrency", self.p90)  # cada job lleva la suya: workflow_run y schedule no deben cancelarse entre sí

    # ---- equivalencia contra las copias de legacy (solo si están en la imagen) ----
    def test_equivalencia_job_a_job(self):
        if len(self.viejos) != len(VIEJOS):
            self.skipTest("legacy/workflows ausente (imagen sin esas copias)")
        for (w, j), nuevo in MAPA.items():
            with self.subTest(antes=f"{w}:{j}", ahora=nuevo):
                a, b = self.viejos[w]["jobs"][j], self.p90["jobs"][nuevo]
                # permisos efectivos idénticos (ninguno gana)
                self.assertEqual(efectivos(self.viejos[w], j), efectivos(self.p90, nuevo))
                for clave in ("runs-on", "timeout-minutes", "continue-on-error", "strategy", "env", "outputs", "name"):
                    self.assertEqual(a.get(clave), b.get(clave), clave)
                if "steps" in a and (w, j) != ("merge", "fusionar"):
                    self.assertEqual(a["steps"], b["steps"] if (w, j) != ("pruebas", "cambios") else self._sin_propio(b["steps"], a["steps"]))
                # concurrencia propia del job: idéntica salvo los grupos de PR/push de pruebas (ver test siguiente)
                if "concurrency" in a and (w, j) not in {("pruebas", x) for x in ("guardian", "suite", "contratos", "productos", "pruebas")} | {("merge", "fusionar")}:
                    self.assertEqual(a["concurrency"], b["concurrency"])

    def test_concurrencia_de_workflow_movida_al_job_largo(self):
        if len(self.viejos) != len(VIEJOS):
            self.skipTest("legacy/workflows ausente")
        # revisor y forense tenían grupo de workflow (sin cancelar, queue: max): ahora en el job que dura (revisar / diagnosticar)
        for w, nuevo in (("revisor", "revisar"), ("forense", "diagnosticar")):
            a = self.viejos[w]["concurrency"]
            b = self.p90["jobs"][nuevo]["concurrency"]
            self.assertEqual((a["group"], a["cancel-in-progress"], a["queue"]), (b["group"], b["cancel-in-progress"], b["queue"]), w)
        # fusionar: mismo grupo por SHA y cancelación, con el SHA del HEAD de la PR en lugar de workflow_run.head_sha
        a, b = self.viejos["merge"]["concurrency"], self.p90["jobs"]["fusionar"]["concurrency"]
        self.assertEqual(a["group"].replace("github.event.workflow_run.head_sha", "github.event.pull_request.head.sha"), b["group"])
        self.assertEqual(a["cancel-in-progress"], b["cancel-in-progress"])
        # pruebas: la cancelación por PR (antes a nivel de workflow) pasa a cada job; push a main y nocturna igual que hoy
        for j in ("guardian", "suite", "contratos", "productos", "pruebas"):
            c, v = self.p90["jobs"][j]["concurrency"], self.viejos["pruebas"]["jobs"][j]["concurrency"]
            self.assertTrue(c["cancel-in-progress"] and v["cancel-in-progress"], j)
            for trozo in re.findall(r"'ddd-main-[^']*'|format\('ddd-main-[^)]*\)|format\('ddd-run-[^)]*\)", v["group"]):
                self.assertIn(trozo, c["group"], j)

    def _sin_propio(self, nuevo, viejo):
        # `cambios` solo cambia la ruta que se dispara a sí misma (pruebas-plataforma.yml → p90-automatico.yml)
        n = yaml.safe_dump(nuevo).replace("p90-automatico", "pruebas-plataforma")
        self.assertEqual(yaml.safe_load(n), viejo)
        return viejo

    def test_condiciones_conservadas_en_los_jobs_movidos(self):
        if len(self.viejos) != len(VIEJOS):
            self.skipTest("legacy/workflows ausente")
        # los jobs con `if` propio lo conservan como subcadena (el evento se AÑADE, no se quita nada)
        norm = lambda s: re.sub(r"\s+", " ", str(s)).replace("${{ ", "").replace(" }}", "").strip()
        for (w, j), nuevo in MAPA.items():
            a = self.viejos[w]["jobs"][j].get("if")
            b = self.p90["jobs"][nuevo].get("if")
            if a is None or (w, j) in {("revisor", "comprobar"), ("forense", "comprobar"), ("merge", "fusionar"),
                                       ("revisor", "revisar"), ("forense", "diagnosticar"), ("mant", "metricas"), ("pruebas", "aviso_nocturna")}:
                continue
            with self.subTest(job=nuevo):
                self.assertIn(norm(a), norm(b))

    def test_equivalencia_check_runs_exigidos(self):
        if len(self.viejos) != len(VIEJOS):
            self.skipTest("legacy/workflows ausente")
        self.assertEqual(self.viejos["pruebas"]["jobs"]["pruebas"]["needs"], self.p90["jobs"]["pruebas"]["needs"])
        self.assertEqual(self.viejos["revisor"]["jobs"]["veredicto"]["needs"], "revisar")


if __name__ == "__main__":
    unittest.main()
