#!/usr/bin/env python3
"""Núcleo G10 v1.1.0: catálogo semántico, huellas, admisión y evidencia durable."""
from __future__ import annotations
import hashlib,json,os,tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any,Iterable,Mapping
from g10.stages import CATALOG_VERSION, normalize

class TaskStatus(str,Enum):
    PENDING="PENDING"; ADMITTED="ADMITTED"; REUSED="REUSED"; CANONICAL_VERIFIED_LEGACY="CANONICAL_VERIFIED_LEGACY"
    WAITING_DEPENDENCY="WAITING_DEPENDENCY"; REJECTED_INPUTS="REJECTED_INPUTS"; REJECTED_BUDGET="REJECTED_BUDGET"
    BLOCKED_DECISION="BLOCKED_DECISION"; RUNNING="RUNNING"; SUCCESS="SUCCESS"; RETRY="RETRY"
    REQUIRES_AGENT="REQUIRES_AGENT"; REQUIRES_HUMAN="REQUIRES_HUMAN"; BLOCKED="BLOCKED"; LOOP_GUARD="LOOP_GUARD"
class FailureClass(str,Enum):
    TRANSIENT_NETWORK="TRANSIENT_NETWORK"; RUNNER_FAILURE="RUNNER_FAILURE"; TIMEOUT="TIMEOUT"; INVALID_INPUT="INVALID_INPUT"
    CONTRACT_FAILURE="CONTRACT_FAILURE"; REGRESSION="REGRESSION"; TOPOLOGY_BLOCK="TOPOLOGY_BLOCK"; PUBLISH_FAILURE="PUBLISH_FAILURE"; UNKNOWN="UNKNOWN"
@dataclass(frozen=True)
class Admission: status: TaskStatus; reason: str
REQUIRED_TASK_FIELDS={"task_id":str,"territory":str,"depends_on":list,"max_attempts":int,"timeout_minutes":int,"estimated_runner_minutes":int,"success_contract":str,"action":str}
ALLOWED_ACTIONS={"g10_selftest","validate_config","territory_m01_m06","verify_existing_evidence"}

def canonical_json(value:Any)->bytes: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode("utf-8")
def compute_fingerprint(paths:Iterable[str|Path],*,context:Mapping[str,Any]|None=None,root:str|Path=".")->str:
    base=Path(root).resolve(); digest=hashlib.sha256(); digest.update(b"DDD-G10-v1\0"); digest.update(canonical_json(context or {}))
    for raw in sorted({str(Path(p)) for p in paths}):
        path=(base/raw).resolve()
        try: relative=path.relative_to(base)
        except ValueError as exc: raise ValueError(f"Ruta fuera del repositorio: {raw}") from exc
        if not path.is_file(): raise FileNotFoundError(raw)
        digest.update(b"\0PATH\0"+relative.as_posix().encode()+b"\0")
        with path.open("rb") as handle:
            for block in iter(lambda:handle.read(1024*1024),b""): digest.update(block)
    return "sha256:"+digest.hexdigest()

def normalized_task(task:Mapping[str,Any])->dict[str,Any]: return normalize(dict(task))
def task_fingerprint(task:Mapping[str,Any],*,root:str|Path=".")->str:
    item=normalized_task(task); paths=item.get("fingerprint_inputs",[])
    if not isinstance(paths,list): raise ValueError("fingerprint_inputs debe ser lista")
    context={"task_id":item["task_id"],"territory":item["territory"],"stage_id":item["stage_id"],"stage_catalog_version":CATALOG_VERSION,"action":item["action"]}
    return compute_fingerprint(paths,context=context,root=root)

