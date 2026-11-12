"""Ahorro de CI (T-149, D-49): robots solo con guardián, cancelación en main, nocturna; los cambios de código siguen con la batería completa."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "pruebas-plataforma.yml"
ZEROS = "0" * 40


def cargar():
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


def paso_cambios():
    return next(s for s in cargar()["jobs"]["cambios"]["steps"] if s.get("id") == "f")


class EstructuraAhorro(unittest.TestCase):
    def test_nocturna_sin_boton_manual_y_sin_cancelar(self):
        d = cargar()
        on = d.get("on") or d.get(True)
        self.assertEqual(on["schedule"], [{"cron": "23 2 * * *"}])
        self.assertNotIn("workflow_dispatch", on)
        self.assertIn("github.event_name != 'schedule'", str(d["concurrency"]["cancel-in-progress"]))
        self.assertIn("github.event_name }}", d["concurrency"]["group"])  # la nocturna no comparte grupo con el push del mismo SHA

    def test_cancelacion_solo_en_push_a_main(self):
        jobs = cargar()["jobs"]
        # Carrera: un push de ROBOT nunca cancela un run de push de CÓDIGO. `cambios` (que clasifica) no está en un grupo cancelable
        # y el resto solo entran en el grupo común de main si no es robot; si lo es, o fuera de push, un grupo único por run.
        self.assertNotIn("concurrency", jobs["cambios"])
        for job in ("guardian", "suite", "contratos", "productos", "pruebas"):
            with self.subTest(job=job):
                c = jobs[job]["concurrency"]
                self.assertTrue(c["cancel-in-progress"])
                self.assertIn("github.event_name == 'push' && needs.cambios.outputs.robot != 'true' && ", c["group"])
                self.assertIn("ddd-main-", c["group"])
                self.assertIn("github.run_id", c["group"])
                self.assertIn("cambios", jobs[job]["needs"] if isinstance(jobs[job]["needs"], list) else [jobs[job]["needs"]])
        # docs conserva su concurrencia propia por referencia: en main también cancela la superada
        self.assertEqual(jobs["docs"]["concurrency"], {"group": "docs-preview-${{ github.ref }}", "cancel-in-progress": True})
        for job in ("catalogo", "resultados", "numeracion"):
            self.assertFalse(jobs[job]["concurrency"]["cancel-in-progress"])  # los escritores jamás se cancelan
            self.assertIn("!cancelled()", jobs[job]["if"])
            self.assertNotIn("always()", jobs[job]["if"])

    def test_suite_solo_se_salta_con_robot_y_pruebas_lo_exige_si_no(self):
        d = cargar()
        self.assertEqual(d["jobs"]["suite"]["needs"], "cambios")
        self.assertEqual(d["jobs"]["suite"]["if"], "${{ needs.cambios.outputs.robot != 'true' }}")
        self.assertEqual(d["jobs"]["pruebas"]["needs"], ["guardian", "suite", "cambios", "contratos", "docs", "productos"])
        run = next(s for s in d["jobs"]["pruebas"]["steps"] if s["name"].startswith("Agregar"))["run"]
        self.assertIn('"$SUITE" == "skipped" && "$ROBOT" == "true"', run)
        subprocess.run(["bash", "-n"], input=run, text=True, check=True)
        self.assertEqual(d["jobs"]["guardian"]["needs"], "cambios")  # la integridad corre siempre, aunque falle `cambios`
        self.assertEqual(d["jobs"]["guardian"]["if"], "${{ !cancelled() }}")

    def test_estado_vivo_solo_en_push_de_robot_y_no_bloquea(self):
        jobs = cargar()["jobs"]
        j = jobs["estado_vivo"]
        self.assertEqual(j["name"], "Estado vivo")
        self.assertEqual(j["needs"], "cambios")
        self.assertIn("github.event_name == 'push' && needs.cambios.outputs.robot == 'true'", j["if"])
        self.assertTrue(j["continue-on-error"])
        self.assertEqual(j["concurrency"], {"group": "ddd-estado-vivo", "cancel-in-progress": True})
        self.assertNotIn("estado_vivo", jobs["pruebas"]["needs"])  # no entra en el check requerido
        for modulo in j["env"]["MODULOS"].split():
            with self.subTest(modulo=modulo):
                self.assertTrue((ROOT / (modulo.replace(".", "/") + ".py")).is_file())
        for paso in j["steps"]:
            if "run" in paso:
                subprocess.run(["bash", "-n"], input=paso["run"], text=True, check=True)

    def test_aviso_si_cae_la_nocturna(self):
        j = cargar()["jobs"]["aviso_nocturna"]
        self.assertIn("github.event_name == 'schedule'", j["if"])
        self.assertEqual(j["permissions"], {"issues": "write"})
        self.assertNotIn("aviso_nocturna", cargar()["jobs"]["pruebas"]["needs"])


class SinClavesDuplicadas(unittest.TestCase):
    def test_ningun_job_repite_claves(self):
        class Estricto(yaml.SafeLoader):
            pass

        def mapa(loader, nodo, profundo=False):
            claves = [loader.construct_object(k, deep=True) for k, _ in nodo.value]
            repetidas = {k for k in claves if claves.count(k) > 1}
            if repetidas:
                raise ValueError(f"claves duplicadas: {repetidas}")
            return loader.construct_mapping(nodo, deep=True)

        Estricto.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapa)
        yaml.load(WF.read_text(encoding="utf-8"), Loader=Estricto)


class ClasificacionRobot(unittest.TestCase):
    """Ejecuta el paso real de `cambios` en un repositorio temporal."""

    def clasificar(self, evento, actor, ficheros, base="HEAD~1", *, antes=(), borrar=(), renombrar=()):
        paso = paso_cambios()
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            run = lambda *a: subprocess.run(a, cwd=repo, check=True, capture_output=True, text=True)
            run("git", "init", "-q"); run("git", "config", "user.email", "a@b"); run("git", "config", "user.name", "a")
            (repo / "base.txt").write_text("0")
            for f in list(antes) + list(borrar) + [a for a, _ in renombrar]:
                p = repo / f; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("contenido " * 20)
            run("git", "add", "-A"); run("git", "commit", "-qm", "0")
            for f in borrar:
                run("git", "rm", "-q", f)
            for a, b in renombrar:
                (repo / b).parent.mkdir(parents=True, exist_ok=True); run("git", "mv", a, b)
            for f in ficheros:
                p = repo / f; p.parent.mkdir(parents=True, exist_ok=True); p.write_text("1")
            run("git", "add", "-A"); run("git", "commit", "-qm", "1", "--allow-empty")
            out = repo / "salida.txt"; out.write_text("")
            env = {**os.environ, **{k: str(v) for k, v in (paso.get("env") or {}).items() if "${{" not in str(v)},
                   "EVENTO": evento, "ACTOR": actor, "BASE": base, "GITHUB_SHA": "HEAD", "GITHUB_OUTPUT": str(out)}
            r = subprocess.run(["bash", "-c", paso["run"]], cwd=repo, env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return dict(l.split("=", 1) for l in out.read_text().splitlines() if "=" in l)

    def test_robot_con_rutas_de_datos_o_registro_solo_guardian(self):
        for ficheros in (["orchestracion/archivo_r2.json"], ["docs/registro/x.md", "docs/REGISTRO_DE_CAMBIOS.md", "legacy/docs/a.md"],
                         ["datos/resultados/a.json"], ["territorios/murcia/evidencia/ejecuciones_completas/1.json"]):
            with self.subTest(ficheros=ficheros):
                self.assertEqual(self.clasificar("push", "ddd-registro[bot]", ficheros)["robot"], "true")

    def test_todo_lo_demas_sigue_con_la_bateria_completa(self):
        casos = {
            "robot con código": ("push", "ddd-registro[bot]", ["modulos/05_optimizar_distritos.py"]),
            "robot con datos y código": ("push", "ddd-registro[bot]", ["orchestracion/a.json", "ddd_core/x.py"]),
            "robot con workflow": ("push", "ddd-registro[bot]", [".github/workflows/pruebas-plataforma.yml"]),
            "persona con datos": ("push", "jfmurciego", ["orchestracion/archivo_r2.json"]),
            "persona con código": ("push", "jfmurciego", ["herramientas/a.py"]),
            "PR de un bot con datos": ("pull_request", "ddd-registro[bot]", ["orchestracion/a.json"]),
            "nocturna": ("schedule", "github-actions[bot]", ["orchestracion/a.json"]),
        }
        for nombre, (evento, actor, ficheros) in casos.items():
            with self.subTest(caso=nombre):
                self.assertEqual(self.clasificar(evento, actor, ficheros)["robot"], "false")

    def test_renombrado_y_borrado_de_codigo_por_un_robot_siguen_con_suite(self):
        r = self.clasificar("push", "ddd-registro[bot]", [], renombrar=[("ddd_core/x.py", "datos/x.json")])
        self.assertEqual(r["robot"], "false")  # sin --no-renames solo se vería datos/x.json
        r = self.clasificar("push", "ddd-registro[bot]", ["orchestracion/a.json"], borrar=["modulos/m.py"])
        self.assertEqual(r["robot"], "false")

    def test_ficheros_de_codigo_dentro_de_rutas_de_datos_son_suite_completa(self):
        for f in ("datos/x.py", "orchestracion/a.js", "orchestracion/campanas/c.yaml", "publicado/dashboard/index.html",
                  "legacy/docs/a.py", "docs/registro/x.sh", "configuracion/catalogo_preparacion.yaml", "territorios/x/evidencia/run.py"):
            with self.subTest(fichero=f):
                self.assertEqual(self.clasificar("push", "ddd-registro[bot]", [f])["robot"], "false")

    def test_carrera_el_robot_posterior_no_hereda_el_diff_del_codigo_anterior(self):
        # Push de robot B tras el push de código A: su BASE es el tip de A, su diff solo datos -> robot=true (solo guardián),
        # pero el run de A no se cancela porque B no entra en el grupo cancelable (ver test_cancelacion_solo_en_push_a_main).
        self.assertEqual(self.clasificar("push", "ddd-registro[bot]", ["orchestracion/a.json"])["robot"], "true")

    def test_sin_base_comparable_suite_completa_y_escritores_todos(self):
        r = self.clasificar("push", "ddd-registro[bot]", ["orchestracion/a.json"], base=ZEROS)
        self.assertEqual(r["robot"], "false")
        for escritor in ("catalogo", "resultados", "numeracion"):
            self.assertEqual(r[escritor], "true")  # lógica de escribe() con EVENTO=push y files=todo

    def test_escritores_solo_en_push_con_sus_rutas(self):
        r = self.clasificar("push", "jfmurciego", ["docs/registro/a.md"])
        self.assertEqual((r["numeracion"], r["catalogo"], r["resultados"]), ("true", "false", "false"))
        r = self.clasificar("pull_request", "jfmurciego", ["docs/registro/a.md"])
        self.assertEqual((r["numeracion"], r["catalogo"], r["resultados"]), ("false", "false", "false"))


if __name__ == "__main__":
    unittest.main()
