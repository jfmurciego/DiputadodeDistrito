from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from herramientas.seleccionar_checkpoint_productivo import select_latest_valid


class ProductiveCheckpointSelectorTests(unittest.TestCase):
    def prepare_root(self, root: Path):
        (root / "territorios/demo/config").mkdir(parents=True)
        (root / "territorios/demo/config/fuentes_oficiales.yaml").write_text(
            "territory:\n  id: demo\n  edition: 2025\ncoverage_checks:\n  expected_sections: 1\n",
            encoding="utf-8",
        )
        params = root / "params.yaml"
        params.write_text("meta:\n  territory_id: demo\n", encoding="utf-8")
        return params

    def package(self, root: Path, name: str, *, payload: bytes = b"id,value\n1,x\n",
                edition: int = 2025, corrupt_hash: bool = False) -> Path:
        package = root / name
        frozen = package / "prepared_sources.zip"
        frozen.parent.mkdir(parents=True, exist_ok=True)
        frozen.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        if corrupt_hash:
            digest = "0" * 64
        manifest = {
            "source_id": "prepared-territorial-sources:official",
            "edition": edition,
            "origin": "https://official.example/source.csv",
            "path": "prepared_sources.zip",
            "bytes": len(payload),
            "sha256": digest,
            "records": 1,
            "acquired_at": "2026-09-17T19:00:00Z",
        }
        (package / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return package

    def test_manifest_present_and_valid_copy_is_selected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            valid = self.package(root, "valid")
            result = select_latest_valid(
                params=params,
                candidates=[{"run_id": 200, "stage": "M06", "from_stage": "M07", "package": valid}],
                root_dir=root,
            )
            self.assertEqual(result["selected"]["run_id"], "200")
            self.assertEqual(result["from_stage"], "M07")
            self.assertEqual(result["discarded"], [])

    def test_manifest_present_but_wrong_checksum_is_discarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            bad = self.package(root, "bad", corrupt_hash=True)
            result = select_latest_valid(
                params=params,
                candidates=[{"run_id": 201, "stage": "M06", "from_stage": "M07", "package": bad}],
                root_dir=root,
            )
            self.assertIsNone(result["selected"])
            self.assertIn("checksum incorrecto", result["discarded"][0]["reason"])
            self.assertEqual(result["from_stage"], "M01")

    def test_wrong_edition_is_discarded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            bad = self.package(root, "bad-edition", edition=2024)
            result = select_latest_valid(
                params=params,
                candidates=[{"run_id": 202, "stage": "M05", "from_stage": "M06", "package": bad}],
                root_dir=root,
            )
            self.assertIsNone(result["selected"])
            self.assertIn("Fuentes BLOQUEADAS", result["discarded"][0]["reason"])

    def test_newest_invalid_falls_back_to_previous_valid(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            newest = self.package(root, "newest", corrupt_hash=True)
            older = self.package(root, "older")
            result = select_latest_valid(
                params=params,
                candidates=[
                    {"run_id": 300, "stage": "M06", "from_stage": "M07", "package": newest},
                    {"run_id": 250, "stage": "M05", "from_stage": "M06", "package": older},
                ],
                root_dir=root,
            )
            self.assertEqual(result["selected"]["run_id"], "250")
            self.assertEqual([d["run_id"] for d in result["discarded"]], ["300"])
            self.assertEqual(result["from_stage"], "M06")

    def test_no_compatible_checkpoint_starts_from_m01(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); params = self.prepare_root(root)
            result = select_latest_valid(params=params, candidates=[], root_dir=root)
            self.assertIsNone(result["selected"])
            self.assertEqual(result["discarded"], [])
            self.assertEqual(result["from_stage"], "M01")


if __name__ == "__main__":
    unittest.main()
