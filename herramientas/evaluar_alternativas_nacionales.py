#!/usr/bin/env python3
"""VERSIÓN: 1.0.2; NOMBRE: evaluación común de alternativas nacionales.
FECHA: 2026-10-10; ALCANCE: medias provinciales y sensibilidad exploratoria.
ESTADO: CI_PENDIENTE; CAMBIOS: métricas sobre reparto ya conservado, sin regenerarlo.
MOTIVO: aportar consecuencias cuantitativas antes de elegir una política institucional.
ANTERIOR: legacy/herramientas/evaluar_alternativas_nacionales_v1.0.1.py; CAMBIOS C1: validar asignación y cuotas provinciales.
"""
from __future__ import annotations
import argparse
import csv
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from herramientas.modelo_cuantitativo_nacional import calculate, half_up


def metadata():
    return {"version": "1.0.2", "name": "Evaluación de alternativas nacionales",
            "date": "2026-10-10", "scope": "análisis local; medias, no distritos generados",
            "status": "CI_PENDIENTE", "changes": "C1: valida asignaciones y cuotas por provincia",
            "reason": "evaluar alternativas antes de decisión institucional", "origin": "legacy/herramientas/evaluar_alternativas_nacionales_v1.0.1.py"}


def validate_model(model):
    if model.get("schema") != "ddd.national-quantitative-model/1.0" or model.get("version") != "1.0.0":
        raise ValueError("MODEL_VERSION_INCOMPATIBLE")
    target = model.get("target_population_hypothesis")
    if type(target) is not int or target <= 0:
        raise ValueError("TARGET_INVALID")
    rules = set(); reference = None
    for alternative in model.get("alternatives", []):
        if alternative["rule"] in rules:
            raise ValueError("RULE_DUPLICATE")
        rules.add(alternative["rule"]); rows = alternative["rows"]
        if len(rows) != 52 or {r["province_code"] for r in rows} != {f"{i:02d}" for i in range(1, 53)}:
            raise ValueError("PROVINCIAL_COVERAGE_INVALID")
        if any(type(r["population"]) is not int or r["population"] < 0 or type(r["k_assigned"]) is not int or r["k_assigned"] < 0 for r in rows):
            raise ValueError("POPULATION_OR_K_INVALID")
        populations = {r["province_code"]: r["population"] for r in rows}
        if reference is not None and reference != populations:
            raise ValueError("POPULATION_UNIVERSE_INCONSISTENT")
        reference = populations
        if sum(populations.values()) != model["population_total"] or sum(r["k_assigned"] for r in rows) != alternative["k_total"]:
            raise ValueError("TOTAL_NOT_CONSERVED")
        for r in rows:
            if Fraction(r["target_quota"]) != Fraction(r["population"], target):
                raise ValueError("TARGET_QUOTA_INCONSISTENT")
    if rules != {"floor_independiente", "nearest_half_up_independiente", "ceil_independiente", "hamilton_k_derivado", "minimos_referencia_k_derivado"}:
        raise ValueError("FIVE_EXISTING_ALTERNATIVES_REQUIRED")
    expected = {a['rule']: a for a in calculate(reference, target)['alternatives']}
    for alternative in model['alternatives']:
        expected_alternative = expected[alternative['rule']]
        for field in ('population_total', 'k_total', 'minimum_reference_violations',
                      'within_constitutional_size_reference', 'equals_congress_size_reference',
                      'city_fixed_one_reference_violations', 'zero_district_populated_provinces'):
            actual = alternative.get(field)
            correct = expected_alternative[field]
            if type(actual) is not type(correct) or actual != correct:
                raise ValueError('ALTERNATIVE_INDICATOR_INCONSISTENT: '+field)
        wanted = {row['province_code']: row for row in expected_alternative['rows']}
        for row in alternative['rows']:
            correct = wanted[row['province_code']]
            if row['k_assigned'] != correct['k_assigned']:
                raise ValueError('PROVINCIAL_ALLOCATION_INCONSISTENT')
            if Fraction(row['allocation_quota']) != Fraction(correct['allocation_quota']):
                raise ValueError('ALLOCATION_QUOTA_INCONSISTENT')
    return reference


