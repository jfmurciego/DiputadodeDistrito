"""Version 1.0.0; registro verificable de la campaña nacional; 2026-10-13.
Alcance: integridad estática del DAG A–J; estado: candidato.
Cambio/motivo: evitar IDs duplicados, dependencias rotas y matrices incoherentes.
Origen: nuevo; no sustituye a los gestores de ejecución territoriales.
"""
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013"


def test_registry_ids_states_dependencies_and_dag_are_valid():
    registry = json.loads((CAMPAIGN / "TASK_REGISTRY.json").read_text())
    graph = json.loads((CAMPAIGN / "DEPENDENCIES.json").read_text())
    tasks = registry["tasks"]
    ids = [task["id"] for task in tasks]
    assert len(ids) == len(set(ids))
    assert all(task["status"] in registry["states"] for task in tasks)
    assert set(graph["nodes"]) == set(ids)
    assert all(edge["from"] in ids and edge["to"] in ids for edge in graph["edges"])
    assert all(dep in ids for task in tasks for dep in task["dependencies"])

    outgoing = {task_id: [] for task_id in ids}
    indegree = {task_id: 0 for task_id in ids}
    for edge in graph["edges"]:
        outgoing[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    ready = sorted(task_id for task_id, degree in indegree.items() if degree == 0)
    visited = 0
    while ready:
        current = ready.pop(0)
        visited += 1
        for dependent in outgoing[current]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
    assert visited == len(ids), "dependency graph must be acyclic"


def test_completion_matrix_is_derived_from_task_registry():
    registry = json.loads((CAMPAIGN / "TASK_REGISTRY.json").read_text())
    rows = list(csv.DictReader((CAMPAIGN / "MATRIZ_CIERRE_AJ.csv").open(newline="")))
    tasks = registry["tasks"]
    by_line = {line: [task for task in tasks if task["line"] == line] for line in "ABCDEFGHIJ"}
    assert len(rows) == 11
    for row in rows[:-1]:
        expected = by_line[row["line"]]
        assert int(row["total_tasks"]) == len(expected)
        assert int(row["COMPLETE"]) == sum(task["status"] == "COMPLETE" for task in expected)
        assert int(row["READY"]) == sum(task["status"] == "READY" for task in expected)
        assert int(row["BLOCKED_EVIDENCE"]) == sum(task["status"] == "BLOCKED_EVIDENCE" for task in expected)
    total = rows[-1]
    assert int(total["total_tasks"]) == len(tasks)
    assert registry["main_sha"] == "21a4a150eb14f1abecd5d798b159d84a71df1f4a"
    columns = [key for key in rows[0] if key not in {"line", "total_tasks", "evidence"}]
    for column in columns:
        expected = sum(task["status"] == column for task in tasks)
        assert int(total[column]) == expected


def test_campaign_ledger_preserves_all_production_barriers():
    manifest = json.loads((CAMPAIGN / "CAMPAIGN_MANIFEST.json").read_text())
    assert manifest["state"] == "NATIONAL_INCOMPLETE"
    assert manifest["baseline_main"] == "21a4a150eb14f1abecd5d798b159d84a71df1f4a"
    assert manifest["permissions"]["merge"] is False
    assert manifest["permissions"]["production_generation"] is False
    assert manifest["permissions"]["source_download"] is False
    assert "K=407" in manifest["owner_decisions_preserved"]
    assert "generation_authorized=false" in manifest["owner_decisions_preserved"]


def test_checkpoint_queues_and_blockers_agree_with_task_states():
    registry = json.loads((CAMPAIGN / "TASK_REGISTRY.json").read_text())
    checkpoint = json.loads((CAMPAIGN / "CHECKPOINT.json").read_text())
    review = json.loads((CAMPAIGN / "REVIEW_QUEUE.json").read_text())
    blockers = json.loads((CAMPAIGN / "BLOCKER_REGISTRY.json").read_text())
    locks = json.loads((CAMPAIGN / "RESOURCE_LOCKS.json").read_text())
    integration = json.loads((CAMPAIGN / "INTEGRATION_QUEUE.json").read_text())
    events = [json.loads(line) for line in (CAMPAIGN / "EVENT_LOG.jsonl").read_text().splitlines()]
    by_id = {task["id"]: task for task in registry["tasks"]}

    review_status = {"REVIEW_PASS": "REVIEW_PASS", "READY_TO_ASSIGN": "READY",
                     "PENDING_IMPLEMENTATION": "RUNNING", "IN_PROGRESS": "REVIEWING"}
    for item in review["items"]:
        assert by_id[item["task_id"]]["status"] == review_status[item["status"]]

    running = {task_id for task_id in checkpoint.get("running_work", [])}
    lock_running = {item["task"] for item in locks["locks"] if item["status"] == "RUNNING"}
    assert lock_running == running
    ready = set(checkpoint.get("ready_next", []))
    assert not running.intersection(ready)
    for task_id in running:
        assert by_id[task_id]["status"] in {"RUNNING", "TESTING", "IMPLEMENTED", "REVIEWING"}
    for task_id in ready:
        task = by_id[task_id]
        assert task["status"] == "READY"
        assert all(by_id[dep]["status"] in {"COMPLETE", "INTEGRATED", "REVIEW_PASS"}
                   for dep in task["dependencies"])
    expected_ready = {task["id"] for task in registry["tasks"]
                      if task["status"] == "READY"
                      and all(by_id[dep]["status"] in {"COMPLETE", "INTEGRATED", "REVIEW_PASS"}
                              for dep in task["dependencies"])}
    assert ready == expected_ready

    event_ids = [event.get("event_id", event.get("id")) for event in events]
    assert checkpoint["latest_event"] == event_ids[-1]
    assert len(set(event_ids)) == len(events)
    review_pass = {item["task_id"] for item in review["items"]
                   if item["status"] == "REVIEW_PASS"}
    queued = {item["task_id"] for item in integration["items"]}
    assert review_pass.intersection({"NAT-B-002", "NAT-D-005", "NAT-I-001"}).issubset(queued)
    assert all(item["merge_authorized"] is False for item in integration["items"])

    for blocker in blockers["blockers"]:
        for task_id in blocker["tasks"]:
            assert by_id[task_id]["status"] in {"WAIT_OWNER", "BLOCKED_EVIDENCE", "BLOCKED_DEPENDENCY", "BLOCKED_ENVIRONMENT"}


def test_active_implementation_paths_are_real_and_match_task_scope():
    registry = json.loads((CAMPAIGN / "TASK_REGISTRY.json").read_text())
    by_id = {task["id"]: task for task in registry["tasks"]}
    for task_id in ("NAT-B-002", "NAT-I-001"):
        assert by_id[task_id]["files_affected"]
        assert all((ROOT / rel).is_file() for rel in by_id[task_id]["files_affected"])
