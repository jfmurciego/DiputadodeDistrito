#!/usr/bin/env python3
"""Gestor de campaña nacional — versión 0.0.1, 2026-10-10.
Alcance: preflight local; estado: candidato.
Cambio/motivo: consumir el plan común y distinguir reuso, generación y preparación.
Anterior: legacy/herramientas/gestor_campana_nacional_v0.0.0.py (sin versión declarada).
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any
import yaml
try:
    from herramientas.catalogo_territorios import load_master
except ModuleNotFoundError:
    from catalogo_territorios import load_master
try:
    from herramientas.resolver_ejecucion_completa import generation_ready_contract, build_plan
except ModuleNotFoundError:
    from resolver_ejecucion_completa import generation_ready_contract, build_plan

MASTER=Path("configuracion/catalogo_territorios_espana_2025.yaml")
CATALOG=Path("configuracion/catalogo_preparacion.yaml")
CONFIRMATION="EXECUTE_CAMPAIGN_CONFIRMED"
MODES={"electoral","territorial_only"}
STRATEGIES={
 "Canónico":("",0,False),
 "GerryChain":("",1,False),
 "GerryChain 25":("",25,False),
 "GerryChain 50":("gerrychain_50",50,True),
}

def _yaml(path:Path)->dict[str,Any]:
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data,dict): raise ValueError(f"YAML inválido: {path}")
    return data

def _sha_payload(data:dict[str,Any])->str:
    raw=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

def validate_manifest_digest(manifest:dict[str,Any],expected_sha:str|None=None)->None:
    body={k:v for k,v in manifest.items() if k!="manifest_sha256"}
    digest=_sha_payload(body)
    if manifest.get("manifest_sha256")!=digest or (expected_sha is not None and expected_sha!=digest):
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: manifest_sha256")

def validate_campaign_child(*,manifest:dict[str,Any],plan:dict[str,Any],root:Path,
                            expected_sha:str,source_sha:str,slot:str,campaign_instance:str,
                            frozen_inputs:dict[str,str]|None=None)->None:
    """Compara referencias congeladas; la habilitación pertenece al validador común."""
    validate_manifest_digest(manifest,expected_sha)
    for key,value in (("source_sha",source_sha),("campaign_instance",campaign_instance),
                      ("data_edition",str(plan.get("edition") or "")),
                      ("optimization_algorithm",plan.get("optimization_algorithm"))):
        if manifest.get(key)!=value:
            raise ValueError(f"CAMPAIGN_MANIFEST_MISMATCH: {key}")
    matches=[r for r in manifest["territories"]
             if r["territory_id"]==plan.get("territory_id") and r["slot"]==slot]
    if len(matches)!=1:
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: territory/slot")
    row=matches[0]
    if row["preflight_status"] not in {"GENERATION_READY","PRODUCT_REUSE_READY","SOURCE_PREPARATION_REQUIRED"} or row.get("preflight_blockers"):
        raise ValueError("CAMPAIGN_GENERATION_CONTRACT_BLOCK: entrada bloqueada")
    if plan.get("publication_mode_effective")!=row["publication_mode"]:
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: publication_mode")
    if frozen_inputs is not None:
        expected_persist="true" if any(row["execution_plan"].get(k) for k in ("pre_m04_accreditation_planned","run_prepare_electoral","run_incorporate")) else "false"
        if str(frozen_inputs.get("PERSIST_INPUT") or "").lower()!=expected_persist:
            raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: persist_state")
        refs=row["generation_contract"]
        source=refs.get("source") or {}
        expected={"CAMPAIGN_CONTRACT_PATH":row["contract_path"],
                  "CAMPAIGN_CONTRACT_SHA256":refs.get("contract_sha256"),
                  "CAMPAIGN_GENERATION_EVIDENCE_PATH":refs.get("generation_evidence_path"),
                  "CAMPAIGN_GENERATION_EVIDENCE_SHA256":refs.get("generation_evidence_sha256")}
        for key in ("run_id","artifact_name","artifact_sha256","package_sha256"):
            expected["CAMPAIGN_SOURCE_"+key.upper()]=source.get(key)
        for key in ("receipt_path","receipt_sha256"):
            expected["CAMPAIGN_EVIDENCE_"+key.upper()]=row["evidence"].get(key)
        for key in ("territorial_identity_sha256","electoral_identity_sha256","pair_sha256"):
            expected["CAMPAIGN_"+key.upper()]=row["evidence"].get(key)
        for key,value in expected.items():
            if str(frozen_inputs.get(key) or "")!=str(value or ""):
                raise ValueError(f"CAMPAIGN_MANIFEST_MISMATCH: caller.{key}")
    state=(_catalog_index(root).get(row["territory_id"],{}).get("editions") or {}).get(manifest["data_edition"]) or {}
    try:
        effective=campaign_execution_plan(root=root,territory_id=row["territory_id"],
                                          edition=manifest["data_edition"],strategy=manifest["optimization_algorithm"])
    except (ValueError,OSError,yaml.YAMLError) as exc:
        raise ValueError(f"CAMPAIGN_GENERATION_CONTRACT_BLOCK: {exc}") from exc
    route=row["preflight_status"]
    if row.get("execution_route")!=route:
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: frozen_route")
    if execution_route(effective)!=route:
        raise ValueError("CAMPAIGN_GENERATION_CONTRACT_BLOCK: el resolver común exige otra ruta")
    if "execution_lineage" in row and _campaign_lineage_identity(effective)!=row["execution_lineage"]:
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: execution_lineage")
    # Only existing assets consumed by this child must retain their frozen identity.
    # 00 can legitimately retain stale products in existing while rebuilding M06/M08,
    # and can normalize a source's mutable decision status after selecting a pair.
    consumed_phases={
        "territorial_source":"run_prepare_territorial",
        "territorial_product":"run_generate",
        "electoral_source":"run_prepare_electoral",
        "electoral_product":"run_incorporate",
    }
    immutable=("run_id","artifact_name","artifact_sha256","package_sha256",
               "source_commit","election_id")
    frozen_lineage=row.get("execution_lineage") or {}
    child_existing=plan.get("existing") or {}
    for asset, rebuild_phase in consumed_phases.items():
        if asset.startswith("electoral_") and row["publication_mode"]!="electoral":
            continue
        if bool(plan.get(rebuild_phase,row["execution_plan"].get(rebuild_phase,False))):
            continue
        frozen_asset=frozen_lineage.get(asset) or {}
        if not frozen_asset:
            continue
        child_asset=child_existing.get(asset) or {}
        for field in immutable:
            if field in frozen_asset and child_asset.get(field)!=frozen_asset[field]:
                raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: child_lineage."+asset+"."+field)
    if effective.get("contract_path")!=row["contract_path"] or plan.get("contract_path")!=row["contract_path"]:
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: contract_path")
    for key in ("run_prepare_territorial","run_generate","run_prepare_electoral","run_incorporate","pre_m04_accreditation_planned"):
        if bool(effective.get(key))!=bool(row["execution_plan"].get(key)):
            raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: execution_plan."+key)
        if key in plan and bool(plan.get(key))!=bool(effective.get(key)):
            raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: child_execution_plan."+key)
    gate=effective.get("generation_gate") or {}
    if route=="PRODUCT_REUSE_READY" and not (gate.get("allowed") and gate.get("route")=="certified_product_lineage"):
        raise ValueError("CAMPAIGN_ROUTE_CONTRACT_BLOCK: producto sin linaje certificado")
    if route=="SOURCE_PREPARATION_REQUIRED" and not (
            effective.get("run_prepare_territorial") and effective.get("run_generate")
            and gate.get("allowed") and gate.get("route")=="planned_pre_m04_accreditation"):
        raise ValueError("CAMPAIGN_ROUTE_CONTRACT_BLOCK: preparación pre-M04 no habilitada")
    if route=="PRODUCT_REUSE_READY":
        frozen=row.get("territorial_product") or {}
        current=(effective.get("existing") or {}).get("territorial_product") or {}
        if not all(frozen.get(k) for k in ("run_id","artifact_name","artifact_sha256")):
            raise ValueError("CAMPAIGN_GENERATION_CONTRACT_BLOCK: producto sin identidad")
        actual_child_product=(plan.get("existing") or {}).get("territorial_product") or {}
        for key in ("run_id","artifact_name","artifact_sha256"):
            if str(current.get(key) or "")!=str(frozen.get(key) or ""):
                raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: territorial_product."+key)
            if str(actual_child_product.get(key) or "")!=str(frozen.get(key) or ""):
                raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: child_product."+key)
    elif route=="SOURCE_PREPARATION_REQUIRED":
        if not effective.get("pre_m04_accreditation_planned"):
            raise ValueError("CAMPAIGN_GENERATION_CONTRACT_BLOCK: pre-M04 no planificado")
    else:
        actual=generation_ready_contract(root_dir=root,state=state,territory_id=row["territory_id"])
        if not actual.get("allowed") or actual.get("status")!="GENERATION_READY":
            raise ValueError("CAMPAIGN_GENERATION_CONTRACT_BLOCK: validación efectiva ausente")
        if actual!=row["generation_contract"] or plan.get("contract_path")!=actual["contract_path"]:
            raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: generation_contract")
    if _evidence_identity(root,state,row["publication_mode"])!=row["evidence"]:
        raise ValueError("CAMPAIGN_MANIFEST_MISMATCH: evidence receipt")
    # La fuente resuelta por 00 debe ser la misma que habilitó generación,
    # no basta con comprobar el catálogo y consumir luego otro receipt.
    resolved=(plan.get("existing") or {}).get("territorial_source") or {}
    if route=="GENERATION_READY":
        for key in ("run_id","artifact_name","artifact_sha256","package_sha256","source_commit"):
            if str(resolved.get(key) or "")!=str(actual["source"].get(key) or ""):
                raise ValueError(f"CAMPAIGN_MANIFEST_MISMATCH: resolved_source.{key}")
    evidence=row["evidence"]
    prepared=plan.get("prepared_source_pair" if row["publication_mode"]=="electoral" else "prepared_territorial_source") or {}
    keys=("receipt_path","territorial_identity_sha256")
    if row["publication_mode"]=="electoral":
        keys+=("pair_sha256","electoral_identity_sha256")
    if route!="SOURCE_PREPARATION_REQUIRED":
        for key in keys:
            if not evidence.get(key) or prepared.get(key)!=evidence[key]:
                raise ValueError(f"CAMPAIGN_MANIFEST_MISMATCH: prepared.{key}")

def _catalog_index(root:Path)->dict[str,dict[str,Any]]:
    data=_yaml(root/CATALOG)
    return {str(r["territory_id"]):r for r in data.get("territories") or []}

def canonical_selection(selected:list[str],root:Path=Path("."))->list[dict[str,Any]]:
    master=load_master(root/MASTER)
    wanted=set(selected)
    known={str(r["territory_id"]) for r in master}
    unknown=sorted(wanted-known)
    if unknown: raise ValueError("Territorios no registrados: "+", ".join(unknown))
    rows=[r for r in master if str(r["territory_id"]) in wanted]
    if not 1<=len(rows)<=19: raise ValueError("La campaña debe seleccionar entre 1 y 19 territorios")
    return rows

def _expected_k(root:Path,contract_path:str)->int:
    c=_yaml(root/contract_path)
    validation=c.get("validation") or {}
    if validation.get("expected_districts") is not None: return int(validation["expected_districts"])
    modules=c.get("modulos") or {}
    for name,key in (("modulo_05_optimizar_distritos","expected_districts"),("modulo_04_generar_semillas","k_districts")):
        value=(modules.get(name) or {}).get(key)
        if value is not None: return int(value)
    raise ValueError(f"{contract_path}: contrato sin K")

def evidence_reference(state:dict[str,Any],mode:str)->tuple[str|None,str]:
    if mode=="electoral":
        ref=str((state.get("evidence") or {}).get("prepared_source_pair") or "")
        return (ref or None,"prepared_source_pair")
    prep=state.get("preparation_evidence") or {}
    ref=str(prep.get("receipt_path") or "")
    return (ref or None,"territorial_source_receipt")

def _evidence_identity(root:Path,state:dict[str,Any],mode:str)->dict[str,Any]:
    ref,kind=evidence_reference(state,mode)
    result={"kind":kind,"receipt_path":ref}
    if not ref or not (root/ref).is_file():
        return result
    data=json.loads((root/ref).read_text(encoding="utf-8"))
    result["receipt_sha256"]=hashlib.sha256((root/ref).read_bytes()).hexdigest()
    if mode=="electoral":
        pair=data.get("pair") if data.get("pair") else data
        territorial=(pair or {}).get("territorial_source") or {}
        electoral=(pair or {}).get("electoral_source") or {}
        result.update({
            "pair_sha256":(pair or {}).get("pair_sha256"),
            "territorial_identity_sha256":territorial.get("territorial_identity_sha256"),
            "electoral_identity_sha256":electoral.get("electoral_identity_sha256"),
        })
    else:
        result["territorial_identity_sha256"]=data.get("territorial_identity_sha256")
    return result

def campaign_execution_plan(*,root:Path,territory_id:str,edition:str,strategy:str)->dict[str,Any]:
    """Planificación pura: misma continuidad y estrategia que el caller común."""
    return build_plan(
        territory=territory_id,edition=edition,execution_mode="reuse",
        catalog=root/CATALOG,root_dir=root,optimization_algorithm=strategy,
        force_selected_algorithm=False,explicit_territorial_source={},
    )


def execution_route(plan:dict[str,Any])->str:
    if plan["run_prepare_territorial"]:
        return "SOURCE_PREPARATION_REQUIRED"
    if plan["run_generate"]:
        return "GENERATION_READY"
    return "PRODUCT_REUSE_READY"


def _campaign_lineage_identity(plan:dict[str,Any])->dict[str,Any]:
    """Identidades inmutables de todos los activos usados al resolver la campaña."""
    existing=plan.get("existing") or {}
    fields=("run_id","artifact_name","artifact_sha256","package_sha256",
            "source_commit","election_id","decision")
    return {name:{key:value[key] for key in fields if key in value}
            for name,value in sorted(existing.items()) if isinstance(value,dict) and value}


def build_manifest(*,selected:list[str],publication_mode:str,source_sha:str,strategy:str,
                   campaign_instance:str,root:Path=Path("."),edition:str="2025")->dict[str,Any]:
    if publication_mode not in MODES: raise ValueError("Modo de publicación no permitido")
    if strategy not in STRATEGIES: raise ValueError("Estrategia no permitida")
    if len(source_sha)!=40 or any(c not in "0123456789abcdef" for c in source_sha.lower()):
        raise ValueError("source_sha inválido")
    catalog=_catalog_index(root)
    territories=[]
    for master in canonical_selection(selected,root):
        tid=str(master["territory_id"]); code=str(master["autonomous_community_code_ine"])
        cat=catalog.get(tid) or {}
        state=(cat.get("editions") or {}).get(edition) or {}
        contract=str(state.get("contract_path") or "")
        evidence=_evidence_identity(root,state,publication_mode)
        blockers=[]
        plan={}
        status="BLOCKED"
        generation={"allowed":False}
        try:
            plan=campaign_execution_plan(root=root,territory_id=tid,edition=edition,strategy=strategy)
            status=execution_route(plan)
        except (ValueError,OSError,yaml.YAMLError) as exc:
            blockers.append("COMMON_RESOLVER_BLOCK:"+str(exc))
        if status=="GENERATION_READY":
            if not evidence.get("receipt_path"): blockers.append("ACCREDITED_EVIDENCE_MISSING")
            elif not (root/str(evidence["receipt_path"])).is_file(): blockers.append("ACCREDITED_EVIDENCE_NOT_MATERIALIZED")
            generation=generation_ready_contract(root_dir=root,state=state,territory_id=tid)
            if not generation.get("allowed"):
                blockers.append("GENERATION_NOT_READY:"+str(generation.get("capability") or "UNKNOWN"))
        if blockers:
            status="BLOCKED"
        territories.append({
          "slot":code,"codauto":code,"territory_id":tid,"territory_name":str(master["name"]),
          "publication_mode":publication_mode,"contract_path":contract,
          "evidence":evidence,
          "generation_contract":generation,
          "territorial_product":dict((plan.get("existing") or {}).get("territorial_product") or {}),
          "execution_lineage":_campaign_lineage_identity(plan) if plan else {},
          "preflight_status":status,
          "execution_route":execution_route(plan) if plan else "BLOCKED",
          "execution_plan":{key:plan[key] for key in (
              "run_prepare_territorial","run_generate","run_prepare_electoral","run_incorporate",
              "pre_m04_accreditation_planned","generation_gate") if key in plan},
          "preflight_blockers":blockers,
          "expected_district_count":_expected_k(root,contract) if contract else 0,
        })
    body={
      "schema":"ddd.campaign-manifest/2.0",
      "campaign_id":"national-selection",
      "campaign_instance":campaign_instance,
      "source_sha":source_sha.lower(),
      "data_edition":edition,
      "execution_mode":"Reutilizar progreso existente",
      "optimization_algorithm":strategy,
      "fail_fast":False,"max_parallel":5,"retry_failed":False,
      "campaign_confirmation":CONFIRMATION,
      "territories":territories,
      "source_authority":"00_common_prepared_source_contracts",
      "generation_enablement_contract":"generation_ready_contract/v1",
    }
    body["manifest_sha256"]=_sha_payload(body)
    return body

def build_matrix(manifest:dict[str,Any],confirmation:str)->dict[str,Any]:
    if confirmation!=CONFIRMATION: raise ValueError("Falta confirmación explícita")
    validate_manifest_digest(manifest)
    entrypoint,count,unique=STRATEGIES[manifest["optimization_algorithm"]]
    include=[]
    for row in manifest["territories"]:
        status=row["preflight_status"]
        if status=="BLOCKED":
            continue
        if status not in {"GENERATION_READY","PRODUCT_REUSE_READY","SOURCE_PREPARATION_REQUIRED"} or row.get("execution_route")!=status:
            raise ValueError("CAMPAIGN_ROUTE_UNSUPPORTED: "+str(row.get("slot")))
        if row.get("preflight_blockers"):
            raise ValueError("CAMPAIGN_ROUTE_BLOCKER_INCONSISTENT: "+str(row.get("slot")))
        # No route may run without a frozen, materialized source/pair receipt.
        evidence=row.get("evidence") or {}
        if not evidence.get("receipt_path") or not evidence.get("receipt_sha256"):
            continue
        tid=row["territory_id"]; slot=row["slot"]; ci=manifest["campaign_instance"]
        include.append({
          **row,"campaign_instance":ci,"namespace":f"{ci}/{slot}/{tid}",
          "artifact_namespace":f"{ci}--{slot}--{tid}",
          "source_sha":manifest["source_sha"],"manifest_sha256":manifest["manifest_sha256"],
          "data_edition":manifest["data_edition"],"execution_mode":manifest["execution_mode"],
          "optimization_algorithm":manifest["optimization_algorithm"],"entrypoint":entrypoint,
          "candidate_count":count,"require_unique_hashes":unique,"retry_failed":False,
          "persist_state":any(row["execution_plan"].get(k) for k in ("pre_m04_accreditation_planned","run_prepare_electoral","run_incorporate")),
        })
    return {"include":include}

def aggregate(manifest:dict[str,Any],reports:list[dict[str,Any]])->dict[str,Any]:
    validate_manifest_digest(manifest)
    by_id={str(r.get("territory_id")):r for r in reports if r.get("territory_id")}
    selected={r["territory_id"] for r in manifest["territories"]}
    unexpected=sorted(set(by_id)-selected)
    duplicates=sorted(tid for tid in by_id if sum(r.get("territory_id")==tid for r in reports)>1)
    rows=[]; failed=list(dict.fromkeys(unexpected+duplicates))
    integrity_errors=[*(f"UNEXPECTED_TERRITORY:{t}" for t in unexpected),
                      *(f"DUPLICATE_REPORT:{t}" for t in duplicates)]
    for expected in manifest["territories"]:
        tid=expected["territory_id"]
        if expected["preflight_status"] not in {"GENERATION_READY","PRODUCT_REUSE_READY","SOURCE_PREPARATION_REQUIRED"}:
            item={**expected,"status":"BLOCKED","reason":", ".join(expected["preflight_blockers"]) or expected["preflight_status"]}
        else:
            observed=by_id.get(tid)
            if observed is None:
                item={**expected,"status":"MISSING","reason":"campaign_status.json ausente"}
            else:
                item={**expected,**observed}
                terminal=item.get("status")
                binding={"campaign_instance":manifest["campaign_instance"],
                         "source_sha":manifest["source_sha"],"manifest_sha256":manifest["manifest_sha256"],
                         "slot":expected["slot"],"publication_mode":expected["publication_mode"]}
                mismatch=any(observed.get(k)!=v for k,v in binding.items())
                if tid in duplicates or mismatch:
                    item["status"]="FAIL"
                    item["reason"]="CAMPAIGN_MANIFEST_MISMATCH: resultado duplicado o de otra identidad"
                    integrity_errors.append(f"CAMPAIGN_MANIFEST_MISMATCH:{tid}")
                elif terminal!="PASS":
                    item["status"]="FAIL" if terminal else "MISSING"
                    item["reason"]=item.get("reason") or "estado terminal PASS ausente"
                elif manifest.get("optimization_algorithm")=="GerryChain 50" and (
                    observed.get("candidate_count_expected")!=50
                    or observed.get("candidate_count_valid")!=50
                    or observed.get("unique_candidate_hash_count")!=50
                    or observed.get("missing_candidate_hash_count")!=0
                    or observed.get("duplicate_candidate_hash_count")!=0
                ):
                    item["status"]="FAIL"
                    item["reason"]="portfolio incompleto o sin 50 candidatos únicos"
        rows.append(item)
        if item.get("status")!="PASS": failed.append(tid)
    return {
      "schema":"ddd.campaign-summary/2.0","campaign_instance":manifest["campaign_instance"],
      "source_sha":manifest["source_sha"],"manifest_sha256":manifest["manifest_sha256"],
      "territory_count_expected":len(manifest["territories"]),
      "territory_count_reported":len(by_id),"failed_territories":failed,
      "status":"PASS" if not failed else "FAIL",
      "integrity_status":"INVALID" if integrity_errors else "VALID",
      "integrity_errors":integrity_errors,
      "completion_status":("COMPLETE" if not failed else
                           "FAILED" if unexpected or duplicates or any(r["status"]=="FAIL" for r in rows)
                           else "PARTIAL"),
      "territories":rows,
    }

def validate_campaign_summary_for_promotion(summary:dict[str,Any])->list[dict[str,Any]]:
    rows=summary.get("territories")
    expected=int(summary.get("territory_count_expected") or 0)
    if summary.get("status")!="PASS": raise ValueError("La campaña no está en PASS")
    if not isinstance(rows,list) or not 1<=expected<=19 or len(rows)!=expected:
        raise ValueError("Cardinalidad territorial inconsistente")
    seen=set()
    for row in rows:
        tid=str(row.get("territory_id") or "")
        if not tid or tid in seen or row.get("status")!="PASS":
            raise ValueError("Estado territorial no promocionable")
        seen.add(tid)
    return rows

def publication_matrix(releases:list[dict[str,Any]],expected_count:int|None=None,
                       expected_territories:list[str]|None=None)->dict[str,Any]:
    if not 1<=len(releases)<=19: raise ValueError("La publicación exige entre 1 y 19 releases")
    if expected_count is not None and len(releases)!=expected_count:
        raise ValueError("No se publican resultados parciales")
    for key in ("release_tag","namespace","territory_id"):
        values=[str(r.get(key) or "") for r in releases]
        if not all(values) or len(set(values))!=len(values): raise ValueError(f"{key} ausente o duplicado")
    if expected_territories is not None and {r["territory_id"] for r in releases}!=set(expected_territories):
        raise ValueError("La publicación no coincide con los territorios seleccionados")
    return {"include":releases}

def _load_json(path:Path)->dict[str,Any]:
    data=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data,dict): raise ValueError("JSON debe ser objeto")
    return data

def main()->None:
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    plan=sub.add_parser("plan"); plan.add_argument("--selected-json",required=True); plan.add_argument("--publication-mode",required=True)
    plan.add_argument("--source-sha",required=True); plan.add_argument("--strategy",required=True); plan.add_argument("--campaign-instance",required=True)
    plan.add_argument("--confirmation",required=True); plan.add_argument("--output-manifest",type=Path,required=True)
    agg=sub.add_parser("aggregate"); agg.add_argument("--manifest",type=Path,required=True); agg.add_argument("--reports-root",type=Path,required=True)
    agg.add_argument("--output-json",type=Path,required=True); agg.add_argument("--output-md",type=Path,required=True)
    a=p.parse_args()
    if a.cmd=="plan":
        selected=json.loads(a.selected_json)
        manifest=build_manifest(selected=selected,publication_mode=a.publication_mode,source_sha=a.source_sha,
          strategy=a.strategy,campaign_instance=a.campaign_instance)
        a.output_manifest.parent.mkdir(parents=True,exist_ok=True)
        a.output_manifest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(build_matrix(manifest,a.confirmation),ensure_ascii=False,separators=(",",":")))
        return
    manifest=_load_json(a.manifest)
    reports=[]
    for path in a.reports_root.rglob("campaign_status.json"):
        try: reports.append(_load_json(path))
        except Exception: pass
    summary=aggregate(manifest,reports)
    a.output_json.parent.mkdir(parents=True,exist_ok=True)
    a.output_json.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# Campaña "+summary["campaign_instance"],"","- estado: "+summary["status"],"",
           "| Slot | Territorio | Estado |","|---|---|---|"]
    for row in summary["territories"]:
        lines.append(f"| {row.get('slot','')} | {row.get('territory_name',row.get('territory_id',''))} | {row.get('status','')} |")
    a.output_md.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))
    # El resultado territorial no altera la integridad del resumen.
    # Las identidades incompatibles siguen bloqueadas.
    raise SystemExit(0 if summary["integrity_status"] == "VALID" else 2)

if __name__=="__main__": main()
