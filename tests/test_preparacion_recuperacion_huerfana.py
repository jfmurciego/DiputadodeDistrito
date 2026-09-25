from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/preparacion-fuentes.yml"


class RecoverUnregisteredSourceContract(unittest.TestCase):
    def test_exact_recovery_never_uses_acquisition_or_unverified_history(self):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        event = workflow.get("on") or workflow.get(True)
        manual = event["workflow_dispatch"]["inputs"]
        reusable = event["workflow_call"]["inputs"]
        for inputs in (manual, reusable):
            self.assertIn("recover_run_id", inputs)
            self.assertIn("recover_artifact_sha256", inputs)

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
