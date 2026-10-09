#!/usr/bin/env python3
"""Auditoría causal genérica: ninguna excepción se autoriza por district_id."""
from __future__ import annotations
import argparse, hashlib, io, json, sys, zipfile
from pathlib import Path
from typing import Any
import geopandas as gpd
import pandas as pd
import yaml
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.ops import unary_union

VERSION="2.0.1"; REPORT_SCHEMA="ddd.geometric-components-audit/2.0"

def _read(path):
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            if len(names)!=1: raise ValueError(f"ZIP debe contener exactamente un GeoJSON; contiene {names}")
            return gpd.read_file(io.BytesIO(z.read(names[0])))
    return gpd.read_file(path)

def _key(v:Any)->str:
    try:
        if not isinstance(v,bool) and pd.notna(v) and float(v).is_integer(): return str(int(float(v)))
    except (TypeError,ValueError,OverflowError): pass
    return str(v)

def _parts(g):
    if g is None or g.is_empty:return []
    if isinstance(g,Polygon):return [g]
    if isinstance(g,MultiPolygon):return list(g.geoms)
    if isinstance(g,GeometryCollection):return [p for x in g.geoms for p in _parts(x)]
    return []

def _sha(b):return hashlib.sha256(b).hexdigest()
def _gsha(g):return _sha(g.wkb)
def _touch(g,parts):return [i for i,p in enumerate(parts) if g.intersection(p).area>1e-6]

def _discover(sections):
    name=sections.name; found=[]
    for p in Path("territorios").glob("*/config/*.yaml"):
        try: cfg=yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception: continue
        run=str((cfg.get("meta") or {}).get("run_name") or "")
        if run and name.startswith(run+"_"):found.append(p)
    if len(found)>1:raise ValueError(f"Contrato ambiguo para {name}: {found}")
    return found[0] if found else None

def _contract(path):
    if path is None:return [],None
    raw=path.read_bytes(); cfg=yaml.safe_load(raw.decode("utf-8")) or {}
    bridges=(((cfg.get("modulos") or {}).get("modulo_02_construir_adyacencias") or {}).get("topology_bridges") or [])
    if not isinstance(bridges,list):raise ValueError("topology_bridges debe ser lista")
    out=[]
    for i,b in enumerate(bridges):
        if not isinstance(b,dict) or not str(b.get("u","")).strip() or not str(b.get("v","")).strip():raise ValueError(f"topology_bridges[{i}] sin u/v")
        out.append({**b,"u":str(b["u"]),"v":str(b["v"]),"contract_index":i})
    return out,_sha(raw)

def _check_legacy_policy(path):
    """Compatibilidad de invocación: nunca se usa como fuente causal."""
    if path is None:return
    payload=json.loads(path.read_text(encoding="utf-8"))
    def forbidden(x):
        if isinstance(x,dict):return "district_id" in x or any(forbidden(v) for v in x.values())
        if isinstance(x,list):return any(forbidden(v) for v in x)
        return False
    if forbidden(payload):raise ValueError("Política geométrica prohibida: contiene district_id")

def _connected(n,edges):
    graph={i:set() for i in range(n)}
    for e in edges:
        a,b=e["components"];graph[a].add(b);graph[b].add(a)
    seen={0};q=[0]
    while q:
        for v in graph[q.pop()]:
            if v not in seen:seen.add(v);q.append(v)
    return len(seen)==n,sorted(set(range(n))-seen)

