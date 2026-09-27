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

    def test_changed_locator_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "locator.csv"
            self._write_locator(path)
            with self.assertRaisesRegex(ValueError, "Huella gobernada"):
                self.module.load_section_locator(path, expected_sha256="0" * 64, expected_sections=2)


if __name__ == "__main__":
    unittest.main()
