"""Regresiones P0: cola de GitHub, wiring y portfolio GerryChain 50."""
from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from herramientas.validar_portfolio_gerrychain50 import (
    PortfolioBlock, assignment_hash_from_zip, validate_directory,
)


ROOT = Path(__file__).resolve().parents[1]


class ConcurrencyQueueContract(unittest.TestCase):
    def test_all_existing_pending_groups_have_queue(self):
        workflows = ROOT / ".github" / "workflows"
        count = 0
        import re
        for path in workflows.glob("*.yml"):
            text = path.read_text(encoding="utf-8")
            for match in re.finditer(r"cancel-in-progress:[ \t]*false", text):
                near = text[match.end():match.end() + 80]
                self.assertRegex(near, r"queue:[ \t]*max", path.name)
                count += 1
        self.assertGreaterEqual(count, 24)

    def test_manual_gerrychain_50_wiring(self):
        for name in ("ejecucion-completa-proyecto.yml", "produccion-distritos.yml"):
            text = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
            self.assertIn("inputs.optimization_algorithm == 'GerryChain 50' && 'gerrychain_50'", text)
            self.assertIn("inputs.optimization_algorithm == 'GerryChain 50' || inputs.require_unique_hashes", text)

    def test_no_fallback_for_gerrychain_50(self):
        text = (ROOT / "procedimiento.sh").read_text(encoding="utf-8")
        self.assertIn('"GerryChain 50" "FAILED" false "gerrychain_runtime_failure"', text)
        self.assertIn('"GerryChain 50" "FAILED" false "gerrychain_portfolio_invalid"', text)
        self.assertIn("validar_portfolio_gerrychain50.py", text)


class GerryChain50PortfolioContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.rows = []
        for i in range(50):
            path = self.root / f"candidate_{i:03d}.geojson.zip"
            doc = {"type": "FeatureCollection", "features": [
                {"type": "Feature", "properties": {"CUSEC_KEY": "0100101001", "ddd_unit_id": "u1", "district_id": i + 1}, "geometry": None},
                {"type": "Feature", "properties": {"CUSEC_KEY": "0100101002", "ddd_unit_id": "u2", "district_id": 1}, "geometry": None},
            ]}
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("candidate.geojson", json.dumps(doc))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            ahash = assignment_hash_from_zip(path)
            self.rows.append({"geojson": str(path), "sha256": digest, "assignment_hash": ahash, "selected": i == 0})
        self.manifest = {"candidate_count": 50, "unique_candidate_count": 50,
                         "selected_assignment_hash": self.rows[0]["assignment_hash"], "candidates": self.rows}
        self._save()

    def _save(self):
        (self.root / "portfolio.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_valid_50_distinct_candidates(self):
        self.assertEqual(validate_directory(self.root)["decision"], "VALIDATED")

    def test_duplicate_assignment_rejected(self):
        self.manifest["candidates"][1]["assignment_hash"] = self.rows[0]["assignment_hash"]
        self._save()
        with self.assertRaises(PortfolioBlock):
            validate_directory(self.root)

    def test_missing_candidate_rejected(self):
        self.rows[49]["geojson"] = str(self.root / "missing.zip")
        self._save()
        with self.assertRaises(PortfolioBlock):
            validate_directory(self.root)

    def test_bad_zip_digest_rejected(self):
        self.rows[10]["sha256"] = "a" * 64
        self._save()
        with self.assertRaises(PortfolioBlock):
            validate_directory(self.root)

    def test_forged_assignment_hash_rejected(self):
        self.rows[10]["assignment_hash"] = "a" * 64
        self._save()
        with self.assertRaises(PortfolioBlock):
            validate_directory(self.root)


if __name__ == "__main__":
    unittest.main()
