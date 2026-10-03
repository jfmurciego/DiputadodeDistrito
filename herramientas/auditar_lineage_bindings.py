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


def audit_binding_lineage(cfg: dict) -> list[dict[str, Any]]:
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

    return [
        {
            "binding": row.binding,
            "value": row.value,
            "upstream": row.upstream,
            "upstream_value": row.upstream_value,
        }
        for row in out
    ]
