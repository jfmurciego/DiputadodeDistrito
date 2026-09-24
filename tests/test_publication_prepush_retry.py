import os
import subprocess
import tempfile
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "herramientas" / "sincronizar_estado_publicacion.sh"
WRAPPER = ROOT / ".github" / "workflows" / "desplegar-visor-publico.yml"
PUBLISHER = ROOT / ".github" / "workflows" / "_reutilizable-publicar-sitio.yml"


class PublicationPrepushRetry(unittest.TestCase):
    def run_sync(self, fail_pushes: int):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            state = root / "push-count"
            fake_git = bin_dir / "git"
            fake_git.write_text(
                """#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  pull)
    exit 0
    ;;
  push)
    count=0
    [[ -f "$STATE_FILE" ]] && count="$(cat "$STATE_FILE")"
    count=$((count + 1))
    printf '%s\\n' "$count" > "$STATE_FILE"
    if (( count <= FAIL_PUSHES )); then
      echo "remote: Internal Server Error" >&2
      exit 1
    fi
    exit 0
    ;;
  rebase)
    exit 0
    ;;
  *)
    exit 0
    ;;
esac
""",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            fake_sleep = bin_dir / "sleep"
            fake_sleep.write_text("#!/usr/bin/env bash\\nexit 0\\n", encoding="utf-8")
            fake_sleep.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "PATH": f"{bin_dir}:{env['PATH']}",
                "STATE_FILE": str(state),
                "FAIL_PUSHES": str(fail_pushes),
            })
            completed = subprocess.run(
                ["bash", str(SYNC)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
            )
            pushes = int(state.read_text(encoding="utf-8").strip()) if state.exists() else 0
            return completed, pushes

    def test_first_push_rejected_then_second_succeeds(self):
        completed, pushes = self.run_sync(1)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(pushes, 2)

    def test_three_push_rejections_stop_before_pages(self):
        completed, pushes = self.run_sync(3)
        self.assertEqual(completed.returncode, 48)
        self.assertEqual(pushes, 3)
        self.assertIn("No se pudo sincronizar el estado operativo antes de publicar.", completed.stderr)

        wrapper = yaml.safe_load(WRAPPER.read_text(encoding="utf-8")) or {}
        self.assertEqual(wrapper["jobs"]["publicar"]["needs"], "preparar_publicacion")
        self.assertNotIn("actions/deploy-pages", WRAPPER.read_text(encoding="utf-8"))
        self.assertIn("actions/deploy-pages", PUBLISHER.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
