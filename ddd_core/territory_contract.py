#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Puerta de admisión de contrato territorial
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Admisión estructural y autorización separadas
FECHA: 2026-09-15
ESTADO: vigente — R036
QUÉ HACE: valida el contrato M01-M06 y comunica por separado si está autorizado, bloqueado o limitado a preflight.
CAMBIOS: añade production_authorization coherente entre catálogo y contrato sin confundir validez estructural con permiso de ejecución.
MOTIVO: impedir que un contrato bloqueado o experimental llegue a producción por una comparación textual incompleta.
ANTERIOR: legacy/core/territory_contract_v1.1.0.py
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from ddd_core.config import load_params_yaml

MODULES = [
    "modulo_01_preparar_base_territorial",
    "modulo_02_construir_adyacencias",
    "modulo_03_construir_grafo",
    "modulo_04_generar_semillas",
    "modulo_05_optimizar_distritos",
    "modulo_06_consolidar_distritos",
]
CONTRACT_KEYS = (
    "unit_id_role", "admin_level_1_role", "admin_level_2_role",
    "k_districts", "district_apportionment", "population_floor_ratio",
    "population_cap_ratio", "target_tolerance_ratio",
    "require_graph_contiguity", "require_single_admin_level_1_per_district",
    "require_municipality_discipline", "oversized_municipality_rule",
    "municipality_atomicity_limit_ratio", "require_auditable_district_catalogue",
)
SCHEMA_FAMILY = "ddd-territory"
PRODUCTION_SCHEMA_VERSION = "1.0.0"
STANDARD_LIMITS = {
    "population_floor_ratio": 0.80,
    "population_cap_ratio": 1.75,
    "target_tolerance_ratio": 0.12,
}
K_SOURCES = {"norma", "formula", "decision_propia", "historico_no_registrado"}
PRODUCTION_AUTHORIZATIONS = {"AUTHORIZED", "BLOCKED", "PREFLIGHT"}


def _get(data: Mapping[str, Any], dotted: str, errors: list[str]) -> Any:
    value: Any = data
    for part in dotted.split("."):
        if not isinstance(value, Mapping) or part not in value:
            errors.append(f"falta {dotted}")
            return None
        value = value[part]
    if value is None or value == "" or value == []:
        errors.append(f"vacío {dotted}")
    return value


def _same(label: str, values: list[tuple[str, Any]], errors: list[str]) -> None:
    present = [(name, value) for name, value in values if value is not None]
    if present and any(value != present[0][1] for _, value in present[1:]):
        errors.append(f"incoherencia {label}: " + ", ".join(f"{n}={v!r}" for n, v in present))


def _inside(root: Path, raw: Any) -> bool:
    if not isinstance(raw, str) or not raw:
        return False
    path = Path(raw)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        resolved.relative_to(root)
        return True
    except ValueError:
        return False


def _manifest_paths(root: Path) -> set[Path]:
    manifest = root / "inputs" / "MANIFEST.sha256"
    if not manifest.is_file():
        return set()
    result = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) == 2 and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            result.add((root / parts[1].lstrip("* ")).resolve())
    return result


def _catalogue_entry(root: Path, territory_id: Any, errors: list[str]) -> Mapping[str, Any]:
    path = root / "configuracion" / "catalogo_territorios_espana_2025.yaml"
    if not path.is_file():
        errors.append("falta catálogo territorial canónico")
        return {}
    data = load_params_yaml(str(path))
    entries = (data.get("territories") or []) if isinstance(data, Mapping) else []
    matches = [item for item in entries if isinstance(item, Mapping) and item.get("territory_id") == territory_id]
    if len(matches) != 1:
        errors.append(f"el catálogo debe contener exactamente una entrada para {territory_id!r}")
        return {}
    return matches[0]


