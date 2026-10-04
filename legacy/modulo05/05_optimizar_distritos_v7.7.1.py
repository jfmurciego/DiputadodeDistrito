#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.7.1
NOMBRE DE VERSIÓN: Reparación poblacional focal por cadenas
FECHA: 2026-09-16
ESTADO: candidato multi-territorio; reparación poblacional opt-in pendiente de validación CI completa.
FUNCIÓN: ejecutar el motor base M05 v7.4.1, aplicar el pulido determinista existente y activar de forma genérica
una reparación poblacional acotada cuando una partición estructuralmente válida conserva violaciones duras.
ENTRADAS: grafo M03 y solución M04 con district_id, ddd_unit_id y provincia.
SALIDAS: GeoJSON optimizado e informe M05 con versión de wrapper y evidencia estructurada de reparación.
REGLAS DURAS: no modifica contratos, tolerancias ni cuotas; una desactivación explícita prevalece y la activación
automática solo ocurre ante violaciones duras sobre una partición estructuralmente válida.
CAMBIOS: añade la fase genérica de reparación poblacional posterior al motor base y al swap-polish,
con límites explícitos de búsqueda y resultados REPAIRED, IMPROVED_NOT_REPAIRED o NO_FEASIBLE_REPAIR_FOUND.
MOTIVO: permitir reparación poblacional reusable y acotada sin alterar el motor base ni los contratos territoriales.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.5.2.py
"""
from __future__ import annotations
import argparse, copy, importlib.util, io, json, sys, tempfile, zipfile
from pathlib import Path
import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from ddd_core.config import load_params_yaml, hard_limits
from ddd_core.m05_swap_polish import polish as swap_polish, load_geo, write_geo
from ddd_core.m05_population_repair import repair, SearchLimits, verify_partition_constraints

BASE_ENGINE = ROOT / "ddd_core" / "m05_opt_engine_v741.py"
WRAPPER_VERSION = "7.7.1"

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

def _protect_closed_urban_districts(g,did,assignments,adj):
    """Aísla del post-procesado las fronteras de los distritos urbanos cerrados."""
    frozen_districts={next(iter(set(x[did]))) for _,x in g.groupby(did) if bool(x["ddd_closed_urban"].all())}
    frozen_units={u for u,d in assignments.items() if d in frozen_districts}
    protected={u:set(vs) for u,vs in adj.items()}
    if frozen_units:
        for u in list(protected):
            protected[u]={v for v in protected[u] if not ((u in frozen_units) ^ (v in frozen_units))}
    return protected,frozen_districts,frozen_units,{u:assignments[u] for u in frozen_units}

def _refresh_population_report(report_path,g,did,pop_by_section,idf,target,floor,cap,tol):
    if not report_path or not report_path.exists(): return
    sec_pop=g[idf].astype(str).map(pop_by_section).fillna(0).astype(int)
    pops=sec_pop.groupby(g[did]).sum().to_dict(); vals=list(pops.values())
    hard=sum(p<floor or p>cap for p in vals)
    hard_mag=sum(max(0,floor-p,p-cap) for p in vals)
    outside=sum(abs(p-target)>tol for p in vals)
    maxdev=max((abs(p-target)/target for p in vals),default=0.0)
    sq=sum(((p-target)/target)**2 for p in vals)
    _merge_report_metadata(
        report_path,
        objective_final=[hard,round(hard_mag/target,12),outside,round(maxdev,12),round(sq,12)],
        districts_below_floor=sum(p<floor for p in vals),
        districts_above_cap=sum(p>cap for p in vals),
        districts_outside_tolerance=outside,
        best_max_rel_dev=round(maxdev,12),
    )

def _apply_swap(cfg,s5,out_path,report_path):
    n=int(s5.get("swap_polish_max",0) or 0)
    if n < 0:
        raise SystemExit("M05: swap_polish_max no puede ser negativo")
    meta={"enabled":False,"max_swaps":0,"accepted_swaps":0}
    if n:
        meta=swap_polish(cfg=cfg,graph_path=Path(str(s5["in_graph_json"])),geojson_path=out_path,out_geojson_path=out_path,max_swaps=n); meta.update(enabled=True,max_swaps=n)
    _merge_report_metadata(report_path,swap_polish=meta); return meta

def _apply_population_repair(cfg,s5,out_path,report_path):
    declared=s5.get("population_repair")
    if isinstance(declared,dict) and declared.get("enabled") is False:
        meta={
            "enabled":False,
            "activation":"EXPLICITLY_DISABLED",
            "result":"DISABLED",
        }
        _merge_report_metadata(report_path,population_repair=meta)
        return meta

    rcfg=declared if isinstance(declared,dict) else {}
    graph=json.loads(Path(str(s5["in_graph_json"])).read_text(encoding="utf-8")); g=load_geo(out_path)
    idf=s5.get("id_field","CUSEC_KEY"); did=s5.get("district_field","district_id"); provf=s5.get("province_field","CPRO")
    g[idf]=g[idf].astype(str); g["ddd_unit_id"]=g["ddd_unit_id"].astype(str); g[provf]=g[provf].astype(str).str.zfill(2)
    pop={str(n["id"]):int(n.get("pop",0)) for n in graph["nodes"]}; sec_unit=dict(zip(g[idf],g["ddd_unit_id"]))
    units={}; assignments={}
    for u,x in g.groupby("ddd_unit_id"):
        ds=set(x[did])
        if len(ds)!=1: raise SystemExit("M05 repair: unidad indivisible partida")
        units[u]={
            "population":sum(pop.get(n,0) for n in x[idf]),
            "province":str(x[provf].iloc[0]).zfill(2),
            "municipality_group":u if str(u).endswith(":M") else None,
        }
        assignments[u]=next(iter(ds))
    adj={u:set() for u in units}
    for e in graph["edges"]:
        a,b=sec_unit.get(str(e["u"])),sec_unit.get(str(e["v"]))
        if a in adj and b in adj and a!=b: adj[a].add(b); adj[b].add(a)

    # Los distritos urbanos cerrados son una restricción dura creada por la formación inicial.
    # El motor base ya los congela; la reparación posterior debe conservar exactamente
    # la misma frontera y no puede usarlos como donante ni receptor.
    adj,frozen_districts,frozen_units,baseline_frozen=_protect_closed_urban_districts(g,did,assignments,adj)
    total=sum(pop.values()); target,floor,cap,tol=hard_limits(cfg,k=len(set(assignments.values())),total_pop=total)

    baseline_check=verify_partition_constraints(assignments,units,adj,floor=floor,cap=cap)
    if not baseline_check.get("valid"):
        raise SystemExit(f"M05 repair: baseline estructuralmente inválido: {baseline_check}")

    hard_before=int(baseline_check.get("hard_population_violations",0))
    if hard_before == 0:
        meta={
            "enabled":False,
            "activation":"NOT_NEEDED",
            "result":"DISABLED",
            "hard_population_violations_before":0,
        }
        _merge_report_metadata(report_path,population_repair=meta)
        return meta

    activation="EXPLICITLY_ENABLED" if isinstance(declared,dict) and declared.get("enabled") is True else "AUTO_HARD_VIOLATIONS"
    limits=SearchLimits(
        max_depth=int(rcfg.get("max_depth",3)),
        max_transfer_set=int(rcfg.get("max_transfer_set",2)),
        max_candidates=int(rcfg.get("max_candidates",5000)),
        max_seconds=float(rcfg.get("max_seconds",5)),
        seed=int(rcfg.get("seed",0)),
    )
    meta=repair(
        assignments=assignments,
        units=units,
        adjacency=adj,
        target=target,
        tolerance=tol,
        floor=floor,
        cap=cap,
        limits=limits,
    )
    meta["enabled"]=True
    meta["activation"]=activation
    meta["hard_population_violations_before"]=hard_before
    moved_frozen={u:(baseline_frozen[u],meta["assignments"].get(u)) for u in baseline_frozen if meta["assignments"].get(u)!=baseline_frozen[u]}
    if moved_frozen: raise SystemExit(f"M05 repair: distrito urbano cerrado modificado: {moved_frozen}")
    meta["frozen_districts"]=sorted(frozen_districts,key=str); meta["frozen_units"]=len(frozen_units)
    for u,d in meta["assignments"].items(): g.loc[g["ddd_unit_id"]==u,did]=d
    write_geo(g,out_path)
    _merge_report_metadata(report_path,population_repair=meta)
    _refresh_population_report(report_path,g,did,pop,idf,target,floor,cap,tol)
    return meta

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
