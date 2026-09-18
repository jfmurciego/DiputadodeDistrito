#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml

CATALOG = Path("configuracion/catalogo_preparacion.yaml")
REQUIRED = (
    "territory_declared","territorial_sources_prepared","territorial_contract_complete",
    "territorial_product_available","electoral_source_prepared","electoral_product_available",
    "territorial_certification","last_valid_checkpoint",
)

def load_catalog(path: Path = CATALOG) -> dict:
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("schema") != "ddd-preparation-catalog/1.0":
        raise ValueError("Esquema de catálogo de preparación no reconocido")
    rows=data.get("territories")
    if not isinstance(rows,list) or not rows:
        raise ValueError("Catálogo de preparación vacío")
    seen=set()
    for row in rows:
        tid=str(row.get("territory_id") or "")
        name=str(row.get("name") or "")
        if not tid or not name or tid in seen:
            raise ValueError(f"Territorio inválido o duplicado: {tid!r}")
        seen.add(tid)
        editions=row.get("editions") or {}
        if not isinstance(editions,dict) or not editions:
            raise ValueError(f"{tid}: sin ediciones")
        for edition,state in editions.items():
            if not isinstance(state,dict):
                raise ValueError(f"{tid}/{edition}: estado inválido")
            missing=[k for k in REQUIRED if k not in state]
            if missing:
                raise ValueError(f"{tid}/{edition}: faltan {', '.join(missing)}")
    return data

def rows_for(mode: str, path: Path = CATALOG) -> list[dict]:
    data=load_catalog(path)
    out=[]
    for row in data["territories"]:
        for edition,state in (row.get("editions") or {}).items():
            if not state.get("territory_declared"):
                continue
            eligible=True
            if mode=="production":
                eligible=bool(
                    state.get("territorial_sources_prepared")
                    and state.get("territorial_contract_complete")
                    and state.get("production_authorization")=="AUTHORIZED"
                )
            if eligible:
                out.append({"territory_id":row["territory_id"],"name":row["name"],"edition":str(edition),**state})
    return out

def resolve(mode: str, territory: str, edition: str, path: Path = CATALOG) -> dict:
    territory=territory.strip()
    matches=[r for r in rows_for(mode,path) if str(r["edition"])==str(edition) and territory in {r["name"],r["territory_id"]}]
    if len(matches)!=1:
        raise SystemExit(f"No existe una opción {mode} única para territorio={territory!r}, edición={edition!r}")
    r=matches[0]
    r["params"]=f"territorios/{r['territory_id']}/config/{r['territory_id']}_{edition}.yaml"
    return r

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--catalog",type=Path,default=CATALOG)
    sub=ap.add_subparsers(dest="cmd",required=True)
    sub.add_parser("validate")
    op=sub.add_parser("options"); op.add_argument("--mode",choices=["preparation","production"],required=True)
    rs=sub.add_parser("resolve"); rs.add_argument("--mode",choices=["preparation","production"],required=True); rs.add_argument("--territory",required=True); rs.add_argument("--edition",required=True)
    args=ap.parse_args()
    if args.cmd=="validate":
        load_catalog(args.catalog); print("OK"); return
    if args.cmd=="options":
        print(json.dumps(rows_for(args.mode,args.catalog),ensure_ascii=False)); return
    print(json.dumps(resolve(args.mode,args.territory,args.edition,args.catalog),ensure_ascii=False))
if __name__=="__main__":
    main()
