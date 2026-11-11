"""T-246: la 00 bloquea al planificar si el paquete electoral del par no es descargable."""
from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas import comprobar_paquete_electoral_remoto as cp

ROOT = Path(__file__).resolve().parents[1]
REPO = "o/r"
RUN = 4242
NAME = "ddd-electoral-source-andalucia"
DIGEST = "a" * 64
NOW = dt.datetime(2026, 11, 11, 12, 0, tzinfo=dt.timezone.utc)


def plan(**over):
    p = {
        "territory_name": "Andalucía",
        "publication_mode_effective": "electoral",
        "electoral_activation": {"execution": "EXECUTE"},
        "run_prepare_electoral": False,
        "prepared_source_pair": {"receipt_path": "pair.json", "pair_sha256": "b" * 64},
        "existing": {"electoral_source": {"run_id": RUN, "artifact_name": NAME, "artifact_sha256": "sha256:" + DIGEST}},
    }
    p.update(over)
    return p


def art(**over):
    a = {"id": 7, "name": NAME, "expired": False, "digest": "sha256:" + DIGEST,
         "expires_at": "2026-11-30T00:00:00Z", "workflow_run": {"id": RUN}}
    a.update(over)
    return a


def fake_api(run_artifacts=(), by_name=(), releases=()):
    def api(path):
        if path.startswith(f"repos/{REPO}/actions/runs/{RUN}/artifacts"):
            return {"artifacts": list(run_artifacts)}
        if path.startswith(f"repos/{REPO}/actions/artifacts?name="):
            return {"artifacts": list(by_name)}
        if path.startswith(f"repos/{REPO}/releases"):
            return list(releases)
        raise AssertionError(path)
    return api


class PreflightPaqueteElectoral(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        (self.root / "pair.json").write_text(json.dumps(
            {"electoral_source": {"remote_verification": {"artifact_id": 7}}}), encoding="utf-8")

    def tearDown(self):
        self.td.cleanup()

    def run_eval(self, p, api):
        return cp.evaluar(p, repo=REPO, root=self.root, api=api, now=NOW)

    def test_vivo_y_acreditado_pasa(self):
        r = self.run_eval(plan(), fake_api([art()]))
        self.assertEqual(r["decision"], "READY")
        self.assertEqual(r["source"], "actions")

    def test_caducado_sin_copia_bloquea_con_remedio(self):
        r = self.run_eval(plan(), fake_api([art(expired=True)]))
        self.assertEqual((r["decision"], r["code"]), ("BLOCK", "ELECTORAL_PACKAGE_EXPIRED"))
        self.assertIn("preparacion-resultados-electorales.yml", r["message"])
        self.assertIn("reutilizar_si_ya_preparada=false", r["message"])
        self.assertIn("prepare_one", r["message"])
        self.assertIn("Andalucía", r["message"])

    def test_ausente_bloquea(self):
        r = self.run_eval(plan(), fake_api())
        self.assertEqual(r["code"], "ELECTORAL_PACKAGE_MISSING")

    def test_digest_distinto_bloquea(self):
        r = self.run_eval(plan(), fake_api([art(digest="sha256:" + "c" * 64)]))
        self.assertEqual(r["code"], "ELECTORAL_PACKAGE_DIGEST_MISMATCH")

    def test_artifact_id_contradice_receipt(self):
        r = self.run_eval(plan(), fake_api([art(id=8)]))
        self.assertEqual(r["code"], "ELECTORAL_PACKAGE_IDENTITY_MISMATCH")

    def test_caduca_antes_de_llegar_a_la_puerta(self):
        r = self.run_eval(plan(), fake_api([art(expires_at="2026-11-11T18:00:00Z")]))
        self.assertEqual(r["code"], "ELECTORAL_PACKAGE_EXPIRES_SOON")

    def test_mismo_digest_en_otro_run_pasa_como_la_puerta(self):
        r = self.run_eval(plan(), fake_api([art(expired=True)], by_name=[art(id=99, workflow_run={"id": 5})]))
        self.assertEqual(r["decision"], "READY")

    def test_copia_durable_en_release_pasa(self):
        release = {"tag_name": f"almacen-m06-andalucia-{RUN}",
                   "assets": [{"id": 1, "name": f"{NAME}-7.zip", "digest": "sha256:" + DIGEST}]}
        r = self.run_eval(plan(), fake_api([art(expired=True)], releases=[release]))
        self.assertEqual((r["decision"], r["source"]), ("READY", "release"))

    def test_sin_par_o_con_03_no_aplica(self):
        for p in (plan(run_prepare_electoral=True), plan(prepared_source_pair={}),
                  plan(publication_mode_effective="territorial_only"),
                  plan(electoral_activation={"execution": "SKIP"})):
            self.assertEqual(self.run_eval(p, fake_api())["decision"], "NOT_REQUIRED")

    def test_identidad_incompleta_bloquea(self):
        p = plan(existing={"electoral_source": {"run_id": RUN, "artifact_name": NAME}})
        self.assertEqual(self.run_eval(p, fake_api())["code"], "ELECTORAL_PACKAGE_IDENTITY_INCOMPLETE")

    def test_cli_sale_con_76_al_bloquear(self):
        (self.root / "plan.json").write_text(json.dumps(plan()), encoding="utf-8")
        out = self.root / "r.json"
        original = cp.gh_api
        cp.gh_api = fake_api([art(expired=True)])
        try:
            code = cp.main(["--plan", str(self.root / "plan.json"), "--repo", REPO,
                            "--root-dir", str(self.root), "--output", str(out)])
        finally:
            cp.gh_api = original
        self.assertEqual(code, 76)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["code"], "ELECTORAL_PACKAGE_EXPIRED")


class WorkflowPlanificar(unittest.TestCase):
    def test_paso_temprano_en_planificar_antes_de_generar(self):
        wf = yaml.load((ROOT / ".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8"),
                       Loader=yaml.BaseLoader)
        steps = wf["jobs"]["planificar"]["steps"]
        ids = [s.get("id") for s in steps]
        i = ids.index("electoral_package")
        self.assertGreater(i, ids.index("plan"))
        step = steps[i]
        self.assertIn("herramientas.comprobar_paquete_electoral_remoto", step["run"])
        self.assertIn("pull_request", step["if"])
        self.assertEqual(step["env"]["GH_TOKEN"], "${{ github.token }}")


if __name__ == "__main__":
    unittest.main()
