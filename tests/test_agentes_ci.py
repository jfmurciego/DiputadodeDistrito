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
    CASOS = {
        "revisor-pr.yml": ("revisar", "veredicto", ".claude/agents/revisor.md"),
        "forense-00.yml": ("diagnosticar", "issue", ".claude/agents/forense.md"),
    }

    def test_sin_boton_manual_y_disparador_esperado(self):
        self.assertIn("pull_request", disparadores(cargar("revisor-pr.yml")))
        run = disparadores(cargar("forense-00.yml"))["workflow_run"]
        self.assertEqual(run["workflows"], ["00 Ejecución Completa del Proyecto"])
        self.assertEqual(run["types"], ["completed"])
        self.assertIn("conclusion == 'failure'", cargar("forense-00.yml")["jobs"]["comprobar"]["if"])
        for nombre in self.CASOS:
            self.assertNotIn("workflow_dispatch", disparadores(cargar(nombre)))

    def test_sin_secreto_se_salta_limpiamente(self):
        for nombre, (agente, publicar, _) in self.CASOS.items():
            with self.subTest(workflow=nombre):
                jobs = cargar(nombre)["jobs"]
                paso = jobs["comprobar"]["steps"][0]
                self.assertEqual(paso["env"]["TOKEN"], "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}")
                self.assertIn('if [[ -z "${TOKEN:-}" ]]', paso["run"])
                self.assertIn("listo=false", paso["run"])
                self.assertIn("exit 0", paso["run"])
                self.assertEqual(jobs[agente]["needs"], "comprobar")
                self.assertEqual(jobs[agente]["if"], "needs.comprobar.outputs.listo == 'true'")
                # el job que publica depende del agente: si este se salta, también se salta (sin fallo)
                self.assertEqual(jobs[publicar]["needs"], agente)
                subprocess.run(["bash", "-n"], input=paso["run"], text=True, check=True)

    def test_el_agente_solo_lee_y_quien_escribe_no_ejecuta_el_agente(self):
        for nombre, (agente, publicar, definicion) in self.CASOS.items():
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
        texto = (WF / "forense-00.yml").read_text(encoding="utf-8")
        for prohibido in ("dispatches", "rerun", "gh workflow run"):
            self.assertNotIn(prohibido, texto)


if __name__ == "__main__":
    unittest.main()
