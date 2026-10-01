from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from herramientas import _resolver_ejecucion_completa_core as _core
from herramientas._resolver_ejecucion_completa_core import *  # noqa: F401,F403
from herramientas.resolver_activos_durables import DurableAssetBlock, validate_durable_assets

_run_from_artifact = _core._run_from_artifact


def _generation_capabilities(contract: dict, root_dir: Path | None = None) -> dict:
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
    if validation.get("hard_partition_mode") == "physical_components":
        if root_dir is None:
            return _core._blocked("CAP_M04_INPUT", "la entrada física requiere resolver su evidencia durable")
        try:
            _core._hard_partition_spec(contract, root_dir)
        except ValueError as exc:
            return _core._blocked("CAP_M04_INPUT", str(exc))
    elif partitioning.get("enabled") is True:
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
                          source_acquisition_planned: bool = False,
                          pre_m04_accreditation_planned: bool = False,
                          source_recalculation_planned: bool = False) -> dict:
    path = root_dir / contract_path if contract_path else None
    if path is None or not path.is_file():
        return _core._blocked("CAP_CONTRACT", "contrato territorial efectivo ausente")
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return _core._blocked("CAP_CONTRACT", "contrato territorial efectivo ilegible")
    if not isinstance(contract, dict) or (contract.get("meta") or {}).get("territory_id") != territory_id:
        return _core._blocked("CAP_CONTRACT", "identidad del contrato territorial no coincide")
    capability_gate = _generation_capabilities(contract, root_dir=root_dir)
    if not capability_gate["allowed"]:
        return capability_gate
    prep = preparation_evidence or {}
    if require_source and not source_acquisition_planned:
        if (
            not isinstance(prep.get("run_id"), int)
            or isinstance(prep.get("run_id"), bool)
            or prep.get("run_id") <= 0
            or not prep.get("artifact_name")
            or not _core._sha256_value(prep.get("artifact_sha256"))
            or not _core._sha256_value(prep.get("package_sha256"))
            or not _core._sha256_value(prep.get("compatibility_identity_sha256"))
            or not isinstance(prep.get("population_year"), int)
            or not isinstance(prep.get("section_year"), int)
        ):
            return _core._blocked(
                "CAP_SOURCE",
                "fuente territorial sin identidad completa run/artefacto/paquete/compatibilidad/años",
            )
        if "source_commit" in prep and not re.fullmatch(r"[0-9a-f]{40}", str(prep.get("source_commit") or "")):
            return _core._blocked("CAP_SOURCE", "source_commit de la fuente efectiva inválido")
    if source_recalculation_planned:
        return {"allowed": True, "route": "accredited_source_recalculation"}
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
    if source_acquisition_planned:
        return {"allowed": True, "route": "planned_source_acquisition"}
    if pre_m04_accreditation_planned:
        return {"allowed": True, "route": "planned_pre_m04_accreditation"}
    if certified_product_ready and not source_recalculation_planned:
        return {"allowed": True, "route": "certified_product_lineage"}
    return _core._blocked(
        "CAP_PRE_M04_EVIDENCE",
        "la generación exige evidencia pre-M04 ligada a la fuente efectiva; los estados históricos no habilitan una fuente nueva",
    )


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



