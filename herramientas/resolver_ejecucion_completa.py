from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup

PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


def generation_enablement(
    *,
    root_dir: Path,
    contract_path: str | None,
    territory_id: str,
    certified_product_ready: bool = False,
) -> dict:
    """Determine generation readiness from contract structure and durable product evidence."""
    path = root_dir / contract_path if contract_path else None
    if path is None or not path.is_file():
        return {"allowed": False, "reason": "contrato territorial efectivo ausente"}
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {"allowed": False, "reason": "contrato territorial efectivo ilegible"}
    if not isinstance(contract, dict) or (contract.get("meta") or {}).get("territory_id") != territory_id:
        return {"allowed": False, "reason": "identidad del contrato territorial no coincide"}

    meta = contract["meta"]
    territory_contract = contract.get("territory_contract") or {}
    status = territory_contract.get("status")
    modules = contract.get("modulos") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m06 = modules.get("modulo_06_consolidar_distritos") or {}

    if meta.get("status") == status == "generation_ready":
        return {"allowed": True, "route": "declared_generation_ready"}

    partitioning = contract.get("partitioning") or {}
    if (partitioning.get("enabled") is True
            and partitioning.get("strategy") == "connected_internal_units"
            and partitioning.get("output_geojson")
            and partitioning["output_geojson"] == m04.get("in_geojson")
            and partitioning.get("partition_unit_field")
            and partitioning["partition_unit_field"] == m04.get("municipality_field")):
        return {"allowed": True, "route": "linked_internal_partitioning"}

    k = territory_contract.get("k_districts")
    production_chain_ready = bool(
        meta.get("contract_level") == "production_m01_m06"
        and meta.get("production_authorization") == "AUTHORIZED"
        and isinstance(k, int) and not isinstance(k, bool) and k > 0
        and m04.get("k_districts") == k
        and m06.get("expected_districts") == k
        and m04.get("in_graph_json")
        and m04.get("in_geojson")
        and m04.get("out_geojson")
        and m04["out_geojson"] == m05.get("in_geojson")
        and m05.get("out_geojson")
        and m05["out_geojson"] == m06.get("in_geojson")
    )
    if certified_product_ready and production_chain_ready:
        return {"allowed": True, "route": "certified_product_lineage"}

    if production_chain_ready:
        return {"allowed": True, "route": "structural_generation_contract"}

    return {"allowed": False, "reason": f"contrato territorial sin generación habilitada: {status or 'sin estado'}"}


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


