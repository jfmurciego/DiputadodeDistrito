#!/usr/bin/env python3
"""Validate M06 catalogues through the single C-10 field contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.m06_schema import VERSION, inspect_catalog


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("catalogs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {
        "schema_version": "1.0.0",
        "contract_version": VERSION,
        "audit_finding": "C-10",
        "catalogs": [inspect_catalog(path) for path in args.catalogs],
        "decision": "CLOSED_SINGLE_SCHEMA_WITH_EXPLICIT_LEGACY_ADAPTER",
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
