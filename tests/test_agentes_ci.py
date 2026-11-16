"""Revisor y forense en CI (T-48): forma de los dos workflows, sin red ni secretos."""
import json
import re
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
ACCION = re.compile(r"^anthropics/claude-code-action@[0-9a-f]{40}$")
ESCRITURA = {"write"}


def cargar(nombre):
    return yaml.safe_load((WF / nombre).read_text(encoding="utf-8"))


def disparadores(d):
    return d.get("on") or d.get(True) or {}


class AgentesEnCI(unittest.TestCase):
    # T-366: el forense vive en p90-automatico.yml (ids renombrados por colisión); el revisor sigue en revisor-pr.yml.
    CASOS = {
        "revisor-pr.yml": ("comprobar", "revisar", "veredicto", ".claude/agents/revisor.md"),
        "p90-automatico.yml": ("forense_comprobar", "diagnosticar", "forense_issue", ".claude/agents/forense.md"),
    }

    def test_sin_boton_manual_y_disparador_esperado(self):
        self.assertIn("pull_request", disparadores(cargar("revisor-pr.yml")))
        run = disparadores(cargar("p90-automatico.yml"))["workflow_run"]
        self.assertEqual(run["workflows"], ["P00 Campaña"])  # T-215, D-78
        self.assertEqual(run["types"], ["completed"])
        self.assertIn("conclusion == 'failure'", cargar("p90-automatico.yml")["jobs"]["forense_comprobar"]["if"])
        self.assertIn("github.event.workflow_run.name == 'P00 Campaña'", cargar("p90-automatico.yml")["jobs"]["forense_comprobar"]["if"])
        for nombre in self.CASOS:
            self.assertNotIn("workflow_dispatch", disparadores(cargar(nombre)))

    def test_revisor_solo_con_etiqueta_revisar_ia(self):
        # T-293: sin la etiqueta (o con borrador/PR de robot) comprobar se salta y arrastra revisar y veredicto a «skipped»
        # (= check `veredicto` cumplido). Los tipos se mantienen para que el check exista en cada HEAD.
        d = cargar("revisor-pr.yml")
        tipos = disparadores(d)["pull_request"]["types"]
        self.assertEqual(set(tipos), {"opened", "synchronize", "reopened", "ready_for_review", "labeled"})
        cond = " ".join(d["jobs"]["comprobar"]["if"].split())
        self.assertIn("contains(github.event.pull_request.labels.*.name, 'revisar-ia')", cond)
        self.assertIn("github.event.label.name == 'revisar-ia'", cond)
        self.assertIn("github.event.pull_request.draft == false", cond)
        self.assertIn("github.event.pull_request.user.type != 'Bot'", cond)
        self.assertFalse(d["concurrency"]["cancel-in-progress"])
        self.assertEqual(d["jobs"]["revisar"]["needs"], "comprobar")
        self.assertEqual(d["jobs"]["veredicto"]["needs"], "revisar")

    def test_sin_secreto_se_salta_limpiamente(self):
        for nombre, (comprobar, agente, publicar, _) in self.CASOS.items():
            with self.subTest(workflow=nombre):
                jobs = cargar(nombre)["jobs"]
                paso = jobs[comprobar]["steps"][0]
                self.assertEqual(paso["env"]["TOKEN"], "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}")
                self.assertIn('if [[ -z "${TOKEN:-}" ]]', paso["run"])
                self.assertIn("listo=false", paso["run"])
                self.assertIn("exit 0", paso["run"])
                self.assertEqual(jobs[agente]["needs"], comprobar)
                self.assertEqual(jobs[agente]["if"], f"needs.{comprobar}.outputs.listo == 'true'")
                # el job que publica depende del agente: si este se salta, también se salta (sin fallo)
                self.assertEqual(jobs[publicar]["needs"], agente)
                subprocess.run(["bash", "-n"], input=paso["run"], text=True, check=True)

    def test_el_agente_solo_lee_y_quien_escribe_no_ejecuta_el_agente(self):
        for nombre, (_, agente, publicar, definicion) in self.CASOS.items():
            with self.subTest(workflow=nombre):
                d = cargar(nombre)
                self.assertEqual(d["permissions"], {"contents": "read"})
                jobs = d["jobs"]
                self.assertFalse(ESCRITURA & set(jobs[agente]["permissions"].values()))
                pasos = jobs[agente]["steps"]
                accion = next(p for p in pasos if "claude-code-action" in str(p.get("uses", "")))
                self.assertRegex(accion["uses"], ACCION)
                self.assertIn(definicion, accion["with"]["prompt"])
                self.assertIn("Solo lectura", accion["with"]["prompt"])
                args = accion["with"]["claude_args"]
                self.assertIn("--model sonnet", args)
                herramientas = re.search(r"--allowedTools (\S+)", args).group(1)
                for prohibida in ("Edit", "Write", "git push", "git commit", "gh pr merge", "gh workflow"):
                    self.assertNotIn(prohibida, herramientas)
                esquema = json.loads(re.search(r"--json-schema '(.+)'", args).group(1))
                self.assertEqual(esquema["type"], "object")
                pub = jobs[publicar]
                self.assertFalse(any("claude-code-action" in str(p.get("uses", "")) for p in pub["steps"]))
                self.assertEqual(set(pub["permissions"].values()), {"write"})
                self.assertEqual(len(pub["permissions"]), 1)
                for p in pub["steps"]:
                    subprocess.run(["bash", "-n"], input=p["run"], text=True, check=True)
                    # la salida del modelo entra por variable de entorno, nunca interpolada en el script
                    self.assertNotIn("needs.", p["run"])

    def test_forense_nunca_relanza(self):
        d = cargar("p90-automatico.yml")
        texto = json.dumps({k: d["jobs"][k] for k in ("forense_comprobar", "diagnosticar", "forense_issue")})
        for prohibido in ("dispatches", "rerun", "gh workflow run"):
            self.assertNotIn(prohibido, texto)


if __name__ == "__main__":
    unittest.main()
