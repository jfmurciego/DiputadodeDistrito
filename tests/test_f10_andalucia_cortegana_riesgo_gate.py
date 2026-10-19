"""Verify risk ledger and official BOP identity without mapping votes to 2025."""
from __future__ import annotations
import csv,json,re
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261019"
ED=ROOT/"docs/AUDITORIAS/CIERRE_FUENTES_20261017"
def load(name,folder=DOC):
    return json.loads((folder/name).read_text(encoding="utf-8"))
def table(name,folder):
    with (folder/name).open(newline="",encoding="utf-8") as f:
        return list(csv.DictReader(f,delimiter=";"))

class AndaluciaGateEvidence(unittest.TestCase):
    def test_official_election_day_cortegana_without_vote_attribution(self):
        b=load("CORTEGANA_BOP_OFICIAL_MESAS_2026.json")
        self.assertEqual(b["election"]["event_date"],"2026-05-17")
        self.assertEqual(b["source"]["provider"],"Oficina del Censo Electoral, Delegación Provincial del INE en Huelva")
        self.assertEqual(b["source"]["raw_pdf_sha256"],"cdd97765f72121a31774d7c0c37f572399ba3c3dca767b44e42bdc4493497dfa")
        self.assertTrue(b["source"]["source_sha256_accredited"])
        self.assertEqual(b["source"]["acquisition"]["conclusion"],"SUCCESS")
        self.assertEqual(b["source"]["acquisition"]["artifact_id"],12179246201)
        self.assertEqual([x["section"] for x in b["official_precincts"] if x["district"]=="02"],["001"])
        sec=b["official_precincts"][-1]
        self.assertEqual(sec["tables"],["A","B","C"])
        self.assertEqual(sec["subsection_identifiers"],["01","02","03"])
        self.assertEqual(b["absent_precincts"],[{"district":"02","section":"002","cusec":"2102502002"}])
        self.assertFalse(b["legal_voter_transfer_accredited"])
        self.assertFalse(b["crosswalk_accredited"])

    def test_67_distinct_sections_47875_votes_no_double_count(self):
        report=load("ANDALUCIA_SIEL_RIESGO_CONSOLIDADO_20261019.json")
        v=report["electoral"]
        fresh=table("ANDALUCIA_SIEL_25_NUEVAS_2026_VOTOS_20261019.csv",ED)
        persisted=table("ANDALUCIA_41_CUSEC_MISMO_CODIGO_LIMITES_CAMBIADOS_VOTOS_2026.csv",DOC)
        merged=table("ANDALUCIA_9_CUSEC_2025_RETIRADOS_VOTOS_SIEL_2026.csv",DOC)
        self.assertEqual(len(fresh),25)
        self.assertEqual(len(persisted),41)
        self.assertEqual(len(merged),9)
        new_ids={x["CUSEC_electoral_2026"] for x in fresh}
        persisted_ids={x["CUSEC_2025_y_2026"] for x in persisted}
        old_ids={x["CUSEC_territorial_2025_retirada"] for x in merged}
        self.assertEqual(len(new_ids),25)
        self.assertEqual(len(persisted_ids),41)
        self.assertEqual(len(old_ids),9)
        self.assertFalse(new_ids & persisted_ids)
        self.assertFalse(old_ids & new_ids)
        self.assertTrue({r["CUSEC_electoral_2026_sucesora_candidata"] for r in merged}<=persisted_ids)
        self.assertTrue(all(x["reparto_a_geografia_2025_autorizado"]=="NO" for x in persisted))
        self.assertTrue(all(x["adscripcion_votos_2025_autorizada"]=="NO" for x in fresh))
        self.assertEqual(sum(int(x["votos_candidaturas_SIEL_2026"]) for x in fresh),15425)
        self.assertEqual(sum(int(x["votos_candidaturas_SIEL_2026"]) for x in persisted),31792)
        self.assertEqual(sum(int(x["votos_SIEL_2026_sucesora_total"]) for x in merged),6901)
        self.assertEqual(15425+31792+658,47875)
        self.assertEqual(v["count_distinct_flagged_sections"],67)
        self.assertEqual(v["distinct_flagged_candidate_votes"],47875)
        self.assertEqual(v["siel_2026_successors_votes_subset_of_41"],6901)
        self.assertEqual(v["total_official_candidate_votes"],4157539)
        self.assertEqual(v["geographic_candidate_votes"]+v["cera_candidate_votes_non_geographic"],4157539)
        self.assertEqual(report["status"]["electoral_F10"],"BLOCKED_CROSSWALK_NOT_PROVEN")
        self.assertFalse(report["status"]["generation_authorized"])
        self.assertTrue(all(re.fullmatch(r"\d{10}",c) for c in new_ids|persisted_ids|old_ids))

if __name__=="__main__":unittest.main()
