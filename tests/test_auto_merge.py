"""T-54: forma del workflow de fusión automática, sin red."""
import subprocess
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "auto-merge.yml"


class AutoMerge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = yaml.safe_load(WF.read_text(encoding="utf-8"))
        cls.on = cls.d.get("on") or cls.d.get(True)
        cls.job = cls.d["jobs"]["fusionar"]
        cls.pasos = {p["name"]: p for p in cls.job["steps"]}

    def test_disparadores_y_permisos(self):
        self.assertNotIn("workflow_dispatch", self.on)
        self.assertNotIn("pull_request_target", self.on)
        pr = self.on["pull_request"]
        self.assertEqual(pr["branches"], ["main"])
        for t in ("opened", "synchronize", "ready_for_review", "labeled"):
            self.assertIn(t, pr["types"])
        self.assertEqual(self.d["permissions"], {"contents": "write", "pull-requests": "write"})
        self.assertIn("head.repo.full_name == github.repository", self.job["if"])

    def test_squash_ligado_al_head_y_respaldo_si_ya_esta_clean(self):
        run = self.pasos["Activar el auto-merge o fusionar si ya está en verde"]["run"]
        self.assertIn('gh pr merge "$PR" --auto --squash --match-head-commit "$HEAD_SHA"', run)
        self.assertIn('"OPEN CLEAN")', run)
        self.assertIn('gh pr merge "$PR" --squash --match-head-commit "$HEAD_SHA"', run)
        self.assertNotIn("--admin", run)  # nunca se salta el ruleset (`pruebas` en verde)

    def test_etiqueta_no_automerge_y_borradores_excluidos(self):
        run = self.pasos["Activar el auto-merge o fusionar si ya está en verde"]["run"]
        self.assertLess(run.index("no-automerge"), run.index("--auto"))
        self.assertIn("--disable-auto", run)
        self.assertLess(run.index('"$DRAFT" == "true"'), run.index("--auto"))

    def test_token_de_la_app_con_respaldo_y_sintaxis(self):
        paso = self.pasos["Activar el auto-merge o fusionar si ya está en verde"]
        self.assertEqual(paso["env"]["APP_ID"], "${{ secrets.DDD_REGISTRO_APP_ID }}")
        self.assertEqual(paso["env"]["GH_TOKEN"], "${{ github.token }}")
        self.assertIn("::add-mask::", paso["run"])
        self.assertLess(paso["run"].index('export GH_TOKEN="$token"'), paso["run"].index("gh pr merge"))
        for p in self.job["steps"]:
            subprocess.run(["bash", "-n"], input=p["run"], text=True, check=True)


if __name__ == "__main__":
    unittest.main()
