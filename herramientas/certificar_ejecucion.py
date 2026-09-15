#!/usr/bin/env python3
"""Emite una certificación técnica consolidada desde evidencias ya producidas."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PASS_STATUSES = {"PASS", "PASS_WITH_EXCEPTIONS"}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def certify(
    decision: dict,
    status: dict,
    audit: dict,
    manifest: dict,
    validation: dict,
    reconciliation: dict,
    *,
    source_commit: str,
    workflow_run_id: str,
) -> dict:
    errors: list[str] = []
    territory = status.get("territory_id")
    run_id = status.get("run_id")

    if decision.get("decision") != "ADMITTED" or decision.get("production_authorization") != "AUTHORIZED":
        errors.append("CONTRACT_NOT_AUTHORIZED")
    if not territory or decision.get("territory_id") != territory:
        errors.append("TERRITORY_ID_MISMATCH")
    if not run_id or manifest.get("run_id") != run_id or validation.get("run_id") != run_id:
        errors.append("RUN_ID_MISMATCH")
    if status.get("from_stage") != "M01" or status.get("to_stage") != "M08":
        errors.append("INCOMPLETE_STAGE_RANGE")
    if status.get("execution_outcome") != "success" or status.get("decision") not in PASS_STATUSES:
        errors.append("PRODUCTION_NOT_PASSED")
    if validation.get("estado") != "PASS" or validation.get("failures"):
        errors.append("TERRITORIAL_VALIDATION_FAILED")
    if validation.get("expected_districts") != validation.get("districts_found"):
        errors.append("DISTRICT_COUNT_MISMATCH")
    if audit.get("decision") not in PASS_STATUSES:
        errors.append("GEOMETRIC_AUDIT_FAILED")
    if audit.get("blocked_districts") or audit.get("policy_mismatches") or audit.get("contract_blockers"):
        errors.append("UNGOVERNED_GEOMETRIC_BLOCK")
    governed = int(audit.get("governed_exceptions", 0))
    if governed:
        governed_rows = [row for row in audit.get("districts", []) if row.get("status") == "GOVERNED_EXCEPTION"]
        if len(governed_rows) != governed or any(
            not row.get("policy_applied") or not row.get("atomic_multipart_cause_proven")
            for row in governed_rows
        ):
            errors.append("GEOMETRIC_EXCEPTION_NOT_PROVEN")
    if reconciliation.get("status") not in {"PASS", "PASS_WITH_DECLARED_EXCEPTIONS"}:
        errors.append("ELECTORAL_RECONCILIATION_FAILED")
    if reconciliation.get("errors"):
        errors.append("ELECTORAL_RECONCILIATION_ERRORS")
    if reconciliation.get("input_votes") != (
        reconciliation.get("assigned_votes", 0) + reconciliation.get("unassigned_votes", 0)
    ):
        errors.append("ELECTORAL_VOTE_IDENTITY_FAILED")
    outputs = manifest.get("outputs") or {}
    required_suffixes = (
        "_m06_distritos.geojson.zip",
        "_m07_reconciliacion.json",
        "_m08_distritos_resultados.geojson.zip",
    )
    selected_outputs = {
        suffix: next((name for name in outputs if name.endswith(suffix)), None)
        for suffix in required_suffixes
    }
    missing = [suffix for suffix, name in selected_outputs.items() if name is None]
    if missing:
        errors.append("MISSING_REQUIRED_OUTPUTS:" + ",".join(missing))
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        errors.append("INVALID_SOURCE_COMMIT")

    certification = "BLOCKED"
    if not errors:
        certification = "CERTIFIED_WITH_GOVERNED_EXCEPTIONS" if (
            status.get("decision") == "PASS_WITH_EXCEPTIONS"
            or audit.get("decision") == "PASS_WITH_EXCEPTIONS"
            or reconciliation.get("status") == "PASS_WITH_DECLARED_EXCEPTIONS"
        ) else "CERTIFIED"

    return {
        "schema": "ddd.technical-certification/1.0",
        "decision": certification,
        "territory_id": territory,
        "production_run_id": run_id,
        "workflow_run_id": str(workflow_run_id),
        "source_commit": source_commit,
        "contract_sha256": (decision.get("contract") or {}).get("contract_sha256"),
        "stage_range": {"from": status.get("from_stage"), "to": status.get("to_stage")},
        "districts": {
            "expected": validation.get("expected_districts"),
            "observed": validation.get("districts_found"),
            "connected": audit.get("connected_districts"),
            "governed_exceptions": governed,
            "blocked": audit.get("blocked_districts"),
        },
        "electoral_reconciliation": {
            "status": reconciliation.get("status"),
            "input_votes": reconciliation.get("input_votes"),
            "assigned_votes": reconciliation.get("assigned_votes"),
            "unassigned_votes": reconciliation.get("unassigned_votes"),
        },
        "output_sha256": {
            name: outputs[name].get("sha256")
            for name in selected_outputs.values() if name is not None
        },
        "errors": errors,
        "publication": {
            "status": "BLOCKED",
            "reason": "La certificación técnica no sustituye la política P01-P09/G01-G04.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--production-status", type=Path, required=True)
    parser.add_argument("--geometric-audit", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = certify(
        load(args.decision), load(args.production_status), load(args.geometric_audit),
        load(args.manifest), load(args.validation), load(args.reconciliation),
        source_commit=args.source_commit, workflow_run_id=args.workflow_run_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["decision"])
    raise SystemExit(0 if result["decision"] != "BLOCKED" else 1)


if __name__ == "__main__":
    main()
