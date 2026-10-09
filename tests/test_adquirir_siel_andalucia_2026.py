from __future__ import annotations

import csv
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "herramientas/adquirir_siel_andalucia_2026.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ddd_siel_acquisition", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class SielSectionLocatorTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def _write_locator(self, path: Path) -> None:
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "codigo_provincia", "codigo_municipio", "codigo_distrito",
                    "codigo_seccion", "partido", "votos",
                ],
            )
            writer.writeheader()
            writer.writerow({"codigo_provincia":"04","codigo_municipio":"029","codigo_distrito":"01","codigo_seccion":"006","partido":"PP","votos":"999999"})
            writer.writerow({"codigo_provincia":"04","codigo_municipio":"029","codigo_distrito":"01","codigo_seccion":"006","partido":"PSOE-A","votos":"1"})
            writer.writerow({"codigo_provincia":"11","codigo_municipio":"001","codigo_distrito":"02","codigo_seccion":"12","partido":"X","votos":"123"})

    def test_provisional_file_is_used_only_as_unique_section_locator(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "locator.csv"
            self._write_locator(path)
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            tasks, meta = self.module.load_section_locator(path, expected_sha256=digest, expected_sections=2)
            self.assertEqual(tasks, [("4","29","1","0006"), ("11","1","2","0012")])
            self.assertEqual(meta["source_class"], "PROVISIONAL")
            self.assertEqual(meta["role"], "SECTION_LOCATOR_ONLY")
            self.assertFalse(meta["votes_consumed"])
            self.assertEqual(meta["sections"], 2)

    def test_checkpoint_identity_allows_same_locator_resume(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            locator = {
                "sha256": "a" * 64,
                "sections": 2,
            }
            checkpoint, meta = self.module._prepare_checkpoint(root, locator, resume=False)
            checkpoint.mkdir(parents=True, exist_ok=True)
            checkpoint2, meta2 = self.module._prepare_checkpoint(root, locator, resume=True)
            self.assertEqual(checkpoint2, checkpoint)
            self.assertEqual(meta2, meta)

    def test_checkpoint_identity_rejects_other_locator(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = {"sha256": "a" * 64, "sections": 2}
            checkpoint, _ = self.module._prepare_checkpoint(root, first, resume=False)
            checkpoint.mkdir(parents=True, exist_ok=True)
            with self.assertRaisesRegex(ValueError, "otra identidad o índice"):
                self.module._prepare_checkpoint(
                    root,
                    {"sha256": "b" * 64, "sections": 2},
                    resume=True,
                )


    def test_checkpoint_roundtrip_and_resume_rows(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkpoint = root / ".checkpoint-sections"
            task1 = ("4", "29", "1", "0006")
            task2 = ("11", "1", "2", "0012")
            votes = [{"party": "PP", "votes": 10}, {"party": "PSOE-A", "votes": 7}]
            self.module._write_checkpoint(checkpoint, task1, votes)
            rows, completed = self.module._load_checkpoint(checkpoint, [task1, task2])
            self.assertEqual(completed, {task1})
            self.assertEqual(
                rows,
                [
                    {"province":"4","municipality":"29","district":"1","section":"0006","party":"PP","votes":10},
                    {"province":"4","municipality":"29","district":"1","section":"0006","party":"PSOE-A","votes":7},
                ],
            )

    def test_checkpoint_from_other_locator_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            checkpoint = root / ".checkpoint-sections"
            foreign = ("4", "99", "1", "0001")
            self.module._write_checkpoint(checkpoint, foreign, [{"party":"PP","votes":1}])
            with self.assertRaisesRegex(ValueError, "ajeno al índice actual"):
                self.module._load_checkpoint(checkpoint, [("4","29","1","0006")])


    def test_changed_locator_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "locator.csv"
            self._write_locator(path)
            with self.assertRaisesRegex(ValueError, "Huella gobernada"):
                self.module.load_section_locator(path, expected_sha256="0" * 64, expected_sections=2)


if __name__ == "__main__":
    unittest.main()
