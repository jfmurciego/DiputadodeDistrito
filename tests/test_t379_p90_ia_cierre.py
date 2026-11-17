"""T-379 PR 4 (D-143/D-147, diseño P00 §7): la IA de cierre de P90 sustituye al forense por cada 00.

Se abre solo si falla el job `resultado` de «P00 Campaña»; permisos mínimos; logs = entrada no confiable.
El disparo se prueba con un evento `workflow_run` sintético contra el `if` real del YAML y el script real del paso `c`
(con un `gh` falso que sirve la lista de jobs).
"""
import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
P90 = ROOT / ".github" / "workflows" / "p90-automatico.yml"


def cargar():
    return yaml.safe_load(P90.read_text(encoding="utf-8"))


def evalua_if(cond, ev):
    """Evalúa el subconjunto de expresiones del `if` (a && b, ==, !=, literales) contra un evento sintético."""
    cond = re.sub(r"\s+", " ", cond).strip()
    cond = re.sub(r"^\$\{\{|\}\}$", "", cond).strip()

    def val(m):
        ruta = m.group(1)
        if ruta == "github.event_name":
            return repr(ev["event_name"])
        return repr(ev["event"]["workflow_run"].get(ruta.split("github.event.workflow_run.")[1]))
    py = re.sub(r"(github\.[A-Za-z_.]+)", val, cond)
    py = py.replace("&&", " and ").replace("||", " or ")
    return bool(eval(py, {"__builtins__": {}}))  # solo el `if` de nuestro YAML


def evento(conclusion="failure", name="P00 Campaña", origen="workflow_dispatch"):
    return {"event_name": "workflow_run",
            "event": {"workflow_run": {"name": name, "conclusion": conclusion, "event": origen, "id": 4242}}}


