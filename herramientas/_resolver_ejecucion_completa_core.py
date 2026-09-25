from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

from herramientas.catalogo_preparacion import lookup

PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}
FIRST_GENERATION_EVIDENCE_SCHEMA = "ddd.catalog-evidence/1.0"
FIRST_GENERATION_EVIDENCE_KIND = "generation_preflight"
FIRST_GENERATION_DECISION = "READY_FOR_FIRST_GENERATION"


def _sha256_value(value: object) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", str(value or "")))


def _git_blob_sha1(path: Path) -> str | None:
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _pre_m04_implementation_binding(root_dir: Path) -> dict:
    return {
        "m01_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/01_preparar_base_territorial.py"),
        "m02_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/02_construir_adyacencias.py"),
        "m03_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/03_construir_grafo.py"),
        "partition_preparer_git_blob_sha1": _git_blob_sha1(root_dir / "herramientas/preparar_unidades_internas.py"),
        "partition_builder_git_blob_sha1": _git_blob_sha1(root_dir / "herramientas/construir_unidades_internas_m04.py"),
    }


def _bridge_signature(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    keys = ("u", "v", "admin_scope", "edge_type")
    return [{key: row.get(key) for key in keys} for row in rows if isinstance(row, dict)]


def _contract_generation_binding(contract: dict) -> dict:
    modules = contract.get("modulos") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m03 = modules.get("modulo_03_construir_grafo") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m06 = modules.get("modulo_06_consolidar_distritos") or {}
    territorial = contract.get("territory_contract") or {}
    validation = contract.get("validation") or {}
    return {
        "contract_level": (contract.get("meta") or {}).get("contract_level"),
        "k_districts": territorial.get("k_districts"),
        "population_floor_ratio": territorial.get("population_floor_ratio"),
        "population_cap_ratio": territorial.get("population_cap_ratio"),
        "target_tolerance_ratio": territorial.get("target_tolerance_ratio"),
        "oversized_municipality_rule": territorial.get("oversized_municipality_rule"),
        "municipality_atomicity_limit_ratio": territorial.get("municipality_atomicity_limit_ratio"),
        "m01_output_geojson": m01.get("out_geojson"),
        "m03_output_graph_json": m03.get("out_graph_json"),
        "m04_input_graph_json": m04.get("in_graph_json"),
        "m04_input_geojson": m04.get("in_geojson"),
        "m04_output_geojson": m04.get("out_geojson"),
        "m05_input_graph_json": m05.get("in_graph_json"),
        "m05_input_geojson": m05.get("in_geojson"),
        "m05_output_geojson": m05.get("out_geojson"),
        "m06_input_geojson": m06.get("in_geojson"),
        "m04_municipality_field": m04.get("municipality_field"),
        "m05_municipality_field": m05.get("municipality_field"),
        "m06_municipality_field": m06.get("municipality_field"),
        "validation_municipality_field": validation.get("municipality_field"),
        "expected_districts": validation.get("expected_districts"),
        "require_graph_contiguity": validation.get("require_graph_contiguity"),
        "require_municipality_discipline": validation.get("require_municipality_discipline"),
    }


def _blocked(capability: str, detail: str) -> dict:
    return {"allowed": False, "capability": capability, "reason": f"{capability}: {detail}"}


def _generation_capabilities(contract: dict) -> dict:
    meta = contract.get("meta") or {}
    territorial = contract.get("territory_contract") or {}
    modules = contract.get("modulos") or {}
    validation = contract.get("validation") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m03 = modules.get("modulo_03_construir_grafo") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m06 = modules.get("modulo_06_consolidar_distritos") or {}

    if meta.get("contract_level") != "production_m01_m06" or not all((m01, m02, m03, m04, m05, m06)):
        return _blocked("CAP_CONTRACT", "contrato M01-M06 ausente o incompleto")
    if meta.get("production_authorization") != "AUTHORIZED":
        return _blocked("CAP_CONTRACT", "producción no autorizada por el contrato efectivo")
    k = territorial.get("k_districts")
    if (not isinstance(k, int) or isinstance(k, bool) or k <= 0
            or m04.get("k_districts") != k or m06.get("expected_districts") != k):
        return _blocked("CAP_K", "K ausente o incoherente entre contrato, Formación inicial y Consolidación")
    limits = (territorial.get("population_floor_ratio"), territorial.get("population_cap_ratio"), territorial.get("target_tolerance_ratio"))
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or v <= 0 for v in limits):
        return _blocked("CAP_POPULATION_LIMITS", "suelo, techo o tolerancia poblacional ausentes o inválidos")
    municipality_field = validation.get("municipality_field")
    if (validation.get("require_municipality_discipline") is not True or not municipality_field
            or m04.get("municipality_field") != municipality_field
            or m05.get("municipality_field") != municipality_field
            or m06.get("municipality_field") != municipality_field):
        return _blocked("CAP_ADMIN_POLICY", "disciplina o campo municipal incompletos o incoherentes")
    graph = m03.get("out_graph_json")
    if (not graph or graph != m04.get("in_graph_json") or graph != m05.get("in_graph_json")
            or validation.get("require_graph_contiguity") is not True):
        return _blocked("CAP_GRAPH", "grafo contractual o control de contigüidad incompletos")
    partitioning = contract.get("partitioning") or {}
    if partitioning.get("enabled") is True:
        if (partitioning.get("strategy") != "connected_internal_units"
                or not partitioning.get("output_geojson")
                or partitioning.get("output_geojson") != m04.get("in_geojson")
                or partitioning.get("partition_unit_field") != m04.get("municipality_field")):
            return _blocked("CAP_M04_INPUT", "particionado interno no enlaza con Formación inicial")
    elif not m01.get("out_geojson") or m01.get("out_geojson") != m04.get("in_geojson"):
        return _blocked("CAP_M04_INPUT", "entrada de Formación inicial no es resoluble desde la base territorial")
    if (not m04.get("out_geojson") or m04.get("out_geojson") != m05.get("in_geojson")
            or not m05.get("out_geojson") or m05.get("out_geojson") != m06.get("in_geojson")):
        return _blocked("CAP_GENERATION_CHAIN", "Formación inicial, Optimización y Consolidación no están enlazadas")
    return {"allowed": True}


