"""Versión 1.0.2; 2026-11-01; candidato. Encadenado automático del par de fuentes hasta la 04 en el 00.
Cambios: 1.0.2 (T-12) el encadenado exige la puerta 02 en success (sin M06 registrado no se encadena).
  1.0.1 el encadenado también aplica en modo reutilizar; el bucle se evita porque el relanzamiento lo dispara github-actions[bot].
Anterior: legacy/tests/test_00_encadenado_par_v1.0.1_20261101.py
"""
from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github/workflows/ejecucion-completa-proyecto.yml"
ACTIVATION = ROOT / ".github/workflows/preparacion-legislatura-vigente.yml"


class EncadenadoParTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wf = yaml.safe_load(ORCH.read_text(encoding="utf-8"))
        cls.job = cls.wf["jobs"]["encadenar_par_y_04"]

    def test_only_after_missing_pair_and_never_from_chained_relaunch(self):
        cond = self.job["if"]
        self.assertIn("needs.clasificar_electoral.outputs.completion_status == 'SKIPPED_NO_ACCREDITED_PAIR'", cond)
        # El modo por defecto es reutilizar: no puede excluir el encadenado.
        self.assertNotIn("execution_mode_internal", cond)
        self.assertIn("github.actor != 'github-actions[bot]'", cond)
        self.assertIn("github.event_name == 'workflow_dispatch'", cond)
        self.assertIn("github.ref_name == 'main'", cond)
        self.assertIn("needs.manifestar.result == 'success'", cond)
        self.assertEqual({"planificar", "puerta_02", "clasificar_electoral", "manifestar"}, set(self.job["needs"]))

    def test_requires_registered_territorial_product(self):
        # T-12: Congreso Álava 41335088773 encadenó con «Registrar producto territorial» en failure
        # y la puerta 02 en skipped; sin M06 registrado no se activa el par ni se relanza el 00.
        self.assertIn("needs.puerta_02.result == 'success'", self.job["if"])

    def test_minimal_permissions_and_relaunch_in_reuse_mode(self):
        self.assertEqual({"actions": "write", "contents": "read"}, self.job["permissions"])
        run = self.job["steps"][0]["run"]
        self.assertIn("preparacion-legislatura-vigente.yml/dispatches", run)
        self.assertIn('inputs[operation]=prepare_one', run)
        self.assertIn('inputs[execution_mode]=Reutilizar progreso existente', run)
        self.assertLess(run.index("exit 71"), run.index("ejecucion-completa-proyecto.yml/dispatches"))

    def test_activation_run_is_identified_by_territory(self):
        activation = yaml.safe_load(ACTIVATION.read_text(encoding="utf-8"))
        self.assertIn("inputs.territory", activation["run-name"])
        self.assertIn("inputs.operation", activation["run-name"])
        run = self.job["steps"][0]["run"]
        self.assertIn("Activación de Legislatura Vigente · $TERRITORY · prepare_one", run)


if __name__ == "__main__":
    unittest.main()
