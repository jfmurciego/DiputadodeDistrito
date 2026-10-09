#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ContractDerivationBlock(ValueError):
    pass


@dataclass(frozen=True)
class BindingLineage:
    binding: str
    value: Any
    upstream: str
    upstream_value: Any


def _get(mapping: dict, path: tuple[str, ...]) -> Any:
    value: Any = mapping
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ContractDerivationBlock(
                "CONTRACT_DERIVATION_BLOCK: falta " + ".".join(path)
            )
        value = value[key]
    return value


def _record(
    out: list[BindingLineage],
    *,
    cfg: dict,
    binding_path: tuple[str, ...],
    contract: dict,
    upstream_path: tuple[str, ...],
) -> None:
    value = _get(cfg, binding_path)
    upstream_value = _get(contract, upstream_path)
    if value != upstream_value:
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: "
            + ".".join(binding_path)
            + f"={value!r} no procede de "
            + ".".join(upstream_path)
            + f"={upstream_value!r}"
        )
    out.append(
        BindingLineage(
            binding=".".join(binding_path),
            value=value,
            upstream="resolved_source_contract." + ".".join(upstream_path),
            upstream_value=upstream_value,
        )
    )


def _source_input_by_role(
    source_inputs: list[dict[str, Any]],
    role: str,
) -> dict[str, Any]:
    matches = [
        row
        for row in source_inputs
        if isinstance(row, dict) and str(row.get("role") or "") == role
    ]
    if len(matches) != 1:
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: "
            f"source_inputs requiere exactamente un role={role}: {len(matches)}"
        )
    return matches[0]


def _record_source_identity(
    out: list[BindingLineage],
    *,
    source_inputs: list[dict[str, Any]],
    role: str,
    contract: dict,
    contract_source_key: str,
) -> None:
    source_input = _source_input_by_role(source_inputs, role)
    contract_source = _get(contract, ("sources", contract_source_key))
    checks = (
        ("source_id", ("source_id",)),
        ("role", ("role",)),
        ("path", ("artifact", "path")),
        ("sha256", ("artifact", "sha256")),
    )
    for input_field, contract_path in checks:
        value = source_input.get(input_field)
        upstream_value = _get(contract_source, contract_path)
        if value != upstream_value:
            raise ContractDerivationBlock(
                "CONTRACT_DERIVATION_BLOCK: "
                f"source_inputs[{role}].{input_field}={value!r} no procede de "
                f"resolved_source_contract.sources.{contract_source_key}."
                + ".".join(contract_path)
                + f"={upstream_value!r}"
            )
        out.append(
            BindingLineage(
                binding=f"generation_state.source_inputs[{role}].{input_field}",
                value=value,
                upstream=(
                    "resolved_source_contract.sources."
                    + contract_source_key
                    + "."
                    + ".".join(contract_path)
                ),
                upstream_value=upstream_value,
            )
        )


