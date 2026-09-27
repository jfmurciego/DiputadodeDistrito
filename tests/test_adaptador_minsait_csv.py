from __future__ import annotations

import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "herramientas/adaptador_minsait_csv.py"


def load_adapter():
    spec = importlib.util.spec_from_file_location("ddd_minsait_csv", ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class MinsaitCsvAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = load_adapter()

    def _source(self, root: Path) -> Path:
        path = root / "source.csv"
        fields = [
            "codigo_ccaa","codigo_provincia","codigo_municipio","codigo_distrito",
            "codigo_seccion","codigo_mesa","partido","votos"
        ]
        provinces = ("04","11","14","18","21","23","29","41")
        with path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            for i, prov in enumerate(provinces, 1):
                w.writerow({
                    "codigo_ccaa":"01","codigo_provincia":prov,"codigo_municipio":str(i),
                    "codigo_distrito":"1","codigo_seccion":"1","codigo_mesa":"A",
                    "partido":"P1","votos":str(i),
                })
        return path

    def test_builds_provisional_non_production_package(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self._source(root)
            out = root / "package"
            manifest = self.adapter.build(
                source, out,
                territory_id="andalucia",
                election_id="andalucia_parlamento_2026",
                election_date="2026-05-17",
                edition="2025",
                expected_sha256=self.adapter.sha256(source),
                expected_ccaa="01",
                expected_sections=8,
                expected_polling_stations=8,
                expected_candidate_votes=36,
                source_url="https://example.invalid/source.csv",
                publisher="Minsait mirror",
            )
            self.assertEqual(manifest["decision"], "ACQUIRE")
            self.assertEqual(manifest["source_status"], "PROVISIONAL")
            self.assertFalse(manifest["production_eligible"])
            self.assertEqual(manifest["sections"], 8)
            self.assertEqual(manifest["polling_stations"], 8)
            self.assertEqual(manifest["candidate_votes"], 36)
            contract = json.loads((out / "contract/election_contract.json").read_text(encoding="utf-8"))
            self.assertEqual(contract["source_verification"]["status"], "PROVISIONAL")
            self.assertFalse(contract["source_verification"]["production_eligible"])

    def test_rejects_wrong_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = self._source(root)
            with self.assertRaisesRegex(ValueError, "SHA-256 Minsait no coincide"):
                self.adapter.build(
                    source, root / "package",
                    territory_id="andalucia",
                    election_id="andalucia_parlamento_2026",
                    election_date="2026-05-17",
                    edition="2025",
                    expected_sha256="0" * 64,
                    expected_ccaa="01",
                    expected_sections=8,
                    expected_polling_stations=8,
                    expected_candidate_votes=36,
                    source_url="https://example.invalid/source.csv",
                    publisher="Minsait mirror",
                )


if __name__ == "__main__":
    unittest.main()
