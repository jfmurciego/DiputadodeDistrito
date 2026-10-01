#!/usr/bin/env python3
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
    from herramientas.resolver_ejecucion_completa import generation_ready_contract
except ModuleNotFoundError:
    from resolver_ejecucion_completa import generation_ready_contract

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
        if not contract: blockers.append("CONTRACT_MISSING")
        if not evidence.get("receipt_path"): blockers.append("ACCREDITED_EVIDENCE_MISSING")
        elif not (root/str(evidence["receipt_path"])).is_file(): blockers.append("ACCREDITED_EVIDENCE_NOT_MATERIALIZED")
        generation={"allowed":False}
        if contract:
            generation=generation_ready_contract(root_dir=root,state=state,territory_id=tid)
            if not generation.get("allowed"):
                blockers.append("GENERATION_NOT_READY:"+str(generation.get("capability") or "UNKNOWN"))
        territories.append({
          "slot":code,"codauto":code,"territory_id":tid,"territory_name":str(master["name"]),
          "publication_mode":publication_mode,"contract_path":contract,
          "evidence":evidence,
          "generation_contract":generation,
          "preflight_status":"BLOCKED" if blockers else "GENERATION_READY",
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
    entrypoint,count,unique=STRATEGIES[manifest["optimization_algorithm"]]
    include=[]
    for row in manifest["territories"]:
        if row["preflight_status"]!="GENERATION_READY": continue
        tid=row["territory_id"]; slot=row["slot"]; ci=manifest["campaign_instance"]
        include.append({
          **row,"campaign_instance":ci,"namespace":f"{ci}/{slot}/{tid}",
          "artifact_namespace":f"{ci}--{slot}--{tid}",
          "source_sha":manifest["source_sha"],"manifest_sha256":manifest["manifest_sha256"],
          "data_edition":manifest["data_edition"],"execution_mode":manifest["execution_mode"],
          "optimization_algorithm":manifest["optimization_algorithm"],"entrypoint":entrypoint,
          "candidate_count":count,"require_unique_hashes":unique,"retry_failed":False,
        })
    return {"include":include}

def aggregate(manifest:dict[str,Any],reports:list[dict[str,Any]])->dict[str,Any]:
    by_id={str(r.get("territory_id")):r for r in reports if r.get("territory_id")}
    rows=[]; failed=[]
    for expected in manifest["territories"]:
        tid=expected["territory_id"]
        if expected["preflight_status"]=="BLOCKED":
            item={**expected,"status":"BLOCKED","reason":", ".join(expected["preflight_blockers"])}
        else:
            observed=by_id.get(tid)
            if observed is None:
                item={**expected,"status":"MISSING","reason":"campaign_status.json ausente"}
            else:
                item=dict(observed)
                terminal=item.get("status")
                if terminal!="PASS":
                    item["status"]="FAIL" if terminal else "MISSING"
                    item["reason"]=item.get("reason") or "estado terminal PASS ausente"
        rows.append(item)
        if item.get("status")!="PASS": failed.append(tid)
    return {
      "schema":"ddd.campaign-summary/2.0","campaign_instance":manifest["campaign_instance"],
      "source_sha":manifest["source_sha"],"manifest_sha256":manifest["manifest_sha256"],
      "territory_count_expected":len(manifest["territories"]),
      "territory_count_reported":len(by_id),"failed_territories":failed,
      "status":"PASS" if not failed else "FAIL","territories":rows,
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

def publication_matrix(releases:list[dict[str,Any]],expected_count:int|None=None)->dict[str,Any]:
    if not 1<=len(releases)<=19: raise ValueError("La publicación exige entre 1 y 19 releases")
    if expected_count is not None and len(releases)!=expected_count:
        raise ValueError("No se publican resultados parciales")
    for key in ("release_tag","namespace","territory_id"):
        values=[str(r.get(key) or "") for r in releases]
        if not all(values) or len(set(values))!=len(values): raise ValueError(f"{key} ausente o duplicado")
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
    raise SystemExit(0 if summary["status"]=="PASS" else 2)

if __name__=="__main__": main()
