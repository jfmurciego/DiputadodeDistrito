#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: preparación declarativa de unidades internas
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Preprocesador común previo a M04
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: materializar, sólo cuando el contrato lo declara, unidades internas conexas antes de M04 sin lógica territorial específica.
CAMBIOS: primera versión.
MOTIVO: convertir connected_internal_units en una capacidad común invocable desde cualquier contrato territorial.
ANTERIOR: ninguno — componente nuevo.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

SUPPORTED_STRATEGIES = {"connected_internal_units"}


def _fmt(value: str, *, cfg: dict, run_id: str) -> str:
    meta = cfg.get("meta") or {}
    return str(value).format(
        run_name=meta.get("run_name", ""),
        run_id=run_id,
        year=meta.get("year", ""),
    )


def build_command(params_path: str | Path, run_id: str) -> list[str] | None:
    params = Path(params_path)
    cfg = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    policy = cfg.get("partitioning") or {}
    if not policy or policy.get("enabled") is False:
        return None
    strategy = str(policy.get("strategy") or "").strip()
    if not strategy:
        return None
    if strategy not in SUPPORTED_STRATEGIES:
        raise ValueError(f"Estrategia común de unidades internas no soportada: {strategy}")

    required = (
        "input_geojson", "graph", "output_geojson", "output_report",
        "partition_unit_field", "atomicity_ratio", "chunk_ratio",
    )
    missing = [key for key in required if policy.get(key) in (None, "")]
    if missing:
        raise ValueError("partitioning incompleto: " + ", ".join(missing))

    contract = cfg.get("territory_contract") or {}
    k = contract.get("k_districts")
    if not isinstance(k, int) or isinstance(k, bool) or k <= 0:
        raise ValueError("territory_contract.k_districts debe ser entero positivo")

    m04 = ((cfg.get("modulos") or {}).get("modulo_04_generar_semillas") or {})
    id_field = str(m04.get("id_field") or "CUSEC_KEY")
    municipality_field = str(policy.get("municipality_field") or "CUMUN")
    population_field = str(policy.get("population_field") or m04.get("pop_field") or f"POP_{(cfg.get('meta') or {}).get('year', '')}")

    output_geojson = _fmt(policy["output_geojson"], cfg=cfg, run_id=run_id)
    m04_input = _fmt(str(m04.get("in_geojson") or ""), cfg=cfg, run_id=run_id)
    if output_geojson != m04_input:
        raise ValueError("partitioning.output_geojson debe coincidir exactamente con M04.in_geojson")

    return [
        sys.executable,
        str(Path(__file__).with_name("construir_unidades_internas_m04.py")),
        "--geojson", _fmt(policy["input_geojson"], cfg=cfg, run_id=run_id),
        "--graph", _fmt(policy["graph"], cfg=cfg, run_id=run_id),
        "--out-geojson", output_geojson,
        "--out-report", _fmt(policy["output_report"], cfg=cfg, run_id=run_id),
        "--k", str(k),
        "--id-field", id_field,
        "--municipality-field", municipality_field,
        "--population-field", population_field,
        "--partition-unit-field", str(policy["partition_unit_field"]),
        "--atomicity-ratio", str(policy["atomicity_ratio"]),
        "--chunk-ratio", str(policy["chunk_ratio"]),
    ]


def prepare(params_path: str | Path, run_id: str, *, execute: bool = True) -> list[str] | None:
    command = build_command(params_path, run_id)
    if command is None:
        print("[UNIDADES INTERNAS] Contrato sin preprocesado declarativo; no-op.")
        return None
    if execute:
        subprocess.run(command, check=True)
    return command


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()
    prepare(args.params, args.run_id, execute=True)


if __name__ == "__main__":
    main()
