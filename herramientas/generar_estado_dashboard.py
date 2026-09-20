#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path
import yaml

def load_yaml(path: Path) -> dict:
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data,dict): raise ValueError(f"YAML inválido: {path}")
    return data

def modern_evidence(state: dict, territory_id: str, key: str) -> bool:
    path=str((state.get("evidence") or {}).get(key) or "")
    return path.startswith(f"territorios/{territory_id}/evidencia/catalogo/")

def derive(row: dict, edition: str) -> dict:
    tid=row["territory_id"]; name=row.get("name",tid)
    state=(row.get("editions") or {}).get(edition) or {}
    contract=bool(state.get("contract_path"))
    ft="green" if state.get("territorial_sources_prepared") else ("yellow" if state.get("territorial_source_declaration") else ("red" if not contract else "gray"))
    fe="green" if state.get("electoral_source_prepared") else ("yellow" if state.get("electoral_source_declaration") else ("red" if not contract else "gray"))
    product=bool(state.get("territorial_product_available"))
    fresh_product=modern_evidence(state,tid,"territorial_product")
    cert=str(state.get("territorial_certification") or "")
    if product and fresh_product and cert in {"PASS","PASS_WITH_GOVERNED_EXCEPTIONS"}: g="green"
    elif product or state.get("production_authorization") in {"AUTHORIZED","PREFLIGHT"}: g="yellow"
    elif not contract: g="red"
    else: g="gray"
    electoral=bool(state.get("electoral_product_available"))
    fresh_electoral=modern_evidence(state,tid,"electoral_product")
    if electoral and fresh_electoral: re="green"
    elif state.get("electoral_source_prepared") and product: re="yellow"
    elif not contract: re="red"
    else: re="gray"

    if not contract: status="No incorporado"
    elif re=="green": status="Producto electoral incorporado"
    elif g=="green" and fe=="green": status="Listo para incorporar resultados electorales"
    elif g=="green": status="Generación territorial validada"
    elif ft=="green": status="Fuentes territoriales preparadas"
    elif state.get("production_authorization")=="PREFLIGHT": status="Preflight"
    elif g=="yellow": status="Revalidación pendiente"
    else: status="Pendiente de preparación"
    cp=state.get("last_valid_checkpoint") or {}
    return {"territory_id":tid,"name":name,"ft":ft,"fe":fe,"g":g,"re":re,"status":status,
            "certification":cert or "NOT_CERTIFIED","run_id":cp.get("run_id"),"stage":cp.get("stage"),
            "edition":edition}

def build(root: Path, edition: str) -> dict:
    catalog=load_yaml(root/"configuracion/catalogo_preparacion.yaml")
    rows=[derive(r,edition) for r in catalog.get("territories") or []]
    rows.sort(key=lambda r:r["name"].casefold())
    validated=[r for r in rows if r["g"]=="green"]
    ready=[r for r in rows if r["ft"]=="green" and r["g"]!="green"]
    pending=[r for r in rows if r["g"]=="yellow" and r not in ready]
    blocked=[r for r in rows if r["ft"] in {"gray","red"} and r not in pending]
    latest=max((r for r in validated if r.get("run_id")),key=lambda r:int(r["run_id"]),default=None)
    alerts=[]
    for r in rows:
        if r["re"]=="yellow":
            alerts.append({"territory":r["name"],"action":"incorporar resultados electorales"})
        elif r["g"]=="yellow":
            alerts.append({"territory":r["name"],"action":"revalidar generación territorial"})
        elif r["ft"]=="red":
            alerts.append({"territory":r["name"],"action":"incorporación territorial pendiente"})
    next_actions=[]
    for r in rows:
        if r["ft"]=="green" and r["fe"]!="green": next_actions.append({"territory":r["name"],"action":"preparar fuentes electorales"})
        elif r["g"]=="green" and r["re"]!="green": next_actions.append({"territory":r["name"],"action":"incorporar resultados electorales"})
        elif r["g"]=="yellow": next_actions.append({"territory":r["name"],"action":"revalidar cadena automática"})
    return {
      "schema":"ddd-dashboard-status/1.0","edition":edition,
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "territories":rows,
      "kpis":{
        "validated":len(validated),"validated_names":[r["name"] for r in validated],
        "ready":len(ready),"ready_names":[r["name"] for r in ready],
        "pending":len(pending),"pending_names":[r["name"] for r in pending],
        "blocked":len(blocked),"blocked_names":[r["name"] for r in blocked],
      },
      "latest_validated":None if latest is None else {
        "territory_id":latest["territory_id"],"name":latest["name"],"run_id":latest["run_id"],
        "stage":latest["stage"],"certification":latest["certification"],"edition":latest["edition"]},
      "alerts":alerts[:8],"next_actions":next_actions[:8]
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--root-dir",type=Path,default=Path("."))
    ap.add_argument("--edition",default="2025")
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    payload=build(args.root_dir,args.edition)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"output":str(args.output),"territories":len(payload["territories"]),"latest_validated":payload["latest_validated"]},ensure_ascii=False))
    return 0
if __name__=="__main__": raise SystemExit(main())
