"""F10 Andalucía official INE three-period TRAM section-linkage evidence.

This certifies street-segment change records, never an allocation of votes
from election-day 2026 to the reference geometry of 2025.
"""
from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261019"
E=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"
R=B/"ANDALUCIA_INE_TRAM_3_PERIODOS_86_CUSEC.json"

def readcsv(path):
    with path.open("r",encoding="utf-8",newline="") as fh:
        return list(csv.DictReader(fh,delimiter=";"))

class TestOfficialAndaluciaTRAMLineage(unittest.TestCase):
    def test_archived_three_intervals_and_identity_scope(self):
        j=json.loads(R.read_text(encoding="utf-8"))
        self.assertEqual(j["schema"],"ddd.f10.and.ine-tram-official-three-intervals/1.0")
        self.assertEqual(j["provenance"]["workflow_conclusion"],"SUCCESS")
        self.assertEqual(j["provenance"]["github_workflow_run"],39245930295)
        self.assertEqual(j["provenance"]["artifact_id"],12183536797)
        self.assertEqual(j["source_2025_01_to_2025_07"]["sha256"],
                         "852db9bcd0c6355e85020a07d229d31d00c4eab9e0493f83a8671bca789e776f")
        self.assertEqual(j["source_2025_07_to_2026_01"]["sha256"],
                         "f2f8299bbcff7e79c69948b900d5c9e97c3b9c71f8cc430f8ffac0e9a475f319")
        self.assertEqual(j["source_2026_01_to_2026_07"]["sha256"],
                         "154b8eacdb886e5b6463283c597076b3b0dde256cfaf74cb34c4ffc5cb326635")
        self.assertEqual(j["summary"]["groups_by_period"],[
            {"period":"2025-01_to_2025-07","groups":58},
            {"period":"2025-07_to_2026-01","groups":22},
            {"period":"2026-01_to_2026-07","groups":2}])
        self.assertEqual(len(j["official_change_groups"]),82)
        self.assertTrue(all(g["code"] in {"M","B"} for g in j["official_change_groups"]))
        self.assertTrue(all(date.fromisoformat(g["date"][0:4]+"-"+g["date"][4:6]+"-"+g["date"][6:8])<=date(2026,5,17)
                            for g in j["official_change_groups"]))

    def test_25_new_sections_every_one_has_administrative_tram_proof_not_vote_attribution(self):
        j=json.loads(R.read_text(encoding="utf-8"))
        a=readcsv(E/"ANDALUCIA_SIEL_25_NUEVAS_2026_VOTOS_20261019.csv")
        expected={x["CUSEC_electoral_2026"]:x for x in a}
        reported={x["electoral_2026"]:x for x in j["new_2026_sections"]}
        self.assertEqual(len(expected),len(reported))
        self.assertEqual(len(expected),25)
        self.assertEqual(set(expected),set(reported))
        self.assertEqual(sum(int(x["votos_candidaturas_SIEL_2026"]) for x in a),15425)
        for code,row in reported.items():
            old=expected[code]["CUSEC_candidata_territorial_2025"]
            self.assertEqual(row["geographic_2025_candidate"],old)
            self.assertEqual(row["candidate_votes_2026"],int(expected[code]["votos_candidaturas_SIEL_2026"]))
            self.assertTrue(row["official_tram_section_change_records"],code)
            for link in row["official_tram_section_change_records"]:
                self.assertEqual(link["code"],"M")
                self.assertEqual({link["source"],link["other"]},{old,code})
                self.assertGreater(link["records"],0)
            self.assertFalse(row["crosswalk_votes_accredited"])
        s=j["summary"]
        self.assertEqual(s["new_with_direct_admin_link"],25)
        self.assertEqual(s["new_with_direct_admin_link_candidate_votes"],15425)
        self.assertEqual(s["retired_2025_count"],9)
        self.assertEqual(s["retired_with_direct_admin_link"],9)

    def test_41_persistent_material_changes_and_cortegana_still_blocked(self):
        j=json.loads(R.read_text(encoding="utf-8"))
        persistent={x["same_code_2025_2026"]:x for x in j["persistent_same_code_changes"]}
        self.assertEqual(len(persistent),41)
        self.assertEqual(sum(x["votes_2026"] for x in persistent.values()),31792)
        self.assertEqual(sum(bool(x["official_changed_tram_groups"]) for x in persistent.values()),39)
        self.assertEqual({k for k,v in persistent.items() if not v["official_changed_tram_groups"]},
                         {"4109110025","4109110027"})
        self.assertTrue(all(not x["allocation_accredited"] for x in persistent.values()))
        c=j["cortegana"]
        self.assertEqual(c["ine_section_2025_and_2026"],"2102502002")
        self.assertEqual(c["electoral_section_2026"],"2102502001")
        self.assertTrue(any(x["date"]=="20260129" and x["source"]=="2102502002"
                            and x["other"]=="2102502001" and x["records"]==15
                            and x["code"]=="M" for x in c["official_segment_events"]))
        con=j["conclusions"]
        self.assertEqual(con["administrative_change_between_section_identifiers"],
                         "SOURCE_ACCREDITED_FOR_TRAM_SEGMENTS")
        self.assertEqual(con["votes_allocated_to_2025_geometry"],0)
        self.assertFalse(con["territorial_reference_2025_change_authorized"])
        self.assertFalse(con["generation_authorized"])
        self.assertIn("BLOCKED",con["official_2025_2026_electoral_vote_crosswalk"])
        self.assertTrue(all(not x["successor_votes_separately_additive"]
                            for x in j["retired_2025_sections"]))

if __name__=="__main__":
    unittest.main()
