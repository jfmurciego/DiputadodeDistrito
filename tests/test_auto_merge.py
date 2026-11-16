"""T-54b: la fusión automática solo ocurre con el check-run `pruebas` en success sobre el HEAD exacto.

Incidente: auto-merge.yml 1.0.0 fusionó #453 (12 s) y #454 (60 s) sin `pruebas`, porque con el token de la app exenta
del ruleset la PR salía «clean» al instante.
"""
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "herramientas"))

import decidir_auto_merge as dam  # noqa: E402

WF = ROOT / ".github" / "workflows" / "p90-automatico.yml"  # T-366: job `fusionar` (antes auto-merge.yml)
REPO = "jfmurciego/DiputadodeDistrito"
SHA = "a" * 40


def pr(**cambios):
    base = {"state": "open", "merged": False, "draft": False, "base": {"ref": "main"},
            "head": {"sha": SHA, "repo": {"full_name": REPO}}, "labels": [],
            "mergeable_state": "clean"}
    base.update(cambios)
    return base


def checks(*runs):
    return {"check_runs": [dict({"name": "pruebas", "head_sha": SHA, "id": i + 1,
                                  "started_at": f"2026-11-07T18:0{i}:00Z"}, **r) for i, r in enumerate(runs)]}


class Decision(unittest.TestCase):
    def test_pruebas_pendiente_no_fusiona(self):
        for estado in ({"status": "queued", "conclusion": None}, {"status": "in_progress", "conclusion": None}):
            self.assertEqual(dam.decidir(pr(), checks(estado), SHA, REPO)["decision"], "ESPERAR")
        self.assertEqual(dam.decidir(pr(), {"check_runs": []}, SHA, REPO)["decision"], "ESPERAR")

    def test_pruebas_en_failure_no_fusiona(self):
        for c in ("failure", "cancelled", "skipped", "timed_out"):
            self.assertEqual(dam.decidir(pr(), checks({"status": "completed", "conclusion": c}), SHA, REPO)["decision"], "NO")

    def test_pruebas_en_success_fusiona(self):
        r = dam.decidir(pr(), checks({"status": "completed", "conclusion": "success"}), SHA, REPO)
        self.assertEqual(r["decision"], "FUSIONAR")

    def test_clean_no_basta_y_cuenta_el_ultimo_run_del_sha(self):
        # mergeable_state clean (como con la app exenta) no sirve sin `pruebas`.
        self.assertEqual(dam.decidir(pr(mergeable_state="clean"), {"check_runs": []}, SHA, REPO)["decision"], "ESPERAR")
        verde_viejo_rojo_nuevo = checks({"status": "completed", "conclusion": "success"},
                                       {"status": "completed", "conclusion": "failure"})
        self.assertEqual(dam.decidir(pr(), verde_viejo_rojo_nuevo, SHA, REPO)["decision"], "NO")
        otro_sha = {"check_runs": [{"name": "pruebas", "head_sha": "b" * 40, "status": "completed",
                                    "conclusion": "success", "id": 1, "started_at": "x"}]}
        self.assertEqual(dam.decidir(pr(), otro_sha, SHA, REPO)["decision"], "ESPERAR")
        otro_check = {"check_runs": [{"name": "guardian", "head_sha": SHA, "status": "completed",
                                      "conclusion": "success", "id": 1, "started_at": "x"}]}
        self.assertEqual(dam.decidir(pr(), otro_check, SHA, REPO)["decision"], "ESPERAR")

    def test_exclusiones(self):
        verde = checks({"status": "completed", "conclusion": "success"})
        casos = [pr(draft=True), pr(labels=[{"name": "no-automerge"}]), pr(base={"ref": "dev"}),
                 pr(head={"sha": SHA, "repo": {"full_name": "otro/fork"}}), pr(head={"sha": "c" * 40, "repo": {"full_name": REPO}}),
                 pr(state="closed")]
        for p in casos:
            self.assertEqual(dam.decidir(p, verde, SHA, REPO)["decision"], "NO", p)


