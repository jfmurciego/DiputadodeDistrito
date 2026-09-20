#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile
from typing import Any

import yaml

from ddd_core.m05_gerrychain_engine import (
    Contract,
    Weights,
    adapt_files,
    run_gerrychain_optimization,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "ddd.m05-gerrychain-strategy/1.0"


def _resolve(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else (ROOT / value).resolve()


def _module(cfg: dict[str, Any], name: str) -> dict[str, Any]:
    return (cfg.get("modulos") or {}).get(name) or {}


def _format_field(value: str | None, year: Any) -> str | None:
    if not value:
        return value
    return str(value).replace("{year}", str(year))


def contract_from_params(cfg: dict[str, Any]) -> Contract:
    tc = cfg.get("territory_contract") or {}
    validation = cfg.get("validation") or {}
    k = int(validation.get("expected_districts") or tc.get("k_districts") or 0)
    if k <= 0:
        raise ValueError("Contrato sin K válido")
    province_districts = validation.get("province_districts")
    return Contract(
        k=k,
        target_tolerance_ratio=float(
            validation.get("target_tolerance_ratio", tc.get("target_tolerance_ratio", 0.12))
        ),
        population_floor_ratio=float(
            validation.get("population_floor_ratio", tc.get("population_floor_ratio", 0.80))
        ),
        population_cap_ratio=float(
            validation.get("population_cap_ratio", tc.get("population_cap_ratio", 1.75))
        ),
        municipality_atomicity_limit_ratio=float(
            validation.get(
                "municipality_atomicity_limit_ratio",
                tc.get("municipality_atomicity_limit_ratio", 1.75),
            )
        ),
        require_single_province=bool(
            validation.get("require_single_province_per_district", True)
        ),
        require_contiguity=bool(validation.get("require_graph_contiguity", True)),
        province_districts={str(k): int(v) for k, v in (province_districts or {}).items()} or None,
        require_municipality_discipline=bool(
            validation.get("require_municipality_discipline", True)
        ),
        max_mixed_districts_per_split_municipality=int(
            validation.get("max_mixed_districts_per_split_municipality", 1)
        ),
        preserve_closed_urban=True,
    )


def build_strategy_inputs(
    params: str | Path,
    *,
    graph_override: str | Path | None = None,
    initial_override: str | Path | None = None,
):
    params_path = _resolve(params)
    cfg = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
    meta = cfg.get("meta") or {}
    year = meta.get("year")
    m02 = _module(cfg, "modulo_02_construir_adyacencias")
    m05 = _module(cfg, "modulo_05_optimizar_distritos")
    graph = _resolve(graph_override or m05.get("in_graph_json", ""))
    initial = _resolve(initial_override or m05.get("in_geojson", ""))
    if not graph.is_file() or not initial.is_file():
        raise FileNotFoundError(f"Entradas GerryChain inexistentes: graph={graph}, initial={initial}")
    bridges = [
        (str(item["u"]), str(item["v"]))
        for item in (m02.get("topology_bridges") or [])
        if item.get("u") and item.get("v")
    ]
    data = adapt_files(
        graph,
        initial,
        section_field=str(m05.get("id_field", "CUSEC_KEY")),
        district_field=str(m05.get("district_field", "district_id")),
        municipality_field=str(m05.get("municipality_field", "CUMUN")),
        province_field=str(m05.get("province_field", "CPRO")),
        population_field=_format_field(m05.get("pop_field"), year),
        atomic_unit_field=str(m05.get("unit_id_field", "ddd_unit_id")),
        closed_urban_field="ddd_closed_urban",
        comarca_enabled=False,
        # M03 ya es el grafo contractual producido por M02 después de aplicar
        # min_shared_border_m en su CRS métrico. M04 puede estar publicado en
        # CRS84; volver a medir aquí "metros" sobre grados sería incorrecto.
        min_shared_border_m=0.0,
        preserve_atomic_multipart_sections=True,
        declared_topology_bridges=bridges,
    )
    return cfg, params_path, graph, initial, data, contract_from_params(cfg), bridges


def _write_geojson(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if path.suffix.lower() == ".zip":
        inner = path.name[:-4]
        if not inner.lower().endswith((".geojson", ".json")):
            inner += ".geojson"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(inner, text)
    else:
        path.write_text(text, encoding="utf-8")


def run_strategy(
    params: str | Path,
    *,
    graph_override: str | Path | None = None,
    initial_override: str | Path | None = None,
    output_override: str | Path | None = None,
    report_override: str | Path | None = None,
    steps_per_stage: int = 250,
    warmup_rounds: int = 4,
    seed: int = 20260920,
) -> dict[str, Any]:
    cfg, params_path, graph, initial, data, contract, bridges = build_strategy_inputs(
        params,
        graph_override=graph_override,
        initial_override=initial_override,
    )
    m05 = _module(cfg, "modulo_05_optimizar_distritos")
    output = _resolve(output_override or m05.get("out_geojson", ""))
    report_path = _resolve(report_override or m05.get("out_report", ""))
    result, report = run_gerrychain_optimization(
        data,
        contract,
        steps_per_stage=steps_per_stage,
        warmup_rounds=warmup_rounds,
        seed=seed,
        weights=Weights(),
    )
    report["strategy"] = {
        "schema": SCHEMA,
        "params": str(params_path.relative_to(ROOT)) if params_path.is_relative_to(ROOT) else str(params_path),
        "graph": str(graph),
        "initial": str(initial),
        "output": str(output),
        "declared_topology_bridges": [list(edge) for edge in bridges],
        "source_topology": {
            "m03_is_canonical_filtered_graph": True,
            "m02_min_shared_border_m": float((_module(cfg, "modulo_02_construir_adyacencias")).get("min_shared_border_m", 0.0)),
        },
    }
    _write_geojson(output, result)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Estrategia M05 GerryChain/ReCom genérica")
    ap.add_argument("--params", required=True)
    ap.add_argument("--graph")
    ap.add_argument("--initial")
    ap.add_argument("--output")
    ap.add_argument("--report")
    ap.add_argument("--steps-per-stage", type=int, default=250)
    ap.add_argument("--warmup-rounds", type=int, default=4)
    ap.add_argument("--seed", type=int, default=20260920)
    args = ap.parse_args()
    report = run_strategy(
        args.params,
        graph_override=args.graph,
        initial_override=args.initial,
        output_override=args.output,
        report_override=args.report,
        steps_per_stage=args.steps_per_stage,
        warmup_rounds=args.warmup_rounds,
        seed=args.seed,
    )
    print(json.dumps({
        "optimization_status": report["optimization_status"],
        "before": report["target_tolerance"]["before"],
        "after": report["target_tolerance"]["after"],
        "objective": report["objective"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