def _catalog_territorial_source(*, row: dict, state: dict, edition: str, root_dir: Path) -> dict:
    territory_id = str(row.get("territory_id") or "")
    if state.get("territorial_sources_prepared") is not True:
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "la fuente territorial no está marcada como preparada"
        )
    prep = state.get("preparation_evidence")
    if not isinstance(prep, dict):
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "falta preparation_evidence durable"
        )
    try:
        run_id = int(prep.get("run_id"))
    except Exception as exc:
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: run_id de fuente inválido"
        ) from exc
    if run_id <= 0:
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: run_id de fuente inválido"
        )
    artifact_name = str(prep.get("artifact_name") or "")
    expected_name = f"ddd-source-package-{territory_id}-{edition}-{run_id}"
    if artifact_name != expected_name:
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            f"artefacto territorial no coincide con run/territorio/edición: {artifact_name!r}"
        )
    artifact_sha256 = str(prep.get("artifact_sha256") or "").removeprefix("sha256:").lower()
    package_sha256 = str(prep.get("package_sha256") or "").removeprefix("sha256:").lower()
    if not _core._sha256_value(artifact_sha256):
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "digest durable del artefacto ausente o inválido"
        )
    if not _core._sha256_value(package_sha256):
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "SHA-256 interno del paquete territorial ausente o inválido"
        )
    compatibility_identity_sha256 = str(prep.get("compatibility_identity_sha256") or "").lower()
    if not _core._sha256_value(compatibility_identity_sha256):
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "identidad de compatibilidad territorial ausente o inválida"
        )
    try:
        population_year = int(prep.get("population_year"))
        section_year = int(prep.get("section_year"))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "population_year/section_year ausentes o inválidos"
        ) from exc
    declaration_rel = str(state.get("territorial_source_declaration") or "")
    declaration_path = root_dir / declaration_rel if declaration_rel else None
    if declaration_path is None or not declaration_path.is_file():
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "declaración durable de procedencia territorial ausente"
        )
    try:
        declaration = yaml.safe_load(declaration_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "declaración durable de procedencia territorial ilegible"
        ) from exc
    territory = declaration.get("territory") or {}
    if (
        not str(declaration.get("schema") or "").startswith("ddd-territory-sources/")
        or str(territory.get("id") or "") != territory_id
        or str(territory.get("edition") or "") != str(edition)
    ):
        raise ValueError(
            f"CATALOG_SOURCE_BLOCK: {row.get('name') or territory_id}: "
            "procedencia territorial no coincide con territorio/edición"
        )
    return {
        **prep,
        "run_id": run_id,
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256,
        "package_sha256": package_sha256,
        "compatibility_identity_sha256": compatibility_identity_sha256,
        "population_year": population_year,
        "section_year": section_year,
        "source_declaration": declaration_rel,
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
    catalog_source_mode = execution_mode == "catalog_source"
    automatic_continue = bool(
        execution_mode == "reuse"
        and selected_explicit_source is None
        and optimization_algorithm == "Canónico"
        and (
            not force_selected_algorithm
            or state.get("territorial_product_available")
            or state.get("electoral_product_available")
        )
    )
    if catalog_source_mode and selected_explicit_source is not None:
        raise ValueError("CATALOG_SOURCE_BLOCK: el modo de fuente acreditada no admite procedencia reuse_* explícita")
    if catalog_source_mode:
        prep = _catalog_territorial_source(row=row, state=state, edition=edition, root_dir=root_dir)
    elif selected_explicit_source is not None:
        prep = selected_explicit_source
    elif automatic_continue and state.get("territorial_sources_prepared"):
        # En continuidad durable, si existe un producto M06/M08 el manifiesto
        # productor es la autoridad de linaje para la fuente usada. El catálogo
        # puede conservar un run_id histórico desfasado aunque artefacto y SHA
        # sigan identificando la misma fuente.
        prep = dict(catalog_prep)
    else:
        prep = catalog_prep
    last = state.get("last_valid_checkpoint") or {}
    last_run = last.get("run_id")
    try:
        last_num = int(str(last.get("stage") or "").removeprefix("M"))
    except ValueError:
        last_num = 0
    from_start = execution_mode == "from_start"
    if execution_mode not in {"reuse", "from_start", "catalog_source"}:
        raise ValueError(f"Modo de ejecución inválido: {execution_mode}")
    if optimization_algorithm not in {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}:
        raise ValueError(f"Estrategia de optimización inválida: {optimization_algorithm}")
    expected_election_id = _core._registered_election_id(root_dir, row["territory_id"])
    if automatic_continue:
        try:
            durable = validate_durable_assets(
                root_dir=root_dir,
                state=state,
                territory_id=row["territory_id"],
                edition=edition,
                territorial_source=prep if state.get("territorial_sources_prepared") else None,
                expected_election_id=expected_election_id,
            )
        except DurableAssetBlock as exc:
            raise ValueError(f"CONTINUE_DURABLE_BLOCK: {row['name']}: {exc}") from exc
        prep = durable["territorial_source"] or {}
        territorial_evidence = durable["territorial_product"] or {}
        electoral_source_evidence = durable["electoral_source"] or {}
        electoral_product_evidence = durable["electoral_product"] or {}

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

    source_shape_ready = bool(
        source_run_id
        and prep.get("artifact_name")
        and _core._sha256_value(prep.get("artifact_sha256"))
        and _core._sha256_value(prep.get("package_sha256"))
        and _core._sha256_value(prep.get("compatibility_identity_sha256"))
        and isinstance(prep.get("population_year"), int)
        and isinstance(prep.get("section_year"), int)
    )
    territorial_sources_ready = bool(
        source_shape_ready
        and (catalog_source_mode or selected_explicit_source is not None or state.get("territorial_sources_prepared"))
    )
    territorial_product_ready = bool(
        state.get("territorial_product_available")
        and state.get("territorial_certification") in _core.PASS_CERTIFICATIONS
        and territorial_product_run_id and territorial_evidence.get("artifact_sha256")
    )
    electoral_source_identity_ready = (
        expected_election_id is None
        or str(electoral_source_evidence.get("election_id") or "") == expected_election_id
    )
    electoral_source_ready = bool(
        state.get("electoral_source_prepared") and electoral_source_run_id
        and electoral_source_evidence.get("artifact_name") and electoral_source_evidence.get("artifact_sha256")
        and electoral_source_identity_ready
    )
    electoral_product_ready = bool(
        state.get("electoral_product_available") and electoral_product_run_id
        and electoral_product_evidence.get("artifact_sha256")
    )
    recompute_requested = bool(
        optimization_algorithm != "Canónico"
        or (force_selected_algorithm and execution_mode != "reuse")
    )
    generation_requested = bool(
        catalog_source_mode or from_start or selected_explicit_source is not None
        or not territorial_product_ready or recompute_requested
    )
    if catalog_source_mode:
        run_prepare_territorial = False
    elif selected_explicit_source is not None:
        run_prepare_territorial = False
    elif from_start:
        run_prepare_territorial = True
    else:
        # "Continuar": una fuente anterior no es necesaria si ya existe un M06
        # certificado compatible. Sólo se prepara 01 cuando 02 deba ejecutarse.
        run_prepare_territorial = bool(generation_requested and not territorial_sources_ready)
    source_acquisition_planned = bool(run_prepare_territorial and not territorial_sources_ready)
    generation_gate = generation_enablement(
        root_dir=root_dir, contract_path=row.get("contract_path"), territory_id=row["territory_id"],
        certified_product_ready=territorial_product_ready and not generation_requested,
        first_generation_evidence=(
            generation_preflight_evidence
            if territorial_sources_ready and not run_prepare_territorial and generation_requested
            else None
        ),
        preparation_evidence=prep,
        require_source=generation_requested,
        source_acquisition_planned=source_acquisition_planned,
        source_recalculation_planned=catalog_source_mode,
    )
    pre_m04_producer_planned = bool(
        selected_explicit_source is None
        and (
            run_prepare_territorial
            or (territorial_sources_ready and generation_requested and not generation_preflight_path)
        )
    )
    pre_m04_accreditation_planned = bool(
        pre_m04_producer_planned
        and territorial_sources_ready
        and generation_requested
        and not generation_gate.get("allowed")
        and generation_gate.get("capability") == "CAP_PRE_M04_EVIDENCE"
    )
    if pre_m04_accreditation_planned:
        run_prepare_territorial = True
        generation_gate = generation_enablement(
            root_dir=root_dir,
            contract_path=row.get("contract_path"),
            territory_id=row["territory_id"],
            certified_product_ready=False,
            first_generation_evidence=None,
            preparation_evidence=prep,
            require_source=True,
            pre_m04_accreditation_planned=True,
        )
    proposed_generate = bool(generation_requested or run_prepare_territorial)
    if proposed_generate and not generation_gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: {row['name']}: {generation_gate['reason']}")
    run_generate = proposed_generate
    run_prepare_electoral = bool(
        from_start
        or (
            not electoral_source_ready
            and (run_generate or not electoral_product_ready)
        )
    )
    run_incorporate = from_start or run_generate or run_prepare_electoral or not electoral_product_ready
    plan = {
        "schema": "ddd.full-run-plan/1.1", "territory_id": row["territory_id"], "territory_name": row["name"],
        "edition": edition, "contract_path": row.get("contract_path"), "execution_mode": execution_mode,
        "generation_execution_mode": "from_start" if catalog_source_mode else execution_mode,
        "optimization_algorithm": optimization_algorithm, "run_prepare_territorial": run_prepare_territorial,
        "pre_m04_accreditation_planned": pre_m04_accreditation_planned,
        "run_generate": run_generate, "run_prepare_electoral": run_prepare_electoral, "run_incorporate": run_incorporate,
        "existing": {
            "territorial_source": {
                "run_id": source_run_id, "artifact_name": prep.get("artifact_name"),
                "artifact_sha256": prep.get("artifact_sha256"), "package_sha256": prep.get("package_sha256"),
                "source_commit": prep.get("source_commit"), "source_declaration": prep.get("source_declaration"),
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
    first = None if certified_product_ready else catalog_state.get("generation_preflight_evidence") or None
    if first:
        source = first.get("source") or {}
        if (run_id != first.get("run_id") or reuse_artifact_name != source.get("artifact_name")
                or reuse_artifact_sha256 != source.get("artifact_sha256") or reuse_source_sha != first.get("source_commit")):
            raise ValueError("GENERATION_CONTRACT_BLOCK: la fuente explícita no coincide con la procedencia validada para primera generación")
        if source.get("package_sha256"):
            prep["package_sha256"] = source["package_sha256"]
    gate = generation_enablement(
        root_dir=root_dir, contract_path=plan.get("contract_path"), territory_id=plan.get("territory_id", ""),
        certified_product_ready=certified_product_ready,
        first_generation_evidence=first,
        preparation_evidence=prep, require_source=True,
    )
    if not gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: Fuente explícita no habilita generación: {gate['reason']}")
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
    ap.add_argument("--execution-mode", choices=["reuse", "from_start", "catalog_source"], required=True)
    ap.add_argument("--optimization-algorithm", default="Canónico", choices=["Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"])
    ap.add_argument("--reuse-existing-optimization", action="store_true")
    ap.add_argument("--catalog", default="configuracion/catalogo_preparacion.yaml")
    ap.add_argument("--root-dir", default=".")
    ap.add_argument("--output")
    ns = ap.parse_args()
    root = Path(ns.root_dir)
    plan = build_plan(
        territory=ns.territory, edition=ns.edition, execution_mode=ns.execution_mode,
        catalog=root / ns.catalog, root_dir=root, optimization_algorithm=ns.optimization_algorithm,
        force_selected_algorithm=(
            False if ns.execution_mode == "reuse" else not ns.reuse_existing_optimization
        ),
    )
    text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        out = Path(ns.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    main()
