from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows"
FULL = WF / "ejecucion-completa-proyecto.yml"


def load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


class FullRunSourceShaPinningTests(unittest.TestCase):
    def test_00_pins_checkout_sha_and_separates_prepared_from_enabled_ref(self):
        text = FULL.read_text(encoding="utf-8")
        full = load(FULL)
        jobs = full["jobs"]

        outputs = jobs["planificar"]["outputs"]
        self.assertEqual(outputs["source_sha"], "${{ steps.plan.outputs.source_sha }}")
        self.assertEqual(outputs["source_ref"], "${{ steps.plan.outputs.source_sha }}")
        self.assertIn('source_sha="$(git rev-parse HEAD)"', text)
        self.assertIn('echo "source_sha=$source_sha"', text)
        self.assertIn('echo "source_ref=$source_sha"', text)

        self.assertEqual(
            jobs["preparar_territorial"]["with"]["source_ref"],
            "${{ needs.planificar.outputs.source_sha }}",
        )

        prepared_ref = (
            "${{ needs.preparar_territorial.result == 'success' && "
            "needs.preparar_territorial.outputs.prepared_source_ref || "
            "needs.planificar.outputs.source_sha }}"
        )
        effective_ref = (
            "${{ needs.acreditar_generacion.result == 'success' && "
            "needs.acreditar_generacion.outputs.enabled_source_ref || "
            "(needs.preparar_territorial.result == 'success' && "
            "needs.preparar_territorial.outputs.prepared_source_ref || "
            "needs.planificar.outputs.source_sha) }}"
        )

        self.assertEqual(jobs["puerta_01"]["with"]["source_ref"], prepared_ref)
        self.assertEqual(
            jobs["acreditar_generacion"]["with"]["source_ref"],
            prepared_ref,
        )
        for name in (
            "generar",
            "puerta_02",
            "preparar_electoral",
            "puerta_03",
            "incorporar",
        ):
            with self.subTest(job=name):
                self.assertEqual(jobs[name]["with"]["source_ref"], effective_ref)

        self.assertIn(
            "needs.recuperar_electoral.outputs.source_commit",
            jobs["puerta_04"]["with"]["source_ref"],
        )
        self.assertIn(
            "needs.acreditar_generacion.outputs.enabled_source_ref",
            jobs["puerta_04"]["with"]["source_ref"],
        )
        self.assertIn(
            "needs.preparar_territorial.outputs.prepared_source_ref",
            jobs["puerta_04"]["with"]["source_ref"],
        )

        self.assertIn("acreditar_generacion", jobs["generar"]["needs"])
        self.assertIn(
            "needs.acreditar_generacion.result == 'success'",
            jobs["generar"]["if"],
        )
        self.assertNotIn(
            "pre_m04_accreditation_planned == 'true' && 'main'",
            jobs["generar"]["with"]["source_ref"],
        )
        self.assertIn(
            '--source-sha "${{ needs.planificar.outputs.source_sha }}"',
            jobs["manifestar"]["steps"][2]["run"],
        )

        for name in ("campaign_status", "manifestar"):
            checkout = next(
                step for step in jobs[name]["steps"]
                if str(step.get("uses", "")).startswith("actions/checkout@")
            )
            self.assertEqual(
                checkout["with"]["ref"],
                "${{ needs.planificar.outputs.source_sha }}",
            )

        state_checkout = next(
            step for step in jobs["actualizar_estado"]["steps"]
            if str(step.get("uses", "")).startswith("actions/checkout@")
        )
        self.assertIn("'main'", state_checkout["with"]["ref"])
        self.assertIn("needs.planificar.outputs.source_sha", state_checkout["with"]["ref"])

    def test_nested_reusables_preserve_code_ref_and_01_returns_prepared_not_enabled_ref(self):
        production = load(WF / "produccion-distritos.yml")
        incorporation = load(WF / "incorporacion-resultados-electorales.yml")
        preparation = load(WF / "preparacion-fuentes.yml")
        full = load(FULL)
        gate = load(WF / "_reutilizable-puerta-validacion.yml")

        self.assertEqual(
            production["jobs"]["ruta"]["with"]["source_ref"],
            "${{ inputs.source_ref }}",
        )
        self.assertEqual(
            incorporation["jobs"]["incorporar"]["with"]["source_ref"],
            "${{ inputs.source_ref }}",
        )

        self.assertNotIn("pre_m04", preparation["jobs"])
        self.assertIn("generation_pending", preparation["jobs"])
        prep_outputs = (
            ((preparation.get("on") or preparation.get(True) or {}).get("workflow_call") or {})
            .get("outputs")
            or {}
        )
        self.assertEqual(
            prep_outputs["prepared_source_ref"]["value"],
            "${{ jobs.generation_pending.outputs.prepared_source_ref }}",
        )
        self.assertNotIn("enabled_source_ref", prep_outputs)
        self.assertEqual(
            preparation["jobs"]["generation_pending"]["steps"][0]["with"]["ref"],
            "${{ needs.registrar.outputs.promotion_sha }}",
        )

        accreditation = full["jobs"]["acreditar_generacion"]
        self.assertTrue(accreditation["with"]["preflight_only"])
        self.assertEqual(
            accreditation["with"]["source_ref"],
            "${{ needs.preparar_territorial.result == 'success' && needs.preparar_territorial.outputs.prepared_source_ref || needs.planificar.outputs.source_sha }}",
        )

        gate_checkout = next(
            step for step in gate["jobs"]["validar"]["steps"]
            if str(step.get("uses", "")).startswith("actions/checkout@")
        )
        self.assertEqual(
            gate_checkout["with"]["ref"],
            "${{ inputs.source_ref || github.sha }}",
        )


if __name__ == "__main__":
    unittest.main()
