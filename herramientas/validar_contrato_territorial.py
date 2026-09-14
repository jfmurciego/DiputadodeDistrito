#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Validador de admisión territorial
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Puerta production-ready M01-M06
FECHA: 2026-09-13
ESTADO: vigente — R034
QUÉ HACE: emite el informe ADMITTED/REJECTED de un contrato sin ejecutar cálculo territorial.
MOTIVO: permitir a G10 y CI detener contratos incompletos antes de abrir la línea de producción.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from ddd_core.territory_contract import validate_production_contract


def main() -> int:
    parser = argparse.ArgumentParser(description="Puerta de admisión M01-M06")
    parser.add_argument("--params", required=True)
    parser.add_argument("--territory")
    parser.add_argument("--output")
    args = parser.parse_args()
    report = validate_production_contract(args.params, expected_territory=args.territory)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if report["status"] == "ADMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())

