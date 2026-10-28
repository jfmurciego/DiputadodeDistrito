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
PRE_GRAPH_AUDIT_FIELDS_M03_BLOB_SHA1 = "c2c928d1e21d3b486ee3e9975eace18364bd3176"
PRE_STRICT_TERRITORIAL_M01_BLOB_SHA1 = "54a4a39de89a53f21a323d36e351b815b0fb0a1f"
PRE_STRICT_TERRITORIAL_M03_BLOB_SHA1 = "776f25060c7668475f6d8ec33a0e2c37a65e4aea"


def _sha256_value(value: object) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{64}", str(value or "")))


def _registered_election_id(root_dir: Path, territory_id: str) -> str | None:
    path = root_dir / "configuracion" / "registro_electoral.yaml"
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    row = (data.get("territories") or {}).get(territory_id)
    if not isinstance(row, dict):
        return None
    election_id = str(row.get("election_id") or "")
    return election_id or None


def _git_blob_sha1(path: Path) -> str | None:
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _pre_m04_implementation_binding(root_dir: Path, contract: dict | None = None) -> dict:
    binding = {
        "m01_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/01_preparar_base_territorial.py"),
        "m02_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/02_construir_adyacencias.py"),
        "m03_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/03_construir_grafo.py"),
        "partition_preparer_git_blob_sha1": _git_blob_sha1(root_dir / "herramientas/preparar_unidades_internas.py"),
        "partition_builder_git_blob_sha1": _git_blob_sha1(root_dir / "herramientas/construir_unidades_internas_m04.py"),
    }
    if contract and ((contract.get("validation") or {}).get("hard_partition_mode") == "physical_components"):
        binding.update({
            "physical_partition_preparer_git_blob_sha1": _git_blob_sha1(
                root_dir / "herramientas/preparar_particiones_fisicas_m04.py"
            ),
            "m04_entrypoint_git_blob_sha1": _git_blob_sha1(root_dir / "modulos/04_generar_semillas.py"),
        })
    return binding


