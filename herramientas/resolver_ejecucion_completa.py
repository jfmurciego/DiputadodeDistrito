from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from herramientas import _resolver_ejecucion_completa_core as _core
from herramientas._resolver_ejecucion_completa_core import *  # noqa: F401,F403

_run_from_artifact = _core._run_from_artifact


def _generation_capabilities(contract: dict) -> dict:
    meta = contract.get("meta") or {}
    territorial = contract.get("territory_contract") or {}
    modules = contract.get("modulos") or {}
    validation = contract.get("validation") or {}
    partitioning = contract.get("partitioning") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m03 = modules.get("modulo_03_construir_grafo") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m06 = modules.get("modulo_06_consolidar_distritos") or {}

    if meta.get("contract_level") != "production_m01_m06" or not all((m01, m02, m03, m04, m05, m06)):
        return _core._blocked("CAP_CONTRACT", "contrato M01-M06 ausente o incompleto")
    if meta.get("production_authorization") == "BLOCKED":
        return _core._blocked("CAP_CONTRACT", "contrato marcado explícitamente como BLOCKED")
    k = territorial.get("k_districts")
    if (not isinstance(k, int) or isinstance(k, bool) or k <= 0
            or m04.get("k_districts") != k or m06.get("expected_districts") != k):
        return _core._blocked("CAP_K", "K ausente o incoherente entre contrato, Formación inicial y Consolidación")
    limits = (
        territorial.get("population_floor_ratio"),
        territorial.get("population_cap_ratio"),
        territorial.get("target_tolerance_ratio"),
    )
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0 for v in limits):
        return _core._blocked("CAP_POPULATION_LIMITS", "suelo, techo o tolerancia poblacional ausentes o inválidos")

    municipality_field = validation.get("municipality_field")
    admin_policy_ok = validation.get("require_municipality_discipline") is True and bool(municipality_field)
    if partitioning.get("enabled") is True:
        partition_field = partitioning.get("partition_unit_field")
        downstream_field = m05.get("municipality_field")
        admin_policy_ok = (
            admin_policy_ok
            and partitioning.get("municipality_field") == municipality_field
            and bool(partition_field)
            and m04.get("municipality_field") == partition_field
            and downstream_field in {municipality_field, partition_field}
            and m06.get("municipality_field") == downstream_field
        )
    else:
        admin_policy_ok = (
            admin_policy_ok
            and m04.get("municipality_field") == municipality_field
            and m05.get("municipality_field") == municipality_field
            and m06.get("municipality_field") == municipality_field
        )
    if not admin_policy_ok:
        return _core._blocked("CAP_ADMIN_POLICY", "disciplina o campo administrativo de trabajo incompletos o incoherentes")

    graph = m03.get("out_graph_json")
    if (not graph or graph != m04.get("in_graph_json") or graph != m05.get("in_graph_json")
            or validation.get("require_graph_contiguity") is not True):
        return _core._blocked("CAP_GRAPH", "grafo contractual o control de contigüidad incompletos")
    if partitioning.get("enabled") is True:
        if (partitioning.get("strategy") != "connected_internal_units"
                or not partitioning.get("output_geojson")
                or partitioning.get("output_geojson") != m04.get("in_geojson")
                or partitioning.get("partition_unit_field") != m04.get("municipality_field")):
            return _core._blocked("CAP_M04_INPUT", "particionado interno no enlaza con Formación inicial")
    elif not m01.get("out_geojson") or m01.get("out_geojson") != m04.get("in_geojson"):
        return _core._blocked("CAP_M04_INPUT", "entrada de Formación inicial no es resoluble desde la base territorial")
    if (not m04.get("out_geojson") or m04.get("out_geojson") != m05.get("in_geojson")
            or not m05.get("out_geojson") or m05.get("out_geojson") != m06.get("in_geojson")):
        return _core._blocked("CAP_GENERATION_CHAIN", "Formación inicial, Optimización y Consolidación no están enlazadas")
    return {"allowed": True}


