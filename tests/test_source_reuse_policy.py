from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from herramientas.politica_reutilizacion_fuentes import resolve_source_action


class SourceReusePolicyTests(unittest.TestCase):
    def prepared(self, root: Path, *, edition=2025, payload=b"a,b\n1,2\n", records=1):
        frozen = root / "frozen/source.csv"
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_bytes(payload)
        return {
            "source_id": "official",
            "edition": edition,
            "origin": "https://official.example/source.csv",
            "path": "frozen/source.csv",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "records": records,
            "acquired_at": "2026-09-17T18:00:00Z",
        }

    def test_resume_reuses_without_network(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = self.prepared(root)
            result = resolve_source_action(prepared_manifest=manifest, root=root, requested_edition=2025,
                                           official_available=False, expected_records=1)
            self.assertEqual(result["decision"], "REUSE")

    def test_prepared_edition_is_reused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = self.prepared(root)
            self.assertEqual(resolve_source_action(prepared_manifest=manifest, root=root,
                requested_edition=2025, official_available=True, expected_records=1)["decision"], "REUSE")

    def test_new_edition_acquires(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = self.prepared(root, edition=2024)
            self.assertEqual(resolve_source_action(prepared_manifest=manifest, root=root,
                requested_edition=2025, official_available=True)["decision"], "ACQUIRE")

    def test_damaged_copy_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = self.prepared(root)
            (root / manifest["path"]).write_bytes(b"tampered")
            result = resolve_source_action(prepared_manifest=manifest, root=root, requested_edition=2025,
                                           official_available=True, expected_records=1)
            self.assertEqual(result["decision"], "BLOCK")
            self.assertIn("dañada", result["reason"])

    def test_missing_official_source_blocks_clearly(self):
        with tempfile.TemporaryDirectory() as td:
            result = resolve_source_action(prepared_manifest=None, root=td, requested_edition=2025,
                                           official_available=False)
            self.assertEqual(result["decision"], "BLOCK")
            self.assertIn("fuente oficial no está disponible", result["reason"])

    def test_same_edition_uses_identical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = self.prepared(root)
            first = resolve_source_action(prepared_manifest=manifest, root=root, requested_edition=2025,
                                          official_available=False, expected_records=1)
            second = resolve_source_action(prepared_manifest=manifest, root=root, requested_edition=2025,
                                           official_available=False, expected_records=1)
            self.assertEqual(first["decision"], "REUSE")
            self.assertEqual(second["decision"], "REUSE")
            self.assertEqual(first["manifest"]["sha256"], second["manifest"]["sha256"])

    def test_explicit_update_acquires_and_unavailable_update_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); manifest = self.prepared(root)
            self.assertEqual(resolve_source_action(prepared_manifest=manifest, root=root, requested_edition=2025,
                official_available=True, force_update=True)["decision"], "ACQUIRE")
            self.assertEqual(resolve_source_action(prepared_manifest=manifest, root=root, requested_edition=2025,
                official_available=False, force_update=True)["decision"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
