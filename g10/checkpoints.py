#!/usr/bin/env python3
"""Checkpoints semánticos G10 v1.0.1: reanudación segura sin recalcular evidencia."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
from g10.stages import BY_ID

CANONICAL_STATUSES={"CANONICAL_VERIFIED_LEGACY","CERTIFIED"}

@dataclass(frozen=True)
class ResumeDecision:
    resume_stage_id: str | None
    reason: str
    checkpoint: Mapping[str, Any] | None

def _order(stage_id:str)->int:
    if stage_id not in BY_ID: raise ValueError(f"Etapa desconocida: {stage_id}")
    return BY_ID[stage_id].stage_order

def validate_checkpoint_inventory(inventory:Mapping[str,Any])->None:
    errors=[]
    if inventory.get("schema_version")!="1.0": errors.append("schema_version debe ser 1.0")
    if not isinstance(inventory.get("territory"),str) or not inventory["territory"]: errors.append("territory es obligatorio")
    if not isinstance(inventory.get("source_run"),str) or not inventory["source_run"]: errors.append("source_run es obligatorio")
    checkpoints=inventory.get("checkpoints")
    if not isinstance(checkpoints,list): errors.append("checkpoints debe ser lista"); checkpoints=[]
    seen=set()
    for i,item in enumerate(checkpoints):
        if not isinstance(item,dict): errors.append(f"checkpoints[{i}] debe ser objeto"); continue
        stage_id=item.get("stage_id")
        if stage_id not in BY_ID: errors.append(f"checkpoints[{i}].stage_id desconocido")
        if not isinstance(item.get("products_manifest"),str) or not item.get("products_manifest"): errors.append(f"checkpoints[{i}].products_manifest obligatorio")
        if item.get("status") not in CANONICAL_STATUSES|{"EXPERIMENTAL_BLOCKED"}: errors.append(f"checkpoints[{i}].status inválido")
        if stage_id in seen: errors.append(f"etapa duplicada: {stage_id}")
        seen.add(stage_id)
    if errors: raise ValueError("Inventario de checkpoints inválido:\n- "+"\n- ".join(errors))

def validate_checkpoint_index(index:Mapping[str,Any])->None:
    if index.get("schema_version")!="1.0" or not isinstance(index.get("territories"),list):
        raise ValueError("Índice de checkpoints inválido")
    for territory in index["territories"]:
        validate_checkpoint_inventory({"schema_version":"1.0","territory":territory.get("territory"),"source_run":territory.get("source_run"),"checkpoints":territory.get("checkpoints")})

def _usable(checkpoint:Mapping[str,Any])->bool:
    return checkpoint.get("status") in CANONICAL_STATUSES and bool(checkpoint.get("products_manifest"))

def select_resume_checkpoint(checkpoints:Sequence[Mapping[str,Any]],*,changed_stage_id:str,target_stage_id:str)->ResumeDecision:
    """El último checkpoint anterior al cambio y al objetivo; nunca salta una etapa no materializada."""
    changed_order=_order(changed_stage_id); target_order=_order(target_stage_id)
    ceiling=min(changed_order-1,target_order-1)
    candidates=[item for item in checkpoints if isinstance(item,Mapping) and item.get("stage_id") in BY_ID and _order(str(item["stage_id"]))<=ceiling and _usable(item)]
    if not candidates:
        return ResumeDecision(None,"no existe checkpoint canónico anterior al cambio",None)
    chosen=max(candidates,key=lambda item:_order(str(item["stage_id"])))
    return ResumeDecision(str(chosen["stage_id"]),f"reanudación segura desde {chosen['stage_id']}",chosen)

def resolve_checkpoint_path(checkpoint:Mapping[str,Any],*,root:str|Path=".")->Path:
    path=(Path(root).resolve()/str(checkpoint["products_manifest"])).resolve()
    try: path.relative_to(Path(root).resolve())
    except ValueError as exc: raise ValueError("products_manifest fuera del repositorio") from exc
    return path
