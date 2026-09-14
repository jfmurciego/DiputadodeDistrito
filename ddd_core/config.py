#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
NÚCLEO: Configuración
VERSIÓN: 1.4.0
NOMBRE DE VERSIÓN: Contrato territorial estricto
FECHA: 2026-09-12
QUÉ HACE: carga el contrato territorial, resuelve rutas y centraliza sus límites poblacionales obligatorios.
ESTADO: candidato F1.3
CAMBIOS: añade hard_limits() con fallo explícito cuando falta cualquier coeficiente territorial.
MOTIVO: impedir la herencia silenciosa de parámetros de Aragón.
ANTERIOR: legacy/core/config_v1.3.0.py
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict
EXT_HINTS=(".zip",".geojson",".json",".csv",".jsonl",".shp",".gpkg",".parquet",".yaml",".yml")
def load_params_yaml(params_path:str)->Dict[str,Any]:
    try: import yaml
    except ImportError as e: raise SystemExit("Falta dependencia: PyYAML") from e
    p=Path(params_path).expanduser().resolve()
    if not p.exists(): raise FileNotFoundError(f"Configuración no encontrada: {p}")
    data=yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data,dict): raise ValueError("El YAML debe tener un objeto raíz")
    io_cfg=data.get("io",{}) or {}; root=p.parent.resolve(); pr=(io_cfg.get("project_root",{}) or {}).get("path","")
    if pr:
        pp=Path(str(pr)).expanduser(); root=pp.resolve() if pp.is_absolute() else (p.parent/pp).resolve()
    meta=data.get("meta",{}) or {}; run_name=meta.get("run_name",p.stem); year=int(meta.get("year",2025)); scope=meta.get("scope","national") or "national"; run_id=os.getenv("DDD_RUN_ID") or meta.get("run_id") or "local"
    fmt={"run_name":run_name,"year":year,"scope":scope,"run_id":run_id}
    def _fmt(s:str)->str:
        try:return s.format(**fmt)
        except Exception:return s
    def _walk(obj):
        if isinstance(obj,dict):return {k:_walk(v) for k,v in obj.items()}
        if isinstance(obj,list):return [_walk(v) for v in obj]
        if isinstance(obj,str):
            s=_fmt(obj)
            if "/" in s or s.endswith(EXT_HINTS):
                xp=Path(s); return str(xp if xp.is_absolute() else (root/xp).resolve())
            return s
        return obj
    resolved=_walk(data); resolved.setdefault("meta",{}); resolved["meta"].update({"run_name":run_name,"year":year,"scope":scope,"run_id":run_id}); resolved.setdefault("io",{}); resolved["io"].setdefault("project_root",{}); resolved["io"]["project_root"]["path"]=str(root); resolved["_internal"]={"params_path":str(p),"root":str(root),"fmt":fmt}; return resolved
def step_cfg(cfg:Dict[str,Any],step_key:str)->Dict[str,Any]:
    step=(cfg.get("steps",{}) or {}).get(step_key,{}) or {}
    if not isinstance(step,dict):raise ValueError(f"steps.{step_key} debe ser un mapping")
    return step
def module_cfg(cfg:Dict[str,Any],module_key:str,legacy_step_key:str|None=None)->Dict[str,Any]:
    module=(cfg.get("modulos",{}) or {}).get(module_key)
    if isinstance(module,dict):return module
    if legacy_step_key:return step_cfg(cfg,legacy_step_key)
    raise ValueError(f"No existe modulos.{module_key}")
def require(value:Any,msg:str):
    if value is None or (isinstance(value,str) and not value.strip()) or (isinstance(value,list) and not value):raise SystemExit(msg)
    return value

def hard_limits(cfg:Dict[str,Any],*,k:int,total_pop:float)->tuple[float,float,float,float]:
    """Devuelve (target, floor, cap, tol); falla si el territorio no los declara."""
    val=cfg.get("validation",{}) or {}
    required=("population_floor_ratio","population_cap_ratio","target_tolerance_ratio")
    missing=[key for key in required if key not in val]
    if missing:
        raise SystemExit(
            f"El territorio no declara {missing}. CONTRATO_TERRITORIO.md §5 prohíbe "
            "heredar silenciosamente valores de otro territorio."
        )
    target=float(total_pop)/int(k)
    return (
        target,
        target*float(val["population_floor_ratio"]),
        target*float(val["population_cap_ratio"]),
        target*float(val["target_tolerance_ratio"]),
    )