def validate_plan(plan:Mapping[str,Any])->None:
    errors=[]; version=plan.get("schema_version")
    if version not in {"1.0","1.1"}: errors.append("schema_version debe ser '1.0' o '1.1'")
    if not isinstance(plan.get("lot_id"),str) or not plan.get("lot_id"): errors.append("lot_id es obligatorio")
    budget=plan.get("budget",{})
    if not isinstance(budget,dict) or not isinstance(budget.get("runner_minutes"),int) or budget.get("runner_minutes",0)<0: errors.append("budget.runner_minutes debe ser entero no negativo")
    if not isinstance(budget,dict) or not isinstance(budget.get("max_parallel"),int) or budget.get("max_parallel",0)<1: errors.append("budget.max_parallel debe ser entero positivo")
    tasks=plan.get("tasks"); tasks=tasks if isinstance(tasks,list) else []
    if not tasks: errors.append("tasks debe ser una lista no vacía")
    ids=set()
    for index,task in enumerate(tasks):
        if not isinstance(task,dict): errors.append(f"tasks[{index}] debe ser objeto"); continue
        for field,expected in REQUIRED_TASK_FIELDS.items():
            if not isinstance(task.get(field),expected): errors.append(f"tasks[{index}].{field} debe ser {expected.__name__}")
        if version=="1.0" and not isinstance(task.get("stage"),str): errors.append(f"tasks[{index}].stage debe ser str")
        if version=="1.1":
            if not isinstance(task.get("stage_id"),str): errors.append(f"tasks[{index}].stage_id debe ser str")
            if not isinstance(task.get("fingerprint_inputs"),list): errors.append(f"tasks[{index}].fingerprint_inputs debe ser lista")
        try: normalized_task(task)
        except (KeyError,ValueError) as exc: errors.append(f"tasks[{index}] etapa: {exc}")
        task_id=task.get("task_id")
        if isinstance(task_id,str):
            if task_id in ids: errors.append(f"task_id duplicado: {task_id}")
            ids.add(task_id)
        if task.get("action") not in ALLOWED_ACTIONS: errors.append(f"acción no permitida: {task.get('action')}")
        for field in ("max_attempts","timeout_minutes","estimated_runner_minutes"):
            value=task.get(field)
            if isinstance(value,int) and value<0: errors.append(f"tasks[{index}].{field} no puede ser negativo")
    for task in tasks:
        if isinstance(task,dict):
            for dep in task.get("depends_on",[]):
                if dep not in ids: errors.append(f"dependencia inexistente {dep} en {task.get('task_id')}")
                if dep==task.get("task_id"): errors.append(f"autodependencia en {dep}")
    if errors: raise ValueError("Plan G10 inválido:\n- "+"\n- ".join(errors))

def successful_fingerprints(state:Mapping[str,Any])->set[str]:
    return {str(x.get("fingerprint")) for x in state.get("records",[]) if x.get("status") in {"SUCCESS","REUSED"} and isinstance(x.get("fingerprint"),str)}
def decide_admission(task:Mapping[str,Any],*,completed:set[str],running_fingerprints:set[str],successful_fingerprints:set[str],fingerprint:str,remaining_runner_minutes:int,human_blocked:bool=False)->Admission:
    missing=sorted(set(task.get("depends_on",[]))-completed)
    if missing:return Admission(TaskStatus.WAITING_DEPENDENCY,f"dependencias pendientes: {missing}")
    if human_blocked:return Admission(TaskStatus.BLOCKED_DECISION,"decisión humana pendiente")
    if fingerprint in successful_fingerprints:return Admission(TaskStatus.REUSED,"resultado válido existente para la misma huella")
    if fingerprint in running_fingerprints:return Admission(TaskStatus.WAITING_DEPENDENCY,"ejecución idéntica ya en curso")
    estimated=int(task.get("estimated_runner_minutes",0))
    if estimated>remaining_runner_minutes:return Admission(TaskStatus.REJECTED_BUDGET,f"requiere {estimated}, quedan {remaining_runner_minutes} minutos")
    return Admission(TaskStatus.ADMITTED,"entradas, dependencias y presupuesto válidos")

def admission_matrix(plan:Mapping[str,Any],state:Mapping[str,Any],*,root:str|Path=".")->dict[str,Any]:
    validate_plan(plan); remaining=int(plan["budget"]["runner_minutes"]); successes=successful_fingerprints(state); include=[]; pre=[]
    for raw in plan["tasks"]:
        item=normalized_task(raw); fp=task_fingerprint(item,root=root)
        admission=decide_admission(item,completed=set(),running_fingerprints=set(),successful_fingerprints=successes,fingerprint=fp,remaining_runner_minutes=remaining)
        if admission.status==TaskStatus.ADMITTED: remaining-=int(item["estimated_runner_minutes"])
        entry={key:item.get(key) for key in ("task_id","territory","action","config","timeout_minutes","stage_id","stage_name","layer_id","legacy_module","artifact_paths")}
        entry.update({"fingerprint":fp,"admission":admission.status.value,"admission_reason":admission.reason})
        include.append(entry); pre.append(entry)
    return {"include":include,"tasks":pre,"remaining_runner_minutes":remaining}

