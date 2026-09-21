from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def phase(
    name: str,
    result: str,
    executed: bool,
    run_id: str | None = None,
    artifact: str | None = None,
    digest: str | None = None,
    validation_decision: str | None = None,
    phase_decision: str | None = None,
) -> dict:
    return {
        "name": name,
        "executed": executed,
        "result": result,
        "run_id": int(run_id) if run_id and str(run_id).isdigit() else None,
        "artifact": artifact or None,
        "artifact_digest": digest or None,
        "validation_decision": validation_decision or None,
        "phase_decision": phase_decision or None,
    }


def optimization_lineage(
    requested: str,
    *,
    generate_executed: bool,
    evidence_path: str | None,
) -> dict:
    if not generate_executed:
        return {
            "optimization_algorithm": requested,
            "optimization_algorithm_requested": requested,
            "optimization_algorithm_effective": None,
            "optimization_fallback": False,
            "optimization_fallback_reason": None,
            "optimization_evidence_status": "REUSED_EXISTING_PRODUCT",
        }
    if not evidence_path:
        raise ValueError("La generación ejecutada debe aportar evidencia de optimización efectiva")
    path = Path(evidence_path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe evidencia de optimización: {path}")
    evidence = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(evidence, dict):
        raise ValueError("La evidencia de optimización debe ser un objeto JSON")
    if evidence.get("requested_algorithm") not in (None, requested):
        raise ValueError(
            "La evidencia de optimización no coincide con la estrategia solicitada: "
            f"{evidence.get('requested_algorithm')} != {requested}"
        )
    effective = evidence.get("effective_algorithm")
    if not effective:
        raise ValueError("La evidencia de optimización no declara effective_algorithm")
    return {
        "optimization_algorithm": requested,
        "optimization_algorithm_requested": requested,
        "optimization_algorithm_effective": effective,
        "optimization_fallback": bool(evidence.get("fallback", False)),
        "optimization_fallback_reason": evidence.get("fallback_reason"),
        "optimization_evidence_status": "VALID",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--territory-name", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--execution-mode", required=True)
    ap.add_argument("--optimization-algorithm", required=True)
    ap.add_argument("--optimization-evidence")
    ap.add_argument("--workflow-run-id", required=True)
    ap.add_argument("--source-sha", required=True)
    ap.add_argument("--publish-requested", choices=["true", "false"], required=True)
    ap.add_argument("--prepare-territorial-result", required=True)
    ap.add_argument("--generate-result", required=True)
    ap.add_argument("--prepare-electoral-result", required=True)
    ap.add_argument("--incorporate-result", required=True)
    ap.add_argument("--publish-result", required=True)
    ap.add_argument("--prepare-territorial-executed", choices=["true", "false"], required=True)
    ap.add_argument("--generate-executed", choices=["true", "false"], required=True)
    ap.add_argument("--prepare-electoral-executed", choices=["true", "false"], required=True)
    ap.add_argument("--incorporate-executed", choices=["true", "false"], required=True)
    ap.add_argument("--territorial-source-run-id")
    ap.add_argument("--territorial-product-run-id")
    ap.add_argument("--electoral-source-run-id")
    ap.add_argument("--electoral-product-run-id")
    ap.add_argument("--territorial-source-artifact")
    ap.add_argument("--territorial-product-artifact")
    ap.add_argument("--electoral-source-artifact")
    ap.add_argument("--electoral-product-artifact")
    ap.add_argument("--territorial-source-digest")
    ap.add_argument("--territorial-product-digest")
    ap.add_argument("--electoral-source-digest")
    ap.add_argument("--electoral-product-digest")
    ap.add_argument("--territorial-source-validation")
    ap.add_argument("--territorial-product-validation")
    ap.add_argument("--electoral-source-validation")
    ap.add_argument("--electoral-product-validation")
    ap.add_argument("--territorial-source-phase-decision")
    ap.add_argument("--territorial-product-phase-decision")
    ap.add_argument("--electoral-source-phase-decision")
    ap.add_argument("--electoral-product-phase-decision")
    ap.add_argument("--output", required=True)
    ns = ap.parse_args()

    def b(v: str) -> bool:
        return v == "true"

    phases = [
        phase("01 · Preparación de Datos Territoriales", ns.prepare_territorial_result, b(ns.prepare_territorial_executed), ns.territorial_source_run_id, ns.territorial_source_artifact, ns.territorial_source_digest, ns.territorial_source_validation, ns.territorial_source_phase_decision),
        phase("02 · Generación de Distritos Autonómicos", ns.generate_result, b(ns.generate_executed), ns.territorial_product_run_id, ns.territorial_product_artifact, ns.territorial_product_digest, ns.territorial_product_validation, ns.territorial_product_phase_decision),
        phase("03 · Preparación de Resultados Electorales", ns.prepare_electoral_result, b(ns.prepare_electoral_executed), ns.electoral_source_run_id, ns.electoral_source_artifact, ns.electoral_source_digest, ns.electoral_source_validation, ns.electoral_source_phase_decision),
        phase("04 · Incorporación de Resultados Electorales", ns.incorporate_result, b(ns.incorporate_executed), ns.electoral_product_run_id, ns.electoral_product_artifact, ns.electoral_product_digest, ns.electoral_product_validation, ns.electoral_product_phase_decision),
        phase(
            "05 · Publicación del Visor",
            ns.publish_result,
            ns.publish_requested == "true",
            ns.workflow_run_id if ns.publish_requested == "true" else None,
            None,
        ),
    ]
    failed = [p["name"] for p in phases if p["executed"] and p["result"] != "success"]
    blocked = [p["name"] for p in phases[:4] if p.get("validation_decision") not in {None, "VALIDADO"}]
    optimization = optimization_lineage(
        ns.optimization_algorithm,
        generate_executed=b(ns.generate_executed),
        evidence_path=ns.optimization_evidence,
    )

    payload = {
        "schema": "ddd.full-run-manifest/2.1",
        "territory_id": ns.territory_id,
        "territory_name": ns.territory_name,
        "edition": ns.edition,
        "execution_mode": ns.execution_mode,
        **optimization,
        "workflow_run_id": int(ns.workflow_run_id),
        "source_sha": ns.source_sha,
        "publish_requested": ns.publish_requested == "true",
        "status": "SUCCESS" if not failed and not blocked else "FAILED",
        "failed_phases": failed,
        "blocked_phases": blocked,
        "phases": phases,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    out = Path(ns.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
