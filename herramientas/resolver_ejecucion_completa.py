from __future__ import annotations

import argparse
import json
from pathlib import Path

from herramientas.catalogo_preparacion import lookup

PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


def _load_json(path: str | None, root: Path) -> dict:
    if not path:
        return {}
    p = root / path
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_plan(*, territory: str, edition: str, execution_mode: str, catalog: Path, root_dir: Path) -> dict:
    row = lookup(territory, edition, catalog)
    state = row["state"]
    evidence = state.get("evidence") or {}

    territorial_evidence = _load_json(evidence.get("territorial_product"), root_dir)
    electoral_source_evidence = _load_json(evidence.get("electoral_source"), root_dir)
    electoral_product_evidence = _load_json(evidence.get("electoral_product"), root_dir)
    prep = state.get("preparation_evidence") or {}
    last = state.get("last_valid_checkpoint") or {}
    last_run = last.get("run_id")
    last_stage = str(last.get("stage") or "")
    try:
        last_num = int(last_stage.removeprefix("M"))
    except ValueError:
        last_num = 0

    territorial_product_run_id = territorial_evidence.get("run_id") or (last_run if last_num >= 6 else None)
    territorial_product_artifact = territorial_evidence.get("artifact_name") or (
        f"ddd-state-{territorial_product_run_id}-M06" if territorial_product_run_id else None
    )
    electoral_product_run_id = electoral_product_evidence.get("run_id") or (last_run if last_num >= 8 else None)
    electoral_product_artifact = electoral_product_evidence.get("artifact_name") or (
        f"ddd-state-{electoral_product_run_id}-M08" if electoral_product_run_id else None
    )

    from_start = execution_mode == "from_start"
    if execution_mode not in {"reuse", "from_start"}:
        raise ValueError(f"Modo de ejecución inválido: {execution_mode}")

    territorial_sources_ready = bool(
        state.get("territorial_sources_prepared") and prep.get("run_id") and prep.get("artifact_name")
    )
    territorial_product_ready = bool(
        state.get("territorial_product_available")
        and state.get("territorial_certification") in PASS_CERTIFICATIONS
        and territorial_product_run_id
    )
    electoral_source_ready = bool(
        state.get("electoral_source_prepared")
        and electoral_source_evidence.get("run_id")
        and electoral_source_evidence.get("artifact_name")
    )
    electoral_product_ready = bool(state.get("electoral_product_available") and electoral_product_run_id)

    run_prepare_territorial = from_start or not territorial_sources_ready
    run_generate = from_start or run_prepare_territorial or not territorial_product_ready
    run_prepare_electoral = from_start or not electoral_source_ready
    run_incorporate = from_start or run_generate or run_prepare_electoral or not electoral_product_ready

    existing_source_run_id = prep.get("run_id")
    existing_source_artifact_name = prep.get("artifact_name")

    plan = {
        "schema": "ddd.full-run-plan/1.0",
        "territory_id": row["territory_id"],
        "territory_name": row["name"],
        "edition": edition,
        "contract_path": row.get("contract_path"),
        "execution_mode": execution_mode,
        "run_prepare_territorial": run_prepare_territorial,
        "run_generate": run_generate,
        "run_prepare_electoral": run_prepare_electoral,
        "run_incorporate": run_incorporate,
        "existing": {
            "territorial_source": {
                "run_id": existing_source_run_id,
                "artifact_name": existing_source_artifact_name,
            },
            "territorial_product": {
                "run_id": territorial_product_run_id,
                "artifact_name": territorial_product_artifact,
                "decision": territorial_evidence.get("decision"),
            },
            "electoral_source": {
                "run_id": electoral_source_evidence.get("run_id"),
                "artifact_name": electoral_source_evidence.get("artifact_name"),
                "election_id": electoral_source_evidence.get("election_id"),
            },
            "electoral_product": {
                "run_id": electoral_product_run_id,
                "artifact_name": electoral_product_artifact,
            },
        },
        "catalog_state": {
            "territorial_sources_prepared": territorial_sources_ready,
            "territorial_product_available": territorial_product_ready,
            "electoral_source_prepared": electoral_source_ready,
            "electoral_product_available": electoral_product_ready,
            "territorial_certification": state.get("territorial_certification"),
        },
    }

    if not plan["contract_path"] and not run_prepare_territorial:
        raise ValueError(f"El territorio {row['name']} no tiene contrato productivo materializado y la preparación territorial no está programada")

    if not run_generate and not plan["existing"]["territorial_product"]["run_id"]:
        raise ValueError("El catálogo marca producto territorial disponible pero no existe evidencia durable con run_id")
    if not run_prepare_electoral and not plan["existing"]["electoral_source"]["run_id"]:
        raise ValueError("El catálogo marca fuente electoral preparada pero no existe evidencia durable con run_id")
    if not run_incorporate and not plan["existing"]["electoral_product"]["run_id"]:
        raise ValueError("El catálogo marca producto electoral disponible pero no existe evidencia durable con run_id")

    return plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--execution-mode", choices=["reuse", "from_start"], required=True)
    ap.add_argument("--catalog", default="configuracion/catalogo_preparacion.yaml")
    ap.add_argument("--root-dir", default=".")
    ap.add_argument("--output")
    ns = ap.parse_args()

    root = Path(ns.root_dir)
    plan = build_plan(
        territory=ns.territory,
        edition=ns.edition,
        execution_mode=ns.execution_mode,
        catalog=root / ns.catalog,
        root_dir=root,
    )
    text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        out = Path(ns.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    main()
