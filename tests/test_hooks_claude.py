"""Pruebas del hook de Claude Code `.claude/hooks/guardia_git.py` (caso que bloquea y caso que pasa)."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "guardia_git.py"
OPEN, SEP, CLOSE = "<" * 7, "=" * 7, ">" * 7


def _hook(comando: str, cwd: Path | None = None, tool: str = "Bash") -> subprocess.CompletedProcess[str]:
    entrada = json.dumps({"tool_name": tool, "tool_input": {"command": comando}})
    return subprocess.run([sys.executable, str(HOOK)], input=entrada, text=True,
                          capture_output=True, cwd=cwd, check=False)


@unittest.skipUnless(HOOK.is_file() and shutil.which("git"), "hook o git no disponibles en este entorno")
class GuardiaGit(unittest.TestCase):
    def test_push_forzado_bloqueado(self):
        for comando in ("git push --force origin main", "git push -f", "git push -uf origin x",
                        "git push --force-with-lease origin x", "git push origin +main",
                        "cd repo && git -C . push --force"):
            with self.subTest(comando=comando):
                res = _hook(comando)
                self.assertEqual(res.returncode, 2, res.stderr)
                self.assertIn("push forzado", res.stderr)

    def test_push_normal_y_otras_herramientas_pasan(self):
        self.assertEqual(_hook("git push -u origin claude/rama").returncode, 0)
        self.assertEqual(_hook("echo git push --force", tool="Read").returncode, 0)
        self.assertEqual(_hook("ls -f").returncode, 0)

    def test_commit_con_marcas_bloqueado_y_limpio_pasa(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git = lambda *a: subprocess.run(["git", "-C", tmp, *a], check=True, capture_output=True)
            git("init", "-q")
            (repo / "limpio.md").write_text(f"Título\n{SEP}\n", encoding="utf-8")
            git("add", "limpio.md")
            self.assertEqual(_hook("git commit -m ok", cwd=repo).returncode, 0)
            (repo / "roto.md").write_text(f"{OPEN} HEAD\na\n{SEP}\nb\n{CLOSE} main\n", encoding="utf-8")
            git("add", "roto.md")
            res = _hook("git add -A && git commit -m roto", cwd=repo)
            self.assertEqual(res.returncode, 2)
            self.assertIn("roto.md:1", res.stderr)
            # Con -a se mira la copia de trabajo aunque no esté preparada.
            git("rm", "-q", "--cached", "roto.md")
            git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "base")
            (repo / "limpio.md").write_text(f"{OPEN} HEAD\n", encoding="utf-8")
            self.assertEqual(_hook("git commit -am x", cwd=repo).returncode, 2)
            self.assertEqual(_hook("git commit -m x", cwd=repo).returncode, 0)


if __name__ == "__main__":
    unittest.main()
