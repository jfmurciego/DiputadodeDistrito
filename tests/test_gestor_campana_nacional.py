"""Regresiones del gestor nacional, versión 0.0.7, 2026-10-29.
Alcance: planificación pura y cierre de acreditación; estado: candidato.
Cambio/motivo: el caso histórico de Extremadura (sin par electoral) se evalúa sobre la raíz congelada
aee8215e; Extremadura ya tiene fuente electoral y par en main.
Anterior: legacy/tests/test_gestor_campana_nacional_v0.0.6_20261029.py.
"""
import copy, json, os, re, shutil, subprocess, sys, tempfile, unittest
import yaml
from pathlib import Path
from herramientas.gestor_campana_nacional import (
 canonical_selection, aggregate, publication_matrix, validate_campaign_summary_for_promotion, build_manifest, build_matrix,
 validate_campaign_child, validate_manifest_digest, _sha_payload, campaign_execution_plan
)

ROOT=Path(__file__).resolve().parents[1]
from tests._raiz_congelada import frozen_root  # noqa: E402

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
 evidence=json.loads((ROOT/"territorios/cantabria/evidencia/catalogo/generation_preflight_2025.json").read_text())
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
 (root/"configuracion/catalogo_preparacion.yaml").write_text(yaml.safe_dump({"schema":"ddd-preparation-catalog/1.1","default_edition":"2025","territories":[row]}))
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
     elif name=="persist_state" and "matrix.persist_state" in str(value):
      inputs[name]=str(matrix["persist_state"]).lower()
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

 def test_campaign_continuity_routes_require_frozen_product_and_common_resolver(self):
  from unittest.mock import patch
  for route in ("PRODUCT_REUSE_READY","SOURCE_PREPARATION_REQUIRED"):
   with self.subTest(route=route), tempfile.TemporaryDirectory() as td:
    root=Path(td); manifest,child=generation_fixture(root,mode="territorial_only")
    row=manifest["territories"][0]
    product={"run_id":101,"artifact_name":"ddd-territorial-product-101","artifact_sha256":"7"*64}
    preparing=route=="SOURCE_PREPARATION_REQUIRED"
    effective={"contract_path":row["contract_path"],"generation_gate":{"allowed":True,"route":"planned_pre_m04_accreditation" if preparing else "certified_product_lineage"},"run_prepare_territorial":preparing,"run_generate":preparing,
               "pre_m04_accreditation_planned":preparing,
               "existing":{"territorial_product":product}}
    for k in ("run_prepare_electoral","run_incorporate"):
     effective[k]=row["execution_plan"].get(k,False)
    row["preflight_status"]=route
    row["execution_route"]=route
    row["execution_plan"].update({k:effective[k] for k in
      ("run_prepare_territorial","run_generate","pre_m04_accreditation_planned")})
    row["generation_contract"]={"allowed":False}
    from herramientas.gestor_campana_nacional import _campaign_lineage_identity
    row["execution_lineage"]=_campaign_lineage_identity(effective)
    row["territorial_product"]=product if not preparing else {}
    if not preparing:
     child["existing"]["territorial_product"]=dict(product)
    freeze(manifest)
    matrix=build_matrix(manifest,"EXECUTE_CAMPAIGN_CONFIRMED")
    self.assertEqual(len(matrix["include"]),1)
    self.assertEqual(matrix["include"][0]["execution_route"],route)
    summary=aggregate(manifest,[])
    self.assertEqual(summary["territories"][0]["status"],"MISSING")
    with patch("herramientas.gestor_campana_nacional.campaign_execution_plan",return_value=effective):
     validate_campaign_child(manifest=manifest,plan=child,root=root,
         expected_sha=manifest["manifest_sha256"],source_sha=manifest["source_sha"],
         slot=row["slot"],campaign_instance=manifest["campaign_instance"])
     with self.assertRaisesRegex(ValueError,"persist_state"):
      validate_campaign_child(manifest=manifest,plan=child,root=root,
         expected_sha=manifest["manifest_sha256"],source_sha=manifest["source_sha"],
         slot=row["slot"],campaign_instance=manifest["campaign_instance"],
         frozen_inputs={"PERSIST_INPUT":"false" if any(row["execution_plan"].get(k) for k in ("pre_m04_accreditation_planned","run_prepare_electoral","run_incorporate")) else "true"})
     if not preparing:
      corrupted=copy.deepcopy(manifest)
      corrupted["territories"][0]["territorial_product"]["artifact_sha256"]="8"*64
      freeze(corrupted)
      with self.assertRaisesRegex(ValueError,"territorial_product"):
       validate_campaign_child(manifest=corrupted,plan=child,root=root,
         expected_sha=corrupted["manifest_sha256"],source_sha=corrupted["source_sha"],
         slot=row["slot"],campaign_instance=corrupted["campaign_instance"])
     changed=dict(effective,run_prepare_territorial=not preparing)
     with patch("herramientas.gestor_campana_nacional.campaign_execution_plan",return_value=changed):
      with self.assertRaisesRegex(ValueError,"el resolver común exige otra ruta"):
       validate_campaign_child(manifest=manifest,plan=child,root=root,
         expected_sha=manifest["manifest_sha256"],source_sha=manifest["source_sha"],
         slot=row["slot"],campaign_instance=manifest["campaign_instance"])

 def test_dispatch_contract_path_and_electoral_persistence(self):
  ROOT=frozen_root()  # Galicia pendiente de incorporar: caso congelado en aee8215e
  manager=(ROOT/".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  self.assertIn("campaign_contract_path: ${{ matrix.contract_path }}",manager)
  self.assertIn("persist_state: ${{ matrix.persist_state }}",manager)
  m=build_manifest(selected=["principado_de_asturias"],publication_mode="electoral",
                   source_sha="a"*40,strategy="Canónico",campaign_instance="electoral-resume",root=ROOT)
  row=m["territories"][0]
  self.assertEqual(row["preflight_status"],"PRODUCT_REUSE_READY")
  plan=campaign_execution_plan(root=ROOT,territory_id="principado_de_asturias",edition="2025",strategy="Canónico")
  self.assertEqual(row["territorial_product"]["run_id"],plan["existing"]["territorial_product"]["run_id"])
  self.assertFalse(row["execution_plan"]["run_generate"])
  self.assertEqual(row["execution_plan"]["run_incorporate"],not plan["catalog_state"]["electoral_product_available"])
  self.assertEqual(len(build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"]),1)
  m=build_manifest(selected=["galicia"],publication_mode="electoral",
                   source_sha="a"*40,strategy="Canónico",campaign_instance="electoral-resume-valid",root=ROOT)
  row=m["territories"][0]
  self.assertEqual(row["preflight_status"],"PRODUCT_REUSE_READY")
  matrix=build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"]
  self.assertTrue(row["execution_plan"]["run_incorporate"])
  self.assertTrue(matrix[0]["persist_state"])
  self.assertEqual(matrix[0]["contract_path"],row["contract_path"])
  galicia=build_manifest(selected=["galicia"],publication_mode="electoral",
                         source_sha="a"*40,strategy="Canónico",campaign_instance="electoral-rebuild",root=ROOT)
  row_g=galicia["territories"][0]
  self.assertEqual(row_g["preflight_status"],"PRODUCT_REUSE_READY")
  self.assertTrue(row_g["execution_plan"]["run_incorporate"])
  self.assertTrue(build_matrix(galicia,"EXECUTE_CAMPAIGN_CONFIRMED")["include"][0]["persist_state"])

 def test_workflow_persists_only_source_preparation(self):
  manager=(ROOT/".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  self.assertIn("persist_state: ${{ matrix.persist_state }}",manager)
  self.assertIn("publish_result: false",manager)
  self.assertIn("fail-fast: false",manager)

 def test_effective_campaign_persistence_is_not_overridden_by_dispatch(self):
  workflow=(ROOT/".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
  self.assertIn('elif [[ "$GITHUB_EVENT_NAME" == "workflow_dispatch" && -z "$CAMPAIGN_INSTANCE" ]]; then',workflow)
  self.assertIn('persist="$PERSIST_INPUT"',workflow)
  self.assertIn('if [[ "$pre_m04_planned" == "true" && "$persist" != "true"',workflow)
  import subprocess
  full=yaml.safe_load(workflow)
  step=next(x for x in full["jobs"]["planificar"]["steps"] if x.get("id")=="plan")
  run=step["run"]
  start=run.index('persist="$PERSIST_INPUT"')
  end=run.index('if [[ "$persist" == "true" && "$GITHUB_REF_NAME" != "main" ]]; then',start)
  script="set -euo pipefail\n"+run[start:end]+"\nprintf '%s' \"$persist\"\n"
  for event,campaign,requested,expected in (
      ("workflow_dispatch","campaign-123","false","false"),
      ("workflow_dispatch","campaign-123","true","true"),
      ("workflow_dispatch","","false","true"),
      ("pull_request","campaign-123","true","false")):
   with self.subTest(event=event,campaign=campaign,requested=requested):
    env={**os.environ,"GITHUB_EVENT_NAME":event,"CAMPAIGN_INSTANCE":campaign,
         "PERSIST_INPUT":requested,"PUBLISH_INPUT":"false"}
    result=subprocess.run(["bash","-c",script],env=env,text=True,capture_output=True,check=True)
    self.assertEqual(result.stdout,expected)

 def test_child_uses_manifest_when_explicit_reuse_inputs_are_absent(self):
  workflow=(ROOT/".github/workflows/ejecucion-completa-proyecto.yml").read_text(encoding="utf-8")
  self.assertIn("elif not campaign_instance or any((reuse_run_id, reuse_artifact, reuse_digest, reuse_source_sha)):",workflow)
  self.assertIn("validate_campaign_child(",workflow)
  self.assertIn("CAMPAIGN_MANIFEST_SHA256",workflow)
  self.assertIn("CAMPAIGN_SOURCE_ARTIFACT_SHA256",workflow)
  from herramientas.resolver_ejecucion_completa import apply_explicit_territorial_source
  with self.assertRaisesRegex(ValueError,"Procedencia explícita incompleta"):
   apply_explicit_territorial_source({},campaign_instance="campaign-test")
  with self.assertRaisesRegex(ValueError,"Procedencia explícita incompleta"):
   apply_explicit_territorial_source({},campaign_instance="campaign-test",reuse_run_id="123")

 def test_2025_canonical_14_routes_rebuild_stale_lineage_without_reusing_obsolete_products(self):
  ROOT = frozen_root()  # caso real congelado en aee8215e
  from herramientas.catalogo_territorios import load_master
  selected_codes={"03","04","05","06","08","09","12","13","14","15","16","17","18","19"}
  selected=[r["territory_id"] for r in load_master(ROOT/"configuracion/catalogo_territorios_espana_2025.yaml")
            if str(r["autonomous_community_code_ine"]) in selected_codes]
  m=build_manifest(selected=selected,publication_mode="electoral",source_sha="a"*40,
                   strategy="Canónico",campaign_instance="regression14",root=ROOT)
  self.assertEqual(len(m["territories"]),14)
  matrix=build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"]
  # El M08 antiguo no invalida M06: Cantabria y Castilla-La Mancha
  # recuperan ruta de producto, pero deben incorporar M08 nuevo.
  # Asturias recupera la ruta M06 al incluirse su manifiesto post-run probado.
  self.assertEqual(len(matrix),14)
  self.assertEqual({r["slot"] for r in matrix},selected_codes)
  all_by_slot={r["slot"]:r for r in m["territories"]}
  self.assertEqual({code for code,row in all_by_slot.items() if row["preflight_status"]=="BLOCKED"},set())
  # Regla, no recuento: cada ruta corresponde a su plan. Los recuentos cambian con cada
  # ejecución completa (p. ej. Melilla y Baleares al preparar fuente con contrato nuevo).
  for r in matrix:
   plan=r["execution_plan"]
   with self.subTest(slot=r["slot"]):
    if r["execution_route"]=="PRODUCT_REUSE_READY":
     self.assertFalse(plan["run_generate"])
    elif r["execution_route"]=="SOURCE_PREPARATION_REQUIRED":
     self.assertTrue(plan["run_prepare_territorial"])
     self.assertTrue(plan["run_generate"])
    else:
     self.assertEqual(r["execution_route"],"GENERATION_READY")
     self.assertFalse(plan["run_prepare_territorial"])
     self.assertTrue(plan["run_generate"])
  by_slot={r["slot"]:r for r in matrix}
  for code in ("06", "08"):
   row=by_slot[code]
   self.assertEqual(row["execution_route"],"PRODUCT_REUSE_READY")
   self.assertFalse(row["execution_plan"]["run_generate"])
   plan=campaign_execution_plan(root=ROOT,territory_id=row["territory_id"],edition="2025",strategy="Canónico")
   self.assertTrue(plan["catalog_state"]["territorial_product_available"])
   # Regla de linaje: se incorpora M08 nuevo sólo si no hay uno ligado al M06 vigente.
   if plan["catalog_state"]["electoral_product_available"]:
    self.assertFalse(row["execution_plan"]["run_incorporate"])
    self.assertEqual(plan["existing"]["electoral_product"]["run_id"],plan["existing"]["territorial_product"]["run_id"])
   else:
    self.assertTrue(row["execution_plan"]["run_incorporate"])
    self.assertTrue(row["persist_state"])
    self.assertFalse((plan["existing"].get("electoral_product") or {}).get("run_id"))
    rejected=plan["catalog_state"]["rejected_electoral_product"]
    self.assertFalse(rejected["reusable"])
    self.assertIn("DURABLE_LINEAGE_INCOMPATIBLE", rejected["reason"])
  self.assertEqual(by_slot["12"]["execution_route"],"PRODUCT_REUSE_READY")
  self.assertTrue(by_slot["12"]["execution_plan"]["run_incorporate"])
  self.assertEqual(by_slot["18"]["execution_route"],"GENERATION_READY")
  self.assertFalse(by_slot["18"]["execution_plan"]["run_prepare_territorial"])
  self.assertTrue(by_slot["18"]["execution_plan"]["run_generate"])
  self.assertFalse(by_slot["18"]["execution_plan"]["pre_m04_accreditation_planned"])
  self.assertTrue(by_slot["18"]["generation_contract"]["allowed"])
  self.assertEqual(aggregate(m,[])["status"],"FAIL")

 def test_obsolete_galicia_ceuta_products_are_deaccredited_from_producer_proof(self):
  ROOT = frozen_root()  # caso real congelado en aee8215e
  catalog=yaml.safe_load((ROOT/"configuracion/catalogo_preparacion.yaml").read_text())
  by_id={r["territory_id"]:r["editions"]["2025"] for r in catalog["territories"]}
  galicia=by_id["galicia"]
  self.assertTrue(galicia["territorial_product_available"])
  self.assertFalse(galicia["electoral_product_available"])
  territorial=json.loads((ROOT/galicia["evidence"]["territorial_product"]).read_text())
  electoral=json.loads((ROOT/galicia["evidence"]["electoral_product"]).read_text())
  producer=json.loads((ROOT/f"territorios/galicia/evidencia/ejecuciones_completas/{electoral['run_id']}.json").read_text())
  phase=next(p for p in producer["phases"] if p["name"].startswith("02 ·"))
  self.assertNotEqual(phase["run_id"],territorial["run_id"])
  self.assertNotEqual(phase["artifact_digest"].removeprefix("sha256:"),territorial["artifact_sha256"])
  ceuta=by_id["ceuta"]
  self.assertTrue(ceuta["territorial_sources_prepared"])
  self.assertFalse(ceuta["territorial_product_available"])
  obsolete=json.loads((ROOT/ceuta["evidence"]["territorial_product"]).read_text())
  producer=json.loads((ROOT/f"territorios/ceuta/evidencia/ejecuciones_completas/{obsolete['run_id']}.json").read_text())
  phase=next(p for p in producer["phases"] if p["name"].startswith("01 ·"))
  self.assertNotEqual(phase["run_id"],ceuta["preparation_evidence"]["run_id"])
  self.assertNotEqual(phase["artifact_digest"].removeprefix("sha256:"),ceuta["preparation_evidence"]["artifact_sha256"])

 def test_matrix_rejects_unblocked_route_mismatch_and_inconsistent_blockers(self):
  m=build_manifest(selected=["galicia"],publication_mode="electoral",
                   source_sha="a"*40,strategy="Canónico",campaign_instance="route-negative",root=ROOT)
  row=m["territories"][0]
  self.assertEqual(row["preflight_status"],"PRODUCT_REUSE_READY")
  drift=copy.deepcopy(m)
  drift["territories"][0]["execution_route"]="SOURCE_PREPARATION_REQUIRED"
  freeze(drift)
  with self.assertRaisesRegex(ValueError,"CAMPAIGN_ROUTE_UNSUPPORTED"):
   build_matrix(drift,"EXECUTE_CAMPAIGN_CONFIRMED")
  blocked=copy.deepcopy(m)
  blocked["territories"][0]["preflight_blockers"]=["ACREDITACION_REVOCADA"]
  freeze(blocked)
  with self.assertRaisesRegex(ValueError,"CAMPAIGN_ROUTE_BLOCKER_INCONSISTENT"):
   build_matrix(blocked,"EXECUTE_CAMPAIGN_CONFIRMED")

 def test_manifest_freezes_all_lineage_and_rejects_electoral_source_drift(self):
  from herramientas.gestor_campana_nacional import _campaign_lineage_identity
  m=build_manifest(selected=["galicia"],publication_mode="electoral",
                   source_sha="a"*40,strategy="Canónico",campaign_instance="lineage-check",root=ROOT)
  row=m["territories"][0]
  self.assertEqual(row["preflight_status"],"PRODUCT_REUSE_READY")
  self.assertEqual(set(row["execution_lineage"]),{"territorial_source","territorial_product","electoral_source","electoral_product"})
  original=copy.deepcopy(row["execution_lineage"])
  self.assertTrue(original["territorial_product"].get("artifact_sha256"))
  self.assertTrue(original["electoral_source"].get("artifact_sha256"))
  plan={"existing":{
   "territorial_source":original["territorial_source"],
   "territorial_product":original["territorial_product"],
   "electoral_source":dict(original["electoral_source"],artifact_sha256="f"*64),
   "electoral_product":original["electoral_product"]}}
  self.assertNotEqual(_campaign_lineage_identity(plan),row["execution_lineage"])
  self.assertEqual(_campaign_lineage_identity({"existing":original}),original)

 def test_galicia_child_consumed_electoral_source_sha_is_enforced(self):
  ROOT=frozen_root()  # Galicia pendiente de incorporar: caso congelado en aee8215e
  from herramientas.gestor_campana_nacional import campaign_execution_plan
  m=build_manifest(selected=["galicia"],publication_mode="electoral",
                   source_sha="a"*40,strategy="Canónico",campaign_instance="galicia-lineage",root=ROOT)
  row=m["territories"][0]
  self.assertEqual(row["preflight_status"],"PRODUCT_REUSE_READY")
  self.assertTrue(row["execution_plan"]["run_incorporate"])
  self.assertTrue(row["execution_lineage"]["electoral_source"]["artifact_sha256"])
  p=copy.deepcopy(campaign_execution_plan(root=ROOT,territory_id="galicia",
                                         edition="2025",strategy="Canónico"))
  p["publication_mode_effective"]="electoral"
  p["prepared_source_pair"]={k:v for k,v in row["evidence"].items()
                              if k not in ("kind","receipt_sha256")}
  # 00 may normalize decision status and retain the old electoral product
  # when M08 is scheduled to be rebuilt. Neither changes the consumed source.
  p["existing"]["electoral_source"]["decision"]="VALIDADO"
  p["existing"]["electoral_product"]={"run_id":0,"artifact_sha256":"f"*64}
  args=dict(manifest=m,root=ROOT,expected_sha=m["manifest_sha256"],
            source_sha=m["source_sha"],slot=row["slot"],
            campaign_instance=m["campaign_instance"])
  validate_campaign_child(plan=p,**args)
  tampered=copy.deepcopy(p)
  tampered["existing"]["electoral_source"]["artifact_sha256"]="f"*64
  with self.assertRaisesRegex(ValueError,
       r"CAMPAIGN_MANIFEST_MISMATCH: child_lineage.electoral_source.artifact_sha256"):
   validate_campaign_child(plan=tampered,**args)

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
    self.assertNotIn("reuse_run_id",json.dumps(manifest))
    expected_kind="prepared_source_pair" if mode=="electoral" else "territorial_source_receipt"
    self.assertEqual({r["evidence"]["kind"] for r in manifest["territories"]},{expected_kind})

 def test_ceuta_stale_m06_is_not_reused_and_new_generation_requires_accreditation(self):
  ROOT = frozen_root()  # caso real congelado en aee8215e
  from herramientas.resolver_ejecucion_completa import build_plan
  p=build_plan(territory="ceuta",edition="2025",execution_mode="reuse",
               catalog=ROOT/"configuracion/catalogo_preparacion.yaml",root_dir=ROOT,
               explicit_territorial_source={})
  self.assertFalse(p["catalog_state"]["territorial_product_available"])
  self.assertTrue(p["run_generate"])
  self.assertFalse(p["run_prepare_territorial"])
  self.assertFalse(p["pre_m04_accreditation_planned"])
  self.assertEqual(p["generation_gate"],{"allowed":True,"route":"validated_pre_m04_topology"})
  m=build_manifest(selected=["ceuta"],publication_mode="territorial_only",source_sha="a"*40,
                   strategy="Canónico",campaign_instance="regression",root=ROOT)
  r=m["territories"][0]
  self.assertEqual(r["preflight_status"],"GENERATION_READY")
  self.assertFalse(r["execution_plan"]["pre_m04_accreditation_planned"])
  self.assertTrue(r["generation_contract"]["allowed"])
  self.assertEqual(len(build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"]),1)

 def test_extremadura_reuse_does_not_authorize_generation(self):
  # M06 40656175842 adoptado: Canónico reutiliza sin generar; GerryChain genera sobre la fuente
  # ya preparada (sin volver a adquirirla) y en modo electoral queda bloqueado sin evidencia M08.
  cases={("territorial_only","Canónico"):("PRODUCT_REUSE_READY",False,1),
         ("territorial_only","GerryChain 50"):("GENERATION_READY",True,1),
         ("electoral","Canónico"):("PRODUCT_REUSE_READY",False,0),
         ("electoral","GerryChain 50"):("BLOCKED",True,0)}
  from tests._raiz_congelada import frozen_root
  frozen=frozen_root()
  for (mode,strategy),(status,allowed,included) in cases.items():
    with self.subTest(mode=mode,strategy=strategy):
     m=build_manifest(selected=["extremadura"],publication_mode=mode,source_sha="a"*40,
                      strategy=strategy,campaign_instance="regression",root=frozen)
     r=m["territories"][0]
     self.assertEqual(r["preflight_status"],status)
     self.assertEqual(r["generation_contract"]["allowed"],allowed)
     self.assertEqual(r["execution_plan"]["run_generate"],strategy!="Canónico")
     self.assertFalse(r["execution_plan"]["run_prepare_territorial"])
     self.assertEqual(len(build_matrix(m,"EXECUTE_CAMPAIGN_CONFIRMED")["include"]),included)
     if status=="BLOCKED":
      self.assertEqual(r["preflight_blockers"],["ACCREDITED_EVIDENCE_MISSING"])
     self.assertEqual(aggregate(m,[])["status"],"FAIL")

 def test_common_resolver_decision_is_authoritative_for_every_territory(self):
  from herramientas.catalogo_territorios import load_master
  from herramientas.gestor_campana_nacional import campaign_execution_plan, execution_route
  ids=[r["territory_id"] for r in load_master(ROOT/"configuracion/catalogo_territorios_espana_2025.yaml")]
  for strategy in ("Canónico","GerryChain 50"):
   m=build_manifest(selected=ids,publication_mode="territorial_only",source_sha="a"*40,
                    strategy=strategy,campaign_instance="regression",root=ROOT)
   for r in m["territories"]:
    with self.subTest(strategy=strategy,territory=r["territory_id"]):
     try:
      p=campaign_execution_plan(root=ROOT,territory_id=r["territory_id"],edition="2025",strategy=strategy)
     except ValueError as exc:
      self.assertEqual(r["preflight_status"],"BLOCKED")
      self.assertIn(str(exc)," ".join(r["preflight_blockers"]))
     else:
      self.assertEqual(r["execution_route"],execution_route(p))
      if execution_route(p)!="GENERATION_READY":
       self.assertEqual(r["preflight_status"],execution_route(p))

 def test_child_rechecks_common_plan_after_manifest_freeze(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as td:
   root=Path(td); m,p=generation_fixture(root)
   with patch("herramientas.gestor_campana_nacional.build_plan",
              side_effect=ValueError("CONTINUE_DURABLE_BLOCK: identity drift")):
    with self.assertRaisesRegex(ValueError,"CAMPAIGN_GENERATION_CONTRACT_BLOCK.*identity drift"):
     validate_campaign_child(manifest=m,plan=p,root=root,expected_sha=m["manifest_sha256"],
                             source_sha=m["source_sha"],slot="06",campaign_instance="fixture")

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
  self.assertIn("name: 0 Gestor de Campañas",text)
  self.assertIn("fail-fast: false",text); self.assertIn("max-parallel: 5",text)
  self.assertIn("publish_result: false",text); self.assertIn("persist_state: ${{ matrix.persist_state }}",text)
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
  self.assertNotIn("  recuperar_portfolio:",text)
  self.assertNotIn("  publicar_recuperacion:",text)

 def test_minimal_campaign_form_aggregates_without_publication(self):
  text=Path(".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  form=text[text.index("  workflow_dispatch:"):text.index("  pull_request:")]
  for required in ("campana:","estrategia:","publication_mode:","territorios:"):
   self.assertIn(required,form)
  for forbidden in ("confirmacion:","portfolio_run_id:","portfolio_artifact_id:","portfolio_source_sha:"):
   self.assertNotIn(forbidden,form)
  summary=text[text.index("  resumen:"):]
  self.assertIn("always()",summary)
  self.assertNotIn("strategy == 'GerryChain 50'",summary)
  self.assertIn("ddd-campaign-summary-",summary)
  self.assertNotIn("  promover_galerias:",text)
  self.assertNotIn("  publicar_galerias:",text)
  self.assertNotIn("_reutilizable-publicar-sitio.yml",text)

 def test_workflow_aggregate_uses_import_safe_package_invocation(self):
  text=(ROOT/".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  summary=text[text.index("  resumen:"):]
  self.assertIn("python -m herramientas.gestor_campana_nacional aggregate",summary)
  self.assertNotIn("python herramientas/gestor_campana_nacional.py aggregate",summary)
  self.assertIn("needs: [preparar, territorios]",summary)
  self.assertIn("always()",summary)
  self.assertIn("if-no-files-found: error",summary)
  self.assertNotIn("  promover_galerias:",text)
  self.assertNotIn("  publicar_galerias:",text)

 def test_campaign_summary_upload_precedes_terminal_failure_gate(self):
  text=(ROOT/".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  summary=text[text.index("  resumen:"):]
  upload=summary.index("name: ddd-campaign-summary-")
  terminal=summary.index("CAMPAIGN_ZERO_EXECUTABLE")
  self.assertLess(upload,terminal)
  self.assertIn("CAMPAIGN_INCOMPLETE",summary)
  self.assertIn(".completion_status == \"COMPLETE\" and .status == \"PASS\"",summary)
  self.assertIn("needs.preparar.outputs.ready_count",summary)
  self.assertIn("jq '.territories | length' .ddd-campaign/campaign-manifest.json",summary)
  self.assertNotIn("  publicar_galerias:",text)

 def test_mixed_states_are_valid_summary_but_not_certified(self):
  m={"campaign_instance":"mixed","source_sha":"a"*40,"optimization_algorithm":"Canónico",
     "territories":[
       {"territory_id":t,"slot":str(i).zfill(2),"publication_mode":"electoral",
        "preflight_status":"BLOCKED" if t=="blocked" else "GENERATION_READY",
        "preflight_blockers":["SOURCE_BLOCK"] if t=="blocked" else []}
       for i,t in enumerate(("pass","blocked","missing","fail"),1)]}
  freeze(m)
  def report(t,status):
   return {"territory_id":t,"status":status,"slot":next(r["slot"] for r in m["territories"] if r["territory_id"]==t),
           "publication_mode":"electoral","campaign_instance":"mixed",
           "source_sha":"a"*40,"manifest_sha256":m["manifest_sha256"]}
  result=aggregate(m,[report("pass","PASS"),report("fail","FAIL")])
  self.assertEqual([r["status"] for r in result["territories"]],["PASS","BLOCKED","MISSING","FAIL"])
  self.assertEqual(result["integrity_status"],"VALID")
  self.assertEqual(result["completion_status"],"FAILED")
  self.assertEqual(result["status"],"FAIL")
  with self.assertRaises(ValueError):
   validate_campaign_summary_for_promotion(result)
  partial=aggregate(m,[report("pass","PASS")])
  self.assertEqual(partial["completion_status"],"PARTIAL")
  self.assertEqual(partial["integrity_status"],"VALID")
  corrupted=aggregate(m,[report("pass","PASS"),{**report("fail","FAIL"),"source_sha":"b"*40}])
  self.assertEqual(corrupted["integrity_status"],"INVALID")
  self.assertIn("CAMPAIGN_MANIFEST_MISMATCH:fail",corrupted["integrity_errors"])
  with self.assertRaises(ValueError):
   validate_campaign_summary_for_promotion(corrupted)

 def test_aggregate_cli_exit_status_tracks_integrity_not_completion(self):
  for corrupt in (False,True):
   with self.subTest(corrupt=corrupt), tempfile.TemporaryDirectory() as td:
    root=Path(td); reports=root/"reports"; reports.mkdir()
    m={"campaign_instance":"cli","source_sha":"a"*40,"optimization_algorithm":"Canónico",
       "territories":[
        {"territory_id":"pass","slot":"01","publication_mode":"electoral",
         "preflight_status":"GENERATION_READY","preflight_blockers":[]},
        {"territory_id":"blocked","slot":"02","publication_mode":"electoral",
         "preflight_status":"BLOCKED","preflight_blockers":["SOURCE_BLOCK"]}]}
    freeze(m)
    manifest_path=root/"manifest.json"; manifest_path.write_text(json.dumps(m))
    report={"territory_id":"pass","slot":"01","publication_mode":"electoral","status":"PASS",
      "campaign_instance":"cli","source_sha":"b"*40 if corrupt else "a"*40,
      "manifest_sha256":m["manifest_sha256"]}
    (reports/"campaign_status.json").write_text(json.dumps(report))
    output_json=root/"summary.json";output_md=root/"summary.md"
    cmd=[sys.executable,"-m","herramientas.gestor_campana_nacional",
         "aggregate","--manifest",str(manifest_path),"--reports-root",str(reports),
         "--output-json",str(output_json),"--output-md",str(output_md)]
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    self.assertEqual(result.returncode,2 if corrupt else 0,result.stderr)
    summary=json.loads(output_json.read_text())
    self.assertEqual(summary["integrity_status"],"INVALID" if corrupt else "VALID")
    self.assertEqual(summary["completion_status"],"FAILED" if corrupt else "PARTIAL")
    self.assertEqual([r["status"] for r in summary["territories"]],
                     ["FAIL","BLOCKED"] if corrupt else ["PASS","BLOCKED"])
    self.assertTrue(output_md.is_file())
    with self.assertRaises(ValueError):
     validate_campaign_summary_for_promotion(summary)

 def test_failed_campaign_cannot_replace_previous_certified_publication(self):
  summary={"status":"FAIL","territory_count_expected":2,"territories":[
    {"territory_id":"a","status":"PASS"},{"territory_id":"b","status":"FAIL"}]}
  with self.assertRaises(ValueError):
   validate_campaign_summary_for_promotion(summary)
  text=Path(".github/workflows/gestor-campanas.yml").read_text(encoding="utf-8")
  self.assertNotIn("  promover_galerias:",text)
  self.assertNotIn("  publicar_galerias:",text)
  self.assertNotIn("  resultado_publicacion:",text)
  self.assertIn("publish_result: false",text)
  self.assertIn("persist_state: ${{ matrix.persist_state }}",text)

if __name__=="__main__": unittest.main()
