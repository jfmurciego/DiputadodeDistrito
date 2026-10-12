"""Informe de tres puertas del Congreso. Solo lectura; no ejecuta módulos."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.congreso_readiness import inspect_three_gates

CONTRACT = ROOT / "territorios/congreso/contrato_congreso_2026.json"
PRODUCT = ROOT / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--province", required=True, help="CPRO, por ejemplo 10 o 01")
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--product-dir", type=Path, default=PRODUCT)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = inspect_three_gates(contract, args.product_dir, args.province)
    print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
