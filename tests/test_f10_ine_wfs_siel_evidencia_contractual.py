"""F10: enforce integrity of research evidence without promoting any blocked gate.

This checks the *recorded* INE/SIEL cross-edition evidence, not raw external data.
Live-source identity and official vote crosswalk remain independently required.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1] / "docs/AUDITORIAS/CIERRE_FUENTES_20261017"
def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))
def sha(value):
    return bool(re.fullmatch(r"[0-9a-f]{64}",str(value)))
def cusec(value):
    return bool(re.fullmatch(r"[0-9]{10}",str(value)))

class FuenteF10Invariants(unittest.TestCase):
    def test_ine_andalucia_2025_2026_nomenclature(self):
        d=read("IDENTIDADES_INE_2025_2026_F10.json")
        a=d["andaluces"]
        rows=a["provinces"]
        self.assertEqual(len(rows),8)
        self.assertEqual({x["CPRO"] for x in rows},{"04","11","14","18","21","23","29","41"})
        self.assertEqual(sum(x["sections_2025"] for x in rows),6029)
        self.assertEqual(sum(x["sections_2026"] for x in rows),6045)
        adds={v for r in rows for v in r["added_2026"]}
        rems={v for r in rows for v in r["removed_since_2025"]}
        self.assertEqual(len(adds),25)
        self.assertEqual(len(rems),9)
        self.assertFalse(adds & rems)
        self.assertTrue(all(cusec(v) for v in adds | rems))
        for r in rows:
            self.assertEqual(r["sections_2026"]-r["sections_2025"],
                             len(r["added_2026"])-len(r["removed_since_2025"]))
        self.assertEqual(a["reported_SIEL_2026_electoral_sections"],6044)
        self.assertEqual(a["difference_ine_2026_minus_siel_2026"],1)
        self.assertFalse(d["production_authorized"])

    def test_siel_group_scope_is_only_34_not_final_crosswalk(self):
        ine=read("IDENTIDADES_INE_2025_2026_F10.json")["andaluces"]
        adds={v for r in ine["provinces"] for v in r["added_2026"]}
        rems={v for r in ine["provinces"] for v in r["removed_since_2025"]}
        s=read("ANDALUCIA_SIEL_202605_IDENTIDADES_34.json")
        self.assertEqual(s["election_key"],202605)
        self.assertEqual(s["groups_queried"],s["groups_received"])
        self.assertEqual(s["errors"],[])
        ids={r["CUSEC"] for r in s["codes"]}
        self.assertEqual(ids,adds|rems)
        self.assertEqual(len(s["codes"]),34)
        self.assertEqual({r["CUSEC"] for r in s["codes"] if r["kind"]=="INE_2026_ADDED"},adds)
        self.assertEqual({r["CUSEC"] for r in s["codes"] if r["kind"]=="INE_2025_RETIRED"},rems)
        self.assertTrue(all(r["siel_group_available"] for r in s["codes"]))
        self.assertTrue(all(r["siel_202605_has_section"] for r in s["codes"] if r["CUSEC"] in adds))
        self.assertTrue(all(not r["siel_202605_has_section"] for r in s["codes"] if r["CUSEC"] in rems))
        self.assertEqual(s["checks"]["total"],34)
        self.assertEqual(s["checks"]["added_present_siel"],25)
        self.assertEqual(s["checks"]["retired_absent_siel"],9)

    def test_exact_6045_6044_discrepancy_no_pass(self):
        d=read("ANDALUCIA_INE_6045_SIEL_6044_DIFERENCIA_NOMINAL.json")
        c=d["comparison"]
        self.assertEqual(c["intersection_count"],6044)
        self.assertEqual(c["locator_only"],[])
        self.assertEqual(c["ine_only"],["2102502002"])
        self.assertEqual(d["discrepant_cusec"]["municipality_name"],"Cortegana")
        self.assertTrue(d["discrepant_cusec"]["ine_2025_present"])
        self.assertTrue(d["discrepant_cusec"]["ine_2026_present"])
        self.assertFalse(d["discrepant_cusec"]["siel_0002_present"])
        self.assertFalse(d["gates"]["generation_authorized"])
        self.assertIn("BLOCKED",d["gates"]["F10_electoral"])
        self.assertFalse(d["electoral_locator"]["source_is_final_official_election"])

    def test_ine_tram_groups_are_distinct_not_vote_mapping(self):
        e=read("INE_CALLEJERO_TRAM_CAMBIOS_15_2025_2026.json")
        self.assertTrue(sha(e["source_sha256"]) and sha(e["source_2_sha256"]))
        self.assertEqual(len(e["change_records"]),15)
        self.assertFalse(e["generation_authorized"])
        self.assertEqual(e["next_period_matched_change_groups"],[])
        seen=set()
        for r in e["change_records"]:
            self.assertTrue(cusec(r["source"]))
            if r["other"] is not None:
                self.assertTrue(cusec(r["other"]))
            self.assertRegex(r["date"],r"^2025[0-1][0-9][0-3][0-9]$")
            self.assertIn(r["code"],{"M","B"})
            self.assertGreater(r["records"],0)
            if r["code"]=="M":
                self.assertNotEqual(r["source"],r["other"])
                self.assertIsNotNone(r["other"])
            k=(r["source"],r["other"],r["date"],r["code"])
            self.assertNotIn(k,seen)
            seen.add(k)

if __name__=="__main__":
    unittest.main()
