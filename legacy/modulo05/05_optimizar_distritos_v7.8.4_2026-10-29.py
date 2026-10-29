#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.8.4
NOMBRE DE VERSIÓN: Estados poblacionales finales y staging completo de M06
FECHA: 2026-10-12
ESTADO: candidato; reparación focal por defecto y estrategia privada experimental optativa con validación oficial obligatoria.
FUNCIÓN: ejecutar el motor base M05 v7.4.1, aplicar pulido determinista y reparar violaciones duras; la estrategia
private_annealing explora copias privadas y solo promueve una candidata tras validación final oficial.
ENTRADAS: grafo M03 y solución M04 con district_id, ddd_unit_id y provincia.
SALIDAS: GeoJSON optimizado e informe M05 con versión de wrapper y evidencia estructurada de reparación.
REGLAS DURAS: no modifica contratos, tolerancias ni cuotas; una desactivación explícita prevalece y la activación
automática solo ocurre ante violaciones duras sobre una partición estructuralmente válida.
CAMBIOS: reconstruye estados poblacionales y reporte desde asignaciones finales; dirige todas las salidas M06 de la puerta privada a staging y limpia el informe operativo temporal del validador.
MOTIVO: impedir atributos y diagnósticos obsoletos y proteger productos duraderos mientras se valida una candidata privada.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.8.3_2026-10-11.py
"""
from __future__ import annotations
import argparse, copy, importlib.util, io, json, os, shutil, subprocess, sys, tempfile, uuid, zipfile
from pathlib import Path
import geopandas as gpd
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from ddd_core.config import load_params_yaml, hard_limits
from ddd_core.m05_swap_polish import polish as swap_polish, load_geo, write_geo
from ddd_core.m05_population_repair import repair, SearchLimits, verify_partition_constraints
from ddd_core.m05_private_annealing import repair_private
from ddd_core.m05_atomic_output import run_staged_output

BASE_ENGINE = ROOT / "ddd_core" / "m05_opt_engine_v741.py"
WRAPPER_VERSION = "7.8.4"

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

def _official_private_candidate_gate(cfg,candidate_geo,output_geo,seed):
    """Stage M05 privately; promote only after official M06 and audits pass."""
    s6=((cfg.get("modulos") or {}).get("modulo_06_consolidar_distritos") or {})
    s5=_module_cfg(cfg); graph=Path(str(s5.get("in_graph_json",""))).resolve()
    territory_id=str((cfg.get("meta") or {}).get("territory_id") or "")
    candidates=sorted((ROOT/"territorios"/territory_id/"config").glob("*.yaml")) if territory_id else []
    run_name=str((cfg.get("meta") or {}).get("run_name") or "")
    contracts=[]
    for candidate in candidates:
        try:
            if str((yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}).get("meta",{}).get("run_name") or "")==run_name:
                contracts.append(candidate)
        except (OSError,ValueError):
            continue
    if not s6 or not graph.is_file() or len(contracts)!=1:
        return {"passed":False,"reason":"OFFICIAL_GATE_CONFIGURATION_MISSING","territory_contracts":len(contracts)}
    output_geo.parent.mkdir(parents=True,exist_ok=True)
    run_id=f"m05-private-{int(seed)}-{os.getpid()}-{uuid.uuid4().hex}"
    operational_root=ROOT/"ejecuciones"; operational_root_existed=operational_root.exists()
    operational_report=operational_root/run_id
    while operational_report.exists():
        run_id=f"m05-private-{int(seed)}-{os.getpid()}-{uuid.uuid4().hex}"
        operational_report=operational_root/run_id
    with tempfile.TemporaryDirectory(prefix="ddd_m05_private_gate_",dir=str(output_geo.parent)) as raw:
        td=Path(raw); staged=td/"candidate.geojson.zip"; write_geo(candidate_geo,staged)
        cfg2=copy.deepcopy(cfg); cfg2.setdefault("io",{}).setdefault("project_root",{})["path"]=str(ROOT)
        mods=cfg2.setdefault("modulos",{}); mods["modulo_05_optimizar_distritos"]["out_geojson"]=str(staged)
        mods["modulo_03_construir_grafo"]["out_graph_json"]=str(graph)
        m6=mods["modulo_06_consolidar_distritos"]; m6["in_geojson"]=str(staged)
        output_keys=("out_summary_csv","out_catalog_csv","out_composition_csv","out_geojson","out_district_geojson","out_diagnostic_json")
        outputs={k:td/"m06"/(k+"_"+Path(str(m6[k])).name) for k in output_keys if m6.get(k)}
        for path in outputs.values():path.parent.mkdir(parents=True,exist_ok=True)
        for k,p in outputs.items():m6[k]=str(p)
        params=td/"params.yaml"; params.write_text(yaml.safe_dump(cfg2,sort_keys=False,allow_unicode=True),encoding="utf-8")
        try:
            try:
                m06=subprocess.run([sys.executable,str(ROOT/"modulos/06_consolidar_distritos.py"),"--params",str(params)],capture_output=True,text=True,timeout=120)
            except subprocess.TimeoutExpired:
                return {"passed":False,"reason":"M06_TIMEOUT"}
            except Exception as exc:
                return {"passed":False,"reason":"M06_EXCEPTION","detail":str(exc)[-1000:]}
            if m06.returncode:return {"passed":False,"reason":"M06_FAIL","detail":(m06.stdout+m06.stderr)[-3000:]}
            # validar_ejecucion.py emits an operational report under ejecuciones/<run_id>.
            # It is not a transactional M06 product; use a unique ID and remove only this
            # private-gate report directory after its result has been consumed.
            try:
                validator=subprocess.run([sys.executable,str(ROOT/"herramientas/validar_ejecucion.py"),"--params",str(params),"--run-id",run_id],capture_output=True,text=True,timeout=120)
            except subprocess.TimeoutExpired:
                return {"passed":False,"reason":"VALIDAR_EJECUCION_TIMEOUT"}
            except Exception as exc:
                return {"passed":False,"reason":"VALIDAR_EJECUCION_EXCEPTION","detail":str(exc)[-1000:]}
            if validator.returncode:return {"passed":False,"reason":"VALIDAR_EJECUCION_FAIL","detail":(validator.stdout+validator.stderr)[-3000:]}
            audit_path=td/"geometry.json"
            try:
                audit=subprocess.run([sys.executable,str(ROOT/"herramientas/auditar_componentes_geometricos.py"),"--sections",str(outputs["out_geojson"]),"--output",str(audit_path),"--section-field",str(m6["id_field"]),"--district-field",str(m6["district_field"]),"--working-crs",str(m6.get("metric_crs","EPSG:3035")),"--expected-districts",str(m6.get("expected_districts",0)),"--contract",str(contracts[0])],capture_output=True,text=True,timeout=120)
            except subprocess.TimeoutExpired:
                return {"passed":False,"reason":"GEOMETRIC_AUDIT_TIMEOUT"}
            except Exception as exc:
                return {"passed":False,"reason":"GEOMETRIC_AUDIT_EXCEPTION","detail":str(exc)[-1000:]}
            if audit.returncode:return {"passed":False,"reason":"GEOMETRIC_AUDIT_FAIL","detail":(audit.stdout+audit.stderr)[-3000:]}
            result=json.loads(audit_path.read_text(encoding="utf-8"));output_geo.parent.mkdir(parents=True,exist_ok=True);os.replace(staged,output_geo)
            return {"passed":True,"m06":"PASS","validar_ejecucion":"PASS","geometry_decision":result["decision"],"geometry_gate":result["gate_statement"],"contract_sha256":result["contract_sha256"]}
        finally:
            shutil.rmtree(operational_report,ignore_errors=True)
            if not operational_root_existed:
                try:operational_root.rmdir()
                except OSError:pass

def _protect_closed_urban_districts(g,did,assignments,adj):
    """Aísla del post-procesado las fronteras de los distritos urbanos cerrados."""
    frozen_districts={next(iter(set(x[did]))) for _,x in g.groupby(did) if bool(x["ddd_closed_urban"].all())}
    frozen_units={u for u,d in assignments.items() if d in frozen_districts}
    protected={u:set(vs) for u,vs in adj.items()}
    if frozen_units:
        for u in list(protected):
            protected[u]={v for v in protected[u] if not ((u in frozen_units) ^ (v in frozen_units))}
    return protected,frozen_districts,frozen_units,{u:assignments[u] for u in frozen_units}

def _refresh_population_report(
    report_path,g,did,pop_by_section,idf,target,floor,cap,tol,district_floors=None,pop_field=None
):
    section_ids=g[idf].astype(str)
    sec_pop=section_ids.map(pop_by_section)
    if sec_pop.isna().any():
        missing=sorted(section_ids[sec_pop.isna()].unique())[:10]
        raise SystemExit(f"M05: población ausente en grafo para secciones: {missing}")
    graph_pop=sec_pop.astype(int)
    if pop_field and pop_field in g.columns:
        section_pop=g[pop_field]
        if section_pop.isna().any():
            raise SystemExit(f"M05: población nula en {pop_field}")
        sec_pop=section_pop.astype(int)
        if not sec_pop.reset_index(drop=True).equals(graph_pop.reset_index(drop=True)):
            mismatches=section_ids[sec_pop.reset_index(drop=True)!=graph_pop.reset_index(drop=True)].tolist()[:10]
            raise SystemExit(f"M05: población por sección no coincide entre GeoJSON y grafo: {mismatches}")
    else:
        sec_pop=graph_pop
    if len(section_ids)!=len(set(section_ids)):
        raise SystemExit("M05: identificadores de sección duplicados al refrescar estado poblacional")
    g=g.copy()
    pops={str(d):int(p) for d,p in sec_pop.groupby(g[did].astype(str)).sum().items()}
    floors={str(d):float(v) for d,v in (district_floors or {}).items()}
    effective_floor=lambda d: floors.get(str(d),float(floor))
    status_by_district={}
    for district,population in pops.items():
        district_floor=effective_floor(district)
        status="ABOVE_CEILING" if population>cap else "BELOW_FLOOR" if population<district_floor else "PASS"
        status_by_district[district]={"population":population,"floor":district_floor,"cap":float(cap),"population_status":status}
    g["ddd_population_status"]=g[did].astype(str).map({d:row["population_status"] for d,row in status_by_district.items()})
    if g["ddd_population_status"].isna().any():
        raise SystemExit("M05: no se pudo asignar estado poblacional a todas las secciones")
    vals=list(pops.values())
    hard=sum(row["population_status"]!="PASS" for row in status_by_district.values())
    hard_mag=sum(max(0,row["floor"]-row["population"],row["population"]-row["cap"]) for row in status_by_district.values())
    outside=sum(abs(p-target)>tol for p in vals)
    maxdev=max((abs(p-target)/target for p in vals),default=0.0)
    sq=sum(((p-target)/target)**2 for p in vals)
    if report_path and report_path.exists():
        _merge_report_metadata(
            report_path,
            population_status_by_district=status_by_district,
            population_baseline_status="PASS" if hard==0 else "PASS_WITH_EXCEPTIONS",
            districts_below_floor=sum(row["population_status"]=="BELOW_FLOOR" for row in status_by_district.values()),
            districts_above_cap=sum(row["population_status"]=="ABOVE_CEILING" for row in status_by_district.values()),
            objective_final=[hard,round(hard_mag/target,12),outside,round(maxdev,12),round(sq,12)],
            districts_outside_tolerance=outside,
            best_max_rel_dev=round(maxdev,12),
        )
    return g

def _refresh_final_population_products(cfg,s5,out_path,report_path):
    graph=json.loads(Path(str(s5["in_graph_json"])).read_text(encoding="utf-8"))
    g=load_geo(out_path)
    idf=s5.get("id_field","CUSEC_KEY"); did=s5.get("district_field","district_id"); popf=s5.get("pop_field","POP_2023")
    pop={str(node["id"]):int(node.get("pop",0)) for node in graph["nodes"]}
    target,floor,cap,tol=hard_limits(cfg,k=len(set(g[did])),total_pop=sum(pop.values()))
    floor_exempt={str(value).zfill(2) for value in ((cfg.get("validation") or {}).get("population_floor_exempt_partitions") or [])}
    provf=s5.get("province_field","CPRO"); districts={}
    for district,frame in g.groupby(did):
        provinces={str(value).zfill(2) for value in frame[provf]}
        if len(provinces)==1:
            province=next(iter(provinces)); districts[str(district)]=0.0 if province in floor_exempt else floor
    g=_refresh_population_report(report_path,g,did,pop,idf,target,floor,cap,tol,districts,popf)
    write_geo(g,out_path)

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
    floor_exempt={
        str(value).zfill(2)
        for value in ((cfg.get("validation") or {}).get("population_floor_exempt_partitions") or [])
    }
    district_floors={}
    for district in set(assignments.values()):
        provinces={
            str(units[u].get("province")).zfill(2)
            for u,d in assignments.items()
            if d==district
        }
        if len(provinces)==1:
            province=next(iter(provinces))
            district_floors[district]=0.0 if province in floor_exempt else floor

    baseline_check=verify_partition_constraints(
        assignments,units,adj,floor=floor,cap=cap,district_floors=district_floors
    )
    if not baseline_check.get("valid"):
        raise SystemExit(f"M05 repair: baseline estructuralmente inválido: {baseline_check}")

    hard_before=int(baseline_check.get("hard_population_violations",0))
    floor_overrides={
        str(district):float(value)
        for district,value in sorted(district_floors.items(),key=lambda item:str(item[0]))
        if float(value)!=float(floor)
    }
    # Experimental private strategy: distinct from the monotonic legacy search.
    # Intermediate hard-population violations remain inside repair_private; the
    # durable GeoJSON is replaced only after atomic final validation succeeds.
    if rcfg.get("enabled") is True and rcfg.get("strategy") == "private_annealing":
        meta=repair_private(
            assignments=assignments, units=units, adjacency=adj,
            target=target, tolerance=tol, floor=floor, cap=cap,
            district_floors=district_floors, frozen_units=frozen_units,
            frozen_districts=frozen_districts,
            seed=int(rcfg.get("seed",0)),
            max_candidates=int(rcfg.get("max_candidates",700000)),
            max_seconds=float(rcfg.get("max_seconds",65.0)),
        )
        meta.update({"enabled":True,"strategy":"private_annealing",
                     "activation":"EXPLICIT_EXPERIMENTAL_SELECTION",
                     "hard_population_violations_before":hard_before,
                     "population_floor_exempt_partitions":sorted(floor_exempt),
                     "district_floor_overrides":floor_overrides,
                     "frozen_districts":sorted(frozen_districts,key=str),
                     "frozen_units":len(frozen_units),
                     "intermediate_population_violations_private_only":True})
        if meta.get("accepted"):
            candidate=meta["assignments"]
            if any(candidate.get(u)!=assignments[u] for u in frozen_units):
                meta.update(accepted=False,result="ATOMIC_REJECTION_FROZEN_UNIT_CHANGED",
                            assignments=assignments)
            else:
                candidate_geo=g.copy()
                for u,d in candidate.items(): candidate_geo.loc[candidate_geo["ddd_unit_id"]==u,did]=d
                candidate_geo=_refresh_population_report(None,candidate_geo,did,pop,idf,target,floor,cap,tol,district_floors,s5.get("pop_field","POP_2023"))
                gate=_official_private_candidate_gate(cfg,candidate_geo,out_path,meta.get("seed",0))
                meta["official_atomic_gate"]=gate
                if not gate.get("passed"):
                    meta.update(accepted=False,result="ATOMIC_REJECTION_OFFICIAL_VALIDATION",assignments=assignments)
                else:
                    _refresh_population_report(report_path,candidate_geo,did,pop,idf,target,floor,cap,tol,district_floors,s5.get("pop_field","POP_2023"))
        _merge_report_metadata(report_path,population_repair=meta)
        return meta

    if hard_before == 0:
        meta={
            "enabled":False,
            "activation":"NOT_NEEDED",
            "result":"DISABLED",
            "hard_population_violations_before":0,
            "population_floor_exempt_partitions":sorted(floor_exempt),
            "district_floor_overrides":floor_overrides,
        }
        _merge_report_metadata(report_path,population_repair=meta)
        return meta

    activation="EXPLICITLY_ENABLED" if isinstance(declared,dict) and declared.get("enabled") is True else "AUTO_HARD_VIOLATIONS"
    limits=SearchLimits(
        max_depth=int(rcfg.get("max_depth",3)),
        max_transfer_set=int(rcfg.get("max_transfer_set",2)),
        max_candidates=int(rcfg.get("max_candidates",20000)),
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
        district_floors=district_floors,
    )
    meta["enabled"]=True
    meta["activation"]=activation
    meta["hard_population_violations_before"]=hard_before
    meta["population_floor_exempt_partitions"]=sorted(floor_exempt)
    meta["district_floor_overrides"]=floor_overrides
    moved_frozen={u:(baseline_frozen[u],meta["assignments"].get(u)) for u in baseline_frozen if meta["assignments"].get(u)!=baseline_frozen[u]}
    if moved_frozen: raise SystemExit(f"M05 repair: distrito urbano cerrado modificado: {moved_frozen}")
    meta["frozen_districts"]=sorted(frozen_districts,key=str); meta["frozen_units"]=len(frozen_units)
    for u,d in meta["assignments"].items(): g.loc[g["ddd_unit_id"]==u,did]=d
    g=_refresh_population_report(None,g,did,pop,idf,target,floor,cap,tol,district_floors,s5.get("pop_field","POP_2023"))
    write_geo(g,out_path)
    _merge_report_metadata(report_path,population_repair=meta)
    _refresh_population_report(report_path,g,did,pop,idf,target,floor,cap,tol,district_floors,s5.get("pop_field","POP_2023"))
    return meta

def _post(cfg,s5,out_path,report_path):
    sw=_apply_swap(cfg,s5,out_path,report_path); rp=_apply_population_repair(cfg,s5,out_path,report_path)
    _refresh_final_population_products(cfg,s5,out_path,report_path)
    return sw,rp

def _private_strategy_selected(s5):
    declared=s5.get("population_repair")
    return isinstance(declared,dict) and declared.get("enabled") is True and declared.get("strategy")=="private_annealing"

def _emit_private_rejection_diagnostic(meta):
    """Emit bounded rejection telemetry before atomic staging is cleaned."""
    fields=("result","termination_reason","elapsed_seconds","candidates",
            "generated_candidates","expanded","accepted_moves","discarded_candidates",
            "seed","hard_population_violations_before","hard_population_violations")
    diagnostic={"wrapper_version":WRAPPER_VERSION,"strategy":"private_annealing"}
    diagnostic.update({key:meta[key] for key in fields if key in meta})
    gate=meta.get("official_atomic_gate")
    if isinstance(gate,dict):
        diagnostic["official_atomic_gate"]={key:gate.get(key) for key in ("passed","reason") if key in gate}
    print("M05_PRIVATE_REJECTION_DIAGNOSTIC="+json.dumps(diagnostic,ensure_ascii=False,sort_keys=True),file=sys.stderr,flush=True)


def _run_private_staged(cfg,s5):
    """Keep even the base M05 write private until the selected strategy passes."""
    def execute(staged,staged_report):
        td=staged.parent
        cfg2=copy.deepcopy(cfg); s52=_module_cfg(cfg2); s52["out_geojson"]=str(staged)
        if staged_report:s52["out_report"]=str(staged_report)
        tp=td/"params.yaml"; tp.write_text(yaml.safe_dump(cfg2,sort_keys=False,allow_unicode=True),encoding="utf-8")
        _run_base(str(tp)); _,repair_meta=_post(cfg2,s52,staged,staged_report)
        repair_meta["wrapper_version"]=WRAPPER_VERSION
        admitted=bool(repair_meta.get("accepted")) or (repair_meta.get("result")=="DISABLED" and repair_meta.get("hard_population_violations_before")==0)
        if not admitted:_emit_private_rejection_diagnostic(repair_meta)
        return admitted,repair_meta
    return run_staged_output(s5["out_geojson"],s5.get("out_report"),execute)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--params",required=True); args=ap.parse_args(); params=Path(args.params).resolve(); cfg=load_params_yaml(str(params)); s5=_module_cfg(cfg); in_path=Path(str(s5.get("in_geojson","")))
    if _ogr_can_read_unit(in_path):
        if _private_strategy_selected(s5):
            try:_run_private_staged(cfg,s5)
            except Exception as exc:raise SystemExit(str(exc))
            return
        _run_base(str(params)); out=Path(str(s5["out_geojson"])); report=Path(str(s5["out_report"])) if s5.get("out_report") else None; _post(cfg,s5,out,report); return
    data,inner=_raw_geojson(in_path); labels=[_normalise_label((f.get("properties") or {}).get("ddd_unit_id")) for f in data.get("features",[])]; unique=sorted(set(labels)); mapping={v:i+1 for i,v in enumerate(unique)}
    for f,label in zip(data.get("features",[]),labels): f.setdefault("properties",{})["ddd_unit_id"]=mapping[label]
    with tempfile.TemporaryDirectory(prefix="ddd_m05_760_") as td:
        td=Path(td); ti=td/"in.zip"; to=td/"out.zip"; tr=td/"report.json"; tp=td/"params.yaml"; _write_zip_json(data,ti,"input.geojson")
        cfg2=copy.deepcopy(cfg); s52=_module_cfg(cfg2); s52.update(in_geojson=str(ti),out_geojson=str(to),out_report=str(tr)); cfg2.setdefault("modulos",{})["modulo_05_optimizar_distritos"]=s52; tp.write_text(yaml.safe_dump(cfg2,sort_keys=False,allow_unicode=True),encoding="utf-8")
        _run_base(str(tp)); _,repair_meta=_post(cfg2,s52,to,tr)
        if _private_strategy_selected(s5):
            admitted=bool(repair_meta.get("accepted")) or (repair_meta.get("result")=="DISABLED" and repair_meta.get("hard_population_violations_before")==0)
            def promote(staged,staged_report):
                if not admitted:
                    repair_meta["wrapper_version"]=WRAPPER_VERSION
                    _emit_private_rejection_diagnostic(repair_meta)
                    return False,repair_meta
                staged.write_bytes(to.read_bytes())
                if staged_report:
                    staged_report.write_bytes(tr.read_bytes())
                    _merge_report_metadata(staged_report,unit_id_normalization={"applied":True,"units":len(unique)})
                return True,repair_meta
            try:run_staged_output(s5["out_geojson"],s5.get("out_report"),promote)
            except Exception as exc:raise SystemExit(str(exc))
        else:
            final=Path(str(s5["out_geojson"])); final.parent.mkdir(parents=True,exist_ok=True); final.write_bytes(to.read_bytes())
            if s5.get("out_report"):
                fr=Path(str(s5["out_report"])); fr.parent.mkdir(parents=True,exist_ok=True); fr.write_bytes(tr.read_bytes()); _merge_report_metadata(fr,unit_id_normalization={"applied":True,"units":len(unique)})
if __name__=="__main__": main()
