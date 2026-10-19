"""F10 SIEL 2026 vote-scope invariants; no historical vote transfer approval."""
from __future__ import annotations
import csv,json
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"

def csv_rows(path):
    with (BASE/path).open("r",encoding="utf-8",newline="") as f:
        return list(csv.DictReader(f,delimiter=";"))

class AndaluciaSIEL2026VoteScope(unittest.TestCase):
    def test_all_new_electoral_sections_have_actual_vote_totals(self):
        g=csv_rows("ANDALUCIA_CANDIDATOS_GEOMETRICOS_34_20261019.csv")
        v=csv_rows("ANDALUCIA_SIEL_25_NUEVAS_2026_VOTOS_20261019.csv")
        evidence=json.loads((BASE/"ANDALUCIA_SIEL_VOTOS_25_NUEVAS_20261019.json").read_text(encoding="utf-8"))
        new={r["CUSEC_cambiada"]:r for r in g if r["sentido"]=="2026_to_2025"}
        old={r["CUSEC_cambiada"] for r in g if r["sentido"]=="2025_to_2026"}
        self.assertEqual(len(g),34)
        self.assertEqual(len(new),25)
        self.assertEqual(len(old),9)
        self.assertEqual(len(v),25)
        self.assertEqual({r["CUSEC_electoral_2026"] for r in v},set(new))
        self.assertTrue(old.isdisjoint(new))
        self.assertTrue(all(r["adscripcion_votos_2025_autorizada"]=="NO" for r in v))
        self.assertEqual(sum(int(r["votos_candidaturas_SIEL_2026"]) for r in v),15425)
        for r in v:
            src=new[r["CUSEC_electoral_2026"]]
            self.assertEqual(r["CUSEC_candidata_territorial_2025"],src["CUSEC_contraparte_principal"])
            self.assertEqual(r["municipio"],src["municipio"])
            self.assertEqual(r["fraccion_coincidencia_geometrica_pct"],src["coincidencia_superficie_pct"])
        stat=evidence["verified"]
        self.assertEqual(stat["section_identities"],6044)
        self.assertEqual(stat["geographic_candidate_vote_rows"],95659)
        self.assertEqual(stat["geographic_candidate_votes"],4136317)
        self.assertEqual(stat["cera_candidate_votes"],21222)
        self.assertEqual(stat["all_official_candidate_votes"],4157539)
        self.assertEqual(stat["geographic_candidate_votes"]+stat["cera_candidate_votes"],
                         stat["all_official_candidate_votes"])
        self.assertEqual(stat["added_2026_candidate_votes"],15425)
        self.assertEqual(stat["ine_2026_only_absent_siel"],"2102502002")
        self.assertEqual(stat["cortegana_2001_candidate_votes"],658)
        self.assertFalse(evidence["crosswalk_accredited"])
        self.assertFalse(evidence["generation_authorized"])
        self.assertTrue(evidence["source"]["official_siel_sections_sha256"])
        self.assertTrue(evidence["source"]["official_siel_cera_sha256"])
        print("DDD_F10_SIEL_NEW_25_15425_VOTES_VERIFIED_CROSSWALK_BLOCKED")

if __name__=="__main__": unittest.main()
