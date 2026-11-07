"""Pruebas de integridad del lector ZIP. Versión 1.0.0, 2026-11-03; nuevo."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from verificar_portfolio_zip import verify


def make_archive(path, corrupt=False, duplicate=False, missing=False):
    rows = []
    with zipfile.ZipFile(path, "w") as archive:
        for i in range(2):
            district = str(1 if duplicate else i + 1)
            assignment = [["u", district]]
            identity = hashlib.sha256(json.dumps(assignment, separators=(",", ":")).encode()).hexdigest()
            feature = {"type": "Feature", "geometry": None, "properties": {
                "CUSEC_KEY": "001", "ddd_unit_id": "u", "district_id": int(district)}}
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, "w") as candidate:
                candidate.writestr("map.geojson", json.dumps({"features": [feature]}))
            raw = inner.getvalue()
            name = f"candidate_{i}.geojson.zip"
            if not (missing and i == 1):
                archive.writestr("cache/portfolio/" + name, raw)
            rows.append({"geojson": "/app/" + name, "sha256": "0" * 64 if corrupt else hashlib.sha256(raw).hexdigest(),
                         "assignment_hash": identity, "index": i, "seed": i, "selected": i == 0})
        archive.writestr("cache/portfolio/portfolio.json", json.dumps({"candidate_count": 2,
            "unique_candidate_count": 2, "selected_assignment_hash": rows[0]["assignment_hash"], "candidates": rows}))


class ByteCheckTests(unittest.TestCase):
    def run_case(self, **kwargs):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.zip"
            make_archive(path, **kwargs)
            return verify(path, expected_count=2)

    def test_complete_portfolio(self):
        self.assertEqual(self.run_case()["unique_assignment_count"], 2)

    def test_rejects_tampered_digest(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 del candidato"):
            self.run_case(corrupt=True)

    def test_rejects_duplicate_assignments(self):
        with self.assertRaisesRegex(ValueError, "Asignaciones no distintas"):
            self.run_case(duplicate=True)

    def test_rejects_missing_candidate(self):
        with self.assertRaises(KeyError):
            self.run_case(missing=True)


if __name__ == "__main__":
    unittest.main()
