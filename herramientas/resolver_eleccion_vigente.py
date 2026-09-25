#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import yaml

DEFAULT = Path("configuracion/elecciones_vigentes.yaml")
PREPARATION_CATALOG = Path("configuracion/catalogo_preparacion.yaml")
ELECTION_REGISTRY = Path("configuracion/registro_electoral.yaml")
DECLARATION_SCHEMA = "ddd-election-official-source-declaration/1.0"


def load_catalog(path: Path) -> dict:
    if not path.is_file(): return {"territories": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data.get("territories"), list): raise ValueError("Catálogo de elecciones vigentes sin territories")
    return data


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _catalog_preparation_row(root_dir: Path, territory: str, edition: str | None):
    path = root_dir / PREPARATION_CATALOG
    if not path.is_file(): return None
    data = _load_yaml(path); token = territory.strip()
    rows = [r for r in (data.get("territories") or []) if token in {str(r.get("territory_id") or ""), str(r.get("name") or "")}]
    if len(rows) != 1: return None
    row=rows[0]; tid=str(row.get("territory_id") or ""); name=str(row.get("name") or ""); selected=str(edition or data.get("default_edition") or ""); state=(row.get("editions") or {}).get(selected)
    return (tid,name,state) if tid and name and isinstance(state,dict) else None


def _declaration_candidates(root_dir, territory_id, state):
    result=[]; explicit=state.get("electoral_source_declaration")
    if explicit and (root_dir/str(explicit)).is_file(): result.append(root_dir/str(explicit))
    folder=root_dir/"territorios"/territory_id/"config"/"elecciones"
    if folder.is_dir():
        for p in sorted(folder.glob("*.yaml")):
            if p not in result and _load_yaml(p).get("schema")==DECLARATION_SCHEMA: result.append(p)
    return result


def _row_from_materialized_contract(*,territory_id,name,territorial_edition,state,root_dir):
    raw=state.get("contract_path")
    if not raw or not (root_dir/str(raw)).is_file(): return None
    params=_load_yaml(root_dir/str(raw)); eraw=((params.get("modulos") or {}).get("modulo_07_agregar_resultados_electorales") or {}).get("election_contract")
    if not eraw or not (root_dir/str(eraw)).is_file(): return None
    try: data=json.loads((root_dir/str(eraw)).read_text(encoding="utf-8"))
    except Exception: return None
    if any(data.get(k) in (None,"") for k in ("territory_id","election_id","election_date")): return None
    if str(data["territory_id"])!=territory_id: raise SystemExit(f"Contrato electoral de otro territorio: {eraw}")
    return {"territory_id":territory_id,"name":name,"territorial_edition":territorial_edition,"election_id":str(data["election_id"]),"election_date":str(data["election_date"]),"declaration":"","election_contract":str(eraw),"resolution_mode":"materialized_election_contract"}


def _row_from_declaration(*,territory_id,name,territorial_edition,declaration,root_dir):
    data=_load_yaml(declaration)
    for k in ("territory_id","election_id","election_date"):
        if data.get(k) in (None,""): raise SystemExit(f"Declaración electoral incompleta: {declaration}; falta {k}")
    if str(data["territory_id"])!=territory_id: raise SystemExit(f"Declaración electoral de otro territorio: {declaration}")
    return {"territory_id":territory_id,"name":name,"territorial_edition":territorial_edition,"election_id":str(data["election_id"]),"election_date":str(data["election_date"]),"declaration":declaration.relative_to(root_dir).as_posix(),"resolution_mode":"auto_discovered_declaration"}


def resolve(territory:str,path:Path=DEFAULT,root_dir:Path=Path("."),edition:str|None=None)->dict:
    root=root_dir.resolve(); token=territory.strip(); override=path if path.is_absolute() else root/path
    rows=[r for r in load_catalog(override)["territories"] if token in {str(r.get("territory_id") or ""),str(r.get("name") or "")}]
    if len(rows)>1: raise SystemExit(f"Elección vigente ambigua para territorio={territory!r}")
    if len(rows)==1:
        row=dict(rows[0]); declaration=root/str(row.get("declaration") or "")
        if any(row.get(k) in (None,"") for k in ("territory_id","name","territorial_edition","election_id","election_date","declaration")) or not declaration.is_file(): raise SystemExit("Elección vigente incompleta")
        row["resolution_mode"]="governed_override"; return row
    found=_catalog_preparation_row(root,token,edition)
    if found is None: raise SystemExit(f"Territorio o edición no declarados: territorio={territory!r}, edición={edition!r}")
    tid,name,state=found; ed=str(edition or _load_yaml(root/PREPARATION_CATALOG).get("default_edition") or "")
    resolved=[_row_from_declaration(territory_id=tid,name=name,territorial_edition=ed,declaration=p,root_dir=root) for p in _declaration_candidates(root,tid,state)]
    if not resolved:
        materialized=_row_from_materialized_contract(territory_id=tid,name=name,territorial_edition=ed,state=state,root_dir=root)
        if materialized is not None:return materialized
        raise SystemExit(f"No existe elección resoluble para territorio={territory!r}: no hay declaración de adquisición ni contrato electoral materializado.")
    resolved.sort(key=lambda r:date.fromisoformat(str(r["election_date"])),reverse=True); return resolved[0]


def resolve_for_preparation(territory:str,path:Path=DEFAULT,root_dir:Path=Path("."),edition:str|None=None)->dict:
    """Identidad electoral permite iniciar 03; no implica fuente adquirible ni paquete."""
    root=root_dir.resolve(); registry=_load_yaml(root/ELECTION_REGISTRY); selected=str(edition or _load_yaml(root/PREPARATION_CATALOG).get("default_edition") or "")
    entries=registry.get("territories") or {}; token=territory.strip(); reg_id=None; entry=None
    for tid,row in entries.items():
        if token in {str(tid),str((row or {}).get("name") or "")}:
            reg_id=str(tid); entry=row; break
    if not isinstance(entry,dict): raise SystemExit(f"Territorio no inscrito en el registro electoral: {territory}")
    # Resolve catalog through canonical name, avoiding id aliases that differ historically (e.g. Madrid).
    found=_catalog_preparation_row(root,str(entry.get("name") or ""),selected)
    if found is None: raise SystemExit(f"Territorio o edición no registrados: {territory!r}, {selected!r}")
    tid,name,_state=found
    if tid!=reg_id: raise SystemExit(f"Registro electoral y catálogo territorial discrepan: {reg_id} != {tid}")
    try: return resolve(name,path,root,selected)
    except SystemExit as exc:
        if not (str(exc).startswith("No existe elección resoluble") or str(exc).startswith("Elección vigente incompleta")): raise
    eid=str(entry.get("election_id") or ""); edate=str(entry.get("election_date") or "")
    if not eid or not edate: raise SystemExit(f"Elección registrada incompleta: {tid}")
    date.fromisoformat(edate)
    return {"territory_id":tid,"name":name,"territorial_edition":selected,"election_id":eid,"election_date":edate,"declaration":"","resolution_mode":"registered_identity_pending_source"}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--territory",required=True); ap.add_argument("--edition"); ap.add_argument("--catalog",type=Path,default=DEFAULT); ap.add_argument("--root-dir",type=Path,default=Path(".")); ap.add_argument("--for-preparation",action="store_true"); a=ap.parse_args()
    fn=resolve_for_preparation if a.for_preparation else resolve; print(json.dumps(fn(a.territory,a.catalog,a.root_dir,a.edition),ensure_ascii=False))
if __name__=="__main__": main()
