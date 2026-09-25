from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
ORCH = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"


class TerritorialOnlyManualSelectorRegression(unittest.TestCase):
    def test_manual_selector_drives_existing_territorial_only_path(self):
        text = ORCH.read_text(encoding="utf-8")
        data = yaml.load(text, Loader=yaml.BaseLoader)
        selector = data["on"]["workflow_dispatch"]["inputs"]["publication_mode"]

        self.assertEqual(selector["type"], "choice")
        self.assertEqual(selector["default"], "electoral")
        self.assertEqual(selector["options"], ["electoral", "territorial_only"])

        # El selector manual alimenta la lógica territorial_only ya existente en main;
        # esta PR no sustituye puertas electorales ni implementa un segundo downgrade.
        self.assertIn(
            "PUBLICATION_MODE: ${{ github.event_name == 'pull_request' && 'electoral' || inputs.publication_mode || 'electoral' }}",
            text,
        )
        self.assertIn('if publication_mode=="territorial_only":', text)
        self.assertIn('p["run_prepare_electoral"]=False', text)
        self.assertIn('p["run_incorporate"]=False', text)

        jobs = data["jobs"]
        self.assertIn(
            "needs.planificar.outputs.run_prepare_electoral == 'true'",
            jobs["preparar_electoral"]["if"],
        )
        self.assertIn("puerta_02", jobs["publicar"]["needs"])
        self.assertEqual(
            jobs["publicar"]["with"]["production_run_id"],
            "${{ needs.puerta_04.result == 'success' && needs.puerta_04.outputs.run_id || needs.puerta_02.outputs.run_id }}",
        )


if __name__ == "__main__":
    unittest.main()
