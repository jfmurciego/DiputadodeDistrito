#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula la clave estable de un lote")
    parser.add_argument("plan")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    territory = re.sub(r"[^a-z0-9-]+", "-", plan["territory_id"].lower()).strip("-")
    print(f"value={territory}-{plan['plan_sha256'][:12]}")


if __name__ == "__main__":
    main()
