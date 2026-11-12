#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-220: el paso «Huella de puentes antes de M02» decide el ámbito con el resolutor (no por prefijo) bajo
`bash -eo pipefail`, como lo ejecuta GitHub (`shell: bash`; lección de #726)."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/_reutilizable-generacion-territorial.yml"


def _paso() -> str:
    wf = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    for job in wf["jobs"].values():
        for step in job.get("steps", []):
            if step.get("name") == "Huella de puentes antes de M02":
                return step["run"].replace("${GITHUB_SHA}", "local")
    raise AssertionError("falta el paso «Huella de puentes antes de M02»")


@unittest.skipIf(shutil.which("bash") is None, "sin bash")
class HuellaDePuentesShell(unittest.TestCase):
    def ejecutar(self, params: str, con_m01: bool = False):
        with tempfile.TemporaryDirectory() as tmp:
            cache, binarios = Path(tmp) / "cache", Path(tmp) / "bin"
            cache.mkdir()
            binarios.mkdir()
            if con_m01:
                (cache / "x_m01_secciones_poblacion.geojson.zip").write_bytes(b"")
            docker = binarios / "docker"  # docker simulado que falla: la huella no casa
            docker.write_text("#!/bin/sh\necho docker-simulado \"$@\"\nexit 1\n", encoding="utf-8")
            docker.chmod(0o755)
            env = {**os.environ, "PARAMS": params, "CACHE_DIR": str(cache),
                   "PATH": f"{binarios}{os.pathsep}{os.environ.get('PATH', '')}"}
            return subprocess.run(["bash", "-eo", "pipefail", "-c", _paso()], cwd=ROOT, env=env,
                                  capture_output=True, text=True)

    def test_autonomica_sale_sin_comprobar(self):
        r = self.ejecutar("territorios/aut02/config/aut02_2025.yaml")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no es un ámbito nacional", r.stdout)

    def test_id_viejo_o_desconocido_no_rompe_el_paso(self):
        r = self.ejecutar("territorios/inexistente/config/inexistente_2025.yaml")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("no es un ámbito nacional", r.stdout)

    def test_nacional_sin_m01_avisa_y_sigue(self):
        r = self.ejecutar("territorios/nac22/config/nac22_2025.yaml")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Sin M01", r.stdout)
        self.assertNotIn("no es un ámbito nacional", r.stdout)

    def test_nacional_con_huella_que_no_casa_falla(self):
        r = self.ejecutar("territorios/nac22/config/nac22_2025.yaml", con_m01=True)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("docker-simulado", r.stdout)


if __name__ == "__main__":
    unittest.main()
