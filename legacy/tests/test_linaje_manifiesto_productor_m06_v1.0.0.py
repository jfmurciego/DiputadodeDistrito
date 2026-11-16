"""Versión 1.0.0; 2026-10-29; candidato. Reutilización M06 con linaje desde el manifiesto del productor.
Origen: nuevo, sin predecesor.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herramientas import consumir_par_fuentes_legislatura as consumer

SOURCE = {
    "run_id": 40691712762,
    "artifact_name": "ddd-source-package-demo-2025-40691712762",
    "artifact_sha256": "a" * 64,
}
IDENTITY = "b" * 64


def _write(root: Path, rel: str, data: dict) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return rel


class ProducerManifestLineageTests(unittest.TestCase):
    def _reuse(self, *, current_source: dict | None, manifest_run: int = 40691712762) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = _write(root, "territorios/demo/evidencia/generaciones_m06/m.json", {
                "identity": {"workflow_run_id": manifest_run},
                "inputs": {"source_package_artifact": dict(SOURCE)},
                "artifacts": {"m06": {"artifact_sha256": "c" * 64}},
            })
            product = _write(root, "territorios/demo/evidencia/catalogo/territorial_product_2025.json", {
                "run_id": 40691712762,
                "artifact_name": "ddd-state-40691712762-M06",
                "artifact_sha256": "c" * 64,
                "producer_manifest_path": manifest,
            })
            row = {"territorial_product_available": True, "evidence": {"territorial_product": product}}
            with mock.patch.object(consumer, "_catalog_row", return_value=row):
                return consumer.resolve_geometric_reuse(
                    root_dir=root, territory_id="demo", edition="2025",
                    current_identity=IDENTITY, current_source=current_source,
                )

    def test_same_source_package_is_reusable(self):
        reuse = self._reuse(current_source=dict(SOURCE))
        self.assertTrue(reuse["compatible"])
        self.assertEqual(reuse["reason"], "SOURCE_PRODUCER_MANIFEST_MATCH")
        self.assertEqual(reuse["product_run_id"], 40691712762)

    def test_other_source_package_keeps_block(self):
        reuse = self._reuse(current_source={**SOURCE, "artifact_sha256": "d" * 64})
        self.assertFalse(reuse["compatible"])
        self.assertEqual(reuse["reason"], "PRODUCT_SOURCE_LINEAGE_MISSING")

    def test_manifest_from_other_run_keeps_block(self):
        reuse = self._reuse(current_source=dict(SOURCE), manifest_run=1)
        self.assertEqual(reuse["reason"], "PRODUCT_SOURCE_LINEAGE_MISSING")

    def test_without_current_source_keeps_block(self):
        self.assertEqual(self._reuse(current_source=None)["reason"], "PRODUCT_SOURCE_LINEAGE_MISSING")


if __name__ == "__main__":
    unittest.main()
