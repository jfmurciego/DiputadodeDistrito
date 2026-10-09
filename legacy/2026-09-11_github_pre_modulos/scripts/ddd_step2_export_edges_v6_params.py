#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 2 — Export adjacency edges (v6.0 unified params)

Run:
  python scripts/ddd_step2_export_edges_v6_params.py --params params/ddd_params.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import io
import json
import zipfile
from pathlib import Path as P
from typing import Iterable, Tuple

import geopandas as gpd

from ddd_core.config import load_params_yaml, step_cfg, require


def _gpd_read_file(path_or_buf, layer=None):
    """Robust reader: prefer pyogrio to avoid Shapely array-interface issues."""
    try:
        import pyogrio
        return pyogrio.read_dataframe(path_or_buf, layer=layer)
    except Exception:
        pass
    try:
        return gpd.read_file(path_or_buf, layer=layer, engine="pyogrio")
    except Exception:
        return gpd.read_file(path_or_buf, layer=layer)


def load_geojson_any(path_str: str) -> gpd.GeoDataFrame:
    p = P(path_str).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"GeoJSON no encontrado: {p}")
    if p.suffix.lower() == ".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p, "r") as z:
            members = [n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/") ]
            if not members:
                raise ValueError(f"ZIP GeoJSON sin .geojson/.json dentro: {p}")
            data = z.read(members[0])
        return _gpd_read_file(io.BytesIO(data))
    return _gpd_read_file(str(p))


def iter_edges(gdf: gpd.GeoDataFrame, id_field: str, predicate: str, min_shared_border_m: float,
              buffer_m: float, simplify_m: float, max_candidates: int, log_every: int) -> Iterable[Tuple[str, str]]:
    if id_field not in gdf.columns:
        raise SystemExit(f"id_field '{id_field}' no existe. Columnas: {list(gdf.columns)[:50]}")
    if gdf.empty:
        return []

    gdf = gdf.copy()
    gdf[id_field] = gdf[id_field].astype(str)

    if gdf.crs is None:
        gdf = gdf.set_crs(25830, allow_override=True)
    else:
        try:
            gdf = gdf.to_crs(25830)
        except Exception:
            pass

    geom = gdf.geometry
    if simplify_m and simplify_m > 0:
        geom = geom.simplify(simplify_m, preserve_topology=True)
    if buffer_m and buffer_m != 0:
        geom = geom.buffer(buffer_m)

    gdf["_geom_work"] = geom
    sindex = gdf.sindex

    seen = set()
    for i, row in gdf.iterrows():
        gi = row["_geom_work"]
        if gi is None or gi.is_empty:
            continue
        cand_idx = list(sindex.intersection(gi.bounds))
        if max_candidates and len(cand_idx) > max_candidates:
            ib = gi.bounds
            icx, icy = (ib[0] + ib[2]) / 2.0, (ib[1] + ib[3]) / 2.0

            def _dist(j):
                jb = gdf.loc[j, "_geom_work"].bounds
                jcx, jcy = (jb[0] + jb[2]) / 2.0, (jb[1] + jb[3]) / 2.0
                return (icx - jcx) ** 2 + (icy - jcy) ** 2

            cand_idx = sorted(cand_idx, key=_dist)[:max_candidates]

        u = row[id_field]
        for j in cand_idx:
            if j == i:
                continue
            v = gdf.loc[j, id_field]
            a, b = (u, v) if u < v else (v, u)
            key = (a, b)
            if key in seen:
                continue

            gj = gdf.loc[j, "_geom_work"]
            if gj is None or gj.is_empty:
                continue

            if predicate == "touches":
                ok = gi.touches(gj)
            elif predicate == "intersects":
                ok = gi.intersects(gj)
            else:
                raise SystemExit("predicate debe ser 'touches' o 'intersects'")

            if not ok:
                continue

            if min_shared_border_m and min_shared_border_m > 0:
                inter = gi.boundary.intersection(gj.boundary)
                blen = getattr(inter, "length", 0.0)
                if blen < min_shared_border_m:
                    continue

            seen.add(key)
            if log_every and len(seen) % log_every == 0:
                print(f"[Step2] edges={len(seen)}")
            yield key


def write_edges_jsonl(edges: Iterable[Tuple[str, str]], out_path: str) -> int:
    outp = P(out_path).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w", encoding="utf-8") as f:
        for u, v in edges:
            f.write(json.dumps({"u": u, "v": v}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description="DDD Step2 (unified params).")
    ap.add_argument("--params", required=True, help="YAML único DDD_params.yaml")
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s2 = step_cfg(cfg, "step2_export_edges")

    in_geo = require(s2.get("in_geojson", ""), "Falta steps.step2_export_edges.in_geojson")
    id_field = require(s2.get("id_field", ""), "Falta steps.step2_export_edges.id_field")
    out_edges = require(s2.get("out_edges_jsonl", ""), "Falta steps.step2_export_edges.out_edges_jsonl")

    predicate = s2.get("predicate", "touches")
    min_shared = float(s2.get("min_shared_border_m", 0.0) or 0.0)
    buffer_m = float(s2.get("buffer_m", 0.0) or 0.0)
    simplify_m = float(s2.get("simplify_m", 0.0) or 0.0)
    max_candidates = int(s2.get("max_candidates", 50) or 50)
    log_every = int(s2.get("log_every", 10000) or 10000)

    gdf = load_geojson_any(in_geo)
    edges = iter_edges(gdf, id_field, predicate, min_shared, buffer_m, simplify_m, max_candidates, log_every)
    n = write_edges_jsonl(edges, out_edges)
    print(f"[Step2] OK edges={n} out={out_edges}")


if __name__ == "__main__":
    main()
