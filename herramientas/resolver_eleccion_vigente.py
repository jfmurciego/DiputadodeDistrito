#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
import yaml

DEFAULT=Path("configuracion/elecciones_vigentes.yaml")

def load_catalog(path:Path)->dict:
    data=yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows=data.get("territories")
    if not isinstance(rows,list): raise ValueError("Catálogo de elecciones vigentes sin territories")
    return data

def resolve(territory:str,path:Path=DEFAULT,root_dir:Path=Path("."))->dict:
    token=territory.strip()
    rows=[r for r in load_catalog(path)["territories"] if token in {str(r.get("territory_id") or ""),str(r.get("name") or "")}]
    if len(rows)!=1: raise SystemExit(f"No existe elección vigente única para territorio={territory!r}")
    row=dict(rows[0])
    for key in ("territory_id","name","territorial_edition","election_id","election_date","declaration"):
        if row.get(key) in (None,""): raise SystemExit(f"Elección vigente incompleta: falta {key}")
    declaration=root_dir/str(row["declaration"])
    if not declaration.is_file(): raise SystemExit(f"Declaración electoral vigente inexistente: {declaration}")
    d=yaml.safe_load(declaration.read_text(encoding="utf-8")) or {}
    if d.get("territory_id")!=row["territory_id"]: raise SystemExit("territory_id de declaración vigente no coincide")
    if d.get("election_id")!=row["election_id"]: raise SystemExit("election_id de declaración vigente no coincide")
    if str(d.get("election_date"))!=str(row["election_date"]): raise SystemExit("election_date de declaración vigente no coincide")
    return row

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--territory",required=True)
    ap.add_argument("--catalog",type=Path,default=DEFAULT)
    ap.add_argument("--root-dir",type=Path,default=Path("."))
    a=ap.parse_args()
    print(json.dumps(resolve(a.territory,a.catalog,a.root_dir),ensure_ascii=False))

if __name__=="__main__":
    main()