class CasoPR458(unittest.TestCase):
    """Datos reales de #458 (T-65): HEAD b833188c, fusionada a las 18:14:04 por la 1.0.0; su `pruebas` (suite
    114870396227) empezó a las 18:14:09 y acabó en failure. Con 1.2.0 nunca se fusiona."""
    HEAD = "b833188c433d8a735fb1291561693a3fca0d4ff7"
    SUITE = 114870396227

    def pr458(self):
        return pr(head={"sha": self.HEAD, "repo": {"full_name": REPO}}, mergeable_state="clean")

    def test_a_la_hora_de_la_fusion_no_habia_pruebas(self):
        r = dam.decidir(self.pr458(), {"check_runs": []}, self.HEAD, REPO, self.SUITE)
        self.assertEqual(r["decision"], "ESPERAR")

    def test_el_pruebas_que_llego_despues_fallo(self):
        real = {"check_runs": [{"id": 128486077717, "name": "pruebas", "head_sha": self.HEAD, "status": "completed",
                                "conclusion": "failure", "started_at": "2026-11-07T18:14:09Z",
                                "check_suite": {"id": self.SUITE}, "app": {"slug": "github-actions"}}]}
        self.assertEqual(dam.decidir(self.pr458(), real, self.HEAD, REPO, self.SUITE)["decision"], "NO")

    def test_un_pruebas_verde_de_otra_suite_no_vale(self):
        otro = {"check_runs": [{"id": 1, "name": "pruebas", "head_sha": self.HEAD, "status": "completed",
                                "conclusion": "success", "started_at": "2026-11-07T18:13:00Z",
                                "check_suite": {"id": 999}}]}
        self.assertEqual(dam.decidir(self.pr458(), otro, self.HEAD, REPO, self.SUITE)["decision"], "ESPERAR")
        otro["check_runs"][0]["check_suite"]["id"] = self.SUITE
        self.assertEqual(dam.decidir(self.pr458(), otro, self.HEAD, REPO, self.SUITE)["decision"], "FUSIONAR")

    def test_la_fusion_corre_en_workflow_run_de_main_no_en_el_codigo_de_la_pr(self):
        # T-366: el job `fusionar` vive en p90-automatico.yml pero se ejecuta SOLO por `workflow_run` de «P90 Automático»: GitHub usa
        # entonces la definición del workflow en `main`, nunca la de la referencia de merge de la PR. Sin auto-merge nativo.
        d = yaml.safe_load(WF.read_text(encoding="utf-8"))
        on = d.get("on") or d.get(True)
        self.assertNotIn("pull_request_target", on)
        self.assertIn("P90 Automático", on["workflow_run"]["workflows"])
        texto = WF.read_text(encoding="utf-8")
        self.assertNotIn("--auto ", texto)
        self.assertNotIn("enablePullRequestAutoMerge", texto)
        job = d["jobs"]["fusionar"]
        self.assertNotIn("needs", job)  # corre en OTRO run: la puerta es el check-run `pruebas` de la suite disparadora
        for trozo in ("github.event_name == 'workflow_run'", "github.event.workflow_run.path == '.github/workflows/p90-automatico.yml'",
                      "github.event.workflow_run.event == 'pull_request'"):
            self.assertIn(trozo, job["if"])
        self.assertEqual(job["steps"][1]["env"]["SUITE"], "${{ github.event.workflow_run.check_suite_id }}")
        self.assertEqual(job["steps"][1]["env"]["SHA"], "${{ github.event.workflow_run.head_sha }}")
        self.assertIn('--suite "$SUITE"', job["steps"][1]["run"])

    def test_el_job_de_fusion_no_se_ejecuta_en_el_run_de_la_pr(self):
        # Ningún disparador de P90 que lleve el código de la PR (pull_request) puede activar `fusionar`: su `if` exige workflow_run.
        d = yaml.safe_load(WF.read_text(encoding="utf-8"))
        self.assertTrue(d["jobs"]["fusionar"]["if"].startswith("${{ github.event_name == 'workflow_run' &&"))
        # y el resto de jobs de escritura de P90 con el token de la app (fusionar) no están en el run `pull_request`
        self.assertEqual(d["jobs"]["fusionar"]["permissions"], {"contents": "read", "checks": "read", "pull-requests": "read"})
        self.assertEqual(d["jobs"]["fusionar"]["steps"][0]["with"]["ref"], "main")

    def test_forense_no_se_dispara_con_la_fusion(self):
        # P90 se dispara a sí mismo (workflow_run): el forense solo atiende «P00 Campaña».
        d = yaml.safe_load(WF.read_text(encoding="utf-8"))
        self.assertIn("github.event.workflow_run.name == 'P00 Campaña'", d["jobs"]["forense_comprobar"]["if"])


class Workflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = yaml.safe_load(WF.read_text(encoding="utf-8"))
        cls.on = cls.d.get("on") or cls.d.get(True)
        cls.job = cls.d["jobs"]["fusionar"]
        cls.script = cls.job["steps"][1]["run"]

    def test_solo_tras_pruebas_y_sin_auto_merge_nativo(self):
        self.assertIn("workflow_run", self.job["if"])
        for prohibido in ("--auto", "--admin", "mergeable_state", "mergeStateStatus", "CLEAN"):
            self.assertNotIn(prohibido, self.script)
        self.assertEqual(self.job["permissions"], {"contents": "read", "checks": "read", "pull-requests": "read"})

    def test_decide_por_el_check_run_del_sha_antes_de_fusionar(self):
        s = self.script
        self.assertIn("commits/$SHA/check-runs?check_name=pruebas", s)
        self.assertIn("herramientas/decidir_auto_merge.py", s)
        self.assertLess(s.index("decidir_auto_merge.py"), s.index("gh pr merge"))
        self.assertIn('gh pr merge "$pr" --squash --match-head-commit "$SHA"', s)
        self.assertEqual(self.job["steps"][0]["with"]["ref"], "main")  # código de main, nunca el de la PR
        subprocess.run(["bash", "-n"], input=s, text=True, check=True)


if __name__ == "__main__":
    unittest.main()