def provincial_metrics(rows, target):
    """MAE ponderado por plazas: Σ K_i |P_i/K_i-T| / Σ K_i, excluyendo K_i=0."""
    if type(target) is not int or target <= 0 or not rows:
        raise ValueError("METRIC_INPUT_INVALID")
    summaries = []; deviation = Fraction(0); squared = Fraction(0); seats = 0; uncovered = 0
    for row in sorted(rows, key=lambda r: r["province_code"]):
        pop = row["population"]; k = row["k_assigned"]
        if type(pop) is not int or pop < 0 or type(k) is not int or k < 0:
            raise ValueError("METRIC_POPULATION_OR_K_INVALID")
        mean = Fraction(pop, k) if k else None
        delta = mean-target if k else None
        summaries.append({"province_code": row["province_code"], "population": pop, "k": k,
                          "mean_population": str(mean) if mean is not None else None,
                          "deviation": str(delta) if delta is not None else None,
                          "relative_deviation": str(delta/target) if delta is not None else None,
                          "within_hypothetical_080_175": Fraction(4,5)*target <= mean <= Fraction(7,4)*target if mean is not None else None})
        if k:
            seats += k; deviation += k*abs(delta); squared += k*delta*delta
        else:
            uncovered += pop
    means = [(Fraction(r["mean_population"]), r["province_code"]) for r in summaries if r["mean_population"] is not None]
    minimum = min(means) if means else None; maximum = max(means) if means else None
    return {"metric_population_scope": "province_mean_proxy_not_observed_district_population",
            "k_total": seats, "unrepresented_population": uncovered,
            "district_weighted_mae": str(deviation/seats) if seats else None,
            "district_weighted_mean_squared_deviation": str(squared/seats) if seats else None,
            "population_per_assigned_seat": str(Fraction(sum(r["population"] for r in rows)-uncovered, seats)) if seats else None,
            "minimum_province_mean": {"population": str(minimum[0]), "province_code": minimum[1]} if minimum else None,
            "maximum_province_mean": {"population": str(maximum[0]), "province_code": maximum[1]} if maximum else None,
            "province_means_outside_hypothetical_080_175": [r["province_code"] for r in summaries if r["within_hypothetical_080_175"] is False],
            "geometric_provincial_barriers_verified": False,
            "observed_district_extremes": None, "provinces": summaries}


def sensitivity(model):
    """Sólo escenarios nuevos: ±1/±5% uniforme y en una provincia cada vez."""
    populations = validate_model(model); target = model["target_population_hypothesis"]
    baseline = {a["rule"]: {r["province_code"]: r["k_assigned"] for r in a["rows"]} for a in model["alternatives"]}
    scenarios = []
    for basis_points in (-500, -100, 100, 500):
        for focus in [None, *sorted(populations)]:
            altered = {c: half_up(p*(10000+basis_points), 10000) if focus is None or c == focus else p for c, p in populations.items()}
            # Recalcular escenarios hipotéticos es necesario para medir estabilidad;
            # no sustituye ni reescribe las cinco asignaciones originales.
            variants = calculate(altered, target)
            for alternative in variants["alternatives"]:
                old = baseline[alternative["rule"]]; new = {r["province_code"]: r["k_assigned"] for r in alternative["rows"]}
                scenarios.append({"rule": alternative["rule"], "shock_basis_points": basis_points,
                                  "scope": "uniform" if focus is None else "single_province", "province_code": focus,
                                  "population_total": variants["population_total"], "k_total": alternative["k_total"],
                                  "k_delta": alternative["k_total"]-sum(old.values()),
                                  "allocation_l1": sum(abs(new[c]-old[c]) for c in old),
                                  "changed_provinces": [c for c in sorted(old) if new[c] != old[c]]})
    return scenarios


