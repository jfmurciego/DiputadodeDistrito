#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta la matriz de perfiles para GitHub Actions")
    parser.add_argument("plan")
    args = parser.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    matrix = {"include": [{"profile": shard["profile"]} for shard in plan["shards"]]}
    print("value=" + json.dumps(matrix, separators=(",", ":")))


if __name__ == "__main__":
    main()