def audit_binding_lineage(
    cfg: dict,
    *,
    source_inputs: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    contract = cfg.get("resolved_source_contract")
    if not isinstance(contract, dict):
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: falta resolved_source_contract"
        )
    if contract.get("schema") != "ddd.resolved-source-contract/1.0":
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: schema de contrato resuelto no autoritativo"
        )

    out: list[BindingLineage] = []

    # Entradas físicas de M01.
    population_paths = _get(cfg, ("io", "input", "population_cip", "paths"))
    if not isinstance(population_paths, list) or len(population_paths) != 1:
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: M01 debe recibir exactamente un path poblacional"
        )
    population_path = _get(contract, ("sources", "population", "artifact", "path"))
    if population_paths[0] != population_path:
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: io.input.population_cip.paths[0] "
            f"={population_paths[0]!r} no procede de "
            f"resolved_source_contract.sources.population.artifact.path={population_path!r}"
        )
    out.append(
        BindingLineage(
            "io.input.population_cip.paths[0]",
            population_paths[0],
            "resolved_source_contract.sources.population.artifact.path",
            population_path,
        )
    )

    _record(
        out,
        cfg=cfg,
        binding_path=("io", "input", "population_cip", "section_key_col"),
        contract=contract,
        upstream_path=("sources", "population", "fields", "section_id"),
    )
    _record(
        out,
        cfg=cfg,
        binding_path=("io", "input", "population_cip", "pop_col"),
        contract=contract,
        upstream_path=("sources", "population", "fields", "population"),
    )
    _record(
        out,
        cfg=cfg,
        binding_path=("io", "input", "seccionado", "path"),
        contract=contract,
        upstream_path=("sources", "sectioning", "artifact", "path"),
    )
    _record(
        out,
        cfg=cfg,
        binding_path=("io", "input", "seccionado", "section_key_col"),
        contract=contract,
        upstream_path=("sources", "sectioning", "fields", "section_id"),
    )

    # Semántica física que M01 debe obedecer literalmente.
    for cfg_field, contract_field in (
        ("container", "container"),
        ("materialized_format", "materialized_format"),
        ("archive_member", "archive_member"),
        ("encoding", "encoding"),
        ("sep", "delimiter"),
    ):
        _record(
            out,
            cfg=cfg,
            binding_path=("io", "input", "population_cip", cfg_field),
            contract=contract,
            upstream_path=("sources", "population", contract_field),
        )
    for field in (
        "container",
        "materialized_format",
        "archive_member",
        "layer",
    ):
        _record(
            out,
            cfg=cfg,
            binding_path=("io", "input", "seccionado", field),
            contract=contract,
            upstream_path=("sources", "sectioning", field),
        )

    # Columnas y filtros físicos que determinan cómo M01 interpreta población.
    population_contract = _get(contract, ("sources", "population"))
    population_fields = population_contract.get("fields") or {}
    population_filters = population_contract.get("filters") or {}
    for cfg_field, contract_field in (
        ("year_col", "year"),
        ("sexo_col", "sex"),
        ("edad_col", "age"),
    ):
        if contract_field in population_fields:
            _record(
                out,
                cfg=cfg,
                binding_path=(
                    "io",
                    "input",
                    "population_cip",
                    "filters",
                    cfg_field,
                ),
                contract=contract,
                upstream_path=(
                    "sources",
                    "population",
                    "fields",
                    contract_field,
                ),
            )
    for cfg_field, contract_field in (
        ("year_value", "year_value"),
        ("sexo_total_values", "sex_total_values"),
        ("edad_total_values", "age_total_values"),
    ):
        if contract_field in population_filters:
            _record(
                out,
                cfg=cfg,
                binding_path=(
                    "io",
                    "input",
                    "population_cip",
                    "filters",
                    cfg_field,
                ),
                contract=contract,
                upstream_path=(
                    "sources",
                    "population",
                    "filters",
                    contract_field,
                ),
            )

    module_specs = (
        ("modulo_02_construir_adyacencias", "id_field", "section_id_field"),
        ("modulo_03_construir_grafo", "id_field", "section_id_field"),
        ("modulo_03_construir_grafo", "pop_field", "population_field"),
        ("modulo_04_generar_semillas", "id_field", "section_id_field"),
        ("modulo_04_generar_semillas", "pop_field", "population_field"),
        ("modulo_05_optimizar_distritos", "id_field", "section_id_field"),
        ("modulo_05_optimizar_distritos", "pop_field", "population_field"),
        ("modulo_06_consolidar_distritos", "id_field", "section_id_field"),
        ("modulo_06_consolidar_distritos", "pop_field", "population_field"),
    )
    modules = cfg.get("modulos") or {}
    for module_name, field, runtime_field in module_specs:
        module = modules.get(module_name)
        if not isinstance(module, dict) or field not in module:
            continue
        _record(
            out,
            cfg=cfg,
            binding_path=("modulos", module_name, field),
            contract=contract,
            upstream_path=("runtime", runtime_field),
        )

    partitioning = cfg.get("partitioning")
    if isinstance(partitioning, dict) and "population_field" in partitioning:
        _record(
            out,
            cfg=cfg,
            binding_path=("partitioning", "population_field"),
            contract=contract,
            upstream_path=("runtime", "population_field"),
        )

    # Bindings administrativos autoritativos.
    for validation_field, runtime_field in (
        ("province_field", "province_field"),
        ("municipality_field", "municipality_field"),
    ):
        validation = cfg.get("validation")
        if isinstance(validation, dict) and validation_field in validation:
            _record(
                out,
                cfg=cfg,
                binding_path=("validation", validation_field),
                contract=contract,
                upstream_path=("runtime", runtime_field),
            )

    if isinstance(partitioning, dict) and "municipality_field" in partitioning:
        _record(
            out,
            cfg=cfg,
            binding_path=("partitioning", "municipality_field"),
            contract=contract,
            upstream_path=("runtime", "municipality_field"),
        )

    for module_name in (
        "modulo_04_generar_semillas",
        "modulo_05_optimizar_distritos",
        "modulo_06_consolidar_distritos",
    ):
        module = modules.get(module_name)
        if isinstance(module, dict) and "province_field" in module:
            _record(
                out,
                cfg=cfg,
                binding_path=("modulos", module_name, "province_field"),
                contract=contract,
                upstream_path=("runtime", "province_field"),
            )

    m04 = modules.get("modulo_04_generar_semillas")
    if isinstance(m04, dict):
        if "source_municipality_field" in m04:
            _record(
                out,
                cfg=cfg,
                binding_path=(
                    "modulos",
                    "modulo_04_generar_semillas",
                    "source_municipality_field",
                ),
                contract=contract,
                upstream_path=("runtime", "municipality_field"),
            )
        if "municipality_field" in m04:
            partition_unit_field = (
                str(partitioning.get("partition_unit_field") or "")
                if isinstance(partitioning, dict)
                else ""
            )
            partitioning_enabled = bool(
                isinstance(partitioning, dict)
                and partitioning.get("enabled") is not False
                and str(partitioning.get("strategy") or "").strip()
                and partition_unit_field
            )
            if partitioning_enabled:
                value = _get(
                    cfg,
                    ("modulos", "modulo_04_generar_semillas", "municipality_field"),
                )
                upstream_value = _get(
                    cfg,
                    ("partitioning", "partition_unit_field"),
                )
                if value != upstream_value:
                    raise ContractDerivationBlock(
                        "CONTRACT_DERIVATION_BLOCK: "
                        "modulos.modulo_04_generar_semillas.municipality_field="
                        f"{value!r} no procede de partitioning.partition_unit_field="
                        f"{upstream_value!r}"
                    )
                out.append(
                    BindingLineage(
                        binding=(
                            "modulos.modulo_04_generar_semillas.municipality_field"
                        ),
                        value=value,
                        upstream="partitioning.partition_unit_field",
                        upstream_value=upstream_value,
                    )
                )
            else:
                _record(
                    out,
                    cfg=cfg,
                    binding_path=(
                        "modulos",
                        "modulo_04_generar_semillas",
                        "municipality_field",
                    ),
                    contract=contract,
                    upstream_path=("runtime", "municipality_field"),
                )

    for module_name in (
        "modulo_05_optimizar_distritos",
        "modulo_06_consolidar_distritos",
    ):
        module = modules.get(module_name)
        if isinstance(module, dict) and "municipality_field" in module:
            _record(
                out,
                cfg=cfg,
                binding_path=("modulos", module_name, "municipality_field"),
                contract=contract,
                upstream_path=("runtime", "municipality_field"),
            )

    # Identidad durable de los bytes consumidos. La fuente de verdad es el
    # estado operativo materializado; un argumento externo sólo puede servir
    # como cross-check, nunca sustituirlo.
    generation_state = cfg.get("generation_state")
    if not isinstance(generation_state, dict):
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: falta generation_state durable"
        )
    durable_source_inputs = generation_state.get("source_inputs")
    if not isinstance(durable_source_inputs, list):
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: generation_state.source_inputs no es lista"
        )
    if source_inputs is not None and source_inputs != durable_source_inputs:
        raise ContractDerivationBlock(
            "CONTRACT_DERIVATION_BLOCK: source_inputs externo difiere de "
            "generation_state.source_inputs durable"
        )
    _record_source_identity(
        out,
        source_inputs=durable_source_inputs,
        role="population",
        contract=contract,
        contract_source_key="population",
    )
    _record_source_identity(
        out,
        source_inputs=durable_source_inputs,
        role="target_sectioning",
        contract=contract,
        contract_source_key="sectioning",
    )

    return [
        {
            "binding": row.binding,
            "value": row.value,
            "upstream": row.upstream,
            "upstream_value": row.upstream_value,
        }
        for row in out
    ]
