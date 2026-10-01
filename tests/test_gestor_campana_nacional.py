import json, tempfile, unittest
from pathlib import Path
from herramientas.gestor_campana_nacional import (
 canonical_selection, aggregate, publication_matrix, validate_campaign_summary_for_promotion, build_manifest, build_matrix
)

class NationalCampaignTests(unittest.TestCase):
 def test_cardinalities_and_codauto_order(self):
  ids=[r["territory_id"] for r in canonical_selection([r["territory_id"] for r in canonical_selection(["andalucia"])] )]
  self.assertEqual(ids,["andalucia"])
  from herramientas.catalogo_territorios import load_master
  all_ids=[r["territory_id"] for r in load_master()]
  for n in (1,5,12,19):
   rows=canonical_selection(list(reversed(all_ids[:n])))
   self.assertEqual([r["autonomous_community_code_ine"] for r in rows],[f"{i:02d}" for i in range(1,n+1)])
 def test_manifest_campaigns_1_5_12_19_in_both_modes(self):
  from herramientas.catalogo_territorios import load_master
  all_ids=[r["territory_id"] for r in load_master()]
  for mode in ("electoral","territorial_only"):
   for n in (1,5,12,19):
    manifest=build_manifest(selected=list(reversed(all_ids[:n])),publication_mode=mode,
      source_sha="a"*40,strategy="GerryChain 50",campaign_instance=f"test-{mode}-{n}")
    self.assertEqual(len(manifest["territories"]),n)
    self.assertEqual([r["codauto"] for r in manifest["territories"]],[f"{i:02d}" for i in range(1,n+1)])
    self.assertEqual({r["publication_mode"] for r in manifest["territories"]},{mode})
    self.assertNotIn("reuse",json.dumps(manifest))
    expected_kind="prepared_source_pair" if mode=="electoral" else "territorial_source_receipt"
    self.assertEqual({r["evidence"]["kind"] for r in manifest["territories"]},{expected_kind})

 def test_zero_rejected(self):
  with self.assertRaisesRegex(ValueError,"entre 1 y 19"): canonical_selection([])
 def test_partial_and_missing_never_pass(self):
  m={"campaign_instance":"c","source_sha":"a"*40,"manifest_sha256":"b"*64,
     "territories":[{"territory_id":"a","preflight_status":"GENERATION_READY","preflight_blockers":[]},
                    {"territory_id":"b","preflight_status":"GENERATION_READY","preflight_blockers":[]}]}
  s=aggregate(m,[{"territory_id":"a","status":"PASS"}])
  self.assertEqual(s["status"],"FAIL"); self.assertEqual(s["territories"][1]["status"],"MISSING")
 def test_blocked_never_passes(self):
  m={"campaign_instance":"c","source_sha":"a"*40,"manifest_sha256":"b"*64,
     "territories":[{"territory_id":"a","preflight_status":"BLOCKED","preflight_blockers":["ACCREDITED_EVIDENCE_MISSING"]}]}
  self.assertEqual(aggregate(m,[])["territories"][0]["status"],"BLOCKED")
 def test_dynamic_promotion_and_publication(self):
  for n in (1,5,12,19):
   rows=[{"territory_id":str(i),"status":"PASS"} for i in range(n)]
   s={"status":"PASS","territory_count_expected":n,"territories":rows}
   self.assertEqual(len(validate_campaign_summary_for_promotion(s)),n)
   rel=[{"territory_id":str(i),"release_tag":f"r{i}","namespace":f"n{i}"} for i in range(n)]
   self.assertEqual(len(publication_matrix(rel,n)["include"]),n)
 def test_partial_release_set_rejected(self):
  with self.assertRaisesRegex(ValueError,"parciales"):
   publication_matrix([{"territory_id":"a","release_tag":"r","namespace":"n"}],2)
 def test_workflow_is_single_manager_and_safe(self):
  text=Path(".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  self.assertIn("name: 0 · Gestor de Campañas",text)
  self.assertIn("fail-fast: false",text); self.assertIn("max-parallel: 5",text)
  self.assertIn("publish_result: false",text); self.assertIn("persist_state: false",text)
  self.assertNotIn("retry_failed: true",text)
  self.assertNotIn("preparacion-fuentes.yml",text)
  self.assertNotIn("preparacion-resultados-electorales.yml",text)
 def test_modes_are_explicit(self):
  from herramientas.gestor_campana_nacional import MODES
  self.assertEqual(MODES,{"electoral","territorial_only"})


 def test_manifest_fixes_validated_generation_references_and_blocked_rows_do_not_launch(self):
  m=build_manifest(selected=["canarias"],publication_mode="electoral",
    source_sha="a"*40,strategy="GerryChain 50",campaign_instance="contract-test")
  row=m["territories"][0]
  self.assertEqual(m["generation_enablement_contract"],"generation_ready_contract/v1")
  self.assertTrue(row["generation_contract"]["allowed"])
  self.assertEqual(row["generation_contract"]["status"],"GENERATION_READY")
  self.assertEqual(len(row["generation_contract"]["contract_sha256"]),64)
  self.assertEqual(len(row["generation_contract"]["generation_evidence_sha256"]),64)
  # La generación está acreditada, pero la campaña electoral sigue bloqueada
  # mientras no exista el receipt durable del par. No se confunden ambas puertas.
  self.assertEqual(row["preflight_status"],"BLOCKED")
  self.assertIn("ACCREDITED_EVIDENCE_MISSING",row["preflight_blockers"])
  self.assertEqual(build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"],[])
  summary=aggregate(m,[])
  self.assertEqual(summary["status"],"FAIL")
  self.assertEqual(summary["territories"][0]["status"],"BLOCKED")

 def test_child_consumes_exact_manifest_references_and_recovery_bypasses_generation_gate(self):
  text=Path(".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  child=Path(".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
  for token in ("campaign_contract_sha256","campaign_generation_evidence_sha256",
                "campaign_source_artifact_sha256","campaign_source_package_sha256",
                "campaign_evidence_receipt_sha256","campaign_territorial_identity_sha256"):
   self.assertIn(token,text); self.assertIn(token,child)
  self.assertIn("CAMPAIGN_MANIFEST_MISMATCH",child)
  recovery=text[text.index("  recuperar_portfolio:"):text.index("  resumen:")]
  self.assertNotIn("generation_ready_contract",recovery)
  self.assertNotIn("campaign_contract_sha256",recovery)

 def test_failed_campaign_cannot_replace_previous_certified_publication(self):
  summary={"status":"FAIL","territory_count_expected":2,"territories":[
    {"territory_id":"a","status":"PASS"},{"territory_id":"b","status":"FAIL"}]}
  with self.assertRaises(ValueError):
   validate_campaign_summary_for_promotion(summary)
  text=Path(".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  self.assertIn("needs.resumen.result == 'success'",text)
  self.assertIn("publish_result: false",text)
  self.assertIn("persist_state: false",text)

if __name__=="__main__": unittest.main()
