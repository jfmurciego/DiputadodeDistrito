"""T-52: cadena 00 territorial → Activación de Legislatura → 00 electoral «Reutilizar» en GitHub, sin el Mac."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"


def triggers(d):
    return d.get("on") or d.get(True)


class CadenaElectoral(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = yaml.safe_load(ORCH.read_text(encoding="utf-8"))
        cls.job = cls.wf["jobs"]["encadenar_par_y_04"]
        cls.script = cls.job["steps"][0]["run"]

    def test_entradas_compatibles_con_lo_actual(self):
        dispatch = triggers(self.wf)["workflow_dispatch"]["inputs"]
        self.assertEqual(dispatch["cadena_electoral"]["default"], False)
        self.assertEqual(dispatch["cadena_electoral"]["type"], "boolean")
        self.assertEqual(dispatch["cadena_origen_run_id"]["default"], "")
        call = triggers(self.wf)["workflow_call"]["inputs"]
        self.assertFalse(call["cadena_electoral"]["default"])
        self.assertIn("inputs.territory_id", self.wf["run-name"])

    def test_territorial_only_con_cadena_encadena_y_el_resto_sigue_igual(self):
        cond = self.job["if"]
        self.assertIn("(inputs.cadena_electoral && inputs.publication_mode == 'territorial_only')", cond)
        self.assertIn("completion_status == 'SKIPPED_NO_ACCREDITED_PAIR'", cond)
        self.assertIn("needs.puerta_02.result == 'success'", cond)
        self.assertIn("(github.actor != 'github-actions[bot]' || inputs.lanzado_por_eleccion)", cond)

    def test_eslabon_electoral_nunca_publica_y_lleva_el_origen(self):
        self.assertIn('-F "inputs[publish_result]=false"', self.script)
        self.assertNotIn("$PUBLISH", self.script)
        self.assertIn('inputs[cadena_origen_run_id]=$ORIGEN', self.script)
        self.assertNotIn("inputs[cadena_electoral]", self.script)  # el relanzamiento no vuelve a encadenar
        self.assertEqual(self.job["env"]["ORIGEN"], "${{ github.run_id }}")

    def test_sin_duplicados_y_parada_con_causa(self):
        self.assertIn("CHAIN_DUPLICATE_SKIPPED", self.script)
        self.assertIn('en_curso preparacion-legislatura-vigente.yml "$titulo_activacion"', self.script)
        self.assertIn('en_curso ejecucion-completa-proyecto.yml "P00 Campaña · $TERRITORY ·"', self.script)
        self.assertIn('en_curso ejecucion-completa-proyecto.yml "00 Ejecución Completa del Proyecto · $TERRITORY ·"', self.script)
        self.assertLess(self.script.index("duplicada="), self.script.index("ejecucion-completa-proyecto.yml/dispatches"))
        self.assertLess(self.script.index("exit 71"), self.script.index("ejecucion-completa-proyecto.yml/dispatches"))
        self.assertIn("paquete electoral caducado o par incompatible", self.script)
        subprocess.run(["bash", "-n"], input=self.script, text=True, check=True)

    def test_estado_de_cada_eslabon(self):
        self.assertIn("ddd.cadena-electoral/1.0", self.script)
        conservar = self.job["steps"][1]
        self.assertEqual(conservar["with"]["name"], "ddd-cadena-${{ github.run_id }}")
        self.assertEqual(conservar["if"], "${{ always() }}")

    def test_los_dispatch_del_bot_no_esperan_al_environment(self):
        # Decisión (c) del planificador con T-41 (#437): el clic del propietario solo en disparo manual humano.
        env = self.wf["jobs"]["planificar"]["environment"]
        self.assertIn("github.event_name == 'workflow_dispatch'", env)
        self.assertIn("github.actor != 'github-actions[bot]'", env)
        self.assertIn("github.actor != 'ddd-registro[bot]'", env)

    def test_manifiesto_guarda_la_cadena(self):
        texto = ORCH.read_text(encoding="utf-8")
        self.assertIn('--chain-origin-run-id "${CHAIN_ORIGIN_RUN_ID:-}"', texto)
        self.assertNotIn("${{ inputs.cadena_origen_run_id }}\"", texto.split("escribir_manifest_ejecucion_completa.py", 1)[1][:6000])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "m.json"
            base = ["--territory-id", "congreso_huesca", "--territory-name", "Congreso Huesca", "--edition", "2025",
                    "--execution-mode", "reuse", "--optimization-algorithm", "Canónico", "--workflow-run-id", "42",
                    "--source-sha", "a" * 40, "--publication-mode-requested", "electoral",
                    "--publication-mode-effective", "electoral", "--output", str(out),
                    "--chain-electoral-requested", "false", "--chain-origin-run-id", "41432561787",
                    "--publish-requested", "false", "--prepare-territorial-result", "skipped",
                    "--generate-result", "skipped", "--prepare-electoral-result", "success",
                    "--incorporate-result", "success", "--publish-result", "skipped",
                    "--prepare-territorial-executed", "false", "--generate-executed", "false",
                    "--prepare-electoral-executed", "true", "--incorporate-executed", "true"]
            r = subprocess.run([sys.executable, "herramientas/escribir_manifest_ejecucion_completa.py", *base],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr[-400:])
            chain = json.loads(out.read_text(encoding="utf-8"))["chain"]
            self.assertEqual(chain, {"electoral_chain_requested": False, "origin_run_id": 41432561787})


if __name__ == "__main__":
    unittest.main()