def _run_from_artifact(name: object, fallback: object = None) -> int | None:
    artifact_name = str(name or "")
    match = re.search(r"-(\d+)-M\d+$", artifact_name)
    if match is None:
        match = re.search(r"-(\d+)$", artifact_name)
    if match:
        return int(match.group(1))
    try:
        return int(fallback) if fallback not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build_plan(*, territory: str, edition: str, execution_mode: str, catalog: Path, root_dir: Path, optimization_algorithm: str = "Canónico", force_selected_algorithm: bool = False) -> dict:
    row = lookup(territory, edition, catalog)
    state = row
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

    source_run_id = _run_from_artifact(prep.get("artifact_name"), prep.get("run_id"))
    territorial_product_run_id = _run_from_artifact(territorial_evidence.get("artifact_name"), territorial_evidence.get("run_id") or (last_run if last_num >= 6 else None))
    territorial_product_artifact = territorial_evidence.get("artifact_name") or (
        f"ddd-state-{territorial_product_run_id}-M06" if territorial_product_run_id else None
    )
    electoral_source_run_id = _run_from_artifact(electoral_source_evidence.get("artifact_name"), electoral_source_evidence.get("run_id"))
    electoral_product_run_id = _run_from_artifact(electoral_product_evidence.get("artifact_name"), electoral_product_evidence.get("run_id") or (last_run if last_num >= 8 else None))
    electoral_product_artifact = electoral_product_evidence.get("artifact_name") or (
        f"ddd-state-{electoral_product_run_id}-M08" if electoral_product_run_id else None
    )

    from_start = execution_mode == "from_start"
    if execution_mode not in {"reuse", "from_start"}:
        raise ValueError(f"Modo de ejecución inválido: {execution_mode}")
    allowed_algorithms = {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}
    if optimization_algorithm not in allowed_algorithms:
        raise ValueError(f"Estrategia de optimización inválida: {optimization_algorithm}")

    territorial_sources_ready = bool(
        state.get("territorial_sources_prepared")
        and source_run_id
        and prep.get("artifact_name")
        and prep.get("artifact_sha256")
    )
    territorial_product_ready = bool(
        state.get("territorial_product_available")
        and state.get("territorial_certification") in PASS_CERTIFICATIONS
        and territorial_product_run_id
        and territorial_evidence.get("artifact_sha256")
    )
    electoral_source_ready = bool(
        state.get("electoral_source_prepared")
        and electoral_source_run_id
        and electoral_source_evidence.get("artifact_name")
        and electoral_source_evidence.get("artifact_sha256")
    )
    electoral_product_ready = bool(
        state.get("electoral_product_available")
        and electoral_product_run_id
        and electoral_product_evidence.get("artifact_sha256")
    )

    run_prepare_territorial = from_start or not territorial_sources_ready
    # En ejecución manual, 00 expone una elección explícita de algoritmo y 02 debe
    # ejecutarse. El smoke de pull request puede desactivar esta fuerza para validar
    # la orquestación sin recalcular un territorio ya certificado.
    generation_gate = generation_enablement(
        root_dir=root_dir,
        contract_path=row.get("contract_path"),
        territory_id=row["territory_id"],
        certified_product_ready=territorial_product_ready,
    )
    proposed_generate = bool(from_start or run_prepare_territorial or not territorial_product_ready or optimization_algorithm != "Canónico" or force_selected_algorithm)
    if proposed_generate and not generation_gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: {row['name']}: {generation_gate['reason']}")
    run_generate = proposed_generate
    run_prepare_electoral = from_start or not electoral_source_ready
    run_incorporate = from_start or run_generate or run_prepare_electoral or not electoral_product_ready

    existing_source_run_id = source_run_id
    existing_source_artifact_name = prep.get("artifact_name")

    plan = {
        "schema": "ddd.full-run-plan/1.1",
        "territory_id": row["territory_id"],
        "territory_name": row["name"],
        "edition": edition,
        "contract_path": row.get("contract_path"),
        "execution_mode": execution_mode,
        "optimization_algorithm": optimization_algorithm,
        "run_prepare_territorial": run_prepare_territorial,
        "run_generate": run_generate,
        "run_prepare_electoral": run_prepare_electoral,
        "run_incorporate": run_incorporate,
        "existing": {
            "territorial_source": {
                "run_id": existing_source_run_id,
                "artifact_name": existing_source_artifact_name,
                "artifact_sha256": prep.get("artifact_sha256"),
                "decision": "VALIDADO" if territorial_sources_ready else None,
            },
            "territorial_product": {
                "run_id": territorial_product_run_id,
                "artifact_name": territorial_product_artifact,
                "artifact_sha256": territorial_evidence.get("artifact_sha256"),
                "decision": territorial_evidence.get("decision"),
            },
            "electoral_source": {
                "run_id": electoral_source_run_id,
                "artifact_name": electoral_source_evidence.get("artifact_name"),
                "artifact_sha256": electoral_source_evidence.get("artifact_sha256"),
                "election_id": electoral_source_evidence.get("election_id"),
                "decision": "VALIDADO" if electoral_source_ready else None,
            },
            "electoral_product": {
                "run_id": electoral_product_run_id,
                "artifact_name": electoral_product_artifact,
                "artifact_sha256": electoral_product_evidence.get("artifact_sha256"),
                "decision": "VALIDADO" if electoral_product_ready else None,
            },
        },
        "generation_gate": generation_gate,
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


def apply_explicit_territorial_source(
    plan: dict,
    *,
    root_dir: Path = Path("."),
    reuse_run_id: str = "",
    reuse_artifact_name: str = "",
    reuse_artifact_sha256: str = "",
    reuse_source_sha: str = "",
    campaign_instance: str = "",
    expected_population: str = "",
    expected_sections: str = "",
    expected_districts: str = "",
    expected_certification: str = "",
) -> dict:
    """Fix the preflight-approved source, regardless of campaign status reporting."""
    fields = (reuse_run_id, reuse_artifact_name, reuse_artifact_sha256, reuse_source_sha)
    if not any(fields):
        if campaign_instance:
            raise ValueError("Procedencia explícita incompleta")
        return plan
    if not all(fields):
        raise ValueError("Procedencia explícita incompleta")
    if not reuse_run_id.isdecimal() or int(reuse_run_id) <= 0:
        raise ValueError("reuse_run_id inválido")
    if not re.fullmatch(r"[0-9a-f]{64}", reuse_artifact_sha256):
        raise ValueError("reuse_artifact_sha256 inválido")
    if not re.fullmatch(r"[0-9a-f]{40}", reuse_source_sha):
        raise ValueError("reuse_source_sha inválido")
    gate = generation_enablement(
        root_dir=root_dir,
        contract_path=plan.get("contract_path"),
        territory_id=plan.get("territory_id", ""),
        certified_product_ready=bool(
            (plan.get("catalog_state") or {}).get("territorial_product_available")
        ),
    )
    if not gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: Fuente explícita no habilita generación: {gate['reason']}")

    plan["execution_mode"] = "from_start"
    plan["run_prepare_territorial"] = False
    plan["run_generate"] = True
    plan["existing"]["territorial_source"] = {
        "run_id": int(reuse_run_id),
        "artifact_name": reuse_artifact_name,
        "artifact_sha256": reuse_artifact_sha256,
        "source_commit": reuse_source_sha,
    }
    if campaign_instance:
        plan["campaign"]["reuse"] = {
            "run_id": int(reuse_run_id),
            "artifact_name": reuse_artifact_name,
            "artifact_sha256": reuse_artifact_sha256,
            "source_sha": reuse_source_sha,
            "expected_population_total": int(expected_population),
            "expected_section_count": int(expected_sections),
            "expected_district_count": int(expected_districts),
            "expected_certification": expected_certification,
        }
    return plan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--territory", required=True)
    ap.add_argument("--edition", required=True)
    ap.add_argument("--execution-mode", choices=["reuse", "from_start"], required=True)
    ap.add_argument("--optimization-algorithm", default="Canónico", choices=["Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"])
    ap.add_argument("--reuse-existing-optimization", action="store_true")
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
        optimization_algorithm=ns.optimization_algorithm,
        force_selected_algorithm=not ns.reuse_existing_optimization,
    )
    text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        out = Path(ns.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    main()
