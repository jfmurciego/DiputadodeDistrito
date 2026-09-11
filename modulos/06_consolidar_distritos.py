#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 06 — Consolidar y describir distritos
VERSIÓN: 7.1.0
NOMBRE DE VERSIÓN: Catálogo territorial auditable
FECHA: 2026-09-11
QUÉ HACE: transforma la asignación M05 en productos territoriales finales de sección y distrito, catálogo distrital auditable y composición exacta por sección.
POR QUÉ ES SEPARADO: M05 optimiza la partición; M06 no puede cambiarla. Su responsabilidad es materializar, medir, describir y validar la solución antes de incorporar datos electorales u otros atributos posteriores.
ESTADO: candidato multi-territorio — CYL-05.
CAMBIOS: amplía v7.0.1 con catálogo distrital, composición por sección, métricas poblacionales, administrativas y geométricas, y validaciones de conservación de filas, población, K y provincia única.
MOTIVO: la documentación de M06 ya exigía entidades distritales auditables, pero v7.0.1 solo producía un resumen poblacional y geometría disuelta. El código debe cumplir el contrato documental antes de portar M06 a un segundo territorio.
ANTERIOR: legacy/modulo06/06_consolidar_distritos_v7.0.1.py
"""
from __future__ import annotations

import argparse
import io
import math
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ddd_core.config import load_params_yaml, module_cfg, require


def _gpd_read_file(path_or_buf, layer=None):
    try:
        import pyogrio
        return pyogrio.read_dataframe(path_or_buf, layer=layer)
    except Exception:
        pass
    try:
        return gpd.read_file(path_or_buf, layer=layer, engine="pyogrio")
    except Exception:
        return gpd.read_file(path_or_buf, layer=layer)


def load_geojson_any(path_str):
    p = Path(path_str).expanduser().resolve()
    if p.suffix.lower() == ".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p, "r") as z:
            members = [n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")]
            if not members:
                raise SystemExit(f"[Módulo 6] ZIP sin GeoJSON: {p}")
            return _gpd_read_file(io.BytesIO(z.read(members[0])))
    return _gpd_read_file(str(p))


def ensure_geojson_zip(gdf, out_zip):
    outp = Path(out_zip)
    outp.parent.mkdir(parents=True, exist_ok=True)
    tmp = outp.parent / (outp.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(outp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def joined_unique(series):
    vals = []
    seen = set()
    for x in series.dropna().astype(str):
        x = x.strip()
        if x and x not in seen:
            seen.add(x)
            vals.append(x)
    return " | ".join(sorted(vals))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s6 = module_cfg(cfg, "modulo_06_consolidar_distritos", legacy_step_key="step6_export_final")
    val = cfg.get("validation", {}) or {}

    in_geo = require(s6.get("in_geojson"), "Falta M06 entrada")
    id_field = require(s6.get("id_field"), "Falta M06 id")
    district_field = require(s6.get("district_field"), "Falta M06 distrito")
    pop_field = require(s6.get("pop_field"), "Falta M06 población")
    out_summary = require(s6.get("out_summary_csv"), "Falta M06 resumen")
    out_geo = s6.get("out_geojson", "")
    out_district_geo = s6.get("out_district_geojson", "")
    out_catalog = s6.get("out_catalog_csv", "")
    out_composition = s6.get("out_composition_csv", "")

    province_field = s6.get("province_field", val.get("province_field", "CPRO"))
    province_name_field = s6.get("province_name_field", "NPRO")
    municipality_field = s6.get("municipality_field", val.get("municipality_field", "CUMUN"))
    municipality_name_field = s6.get("municipality_name_field", val.get("municipality_name_field", "NMUN"))
    cudis_field = s6.get("cudis_field", "CUDIS")
    metric_crs = s6.get("metric_crs", "EPSG:3035")

    gdf = load_geojson_any(in_geo)
    for col in (id_field, district_field, pop_field):
        if col not in gdf.columns:
            raise SystemExit(f"[Módulo 6] Entrada sin columna '{col}'")
    if gdf.crs is None:
        raise SystemExit("[Módulo 6] Entrada sin CRS; no se pueden certificar métricas geométricas")

    df = gdf.copy()
    df[id_field] = df[id_field].astype(str)
    df[district_field] = pd.to_numeric(df[district_field], errors="raise").astype(int)
    df[pop_field] = pd.to_numeric(df[pop_field], errors="coerce").fillna(0).astype("int64")
    if province_field in df.columns:
        df[province_field] = df[province_field].astype(str).str.zfill(2)
    if municipality_field in df.columns:
        df[municipality_field] = df[municipality_field].astype(str)

    expected_k = int(s6.get("expected_districts", val.get("expected_districts", 0)) or 0)
    strict_k = bool(s6.get("strict_expected_k", True))
    n_rows = len(df)
    total_pop = int(df[pop_field].sum())

    if df[id_field].duplicated().any():
        dup = df.loc[df[id_field].duplicated(), id_field].iloc[0]
        raise SystemExit(f"[Módulo 6] ID de sección duplicado: {dup}")

    summary = (
        df.groupby(district_field, as_index=False)[pop_field]
        .sum()
        .rename(columns={pop_field: "district_pop", district_field: "district_id"})
        .sort_values("district_id")
        .reset_index(drop=True)
    )
    k = len(summary)
    if expected_k and strict_k and k != expected_k:
        raise SystemExit(f"[Módulo 6] ERROR: distritos={k} esperados={expected_k}")

    target = total_pop / k
    floor_ratio = float(val.get("population_floor_ratio", 0.80))
    cap_ratio = float(val.get("population_cap_ratio", 1.75))
    tol_ratio = float(val.get("target_tolerance_ratio", 0.12))
    floor = target * floor_ratio
    cap = target * cap_ratio
    tol = target * tol_ratio

    summary["target"] = target
    summary["difference"] = summary["district_pop"] - target
    summary["abs_difference"] = summary["difference"].abs()
    summary["relative_deviation"] = summary["difference"] / target
    summary["population_target_ratio"] = summary["district_pop"] / target
    summary["population_floor"] = floor
    summary["population_cap"] = cap
    summary["within_hard_bounds"] = (summary["district_pop"] >= floor) & (summary["district_pop"] <= cap)
    summary["within_target_tolerance"] = summary["relative_deviation"].abs() <= tol_ratio + 1e-12

    if not bool(summary["within_hard_bounds"].all()):
        bad = summary.loc[~summary["within_hard_bounds"], ["district_id", "district_pop"]].to_dict("records")
        raise SystemExit(f"[Módulo 6] Violación poblacional dura heredada de M05: {bad}")

    # Disolver solo después de certificar la asignación básica.
    dist = df[[district_field, pop_field, "geometry"]].copy().dissolve(
        by=district_field, aggfunc={pop_field: "sum"}, as_index=False
    ).rename(columns={district_field: "district_id", pop_field: "district_pop"})
    dist["district_id"] = dist["district_id"].astype(int)

    metric = dist.to_crs(metric_crs)
    area_m2 = metric.geometry.area
    perimeter_m = metric.geometry.length
    compactness = []
    for a, p in zip(area_m2, perimeter_m):
        compactness.append((4.0 * math.pi * a / (p * p)) if p > 0 else 0.0)
    cent = metric.geometry.centroid
    bounds = metric.geometry.bounds

    geom_metrics = pd.DataFrame({
        "district_id": metric["district_id"].astype(int),
        "area_km2": area_m2 / 1_000_000.0,
        "perimeter_km": perimeter_m / 1000.0,
        "polsby_popper": compactness,
        "centroid_x": cent.x,
        "centroid_y": cent.y,
        "bbox_minx": bounds.minx,
        "bbox_miny": bounds.miny,
        "bbox_maxx": bounds.maxx,
        "bbox_maxy": bounds.maxy,
        "metric_crs": metric_crs,
    })

    rows = []
    for d, x in df.groupby(district_field):
        row = {
            "district_id": int(d),
            "section_count": int(len(x)),
        }
        if municipality_field in x.columns:
            row["municipality_count"] = int(x[municipality_field].nunique())
            row["municipality_codes"] = joined_unique(x[municipality_field])
        if municipality_name_field in x.columns:
            row["municipality_names"] = joined_unique(x[municipality_name_field])
        if province_field in x.columns:
            row["province_count"] = int(x[province_field].nunique())
            row["province_codes"] = joined_unique(x[province_field])
            if bool(val.get("require_single_province_per_district", False)) and row["province_count"] != 1:
                raise SystemExit(f"[Módulo 6] Distrito {d} cruza provincias")
        if province_name_field in x.columns:
            row["province_names"] = joined_unique(x[province_name_field])
        rows.append(row)
    territorial = pd.DataFrame(rows)

    catalog = summary.merge(territorial, on="district_id", how="left").merge(geom_metrics, on="district_id", how="left")
    catalog = catalog.sort_values("district_id").reset_index(drop=True)

    # Composición exacta y reconstruible, sin depender de GIS.
    comp_cols = [id_field, district_field, pop_field]
    for col in (province_field, province_name_field, municipality_field, municipality_name_field, cudis_field, "ddd_unit_id", "ddd_closed_urban"):
        if col in df.columns and col not in comp_cols:
            comp_cols.append(col)
    composition = df[comp_cols].copy().rename(columns={district_field: "district_id", pop_field: "section_pop"})
    composition = composition.sort_values(["district_id", id_field]).reset_index(drop=True)

    if len(composition) != n_rows or int(composition["section_pop"].sum()) != total_pop:
        raise SystemExit("[Módulo 6] La composición no conserva filas o población")
    if int(catalog["district_pop"].sum()) != total_pop or len(catalog) != k:
        raise SystemExit("[Módulo 6] El catálogo no conserva población o K")

    outp = Path(out_summary)
    outp.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(outp, index=False)
    if out_catalog:
        p = Path(out_catalog); p.parent.mkdir(parents=True, exist_ok=True); catalog.to_csv(p, index=False)
    if out_composition:
        p = Path(out_composition); p.parent.mkdir(parents=True, exist_ok=True); composition.to_csv(p, index=False)
    if out_geo:
        ensure_geojson_zip(df, out_geo)
    if out_district_geo:
        dist_out = dist.merge(catalog.drop(columns=["district_pop"], errors="ignore"), on="district_id", how="left")
        ensure_geojson_zip(dist_out, out_district_geo)

    outside = int((~summary["within_target_tolerance"]).sum())
    print(
        f"[Módulo 6] OK v7.1.0 K={k} rows={n_rows} pop={total_pop} fuera_12={outside} "
        f"catalog={out_catalog or '-'} composition={out_composition or '-'} districts={out_district_geo or '-'}"
    )


if __name__ == "__main__":
    main()
