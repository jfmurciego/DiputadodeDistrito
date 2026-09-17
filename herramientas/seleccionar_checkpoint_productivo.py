#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Selector productivo de checkpoints reutilizables.

No adquiere ni descarga fuentes oficiales. Valida paquetes ``sources/`` ya
recuperados de checkpoints mediante la misma puerta común de reanudación y
permite seleccionar el candidato más reciente que resulte REUSE.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from herramientas.validar_fuentes_reanudacion import validate_resume_sources


def evaluate_candidate(*, params: Path, package: Path, run_id: str, stage: str,
                       root_dir: Path = Path(".")) -> dict:
    try:
        evidence = validate_resume_sources(
            params=params,
            package=package,
            root_dir=root_dir,
        )
    except Exception as exc:
        return {
            "valid": False,
            "run_id": str(run_id),
            "stage": str(stage),
            "reason": str(exc),
        }
    return {
        "valid": True,
        "run_id": str(run_id),
        "stage": str(stage),
        "reason": "checkpoint compatible: paquete de fuentes validado completamente",
        "source_evidence": evidence,
    }


def select_latest_valid(*, params: Path, candidates: Iterable[dict],
                        root_dir: Path = Path(".")) -> dict:
    """Evalúa candidatos ya ordenados de más reciente a más antiguo."""
    discarded: list[dict] = []
    for candidate in candidates:
        result = evaluate_candidate(
            params=params,
            package=Path(candidate["package"]),
            run_id=str(candidate["run_id"]),
            stage=str(candidate["stage"]),
            root_dir=root_dir,
        )
        if result["valid"]:
            return {"selected": result, "discarded": discarded, "from_stage": candidate.get("from_stage")}
        discarded.append(result)
    return {"selected": None, "discarded": discarded, "from_stage": "M01"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, type=Path)
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--root-dir", default=".", type=Path)
    args = ap.parse_args()
    result = evaluate_candidate(
        params=args.params,
        package=args.package,
        run_id=args.run_id,
        stage=args.stage,
        root_dir=args.root_dir,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
