#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""M05 — wrapper del optimizador base, pulido y reparación poblacional genérica opt-in."""
from __future__ import annotations
import argparse, copy, importlib.util, io, json, sys, tempfile, zipfile
from pathlib import Path
import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from ddd_core.config import load_params_yaml, hard_limits
from ddd_core.m05_swap_polish import polish as swap_polish, load_geo, write_geo
from ddd_core.m05_population_repair import repair, SearchLimits

BASE_ENGINE = ROOT / "ddd_core" / "m05_opt_engine_v740.py"
WRAPPER_VERSION = "7.6.0"

def _load_base():
    spec=importlib.util.spec_from_file_location("ddd_m05_opt_engine_v740", BASE_ENGINE)
    if spec is None or spec.loader is None: raise SystemExit("M05: motor base no cargable")
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

def _run_base(params_path):
    mod=_load_base(); old=list(sys.argv)
    try: sys.argv=[str(BASE_ENGINE),"--params",params_path]; mod.main()
    finally: sys.argv=old

def _module_cfg(cfg):
    return (cfg.get("modulos",{}) or {}).get("modulo_05_optimizar_distritos") or cfg.get("step5_optimize_swaps") or {}

def _raw_geojson(path):
    if path.suffix.lower()==".zip":
        with zipfile.ZipFile(path) as z:
            n=next(n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")); return json.loads(z.read(n)),n
    return json.loads(path.read_text(encoding="utf-8")),path.name

def _normalise_label(v):
    if isinstance(v,list):
        if len(v)!=1: raise SystemExit("M05: ddd_unit_id multivaluado")
        v=v[0]
    if v is None: raise SystemExit("M05: ddd_unit_id nulo")
    return str(v)

def _ogr_can_read_unit(path):
    try: return "ddd_unit_id" in load_geo(path).columns
    except Exception: return False

def _write_zip_json(data,path,inner):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z: z.writestr(inner,json.dumps(data,ensure_ascii=False,separators=(",",":")))

def _merge_report_metadata(report_path, **metadata):
    if not report_path or not report_path.exists(): return
    rep=json.loads(report_path.read_text(encoding="utf-8")); rep["wrapper_version"]=WRAPPER_VERSION; rep.update(metadata)
    report_path.write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding="utf-8")

def _apply_swap(cfg,s5,out_path,report_path):
    n=int(s5.get("swap_polish_max",0) or 0)
    meta={"enabled":False,"max_swaps":0,"accepted_swaps":0}
    if n:
        meta=swap_polish(cfg=cfg,graph_path=Path(str(s5["in_graph_json"])),geojson_path=out_path,out_geojson_path=out_path,max_swaps=n); meta.update(enabled=True,max_swaps=n)
    _merge_report_metadata(report_path,swap_polish=meta); return meta

def _apply_population_repair(cfg,s5,out_path,report_path):
    rcfg=(s5.get("population_repair") or {})
    if not rcfg.get("enabled",False):
        meta={"enabled":False,"result":"NO_FEASIBLE_REPAIR_FOUND"}; _merge_report_metadata(report_path,population_repair=meta); return meta
    graph=json.loads(Path(str(s5["in_graph_json"])).read_text(encoding="utf-8")); g=load_geo(out_path)
    idf=s5.get("id_field","CUSEC_KEY"); did=s5.get("district_field","district_id"); provf=s5.get("province_field","CPRO")
    g[idf]=g[idf].astype(str); g["ddd_unit_id"]=g["ddd_unit_id"].astype(str); g[provf]=g[provf].astype(str).str.zfill(2)
    pop={str(n["id"]):int(n.get("pop",0)) for n in graph["nodes"]}; sec_unit=dict(zip(g[idf],g["ddd_unit_id"]))
    units={}; assignments={}
    for u,x in g.groupby("ddd_unit_id"):
        ds=set(x[did]);
        if len(ds)!=1: raise SystemExit("M05 repair: unidad indivisible partida")
        units[u]={"population":sum(pop.get(n,0) for n in x[idf]),"province":str(x[provf].iloc[0]).zfill(2),"municipality_group":u if str(u).endswith(":M") else None}; assignments[u]=next(iter(ds))
    adj={u:set() for u in units}
    for e in graph["edges"]:
        a,b=sec_unit.get(str(e["u"])),sec_unit.get(str(e["v"]));
        if a in adj and b in adj and a!=b: adj[a].add(b); adj[b].add(a)
    total=sum(pop.values()); target,floor,cap,tol=hard_limits(cfg,k=len(set(assignments.values())),total_pop=total)
    limits=SearchLimits(max_depth=int(rcfg.get("max_depth",3)),max_transfer_set=int(rcfg.get("max_transfer_set",2)),max_candidates=int(rcfg.get("max_candidates",5000)),max_seconds=float(rcfg.get("max_seconds",5)),seed=int(rcfg.get("seed",0)))
    meta=repair(assignments=assignments,units=units,adjacency=adj,target=target,tolerance=tol,floor=floor,cap=cap,limits=limits); meta["enabled"]=True
    for u,d in meta["assignments"].items(): g.loc[g["ddd_unit_id"]==u,did]=d
    write_geo(g,out_path); _merge_report_metadata(report_path,population_repair=meta); return meta

def _post(cfg,s5,out_path,report_path):
    sw=_apply_swap(cfg,s5,out_path,report_path); rp=_apply_population_repair(cfg,s5,out_path,report_path); return sw,rp

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--params",required=True); args=ap.parse_args(); params=Path(args.params).resolve(); cfg=load_params_yaml(str(params)); s5=_module_cfg(cfg); in_path=Path(str(s5.get("in_geojson","")))
    if _ogr_can_read_unit(in_path):
        _run_base(str(params)); out=Path(str(s5["out_geojson"])); report=Path(str(s5["out_report"])) if s5.get("out_report") else None; _post(cfg,s5,out,report); return
    data,inner=_raw_geojson(in_path); labels=[_normalise_label((f.get("properties") or {}).get("ddd_unit_id")) for f in data.get("features",[])]; unique=sorted(set(labels)); mapping={v:i+1 for i,v in enumerate(unique)}
    for f,label in zip(data.get("features",[]),labels): f.setdefault("properties",{})["ddd_unit_id"]=mapping[label]
    with tempfile.TemporaryDirectory(prefix="ddd_m05_760_") as td:
        td=Path(td); ti=td/"in.zip"; to=td/"out.zip"; tr=td/"report.json"; tp=td/"params.yaml"; _write_zip_json(data,ti,"input.geojson")
        cfg2=copy.deepcopy(cfg); s52=_module_cfg(cfg2); s52.update(in_geojson=str(ti),out_geojson=str(to),out_report=str(tr)); cfg2.setdefault("modulos",{})["modulo_05_optimizar_distritos"]=s52; tp.write_text(yaml.safe_dump(cfg2,sort_keys=False,allow_unicode=True),encoding="utf-8")
        _run_base(str(tp)); _post(cfg2,s52,to,tr); final=Path(str(s5["out_geojson"])); final.parent.mkdir(parents=True,exist_ok=True); final.write_bytes(to.read_bytes())
        if s5.get("out_report"):
            fr=Path(str(s5["out_report"])); fr.parent.mkdir(parents=True,exist_ok=True); fr.write_bytes(tr.read_bytes()); _merge_report_metadata(fr,unit_id_normalization={"applied":True,"units":len(unique)})
if __name__=="__main__": main()
