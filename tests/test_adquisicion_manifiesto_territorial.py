from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from herramientas.ejecutar_fuentes_workflow import BUNDLE_NAME, _manifest_from_acquisition
from herramientas.gestionar_fuentes_checkpoint import execute_source_policy


class TerritorialAcquisitionManifestTests(unittest.TestCase):
    def evidence(self, root: Path, *, acquired_at="2026-10-01T12:00:00+00:00") -> Path:
        evidence = root / "evidence"
        materialized = evidence / "materialized" / "inputs"
        materialized.mkdir(parents=True)
        payload = b"territorial-source"
        (materialized / "population.zip").write_bytes(payload)
        inventory = {
            "sources": [{
                "source_id": "poblacion_por_sexo_y_edad",
                "availability": "AVAILABLE",
                "path": "inputs/population.zip",
                "bytes": len(payload),
                "sha256": "not-used-by-this-unit-test",
                "urls": ["https://official.example/65034"],
                "edition": 2023,
                "records": 1,
            }]
        }
        provenance_row = {
            "source_id": "poblacion_por_sexo_y_edad",
            "official_origin_url": "https://official.example/65034",
        }
        if acquired_at is not None:
            provenance_row["acquired_at_utc"] = acquired_at
        (evidence / "inventario_fuentes.json").write_text(
            json.dumps(inventory), encoding="utf-8"
        )
        (evidence / "manifiesto_procedencia.json").write_text(
            json.dumps({"sources": [provenance_row]}), encoding="utf-8"
        )
        (evidence / "decision_adquisicion.json").write_text(
            json.dumps({"decision": "READY", "reasons": []}), encoding="utf-8"
        )
        return evidence

    def manifest(self, evidence: Path, working: Path, acquisition: dict) -> dict:
        return _manifest_from_acquisition(
            evidence,
            working,
            "cantabria",
            2025,
            2023,
            2023,
            1,
            acquisition,
        )

    def test_failed_acquisition_preserves_original_reason_and_creates_no_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = self.evidence(root, acquired_at=None)
            working = root / "working"
            acquisition = {
                "decision": "BLOCKED",
                "reasons": [{
                    "source_id": "poblacion_por_sexo_y_edad",
                    "reason": "SECTION_ID_INVALID: evidencia original",
                }],
            }
            with self.assertRaisesRegex(RuntimeError, "SECTION_ID_INVALID: evidencia original"):
                self.manifest(evidence, working, acquisition)
            self.assertFalse((working / BUNDLE_NAME).exists())

    def test_material_validation_failure_creates_no_consumable_bundle_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = self.evidence(root)
            working = root / "working"
            checkpoint = root / "checkpoint"
            acquisition = {
                "decision": "BLOCKED",
                "reasons": [{
                    "source_id": "population_sectioning_compatibility",
                    "reason": "POPULATION_SECTIONING_MATERIAL_MISMATCH",
                }],
            }

            def downloader(target: Path) -> dict:
                return self.manifest(evidence, target, acquisition)

            with self.assertRaisesRegex(RuntimeError, "POPULATION_SECTIONING_MATERIAL_MISMATCH"):
                execute_source_policy(
                    requested_edition=2025,
                    working=working,
                    checkpoint_in=None,
                    checkpoint_out=checkpoint,
                    official_available=True,
                    downloader=downloader,
                    expected_records=None,
                )
            self.assertFalse((working / BUNDLE_NAME).exists())
            self.assertFalse(checkpoint.exists())

    def test_ready_acquisition_with_real_date_builds_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = self.evidence(root, acquired_at="2026-10-01T12:34:56+00:00")
            working = root / "working"
            manifest = self.manifest(
                evidence, working, {"decision": "READY", "reasons": []}
            )
            self.assertTrue((working / BUNDLE_NAME).is_file())
            self.assertEqual(manifest["acquired_at"], "2026-10-01T12:34:56+00:00")

    def test_ready_acquisition_without_date_is_rejected_before_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = self.evidence(root, acquired_at=None)
            working = root / "working"
            with self.assertRaisesRegex(RuntimeError, "sin fecha de adquisición interpretable"):
                self.manifest(evidence, working, {"decision": "READY", "reasons": []})
            self.assertFalse((working / BUNDLE_NAME).exists())

    def test_ready_acquisition_with_invalid_date_is_rejected_before_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evidence = self.evidence(root, acquired_at="fecha-invalida")
            working = root / "working"
            with self.assertRaises((ValueError, RuntimeError)):
                self.manifest(evidence, working, {"decision": "READY", "reasons": []})
            self.assertFalse((working / BUNDLE_NAME).exists())


if __name__ == "__main__":
    unittest.main()
