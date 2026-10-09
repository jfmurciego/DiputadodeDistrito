#!/usr/bin/env python3
"""Núcleo G10: huellas, admisión, reintentos, anti-bucle y agregación."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    ADMITTED = "ADMITTED"
    REUSED = "REUSED"
    WAITING_DEPENDENCY = "WAITING_DEPENDENCY"
    REJECTED_INPUTS = "REJECTED_INPUTS"
    REJECTED_BUDGET = "REJECTED_BUDGET"
    BLOCKED_DECISION = "BLOCKED_DECISION"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    REQUIRES_AGENT = "REQUIRES_AGENT"
    REQUIRES_HUMAN = "REQUIRES_HUMAN"
    BLOCKED = "BLOCKED"
    LOOP_GUARD = "LOOP_GUARD"


class FailureClass(str, Enum):
    TRANSIENT_NETWORK = "TRANSIENT_NETWORK"
    RUNNER_FAILURE = "RUNNER_FAILURE"
    TIMEOUT = "TIMEOUT"
    INVALID_INPUT = "INVALID_INPUT"
    CONTRACT_FAILURE = "CONTRACT_FAILURE"
    REGRESSION = "REGRESSION"
    TOPOLOGY_BLOCK = "TOPOLOGY_BLOCK"
    PUBLISH_FAILURE = "PUBLISH_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Admission:
    status: TaskStatus
    reason: str


REQUIRED_TASK_FIELDS = {
    "task_id": str,
    "territory": str,
    "stage": str,
    "depends_on": list,
    "max_attempts": int,
    "timeout_minutes": int,
    "estimated_runner_minutes": int,
    "success_contract": str,
    "action": str,
}
ALLOWED_ACTIONS = {"g10_selftest", "validate_config", "territory_m01_m06"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def compute_fingerprint(paths: Iterable[str | Path], *, context: Mapping[str, Any] | None = None,
                        root: str | Path = ".") -> str:
    """Huella estable del contenido; el orden recibido no afecta al resultado."""
    base = Path(root).resolve()
    digest = hashlib.sha256()
    digest.update(b"DDD-G10-v1\0")
    digest.update(canonical_json(context or {}))
    for raw in sorted({str(Path(p)) for p in paths}):
        path = (base / raw).resolve()
        try:
            relative = path.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"Ruta fuera del repositorio: {raw}") from exc
        if not path.is_file():
            raise FileNotFoundError(raw)
        digest.update(b"\0PATH\0" + relative.as_posix().encode("utf-8") + b"\0")
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return "sha256:" + digest.hexdigest()


def validate_plan(plan: Mapping[str, Any]) -> None:
    errors: list[str] = []
    if plan.get("schema_version") != "1.0":
        errors.append("schema_version debe ser '1.0'")
    if not isinstance(plan.get("lot_id"), str) or not plan.get("lot_id"):
        errors.append("lot_id es obligatorio")
    budget = plan.get("budget", {})
    if not isinstance(budget, dict) or not isinstance(budget.get("runner_minutes"), int) or budget.get("runner_minutes", 0) < 0:
        errors.append("budget.runner_minutes debe ser entero no negativo")
    if not isinstance(budget, dict) or not isinstance(budget.get("max_parallel"), int) or budget.get("max_parallel", 0) < 1:
        errors.append("budget.max_parallel debe ser entero positivo")
    tasks = plan.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks debe ser una lista no vacía")
        tasks = []
    ids: set[str] = set()
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{index}] debe ser un objeto")
            continue
        for field, expected in REQUIRED_TASK_FIELDS.items():
            if not isinstance(task.get(field), expected):
                errors.append(f"tasks[{index}].{field} debe ser {expected.__name__}")
        task_id = task.get("task_id")
        if isinstance(task_id, str):
            if task_id in ids:
                errors.append(f"task_id duplicado: {task_id}")
            ids.add(task_id)
        if task.get("action") not in ALLOWED_ACTIONS:
            errors.append(f"acción no permitida: {task.get('action')}")
        for field in ("max_attempts", "timeout_minutes", "estimated_runner_minutes"):
            value = task.get(field)
            if isinstance(value, int) and value < 0:
                errors.append(f"tasks[{index}].{field} no puede ser negativo")
    for task in tasks:
        if isinstance(task, dict):
            for dep in task.get("depends_on", []):
                if dep not in ids:
                    errors.append(f"dependencia inexistente {dep} en {task.get('task_id')}")
                if dep == task.get("task_id"):
                    errors.append(f"autodependencia en {dep}")
    if errors:
        raise ValueError("Plan G10 inválido:\n- " + "\n- ".join(errors))


def decide_admission(task: Mapping[str, Any], *, completed: set[str], running_fingerprints: set[str],
                     successful_fingerprints: set[str], fingerprint: str,
                     remaining_runner_minutes: int, human_blocked: bool = False) -> Admission:
    missing = sorted(set(task.get("depends_on", [])) - completed)
    if missing:
        return Admission(TaskStatus.WAITING_DEPENDENCY, f"dependencias pendientes: {missing}")
    if human_blocked:
        return Admission(TaskStatus.BLOCKED_DECISION, "decisión humana pendiente")
    if fingerprint in successful_fingerprints:
        return Admission(TaskStatus.REUSED, "resultado válido existente para la misma huella")
    if fingerprint in running_fingerprints:
        return Admission(TaskStatus.WAITING_DEPENDENCY, "ejecución idéntica ya en curso")
    estimated = int(task.get("estimated_runner_minutes", 0))
    if estimated > remaining_runner_minutes:
        return Admission(TaskStatus.REJECTED_BUDGET, f"requiere {estimated}, quedan {remaining_runner_minutes} minutos")
    return Admission(TaskStatus.ADMITTED, "entradas, dependencias y presupuesto válidos")


def classify_failure(*, exit_code: int, log: str = "", failed_stage: str | None = None) -> FailureClass | None:
    if exit_code == 0:
        return None
    value = log.casefold()
    if any(x in value for x in ("timed out", "timeout", "deadline exceeded")):
        return FailureClass.TIMEOUT
    if any(x in value for x in ("connection reset", "temporary failure", "503 service unavailable", "rate limit")):
        return FailureClass.TRANSIENT_NETWORK
    if any(x in value for x in ("runner has received a shutdown", "lost communication with the server")):
        return FailureClass.RUNNER_FAILURE
    if any(x in value for x in ("file not found", "no such file", "checksum mismatch", "entrada inválida")):
        return FailureClass.INVALID_INPUT
    if any(x in value for x in ("regresion vs baseline", "regression", "trinquete")):
        return FailureClass.REGRESSION
    if any(x in value for x in ("topology", "topología", "not contiguous", "no contiguo", "isolated node")):
        return FailureClass.TOPOLOGY_BLOCK
    if any(x in value for x in ("flourish", "featurecollection", "invalid geometry", "publish")) or failed_stage == "EXPORT":
        return FailureClass.PUBLISH_FAILURE
    if any(x in value for x in ("assertionerror", "contract", "contrato", "invariante")):
        return FailureClass.CONTRACT_FAILURE
    return FailureClass.UNKNOWN


def retry_decision(failure: FailureClass, *, attempt: int, max_attempts: int,
                   last_valid_checkpoint: str | None) -> dict[str, Any]:
    limits = {FailureClass.TRANSIENT_NETWORK: 2, FailureClass.RUNNER_FAILURE: 2,
              FailureClass.PUBLISH_FAILURE: 2, FailureClass.TIMEOUT: 1}
    limit = min(max_attempts, limits.get(failure, 0))
    if attempt < limit:
        return {"decision": "RETRY", "resume_from": last_valid_checkpoint,
                "next_attempt": attempt + 1, "agent_required": False}
    return {"decision": "REQUIRES_AGENT", "resume_from": last_valid_checkpoint,
            "next_attempt": None, "agent_required": True}


def loop_guard(history: Iterable[Mapping[str, Any]], *, fingerprint: str,
               failure_class: str, decision: str, max_agent_cycles: int = 1) -> bool:
    repeats = sum(1 for item in history if item.get("fingerprint") == fingerprint
                  and item.get("failure_class") == failure_class
                  and item.get("decision") == decision)
    return repeats >= max_agent_cycles


def aggregate_summaries(summaries: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    items = sorted((dict(x) for x in summaries), key=lambda x: x.get("task_id", ""))
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    needs_human = [x.get("task_id") for x in items if x.get("status") in {"REQUIRES_HUMAN", "LOOP_GUARD"}]
    return {"schema_version": "1.0", "tasks_total": len(items), "counts": counts,
            "requires_human": needs_human, "tasks": items}


def atomic_write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
