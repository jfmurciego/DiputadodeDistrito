#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 8 — Join district geometry + election results (v7.0)

Input:
  - District dissolved GeoJSON from Step 6:
      district_id, district_name, district_pop, n_sections,
      dominant_comarca_id, dominant_comarca_name, sections_list, geometry
  - District election summary CSV from Step 7:
      district_id, district_name, total_votes, winner_party, winner_votes,
      winner_share, winner_bloc, <party>_votes, <party>_share, …

Output: single GeoJSON with ALL above columns merged on district_id.
  This file is ready to upload to Flourish or any choropleth tool.
  Columns: geometry + all district attributes + all election columns.

Run:
  python scripts/ddd_step8_join_results_v7_params.py --params params/ddd_params.yaml
"""
from __future__ import annotations
import sys, argparse, io, zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd

from ddd_core.config import load_params_yaml, step_cfg, require


def _gpd_read(path_or_buf):
    try:
        import pyogrio; return pyogrio.read_dataframe(path_or_buf)
    except Exception:
        return gpd.read_file(path_or_buf)


def load_gz(p: str) -> gpd.GeoDataFrame:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"No existe: {pp}")
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def save_gz(gdf: gpd.GeoDataFrame, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    suffix = pp.name.lower()
    if suffix.endswith(".geojson.zip"):
        tmp = pp.parent / (pp.stem.replace(".geojson","") + ".geojson")
        gdf.to_file(tmp, driver="GeoJSON")
        with zipfile.ZipFile(pp,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, arcname=tmp.name)
        try: tmp.unlink()
        except Exception: pass
    elif suffix.endswith(".geojson"):
        gdf.to_file(str(pp), driver="GeoJSON")
    else:
        gdf.to_file(str(pp), driver="GeoJSON")   # fallback


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s8  = step_cfg(cfg, "step8_join_results")
    s6  = step_cfg(cfg, "step6_export_final")
    s7  = step_cfg(cfg, "step7_aggregate_elections")

    # Read input paths — support both explicit step8 keys and fallback to step6/7 keys
    dist_geo = (s8.get("in_district_geojson","") or
                s6.get("out_district_geojson","") or "")
    dist_geo = require(dist_geo, "Falta steps.step8_join_results.in_district_geojson "
                                 "(o steps.step6_export_final.out_district_geojson)")

    results_csv = (s8.get("in_district_summary_csv","") or
                   s7.get("out_district_summary_csv","") or "")
    results_csv = require(results_csv, "Falta steps.step8_join_results.in_district_summary_csv "
                                       "(o steps.step7_aggregate_elections.out_district_summary_csv)")

    out_p = require(s8.get("out_districts_with_results_geojson",""),
                    "Falta steps.step8_join_results.out_districts_with_results_geojson")

    gdf = load_gz(dist_geo)
    df  = pd.read_csv(Path(results_csv).expanduser().resolve())

    if "district_id" not in gdf.columns:
        raise SystemExit("District GeoJSON no tiene 'district_id'.")
    if "district_id" not in df.columns:
        raise SystemExit("Results CSV no tiene 'district_id'.")

    gdf["district_id"] = gdf["district_id"].astype(str)
    df["district_id"]  = df["district_id"].astype(str)

    # Drop columns in df that already exist in gdf (except district_id) to avoid _x/_y
    dup_cols = [c for c in df.columns if c in gdf.columns and c != "district_id"]
    if dup_cols:
        print(f"[Step8] Descartando columnas duplicadas del CSV (ya en GeoJSON): {dup_cols}")
        df = df.drop(columns=dup_cols)

    out = gdf.merge(df, on="district_id", how="left")

    # Reproject to WGS84 for safe GeoJSON output
    try: out = out.to_crs(4326)
    except Exception: pass

    save_gz(out, out_p)
    print(f"[Step8] OK — {len(out)} distritos  columns={list(out.columns)}  out={out_p}")


if __name__ == "__main__":
    main()
