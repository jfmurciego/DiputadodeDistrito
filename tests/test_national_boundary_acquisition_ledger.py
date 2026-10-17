import csv
import json
import re
from pathlib import Path

from ddd_core.national_campaign_planner import select_ready_tasks


ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013"


def _read(name):
    return json.loads((CAMPAIGN / name).read_text(encoding="utf-8"))


def test_boundary_acquisition_gate_and_province_dependencies():
    registry = _read("TASK_REGISTRY.json")
    tasks = {task["id"]: task for task in registry["tasks"]}
    rollup = tasks["NAT-C-002"]
    catalog = tasks["NAT-C-055"]
    receipt = tasks["NAT-C-056"]

    assert rollup["status"] == "BLOCKED_DEPENDENCY"
    assert set(rollup["dependencies"]) == {f"NAT-C-{n:03d}" for n in range(3, 55)}
    assert catalog["status"] == "INTEGRATED"
    assert catalog["dependencies"] == []
    assert catalog["commit"] == "edcc767c77fb1e0f552c3316d3d4042bd63680db"
    assert catalog["review"]["verdict"] == "REVIEW_PASS_WITH_SCOPE_LIMITS"
    assert receipt["status"] == "READY"
    assert receipt["dependencies"] == ["NAT-C-055"]
    assert receipt["permissions_required"] == []

    province_tasks = [tasks[f"NAT-C-{number:03d}"] for number in range(3, 55)]
    assert len(province_tasks) == 52
    assert {re.search(r"CPRO=(\d{2})", task["objective"]).group(1)
            for task in province_tasks} == {
        f"{number:02d}" for number in range(1, 53)
    }
    assert all(task["status"] == "BLOCKED_DEPENDENCY" for task in province_tasks)
    assert all(set(task["dependencies"]) == {"NAT-C-001", "NAT-C-056"}
               for task in province_tasks)
    assert len({task["files_affected"][0] for task in province_tasks}) == 52
    assert set(rollup["dependencies"]) == {task["id"] for task in province_tasks}

    graph = _read("DEPENDENCIES.json")
    locks = _read("RESOURCE_LOCKS.json")
    selection = _read("READY_SELECTION.json")
    assert select_ready_tasks(registry, graph, locks) == selection
    projected = {(edge["from"], edge["to"]) for edge in graph["edges"]}
    assert projected == {
        (dependency, task["id"])
        for task in registry["tasks"]
        for dependency in task["dependencies"]
    }
    assert ("NAT-C-002", "NAT-C-003") not in projected


def test_boundary_acquisition_dossier_does_not_claim_source_accreditation():
    dossier = (CAMPAIGN / "ADQUISICION_FUENTE_LIMITE_CNIG.md").read_text(encoding="utf-8")
    assert "no descargado; no acreditado" in dossier
    assert "2026-08-10" in dossier
    assert "2025-01-01" in dossier
    assert "source_download=true" in dossier

    with (CAMPAIGN / "AUDITORIA_BLOQUEOS_C_003_056.csv").open(
        newline="", encoding="utf-8"
    ) as stream:
        rows = list(csv.DictReader(stream))
    province_rows = [row for row in rows if row["task_id"].startswith("NAT-C-")
                     and row["task_id"] not in {"NAT-C-002", "NAT-C-055", "NAT-C-056"}]
    assert len(province_rows) == 52
    assert len({row["cpro"] for row in province_rows}) == 52
    assert {row["cpro"] for row in province_rows} == {f"{n:02d}" for n in range(1, 53)}
    assert {row["required_source"] for row in province_rows} == {
        "Same shared CNIG/IGN BDLJE/RCC source receipt"
    }
    assert all("No local candidate package bytes/hash" in row["local_source_bytes_or_sha"]
               for row in province_rows)


def test_publication_and_production_gates_remain_closed():
    manifest = _read("CAMPAIGN_MANIFEST.json")
    selection = _read("READY_SELECTION.json")
    assert "K=407" in manifest["owner_decisions_preserved"]
    assert "generation_authorized=false" in manifest["owner_decisions_preserved"]
    assert manifest["permissions"]["source_download"] is True
    assert manifest["source_acquisition_authorization"]["receipt_verified"] is False
    assert manifest["permissions"]["production_generation"] is False
    assert selection["ready_task_ids"] == ["NAT-C-056"]
    assert selection["execution_started"] is False
    assert selection["generation_authorized"] is False
    blockers = _read("BLOCKER_REGISTRY.json")["blockers"]
    assert all("NAT-C-056" not in blocker["tasks"] for blocker in blockers)
    resolved = _read("BLOCKER_REGISTRY.json")["resolved_blockers"]
    assert any(item["id"] == "NAT-BLK-CNIG-RECEIPT" for item in resolved)
    assert any(item["id"] == "NAT-BLK-PUBLICATION" for item in resolved)


# Bridge function-style regressions into the repository's unittest CI.
def load_tests(loader, tests, pattern):
    import unittest

    suite = unittest.TestSuite()
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            suite.addTest(unittest.FunctionTestCase(fn, description=name))
    return suite
