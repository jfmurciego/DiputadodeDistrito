from pathlib import Path
import unittest
from unittest.mock import patch

import yaml

from herramientas.resolver_ejecucion_completa import resolve_publication_mode

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"


class ElectoralDowngradeRegression(unittest.TestCase):
    def test_valid_territorial_execution_without_resolvable_election_stays_territorial(self):
        plan = {
            "territory_id": "demo",
            "territory_name": "Demo",
            "edition": "2025",
            "run_prepare_electoral": True,
            "run_incorporate": True,
        }
        with patch(
            "herramientas.resolver_eleccion_vigente.resolve",
            side_effect=SystemExit("No existe elección resoluble para territorio=Demo"),
        ):
            effective = resolve_publication_mode(plan, "electoral", root_dir=ROOT)

        self.assertEqual(effective, "territorial_only")
        plan["publication_mode"] = effective
        if effective == "territorial_only":
            plan["run_prepare_electoral"] = False
            plan["run_incorporate"] = False

        self.assertFalse(plan["run_prepare_electoral"])
        self.assertFalse(plan["run_incorporate"])

        workflow = yaml.safe_load(ORCH.read_text(encoding="utf-8")) or {}
        jobs = workflow["jobs"]

        self.assertIn(
            "needs.planificar.outputs.run_prepare_electoral == 'true'",
            jobs["preparar_electoral"]["if"],
        )
        self.assertIn(
            "needs.planificar.outputs.publication_mode == 'electoral'",
            jobs["puerta_03"]["if"],
        )
        self.assertIn("needs.puerta_03.result == 'success'", jobs["incorporar"]["if"])
        self.assertIn(
            "needs.planificar.outputs.run_incorporate == 'true'",
            jobs["incorporar"]["if"],
        )
        self.assertIn(
            "needs.planificar.outputs.publication_mode == 'electoral'",
            jobs["puerta_04"]["if"],
        )

        self.assertIn("puerta_02", jobs["actualizar_estado"]["needs"])
        self.assertIn(
            "needs.planificar.outputs.run_incorporate == 'false'",
            jobs["actualizar_estado"]["if"],
        )
        self.assertIn("puerta_02", jobs["publicar"]["needs"])
        self.assertIn("actualizar_estado", jobs["publicar"]["needs"])
        self.assertIn("needs.puerta_02.result == 'success'", jobs["publicar"]["if"])
        self.assertEqual(
            jobs["publicar"]["with"]["production_run_id"],
            "${{ needs.puerta_04.result == 'success' && needs.puerta_04.outputs.run_id || needs.puerta_02.outputs.run_id }}",
        )

    def test_no_post_plan_decision_reads_raw_publication_mode(self):
        lines = ORCH.read_text(encoding="utf-8").splitlines()
        plan_end = next(i for i, line in enumerate(lines) if line.startswith("  preparar_territorial:"))
        downstream = "\n".join(lines[plan_end:])
        self.assertNotIn("inputs.publication_mode", downstream)
        self.assertIn("needs.planificar.outputs.publication_mode", downstream)


if __name__ == "__main__":
    unittest.main()
