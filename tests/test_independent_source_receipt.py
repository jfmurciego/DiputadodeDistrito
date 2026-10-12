"""Regresión F10 v1.0.0 — evidencia fuente independiente sin cambio de linaje.

Fecha: 2026-10-12; alcance: puerta de receipt #179.
Motivo: admitir una fuente auténtica no promovida sin reemplazar el source run
        que sustenta un producto territorial existente.
Predecesor: nueva regresión para la separación de receipts; no existía caso equivalente.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herramientas import consumir_par_fuentes_legislatura as consumer
from herramientas.identidad_fuentes_legislatura import territorial_identity


class IndependentSourceReceiptTests(unittest.TestCase):
    def make_row(self, root: Path, *, promoted: bool = False) -> tuple[dict, dict]:
        package_sha = "a" * 64
        compatibility_sha = "b" * 64
        report_sha = "c" * 64
        identity = territorial_identity(
            territory_id="extremadura",
            edition="2025",
            population_year=2025,
            section_year=2025,
            package_sha256=package_sha,
            compatibility_identity_sha256=compatibility_sha,
        )
        receipt = {
            "schema": "ddd.territorial-source-receipt/1.0",
            "kind": "territorial_source",
            "territory_id": "extremadura",
            "edition": "2025",
            "run_id": 38091144559,
            "artifact_name": "ddd-source-package-extremadura-2025-38091144559",
            "artifact_sha256": "d" * 64,
            "package_sha256": package_sha,
            "population_year": 2025,
            "section_year": 2025,
            "territorial_identity_sha256": identity["territorial_identity_sha256"],
            "compatibility_report_member": consumer.REPORT_NAME,
            "compatibility_report_sha256": report_sha,
            "compatibility_identity_sha256": compatibility_sha,
        }
        receipt_path = root / "independent-receipt.json"
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        historic = {
            "run_id": 35755043806,
            "package_sha256": "e" * 64,
            "source_role": "historical_product_source",
        }
        independent = {
            **{key: receipt[key] for key in (
                "run_id", "artifact_name", "artifact_sha256", "package_sha256",
                "population_year", "section_year", "territorial_identity_sha256",
                "compatibility_report_member", "compatibility_report_sha256",
                "compatibility_identity_sha256",
            )},
            "receipt_path": str(receipt_path),
            "status": "AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED",
            "promoted": promoted,
        }
        row = {
            "territory_id": "extremadura",
            "name": "Extremadura",
            "territorial_sources_prepared": True,
            "preparation_evidence": historic,
            "independent_source_evidence": independent,
        }
        return row, receipt

    def test_independent_receipt_is_consumed_without_overwriting_historic_preparation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            row, expected = self.make_row(root)
            with mock.patch.object(consumer, "_catalog_row", return_value=row):
                actual_row, receipt = consumer.validate_territorial_receipt(
                    root_dir=root, territory="extremadura", edition="2025"
                )
            self.assertEqual(expected, receipt)
            self.assertEqual(35755043806, actual_row["preparation_evidence"]["run_id"])
            self.assertEqual(
                "AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED",
                actual_row["independent_source_evidence"]["status"],
            )

    def test_promoted_or_unclassified_independent_receipt_fails_closed(self):
        for promoted, status in ((True, "AUTHENTIC_EVIDENCE_ONLY_HISTORICAL_PRODUCT_LINEAGE_PRESERVED"),
                                 (False, "READY")):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                row, _ = self.make_row(root, promoted=promoted)
                row["independent_source_evidence"]["status"] = status
                with mock.patch.object(consumer, "_catalog_row", return_value=row):
                    with self.subTest(promoted=promoted, status=status), self.assertRaisesRegex(
                        consumer.PreparedPairExecutionBlock, "evidencia auténtica no promovida"
                    ):
                        consumer.validate_territorial_receipt(
                            root_dir=root, territory="extremadura", edition="2025"
                        )


if __name__ == "__main__":
    unittest.main()
