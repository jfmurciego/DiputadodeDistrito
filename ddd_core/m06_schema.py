"""Canonical M06 district-catalog contract and explicit legacy aliases."""

from __future__ import annotations

import csv
from pathlib import Path


VERSION = "1.0.0"
CANONICAL_REQUIRED = (
    "district_id",
    "population",
    "target_population",
    "relative_deviation",
    "population_ratio",
    "population_floor",
    "population_cap",
    "within_hard_limits",
    "section_count",
    "municipality_count",
    "province_count",
    "area_km2",
    "perimeter_km",
    "polsby_popper",
)

LEGACY_ALIASES = {
    "district_pop": "population",
    "target": "target_population",
    "difference": "population_difference",
    "abs_difference": "abs_population_difference",
    "population_target_ratio": "population_ratio",
    "floor_population": "population_floor",
    "cap_population": "population_cap",
    "within_hard_bounds": "within_hard_limits",
    "compactness_polsby_popper": "polsby_popper",
    "centroid_x_etrs89_utm30": "centroid_x",
    "centroid_y_etrs89_utm30": "centroid_y",
}


def canonical_field(field: str) -> str:
    return LEGACY_ALIASES.get(field, field)


def inspect_catalog(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        source_fields = tuple(reader.fieldnames or ())
        rows = list(reader)
    canonical_fields = tuple(canonical_field(field) for field in source_fields)
    duplicates = sorted({field for field in canonical_fields if canonical_fields.count(field) > 1})
    missing = sorted(set(CANONICAL_REQUIRED) - set(canonical_fields))
    if duplicates or missing:
        raise ValueError(f"{path}: duplicates={duplicates}; missing={missing}")

    polsby_source = next(
        field for field in source_fields if canonical_field(field) == "polsby_popper"
    )
    values = [float(row[polsby_source]) for row in rows]
    if not rows or any(value < 0 or value > 1 for value in values):
        raise ValueError(f"{path}: polsby_popper ausente o fuera de [0,1]")
    migrations = {
        field: canonical_field(field)
        for field in source_fields
        if canonical_field(field) != field
    }
    return {
        "path": str(path),
        "rows": len(rows),
        "contract_version": VERSION,
        "canonical_fields": list(canonical_fields),
        "legacy_aliases_applied": migrations,
        "schema_status": "PASS_CANONICAL" if not migrations else "PASS_LEGACY_ADAPTED",
    }
