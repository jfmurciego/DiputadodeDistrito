"""Versión 1.0.0; 2026-10-29; candidato. El detector de M08 huérfano lee los receipts donde el catálogo los declara.
Origen: nuevo, sin predecesor.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import yaml

from herramientas.detectar_producto_electoral_huerfano import _receipt


class DeclaredReceiptTests(unittest.TestCase):
    def test_electoral_source_follows_catalog_evidence_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "territorios/demo/evidencia/fuentes_electorales/2025/x/123/receipt.json"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text(json.dumps({"run_id": 123}), encoding="utf-8")
            (root / "configuracion").mkdir()
            (root / "configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump({"territories": [
                {"territory_id": "demo", "editions": {"2025": {"evidence": {"electoral_source": rel}}}},
            ]}), encoding="utf-8")
            self.assertEqual(123, _receipt(root, "demo", "2025", "electoral_source")["run_id"])
            self.assertEqual({}, _receipt(root, "demo", "2025", "electoral_product"))

    def test_catalog_directory_receipt_keeps_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "territorios/demo/evidencia/catalogo/electoral_source_2025.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"run_id": 7}), encoding="utf-8")
            self.assertEqual(7, _receipt(root, "demo", "2025", "electoral_source")["run_id"])


if __name__ == "__main__":
    unittest.main()
