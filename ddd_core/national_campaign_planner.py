"""Read-only READY selector for the persistent national campaign ledger.

It validates task/dependency identity and cycles, then proposes deterministic
work that has satisfied dependencies and does not conflict with active file
locks. It never mutates the ledger, assigns workers, or starts territorial work.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
from pathlib import Path
from typing import Any

TERMINAL_DEPENDENCIES = {"COMPLETE", "INTEGRATED", "REVIEW_PASS"}
ELIGIBLE = {"DISCOVERED", "READY"}


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def select_ready_tasks(registry: dict[str, Any], graph: dict[str, Any], locks: dict[str, Any]) -> dict[str, Any]:
    tasks = registry.get("tasks")
    ids = [task.get("id") for task in tasks or [] if isinstance(task, dict)]
    if not isinstance(tasks, list) or len(ids) != len(tasks) or len(ids) != len(set(ids)):
        raise ValueError("TASK_IDS_INVALID_OR_DUPLICATED")
    by_id = {task["id"]: task for task in tasks}
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or set(nodes) != set(ids) or len(nodes) != len(ids):
        raise ValueError("DAG_NODE_COVERAGE_MISMATCH")
    if not isinstance(edges, list):
        raise ValueError("DAG_EDGES_INVALID")
    dependencies = {task_id: set() for task_id in ids}
    for edge in edges:
        if not isinstance(edge, dict):
            raise ValueError("DAG_EDGE_INVALID")
        parent, child = edge.get("from"), edge.get("to")
        if parent not in by_id or child not in by_id or parent == child:
            raise ValueError("DAG_EDGE_ENDPOINT_INVALID")
        dependencies[child].add(parent)
    if any(set(task.get("dependencies", [])) != dependencies[task_id]
           for task_id, task in by_id.items()):
        raise ValueError("TASK_DEPENDENCY_EDGE_MISMATCH")

    # Kahn's algorithm both rejects cycles and avoids depending on file order.
    outgoing = {task_id: set() for task_id in ids}
    remaining = {task_id: len(dependencies[task_id]) for task_id in ids}
    for child, parents in dependencies.items():
        for parent in parents:
            outgoing[parent].add(child)
    ready_nodes = sorted(task_id for task_id, degree in remaining.items() if degree == 0)
    visited = 0
    while ready_nodes:
        current = ready_nodes.pop(0)
        visited += 1
        for child in sorted(outgoing[current]):
            remaining[child] -= 1
            if remaining[child] == 0:
                ready_nodes.append(child)
                ready_nodes.sort()
    if visited != len(ids):
        raise ValueError("DEPENDENCY_CYCLE")

    active_patterns: list[tuple[str, str]] = []
    for lock in locks.get("locks", []):
        if lock.get("status") not in {"RUNNING", "TESTING", "IMPLEMENTED", "REVIEWING"}:
            continue
        for pattern in str(lock.get("resource", "")).split(";"):
            pattern = pattern.strip()
            if pattern:
                active_patterns.append((lock.get("task", "UNKNOWN"), pattern))

    candidates = []
    deferred = []
    for task_id in sorted(ids):
        task = by_id[task_id]
        if task.get("status") not in ELIGIBLE:
            continue
        unresolved = sorted(dep for dep in dependencies[task_id]
                            if by_id[dep].get("status") not in TERMINAL_DEPENDENCIES)
        if unresolved:
            deferred.append({"task_id": task_id, "reason": "DEPENDENCIES_PENDING", "dependencies": unresolved})
            continue
        conflicts = sorted({owner for owner, pattern in active_patterns
                            if any(fnmatch.fnmatchcase(path, pattern)
                                   for path in task.get("files_affected", []))})
        if conflicts:
            deferred.append({"task_id": task_id, "reason": "RESOURCE_LOCKED", "owners": conflicts})
            continue
        candidates.append(task)
    candidates.sort(key=lambda task: (task.get("priority", 999), task["id"]))
    return {
        "schema": "ddd.national-ready-proposal/1.0",
        "campaign_id": registry.get("campaign_id"),
        "registry_sha256": hashlib.sha256(
            json.dumps(registry, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "ready_task_ids": [task["id"] for task in candidates],
        "deferred": deferred,
        "execution_started": False,
        "generation_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--dependencies", required=True, type=Path)
    parser.add_argument("--locks", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = select_ready_tasks(_load(args.registry), _load(args.dependencies), _load(args.locks))
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
