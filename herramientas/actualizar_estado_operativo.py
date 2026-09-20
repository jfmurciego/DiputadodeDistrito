#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from herramientas.estado_operativo import write_state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--edition", default="2025")
    ap.add_argument("--canonical", type=Path, default=Path("publicado/estado_operativo.json"))
    ap.add_argument("--dashboard", type=Path, default=Path("publicado/dashboard/status.json"))
    ap.add_argument("--readme", type=Path, default=Path("README.md"))
    ap.add_argument("--sin-canonical", action="store_true")
    ap.add_argument("--sin-dashboard", action="store_true")
    ap.add_argument("--sin-readme", action="store_true")
    args = ap.parse_args()

    payload = write_state(
        root=args.root_dir,
        edition=args.edition,
        canonical_path=None if args.sin_canonical else args.canonical,
        dashboard_path=None if args.sin_dashboard else args.dashboard,
        readme_path=None if args.sin_readme else args.readme,
    )
    print(json.dumps({
        "schema": payload["schema"],
        "edition": payload["edition"],
        "complete": payload["kpis"]["complete"],
        "validated": payload["kpis"]["validated"],
        "latest_complete": payload["latest_complete"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
