#!/usr/bin/env python3
"""CLI de control del Marco G10."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from g10.core import aggregate_summaries, atomic_write_json, classify_failure, compute_fingerprint, validate_plan


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Orquestación reproducible G10")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate-plan")
    validate.add_argument("--plan", required=True)
    matrix = sub.add_parser("matrix")
    matrix.add_argument("--plan", required=True)
    fingerprint = sub.add_parser("fingerprint")
    fingerprint.add_argument("--root", default=".")
    fingerprint.add_argument("--context", default="{}")
    fingerprint.add_argument("paths", nargs="+")
    classify = sub.add_parser("classify")
    classify.add_argument("--exit-code", type=int, required=True)
    classify.add_argument("--log", required=True)
    classify.add_argument("--stage")
    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--output", required=True)
    aggregate.add_argument("summaries", nargs="+")
    args = parser.parse_args()

    if args.command == "validate-plan":
        plan = read_json(args.plan); validate_plan(plan)
        print(f"G10 PLAN PASS: {plan['lot_id']} tasks={len(plan['tasks'])}")
    elif args.command == "matrix":
        plan = read_json(args.plan); validate_plan(plan)
        include = [{"task_id": t["task_id"], "territory": t["territory"],
                    "action": t["action"], "config": t.get("config", ""),
                    "timeout_minutes": t["timeout_minutes"]} for t in plan["tasks"]]
        print(json.dumps({"include": include}, separators=(",", ":")))
    elif args.command == "fingerprint":
        print(compute_fingerprint(args.paths, context=json.loads(args.context), root=args.root))
    elif args.command == "classify":
        log = Path(args.log).read_text(encoding="utf-8", errors="replace")
        failure = classify_failure(exit_code=args.exit_code, log=log, failed_stage=args.stage)
        print("SUCCESS" if failure is None else failure.value)
    elif args.command == "aggregate":
        summaries = [read_json(x) for x in args.summaries]
        result = aggregate_summaries(summaries); atomic_write_json(args.output, result)
        print(json.dumps(result["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
