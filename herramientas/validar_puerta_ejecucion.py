#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from herramientas.seleccionar_paquete_fuentes import validate_prepared_package
from herramientas.validar_paquete_electoral import validate_package as validate_electoral_package

PASS_DECISIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}
ELECTORAL_SOURCE_DECISIONS = {"REUSE", "ACQUIRE"}


def _read_json(path: Path | None) -> dict:
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _first(root: Path | None, name: str) -> Path | None:
    if root is None or not root.exists():
        return None
    rows = sorted(root.rglob(name))
    return rows[0] if rows else None


def _normalise_digest(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return raw.removeprefix("sha256:").lower()


def _artifact_name_is_consistent(phase: str, territory_id: str, edition: str, run_id: str, artifact_name: str) -> bool:
    if phase == "territorial_source":
        return artifact_name == f"ddd-source-package-{territory_id}-{edition}-{run_id}"
    if phase == "electoral_source":
        return artifact_name == f"ddd-electoral-package-{territory_id}-{edition}-{run_id}"
    if phase == "territorial_product":
        return artifact_name == f"ddd-state-{run_id}-M06"
    if phase == "electoral_product":
        return artifact_name == f"ddd-state-{run_id}-M08"
    return False


def _completed_stage(artifact_root: Path) -> int | None:
    chain = _read_json(_first(artifact_root, "CHAIN_STATE.json"))
    try:
        return int(chain.get("completed_stage"))
    except (TypeError, ValueError):
        return None


def validate_gate(
    *,
    phase: str,
    artifact_root: Path,
    territory_id: str,
    edition: str,
    run_id: str,
    artifact_name: str,
    artifact_digest: str,
    expected_digest: str | None = None,
    audit_root: Path | None = None,
    params: Path | None = None,
    root_dir: Path = Path("."),
) -> dict:
    reasons: list[str] = []
    phase_decision: str | None = None

    if not str(run_id).isdigit():
        reasons.append("RUN_ID_INVALIDO")
    if not artifact_name:
        reasons.append("ARTEFACTO_SIN_NOMBRE")
    elif str(run_id).isdigit() and not _artifact_name_is_consistent(phase, territory_id, str(edition), str(run_id), artifact_name):
        reasons.append("NOMBRE_ARTEFACTO_NO_COINCIDE_CON_RUN")
    actual_digest = _normalise_digest(artifact_digest)
    expected = _normalise_digest(expected_digest)
    if actual_digest is None or not re.fullmatch(r"[0-9a-f]{64}", actual_digest):
        reasons.append("DIGEST_ARTEFACTO_INVALIDO")
    if expected and actual_digest and expected != actual_digest:
        reasons.append("DIGEST_NO_COINCIDE_CON_EVIDENCIA_DURABLE")
    if not artifact_root.exists() or not any(p.is_file() for p in artifact_root.rglob("*")):
        reasons.append("ARTEFACTO_VACIO_O_AUSENTE")

    if not reasons and phase == "territorial_source":
        valid, validation_reasons = validate_prepared_package(
            artifact_root, territory_id=territory_id, edition=edition
        )
        if not valid:
            reasons.extend(f"PAQUETE_TERRITORIAL:{reason}" for reason in validation_reasons)
        else:
            phase_decision = "READY"

    elif not reasons and phase == "electoral_source":
        if params is None or not params.is_file():
            reasons.append("CONTRATO_TERRITORIAL_AUSENTE")
        else:
            try:
                validation = validate_electoral_package(
                    package=artifact_root, params=params, territory_id=territory_id,
                    edition=str(edition), root=root_dir, materialize=False,
                )
                manifest = _read_json(_first(artifact_root, "manifest.json"))
                phase_decision = str(manifest.get("decision") or "")
                if phase_decision not in ELECTORAL_SOURCE_DECISIONS:
                    reasons.append("DECISION_ELECTORAL_NO_ADMITIDA")
                if validation.get("decision") != "READY_PACKAGE":
                    reasons.append("PAQUETE_ELECTORAL_NO_VALIDADO")
            except Exception as exc:
                reasons.append(f"PAQUETE_ELECTORAL:{exc}")

    elif not reasons and phase in {"territorial_product", "electoral_product"}:
        if params is None or not params.is_file():
            reasons.append("CONTRATO_TERRITORIAL_AUSENTE")
        else:
            try:
                cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
                contract_edition = str((cfg.get("meta") or {}).get("year") or "")
                if contract_edition != str(edition):
                    reasons.append("EDICION_CONTRATO_NO_COINCIDE")
            except Exception as exc:
                reasons.append(f"CONTRATO_TERRITORIAL_INVALIDO:{exc}")
        for directory in ("cache", "run", "sources"):
            if not (artifact_root / directory).is_dir():
                reasons.append(f"ESTADO_SIN_{directory.upper()}")
        expected_stage = 6 if phase == "territorial_product" else 8
        completed = _completed_stage(artifact_root)
        if completed is None or completed < expected_stage:
            reasons.append(f"ESTADO_NO_ALCANZA_M{expected_stage:02d}")
        status = _read_json(_first(audit_root or artifact_root, "production_status.json"))
        if not status:
            reasons.append("PRODUCTION_STATUS_AUSENTE")
        else:
            certified = str(status.get("territory_id") or "")
            if certified != territory_id:
                reasons.append("TERRITORIO_CERTIFICADO_NO_COINCIDE")
            phase_decision = str(status.get("decision") or "")
            if phase_decision not in PASS_DECISIONS:
                reasons.append("PRODUCTO_NO_CERTIFICADO")
            scope = str(status.get("scope_through_stage") or "")
            if phase == "territorial_product" and scope and scope != "M06":
                reasons.append("ETAPA_CERTIFICADA_NO_COINCIDE")
            if phase == "electoral_product":
                electoral_application = status.get("electoral_application")
                if electoral_application is False:
                    reasons.append("INCORPORACION_ELECTORAL_RECHAZADA")
                elif electoral_application is not True and expected is None:
                    reasons.append("INCORPORACION_ELECTORAL_NO_ACREDITADA")

    decision = "VALIDADO" if not reasons else "BLOQUEADO"
    return {
        "schema": "ddd.puerta-validacion/1.0",
        "phase": phase,
        "decision": decision,
        "phase_decision": phase_decision,
        "territory_id": territory_id,
        "edition": str(edition),
        "run_id": int(run_id) if str(run_id).isdigit() else None,
        "artifact_name": artifact_name or None,
        "artifact_digest": f"sha256:{actual_digest}" if actual_digest else None,
        "expected_digest": f"sha256:{expected}" if expected else None,
        "reasons": reasons,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=("territorial_source", "territorial_product", "electoral_source", "electoral_product"), required=True)
    ap.add_argument("--artifact-root", type=Path, required=True)
    ap.add_argument("--audit-root", type=Path)
    ap.add_argument("--params", type=Path)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--artifact-name", required=True)
    ap.add_argument("--artifact-digest", required=True)
    ap.add_argument("--expected-digest")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    payload = validate_gate(
        phase=args.phase,
        artifact_root=args.artifact_root,
        audit_root=args.audit_root,
        params=args.params,
        root_dir=args.root_dir,
        territory_id=args.territory_id,
        edition=args.edition,
        run_id=args.run_id,
        artifact_name=args.artifact_name,
        artifact_digest=args.artifact_digest,
        expected_digest=args.expected_digest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["decision"] == "VALIDADO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