def classify_failure(*,exit_code:int,log:str="",failed_stage:str|None=None)->FailureClass|None:
    if exit_code==0:return None
    value=log.casefold()
    if any(x in value for x in ("timed out","timeout","deadline exceeded")):return FailureClass.TIMEOUT
    if any(x in value for x in ("connection reset","temporary failure","503 service unavailable","rate limit")):return FailureClass.TRANSIENT_NETWORK
    if any(x in value for x in ("runner has received a shutdown","lost communication with the server")):return FailureClass.RUNNER_FAILURE
    if any(x in value for x in ("file not found","no such file","checksum mismatch","entrada inválida")):return FailureClass.INVALID_INPUT
    if any(x in value for x in ("regresion vs baseline","regression","trinquete")):return FailureClass.REGRESSION
    if any(x in value for x in ("topology","topología","not contiguous","no contiguo","isolated node")):return FailureClass.TOPOLOGY_BLOCK
    if any(x in value for x in ("flourish","featurecollection","invalid geometry","publish")) or failed_stage=="PUBLIC_PRODUCT_PUBLICATION":return FailureClass.PUBLISH_FAILURE
    if any(x in value for x in ("assertionerror","contract","contrato","invariante")):return FailureClass.CONTRACT_FAILURE
    return FailureClass.UNKNOWN
def retry_decision(failure:FailureClass,*,attempt:int,max_attempts:int,last_valid_checkpoint:str|None)->dict[str,Any]:
    limits={FailureClass.TRANSIENT_NETWORK:2,FailureClass.RUNNER_FAILURE:2,FailureClass.PUBLISH_FAILURE:2,FailureClass.TIMEOUT:1}; limit=min(max_attempts,limits.get(failure,0))
    return {"decision":"RETRY","resume_from":last_valid_checkpoint,"next_attempt":attempt+1,"agent_required":False} if attempt<limit else {"decision":"REQUIRES_AGENT","resume_from":last_valid_checkpoint,"next_attempt":None,"agent_required":True}
def loop_guard(history:Iterable[Mapping[str,Any]],*,fingerprint:str,failure_class:str,decision:str,max_agent_cycles:int=1)->bool:
    return sum(1 for x in history if x.get("fingerprint")==fingerprint and x.get("failure_class")==failure_class and x.get("decision")==decision)>=max_agent_cycles
def aggregate_summaries(summaries:Iterable[Mapping[str,Any]])->dict[str,Any]:
    items=sorted((dict(x) for x in summaries),key=lambda x:x.get("task_id","")); counts={}
    for item in items: counts[str(item.get("status","UNKNOWN"))]=counts.get(str(item.get("status","UNKNOWN")),0)+1
    return {"schema_version":"1.1","stage_catalog_version":CATALOG_VERSION,"tasks_total":len(items),"counts":counts,"requires_human":[x.get("task_id") for x in items if x.get("status") in {"REQUIRES_HUMAN","REQUIRES_AGENT","LOOP_GUARD"}],"tasks":items}
def merge_successful_state(state:Mapping[str,Any],summaries:Iterable[Mapping[str,Any]],*,run_id:str)->dict[str,Any]:
    records=[x for x in state.get("records",[]) if isinstance(x,dict)]; by_key={(x.get("task_id"),x.get("fingerprint")):x for x in records}
    for item in summaries:
        if item.get("status") not in {"SUCCESS","REUSED"}: continue
        key=(item.get("task_id"),item.get("fingerprint")); by_key[key]={"task_id":key[0],"territory":item.get("territory"),"stage_id":item.get("stage_id"),"legacy_module":item.get("legacy_module"),"fingerprint":key[1],"status":"SUCCESS","run_id":str(run_id),"artifacts":item.get("artifacts",[])}
    return {"schema_version":"1.0","stage_catalog_version":CATALOG_VERSION,"records":sorted(by_key.values(),key=lambda x:(str(x.get("task_id")),str(x.get("fingerprint"))))}
def atomic_write_json(path:str|Path,value:Any)->None:
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True);fd,tmp=tempfile.mkstemp(prefix=target.name+".",dir=target.parent)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:json.dump(value,h,ensure_ascii=False,sort_keys=True,indent=2);h.write("\n")
        os.replace(tmp,target)
    except BaseException:
        try:os.unlink(tmp)
        except FileNotFoundError:pass
        raise
