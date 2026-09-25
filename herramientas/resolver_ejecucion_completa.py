from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import yaml

from ddd_core.territory_contract import validate_production_contract
from herramientas.catalogo_preparacion import lookup

PASS_CERTIFICATIONS = {"PASS", "PASS_WITH_EXCEPTIONS", "PASS_WITH_GOVERNED_EXCEPTIONS"}


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()


def _validated_first_generation_preflight(
    *,
    root_dir: Path,
    contract_path: str,
    territory_id: str,
    edition: str,
    contract: dict,
    preparation_evidence: dict | None,
    generation_preflight: dict | None,
) -> dict | None:
    """Validate durable M03/topology evidence for a first territorial product."""
    evidence = generation_preflight or {}
    if not evidence:
        return None

    def blocked(reason: str) -> dict:
        return {
            "allowed": False,
            "reason": f"preflight de primera generación inválido: {reason}",
        }

    if evidence.get("schema") != "ddd.generation-preflight-evidence/1.0":
        return blocked("schema no soportado")
    if evidence.get("decision") != "READY_FOR_FIRST_GENERATION":
        return blocked("decisión distinta de READY_FOR_FIRST_GENERATION")
    if evidence.get("territory_id") != territory_id or str(evidence.get("edition")) != str(edition):
        return blocked("identidad territorio/edición no coincide")

    path = root_dir / contract_path
    contract_ref = evidence.get("contract") or {}
    if contract_ref.get("path") != contract_path:
        return blocked("ruta de contrato no coincide")
    if contract_ref.get("git_blob_sha1") != _git_blob_sha1(path):
        return blocked("huella del contrato vigente no coincide")

    try:
        admission = validate_production_contract(path, expected_territory=territory_id)
    except Exception as exc:
        return blocked(f"contrato no auditable: {exc}")
    if admission.get("status") != "ADMITTED" or not admission.get("production_authorized"):
        return blocked("contrato M01-M06 no admitido/autorizado estructuralmente")

    prep = preparation_evidence or {}
    source = evidence.get("source") or {}
    source_fields = ("run_id", "artifact_name", "artifact_sha256", "package_sha256")
    if any(source.get(key) != prep.get(key) for key in source_fields):
        return blocked("fuente territorial durable no coincide con el catálogo")
    if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("artifact_sha256") or "")):
        return blocked("digest de fuente inválido")
    if not re.fullmatch(r"[0-9a-f]{64}", str(source.get("package_sha256") or "")):
        return blocked("digest del paquete fuente inválido")

    validation = contract.get("validation") or {}
    modules = contract.get("modulos") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    graph = evidence.get("graph") or {}
    if graph.get("run_id") != source.get("run_id"):
        return blocked("M03 no pertenece al mismo run de fuente")
    if graph.get("artifact_name") != f"ddd-state-{source.get('run_id')}-M03":
        return blocked("nombre del checkpoint M03 no coincide")
    if not re.fullmatch(r"[0-9a-f]{64}", str(graph.get("artifact_sha256") or "")):
        return blocked("digest del checkpoint M03 inválido")
    if graph.get("completed_stage") != "M03":
        return blocked("checkpoint no alcanza M03")
    if graph.get("nodes") != validation.get("expected_sections_geometry"):
        return blocked("número de secciones M03 no coincide con contrato")
    if graph.get("population") != validation.get("expected_population_total_2025"):
        return blocked("población M03 no coincide con contrato")
    if graph.get("topology_bridges") != validation.get("expected_topology_bridges"):
        return blocked("pasarelas M03 no coinciden con contrato")
    if not isinstance(graph.get("edges"), int) or graph["edges"] <= 0:
        return blocked("grafo M03 sin aristas acreditadas")
    if graph.get("isolated") != 0 or graph.get("global_components") != 1:
        return blocked("grafo M03 no es una única componente sin aislados")
    if graph.get("province_disconnected") != 0:
        return blocked("M03 mantiene provincias desconectadas")
    if graph.get("municipality_disconnected") != 0:
        return blocked("M03 mantiene municipios desconectados")

    partitioning = evidence.get("partitioning") or {}
    contract_partitioning = contract.get("partitioning") or {}
    active_partitioning = bool(
        isinstance(contract_partitioning, dict)
        and contract_partitioning.get("enabled") is not False
        and str(contract_partitioning.get("strategy") or "").strip()
    )
    if partitioning.get("mode") != "none_required":
        return blocked("modo de particionado pre-M04 no soportado por esta evidencia")
    if active_partitioning:
        return blocked("el contrato exige particionado interno pero la evidencia declara NOOP")
    if partitioning.get("enabled") is not False or partitioning.get("status") != "NOOP":
        return blocked("particionado NOOP no acreditado")
    if partitioning.get("artifact_name") != f"ddd-internal-units-{source.get('run_id')}":
        return blocked("artefacto de particionado no coincide con el run")
    if not re.fullmatch(r"[0-9a-f]{64}", str(partitioning.get("artifact_sha256") or "")):
        return blocked("digest de particionado inválido")
    if m04.get("municipality_field") != validation.get("municipality_field"):
        return blocked("M04 no consume directamente el municipio validado")

    expected_provinces = validation.get("expected_province_codes") or []
    if graph.get("province_groups") != len(expected_provinces):
        return blocked("grupos provinciales M03 no coinciden con contrato")

    return {"allowed": True, "route": "validated_pre_m04_topology"}


