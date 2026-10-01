import copy, json, os, re, shutil, subprocess, sys, tempfile, unittest
import yaml
from pathlib import Path
from herramientas.gestor_campana_nacional import (
 canonical_selection, aggregate, publication_matrix, validate_campaign_summary_for_promotion, build_manifest, build_matrix,
 validate_campaign_child, validate_manifest_digest, _sha_payload
)

ROOT=Path(__file__).resolve().parents[1]

def freeze(manifest):
 manifest["manifest_sha256"]=_sha_payload({k:v for k,v in manifest.items() if k!="manifest_sha256"})
 return manifest

def generation_fixture(root, mode="territorial_only", with_receipt=True):
 # Local evidence uses the common validator with current implementation bytes.
 # No live catalog entry is assumed to authorize a new generation.
 from herramientas._resolver_ejecucion_completa_core import _contract_generation_binding, _pre_m04_implementation_binding
 catalog=yaml.safe_load((ROOT/"configuracion/catalogo_preparacion.yaml").read_text())
 row=copy.deepcopy(next(r for r in catalog["territories"] if r["territory_id"]=="cantabria"))
 state=row["editions"]["2025"]
 contract=yaml.safe_load((ROOT/state["contract_path"]).read_text())
 evidence=json.loads((ROOT/state["evidence"]["generation_preflight"]).read_text())
 (root/"configuracion").mkdir()
 shutil.copy(ROOT/"configuracion/catalogo_territorios_espana_2025.yaml", root/"configuracion")
 for rel in ("modulos/01_preparar_base_territorial.py", "modulos/02_construir_adyacencias.py",
             "modulos/03_construir_grafo.py", "herramientas/preparar_unidades_internas.py",
             "herramientas/construir_unidades_internas_m04.py"):
  (root/rel).parent.mkdir(exist_ok=True)
  shutil.copy(ROOT/rel,root/rel)
 prep={"run_id":7,"artifact_name":"ddd-source-package-cantabria-2025-7",
       "artifact_sha256":"a"*64,"package_sha256":"b"*64,
       "compatibility_identity_sha256":"c"*64,"population_year":2023,
       "section_year":2023,"source_commit":"d"*40,"receipt_path":"receipt.json"}
 contract["meta"].update(source_population_year=2023,source_section_year=2023)
 contract["validation"]["source_baseline"]={
  "schema":"ddd.source-baseline/1.0","edition":"2025","population_year":2023,"section_year":2023,
  "population_total":evidence["graph"]["population"],"target_section_count":evidence["graph"]["nodes"],
  "package_sha256":prep["package_sha256"],"compatibility_report_sha256":"9"*64,
  "compatibility_identity_sha256":prep["compatibility_identity_sha256"]}
 evidence.update(run_id=7,source_commit="e"*40,artifact_name="ddd-state-7-M03U",artifact_sha256="f"*64)
 evidence["source"].update({k:v for k,v in prep.items() if k!="receipt_path"})
 evidence["graph"]["artifact_name"]="ddd-state-7-M03"
 evidence["partitioning"]["job_artifact_name"]="ddd-internal-units-7"
 contract["generation_state"]={"source_prepared":True,"generation_enabled":True,
  "package_sha256":prep["package_sha256"],"compatibility_identity_sha256":prep["compatibility_identity_sha256"],
  "pre_m04_run_id":7,"pre_m04_source_commit":evidence["source_commit"],
  "pre_m04_artifact_sha256":evidence["artifact_sha256"]}
 evidence["implementation"]=_pre_m04_implementation_binding(root,contract)
 evidence["contract_binding"]=_contract_generation_binding(contract)
 (root/"contract.yaml").write_text(yaml.safe_dump(contract))
 (root/"preflight.json").write_text(json.dumps(evidence))
 state.update(contract_path="contract.yaml",generation_enabled=True,preparation_evidence=prep)
 state["evidence"]={"generation_preflight":"preflight.json"}
 if with_receipt:
  receipt={"territorial_identity_sha256":"1"*64}
  if mode=="electoral":
   state["evidence"]["prepared_source_pair"]="pair.json"
   receipt={"pair":{"pair_sha256":"2"*64,
     "territorial_source":{"territorial_identity_sha256":"1"*64},
     "electoral_source":{"electoral_identity_sha256":"3"*64}}}
  (root/("pair.json" if mode=="electoral" else "receipt.json")).write_text(json.dumps(receipt))
 (root/"configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump({"territories":[row]}))
 m=build_manifest(selected=["cantabria"],publication_mode=mode,source_sha="a"*40,
                  strategy="GerryChain 50",campaign_instance="fixture",root=root)
 r=m["territories"][0]
 plan={"territory_id":"cantabria","edition":"2025","optimization_algorithm":"GerryChain 50",
       "contract_path":"contract.yaml","publication_mode_effective":mode,
       "existing":{"territorial_source":dict(prep)}}
 plan["prepared_source_pair" if mode=="electoral" else "prepared_territorial_source"]={
  k:v for k,v in r["evidence"].items() if k not in ("kind","receipt_sha256")}
 return m,plan

class NationalCampaignTests(unittest.TestCase):
 def test_actual_workflow_child_manifest_transmission(self):
  manager=yaml.safe_load((ROOT/".github/workflows/gestor-campanas.yml").read_text())
  child=yaml.safe_load((ROOT/".github/workflows/ejecucion-completa-proyecto.yml").read_text())
  caller=next(job["with"] for job in manager["jobs"].values()
              if job.get("uses")=="./.github/workflows/ejecucion-completa-proyecto.yml")
  step=next(s for s in child["jobs"]["planificar"]["steps"]
            if "validate_campaign_child(" in s.get("run",""))
  code=step["run"].split('if [[ -n "$CAMPAIGN_INSTANCE" ]]; then',1)[1].split("python - <<'PY'\n",1)[1].split("\nPY",1)[0]
  for mode in ("electoral","territorial_only"):
   with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
    root=Path(td); m,p=generation_fixture(root,mode)
    # The suite container has no Git. Model only checkout SHA resolution;
    # manifest transmission and the actual child validator remain unmocked.
    bindir=root/"bin"; bindir.mkdir(); git=bindir/"git"
    git.write_text(f"#!{sys.executable}\nimport sys\nassert sys.argv[1:]==['rev-parse','HEAD']\nprint({m['source_sha']!r})\n")
    git.chmod(0o755)
    freeze(m); matrix=build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"][0]
    inputs={}
    for name,value in caller.items():
     match=re.fullmatch(r"\$\{\{ matrix\.([\w.]+)(?: \|\| '')? \}\}",str(value))
     if match:
      resolved=matrix
      for key in match[1].split("."): resolved=resolved.get(key,{}) if isinstance(resolved,dict) else {}
      inputs[name]=resolved if resolved!={} else ""
    env={**os.environ,"PYTHONPATH":str(ROOT),"PATH":str(bindir)}
    for name,value in step["env"].items():
     match=re.fullmatch(r"\$\{\{ inputs\.(\w+) \}\}",str(value))
     if match: env[name]=str(inputs.get(match[1],""))
    for rel,payload in ((".ddd-campaign/campaign-manifest.json",m),(".ddd-full-run/plan.json",p)):
     path=root/rel; path.parent.mkdir(); path.write_text(json.dumps(payload))
    result=subprocess.run([sys.executable,"-c",code],cwd=root,env=env,capture_output=True,text=True)
    self.assertEqual(result.returncode,0,result.stderr)
    for name in (k for k in env if k.startswith("CAMPAIGN_") and k not in ("CAMPAIGN_INSTANCE","CAMPAIGN_NAMESPACE")):
     result=subprocess.run([sys.executable,"-c",code],cwd=root,env={**env,name:"drift"},capture_output=True,text=True)
     self.assertNotEqual(result.returncode,0,name)
     self.assertIn("CAMPAIGN_MANIFEST_MISMATCH",result.stderr,name)

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
     "territories":[{"territory_id":"a","slot":"01","publication_mode":"electoral","preflight_status":"GENERATION_READY","preflight_blockers":[]},
                    {"territory_id":"b","slot":"02","publication_mode":"electoral","preflight_status":"GENERATION_READY","preflight_blockers":[]}]}
  freeze(m)
  s=aggregate(m,[{"territory_id":"a","status":"PASS"}])
  self.assertEqual(s["status"],"FAIL"); self.assertEqual(s["territories"][1]["status"],"MISSING")
 def test_blocked_never_passes(self):
  m={"campaign_instance":"c","source_sha":"a"*40,"manifest_sha256":"b"*64,
     "territories":[{"territory_id":"a","preflight_status":"BLOCKED","preflight_blockers":["ACCREDITED_EVIDENCE_MISSING"]}]}
  freeze(m)
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
  with tempfile.TemporaryDirectory() as td:
   m,_=generation_fixture(Path(td),mode="electoral",with_receipt=False)
   row=m["territories"][0]
   self.assertEqual(m["generation_enablement_contract"],"generation_ready_contract/v1")
   self.assertTrue(row["generation_contract"]["allowed"])
   self.assertEqual(row["generation_contract"]["status"],"GENERATION_READY")
   self.assertEqual(len(row["generation_contract"]["contract_sha256"]),64)
   self.assertEqual(len(row["generation_contract"]["generation_evidence_sha256"]),64)
   self.assertEqual(row["preflight_status"],"BLOCKED")
   self.assertIn("ACCREDITED_EVIDENCE_MISSING",row["preflight_blockers"])
   self.assertEqual(build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"],[])
   self.assertEqual(aggregate(m,[])["status"],"FAIL")

 def test_common_generation_validator_accepts_frozen_child_in_both_modes(self):
  for mode in ("territorial_only","electoral"):
   with self.subTest(mode=mode), tempfile.TemporaryDirectory() as td:
    root=Path(td); m,p=generation_fixture(root,mode)
    self.assertEqual(len(build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"]),1)
    validate_campaign_child(manifest=m,plan=p,root=root,expected_sha=m["manifest_sha256"],
                            source_sha=m["source_sha"],slot="06",campaign_instance="fixture")

 def test_child_blocks_frozen_identity_and_resolved_source_drift(self):
  for mode in ("territorial_only","electoral"):
   with tempfile.TemporaryDirectory() as td:
    root=Path(td); m,p=generation_fixture(root,mode)
    args=dict(manifest=m,plan=p,root=root,expected_sha=m["manifest_sha256"],
              source_sha=m["source_sha"],slot="06",campaign_instance="fixture")
    for key in ("run_id","artifact_name","artifact_sha256","package_sha256","source_commit"):
     changed=copy.deepcopy(p); changed["existing"]["territorial_source"][key]="drift"
     with self.subTest(mode=mode,source=key), self.assertRaisesRegex(ValueError,"CAMPAIGN_MANIFEST_MISMATCH"):
      validate_campaign_child(**{**args,"plan":changed})
    for key in ("receipt_path","territorial_identity_sha256","electoral_identity_sha256","pair_sha256"):
     if mode!="electoral" and key in ("electoral_identity_sha256","pair_sha256"): continue
     changed=copy.deepcopy(p)
     changed["prepared_source_pair" if mode=="electoral" else "prepared_territorial_source"][key]="drift"
     with self.subTest(mode=mode,prepared=key), self.assertRaisesRegex(ValueError,"CAMPAIGN_MANIFEST_MISMATCH"):
      validate_campaign_child(**{**args,"plan":changed})
    for key in ("source_sha","slot","campaign_instance","expected_sha"):
     with self.subTest(context=key), self.assertRaisesRegex(ValueError,"CAMPAIGN_MANIFEST_MISMATCH"):
      validate_campaign_child(**{**args,key:"drift"})
    (root/"contract.yaml").write_text((root/"contract.yaml").read_text()+"\n# changed bytes\n")
    with self.assertRaisesRegex(ValueError,"CAMPAIGN_MANIFEST_MISMATCH"):
     validate_campaign_child(**args)

 def test_manifest_drift_and_revoked_generation_block(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); m,p=generation_fixture(root)
   changed=copy.deepcopy(m); changed["territories"][0]["generation_contract"]["source"]["package_sha256"]="0"*64
   with self.assertRaisesRegex(ValueError,"manifest_sha256"):
    build_matrix(changed,"EXECUTE_CAMPAIGN_CONFIRMED")
   catalog=root/"configuracion/catalogo_preparacion.yaml"
   data=yaml.safe_load(catalog.read_text()); data["territories"][0]["editions"]["2025"]["generation_enabled"]=False
   catalog.write_text(yaml.safe_dump(data))
   with self.assertRaisesRegex(ValueError,"CAMPAIGN_GENERATION_CONTRACT_BLOCK"):
    validate_campaign_child(manifest=m,plan=p,root=root,expected_sha=m["manifest_sha256"],
                            source_sha=m["source_sha"],slot="06",campaign_instance="fixture")

 def test_incomplete_duplicate_or_foreign_results_never_promote(self):
  with tempfile.TemporaryDirectory() as td:
   m,_=generation_fixture(Path(td))
   report={"territory_id":"cantabria","slot":"06","publication_mode":"territorial_only",
           "campaign_instance":"fixture","source_sha":m["source_sha"],"manifest_sha256":m["manifest_sha256"],
           "status":"PASS","candidate_count_expected":50,"candidate_count_valid":50,
           "unique_candidate_hash_count":50,"missing_candidate_hash_count":0,"duplicate_candidate_hash_count":0}
   self.assertEqual(aggregate(m,[report])["status"],"PASS")
   for field,value in (("source_sha","0"*40),("manifest_sha256","0"*64),
                       ("campaign_instance","old"),("status",None),("status","INCOMPLETE"),
                       ("candidate_count_valid",49),("unique_candidate_hash_count",49)):
    with self.subTest(field=field,value=value):
     s=aggregate(m,[{**report,field:value}])
     self.assertEqual(s["status"],"FAIL")
     with self.assertRaises(ValueError): validate_campaign_summary_for_promotion(s)
   for reports in ([],[report,report],[report,{**report,"territory_id":"galicia"}]):
    s=aggregate(m,reports)
    self.assertEqual(s["status"],"FAIL")
    with self.assertRaises(ValueError): validate_campaign_summary_for_promotion(s)

 def test_same_cardinality_does_not_allow_substituting_selected_territory(self):
  with self.assertRaisesRegex(ValueError,"territorios seleccionados"):
   publication_matrix([{"territory_id":"galicia","release_tag":"r","namespace":"n"}],1,["cantabria"])

 def test_workflow_freezes_every_strategy_and_handles_all_blocked_without_children(self):
  text=Path(".github/workflows/gestor-campanas.yml").read_text()
  self.assertIn("campaign_instance: ${{ matrix.campaign_instance }}",text)
  self.assertIn("expected_district_count: ${{ matrix.expected_district_count }}",text)
  self.assertIn("needs.preparar.outputs.ready_count != '0'",text)
  child=Path(".github/workflows/ejecucion-completa-proyecto.yml").read_text()
  self.assertIn("name: ddd-campaign-manifest-${{ inputs.campaign_instance }}",child)
  self.assertIn("validate_campaign_child(",child)
  self.assertNotIn('cs=p.get("catalog_state") or {}',child)

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