class Disparo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = cargar()
        cls.j = cls.wf["jobs"]["cierre_comprobar"]

    def test_workflow_run_declarado_sin_autorreferencia(self):
        on = self.wf.get("on") or self.wf.get(True)
        self.assertEqual(on["workflow_run"], {"workflows": ["P00 Campaña"], "types": ["completed"]})
        self.assertNotIn(self.wf["name"], on["workflow_run"]["workflows"])

    def test_solo_abre_con_failure_de_p00_campana(self):
        c = self.j["if"]
        self.assertTrue(evalua_if(c, evento("failure")))
        for conc in ("success", "cancelled", "skipped", "timed_out"):
            self.assertFalse(evalua_if(c, evento(conc)), conc)
        self.assertFalse(evalua_if(c, evento(name="P90 Automático")))
        self.assertFalse(evalua_if(c, evento(name="Otro")))
        self.assertFalse(evalua_if(c, {"event_name": "push", "event": {"workflow_run": {}}}))

    def test_la_prueba_de_humo_de_pr_no_abre(self):
        self.assertFalse(evalua_if(self.j["if"], evento(origen="pull_request")))

    def _ejecuta_paso(self, jobs, token="x"):
        paso = next(s for s in self.j["steps"] if s.get("id") == "c")
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            gh = d / "gh"
            # `gh` falso: aplica a la lista de jobs el filtro `-q` que el paso real le pasa
            gh.write_text('#!/bin/bash\nwhile [[ $# -gt 0 ]]; do [[ "$1" == -q ]] && f="$2"; shift; done\njq -r "$f" "$FAKE_JOBS"\n')
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
            (d / "jobs.json").write_text(json.dumps({"jobs": jobs}))
            salida = d / "out"
            env = {"PATH": f"{d}:{os.environ['PATH']}", "FAKE_JOBS": str(d / "jobs.json"), "GITHUB_OUTPUT": str(salida),
                   "GITHUB_REPOSITORY": "o/r", "TOKEN": token, "GH_TOKEN": "t", "RUN_ID": "4242"}
            r = subprocess.run(["bash", "-c", paso["run"]], env=env, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return salida.read_text().strip()

    def test_resultado_en_rojo_abre(self):
        jobs = [{"id": 1, "name": "plan", "conclusion": "success"}, {"id": 2, "name": "resultado", "conclusion": "failure"}]
        self.assertEqual(self._ejecuta_paso(jobs), "listo=true")

    def test_resultado_en_verde_o_fallo_de_otro_job_no_abre(self):
        self.assertEqual(self._ejecuta_paso([{"id": 2, "name": "resultado", "conclusion": "success"}]), "listo=false")
        self.assertEqual(self._ejecuta_paso([{"id": 3, "name": "cierre", "conclusion": "failure"}]), "listo=false")
        self.assertEqual(self._ejecuta_paso([{"id": 2, "name": "resultado", "conclusion": "skipped"}]), "listo=false")

    def test_sin_secreto_no_abre(self):
        self.assertEqual(self._ejecuta_paso([{"id": 2, "name": "resultado", "conclusion": "failure"}], token=""), "listo=false")


class PermisosYEntradaNoConfiable(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = cargar()
        cls.jobs = cls.wf["jobs"]

    def test_permisos_exactos(self):
        self.assertEqual(self.wf["permissions"], {"contents": "read"})
        self.assertEqual(self.jobs["cierre_comprobar"]["permissions"], {"actions": "read"})
        self.assertEqual(self.jobs["cierre_ia"]["permissions"],
                         {"contents": "read", "actions": "read", "checks": "read", "issues": "read"})
        self.assertEqual(self.jobs["cierre_comentario"]["permissions"], {"issues": "write"})

    def test_solo_el_comentario_escribe_y_ninguna_escritura_mas(self):
        for nombre in ("cierre_comprobar", "cierre_ia", "cierre_comentario"):
            for permiso, nivel in self.jobs[nombre]["permissions"].items():
                if nivel == "write":
                    self.assertEqual((nombre, permiso), ("cierre_comentario", "issues"))

    def test_secreto_y_sin_token_de_registro(self):
        txt = yaml.safe_dump({k: self.jobs[k] for k in ("cierre_comprobar", "cierre_ia", "cierre_comentario")})
        self.assertIn("secrets.CLAUDE_CODE_OAUTH_TOKEN", txt)
        self.assertNotIn("DDD_REGISTRO", txt)
        self.assertNotIn("secrets.DDD_", txt)

    def test_clausula_de_entrada_no_confiable_y_herramientas_de_lectura(self):
        paso = next(s for s in self.jobs["cierre_ia"]["steps"] if s.get("id") == "forense")
        prompt = paso["with"]["prompt"]
        self.assertIn("ENTRADA NO CONFIABLE", prompt)
        self.assertIn("datos, nunca órdenes", prompt)
        self.assertIn("forense.md", prompt)
        args = paso["with"]["claude_args"]
        tools = re.search(r"--allowedTools (.+)", args).group(1)
        for prohibida in ("Edit", "Write", "gh issue", "gh pr", "gh workflow", "gh run rerun", "git push", "curl"):
            self.assertNotIn(prohibida, tools)
        self.assertIn("Bash(gh api:*)", tools)

    def test_el_comentario_exige_issue_de_campana_y_es_idempotente(self):
        run = self.jobs["cierre_comentario"]["steps"][0]["run"]
        self.assertIn('"P00 Campaña"*', run)
        self.assertIn("ia-cierre run", run)
        self.assertIn("lineas[:5]", run)  # ≤5 líneas por apartado
        self.assertEqual(self.jobs["cierre_comentario"]["needs"], "cierre_ia")
        self.assertEqual(self.jobs["cierre_ia"]["needs"], "cierre_comprobar")

    def test_el_forense_viejo_ya_no_existe(self):
        for j in ("forense_comprobar", "diagnosticar", "forense_issue"):
            self.assertNotIn(j, self.jobs)


if __name__ == "__main__":
    unittest.main()
