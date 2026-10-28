"""Regresión: fuente territorial registrada cuyo artefacto de Actions ya no existe.

El 27-10-2026 Andalucía (run 40604585745) y Comunidad Valenciana (run 40604791319)
fallaron en "Recuperar fuente territorial registrada" con exit 44 porque el artefacto
registrado había caducado. Caducado o eliminado no contradice la identidad registrada:
el paso debe ceder a la adquisición oficial. Un digest distinto, un nombre ambiguo o
una recuperación exacta (recover_run_id) siguen bloqueando.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "preparacion-fuentes.yml"
NAME = "ddd-source-package-andalucia-2025-36020646219"
DIGEST = "a" * 64


def _workflow():
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _step(job, step_id=None, name=None):
    for step in _workflow()["jobs"][job]["steps"]:
        if (step_id and step.get("id") == step_id) or (name and step.get("name") == name):
            return step
    raise AssertionError(f"paso no encontrado en {job}")


class FuenteCaducadaTests(unittest.TestCase):
    def _run_previous(self, artifacts, explicit_recovery=False):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "artifacts.json").write_text(json.dumps({"artifacts": artifacts}), encoding="utf-8")
            gh = tmp / "bin" / "gh"
            gh.parent.mkdir()
            # Solo responde al inventario; cualquier descarga indicaría reutilización.
            gh.write_text(
                "#!/usr/bin/env bash\n"
                f'if [[ "$1" == api ]]; then cat {tmp / "artifacts.json"}; exit 0; fi\n'
                'echo "DOWNLOAD_ATTEMPTED $*" >&2; exit 99\n', encoding="utf-8")
            gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
            output = tmp / "github_output"
            output.write_text("", encoding="utf-8")
            env = dict(os.environ, PATH=f"{gh.parent}:{os.environ['PATH']}", GITHUB_OUTPUT=str(output),
                       GITHUB_REPOSITORY="jfmurciego/DiputadodeDistrito", REGISTERED_RUN_ID="36020646219",
                       REGISTERED_ARTIFACT_NAME=NAME, REGISTERED_ARTIFACT_SHA256=DIGEST,
                       TERRITORY_ID="andalucia", EDITION="2025", POPULATION_YEAR="2025", SECTION_YEAR="2025",
                       EXPLICIT_RECOVERY=str(explicit_recovery).lower())
            result = subprocess.run(["bash", "-c", _step("territoriales", step_id="previous")["run"]],
                                    cwd=tmp, env=env, capture_output=True, text=True)
            return result, output.read_text(encoding="utf-8")

    def test_artefacto_caducado_cede_a_la_adquisicion_oficial(self):
        result, output = self._run_previous([{"name": NAME, "expired": True, "digest": f"sha256:{DIGEST}"}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reused_candidate=false", output)
        self.assertIn("::warning::", result.stdout)
        self.assertNotIn("DOWNLOAD_ATTEMPTED", result.stderr)

    def test_artefacto_eliminado_cede_a_la_adquisicion_oficial(self):
        result, output = self._run_previous([{"name": "otro-artefacto", "expired": False}])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("reused_candidate=false", output)

    def test_recuperacion_exacta_caducada_sigue_bloqueando(self):
        result, output = self._run_previous([{"name": NAME, "expired": True, "digest": f"sha256:{DIGEST}"}],
                                            explicit_recovery=True)
        self.assertEqual(result.returncode, 44)
        self.assertNotIn("reused_candidate", output)

    def test_digest_distinto_sigue_bloqueando(self):
        result, output = self._run_previous([{"name": NAME, "expired": False, "digest": "sha256:" + "b" * 64}])
        self.assertEqual(result.returncode, 45)
        self.assertNotIn("reused_candidate", output)

    def test_nombre_ambiguo_sigue_bloqueando(self):
        twin = {"name": NAME, "expired": False, "digest": f"sha256:{DIGEST}"}
        result, output = self._run_previous([twin, dict(twin)])
        self.assertEqual(result.returncode, 44)
        self.assertNotIn("reused_candidate", output)

    def test_la_adquisicion_depende_de_reused_candidate(self):
        acquire = _step("territoriales", step_id="acquire")
        self.assertEqual(acquire["if"], "${{ steps.previous.outputs.reused_candidate != 'true' }}")

    def test_resultado_no_atribuye_preparacion_a_un_fallo(self):
        step = _step("resultado", name="Exigir registro cuando la persistencia es obligatoria")
        env = dict(os.environ, PREPARATION_RESULT="failure", REGISTRATION_RESULT="skipped",
                   PERSIST_STATE="true", GENERATION_PENDING_RESULT="skipped")
        result = subprocess.run(["bash", "-c", step["run"]], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("La fuente fue preparada", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