def _validated_first_generation_preflight(*, contract: dict, evidence: dict, preparation_evidence: dict,
                                          territory_id: str, root_dir: Path) -> dict:
    def blocked(reason: str) -> dict:
        return _blocked("CAP_PRE_M04_EVIDENCE", f"evidencia pre-M04 inválida: {reason}")
    if evidence.get("schema") != FIRST_GENERATION_EVIDENCE_SCHEMA:
        return blocked("schema no reconocido")
    if evidence.get("kind") != FIRST_GENERATION_EVIDENCE_KIND:
        return blocked("kind no reconocido")
    if evidence.get("decision") != FIRST_GENERATION_DECISION or evidence.get("stage") != "M03U":
        return blocked("decisión/etapa no habilitan primera generación")
    if evidence.get("territory_id") != territory_id:
        return blocked("territorio no coincide")
    run_id = evidence.get("run_id")
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        return blocked("run_id inválido")
    source = evidence.get("source") or {}
    if (preparation_evidence.get("run_id") != run_id
            or source.get("artifact_name") != preparation_evidence.get("artifact_name")
            or source.get("artifact_sha256") != preparation_evidence.get("artifact_sha256")
            or source.get("package_sha256") != preparation_evidence.get("package_sha256")):
        return blocked("la fuente preparada no coincide con la evidencia topológica")
    if not _sha256_value(source.get("artifact_sha256")) or not _sha256_value(source.get("package_sha256")):
        return blocked("SHA-256 de fuente inválido")
    if not re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("source_commit") or "")):
        return blocked("source_commit inválido")
    if evidence.get("implementation") != _pre_m04_implementation_binding(root_dir):
        return blocked("la implementación pre-M04 cambió respecto a la evidencia")
    if evidence.get("contract_binding") != _contract_generation_binding(contract):
        return blocked("el contrato de generación cambió respecto a la evidencia")
    modules = contract.get("modulos") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    validation = contract.get("validation") or {}
    expected_adjacency = {
        "predicate": m02.get("predicate"), "working_crs": m02.get("working_crs"),
        "min_shared_border_m": m02.get("min_shared_border_m"),
        "max_precision_overlap_area_m2": m02.get("max_precision_overlap_area_m2"),
        "buffer_m": m02.get("buffer_m"), "simplify_m": m02.get("simplify_m"),
        "topology_bridges": _bridge_signature(m02.get("topology_bridges") or []),
    }
    if (evidence.get("adjacency") or {}) != expected_adjacency:
        return blocked("la política de adyacencia/grafo no coincide")
    graph = evidence.get("graph") or {}
    if graph.get("artifact_name") != f"ddd-state-{run_id}-M03" or not _sha256_value(graph.get("artifact_sha256")):
        return blocked("artefacto M03 no es identificable")
    if graph.get("nodes") != validation.get("expected_sections_geometry"):
        return blocked("número de secciones del grafo no coincide")
    if graph.get("population") != validation.get("expected_population_total_2025"):
        return blocked("población del grafo no coincide")
    if (graph.get("isolated") != 0 or graph.get("global_components") != 1
            or graph.get("province_disconnected") != 0 or graph.get("municipality_disconnected") != 0):
        return blocked("grafo territorial no supera conectividad administrativa")
    partitioning = evidence.get("partitioning") or {}
    if evidence.get("artifact_name") != f"ddd-state-{run_id}-M03U" or not _sha256_value(evidence.get("artifact_sha256")):
        return blocked("artefacto M03U no es identificable")
    if (partitioning.get("job_artifact_name") != f"ddd-internal-units-{run_id}"
            or not _sha256_value(partitioning.get("job_artifact_sha256"))):
        return blocked("evidencia del paso de particionado no es identificable")
    policy = contract.get("partitioning") or {}
    if partitioning.get("status") == "NOOP":
        m01 = modules.get("modulo_01_preparar_base_territorial") or {}
        if (policy and policy.get("enabled") is not False and str(policy.get("strategy") or "").strip()):
            return blocked("la evidencia dice NOOP pero el contrato declara particionado")
        if (partitioning.get("strategy") is not None
                or partitioning.get("contract_output_geojson") != m04.get("in_geojson")
                or m04.get("in_geojson") != m01.get("out_geojson")):
            return blocked("NOOP no coincide con la entrada contractual de M04")
    elif partitioning.get("status") == "PREPARED":
        if (policy.get("enabled") is not True or policy.get("strategy") != "connected_internal_units"
                or partitioning.get("strategy") != "connected_internal_units"
                or policy.get("output_geojson") != m04.get("in_geojson")
                or policy.get("partition_unit_field") != m04.get("municipality_field")):
            return blocked("particionado materializado no coincide con el contrato")
    else:
        return blocked("estado de particionado no reconocido")
    return {"allowed": True, "route": "validated_pre_m04_topology"}


