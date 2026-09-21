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

SCHEMA = "ddd.gerrychain-comarca-sweep/1.2"

BASELINE_CANONICAL = {
    "row_type": "baseline_canonico",
    "source_artifact": "gh-34599224954-1",
    "comarca_surcharge": None,
    "seed": None,
    "selected_for_surcharge": None,
    "comarcas_divididas": 31,
    "comarcas_divididas_evitables": 20,
    "retencion_comarcal": 0.290,
    "retencion_techo_teorico": 0.352,
    "retencion_sobre_maximo": 0.822,
    "polsby_popper_min": None,
    "polsby_popper_median": None,
    "max_relative_deviation": 0.09930,
    "assignment_hash": None,
}


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


def comarca_metrics(problem, assignment, *, target_tolerance_ratio: float) -> dict[str, float | int | None]:
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

    comarca_totals = {
        comarca: sum(pieces.values())
        for comarca, pieces in by_comarca.items()
    }
    single_district_ceiling = problem.target_population * (1.0 + target_tolerance_ratio)
    split = sum(
        1
        for pieces in by_comarca.values()
        if len([population for population in pieces.values() if population > 0]) > 1
    )
    split_avoidable = sum(
        1
        for comarca, pieces in by_comarca.items()
        if comarca_totals[comarca] <= single_district_ceiling + 1e-9
        and len([population for population in pieces.values() if population > 0]) > 1
    )
    retained_population = sum(max(pieces.values()) for pieces in by_comarca.values() if pieces)
    retention = retained_population / covered_population if covered_population else None
    theoretical_retained_population = sum(
        min(total, single_district_ceiling)
        for total in comarca_totals.values()
    )
    retention_ceiling = (
        theoretical_retained_population / covered_population
        if covered_population
        else None
    )
    retention_over_maximum = (
        retention / retention_ceiling
        if retention is not None and retention_ceiling
        else None
    )
    return {
        "comarcas_divididas": split,
        "comarcas_divididas_evitables": split_avoidable,
        "retencion_comarcal": retention,
        "retencion_techo_teorico": retention_ceiling,
        "retencion_sobre_maximo": retention_over_maximum,
        "poblacion_maxima_comarca_en_un_distrito": single_district_ceiling,
    }


def rows_from_portfolio(problem, contract, surcharge: float, portfolio: dict) -> list[dict]:
    selected_hash = portfolio["selected"]["assignment_hash"]
    rows: list[dict] = []
    for run in portfolio["runs"]:
        assignment = run["assignment"]
        violations = hard_constraint_violations(problem, assignment, contract)
        if violations:
            raise AssertionError(
                f"Salida inválida con surcharge={surcharge}, seed={run['seed']}: {violations[:20]}"
            )
        comarca = comarca_metrics(
            problem,
            assignment,
            target_tolerance_ratio=contract.target_tolerance_ratio,
        )
        shape = geometric_shape_metrics(problem, assignment)
        population = population_metrics(problem, assignment, contract)
        rows.append({
            "row_type": "barrido",
            "source_artifact": None,
            "comarca_surcharge": surcharge,
            "seed": run["seed"],
            "selected_for_surcharge": run["assignment_hash"] == selected_hash,
            "comarcas_divididas": comarca["comarcas_divididas"],
            "comarcas_divididas_evitables": comarca["comarcas_divididas_evitables"],
            "retencion_comarcal": comarca["retencion_comarcal"],
            "retencion_techo_teorico": comarca["retencion_techo_teorico"],
            "retencion_sobre_maximo": comarca["retencion_sobre_maximo"],
            "polsby_popper_min": shape["polsby_popper_min"],
            "polsby_popper_median": shape["polsby_popper_median"],
            "max_relative_deviation": population["max_relative_deviation"],
            "assignment_hash": run["assignment_hash"],
        })
    return rows


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
        rows.extend(rows_from_portfolio(problem, contract, surcharge, portfolio))

    payload = {
        "schema": SCHEMA,
        "territory_id": "aragon",
        "promotion": "forbidden",
        "metrics_only": True,
        "population_band": base.population_band,
        "metric_crs": base.metric_crs,
        "min_shared_border_m": base.min_shared_border_m,
        "seed_count": base.seed_count,
        "expected_rows": len(surcharges) * base.seed_count,
        "baseline": BASELINE_CANONICAL,
        "rows": rows,
    }
    json_path = output_dir / "barrido_comarca_surcharge_aragon.json"
    csv_path = output_dir / "barrido_comarca_surcharge_aragon.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    csv_rows = [BASELINE_CANONICAL, *rows]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(csv_rows[0]) if csv_rows else [])
        writer.writeheader()
        writer.writerows(csv_rows)
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
