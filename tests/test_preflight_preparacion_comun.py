from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.preflight_preparacion_fuente import preflight

ROOT = Path(__file__).resolve().parents[1]
WF01 = ROOT / ".github" / "workflows" / "preparacion-fuentes.yml"
WF03 = ROOT / ".github" / "workflows" / "preparacion-resultados-electorales.yml"
WF00 = ROOT / ".github" / "workflows" / "ejecucion-completa-proyecto.yml"


def write_catalog(root: Path, state: dict):
    path = root / "configuracion" / "catalogo_preparacion.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "schema": "ddd-preparation-catalog/1.1",
                "default_edition": "2025",
                "territories": [
                    {
                        "territory_id": "demo",
                        "name": "Demo",
                        "editions": {"2025": state},
                    }
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


class CommonPreparationPreflightTests(unittest.TestCase):
    def test_territorial_registered_source_requires_complete_registry_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            digest = "a" * 64
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": False,
                    "preparation_evidence": {
                        "run_id": 123,
                        "artifact_name": "ddd-source-package-demo-2025-123",
                        "artifact_sha256": digest,
                    },
                },
            )
            result = preflight(root, "territorial", "Demo", "2025")
            self.assertTrue(result["registered"])
            self.assertEqual(result["run_id"], 123)
            self.assertEqual(result["artifact_sha256"], digest)

    def test_territorial_prepared_without_registry_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": False,
                },
            )
            with self.assertRaisesRegex(ValueError, "sin preparation_evidence"):
                preflight(root, "territorial", "Demo", "2025")

    def test_electoral_registered_source_requires_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt = root / "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text(
                json.dumps(
                    {
                        "schema": "ddd.catalog-evidence/1.0",
                        "kind": "electoral_source",
                        "territory_id": "demo",
                        "edition": "2025",
                        "run_id": 456,
                        "artifact_name": "ddd-electoral-package-demo-2025-456",
                        "artifact_sha256": "b" * 64,
                        "election_id": "demo_2024",
                    }
                ),
                encoding="utf-8",
            )
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": True,
                    "evidence": {
                        "electoral_source": "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
                    },
                },
            )
            result = preflight(root, "electoral", "demo", "2025")
            self.assertTrue(result["registered"])
            self.assertEqual(result["run_id"], 456)
            self.assertEqual(result["election_id"], "demo_2024")

    def test_electoral_prepared_with_missing_receipt_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": True,
                    "electoral_source_prepared": True,
                    "evidence": {
                        "electoral_source": "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
                    },
                },
            )
            with self.assertRaisesRegex(ValueError, "registro electoral inexistente"):
                preflight(root, "electoral", "Demo", "2025")

    def test_unprepared_source_has_no_fabricated_registered_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_catalog(
                root,
                {
                    "territorial_sources_prepared": False,
                    "electoral_source_prepared": False,
                },
            )
            self.assertFalse(preflight(root, "territorial", "Demo", "2025")["registered"])
            self.assertFalse(preflight(root, "electoral", "Demo", "2025")["registered"])

    def test_00_passes_same_edition_into_03(self):
        data = yaml.safe_load(WF00.read_text(encoding="utf-8"))
        self.assertEqual(
            data["jobs"]["preparar_electoral"]["with"]["data_edition"],
            "${{ needs.planificar.outputs.edition }}",
        )

    def test_01_reuse_path_skips_all_acquisition_steps(self):
        data = yaml.safe_load(WF01.read_text(encoding="utf-8"))
        steps = data["jobs"]["territoriales"]["steps"]
        gated = [
            next(step for step in steps if str(step.get("uses", "")).startswith("docker/setup-buildx-action@")),
            next(step for step in steps if str(step.get("uses", "")).startswith("docker/build-push-action@")),
            next(step for step in steps if step.get("id") == "mode"),
            next(step for step in steps if step.get("name") == "Adquirir y congelar fuentes"),
        ]
        for step in gated:
            self.assertIn("reused_candidate != 'true'", step["if"])

    def test_03_reuse_path_feeds_downloaded_package_into_reuse_engine(self):
        data = yaml.safe_load(WF03.read_text(encoding="utf-8"))
        steps = data["jobs"]["electorales"]["steps"]
        previous = next(step for step in steps if step.get("id") == "previous")
        prepare = next(step for step in steps if step.get("id") == "prepare")
        self.assertIn("REGISTERED_ARTIFACT_SHA256", previous["run"])
        self.assertIn("--previous-package .ddd-electoral-previous", prepare["run"])
        self.assertIn("--previous-run-id", prepare["run"])
        self.assertIn("--previous-artifact-name", prepare["run"])


if __name__ == "__main__":
    unittest.main()