def generation_enablement(*, root_dir: Path, contract_path: str | None, territory_id: str,
                          certified_product_ready: bool = False, first_generation_evidence: dict | None = None,
                          preparation_evidence: dict | None = None, require_source: bool = False,
                          source_acquisition_planned: bool = False) -> dict:
    path = root_dir / contract_path if contract_path else None
    if path is None or not path.is_file():
        return _blocked("CAP_CONTRACT", "contrato territorial efectivo ausente")
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return _blocked("CAP_CONTRACT", "contrato territorial efectivo ilegible")
    if not isinstance(contract, dict) or (contract.get("meta") or {}).get("territory_id") != territory_id:
        return _blocked("CAP_CONTRACT", "identidad del contrato territorial no coincide")
    capability_gate = _generation_capabilities(contract)
    if not capability_gate["allowed"]:
        return capability_gate
    prep = preparation_evidence or {}
    if require_source and not source_acquisition_planned:
        if (not isinstance(prep.get("run_id"), int) or isinstance(prep.get("run_id"), bool)
                or prep.get("run_id") <= 0 or not prep.get("artifact_name") or not _sha256_value(prep.get("artifact_sha256"))):
            return _blocked("CAP_SOURCE", "fuente territorial no acreditada por run, artefacto y SHA-256")
    if first_generation_evidence:
        return _validated_first_generation_preflight(
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
    return _blocked("CAP_PRE_M04_EVIDENCE", "primera generación sin evidencia durable pre-M04")


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
    match = re.search(r"-(\d+)-M\d+$", artifact_name) or re.search(r"-(\d+)$", artifact_name)
    if match:
        return int(match.group(1))
    try:
        return int(fallback) if fallback not in (None, "") else None
    except (TypeError, ValueError):
        return None


def build_plan(*, territory: str, edition: str, execution_mode: str, catalog: Path, root_dir: Path,
               optimization_algorithm: str = "Canónico", force_selected_algorithm: bool = False) -> dict:
    row = lookup(territory, edition, catalog)
    state = row
    evidence = state.get("evidence") or {}
    territorial_evidence = _load_json(evidence.get("territorial_product"), root_dir)
    electoral_source_evidence = _load_json(evidence.get("electoral_source"), root_dir)
    electoral_product_evidence = _load_json(evidence.get("electoral_product"), root_dir)
    generation_preflight_path = evidence.get("generation_preflight")
    generation_preflight_evidence = _load_json(generation_preflight_path, root_dir)
    if generation_preflight_path and not generation_preflight_evidence:
        generation_preflight_evidence = {"_load_error": f"no se pudo leer {generation_preflight_path}"}
    prep = state.get("preparation_evidence") or {}
    last = state.get("last_valid_checkpoint") or {}
    last_run = last.get("run_id")
    try:
        last_num = int(str(last.get("stage") or "").removeprefix("M"))
    except ValueError:
        last_num = 0
    source_run_id = _run_from_artifact(prep.get("artifact_name"), prep.get("run_id"))
    territorial_product_run_id = _run_from_artifact(territorial_evidence.get("artifact_name"), territorial_evidence.get("run_id") or (last_run if last_num >= 6 else None))
    territorial_product_artifact = territorial_evidence.get("artifact_name") or (f"ddd-state-{territorial_product_run_id}-M06" if territorial_product_run_id else None)
    electoral_source_run_id = _run_from_artifact(electoral_source_evidence.get("artifact_name"), electoral_source_evidence.get("run_id"))
    electoral_product_run_id = _run_from_artifact(electoral_product_evidence.get("artifact_name"), electoral_product_evidence.get("run_id") or (last_run if last_num >= 8 else None))
    electoral_product_artifact = electoral_product_evidence.get("artifact_name") or (f"ddd-state-{electoral_product_run_id}-M08" if electoral_product_run_id else None)
    from_start = execution_mode == "from_start"
    if execution_mode not in {"reuse", "from_start"}:
        raise ValueError(f"Modo de ejecución inválido: {execution_mode}")
    if optimization_algorithm not in {"Canónico", "GerryChain", "GerryChain 25", "GerryChain 50"}:
        raise ValueError(f"Estrategia de optimización inválida: {optimization_algorithm}")
    territorial_sources_ready = bool(state.get("territorial_sources_prepared") and source_run_id and prep.get("artifact_name") and prep.get("artifact_sha256"))
    territorial_product_ready = bool(state.get("territorial_product_available") and state.get("territorial_certification") in PASS_CERTIFICATIONS and territorial_product_run_id and territorial_evidence.get("artifact_sha256"))
    electoral_source_ready = bool(state.get("electoral_source_prepared") and electoral_source_run_id and electoral_source_evidence.get("artifact_name") and electoral_source_evidence.get("artifact_sha256"))
    electoral_product_ready = bool(state.get("electoral_product_available") and electoral_product_run_id and electoral_product_evidence.get("artifact_sha256"))
    run_prepare_territorial = from_start or not territorial_sources_ready
    generation_gate = generation_enablement(
        root_dir=root_dir, contract_path=row.get("contract_path"), territory_id=row["territory_id"],
        certified_product_ready=territorial_product_ready,
        first_generation_evidence=(generation_preflight_evidence if territorial_sources_ready and not run_prepare_territorial and not territorial_product_ready else None),
        preparation_evidence=prep, require_source=True, source_acquisition_planned=run_prepare_territorial,
    )
    proposed_generate = bool(from_start or run_prepare_territorial or not territorial_product_ready or optimization_algorithm != "Canónico" or force_selected_algorithm)
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
            "territorial_source": {"run_id": source_run_id, "artifact_name": prep.get("artifact_name"), "artifact_sha256": prep.get("artifact_sha256"), "decision": "VALIDADO" if territorial_sources_ready else None},
            "territorial_product": {"run_id": territorial_product_run_id, "artifact_name": territorial_product_artifact, "artifact_sha256": territorial_evidence.get("artifact_sha256"), "decision": territorial_evidence.get("decision")},
            "electoral_source": {"run_id": electoral_source_run_id, "artifact_name": electoral_source_evidence.get("artifact_name"), "artifact_sha256": electoral_source_evidence.get("artifact_sha256"), "election_id": electoral_source_evidence.get("election_id"), "decision": "VALIDADO" if electoral_source_ready else None},
            "electoral_product": {"run_id": electoral_product_run_id, "artifact_name": electoral_product_artifact, "artifact_sha256": electoral_product_evidence.get("artifact_sha256"), "decision": "VALIDADO" if electoral_product_ready else None},
        },
        "generation_gate": generation_gate,
        "catalog_state": {"territorial_sources_prepared": territorial_sources_ready, "territorial_product_available": territorial_product_ready,
                          "electoral_source_prepared": electoral_source_ready, "electoral_product_available": electoral_product_ready,
                          "territorial_certification": state.get("territorial_certification"), "preparation_evidence": prep,
                          "generation_preflight_evidence": generation_preflight_evidence, "generation_preflight_path": generation_preflight_path},
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


