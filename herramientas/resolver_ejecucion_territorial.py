#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Resolutor universal de ejecución territorial
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Resolución con autorización explícita
FECHA: 2026-09-15
ESTADO: vigente — R038
QUÉ HACE: transforma un YAML admitido en una decisión neutral e incluye su autorización independiente de producción.
CAMBIOS: propaga production_authorization y production_authorized al workflow modular.
MOTIVO: permitir verificar contratos bloqueados sin permitir su ejecución accidental.
ANTERIOR: legacy/herramientas/resolver_ejecucion_territorial_v1.1.0.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml
from ddd_core.territory_contract import validate_production_contract


def relative_to_root(path: str, root: Path) -> str:
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"Ruta fuera del repositorio: {resolved}") from exc


def resolve(params_path: str, run_id: str | None = None) -> dict:
    if run_id:
        os.environ["DDD_RUN_ID"] = run_id
    params = Path(params_path).resolve()
    try:
        params_rel = params.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ValueError("El contrato debe estar dentro del repositorio") from exc
    report = validate_production_contract(params)
    cfg = load_params_yaml(str(params))
    meta = cfg["meta"]
    cache = ((cfg.get("io") or {}).get("cache") or {}).get("dir")
    runs = ((cfg.get("io") or {}).get("runs") or {}).get("dir")
    if not cache or not runs:
        raise ValueError("El contrato admitido debe declarar io.cache.dir e io.runs.dir")
    return {
        "schema_version": "1.0.0",
        "decision": "ADMITTED" if report["status"] == "ADMITTED" else "REJECTED",
        "production_authorization": report.get("production_authorization"),
        "production_authorized": bool(report.get("production_authorized")),
        "contract": report,
        "territory_id": meta["territory_id"],
        "run_name": meta["run_name"],
        "params": params_rel,
        "cache_dir": relative_to_root(cache, ROOT),
        "runs_dir": relative_to_root(runs, ROOT),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolver contrato DDD para ejecución común")
    parser.add_argument("--params", required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = resolve(args.params, args.run_id)
    except Exception as exc:
        result = {"schema_version": "1.0.0", "decision": "REJECTED", "errors": [str(exc)]}
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result["decision"] == "ADMITTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
