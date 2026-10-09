#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def resolve_persist_state(requested: str | bool | None) -> bool:
    """Ausente en workflow_dispatch => persistencia obligatoria; workflow_call conserva bool explícito."""
    if isinstance(requested, bool):
        return requested
    raw = str(requested if requested is not None else "").strip().lower()
    if raw in {"", "null", "none"}:
        return True
    if raw in {"true", "1", "yes"}:
        return True
    if raw in {"false", "0", "no"}:
        return False
    raise ValueError(f"persist_state inválido: {requested!r}")


def terminal_decision(*, preparation_result: str, registration_result: str, persist_state: bool) -> dict:
    if preparation_result != "success":
        return {"status": "FAILURE", "reason": f"PREPARATION_{preparation_result.upper()}"}
    if persist_state:
        if registration_result != "success":
            return {"status": "FAILURE", "reason": f"REGISTRATION_{registration_result.upper()}"}
        return {"status": "SUCCESS", "reason": "REGISTERED"}
    if registration_result not in {"skipped", "success"}:
        return {"status": "FAILURE", "reason": f"UNEXPECTED_REGISTRATION_{registration_result.upper()}"}
    return {"status": "SUCCESS", "reason": "PERSISTENCE_NOT_REQUIRED"}


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("resolve")
    r.add_argument("--requested", default="")
    t = sub.add_parser("terminal")
    t.add_argument("--preparation-result", required=True)
    t.add_argument("--registration-result", required=True)
    t.add_argument("--persist-state", required=True)
    args = ap.parse_args()

    if args.command == "resolve":
        result = {"persist_state": resolve_persist_state(args.requested)}
    else:
        result = terminal_decision(
            preparation_result=args.preparation_result,
            registration_result=args.registration_result,
            persist_state=resolve_persist_state(args.persist_state),
        )
    print(json.dumps(result))
    return 0 if result.get("status", "SUCCESS") == "SUCCESS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