def evaluate(model, historical_counts=None):
    validate_model(model); results = []
    for alternative in model["alternatives"]:
        record = {"rule": alternative["rule"], **provincial_metrics(alternative["rows"], model["target_population_hypothesis"]),
                  "minimum_reference_violations": alternative["minimum_reference_violations"],
                  "within_constitutional_size_reference": alternative["within_constitutional_size_reference"],
                  "equals_congress_size_reference": alternative["equals_congress_size_reference"]}
        if historical_counts is not None:
            current = {r["province_code"]: r["k_assigned"] for r in alternative["rows"]}
            if set(current) != set(historical_counts):
                raise ValueError("HISTORICAL_COUNT_COVERAGE_INVALID")
            record["against_undated_historical_allocation"] = {"historical_k": sum(historical_counts.values()),
                "k_delta": alternative["k_total"]-sum(historical_counts.values()),
                "allocation_l1": sum(abs(current[c]-historical_counts[c]) for c in current),
                "province_k_deltas": {c: current[c]-historical_counts[c] for c in sorted(current)},
                "interpretation": "model_allocation_difference_not_administrative_change_or_map_correspondence"}
        results.append(record)
    scenarios = sensitivity(model)
    return {"metadata": metadata(), "approved_k_alternatives": [], "target_hypothesis": model["target_population_hypothesis"],
            "alternatives": results, "sensitivity_assumptions": {"basis_points": [-500,-100,100,500],
            "rounding": "nearest_half_up_per_province_population", "actual_temporal_change": False}, "sensitivity": scenarios}


def population_diagnostic(historical, reference):
    """Diferencia entre cifras, NO crecimiento 2022/2025 cuando la edición vieja falta."""
    if reference.get('population_year') != 2025:
        raise ValueError('POPULATION_REFERENCE_EDITION_INCOMPATIBLE')
    old=historical['province_population_reported_decimal']
    new={r['province_code']:r['population'] for r in reference['rows']}
    if set(old) != set(new) or len(new) != len(reference['rows']) or len(new) != 52:
        raise ValueError('POPULATION_DIAGNOSTIC_COVERAGE_INCOMPATIBLE')
    if sum(new.values()) != reference['national_population']:
        raise ValueError('POPULATION_REFERENCE_TOTAL_INCONSISTENT')
    old_values={c:Decimal(old[c]) for c in old}
    if any(not p.is_finite() or p < 0 for p in old_values.values()):
        raise ValueError('HISTORICAL_POPULATION_INVALID')
    rows=[{'province_code':c,'historical_population_reported':str(old_values[c]),
           'population_2025':new[c],'numeric_difference_not_temporal_growth':str(Decimal(new[c])-old_values[c])} for c in sorted(new)]
    return {'metadata':metadata(),'historical_population_edition':historical.get('historical_population_edition'),
            'reference_population_edition':2025,'status':'NUMERIC_DIAGNOSTIC_NOT_ACCREDITED_TEMPORAL_COMPARISON',
            'historical_total_reported':str(sum(old_values.values())), 'reference_total':reference['national_population'],
            'numeric_difference_not_temporal_growth':str(Decimal(reference['national_population'])-sum(old_values.values())),
            'province_rows':rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path); parser.add_argument("--historical-counts", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    raw = args.model.read_bytes(); model = json.loads(raw)
    counts = json.loads(args.historical_counts.read_text()) if args.historical_counts else None
    result = evaluate(model, counts)
    result["model_sha256"] = hashlib.sha256(raw).hexdigest()
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n")
    with args.output.with_suffix(".csv").open("x", encoding="utf-8", newline="") as output:
        fields = ["rule", "k_total", "unrepresented_population", "district_weighted_mae", "population_per_assigned_seat", "minimum_province_mean", "maximum_province_mean"]
        writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n"); writer.writeheader()
        for alternative in result["alternatives"]:
            row = {key: alternative[key] for key in fields}
            for key in ("minimum_province_mean", "maximum_province_mean"):
                row[key] = json.dumps(row[key], sort_keys=True)
            writer.writerow(row)
    print("PASS: cinco alternativas conservadas evaluadas; escenarios hipotéticos separados")


if __name__ == "__main__":
    main()
