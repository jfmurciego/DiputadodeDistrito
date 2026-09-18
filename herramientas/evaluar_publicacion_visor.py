#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evalúa la identidad entre una ejecución territorial y lo publicado en el visor.

No usa logs ni catálogo histórico como prueba de una ejecución concreta. La identidad
sale de production_status.json y del registro estructurado viewer-results.json.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

PRODUCTION_KINDS = {"canonical_m06", "canonical_m08"}
RUN_RE = re.compile(r"^production-(\d+)-(\d+)$")


def _read_json(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _first(root: Path | None, name: str) -> Path | None:
    if root is None or not root.exists():
        return None
    found = sorted(root.rglob(name))
    return found[0] if found else None


def generated_identity(production_root: Path | None) -> tuple[str | None, str | None, str | None]:
    status_path = _first(production_root, "production_status.json")
    status = _read_json(status_path)
    raw_run = status.get("run_id")
    workflow_run = status.get("workflow_run_id")
    if workflow_run is None and isinstance(raw_run, str):
        match = RUN_RE.match(raw_run)
        if match:
            workflow_run = match.group(1)
    territory = status.get("territory_id")
    return (
        str(workflow_run) if workflow_run not in (None, "") else None,
        str(raw_run) if raw_run not in (None, "") else None,
        str(territory) if territory not in (None, "") else None,
    )


def evaluate_publication(
    *,
    requested_run_id: str | None,
    production_root: Path | None = None,
    registry_path: Path | None = None,
    viewer_url: str | None = None,
    deployment_outcome: str | None = None,
    phase: str = "prepared",
) -> dict:
    requested = str(requested_run_id or "").strip() or None
    generated_run, generated_internal_run, generated_territory = generated_identity(production_root)
    registry = _read_json(registry_path)
    results = registry.get("results") if isinstance(registry.get("results"), list) else []
    production_results = [row for row in results if isinstance(row, dict) and row.get("kind") in PRODUCTION_KINDS]
    historical_results = [row for row in results if isinstance(row, dict) and row.get("kind") == "static"]

    reasons: list[str] = []
    matching: list[dict[str, Any]] = []
    if requested:
        if generated_run is None:
            reasons.append("EXECUCION_SOLICITADA_SIN_EVIDENCIA_GENERADA")
        elif generated_run != requested:
            reasons.append("IDENTIFICADOR_EJECUCION_GENERADA_NO_COINCIDE")
        matching = [row for row in production_results if str(row.get("run_id") or "") == requested]
        if phase in {"prepared", "final"} and not matching:
            reasons.append("EJECUCION_SOLICITADA_NO_CARGADA_EN_VISOR")
    else:
        reasons.append("VISOR_SOLO_HISTORICO_SIN_EJECUCION_SOLICITADA")

    loaded_ids = sorted({str(row.get("run_id")) for row in matching if row.get("run_id") not in (None, "")})
    territories = sorted({str(row.get("territory_id")) for row in matching if row.get("territory_id") not in (None, "")})
    loaded_run = loaded_ids[0] if len(loaded_ids) == 1 else None
    territory = territories[0] if len(territories) == 1 else generated_territory
    if requested and len(loaded_ids) > 1:
        reasons.append("VARIAS_EJECUCIONES_CARGADAS_COMO_RESULTADO_SOLICITADO")
    if requested and len(territories) > 1:
        reasons.append("VARIOS_TERRITORIOS_CARGADOS_PARA_LA_MISMA_EJECUCION")
    if requested and generated_territory and territories and generated_territory not in territories:
        reasons.append("TERRITORIO_PUBLICADO_NO_COINCIDE_CON_GENERADO")

    new_maps = sorted({str(row.get("viewer_path")) for row in matching if row.get("viewer_path")})
    same_execution = bool(
        requested
        and generated_run == requested
        and loaded_run == requested
        and len(territories) == 1
        and (not generated_territory or generated_territory == territories[0])
    )

    if phase == "source":
        ready = bool(requested and generated_run == requested and not reasons)
        status = "READY" if ready else "BLOCK"
    elif phase == "prepared":
        ready = same_execution and not reasons
        status = "READY" if ready else "BLOCK"
    elif phase == "final":
        if same_execution and deployment_outcome != "success":
            reasons.append("DESPLIEGUE_VISOR_NO_COMPLETADO")
        if same_execution and not viewer_url:
            reasons.append("VISOR_SIN_ENLACE_PUBLICADO")
        if same_execution and not new_maps:
            reasons.append("EJECUCION_PUBLICADA_SIN_MAPAS_NUEVOS")
        ready = bool(
            same_execution
            and deployment_outcome == "success"
            and viewer_url
            and len(new_maps) > 0
            and not reasons
        )
        status = "SUCCESS" if ready else "BLOCK"
    else:
        raise ValueError(f"Fase desconocida: {phase}")

    return {
        "schema": "ddd-publication-evidence/2.1",
        "status": status,
        "deployment_status": status,
        "phase": phase,
        "requested_run_id": requested,
        "generated_run_id": generated_run,
        "generated_internal_run_id": generated_internal_run,
        "loaded_run_id": loaded_run,
        "territory_id": territory,
        "new_map_count": len(new_maps),
        "new_maps": new_maps,
        "historical_result_count": len(historical_results),
        "historical_only": requested is None,
        "same_execution": same_execution,
        "viewer_url": viewer_url or None,
        "deployment_outcome": deployment_outcome or None,
        "reasons": list(dict.fromkeys(reasons)),
        "source": "workflow_evidence",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requested-run-id", default="")
    parser.add_argument("--production-root", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--viewer-url", default="")
    parser.add_argument("--deployment-outcome", default="")
    parser.add_argument("--phase", choices=("source", "prepared", "final"), default="prepared")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict-request", action="store_true")
    args = parser.parse_args()

    payload = evaluate_publication(
        requested_run_id=args.requested_run_id,
        production_root=args.production_root,
        registry_path=args.registry,
        viewer_url=args.viewer_url or None,
        deployment_outcome=args.deployment_outcome or None,
        phase=args.phase,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.strict_request and args.requested_run_id and payload["status"] == "BLOCK":
        raise SystemExit("Publicación bloqueada: " + "; ".join(payload["reasons"]))


if __name__ == "__main__":
    main()
