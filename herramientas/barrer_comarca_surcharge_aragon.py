#!/usr/bin/env python3
"""Barrido métrico de comarca_surcharge para Aragón.

No publica, no promueve y no modifica el catálogo. Reutiliza M03/M04 ya
preparados, ejecuta la misma estrategia GerryChain con semillas idénticas para
cada surcharge y persiste únicamente métricas comparables en JSON/CSV.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import replace
from pathlib import Path

import geopandas as gpd
import yaml

from ddd_core.comarcas import load_comarcas, normalize_municipality_key
from ddd_core.m05_gerrychain_strategy import (
    contract_from_yaml,
    geometric_shape_metrics,
    hard_constraint_violations,
    population_metrics,
    prepare_problem,
    run_portfolio,
    strategy_config_from_yaml,
)

SCHEMA = "ddd.gerrychain-comarca-sweep/1.0"


def _enrich_with_comarcas(initial: Path, comarca_csv: Path, output: Path) -> Path:
    frame = gpd.read_file("zip://" + str(initial)) if initial.suffix.lower() == ".zip" else gpd.read_file(initial)
    lookup = load_comarcas({
        "path": str(comarca_csv),
        "sep": "auto",
        "join": {
            "comarcas_key_col": "Municipio código",
            "comarca_code_col": "Comarca código",
            "comarca_name_col": "Comarca nombre",
        },
    })
    by_municipality = lookup.set_index("MUN_KEY")[["COMARCA_CODIGO", "COMARCA_NOMBRE"]].to_dict("index")
    municipality = frame["CUSEC_KEY"].map(normalize_municipality_key)
    frame["COMARCA_CODIGO"] = municipality.map(lambda key: (by_municipality.get(key) or {}).get("COMARCA_CODIGO"))
    frame["COMARCA_NOMBRE"] = municipality.map(lambda key: (by_municipality.get(key) or {}).get("COMARCA_NOMBRE"))
    missing = sorted(set(municipality[frame["COMARCA_CODIGO"].isna()].dropna()))
    if missing:
        raise ValueError(f"Fuente comarcal sin cobertura para {len(missing)} municipios: {missing[:10]}")
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_file(output, driver="GeoJSON")
    return output


def comarca_metrics(problem, assignment) -> dict[str, float | int | None]:
    by_comarca: dict[str, dict[object, float]] = defaultdict(lambda: defaultdict(float))
    covered_population = 0.0
    for unit, district in assignment.items():
        row = problem.units[unit]
        comarca = row.get("comarca")
        if not comarca:
            continue
        population = float(row["population"])
        covered_population += population
        by_comarca[str(comarca)][district] += population
    split = sum(1 for pieces in by_comarca.values() if len([p for p in pieces.values() if p > 0]) > 1)
    retained = sum(max(pieces.values()) for pieces in by_comarca.values() if pieces)
    return {
        "comarcas_divididas": split,
        "retencion_comarcal": retained / covered_population if covered_population else None,
    }


def execute(config_path: Path, graph: Path, initial: Path, comarca_csv: Path, output_dir: Path) -> dict:
    spec = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if spec.get("territory_id") != "aragon":
        raise ValueError("El barrido está limitado a Aragón")
    if spec.get("promotion") != "forbidden":
        raise ValueError("El experimento debe prohibir promoción")
    surcharges = [float(value) for value in spec.get("comarca_surcharge_values", [])]
    if surcharges != [0.3, 0.4, 0.5, 0.6, 0.8]:
        raise ValueError("Valores de comarca_surcharge distintos del contrato del barrido")

    params = Path(spec["territorial_params"])
    territorial = yaml.safe_load(params.read_text(encoding="utf-8")) or {}
    contract = contract_from_yaml(territorial)
    base = strategy_config_from_yaml(territorial)
    output_dir.mkdir(parents=True, exist_ok=True)
    enriched = _enrich_with_comarcas(initial, comarca_csv, output_dir / "m04_comarcas.geojson")
    problem = prepare_problem(
        graph,
        enriched,
        contract,
        metric_crs=base.metric_crs,
        min_shared_border_m=base.min_shared_border_m,
    )

    rows = []
    for surcharge in surcharges:
        strategy = replace(base, comarca_surcharge=surcharge)
        portfolio = run_portfolio(problem, contract, strategy)
        assignment = portfolio["selected"]["assignment"]
        violations = hard_constraint_violations(problem, assignment, contract)
        if violations:
            raise AssertionError(f"Salida inválida con surcharge={surcharge}: {violations[:20]}")
        comarca = comarca_metrics(problem, assignment)
        shape = geometric_shape_metrics(problem, assignment)
        population = population_metrics(problem, assignment, contract)
        rows.append({
            "comarca_surcharge": surcharge,
            "comarcas_divididas": comarca["comarcas_divididas"],
            "retencion_comarcal": comarca["retencion_comarcal"],
            "polsby_popper_min": shape["polsby_popper_min"],
            "polsby_popper_median": shape["polsby_popper_median"],
            "max_relative_deviation": population["max_relative_deviation"],
            "selected_seed": portfolio["selected"]["seed"],
            "assignment_hash": portfolio["selected"]["assignment_hash"],
        })

    payload = {
        "schema": SCHEMA,
        "territory_id": "aragon",
        "promotion": "forbidden",
        "metrics_only": True,
        "population_band": base.population_band,
        "metric_crs": base.metric_crs,
        "min_shared_border_m": base.min_shared_border_m,
        "rows": rows,
    }
    json_path = output_dir / "barrido_comarca_surcharge_aragon.json"
    csv_path = output_dir / "barrido_comarca_surcharge_aragon.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else [])
        writer.writeheader()
        writer.writerows(rows)
    enriched.unlink(missing_ok=True)
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--graph", type=Path, required=True)
    ap.add_argument("--initial", type=Path, required=True)
    ap.add_argument("--comarca-csv", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    result = execute(args.config, args.graph, args.initial, args.comarca_csv, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
