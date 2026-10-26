#!/usr/bin/env python3
"""Valida que un M05 GerryChain 50 materializó 50 candidatos distintos."""
# PROYECTO: Diputado de Distrito
# VERSIÓN: 1.0.0
# NOMBRE DE VERSIÓN: Validación estricta de portfolio GerryChain 50
# FECHA: 2026-10-25
# ESTADO: candidato
# CAMBIOS: contrasta el informe M05 y los SHA de los 50 artefactos del portfolio.
# MOTIVO: impedir que M05 SUCCESS represente un portfolio incompleto o duplicado.
# ANTERIOR: herramienta nueva; predecesor histórico no recuperado.
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


class PortfolioValidationError(ValueError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_portfolio(report_path: Path) -> dict[str, Any]:
    report_path = report_path.resolve()
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PortfolioValidationError(f"M05_REPORT_UNREADABLE: {report_path}: {exc}") from exc
    portfolio = report.get("portfolio") if isinstance(report, dict) else None
    if not isinstance(portfolio, dict):
        raise PortfolioValidationError("M05_PORTFOLIO_MISSING")
    rows = portfolio.get("candidates")
    if not isinstance(rows, list) or len(rows) != 50 or portfolio.get("candidate_count") != 50:
        raise PortfolioValidationError("GERRYCHAIN50_CANDIDATE_COUNT_NOT_50")
    hashes = [row.get("assignment_hash") for row in rows if isinstance(row, dict)]
    if len(hashes) != 50 or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in hashes):
        raise PortfolioValidationError("GERRYCHAIN50_ASSIGNMENT_HASH_MISSING_OR_INVALID")
    if len(set(hashes)) != 50 or portfolio.get("unique_candidate_count") != 50:
        raise PortfolioValidationError("GERRYCHAIN50_ASSIGNMENT_HASHES_NOT_UNIQUE")
    selected = [row for row in rows if row.get("selected") is True]
    selected_hash = (portfolio.get("selected_assignment_hash") or report.get("selected_assignment_hash")
                     or (report.get("search") or {}).get("selected_assignment_hash"))
    if len(selected) != 1 or selected[0].get("assignment_hash") != selected_hash:
        raise PortfolioValidationError("GERRYCHAIN50_SELECTED_CANDIDATE_MISMATCH")
    for index, row in enumerate(rows, start=1):
        raw = row.get("geojson")
        expected = row.get("sha256")
        if not isinstance(raw, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise PortfolioValidationError(f"GERRYCHAIN50_CANDIDATE_{index:03d}_IDENTITY_MISSING")
        artifact = Path(raw)
        if not artifact.is_absolute():
            artifact = (report_path.parent / artifact).resolve()
        if not artifact.is_file() or _sha256(artifact) != expected:
            raise PortfolioValidationError(f"GERRYCHAIN50_CANDIDATE_{index:03d}_ARTIFACT_SHA_MISMATCH")
    return {
        "candidate_count": 50,
        "unique_candidate_hash_count": 50,
        "selected_assignment_hash": selected_hash,
        "report_path": str(report_path),
    }


def report_path_from_contract(params_path: Path, run_id: str) -> Path:
    from ddd_core.m05_gerrychain_strategy import resolve_paths

    params_path = params_path.resolve()
    config = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
    return resolve_paths(config, params_path, run_id)["report"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--params", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    path = report_path_from_contract(args.params, args.run_id)
    result = validate_portfolio(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