def _bridge_signature(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    keys = ("u", "v", "admin_scope", "edge_type")
    return [{key: row.get(key) for key in keys} for row in rows if isinstance(row, dict)]


def _pre_m04_implementation_matches(observed: object, expected: dict, *, hard_partition: bool) -> bool:
    if observed == expected:
        return True
    if not isinstance(observed, dict):
        return False

    # No se acepta deriva arbitraria. Sólo son compatibles las versiones
    # conocidas cuya diferencia consiste en endurecer la validación de entrada;
    # los módulos de topología/particionado y el resto del binding deben ser
    # exactamente los mismos.
    for key, expected_value in expected.items():
        observed_value = observed.get(key)
        if key == "m01_git_blob_sha1":
            if observed_value not in {
                expected_value,
                PRE_STRICT_TERRITORIAL_M01_BLOB_SHA1,
            }:
                return False
            continue
        if key == "m03_git_blob_sha1":
            if observed_value not in {
                expected_value,
                PRE_STRICT_TERRITORIAL_M03_BLOB_SHA1,
                PRE_GRAPH_AUDIT_FIELDS_M03_BLOB_SHA1,
            }:
                return False
            continue
        if observed_value != expected_value:
            return False

    # Una evidencia no puede omitir ni añadir componentes de implementación,
    # especialmente los de partición física de archipiélagos.
    return set(observed) == set(expected)



def _effective_physical_source_identity(contract: dict) -> dict:
    """Resolve the material territorial identity that selects a physical inventory."""
    meta = contract.get("meta") or {}
    validation = contract.get("validation") or {}
    baseline = validation.get("source_baseline") or {}
    state = contract.get("generation_state") or {}
    territory_id = str(meta.get("territory_id") or "")
    edition = str(meta.get("year") or baseline.get("edition") or "")
    try:
        population_year = int(baseline.get("population_year") or meta.get("source_population_year"))
        section_year = int(baseline.get("section_year") or meta.get("source_section_year"))
    except (TypeError, ValueError):
        raise ValueError("SOURCE_IDENTITY_MISMATCH: physical_components sin años materiales de fuente")

    package_sha256 = str(baseline.get("package_sha256") or state.get("package_sha256") or "").lower()
    compatibility_identity_sha256 = str(
        baseline.get("compatibility_identity_sha256")
        or state.get("compatibility_identity_sha256")
        or ""
    ).lower()
    if not territory_id or not edition or not _sha256_value(package_sha256):
        raise ValueError("SOURCE_IDENTITY_MISMATCH: physical_components sin identidad de paquete durable")
    if compatibility_identity_sha256 and not _sha256_value(compatibility_identity_sha256):
        raise ValueError("SOURCE_IDENTITY_MISMATCH: identidad de compatibilidad territorial inválida")

    section_rows = [
        row for row in (state.get("source_inputs") or [])
        if isinstance(row, dict)
        and (
            str(row.get("source_id") or "") == "secciones_censales"
            or str(row.get("role") or "") == "target_sectioning"
            or str(row.get("path") or "").endswith(f"seccionado_{section_year}.zip")
        )
    ]
    section_hashes = {
        str(row.get("sha256") or "").lower()
        for row in section_rows
        if _sha256_value(str(row.get("sha256") or "").lower())
    }
    if len(section_hashes) != 1:
        raise ValueError(
            "SOURCE_IDENTITY_MISMATCH: physical_components requiere un único SHA-256 del seccionado efectivo"
        )
    sectioning_sha256 = next(iter(section_hashes))

    payload = {
        "territory_id": territory_id,
        "edition": edition,
        "population_year": population_year,
        "section_year": section_year,
        "package_sha256": package_sha256,
    }
    if compatibility_identity_sha256:
        payload["compatibility_identity_sha256"] = compatibility_identity_sha256
    territorial_identity_sha256 = hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    declared_identity = str(state.get("territorial_identity_sha256") or "").lower()
    if declared_identity and declared_identity != territorial_identity_sha256:
        raise ValueError("SOURCE_IDENTITY_MISMATCH: identidad territorial declarada contradice la fuente efectiva")

    return {
        **payload,
        "sectioning_sha256": sectioning_sha256,
        "territorial_identity_sha256": territorial_identity_sha256,
    }


def _hard_partition_spec(contract: dict, root_dir: Path) -> dict | None:
    """Resolve and validate the durable physical-component input declared for M04."""
    modules = contract.get("modulos") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    validation = contract.get("validation") or {}
    mode = validation.get("hard_partition_mode")
    if not mode:
        return None
    if mode != "physical_components":
        raise ValueError(f"hard_partition_mode no soportado: {mode!r}")
    partitioning = contract.get("partitioning") or {}
    if partitioning.get("enabled") is True:
        raise ValueError("particionado físico y unidades internas no pueden estar activos simultáneamente")

    territory_id = str((contract.get("meta") or {}).get("territory_id") or "")
    source_geojson = m04.get("source_geojson")
    input_geojson = m04.get("in_geojson")
    lookup_raw = m04.get("hard_partition_lookup")
    if (not territory_id or not source_geojson or source_geojson != m01.get("out_geojson")
            or not input_geojson or input_geojson == source_geojson):
        raise ValueError("la derivación física no enlaza fuente territorial y entrada de Formación inicial")
    if (not lookup_raw or lookup_raw != validation.get("hard_partition_lookup")
            or m04.get("hard_partition_territory_id") != territory_id):
        raise ValueError("lookup físico ausente o no enlazado con el territorio efectivo")
    if (m04.get("district_apportionment") != "hamilton_components"
            or validation.get("province_apportionment") != "hamilton_components"):
        raise ValueError("reparto DDD por componentes no está declarado como Hamilton")
    if (m04.get("province_field") != validation.get("province_field")
            or m04.get("municipality_field") != validation.get("municipality_field")):
        raise ValueError("campos físicos de Formación inicial no coinciden con validación")
    if m02.get("topology_bridges") not in ([], None):
        raise ValueError("un contrato de componentes físicos no puede introducir puentes topológicos")

    lookup_path = root_dir / str(lookup_raw)
    if not lookup_path.is_file():
        raise ValueError("lookup físico durable inexistente")
    try:
        payload = json.loads(lookup_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("lookup físico durable ilegible") from exc
    territory = (payload.get("territories") or {}).get(territory_id)
    if not isinstance(territory, dict) or territory.get("partition_mode") != "physical_components":
        raise ValueError("lookup físico no contiene el territorio/modo esperados")
    components = territory.get("components") or {}
    if not isinstance(components, dict) or not components:
        raise ValueError("lookup físico sin componentes")
    provinces_by_component = {}
    for key, row in components.items():
        if not isinstance(row, dict):
            raise ValueError(f"componente física inválida: {key}")
        province = str(row.get("province_code") or "")
        name = str(row.get("name") or "").strip()
        if not province or not name:
            raise ValueError(f"componente física sin identidad estable válida: {key}")
        provinces_by_component[str(key)] = province
    component_ids = set(provinces_by_component)
    declared_component_count = territory.get("physical_component_count")
    if declared_component_count != len(component_ids):
        raise ValueError("número físico de componentes no coincide con su definición estable")

    source_identity = _effective_physical_source_identity(contract)
    inventories = territory.get("inventories") or []
    if not isinstance(inventories, list) or not inventories:
        raise ValueError("SOURCE_IDENTITY_MISMATCH: lookup físico sin inventarios acreditados")
    matches = [
        row for row in inventories
        if isinstance(row, dict)
        and int(row.get("section_year") or 0) == source_identity["section_year"]
        and str(row.get("sectioning_sha256") or "").lower() == source_identity["sectioning_sha256"]
        and str(row.get("territorial_identity_sha256") or "").lower()
            == source_identity["territorial_identity_sha256"]
    ]
    if len(matches) != 1:
        raise ValueError(
            "SOURCE_IDENTITY_MISMATCH: no existe inventario físico acreditado para "
            f"section_year={source_identity['section_year']} "
            f"sectioning_sha256={source_identity['sectioning_sha256']} "
            f"territorial_identity_sha256={source_identity['territorial_identity_sha256']}"
        )
    inventory = matches[0]
    if (
        inventory.get("source_package_sha256")
        and str(inventory.get("source_package_sha256") or "").lower() != source_identity["package_sha256"]
    ):
        raise ValueError("SOURCE_IDENTITY_MISMATCH: inventario físico ligado a otro paquete territorial")

    section_counts = {
        str(k): int(v) for k, v in (inventory.get("component_sections") or {}).items()
        if isinstance(v, int) and not isinstance(v, bool)
    }
    component_hashes = {
        str(k): str(v).lower()
        for k, v in (inventory.get("component_cusec_set_sha256") or {}).items()
    }
    universe_count = inventory.get("universe_section_count")
    universe_hash = str(inventory.get("universe_cusec_set_sha256") or "").lower()
    if (
        set(section_counts) != component_ids
        or any(v <= 0 for v in section_counts.values())
        or set(component_hashes) != component_ids
        or any(not _sha256_value(v) for v in component_hashes.values())
        or not isinstance(universe_count, int)
        or isinstance(universe_count, bool)
        or universe_count != sum(section_counts.values())
        or not _sha256_value(universe_hash)
    ):
        raise ValueError("inventario físico acreditado incompleto o inconsistente")
    municipality_map = {str(k): str(v) for k, v in (territory.get("municipality_to_partition") or {}).items()}
    overrides = {str(k): str(v) for k, v in (territory.get("section_overrides") or {}).items()}
    if not municipality_map or any(v not in component_ids for v in municipality_map.values()):
        raise ValueError("lookup físico contiene mapeo municipal incompleto o ajeno a sus componentes")
    if any(v not in component_ids for v in overrides.values()):
        raise ValueError("lookup físico contiene override de sección ajeno a sus componentes")

    quotas = validation.get("province_districts") or {}
    populations = validation.get("partition_populations") or {}
    audit = validation.get("partition_apportionment_audit") or {}
    if set(map(str, quotas)) != component_ids or set(map(str, populations)) != component_ids or set(map(str, audit)) != component_ids:
        raise ValueError("particiones, poblaciones, reparto DDD y auditoría no cubren exactamente las componentes físicas")
    k = (contract.get("territory_contract") or {}).get("k_districts")
    if (not isinstance(k, int) or isinstance(k, bool)
            or any(not isinstance(v, int) or isinstance(v, bool) or v <= 0 for v in quotas.values())
            or sum(quotas.values()) != k):
        raise ValueError("reparto DDD por componentes no conserva K")

    required_exempt = set()
    for key in component_ids:
        row = audit.get(key) or {}
        if row.get("population") != populations.get(key) or row.get("districts") != quotas.get(key):
            raise ValueError(f"auditoría de reparto inconsistente para {key}")
        if row.get("floor_exception_required") is True:
            required_exempt.add(key)
            if row.get("floor_exception_governed") is not True:
                raise ValueError(f"excepción de suelo no gobernada para {key}")
    if set(validation.get("population_floor_exempt_partitions") or []) != required_exempt:
        raise ValueError("excepciones de suelo no coinciden con la auditoría de componentes")

    province_groups = {}
    for key, province in provinces_by_component.items():
        province_groups.setdefault(province, set()).add(key)
    expected_province_disconnected = sum(1 for values in province_groups.values() if len(values) > 1)
    municipality_components = {mun: {component} for mun, component in municipality_map.items()}
    for section, component in overrides.items():
        municipality = section[:5]
        municipality_components.setdefault(municipality, set()).add(component)
    expected_municipality_disconnected = sum(1 for values in municipality_components.values() if len(values) > 1)

    return {
        "mode": "physical_components",
        "lookup": str(lookup_raw),
        "lookup_sha256": hashlib.sha256(lookup_path.read_bytes()).hexdigest(),
        "territory_id": territory_id,
        "source_geojson": source_geojson,
        "input_geojson": input_geojson,
        "partition_field": m04.get("province_field"),
        "municipality_field": m04.get("municipality_field"),
        "inventory_id": str(inventory.get("inventory_id") or ""),
        "source_identity": source_identity,
        "component_sections": section_counts,
        "component_cusec_set_sha256": component_hashes,
        "universe_cusec_set_sha256": universe_hash,
        "component_populations": {str(k): int(v) for k, v in populations.items()},
        "component_districts": {str(k): int(v) for k, v in quotas.items()},
        "expected_graph_nodes": universe_count,
        "expected_graph_population": sum(int(v) for v in populations.values()),
        "expected_global_components": len(component_ids),
        "expected_isolated": sum(1 for v in section_counts.values() if v == 1),
        "expected_province_disconnected": expected_province_disconnected,
        "expected_municipality_disconnected": expected_municipality_disconnected,
    }


def _contract_generation_binding(contract: dict) -> dict:
    modules = contract.get("modulos") or {}
    m01 = modules.get("modulo_01_preparar_base_territorial") or {}
    m03 = modules.get("modulo_03_construir_grafo") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}
    m05 = modules.get("modulo_05_optimizar_distritos") or {}
    m06 = modules.get("modulo_06_consolidar_distritos") or {}
    territorial = contract.get("territory_contract") or {}
    validation = contract.get("validation") or {}
    meta = contract.get("meta") or {}
    binding = {
        "contract_level": meta.get("contract_level"),
        "edition": meta.get("year"),
        "population_year": meta.get("source_population_year"),
        "section_year": meta.get("source_section_year"),
        "source_baseline": validation.get("source_baseline"),
        "topology_accreditation": validation.get("topology_accreditation"),
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
    if validation.get("hard_partition_mode") == "physical_components":
        binding["hard_partition_input"] = {
            "mode": validation.get("hard_partition_mode"),
            "lookup": validation.get("hard_partition_lookup"),
            "partition_populations": validation.get("partition_populations"),
            "component_districts": validation.get("province_districts"),
            "partition_apportionment_audit": validation.get("partition_apportionment_audit"),
            "population_floor_exempt_partitions": validation.get("population_floor_exempt_partitions"),
            "source_geojson": m04.get("source_geojson"),
            "input_geojson": m04.get("in_geojson"),
            "partition_field": m04.get("province_field"),
            "municipality_field": m04.get("municipality_field"),
            "district_apportionment": m04.get("district_apportionment"),
            "hard_partition_territory_id": m04.get("hard_partition_territory_id"),
        }
    return binding


def _blocked(capability: str, detail: str) -> dict:
    return {"allowed": False, "capability": capability, "reason": f"{capability}: {detail}"}


def _generation_capabilities(contract: dict, root_dir: Path | None = None) -> dict:
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
    if (validation.get("hard_partition_mode") == "physical_components"):
        if root_dir is None:
            return _blocked("CAP_M04_INPUT", "la entrada física requiere resolver su evidencia durable")
        try:
            _hard_partition_spec(contract, root_dir)
        except ValueError as exc:
            return _blocked("CAP_M04_INPUT", str(exc))
    elif partitioning.get("enabled") is True:
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
    source_run_id = source.get("run_id", run_id)
    identity_fields = (
        "artifact_name",
        "artifact_sha256",
        "package_sha256",
        "compatibility_identity_sha256",
        "population_year",
        "section_year",
    )
    if preparation_evidence.get("run_id") != source_run_id or any(
        str(source.get(key) or "") != str(preparation_evidence.get(key) or "")
        for key in identity_fields
    ):
        return blocked("la fuente preparada no coincide con la evidencia topológica")
    if not _sha256_value(source.get("artifact_sha256")) or not _sha256_value(source.get("package_sha256")):
        return blocked("SHA-256 de fuente inválido")
    if not _sha256_value(source.get("compatibility_identity_sha256")):
        return blocked("identidad de compatibilidad de fuente inválida")
    if not re.fullmatch(r"[0-9a-f]{40}", str(evidence.get("source_commit") or "")):
        return blocked("source_commit inválido")
    generation_state = contract.get("generation_state") or {}
    if generation_state.get("generation_enabled") is True:
        if (
            int(generation_state.get("pre_m04_run_id") or 0) != run_id
            or str(generation_state.get("pre_m04_source_commit") or "") != str(evidence.get("source_commit") or "")
            or str(generation_state.get("pre_m04_artifact_sha256") or "").removeprefix("sha256:")
                != str(evidence.get("artifact_sha256") or "").removeprefix("sha256:")
        ):
            return blocked("run/revisión/digest pre-M04 no coinciden con la habilitación registrada")
    expected_implementation = _pre_m04_implementation_binding(root_dir, contract)
    hard_partition_declared = ((contract.get("validation") or {}).get("hard_partition_mode") == "physical_components")
    if not _pre_m04_implementation_matches(
        evidence.get("implementation"), expected_implementation, hard_partition=hard_partition_declared
    ):
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
    try:
        hard_partition = _hard_partition_spec(contract, root_dir)
    except ValueError as exc:
        return blocked(str(exc))
    if hard_partition:
        if graph.get("nodes") != hard_partition["expected_graph_nodes"]:
            return blocked("número de secciones del grafo no coincide con las componentes físicas")
        if graph.get("population") != hard_partition["expected_graph_population"]:
            return blocked("población del grafo no coincide con el reparto físico acreditado")
        baseline = validation.get("source_baseline") or {}
        if (
            baseline.get("schema") != "ddd.source-baseline/1.0"
            or baseline.get("target_section_count") != hard_partition["expected_graph_nodes"]
            or baseline.get("population_total") != hard_partition["expected_graph_population"]
            or str(baseline.get("package_sha256") or "") != str(source.get("package_sha256") or "")
            or str(baseline.get("compatibility_identity_sha256") or "") != str(source.get("compatibility_identity_sha256") or "")
        ):
            return blocked("baseline físico no está ligado a la fuente acreditada")
        expected_graph = (
            hard_partition["expected_isolated"],
            hard_partition["expected_global_components"],
            hard_partition["expected_province_disconnected"],
            hard_partition["expected_municipality_disconnected"],
        )
        actual_graph = (
            graph.get("isolated"), graph.get("global_components"),
            graph.get("province_disconnected"), graph.get("municipality_disconnected"),
        )
        if actual_graph != expected_graph:
            return blocked("componentes físicas del grafo no coinciden con el lookup durable")
    else:
        baseline = validation.get("source_baseline") or {}
        if (
            baseline.get("schema") != "ddd.source-baseline/1.0"
            or str(baseline.get("package_sha256") or "") != str(source.get("package_sha256") or "")
            or str(baseline.get("compatibility_identity_sha256") or "") != str(source.get("compatibility_identity_sha256") or "")
            or int(baseline.get("population_year") or 0) != int(source.get("population_year") or 0)
            or int(baseline.get("section_year") or 0) != int(source.get("section_year") or 0)
        ):
            return blocked("baseline del contrato no está ligado a la fuente acreditada")
        if graph.get("nodes") != baseline.get("target_section_count"):
            return blocked("número de secciones del grafo no coincide con el baseline de fuente")
        if graph.get("population") != baseline.get("population_total"):
            return blocked("población del grafo no coincide con el baseline de fuente")
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
    if hard_partition:
        if (partitioning.get("status") != "PREPARED"
                or partitioning.get("strategy") != "physical_components"
                or partitioning.get("contract_output_geojson") != m04.get("in_geojson")
                or partitioning.get("resolved_output_geojson") is None
                or partitioning.get("hard_partition_lookup") != hard_partition["lookup"]
                or partitioning.get("hard_partition_lookup_sha256") != hard_partition["lookup_sha256"]
                or partitioning.get("inventory_id") != hard_partition["inventory_id"]
                or partitioning.get("source_identity") != hard_partition["source_identity"]
                or partitioning.get("partition_field") != hard_partition["partition_field"]
                or partitioning.get("municipality_field") != hard_partition["municipality_field"]
                or partitioning.get("input_section_count") != hard_partition["expected_graph_nodes"]
                or partitioning.get("output_section_count") != hard_partition["expected_graph_nodes"]
                or partitioning.get("input_output_cusec_equal") is not True
                or partitioning.get("universe_cusec_set_sha256") != hard_partition["universe_cusec_set_sha256"]
                or partitioning.get("component_sections") != hard_partition["component_sections"]
                or partitioning.get("component_cusec_set_sha256") != hard_partition["component_cusec_set_sha256"]
                or partitioning.get("component_districts") != hard_partition["component_districts"]):
            return blocked("particionado físico materializado no coincide con contrato, lookup y reparto DDD")
    elif partitioning.get("status") == "NOOP":
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
                          source_acquisition_planned: bool = False,
                          pre_m04_accreditation_planned: bool = False,
                          source_recalculation_planned: bool = False) -> dict:
    """Cadena única de habilitación de generación.

    Los estados históricos sólo conservan continuidad del producto certificado.
    Una fuente nueva exige identidad material completa y evidencia pre-M04
    vinculada a esa misma identidad, salvo que la adquisición/reacreditación
    esté explícitamente planificada para el run actual.
    """
    path = root_dir / contract_path if contract_path else None
    if path is None or not path.is_file():
        return _blocked("CAP_CONTRACT", "contrato territorial efectivo ausente")
    try:
        contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return _blocked("CAP_CONTRACT", "contrato territorial efectivo ilegible")
    if not isinstance(contract, dict) or (contract.get("meta") or {}).get("territory_id") != territory_id:
        return _blocked("CAP_CONTRACT", "identidad del contrato territorial no coincide")
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
            or not _sha256_value(prep.get("artifact_sha256"))
            or not _sha256_value(prep.get("package_sha256"))
            or not _sha256_value(prep.get("compatibility_identity_sha256"))
            or not isinstance(prep.get("population_year"), int)
            or not isinstance(prep.get("section_year"), int)
        ):
            return _blocked(
                "CAP_SOURCE",
                "fuente territorial sin identidad completa run/artefacto/paquete/compatibilidad/años",
            )
        if "source_commit" in prep and not re.fullmatch(
            r"[0-9a-f]{40}", str(prep.get("source_commit") or "")
        ):
            return _blocked("CAP_SOURCE", "source_commit de la fuente efectiva inválido")

    if first_generation_evidence:
        return _validated_first_generation_preflight(
            contract=contract,
            evidence=first_generation_evidence,
            preparation_evidence=prep,
            territory_id=territory_id,
            root_dir=root_dir,
        )
    if pre_m04_accreditation_planned:
        return {"allowed": True, "route": "planned_pre_m04_accreditation"}
    if source_acquisition_planned:
        return {"allowed": True, "route": "planned_source_acquisition"}
    if certified_product_ready and not require_source:
        return {"allowed": True, "route": "certified_product_lineage"}
    return _blocked(
        "CAP_PRE_M04_EVIDENCE",
        "la generación exige evidencia pre-M04 ligada a la fuente efectiva; "
        "los estados históricos no habilitan una fuente nueva",
    )

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
    expected_election_id = _registered_election_id(root_dir, row["territory_id"])
    electoral_source_identity_ready = (
        expected_election_id is None
        or str(electoral_source_evidence.get("election_id") or "") == expected_election_id
    )
    electoral_source_ready = bool(
        state.get("electoral_source_prepared")
        and electoral_source_run_id
        and electoral_source_evidence.get("artifact_name")
        and electoral_source_evidence.get("artifact_sha256")
        and electoral_source_identity_ready
    )
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
    if requested_mode == "territorial_only":
        return "territorial_only"
    if not plan.get("run_prepare_electoral"):
        return "electoral"
    from herramientas.resolver_eleccion_vigente import resolve_for_preparation
    territory = str(plan.get("territory_name") or plan.get("territory_id") or "")
    edition = str(plan.get("edition") or "")
    try:
        resolve_for_preparation(territory, root_dir=root_dir, edition=edition)
    except SystemExit as exc:
        raise ValueError(f"ELECTORAL_IDENTITY_BLOCK: {exc}") from exc
    return "electoral"


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
