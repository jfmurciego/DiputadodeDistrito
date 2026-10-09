#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    tests_dir = root / "tests"
    failures = []
    for path in sorted(tests_dir.glob("test_*.py")):
        suite = unittest.defaultTestLoader.discover(
            start_dir=str(tests_dir),
            pattern=path.name,
            top_level_dir=str(root),
        )
        count = suite.countTestCases()
        if count == 0:
            failures.append(path.relative_to(root).as_posix())
    if failures:
        print("Ficheros test_*.py sin tests descubribles por unittest:", file=sys.stderr)
        for path in failures:
            print(f" - {path}", file=sys.stderr)
        return 2
    print(f"OK: {len(list(tests_dir.glob('test_*.py')))} ficheros test_*.py aportan al menos un test descubrible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
