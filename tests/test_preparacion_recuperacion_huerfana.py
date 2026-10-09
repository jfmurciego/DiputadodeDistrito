from pathlib import Path
import unittest
import yaml

from herramientas.evaluar_persistencia_preparacion import resolve_persist_state
from herramientas.catalogo_territorios import format_territory_label, load_master, normalize_territory_input

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-fuentes.yml"
CURRENT = ROOT / "configuracion/preparacion_legislatura_vigente.yaml"
MASTER = ROOT / "configuracion/catalogo_territorios_espana_2025.yaml"


class RecoverUnregisteredSourceContract(unittest.TestCase):
    def test_recovery_requires_effective_persistence_for_manual_and_workflow_call(self):
        self.assertTrue(resolve_persist_state(None))
        self.assertFalse(resolve_persist_state(False))

        def accepted(*, recovery_requested: bool, persist_requested):
            effective = resolve_persist_state(persist_requested)
            return (not recovery_requested) or effective

        matrix = [
            (True, None, True),
            (True, False, False),
            (True, True, True),
            (False, False, True),
        ]
        for recovery_requested, persist_requested, expected in matrix:
            with self.subTest(recovery_requested=recovery_requested, persist_requested=persist_requested):
                self.assertEqual(
                    accepted(
                        recovery_requested=recovery_requested,
                        persist_requested=persist_requested,
                    ),
                    expected,
                )

        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        resolver = next(
            step for step in workflow["jobs"]["resolver"]["steps"] if step.get("id") == "resolve"
        )
        body = resolver["run"]
        self.assertIn("La recuperación durable exige persist_state=true.", body)
        self.assertIn(
            "[[ \"$(jq -r '.persist_state|tostring' <<<\"$persist_json\")\" == true ]]",
            body,
        )
        self.assertLess(
            body.index("La recuperación durable exige persist_state=true."),
            body.index("registered_run_id=$RECOVERY_RUN_ID"),
        )

    def test_manual_selector_resolves_all_19_current_territories(self):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        event = workflow.get("on") or workflow.get(True)
        options = event["workflow_dispatch"]["inputs"]["territory_id"]["options"]
        current = yaml.safe_load(CURRENT.read_text(encoding="utf-8")) or {}
        rows = current.get("territories") or []

        self.assertEqual(len(options), 19)
        self.assertEqual(len(rows), 19)

        expected = [format_territory_label(row) for row in load_master(MASTER)]
        self.assertEqual(options, expected)
        self.assertTrue(all(" · " not in option for option in options))

        normalized = [normalize_territory_input(option) for option in options]
        configured = [str(row.get("name") or "").strip() for row in rows]
        self.assertEqual(set(normalized), set(configured))
        self.assertEqual(len(set(normalized)), 19)

        for option, wanted in zip(options, normalized):
            with self.subTest(option=option):
                matches = [
                    row for row in rows
                    if str(row.get("name") or "").strip() == wanted
                    or str(row.get("territory_id") or "").strip() == wanted
                ]
                self.assertEqual(len(matches), 1)

        resolver = next(
            step for step in workflow["jobs"]["resolver"]["steps"] if step.get("id") == "resolve"
        )
        body = resolver["run"]
        self.assertIn(
            'resolver_preparacion_legislatura.py --root-dir . --territory "$TERRITORY"',
            body,
        )
        self.assertIn(".population_year_selected", body)
        self.assertIn(".section_year_selected", body)
        self.assertIn('TERRITORY="$(jq -r .territory_id <<<"$plan")"', body)
        self.assertNotIn("population_current_year", body)
        self.assertNotIn("section_current_year", body)

    def test_exact_recovery_never_uses_acquisition_or_unverified_history(self):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        event = workflow.get("on") or workflow.get(True)
        manual = event["workflow_dispatch"]["inputs"]
        reusable = event["workflow_call"]["inputs"]
        self.assertEqual(list(manual), ["territory_id"])
        self.assertNotIn("recover_run_id", manual)
        self.assertNotIn("recover_artifact_sha256", manual)
        self.assertIn("recover_run_id", reusable)
        self.assertIn("recover_artifact_sha256", reusable)

        jobs = workflow["jobs"]
        resolver = next(step for step in jobs["resolver"]["steps"] if step.get("id") == "resolve")
        body = resolver["run"]
        self.assertIn('[[ -n "$RECOVERY_RUN_ID" && -n "$RECOVERY_SHA256" ]]', body)
        self.assertIn('[[ "$RECOVERY_SHA256" =~ ^[a-fA-F0-9]{64}$ ]]', body)
        self.assertIn('[[ "$(jq -r \'.registered\' <<<"$preflight")" == false ]]', body)
        self.assertIn('ddd-source-package-$(jq -r .territory_id <<<"$row")-$EDITION-$RECOVERY_RUN_ID', body)

        steps = jobs["territoriales"]["steps"]
        recovery = next(step for step in steps if step.get("id") == "previous")
        download = recovery["run"]
        self.assertIn('actions/runs/$REGISTERED_RUN_ID/artifacts', download)
        self.assertIn('length==1', download)
        self.assertIn('"$actual_digest" == "$REGISTERED_ARTIFACT_SHA256"', download)
        self.assertIn('gh run download "$REGISTERED_RUN_ID"', download)
        self.assertNotIn("actions/runs?status=completed", download)
        self.assertTrue(all(
            "steps.previous.outputs.reused_candidate != 'true'" in str(step.get("if"))
            for step in steps
            if step.get("name") == "Adquirir y congelar fuentes"
            or "docker/build-push-action" in str(step.get("uses"))
            or "docker/setup-buildx-action" in str(step.get("uses"))
        ))
        self.assertIn("needs.resolver.outputs.persist_state == 'true'", jobs["registrar"]["if"])
        self.assertIn("always()", jobs["resultado"]["if"])


if __name__ == "__main__":
    unittest.main()