def validate_production_contract(params_path: str | Path, *, expected_territory: str | None = None) -> dict[str, Any]:
    """Return an auditable admission report; no territorial module is executed."""
    params = Path(params_path).resolve()
    cfg = load_params_yaml(str(params))
    errors: list[str] = []
    warnings: list[str] = []
    root = Path(cfg["_internal"]["root"]).resolve()

    territory_id = _get(cfg, "meta.territory_id", errors)
    for key in ("procedure_name", "territory", "run_name", "year", "scope", "schema_version", "status"):
        _get(cfg, f"meta.{key}", errors)
    if not isinstance(territory_id, str) or not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", territory_id or ""):
        errors.append("meta.territory_id debe usar minúsculas, números y guiones bajos")
    if expected_territory and territory_id != expected_territory:
        errors.append(f"territorio solicitado {expected_territory!r} no coincide con meta.territory_id={territory_id!r}")
    if territory_id and params.name != f"{territory_id}_{cfg.get('meta', {}).get('year')}.yaml":
        warnings.append("el nombre del YAML no sigue <territory_id>_<year>.yaml")
    if (cfg.get("meta") or {}).get("schema_family") != SCHEMA_FAMILY:
        errors.append(f"meta.schema_family debe ser {SCHEMA_FAMILY!r}")
    if (cfg.get("meta") or {}).get("contract_level") != "production_m01_m06":
        errors.append("meta.contract_level debe ser 'production_m01_m06'")
    if (cfg.get("meta") or {}).get("contract_schema_version") != PRODUCTION_SCHEMA_VERSION:
        errors.append(f"meta.contract_schema_version debe ser {PRODUCTION_SCHEMA_VERSION!r}")

    production_authorization = (cfg.get("meta") or {}).get("production_authorization")
    if production_authorization not in PRODUCTION_AUTHORIZATIONS:
        errors.append(
            "meta.production_authorization debe ser uno de "
            f"{sorted(PRODUCTION_AUTHORIZATIONS)}"
        )

    catalogue = _catalogue_entry(root, territory_id, errors)
    if catalogue and catalogue.get("contract_level") != "production_m01_m06":
        errors.append("el catálogo no declara el territorio como production_m01_m06")
    _same(
        "autorización de producción",
        [("catálogo", catalogue.get("production_authorization")), ("contrato", production_authorization)],
        errors,
    )

    contract = cfg.get("territory_contract") or {}
    if not isinstance(contract, Mapping):
        errors.append("territory_contract debe ser un objeto")
        contract = {}
    for key in CONTRACT_KEYS:
        _get(contract, key, errors)
    provinces = _get(contract, "province_codes", errors)
    if not isinstance(provinces, list) or not provinces or len({str(x) for x in provinces}) != len(provinces):
        errors.append("territory_contract.province_codes debe ser una lista única no vacía")
    k = contract.get("k_districts")
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        errors.append("territory_contract.k_districts debe ser entero positivo")
    k_source = _get(contract, "k_source", errors)
    k_rationale = _get(contract, "k_rationale", errors)
    if k_source not in K_SOURCES:
        errors.append(f"territory_contract.k_source debe ser uno de {sorted(K_SOURCES)}")
    if not isinstance(k_rationale, str) or len(k_rationale.strip()) < 12:
        errors.append("territory_contract.k_rationale debe justificar K de forma auditable")
    _same("K catálogo/contrato", [("catálogo", catalogue.get("k_districts")), ("contrato", k)], errors)
    _same("origen de K", [("catálogo", catalogue.get("k_source")), ("contrato", k_source)], errors)
    _same("justificación de K", [("catálogo", catalogue.get("k_rationale")), ("contrato", k_rationale)], errors)
    for key in ("population_floor_ratio", "target_tolerance_ratio", "municipality_atomicity_limit_ratio"):
        value = contract.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            errors.append(f"territory_contract.{key} debe ser numérico positivo")
    cap = contract.get("population_cap_ratio")
    floor = contract.get("population_floor_ratio")
    if not isinstance(cap, (int, float)) or isinstance(cap, bool) or cap <= 1:
        errors.append("territory_contract.population_cap_ratio debe ser mayor que 1")
    if isinstance(floor, (int, float)) and isinstance(cap, (int, float)) and floor >= cap:
        errors.append("el suelo poblacional debe ser menor que el techo")
    limits_profile = _get(contract, "limits_profile", errors)
    deviations = {
        key: contract.get(key) for key, standard in STANDARD_LIMITS.items()
        if contract.get(key) != standard
    }
    if deviations:
        if limits_profile != "exception":
            errors.append("los límites distintos del estándar exigen limits_profile='exception'")
        for key in ("limits_exception_rationale", "limits_exception_evidence", "limits_exception_decided_at"):
            _get(contract, key, errors)
    elif limits_profile != "standard-1.0.0":
        errors.append("los límites comunes exigen limits_profile='standard-1.0.0'")

    modules = cfg.get("modulos") or {}
    if not isinstance(modules, Mapping):
        errors.append("modulos debe ser un objeto")
        modules = {}
    for name in MODULES:
        if not isinstance(modules.get(name), Mapping):
            errors.append(f"falta módulo de producción {name}")
    m = [modules.get(name, {}) if isinstance(modules.get(name), Mapping) else {} for name in MODULES]
    required_by_module = [
        ("province_codes", "out_geojson", "out_report"),
        ("in_geojson", "id_field", "out_edges_jsonl", "predicate"),
        ("in_geojson", "in_edges_jsonl", "id_field", "pop_field", "out_graph_json", "out_report"),
        ("in_graph_json", "in_geojson", "id_field", "pop_field", "province_field", "municipality_field", "district_apportionment", "k_districts", "seed", "out_geojson", "out_report"),
        ("in_graph_json", "in_geojson", "id_field", "pop_field", "district_field", "province_field", "municipality_field", "seed", "out_geojson", "out_report"),
        ("in_geojson", "id_field", "district_field", "pop_field", "province_field", "municipality_field", "expected_districts", "strict_expected_k", "out_summary_csv", "out_catalog_csv", "out_composition_csv", "out_geojson", "out_district_geojson"),
    ]
    for index, keys in enumerate(required_by_module):
        for key in keys:
            if key not in m[index] or m[index].get(key) in (None, "", []):
                errors.append(f"falta modulos.{MODULES[index]}.{key}")

    chains = [
        ("M01→M02 geometría", m[0].get("out_geojson"), m[1].get("in_geojson")),
        ("M01→M03 geometría", m[0].get("out_geojson"), m[2].get("in_geojson")),
        ("M02→M03 adyacencias", m[1].get("out_edges_jsonl"), m[2].get("in_edges_jsonl")),
        ("M03→M04 grafo", m[2].get("out_graph_json"), m[3].get("in_graph_json")),
        ("M03→M05 grafo", m[2].get("out_graph_json"), m[4].get("in_graph_json")),
        ("M04→M05 asignación", m[3].get("out_geojson"), m[4].get("in_geojson")),
        ("M05→M06 asignación", m[4].get("out_geojson"), m[5].get("in_geojson")),
    ]
    for label, left, right in chains:
        if left is not None and right is not None and left != right:
            errors.append(f"cadena rota {label}")
    _same("K", [("contrato", k), ("M04", m[3].get("k_districts")), ("M06", m[5].get("expected_districts")), ("validación", (cfg.get("validation") or {}).get("expected_districts"))], errors)
    def normalized_codes(value: Any) -> Any:
        return [str(item).zfill(2) for item in value] if isinstance(value, list) else value
    _same("provincias", [("contrato", normalized_codes(provinces)), ("M01", normalized_codes(m[0].get("province_codes"))), ("validación", normalized_codes((cfg.get("validation") or {}).get("expected_province_codes", provinces)))], errors)
    for field, indexes in (("id_field", range(1, 6)), ("pop_field", range(2, 6)), ("province_field", range(3, 6))):
        _same(field, [(f"M{i+1}", m[i].get(field)) for i in indexes], errors)

    partitioning = cfg.get("partitioning") or {}
    partitioning_enabled = bool(
        isinstance(partitioning, Mapping)
        and partitioning.get("enabled") is not False
        and str(partitioning.get("strategy") or "").strip()
    )
    if partitioning_enabled:
        if partitioning.get("strategy") != "connected_internal_units":
            errors.append("partitioning.strategy no soportada por contrato productivo")
        partition_field = partitioning.get("partition_unit_field")
        admin_municipality_field = partitioning.get("municipality_field")
        if not partition_field:
            errors.append("falta partitioning.partition_unit_field")
        if not admin_municipality_field:
            errors.append("falta partitioning.municipality_field")
        if m[3].get("municipality_field") != partition_field:
            errors.append(
                "M04.municipality_field debe coincidir con partitioning.partition_unit_field "
                "cuando hay unidades internas"
            )
        _same(
            "municipio administrativo",
            [
                ("partitioning", admin_municipality_field),
                ("M05", m[4].get("municipality_field")),
                ("M06", m[5].get("municipality_field")),
                ("validación", (cfg.get("validation") or {}).get("municipality_field")),
            ],
            errors,
        )
        if partitioning.get("output_geojson") != m[3].get("in_geojson"):
            errors.append("partitioning.output_geojson debe alimentar M04.in_geojson")
        if partitioning.get("input_geojson") != m[0].get("out_geojson"):
            errors.append("partitioning.input_geojson debe partir de M01.out_geojson")
        if partitioning.get("graph") != m[2].get("out_graph_json"):
            errors.append("partitioning.graph debe coincidir con M03.out_graph_json")
    else:
        _same("municipality_field", [(f"M{i+1}", m[i].get("municipality_field")) for i in range(3, 6)], errors)
    _same("district_field", [("M05", m[4].get("district_field")), ("M06", m[5].get("district_field"))], errors)
    _same("reparto", [("contrato", contract.get("district_apportionment")), ("M04", m[3].get("district_apportionment")), ("validación", (cfg.get("validation") or {}).get("province_apportionment"))], errors)

    validation = cfg.get("validation") or {}
    if not isinstance(validation, Mapping):
        errors.append("validation debe ser un objeto")
        validation = {}
    for key in ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio", "require_graph_contiguity", "require_single_province_per_district", "require_municipality_discipline", "require_m06_population_conservation", "require_m06_assignment_identity_with_m05"):
        _get(validation, key, errors)
    for key in ("population_floor_ratio", "population_cap_ratio", "target_tolerance_ratio"):
        _same(key, [("contrato", contract.get(key)), ("validación", validation.get(key))], errors)
    _same("contigüidad", [("contrato", contract.get("require_graph_contiguity")), ("validación", validation.get("require_graph_contiguity"))], errors)
    _same("barrera administrativa", [("contrato", contract.get("require_single_admin_level_1_per_district")), ("validación", validation.get("require_single_province_per_district"))], errors)
    _same("disciplina municipal", [("contrato", contract.get("require_municipality_discipline")), ("validación", validation.get("require_municipality_discipline"))], errors)
    if m[5].get("strict_expected_k") is not True:
        errors.append("M06 debe declarar strict_expected_k=true")

    output_keys = {"out_geojson", "out_report", "out_edges_jsonl", "out_graph_json", "out_summary_csv", "out_catalog_csv", "out_composition_csv", "out_district_geojson"}
    outputs: list[str] = []
    for index, module in enumerate(m):
        for key, value in module.items():
            if key in output_keys and isinstance(value, str):
                outputs.append(value)
                if not _inside(root, value):
                    errors.append(f"salida fuera del repositorio: M{index+1}.{key}")
    if len(outputs) != len(set(outputs)):
        errors.append("dos outputs de módulos escriben la misma ruta")

    source_paths = []
    io_input = ((cfg.get("io") or {}).get("input") or {})
    seccionado = (io_input.get("seccionado") or {}).get("path")
    population = (io_input.get("population_cip") or {}).get("paths")
    if not seccionado:
        errors.append("falta io.input.seccionado.path")
    else:
        source_paths.append(Path(str(seccionado)).resolve())
    if not isinstance(population, list) or not population:
        errors.append("falta io.input.population_cip.paths")
    else:
        source_paths.extend(Path(str(x)).resolve() for x in population)
    manifest_paths = _manifest_paths(root)
    if not manifest_paths:
        errors.append("falta inputs/MANIFEST.sha256 con procedencia verificable")
    for source in source_paths:
        if source not in manifest_paths:
            errors.append(f"fuente sin checksum declarado: {source.relative_to(root) if _inside(root, str(source)) else source}")

    canonical = json.dumps({k: v for k, v in cfg.items() if k != "_internal"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": "1.1.0",
        "contract_version": str((cfg.get("meta") or {}).get("schema_version", "")),
        "territory_id": territory_id,
        "level": "M01_M06_PRODUCTION",
        "status": "ADMITTED" if not errors else "REJECTED",
        "production_authorization": production_authorization,
        "production_authorized": not errors and production_authorization == "AUTHORIZED",
        "errors": errors,
        "warnings": warnings,
        "contract_sha256": hashlib.sha256(canonical).hexdigest(),
        "modules": MODULES,
    }