def generation_enablement(
    *,
    root_dir: Path,
    contract_path: str | None,
    territory_id: str,
    edition: str = "2025",
    certified_product_ready: bool = False,
    preparation_evidence: dict | None = None,
    generation_preflight: dict | None = None,
) -> dict:
    """Determine generation readiness from structural contract and durable evidence."""
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

    partitioning = contract.get("partitioning") or {}
    if (partitioning.get("enabled") is True
            and partitioning.get("strategy") == "connected_internal_units"
            and partitioning.get("output_geojson")
            and partitioning["output_geojson"] == m04.get("in_geojson")
            and partitioning.get("partition_unit_field")
            and partitioning["partition_unit_field"] == m04.get("municipality_field")):
        return {"allowed": True, "route": "linked_internal_partitioning"}

    k = territory_contract.get("k_districts")
    if (certified_product_ready
            and meta.get("contract_level") == "production_m01_m06"
            and isinstance(k, int) and not isinstance(k, bool) and k > 0
            and m04.get("k_districts") == k
            and m06.get("expected_districts") == k
            and m04.get("out_geojson")
            and m04["out_geojson"] == m05.get("in_geojson")
            and m05.get("out_geojson")
            and m05["out_geojson"] == m06.get("in_geojson")):
        return {"allowed": True, "route": "certified_product_lineage"}

    preflight = _validated_first_generation_preflight(
        root_dir=root_dir,
        contract_path=contract_path,
        territory_id=territory_id,
        edition=str(edition),
        contract=contract,
        preparation_evidence=preparation_evidence,
        generation_preflight=generation_preflight,
    )
    if preflight is not None:
        return preflight

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
    generation_preflight = _load_json(evidence.get("generation_preflight"), root_dir)
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
        edition=edition,
        certified_product_ready=territorial_product_ready,
        preparation_evidence=prep,
        generation_preflight=generation_preflight,
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
            "preparation_evidence": prep,
            "generation_preflight": generation_preflight,
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
    catalog_state = plan.get("catalog_state") or {}
    gate = generation_enablement(
        root_dir=root_dir,
        contract_path=plan.get("contract_path"),
        territory_id=plan.get("territory_id", ""),
        edition=str(plan.get("edition") or "2025"),
        certified_product_ready=bool(catalog_state.get("territorial_product_available")),
        preparation_evidence=catalog_state.get("preparation_evidence"),
        generation_preflight=catalog_state.get("generation_preflight"),
    )
    if not gate["allowed"]:
        raise ValueError(f"GENERATION_CONTRACT_BLOCK: Fuente explícita no habilita generación: {gate['reason']}")
    if gate.get("route") == "validated_pre_m04_topology":
        source = (catalog_state.get("generation_preflight") or {}).get("source") or {}
        expected = (
            str(source.get("run_id") or ""),
            str(source.get("artifact_name") or ""),
            str(source.get("artifact_sha256") or ""),
            str(source.get("source_commit") or ""),
        )
        actual = (
            reuse_run_id,
            reuse_artifact_name,
            reuse_artifact_sha256,
            reuse_source_sha,
        )
        if actual != expected:
            raise ValueError(
                "GENERATION_CONTRACT_BLOCK: Fuente explícita no coincide con el preflight territorial validado"
            )

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
