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
from herramientas.huella_checkpoint_m05 import build_fingerprint
from herramientas.derivar_checkpoint_acumulado import inspect_derivable_checkpoint
from herramientas.estado_produccion import TARGET_MET, population_dimension
from ddd_core.config import load_params_yaml


def _stage_num(stage: str) -> int:
    value=str(stage).strip().upper()
    if not value.startswith("M") or not value[1:].isdigit():
        raise ValueError(f"etapa de checkpoint inválida: {stage}")
    return int(value[1:])


def _validate_m05_compatibility(*, params: Path, state_root: Path, root_dir: Path) -> dict:
    path=state_root / "compatibility" / "m05.json"
    if not path.is_file():
        raise ValueError("checkpoint M05/M06 sin huella de compatibilidad M05")
    stored=json.loads(path.read_text(encoding="utf-8"))
    current=build_fingerprint(params=params,root_dir=root_dir)
    if stored.get("fingerprint") != current.get("fingerprint"):
        raise ValueError(
            "checkpoint incompatible con M05 actual: "
            f"{stored.get('fingerprint') or 'MISSING'} != {current.get('fingerprint')}"
        )
    return {"stored":stored,"current":current}


def _validate_population_certification(*, params: Path, state_root: Path, run_id: str) -> dict:
    cfg = load_params_yaml(str(params))
    m05 = (cfg.get("modulos", {}) or {}).get("modulo_05_optimizar_distritos") or cfg.get("step5_optimize_swaps") or {}
    raw = m05.get("out_report")
    if not raw:
        raise ValueError("M05 no declara out_report; checkpoint no certificable poblacionalmente")
    meta = cfg.get("meta") or {}
    expected = Path(str(raw).format(
        year=meta.get("year"),
        run_name=meta.get("run_name"),
        run_id=run_id,
    )).name
    matches = sorted(state_root.rglob(expected))
    if len(matches) != 1:
        raise ValueError(f"checkpoint sin evidencia M05 unívoca: {expected} ({len(matches)} coincidencias)")
    try:
        report = json.loads(matches[0].read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"evidencia M05 ilegible: {type(exc).__name__}: {exc}") from exc
    if not isinstance(report, dict):
        raise ValueError("evidencia M05 inválida: se esperaba objeto JSON")
    population = population_dimension(report)
    target_required = bool(
        ((cfg.get("validation") or {}).get("require_zero_outside_tolerance_after_m05", False))
    )
    invalid = (
        population.get("population_outcome") != "success"
        or population.get("population_hard_constraints_after") != 0
        or (
            target_required
            and (
                population.get("population_decision") != TARGET_MET
                or population.get("population_outliers_after") != 0
            )
        )
    )
    if invalid:
        raise ValueError(
            "checkpoint poblacionalmente no certificado: "
            f"target_required={target_required}, "
            f"decision={population.get('population_decision')}, "
            f"hard={population.get('population_hard_constraints_after')}, "
            f"outliers={population.get('population_outliers_after')}"
        )
    return {
        "report_path": matches[0].as_posix(),
        "population_target_required": target_required,
        **population,
    }


def evaluate_candidate(*, params: Path, package: Path, run_id: str, stage: str,
                       root_dir: Path = Path("."), state_root: Path | None = None) -> dict:
    try:
        evidence = validate_resume_sources(
            params=params,
            package=package,
            root_dir=root_dir,
        )
        compatibility=None
        population_evidence=None
        derivation=None
        compatibility_error=None
        if _stage_num(stage) >= 5:
            if state_root is None:
                raise ValueError("checkpoint M05/M06 exige estado completo para validar compatibilidad")
            try:
                compatibility=_validate_m05_compatibility(params=params,state_root=state_root,root_dir=root_dir)
            except Exception as exc:
                compatibility_error=str(exc)
                derivation=inspect_derivable_checkpoint(params=params,state_root=state_root,target_stage=4)
            else:
                try:
                    population_evidence=_validate_population_certification(
                        params=params,
                        state_root=state_root,
                        run_id=str(run_id),
                    )
                except Exception as exc:
                    compatibility_error=str(exc)
                    compatibility=None
                    derivation=inspect_derivable_checkpoint(params=params,state_root=state_root,target_stage=4)
    except Exception as exc:
        return {
            "valid": False,
            "run_id": str(run_id),
            "stage": str(stage),
            "reason": str(exc),
        }
    result={
        "valid": True,
        "run_id": str(run_id),
        "stage": str(stage),
        "reason": "checkpoint compatible: fuentes y huella de etapa validadas",
        "source_evidence": evidence,
        "requires_derivation": False,
        "effective_stage": str(stage),
        "from_stage": f"M{_stage_num(stage)+1:02d}",
    }
    if compatibility is not None:
        result["m05_compatibility"]=compatibility
        result["population_evidence"]=population_evidence
        result["reason"]="checkpoint compatible: fuentes, huella M05 y certificación poblacional validadas"
    elif derivation is not None:
        result.update({
            "reason":"checkpoint M05/M06 incompatible con el motor actual; M04 acumulado es reutilizable",
            "requires_derivation":True,
            "effective_stage":"M04",
            "from_stage":"M05",
            "compatibility_error":compatibility_error,
            "derivation":derivation,
        })
    return result


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
            state_root=Path(candidate["state_root"]) if candidate.get("state_root") else None,
        )
        if result["valid"]:
            return {"selected": result, "discarded": discarded, "from_stage": result.get("from_stage") or candidate.get("from_stage")}
        discarded.append(result)
    return {"selected": None, "discarded": discarded, "from_stage": "M01"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True, type=Path)
    ap.add_argument("--package", required=True, type=Path)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--stage", required=True)
    ap.add_argument("--root-dir", default=".", type=Path)
    ap.add_argument("--state-root", type=Path)
    args = ap.parse_args()
    result = evaluate_candidate(
        params=args.params,
        package=args.package,
        run_id=args.run_id,
        stage=args.stage,
        root_dir=args.root_dir,
        state_root=args.state_root,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
