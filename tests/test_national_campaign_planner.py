import pytest

from ddd_core.national_campaign_planner import select_ready_tasks


def _inputs():
    tasks = [
        {"id": "NAT-A-001", "status": "INTEGRATED", "dependencies": [], "priority": 1,
         "files_affected": ["contract.json"]},
        {"id": "NAT-B-001", "status": "DISCOVERED", "dependencies": ["NAT-A-001"],
         "priority": 2, "files_affected": ["docs/report.md"]},
        {"id": "NAT-C-001", "status": "DISCOVERED", "dependencies": ["NAT-A-001"],
         "priority": 1, "files_affected": ["contract.json"]},
    ]
    registry = {"campaign_id": "fixture", "tasks": tasks}
    graph = {"nodes": [task["id"] for task in tasks], "edges": [
        {"from": "NAT-A-001", "to": "NAT-B-001"},
        {"from": "NAT-A-001", "to": "NAT-C-001"},
    ]}
    return registry, graph


def test_ready_selection_is_deterministic_and_respects_active_file_locks():
    registry, graph = _inputs()
    result = select_ready_tasks(registry, graph, {"locks": [
        {"task": "other-worker", "resource": "contract.json", "status": "RUNNING"}
    ]})
    assert result["ready_task_ids"] == ["NAT-B-001"]
    assert result["deferred"] == [{"task_id": "NAT-C-001", "reason": "RESOURCE_LOCKED",
                                  "owners": ["other-worker"]}]
    assert result["execution_started"] is False
    assert result["generation_authorized"] is False


def test_ready_selection_defers_unfinished_dependencies():
    registry, graph = _inputs()
    registry["tasks"][0]["status"] = "REVIEWING"
    result = select_ready_tasks(registry, graph, {"locks": []})
    assert result["ready_task_ids"] == []
    assert all(row["reason"] == "DEPENDENCIES_PENDING" for row in result["deferred"])


@pytest.mark.parametrize("mutation, error", [
    ("cycle", "DEPENDENCY_CYCLE"),
    ("mismatch", "TASK_DEPENDENCY_EDGE_MISMATCH"),
])
def test_invalid_dependency_graph_fails_closed(mutation, error):
    registry, graph = _inputs()
    if mutation == "cycle":
        registry["tasks"][0]["dependencies"] = ["NAT-B-001"]
        graph["edges"].append({"from": "NAT-B-001", "to": "NAT-A-001"})
    else:
        graph["edges"].pop()
    with pytest.raises(ValueError, match=error):
        select_ready_tasks(registry, graph, {"locks": []})
