"""T-78: allowlist de herramientas por rol (`.claude/hooks/rol_herramientas.py` y su cableado)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "rol_herramientas.py"


def _hook(tool: str, rol: str | None = None, comando: str = "", env_rol: str | None = None,
          agente: str | None = None):
    datos = {"tool_name": tool, "tool_input": {"command": comando, "file_path": "/tmp/x"}}
    if agente:
        datos["agent_type"] = agente
    entrada = json.dumps(datos)
    env = {k: v for k, v in os.environ.items() if k != "DDD_ROL"}
    if env_rol:
        env["DDD_ROL"] = env_rol
    args = [sys.executable, str(HOOK)] + (["--rol", rol] if rol else [])
    return subprocess.run(args, input=entrada, text=True, capture_output=True, env=env, check=False)


class SoloLectura(unittest.TestCase):
    def test_herramientas_de_escritura_bloqueadas(self):
        for tool in ("Edit", "Write", "NotebookEdit", "Agent", "mcp__github__merge_pull_request",
                     "mcp__github__create_or_update_file", "mcp__github__actions_run_trigger"):
            with self.subTest(tool=tool):
                res = _hook(tool, "solo-lectura")
                self.assertEqual(res.returncode, 2, res.stderr)
                self.assertIn("Bloqueado", res.stderr)

    def test_bash_que_escribe_bloqueado(self):
        for comando in ("git commit -m x", "git push -u origin rama", "git checkout main", "git branch -D x",
                        "gh api -X POST repos/o/r/actions/workflows/f.yml/dispatches -f ref=main",
                        "gh api repos/o/r/issues/1/comments -f body=x", "gh api --method=PATCH repos/o/r",
                        "gh pr merge 3", "gh workflow run f.yml", "gh run rerun 1", "rm -rf x",
                        "echo x > f.txt", "cat a | tee b", "sed -i s/a/b/ f", "find . -delete",
                        "python3 -c 'open(1)'", "curl -X POST https://x", "ls $(rm x)",
                        "git -C repo push origin x", "xargs rm < lista"):
            with self.subTest(comando=comando):
                self.assertEqual(_hook("Bash", "solo-lectura", comando).returncode, 2, comando)

    def test_lectura_pasa(self):
        for tool in ("Read", "Grep", "Glob", "mcp__github__get_job_logs", "mcp__github__pull_request_read"):
            self.assertEqual(_hook(tool, "solo-lectura").returncode, 0, tool)
        for comando in ("git diff origin/main...HEAD", "git -C . log --oneline -5", "git show abc:f.py | head",
                        "gh api repos/o/r/pulls/3 -q .head.sha", "gh api -X GET search/code -f q=x",
                        "gh pr diff 3", "gh run view 9 --log-failed 2>&1 | grep -E 'Error' | head",
                        "cat f >/dev/null 2>&1", "jq '.a > 3' f.json", "unzip -l z.zip", "sed -n 1,5p f"):
            with self.subTest(comando=comando):
                res = _hook("Bash", "solo-lectura", comando)
                self.assertEqual(res.returncode, 0, res.stderr)


class PorAgentType(unittest.TestCase):
    """El hook global recibe `agent_type` cuando actúa un subagente (comprobado en Claude Code 2.1.319)."""

    def test_revisor_y_forense_son_solo_lectura_aunque_la_sesion_sea_operador(self):
        for agente in ("revisor", "forense"):
            with self.subTest(agente=agente):
                self.assertEqual(_hook("Bash", comando="git commit -m x", agente=agente).returncode, 2)
                self.assertEqual(_hook("Bash", comando="echo x > f", agente=agente, env_rol="operador").returncode, 2)
                self.assertEqual(_hook("Bash", comando="git log -1", agente=agente).returncode, 0)

    def test_otros_subagentes_no_heredan_solo_lectura(self):
        self.assertEqual(_hook("Bash", comando="git commit -m x", agente="Explore").returncode, 0)


class Operador(unittest.TestCase):
    def test_operador_no_edita_y_si_lanza(self):
        for tool in ("Edit", "Write", "NotebookEdit"):
            self.assertEqual(_hook(tool, env_rol="operador").returncode, 2, tool)
        lanzar = "gh api -X POST repos/o/r/actions/workflows/f.yml/dispatches -f ref=main"
        self.assertEqual(_hook("Bash", env_rol="operador", comando=lanzar).returncode, 0)

    def test_sin_rol_no_restringe(self):
        for tool in ("Edit", "Write"):
            self.assertEqual(_hook(tool).returncode, 0, tool)


class Cableado(unittest.TestCase):
    def _frontmatter(self, nombre):
        texto = (ROOT / ".claude" / "agents" / f"{nombre}.md").read_text(encoding="utf-8")
        return yaml.safe_load(texto.split("---")[1])

    def test_subagentes_con_allowlist(self):
        for nombre in ("revisor", "forense"):
            with self.subTest(agente=nombre):
                fm = self._frontmatter(nombre)
                self.assertEqual([t.strip() for t in fm["tools"].split(",")], ["Read", "Grep", "Glob", "Bash"])
                denegadas = {t.strip() for t in fm["disallowedTools"].split(",")}
                self.assertLessEqual({"Edit", "Write", "NotebookEdit", "Agent"}, denegadas)

    def test_settings_cablea_operador_y_deniega(self):
        d = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("mcp__github__create_repository", d["permissions"]["deny"])
        self.assertNotIn("allow", d["permissions"])  # T-78 no amplía permisos de nadie
        entradas = {m["matcher"]: [h["command"] for h in m["hooks"]] for m in d["hooks"]["PreToolUse"]}
        self.assertTrue(any("guardia_git.py" in c for c in entradas["Bash"]))
        self.assertTrue(any("rol_herramientas.py" in c for c in entradas["*"]))


if __name__ == "__main__":
    unittest.main()