def generation_enablement(*, root_dir: Path, contract_path: str | None, territory_id: str,
                          certified_product_ready: bool = False, first_generation_evidence: dict | None = None,
                          preparation_evidence: dict | None = None, require_source: bool = False,
                          source_acquisition_planned: bool = False) -> dict:
    path = root_dir / contract_path if contract_path else None
    if path is None or not path.is_file():
        return _core._blocked("CAP_CONTRACT", "contrato territorial efectivo ausente")
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return _core._blocked("CAP_CONTRACT", "contrato territorial efectivo ilegible")
    if not isinstance(contract, dict) or (contract.get("meta") or {}).get("territory_id") != territory_id:
        return _core._blocked("CAP_CONTRACT", "identidad del contrato territorial no coincide")
    capability_gate = _generation_capabilities(contract)
    if not capability_gate["allowed"]:
        return capability_gate
    prep = preparation_evidence or {}
    if require_source and not source_acquisition_planned:
        if (not isinstance(prep.get("run_id"), int) or isinstance(prep.get("run_id"), bool)
                or prep.get("run_id") <= 0 or not prep.get("artifact_name")
                or not _core._sha256_value(prep.get("artifact_sha256"))):
            return _core._blocked("CAP_SOURCE", "fuente territorial no acreditada por run, artefacto y SHA-256")
        if "source_commit" in prep and not re.fullmatch(r"[0-9a-f]{40}", str(prep.get("source_commit") or "")):
            return _core._blocked("CAP_SOURCE", "source_commit de la fuente efectiva inválido")
    if first_generation_evidence:
        return _core._validated_first_generation_preflight(
            contract=contract, evidence=first_generation_evidence, preparation_evidence=prep,
            territory_id=territory_id, root_dir=root_dir,
        )
    meta = contract.get("meta") or {}
    territorial = contract.get("territory_contract") or {}
    modules = contract.get("modulos") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    partitioning = contract.get("partitioning") or {}
    if certified_product_ready:
        return {"allowed": True, "route": "certified_product_lineage"}
    if source_acquisition_planned:
        return {"allowed": True, "route": "planned_source_acquisition"}
    if meta.get("status") == territorial.get("status") == "generation_ready":
        return {"allowed": True, "route": "declared_generation_ready"}
    if (partitioning.get("enabled") is True and partitioning.get("strategy") == "connected_internal_units"
            and partitioning.get("output_geojson") == m04.get("in_geojson")
            and partitioning.get("partition_unit_field") == m04.get("municipality_field")):
        return {"allowed": True, "route": "linked_internal_partitioning"}
    return _core._blocked("CAP_PRE_M04_EVIDENCE", "primera generación sin evidencia durable pre-M04")


def _explicit_source(values: dict | None) -> dict | None:
    if not values:
        env = __import__("os").environ
        env_values = {
            "run_id": env.get("REUSE_RUN_ID", ""),
            "artifact_name": env.get("REUSE_ARTIFACT_NAME", ""),
            "artifact_sha256": env.get("REUSE_ARTIFACT_SHA256", ""),
            "source_commit": env.get("REUSE_SOURCE_SHA", ""),
        }
        if any(env_values.values()):
            values = env_values
    if not values:
        return None
    run_id = values.get("run_id")
    if isinstance(run_id, str) and run_id.isdecimal():
        run_id = int(run_id)
    return {
        "run_id": run_id,
        "artifact_name": values.get("artifact_name"),
        "artifact_sha256": values.get("artifact_sha256"),
        "source_commit": values.get("source_commit"),
        **({"package_sha256": values.get("package_sha256")} if values.get("package_sha256") else {}),
    }


