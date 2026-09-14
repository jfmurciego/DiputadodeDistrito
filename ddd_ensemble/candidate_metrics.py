from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def _edge_lengths(rectangle: Any) -> list[float]:
    coords = list(rectangle.exterior.coords)
    return [math.dist(coords[i], coords[i + 1]) for i in range(4)]


def measure_candidate(
    geojson_path: str,
    candidate_id: str,
    profile: str,
    seed: int,
    district_field: str = "district_id",
    population_field: str = "population",
    municipality_field: str = "municipality",
    comarca_field: str = "comarca",
    hard_constraints: dict[str, Any] | None = None,
    engine_run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        from shapely.geometry import shape
        from shapely.ops import unary_union
    except ImportError as exc:
        raise RuntimeError("Shapely 2.x es necesario para medir geometrías") from exc

    payload = json.loads(Path(geojson_path).read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not features:
        raise ValueError("El GeoJSON no contiene features")

    districts: dict[str, list[Any]] = defaultdict(list)
    population: dict[str, float] = defaultdict(float)
    comarca_district_pop: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    municipality_districts: dict[str, set[str]] = defaultdict(set)
    section_count = 0
    for feature in features:
        props = feature.get("properties", {})
        district = str(props.get(district_field, ""))
        if not district:
            raise ValueError(f"Falta {district_field} en una sección")
        pop = float(props.get(population_field, 0))
        if pop < 0:
            raise ValueError("La población no puede ser negativa")
        geom = shape(feature.get("geometry"))
        if geom.is_empty or not geom.is_valid:
            raise ValueError("Geometría vacía o inválida")
        districts[district].append(geom)
        population[district] += pop
        comarca = str(props.get(comarca_field, "SIN_COMARCA"))
        comarca_district_pop[comarca][district] += pop
        municipality = str(props.get(municipality_field, ""))
        if municipality:
            municipality_districts[municipality].add(district)
        section_count += 1

    ideal = sum(population.values()) / len(population)
    deviations = [abs(value / ideal - 1.0) if ideal else 0.0 for value in population.values()]
    pp_values: list[float] = []
    hull_ratios: list[float] = []
    elongations: list[float] = []
    corridor_alerts: list[str] = []
    for district, geometries in districts.items():
        dissolved = unary_union(geometries)
        area = dissolved.area
        perimeter = dissolved.length
        pp = 4 * math.pi * area / (perimeter * perimeter) if perimeter else 0.0
        hull_ratio = area / dissolved.convex_hull.area if dissolved.convex_hull.area else 0.0
        lengths = sorted(_edge_lengths(dissolved.minimum_rotated_rectangle))
        elongation = lengths[-1] / lengths[0] if lengths and lengths[0] else float("inf")
        pp_values.append(pp)
        hull_ratios.append(hull_ratio)
        elongations.append(elongation)
        if pp < 0.10 or hull_ratio < 0.35 or elongation > 4.0:
            corridor_alerts.append(district)

    split_comarcas = sum(1 for values in comarca_district_pop.values() if sum(v > 0 for v in values.values()) > 1)
    comarca_total = sum(sum(values.values()) for values in comarca_district_pop.values())
    comarca_retained = sum(max(values.values(), default=0.0) for values in comarca_district_pop.values())
    split_municipalities = sum(1 for values in municipality_districts.values() if len(values) > 1)

    report = {
        "schema": "ddd.candidate-report/1.0",
        "candidate_id": candidate_id,
        "profile": profile,
        "seed": seed,
        "geojson": str(Path(geojson_path).resolve()),
        "fields": {
            "district": district_field,
            "population": population_field,
            "municipality": municipality_field,
            "comarca": comarca_field,
        },
        # La geometría por sí sola no acredita contigüidad de grafo, K,
        # provincia o atomicidad. El motor/verificador debe aportar la puerta.
        "hard_constraints": hard_constraints or {"all_pass": False, "reason": "ENGINE_REPORT_REQUIRED"},
        "metrics": {
            "population": {
                "district_count": len(districts),
                "total": sum(population.values()),
                "max_deviation": max(deviations, default=0.0),
            },
            "shape": {
                "polsby_popper_min": min(pp_values),
                "polsby_popper_median": statistics.median(pp_values),
                "convex_hull_ratio_min": min(hull_ratios),
                "elongation_max": max(elongations),
                "corridor_alerts": corridor_alerts,
            },
            "comarca": {
                "split_count": split_comarcas,
                "retention_ratio": comarca_retained / comarca_total if comarca_total else 1.0,
            },
            "municipality": {"split_count": split_municipalities},
            "stability": {"assignment_delta": 0.0},
            "universe": {"section_count": section_count},
        },
    }
    if engine_run is not None:
        report["engine_run"] = engine_run
    return report