def resolve_publication_mode(plan: dict, requested_mode: str, *, root_dir: Path) -> str:
    if requested_mode not in {"electoral", "territorial_only"}:
        raise ValueError(f"publication_mode inválido: {requested_mode}")
    if requested_mode == "territorial_only" or not plan.get("run_prepare_electoral"):
        return requested_mode
    from herramientas.resolver_eleccion_vigente import resolve as resolve_current_election
    try:
        resolve_current_election(str(plan.get("territory_name") or plan.get("territory_id") or ""), root_dir=root_dir, edition=str(plan.get("edition") or ""))
    except SystemExit as exc:
        if str(exc).startswith("No existe elección resoluble para territorio="):
            return "territorial_only"
        raise
    return requested_mode


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
    if not reuse_run_id.isdecimal() or int(reuse_run_id) <= 0:
        raise ValueError("reuse_run_id inválido")
    if not _sha256_value(reuse_artifact_sha256):
        raise ValueError("reuse_artifact_sha256 inválido")
    if not re.fullmatch(r"[0-9a-f]{40}", reuse_source_sha):
        raise ValueError("reuse_source_sha inválido")
    catalog_state = plan.get("catalog_state") or {}
    certified_product_ready = bool(catalog_state.get("territorial_product_available"))
    prep = catalog_state.get("preparation_evidence") or {"run_id": int(reuse_run_id), "artifact_name": reuse_artifact_name, "artifact_sha256": reuse_artifact_sha256}
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
        if (int(reuse_run_id) != first.get("run_id") or reuse_artifact_name != source.get("artifact_name")
                or reuse_artifact_sha256 != source.get("artifact_sha256") or reuse_source_sha != first.get("source_commit")):
            raise ValueError("GENERATION_CONTRACT_BLOCK: la fuente explícita no coincide con la procedencia validada para primera generación")
    plan["execution_mode"] = "from_start"
    plan["run_prepare_territorial"] = False
    plan["run_generate"] = True
    plan["existing"]["territorial_source"] = {"run_id": int(reuse_run_id), "artifact_name": reuse_artifact_name, "artifact_sha256": reuse_artifact_sha256, "source_commit": reuse_source_sha}
    if campaign_instance:
        plan["campaign"]["reuse"] = {"run_id": int(reuse_run_id), "artifact_name": reuse_artifact_name,
                                      "artifact_sha256": reuse_artifact_sha256, "source_sha": reuse_source_sha,
                                      "expected_population_total": int(expected_population), "expected_section_count": int(expected_sections),
                                      "expected_district_count": int(expected_districts), "expected_certification": expected_certification}
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
    plan = build_plan(territory=ns.territory, edition=ns.edition, execution_mode=ns.execution_mode,
                      catalog=root / ns.catalog, root_dir=root, optimization_algorithm=ns.optimization_algorithm,
                      force_selected_algorithm=not ns.reuse_existing_optimization)
    text = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        out = Path(ns.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False))


if __name__ == "__main__":
    main()