def build_plan(*, territory: str, edition: str, execution_mode: str, catalog: Path, root_dir: Path,
               optimization_algorithm: str = "Canónico", force_selected_algorithm: bool = False,
               explicit_territorial_source: dict | None = None) -> dict:
    row = _core.lookup(territory, edition, catalog)
    state = row
    evidence = state.get("evidence") or {}
    territorial_evidence = _core._load_json(evidence.get("territorial_product"), root_dir)
    electoral_source_evidence = _core._load_json(evidence.get("electoral_source"), root_dir)
    electoral_product_evidence = _core._load_json(evidence.get("electoral_product"), root_dir)
    generation_preflight_path = evidence.get("generation_preflight")
    generation_preflight_evidence = _core._load_json(generation_preflight_path, root_dir)
    if generation_preflight_path and not generation_preflight_evidence:
        generation_preflight_evidence = {"_load_error": f"no se pudo leer {generation_preflight_path}"}
    catalog_prep = state.get("preparation_evidence") or {}
    selected_explicit_source = _explicit_source(explicit_territorial_source)
    prep = selected_explicit_source or catalog_prep
    last = state.get("last_valid_checkpoint") or {}
    last_run = last.get("run_id")
    try:
        last_num = int(str(last.get("stage") or "").removeprefix("M"))
    except ValueError:
        last_num = 0
    source_run_id = _core._run_from_artifact(prep.get("artifact_name"), prep.get("run_id"))
    territorial_product_run_id = _core._run_from_artifact(
        territorial_evidence.get("artifact_name"),
        territorial_evidence.get("run_id") or (last_run if last_num >= 6 else None),
    )
    territorial_product_artifact = territorial_evidence.get("artifact_name") or (
        f"ddd-state-{territorial_product_run_id}-M06" if territorial_product_run_id else None
    )
    electoral_source_run_id = _core._run_from_artifact(
        electoral_source_evidence.get("artifact_name"), electoral_source_evidence.get("run_id")
    )
    electoral_product_run_id = _core._run_from_artifact(
        electoral_product_evidence.get("artifact_name"),
        electoral_product_evidence.get("run_id") or (last_run if last_num >= 8 else None),
    )
    electoral_product_artifact = electoral_product_evidence.get("artifact_name") or (
        f"ddd-state-{electoral_product_run_id}-M08" if electoral_product_run_id else None
    )
    from_start = execution_mode == "from_start"
    if execution_mode not in {"reuse", "from_start"}:
        raise ValueError(f"Modo de ejecución inválido: {execution_mode}")
    if optimization_algorithm not in {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}:
        raise ValueError(f"Estrategia de optimización inválida: {optimization_algorithm}")
    source_shape_ready = bool(
        source_run_id and prep.get("artifact_name") and _core._sha256_value(prep.get("artifact_sha256"))
    )
    territorial_sources_ready = bool(
        source_shape_ready and (selected_explicit_source is not None or state.get("territorial_sources_prepared"))
    )
    territorial_product_ready = bool(
        state.get("territorial_product_available")
        and state.get("territorial_certification") in _core.PASS_CERTIFICATIONS
        and territorial_product_run_id and territorial_evidence.get("artifact_sha256")
    )
    electoral_source_ready = bool(
        state.get("electoral_source_prepared") and electoral_source_run_id
        and electoral_source_evidence.get("artifact_name") and electoral_source_evidence.get("artifact_sha256")
    )
    electoral_product_ready = bool(
        state.get("electoral_product_available") and electoral_product_run_id
        and electoral_product_evidence.get("artifact_sha256")
    )
    run_prepare_territorial = from_start if selected_explicit_source is None else False
    if selected_explicit_source is None and not from_start:
        run_prepare_territorial = not territorial_sources_ready
    generation_gate = generation_enablement(
        root_dir=root_dir, contract_path=row.get("contract_path"), territory_id=row["territory_id"],
        certified_product_ready=territorial_product_ready,
        first_generation_evidence=(
            generation_preflight_evidence
            if territorial_sources_ready and not run_prepare_territorial and not territorial_product_ready else None
        ),
        preparation_evidence=prep, require_source=True, source_acquisition_planned=run_prepare_territorial,
    )
    proposed_generate = bool(
        from_start or selected_explicit_source is not None or run_prepare_territorial or not territorial_product_ready
        or optimization_algorithm != "Canónico" or force_selected_algorithm
    )
    if proposed_generate and not generation_gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: {row['name']}: {generation_gate['reason']}")
    run_generate = proposed_generate
    run_prepare_electoral = from_start or not electoral_source_ready
    run_incorporate = from_start or run_generate or run_prepare_electoral or not electoral_product_ready
    plan = {
        "schema": "ddd.full-run-plan/1.1", "territory_id": row["territory_id"], "territory_name": row["name"],
        "edition": edition, "contract_path": row.get("contract_path"), "execution_mode": execution_mode,
        "optimization_algorithm": optimization_algorithm, "run_prepare_territorial": run_prepare_territorial,
        "run_generate": run_generate, "run_prepare_electoral": run_prepare_electoral, "run_incorporate": run_incorporate,
        "existing": {
            "territorial_source": {
                "run_id": source_run_id, "artifact_name": prep.get("artifact_name"),
                "artifact_sha256": prep.get("artifact_sha256"), "source_commit": prep.get("source_commit"),
                "decision": "VALIDADO" if territorial_sources_ready else None,
            },
            "territorial_product": {"run_id": territorial_product_run_id, "artifact_name": territorial_product_artifact, "artifact_sha256": territorial_evidence.get("artifact_sha256"), "decision": territorial_evidence.get("decision")},
            "electoral_source": {"run_id": electoral_source_run_id, "artifact_name": electoral_source_evidence.get("artifact_name"), "artifact_sha256": electoral_source_evidence.get("artifact_sha256"), "election_id": electoral_source_evidence.get("election_id"), "decision": "VALIDADO" if electoral_source_ready else None},
            "electoral_product": {"run_id": electoral_product_run_id, "artifact_name": electoral_product_artifact, "artifact_sha256": electoral_product_evidence.get("artifact_sha256"), "decision": "VALIDADO" if electoral_product_ready else None},
        },
        "generation_gate": generation_gate,
        "catalog_state": {
            "territorial_sources_prepared": territorial_sources_ready,
            "territorial_product_available": territorial_product_ready,
            "electoral_source_prepared": electoral_source_ready,
            "electoral_product_available": electoral_product_ready,
            "territorial_certification": state.get("territorial_certification"),
            "preparation_evidence": prep,
            "catalog_preparation_evidence": catalog_prep,
            "generation_preflight_evidence": generation_preflight_evidence,
            "generation_preflight_path": generation_preflight_path,
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


def apply_explicit_territorial_source(plan: dict, *, root_dir: Path = Path("."), reuse_run_id: str = "",
                                      reuse_artifact_name: str = "", reuse_artifact_sha256: str = "",
                                      reuse_source_sha: str = "", campaign_instance: str = "",
                                      expected_population: str = "", expected_sections: str = "",
                                      expected_districts: str = "", expected_certification: str = "") -> dict:
    fields = (reuse_run_id, reuse_artifact_name, reuse_artifact_sha256, reuse_source_sha)
    if not any(fields):
        if campaign_instance:
            raise ValueError("Procedencia explícita incompleta")
        return plan
    if not all(fields):
        raise ValueError("Procedencia explícita incompleta")
    try:
        run_id = int(reuse_run_id)
    except (TypeError, ValueError):
        run_id = 0
    prep = {
        "run_id": run_id,
        "artifact_name": reuse_artifact_name,
        "artifact_sha256": reuse_artifact_sha256,
        "source_commit": reuse_source_sha,
    }
    catalog_state = plan.get("catalog_state") or {}
    certified_product_ready = bool(catalog_state.get("territorial_product_available"))
    gate = generation_enablement(
        root_dir=root_dir, contract_path=plan.get("contract_path"), territory_id=plan.get("territory_id", ""),
        certified_product_ready=certified_product_ready,
        first_generation_evidence=(None if certified_product_ready else catalog_state.get("generation_preflight_evidence") or None),
        preparation_evidence=prep, require_source=True,
    )
    if not gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: Fuente explícita no habilita generación: {gate['reason']}")
    if gate.get("route") == "validated_pre_m04_topology":
        first = catalog_state.get("generation_preflight_evidence") or {}
        source = first.get("source") or {}
        if (run_id != first.get("run_id") or reuse_artifact_name != source.get("artifact_name")
                or reuse_artifact_sha256 != source.get("artifact_sha256") or reuse_source_sha != first.get("source_commit")):
            raise ValueError("GENERATION_CONTRACT_BLOCK: la fuente explícita no coincide con la procedencia validada para primera generación")
    plan["execution_mode"] = "from_start"
    plan["run_prepare_territorial"] = False
    plan["run_generate"] = True
    plan["generation_gate"] = gate
    plan["existing"]["territorial_source"] = prep
    catalog_state["preparation_evidence"] = prep
    if campaign_instance:
        plan["campaign"]["reuse"] = {
            "run_id": run_id, "artifact_name": reuse_artifact_name,
            "artifact_sha256": reuse_artifact_sha256, "source_sha": reuse_source_sha,
            "expected_population_total": int(expected_population), "expected_section_count": int(expected_sections),
            "expected_district_count": int(expected_districts), "expected_certification": expected_certification,
        }
    return plan


_core._generation_capabilities = _generation_capabilities
_core.generation_enablement = generation_enablement
_core.build_plan = build_plan
_core.apply_explicit_territorial_source = apply_explicit_territorial_source


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
    ap.add_argument("--explicit-source-run-id", default="")
    ap.add_argument("--explicit-source-artifact-name", default="")
    ap.add_argument("--explicit-source-artifact-sha256", default="")
    ap.add_argument("--explicit-source-commit", default="")
    ns = ap.parse_args()
    explicit_values = (
        ns.explicit_source_run_id, ns.explicit_source_artifact_name,
        ns.explicit_source_artifact_sha256, ns.explicit_source_commit,
    )
    explicit = None
    if any(explicit_values):
        if not all(explicit_values):
            raise SystemExit("Procedencia explícita incompleta")
        try:
            explicit_run_id = int(ns.explicit_source_run_id)
        except ValueError as exc:
            raise SystemExit("explicit-source-run-id inválido") from exc
        explicit = {
            "run_id": explicit_run_id,
            "artifact_name": ns.explicit_source_artifact_name,
            "artifact_sha256": ns.explicit_source_artifact_sha256,
            "source_commit": ns.explicit_source_commit,
        }
    root = Path(ns.root_dir)
    plan = build_plan(
        territory=ns.territory, edition=ns.edition, execution_mode=ns.execution_mode,
        catalog=root / ns.catalog, root_dir=root, optimization_algorithm=ns.optimization_algorithm,
        force_selected_algorithm=not ns.reuse_existing_optimization,
        explicit_territorial_source=explicit,
    )
    text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        out = Path(ns.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    main()
