#!/usr/bin/env python3
"""DDD plan migration 1.0.0, 2026-10-11, candidate, local isolated copies.

Origin: new module. Preserve old ledger bytes and formal decisions; build an
evidence index without converting experiments, PRs or local reviews to PASS.
The installed plan is changed only by the separately reviewed installer.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile

TABLES = ("work_item", "research_experiment", "code_delivery", "review",
          "github_pr", "workflow_run", "source_receipt", "owner_decision")
FORMAL_STATES = {"PENDING", "RUNNING", "PASS", "FAIL", "BLOCKED", "SKIPPED"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode()


def read_json(path: Path):
    return json.loads(path.read_text())


def fingerprint(path: Path) -> dict:
    return {"path": str(path.resolve()), "sha256": digest(path.read_bytes()),
            "mode": stat.S_IMODE(path.stat().st_mode), "bytes": path.stat().st_size}


def atomic_write(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def parse_ledger(data: bytes) -> list[dict]:
    if data and not data.endswith(b"\n"):
        raise ValueError("LEDGER_TRUNCATED: preserve bytes; owner must reconcile trailing event")
    events = []
    for number, line in enumerate(data.splitlines(), 1):
        if not line.strip():
            raise ValueError(f"LEDGER_INVALID: empty event at {number}")
        try:
            event = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"LEDGER_INVALID: event {number}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"LEDGER_INVALID: event {number} is not an object")
        events.append(event)
    return events


def replay_formal(events: list[dict]) -> dict[str, str]:
    """Read heterogeneous historical events and the compatible snapshot anchor."""
    states = {}
    for event in events:
        if event.get("event") == "PLAN_INDEX_RECONCILIATION":
            states = dict(event["formal_snapshot"])
        changes = event.get("task_changes", [])
        if isinstance(changes, dict):
            changes = [dict(value, id=key) for key, value in changes.items()]
        for change in changes:
            task_id = change.get("task_id", change.get("id"))
            value = change.get("status_after", change.get("after"))
            if isinstance(value, dict):
                value = value.get("status")
            if task_id and value in FORMAL_STATES:
                states[task_id] = value
        task_id = event.get("task_id")
        value = event.get("status_after", event.get("to", event.get("status")))
        if task_id and value in FORMAL_STATES:
            states[task_id] = value
    return states


def validate_catalog(catalog: dict, base: Path) -> dict[str, dict]:
    tasks = catalog.get("tasks", [])
    ids = [task["id"] for task in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("DUPLICATE_ID")
    by_id = {task["id"]: task for task in tasks}
    aliases = set(ids)
    for task in tasks:
        for alias in task.get("aliases", []):
            if alias in aliases:
                raise ValueError(f"ALIAS_COLLISION: {alias}")
            aliases.add(alias)
        for field in ("depends_on", "preparation_dependencies", "acceptance_dependencies",
                      "integration_dependencies", "production_dependencies", "dedup_targets"):
            values = task.get(field, [])
            if len(values) != len(set(values)) or any(value not in by_id for value in values):
                raise ValueError(f"INVALID_DEPENDENCY: {task['id']} {field}")
        prompt = (base / task["prompt_file"]).resolve()
        if not prompt.is_relative_to(base.resolve()) or not prompt.is_file():
            raise ValueError(f"PROMPT_MISSING: {task['id']}")
        if digest(prompt.read_bytes()) != task.get("prompt_sha256"):
            raise ValueError(f"PROMPT_HASH_MISMATCH: {task['id']}")
    for field in ("depends_on", "preparation_dependencies", "acceptance_dependencies",
                  "integration_dependencies", "production_dependencies"):
        visited, active = set(), set()

        def visit(task_id):
            if task_id in active:
                raise ValueError(f"DEPENDENCY_CYCLE: {field} {task_id}")
            if task_id in visited:
                return
            active.add(task_id)
            for parent in by_id[task_id].get(field, []):
                visit(parent)
            active.remove(task_id)
            visited.add(task_id)
        for task_id in by_id:
            visit(task_id)
    return by_id


def build_index(state: dict, catalog: dict, events: list[dict], evidence: dict | None = None) -> dict:
    """Immutable entity/relationship identities are hashes of their provenance."""
    index = {"schema": "ddd.plan-entities/1.0", "tables": {name: [] for name in TABLES},
             "relations": [], "remote_identity": "UNVERIFIED_OFFLINE"}
    seen = set()

    def add(table, payload, provenance):
        body = {"entity_type": table, "data": payload, "provenance": provenance}
        entity_id = table + ":" + digest(canonical(body))
        if entity_id not in seen:
            index["tables"][table].append(dict(body, entity_id=entity_id, sha256=digest(canonical(body))))
            seen.add(entity_id)
            if "ledger_event" in provenance:
                original = events[provenance["ledger_event"]]
                recipients = {original.get("task_id")}
                changes = original.get("task_changes", [])
                if isinstance(changes, dict):
                    recipients.update(changes)
                else:
                    recipients.update(c.get("task_id", c.get("id")) for c in changes)
                for recipient in sorted(r for r in recipients if r in work_ids):
                    relate(work_ids[recipient], entity_id, "has_historical_evidence", provenance)
        return entity_id

    def relate(source, target, relation, provenance):
        body = {"source": source, "target": target, "relation": relation, "provenance": provenance}
        index["relations"].append(dict(body, relation_id=digest(canonical(body))))

    work_ids = {}
    specs = {task["id"]: task for task in catalog["tasks"]}
    for task in state["tasks"]:
        spec = specs[task["id"]]
        work_ids[task["id"]] = add("work_item", {
            "id": task["id"], "formal_status": task["status"],
            "technical_status": task.get("technical_status", "UNRECONCILED"),
            "aliases": spec.get("aliases", []), "origin": spec.get("origin"),
            "date": spec.get("origin_date"), "spec_sha256": spec.get("spec_sha256"),
            "evidence": task.get("evidence", [])}, {"state_task_sha256": digest(canonical(task))})
    for task in catalog["tasks"]:
        for target in task.get("dedup_targets", []):
            relate(work_ids[task["id"]], work_ids[target], "overlaps_initiative",
                   {"spec_sha256": task["spec_sha256"], "does_not_close_target": True})
    for number, event in enumerate(events):
        # The entire historical event stays available; extracting entities must
        # never turn a metadata record into a new formal owner decision.
        provenance = {"ledger_event": number, "event_sha256": digest(canonical(event))}
        if event.get("authority") or "DECISION" in event.get("event", ""):
            add("owner_decision", event, provenance)
        def inspect(value, key=""):
            if isinstance(value, dict):
                if "head_sha" in value or "commit_sha" in value:
                    add("code_delivery", value, provenance)
                if "number" in value and ("pull" in str(value.get("url", "")) or "merged" in value):
                    add("github_pr", dict(value, remote_verification="UNVERIFIED_OFFLINE"), provenance)
                if "run_id" in value or ("id" in value and "conclusion" in value):
                    add("workflow_run", dict(value, remote_verification="UNVERIFIED_OFFLINE"), provenance)
                if "review" in key.lower() or "independent_review" in value:
                    add("review", value, provenance)
                if "receipt" in key.lower() or "receipt" in value:
                    add("source_receipt", value, provenance)
                for child_key, child in value.items():
                    inspect(child, child_key)
            elif isinstance(value, list):
                for child in value:
                    inspect(child, key)
        inspect(event)
    for item in (evidence or {}).get("items", []):
        ref = item.get("file", {})
        path = Path(ref.get("path", ""))
        verified = path.is_file() and digest(path.read_bytes()) == ref.get("sha256")
        if not verified:
            raise ValueError("EVIDENCE_HASH_MISMATCH: " + str(path))
        table = item.get("entity_type", "research_experiment")
        if table not in TABLES or table == "work_item":
            raise ValueError("INVALID_ENTITY_TYPE")
        entity_id = add(table, item, ref)
        for task_id in item.get("work_items", []):
            if task_id not in work_ids:
                raise ValueError("UNKNOWN_EVIDENCE_WORK_ITEM: " + task_id)
            relate(work_ids[task_id], entity_id, "has_evidence", ref)
    index["formal_from_ledger"] = replay_formal(events)
    return index


def migrate(source_plan: Path, catalog_path: Path, output: Path,
            authority_ref: Path | None = None, evidence_manifest: Path | None = None) -> dict:
    source_plan, catalog_path, output = map(lambda p: Path(p).resolve(),
                                           (source_plan, catalog_path, output))
    if output == source_plan or output.is_relative_to(source_plan):
        raise ValueError("ISOLATED_OUTPUT_REQUIRED")
    if authority_ref is None or not Path(authority_ref).is_file():
        raise ValueError("AUTHORITY_REFERENCE_REQUIRED: actual instruction bytes")
    authority = fingerprint(Path(authority_ref))
    catalog = read_json(catalog_path)
    specs = validate_catalog(catalog, catalog_path.parent)
    inputs = {name: fingerprint(source_plan / name)
              for name in ("plan.md", "estado.json", "eventos.jsonl")}
    inputs["catalogo.json"] = fingerprint(catalog_path)
    ledger_bytes = (source_plan / "eventos.jsonl").read_bytes()
    events = parse_ledger(ledger_bytes)
    evidence = read_json(Path(evidence_manifest)) if evidence_manifest else {}
    if evidence_manifest:
        inputs["inventory.json"] = fingerprint(Path(evidence_manifest))
    migration_key = digest(canonical({"inputs": inputs, "authority": authority}))
    manifest_path = output / "migration.json"
    if manifest_path.exists():
        report = read_json(manifest_path)
        if report.get("migration_key") != migration_key:
            raise ValueError("MIGRATION_CONFLICT: output belongs to other input bytes")
        for name, expected in report["outputs"].items():
            if digest((output / name).read_bytes()) != expected["sha256"]:
                raise ValueError("MIGRATION_OUTPUT_TAMPERED: " + name)
        return report
    if output.exists() and any(output.iterdir()):
        raise ValueError("OUTPUT_NOT_EMPTY")
    state = read_json(source_plan / "estado.json")
    tasks = {task["id"]: task for task in state["tasks"]}
    if len(tasks) != len(state["tasks"]) or any(task_id not in specs for task_id in tasks):
        raise ValueError("SOURCE_TASK_ID_CONFLICT")
    if any(task["status"] not in FORMAL_STATES for task in tasks.values()):
        raise ValueError("SOURCE_FORMAL_STATE_INVALID")
    original_pass = sorted(task_id for task_id, task in tasks.items() if task["status"] == "PASS")
    replay = replay_formal(events)
    contradictions = [{"task_id": task_id, "ledger": replay.get(task_id), "state": task["status"]}
                      for task_id, task in tasks.items()
                      if task_id in replay and replay[task_id] != task["status"]]
    for conflict in contradictions:
        if conflict["task_id"] != "F02" or conflict["state"] != "PASS":
            raise ValueError("UNRESOLVED_FORMAL_CONTRADICTION: " + conflict["task_id"])
        decisions = tasks["F02"].get("evidence", [])
        if not any(e.get("closure") == "CLOSED" and e.get("independent_review") == "REVIEW_PASS"
                   and e.get("decision", {}).get("authorization") for e in decisions):
            raise ValueError("F02_FORMAL_DECISION_MISSING")
    now = datetime.now(timezone.utc).isoformat()
    new_events = []
    def event(kind, task_id=None, **fields):
        body = {"schema": "ddd.plan-event/1.1", "event": kind, "at": now,
                "actor": "Codex", "authority_ref": authority,
                "plan_hash": inputs["plan.md"]["sha256"], "migration_key": migration_key,
                "manifest_sha256": inputs.get("inventory.json", inputs["catalogo.json"])["sha256"],
                "evidence_ref": inputs.get("inventory.json", inputs["catalogo.json"]),
                "parent_event_id": new_events[-1]["event_id"] if new_events else digest(ledger_bytes),
                **fields}
        if task_id:
            body["task_id"] = task_id
            body["spec_hash"] = specs[task_id]["spec_sha256"]
        body["event_id"] = digest(canonical(body))
        new_events.append(body)
    for conflict in contradictions:
        task_id = conflict["task_id"]
        event("RECONCILIATION_STATE_LEDGER", task_id, **{"from": conflict["ledger"], "to": conflict["state"]},
              reason="Contemporary reconciliation of already recorded owner closure; no new approval",
              evidence={"state": inputs["estado.json"], "existing_task": tasks[task_id]},
              historical_authority="Stored historical owner decision; not regenerated")
    added = []
    for spec in catalog["tasks"]:
        task_id = spec["id"]
        if task_id not in tasks:
            task = {"id": task_id, "front": spec["front"], "title": spec["title"],
                    "depends_on": spec["depends_on"], "acceptance": spec["acceptance"],
                    "execution": spec["execution"], "status": "PENDING", "evidence": [],
                    "attempts": 0, "blocker": None, "authorization": "owner-scope-required",
                    "technical_status": "EVIDENCE_REVIEW_REQUIRED"}
            task["evidence"] = [{"file": item["file"], "entity_type": item["entity_type"],
                                 "finding": item.get("finding"), "remote_verification": "UNVERIFIED_OFFLINE"}
                                for item in evidence.get("items", []) if task_id in item.get("work_items", [])]
            disposition = evidence.get("work_item_dispositions", {}).get(task_id)
            if disposition:
                if disposition.get("technical_status") not in ("ALREADY_EVIDENCED", "EVIDENCE_REVIEW_REQUIRED", "WAIT_OWNER"):
                    raise ValueError("INVALID_HISTORICAL_DISPOSITION: " + task_id)
                refs = disposition.get("evidence_refs", [])
                if not refs or any(not Path(ref["path"]).is_file() or digest(Path(ref["path"]).read_bytes()) != ref["sha256"] for ref in refs):
                    raise ValueError("HISTORICAL_DISPOSITION_EVIDENCE_MISSING: " + task_id)
                task["technical_status"] = disposition["technical_status"]
                task["historical_disposition"] = disposition
                task["inventory_receipt"] = inputs.get("inventory.json")
            tasks[task_id] = task
            state["tasks"].append(task)
            added.append(task_id)
            event("WORK_ITEM_IMPORTED", task_id, **{"from": None, "to": "PENDING"},
                  reason="Candidate specification, deduplicated through immutable relationships; no closure",
                  origin=spec["origin"], aliases=spec.get("aliases", []),
                  dedup_targets=spec.get("dedup_targets", []),
                  technical_status=task["technical_status"], evidence=task["evidence"],
                  historical_disposition=task.get("historical_disposition"))
    if tasks.get("F04", {}).get("status") == "PENDING":
        tasks["F04"]["technical_status"] = "WAIT_OWNER"
        tasks["F04"]["blocker"] = "Material GO_ACOTADO is not an unequivocal formal F04 closure decision"
        event("FORMAL_DISCREPANCY_DOCUMENTED", "F04", **{"from": "PENDING", "to": "PENDING"},
              reason=tasks["F04"]["blocker"], technical_status="WAIT_OWNER",
              evidence={"state": inputs["estado.json"]})
    snapshot = {task["id"]: task["status"] for task in state["tasks"]}
    event("PLAN_INDEX_RECONCILIATION", formal_snapshot=snapshot,
          reason="Snapshot anchor for old tools; all formal PASS preserved, no imported PASS",
          evidence={"state": inputs["estado.json"], "ledger": inputs["eventos.jsonl"]},
          contradictions=contradictions, unjournalled_initial_states=[task_id for task_id in tasks if task_id not in replay])
    state["plan_revision"] = "1.3.0-candidate"
    state["catalog_file"] = "catalogo.json"
    state["entity_index_file"] = "indice.json"
    state["last_updated_utc"] = now
    state["migration"] = {"migration_key": migration_key, "actor": "Codex", "authority_ref": authority,
                          "original_pass_preserved": original_pass, "source_state": inputs["estado.json"]}
    full_ledger = ledger_bytes + b"".join(canonical(e) + b"\n" for e in new_events)
    index = build_index(state, catalog, events + new_events, evidence)
    if index["formal_from_ledger"] != snapshot:
        raise ValueError("REPLAY_MISMATCH")
    if not full_ledger.startswith(ledger_bytes) or digest(full_ledger[:len(ledger_bytes)]) != digest(ledger_bytes):
        raise ValueError("LEDGER_PREFIX_CHANGED")
    output.mkdir(parents=True, exist_ok=True)
    backup = output.parent / (output.name + "-source-backup-" + migration_key[:12])
    if backup.exists():
        raise ValueError("BACKUP_ALREADY_EXISTS_WITHOUT_MIGRATION")
    backup.mkdir()
    for name in ("plan.md", "estado.json", "eventos.jsonl"):
        shutil.copy2(source_plan / name, backup / name)
    atomic_write(backup / "manifest.json", canonical(inputs) + b"\n")
    atomic_write(output / "estado.json", json.dumps(state, ensure_ascii=False, indent=2).encode()+b"\n",
                 inputs["estado.json"]["mode"])
    atomic_write(output / "eventos.jsonl", full_ledger, inputs["eventos.jsonl"]["mode"])
    suffix = ("\n\n## Índice expandible 1.3.0 (candidato local)\n"
              "Se conservan los IDs, decisiones y eventos anteriores. Catálogo: `catalogo.json`; "
              "entidades/evidencias: `indice.json`. Los estados formales siguen en `estado.json`.\n"
              f"Fichas: {len(tasks)}; nuevas: {len(added)}; PASS anteriores: {len(original_pass)}. "
              "Las fichas nuevas requieren contraste de evidencia y autorización; no son cierres.\n"
              "F02: evento contemporáneo reconcilia cierre preexistente. F04: PENDING / WAIT_OWNER "
              "si no hay decisión formal. F09 preservado; F10 no promovido.\n"
              "Preparación y aceptación tienen grafos distintos en el catálogo. Ninguna dependencia "
              "técnica acredita integración, adquisición, generación o producción.\n").encode()
    atomic_write(output / "plan.md", (source_plan / "plan.md").read_bytes()+suffix, inputs["plan.md"]["mode"])
    shutil.copy2(catalog_path, output / "catalogo.json")
    for spec in catalog["tasks"]:
        target = output / spec["prompt_file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(catalog_path.parent / spec["prompt_file"], target)
    atomic_write(output / "indice.json", json.dumps(index, ensure_ascii=False, indent=2).encode()+b"\n")
    # Before publishing the report, prove no source bytes moved during migration.
    for name in ("plan.md", "estado.json", "eventos.jsonl"):
        if digest((source_plan / name).read_bytes()) != inputs[name]["sha256"]:
            raise ValueError("SOURCE_CHANGED_CONCURRENTLY")
    report = {"schema": "ddd.plan-migration/1.0", "status": "CANDIDATE_COPY_VALIDATED",
              "migration_key": migration_key, "inputs": inputs, "authority_ref": authority,
              "backup": str(backup), "original_tasks": len(tasks)-len(added), "added_tasks": len(added),
              "tasks": len(tasks), "formal_counts": dict(Counter(snapshot.values())),
              "original_pass_preserved": original_pass, "contradictions": contradictions,
              "ledger_prefix_bytes": len(ledger_bytes), "ledger_prefix_sha256": digest(ledger_bytes),
              "original_events": len(events), "new_events": len(new_events),
              "dedup_links": sum(len(t.get("dedup_targets", [])) for t in catalog["tasks"]),
              "source_unchanged": True, "remote_identity": "UNVERIFIED_OFFLINE",
              "outputs": {str(path.relative_to(output)): fingerprint(path)
                          for path in sorted(output.rglob("*")) if path.is_file()}}
    atomic_write(manifest_path, json.dumps(report, ensure_ascii=False, indent=2).encode()+b"\n")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-plan", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--authority-ref", type=Path, required=True)
    parser.add_argument("--evidence", type=Path)
    args = parser.parse_args(argv)
    try:
        report = migrate(args.source_plan, args.catalog, args.output, args.authority_ref, args.evidence)
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({"status": "NO_READY", "cause": str(exc)}))
        return 2
    print(json.dumps({key: report[key] for key in ("status", "tasks", "formal_counts", "new_events",
                                                "ledger_prefix_sha256", "backup")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
