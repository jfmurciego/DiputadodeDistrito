"""Focused checks for the official-source reconciliation added in F10_PROCESSOR 1.0.0."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from herramientas.procesar_f10_resultados_aragon_cyl import (
    EVIDENCE,
    aragon_cusec,
    cyl_cusec,
    nonnegative_int,
    sha256,
)

ROOT = Path(__file__).resolve().parents[1]


class F10OfficialElectoralSources(unittest.TestCase):
    def test_section_code_builders_preserve_official_widths(self):
        self.assertEqual(aragon_cusec("50", 25, "1-003-A"), "5002501003")
        self.assertEqual(cyl_cusec("León", "089", "04", "017"), "2408904017")

    def test_invalid_section_identifiers_and_fractional_votes_fail_closed(self):
        with self.assertRaises(ValueError):
            aragon_cusec("50", 25, "invalid")
        with self.assertRaises(ValueError):
            cyl_cusec("León", "089", "04", "0")
        with self.assertRaises(ValueError):
            nonnegative_int("3.5", "votes")
        with self.assertRaises(ValueError):
            nonnegative_int("-1", "votes")

    def test_processed_evidence_matches_raw_files_and_preserves_known_gaps(self):
        result = json.loads((EVIDENCE / "procesados/resultado_procesamiento.json").read_text(encoding="utf-8"))
        manifest_path = EVIDENCE / "procesados/manifest_procesamiento.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        declared = {row["path"]: row for row in manifest["originals"]}
        for rel, row in declared.items():
            path = ROOT / rel
            self.assertTrue(path.is_file(), rel)
            self.assertEqual(path.stat().st_size, row["bytes"], rel)
            self.assertEqual(sha256(path), row["sha256"], rel)

        aragon = result["aragon"]
        self.assertEqual(aragon["open_data_rows"], 30326)
        self.assertEqual(aragon["open_data_cusec_party_mismatches"], 0)
        self.assertEqual(aragon["candidate_votes_geographic"], 656725)
        self.assertEqual(aragon["candidate_votes_cera"], 4259)
        self.assertEqual(aragon["temporal_crosswalk"]["status"], "BLOCKED_UNRESOLVED_OFFICIAL_IDENTITY")
        self.assertEqual(aragon["temporal_crosswalk"]["result_only"], [
            {"cusec": "5002501003", "candidate_votes": 608, "status": "UNMATCHED_TEMPORAL_IDENTITY"}
        ])

        cyl = result["castilla_y_leon"]
        self.assertEqual(cyl["dataset_records"], 67006)
        self.assertEqual(cyl["candidate_votes_including_cera"], 1236753)
        self.assertEqual(cyl["temporal_crosswalk"]["status"], "BLOCKED_UNRESOLVED_OFFICIAL_IDENTITY")
        self.assertEqual(cyl["cera_cusec_count"], 19)
        self.assertEqual(cyl["temporal_crosswalk"]["geographic_electoral_only_votes"], 3874)
        self.assertEqual(len(cyl["temporal_crosswalk"]["electoral_only"]), 24)
        self.assertEqual(cyl["temporal_crosswalk"]["map_only"], ["3412004006", "3710701002"])
        for territory in ("aragon", "castilla_y_leon"):
            validation = result["canonical_package_validation"][territory]
            self.assertEqual(validation["decision"], "READY_PACKAGE")
            self.assertTrue(validation["provenance_hash_matches_contract"])


if __name__ == "__main__":
    unittest.main()