def audit(sections_path:Path,*,section_field:str,district_field:str,working_crs:str,
          contract_path:Path|None=None,expected_districts:int|None=None,policy_path:Path|None=None)->dict:
    _check_legacy_policy(policy_path)
    if contract_path is None:contract_path=_discover(sections_path)
    s=_read(sections_path)
    if s.crs is None:raise ValueError("Las secciones deben declarar CRS")
    for f in (section_field,district_field):
        if f not in s.columns:raise ValueError(f"Falta columna {f!r}")
    if s[section_field].isna().any() or s[district_field].isna().any():raise ValueError("Identificadores nulos")
    s=s.copy();s[section_field]=s[section_field].astype(str)
    if s[section_field].duplicated().any():raise ValueError(f"{section_field} contiene duplicados")
    if s.geometry.isna().any() or s.geometry.is_empty.any():raise ValueError("Geometría vacía")
    if (~s.geometry.is_valid).any():raise ValueError("Geometrías inválidas")
    if set(s.geometry.geom_type)-{"Polygon","MultiPolygon"}:raise ValueError("Solo Polygon/MultiPolygon")
    metric=s.to_crs(working_crs);bridges,chash=_contract(contract_path);idx=metric.set_index(section_field,drop=False)
    rows=[];pc=ec=bc=0
    for raw,grp in metric.groupby(district_field,sort=True):
        label=_key(raw); ordered=grp.sort_values(section_field); dissolved=unary_union(list(ordered.geometry))
        parts=sorted(_parts(dissolved),key=lambda g:(-float(g.area),tuple(float(v) for v in g.bounds)))
        if not parts:raise ValueError(f"Distrito {label}: dissolve vacío")
        ghash=_gsha(dissolved);total=sum(float(p.area) for p in parts);edges=[]
        for _,r in ordered.iterrows():
            if isinstance(r.geometry,MultiPolygon):
                touched=_touch(r.geometry,parts)
                for i,a in enumerate(touched):
                    for b in touched[i+1:]:edges.append({"type":"ATOMIC_MULTIPART","sections":[str(r[section_field])],"endpoints":None,"components":[a,b],"source":"official_census_section_geometry"})
        ids=set(ordered[section_field].astype(str))
        for bridge in bridges:
            u,v=bridge["u"],bridge["v"]
            if u not in ids or v not in ids or u not in idx.index or v not in idx.index:continue
            for a in _touch(idx.loc[u].geometry,parts):
                for b in _touch(idx.loc[v].geometry,parts):
                    if a!=b:edges.append({"type":"GOVERNED_BRIDGE","sections":None,"endpoints":[u,v],"components":[a,b],"edge_type":bridge.get("edge_type"),"admin_scope":bridge.get("admin_scope"),"reason":bridge.get("reason"),"source":f"{contract_path}:modulos.modulo_02_construir_adyacencias.topology_bridges[{bridge['contract_index']}]"})
        if len(parts)==1:decision,unexplained="PASS",[];pc+=1
        else:
            ok,unexplained=_connected(len(parts),edges)
            if ok:decision="PASS_WITH_EXCEPTIONS";ec+=1
            else:decision="BLOCK";bc+=1
        evidence=[{**e,"components":[x+1 for x in e["components"]],"geometry_sha256":ghash,"contract_sha256":chash} for e in edges]
        rows.append({"district_id":label,"decision":decision,"section_count":int(len(grp)),"component_count":len(parts),"interior_ring_count":sum(len(p.interiors) for p in parts),"geometry_sha256":ghash,"contract_sha256":chash,"components":[{"component":i+1,"area_m2":float(p.area),"area_share":float(p.area)/total if total else None,"geometry_sha256":_gsha(p),"bounds":[float(v) for v in p.bounds]} for i,p in enumerate(parts)],"causal_exceptions":evidence,"unexplained_components":[x+1 for x in unexplained]})
    n=len(rows);expected_ok=expected_districts in (None,0) or n==expected_districts;blockers=[] if expected_ok else [f"district_count={n}, expected={expected_districts}"]
    overall="BLOCK" if bc or blockers else ("PASS_WITH_EXCEPTIONS" if ec else "PASS")
    return {"schema":REPORT_SCHEMA,"tool_version":VERSION,"decision":overall,"gate_statement":f"{n} distritos evaluados / {pc} PASS / {ec} PASS_WITH_EXCEPTIONS / {bc} BLOCK","source":str(sections_path),"contract_path":str(contract_path) if contract_path else None,"contract_sha256":chash,"working_crs":working_crs,"section_field":section_field,"district_field":district_field,"section_count":int(len(s)),"district_count":n,"expected_districts":expected_districts,"expected_districts_ok":expected_ok,"connected_districts":pc,"governed_exceptions":ec,"blocked_districts":bc,"policy_mismatches":0,"contract_blockers":blockers,"districts":rows}

def main():
    p=argparse.ArgumentParser();p.add_argument("--sections",type=Path,required=True);p.add_argument("--output",type=Path,required=True);p.add_argument("--section-field",default="CUSEC_KEY");p.add_argument("--district-field",default="district_id");p.add_argument("--working-crs",default="EPSG:3035");p.add_argument("--expected-districts",type=int,default=0);p.add_argument("--contract",type=Path);p.add_argument("--policy",type=Path,help="Compatibilidad: solo evidencia migrada sin district_id; nunca autoriza excepciones")
    a=p.parse_args();r=audit(a.sections,section_field=a.section_field,district_field=a.district_field,working_crs=a.working_crs,contract_path=a.contract,expected_districts=a.expected_districts,policy_path=a.policy);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(2 if r["decision"]=="BLOCK" else 0)
if __name__=="__main__":main()
