from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Callable



class TerritorialDataError(ValueError):
    pass


_POP_INTEGER = re.compile(r"^-?(?:\d+|\d{1,3}(?:[.,]\d{3})+)$")


def parse_population_value(value: Any, *, section_id: str | None = None, label: str = "población") -> int:
    where = f" para sección {section_id}" if section_id else ""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        raise TerritorialDataError(f"POPULATION_MISSING: {label}{where}")
    if isinstance(value, bool):
        raise TerritorialDataError(f"POPULATION_NON_NUMERIC: {label}{where}: {value!r}")
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, float):
        if not math.isfinite(value) or not value.is_integer():
            raise TerritorialDataError(f"POPULATION_NON_INTEGER: {label}{where}: {value!r}")
        parsed = int(value)
    else:
        raw = str(value).strip().replace("\u00a0", "").replace(" ", "")
        if raw == "":
            raise TerritorialDataError(f"POPULATION_MISSING: {label}{where}")
        if not _POP_INTEGER.fullmatch(raw):
            raise TerritorialDataError(f"POPULATION_NON_NUMERIC: {label}{where}: {value!r}")
        parsed = int(raw.replace(".", "").replace(",", ""))
    if parsed < 0:
        raise TerritorialDataError(f"POPULATION_NEGATIVE: {label}{where}: {parsed}")
    return parsed


def strict_population_series(
    values,
    *,
    section_ids=None,
    label: str = "población",
    require_non_null: bool = True,
):
    import pandas as pd
    parsed = []
    ids = list(section_ids.astype(str)) if section_ids is not None else [None] * len(values)
    for value, section_id in zip(values.tolist(), ids, strict=False):
        try:
            parsed.append(parse_population_value(value, section_id=section_id, label=label))
        except TerritorialDataError as exc:
            if not require_non_null and str(exc).startswith("POPULATION_MISSING:"):
                parsed.append(pd.NA)
                continue
            raise
    result = pd.Series(parsed, index=values.index, dtype="Int64")
    if require_non_null and result.isna().any():
        raise TerritorialDataError(f"POPULATION_MISSING: {label}")
    return result


def normalized_unique_keys(
    values,
    *,
    normalize: Callable[[Any], str | None],
    label: str,
):
    import pandas as pd
    normalized = values.map(normalize)
    missing = normalized.isna() | normalized.astype("string").str.strip().eq("")
    if missing.any():
        sample = [str(values.loc[idx]) for idx in values.index[missing][:5]]
        raise TerritorialDataError(f"SECTION_ID_INVALID: {label}: {sample}")
    normalized = normalized.astype(str)
    duplicates = normalized[normalized.duplicated(keep=False)]
    if not duplicates.empty:
        sample = sorted(set(duplicates.tolist()))[:10]
        raise TerritorialDataError(f"SECTION_ID_DUPLICATE_AFTER_NORMALIZATION: {label}: {sample}")
    return normalized


def geometry_runtime_versions() -> dict[str, str]:
    import geopandas as gpd
    import pyproj
    import shapely

    return {
        "geopandas": str(gpd.__version__),
        "shapely": str(shapely.__version__),
        "geos": str(shapely.geos_version_string),
        "pyproj": str(pyproj.__version__),
    }


def invalid_geometry_diagnostics(
    gdf: Any,
    *,
    id_column: str | None = None,
) -> list[dict[str, str]]:
    import shapely
    from shapely.validation import explain_validity

    geometry = gdf.geometry
    if id_column is None:
        for candidate in ("CUSEC", "CUSEC_KEY", "section_id"):
            if candidate in getattr(gdf, "columns", []):
                id_column = candidate
                break

    diagnostics: list[dict[str, str]] = []
    for index, geom in geometry[~geometry.is_valid].items():
        feature_id = (
            str(gdf.at[index, id_column])
            if id_column and id_column in gdf.columns
            else str(index)
        )
        wkb = shapely.to_wkb(
            geom,
            hex=False,
            output_dimension=2,
            byte_order=1,
            include_srid=False,
        )
        diagnostics.append(
            {
                "feature_id": feature_id,
                "geometry_type": str(geom.geom_type),
                "reason": str(explain_validity(geom)),
                "parsed_geometry_wkb_sha256": hashlib.sha256(wkb).hexdigest(),
            }
        )
    diagnostics.sort(
        key=lambda row: (
            row["feature_id"],
            row["parsed_geometry_wkb_sha256"],
        )
    )
    return diagnostics


def validate_geodataframe(gdf: Any, *, label: str) -> None:
    crs = getattr(gdf, "crs", None)
    if crs is None or str(crs).strip() == "":
        raise TerritorialDataError(f"CRS_MISSING: {label}")
    try:
        from pyproj import CRS
        CRS.from_user_input(crs)
    except Exception as exc:
        raise TerritorialDataError(f"CRS_INVALID: {label}: {crs!r}") from exc

    try:
        geometry = gdf.geometry
    except Exception as exc:
        raise TerritorialDataError(f"GEOMETRY_MISSING: {label}") from exc

    null_mask = geometry.isna()
    if bool(null_mask.any()):
        raise TerritorialDataError(f"GEOMETRY_NULL: {label}: count={int(null_mask.sum())}")
    empty_mask = geometry.is_empty
    if bool(empty_mask.any()):
        raise TerritorialDataError(f"GEOMETRY_EMPTY: {label}: count={int(empty_mask.sum())}")
    valid_mask = geometry.is_valid
    if bool((~valid_mask).any()):
        defects = invalid_geometry_diagnostics(gdf)
        raise TerritorialDataError(
            f"GEOMETRY_INVALID: {label}: count={int((~valid_mask).sum())}; "
            f"defects={json.dumps(defects, ensure_ascii=False, sort_keys=True)}; "
            f"libraries={json.dumps(geometry_runtime_versions(), sort_keys=True)}"
        )
