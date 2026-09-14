#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 2 — Export adjacency edges (v7.0)

Bugs fixed vs v6.0:
  1. buffer_m + predicate='touches' always produced 0 edges.
     When geometries are buffered they OVERLAP — touching requires only
     boundary contact with no interior overlap, so touches() always returns
     False for buffered polygons. Fix: when buffer_m > 0, use 'intersects'.
  2. Spatial index was built on original geometry, not on buffered geometry,
     so candidates from sindex.intersection() were wrong after buffering.
     Fix: set gdf.geometry = buffered geometry before building sindex.
  3. Added diagnostic output: prints CRS, geometry type, first few IDs so
     you can immediately see if something is wrong with the input.

Run:
  python scripts/ddd_step2_export_edges_v7_params.py --params params/ddd_params.yaml
"""
from __future__ import annotations
import sys, argparse, io, json, zipfile
from pathlib import Path
from typing import Iterable, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd

from ddd_core.config import load_params_yaml, step_cfg, require


def _gpd_read(path_or_buf, layer=None):
    try:
        import pyogrio; return pyogrio.read_dataframe(path_or_buf, layer=layer)
    except Exception: pass
    try:
        return gpd.read_file(path_or_buf, layer=layer, engine="pyogrio")
    except Exception:
        return gpd.read_file(path_or_buf, layer=layer)


def load_geojson(p: str) -> gpd.GeoDataFrame:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"GeoJSON no encontrado: {pp}")
    if pp.suffix.lower() == ".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm = [n for n in z.namelist()
                  if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def iter_edges(
    gdf: gpd.GeoDataFrame,
    id_field: str,
    predicate: str,
    min_shared_border_m: float,
    buffer_m: float,
    simplify_m: float,
    max_candidates: int,
    log_every: int,
) -> Iterable[Tuple[str, str]]:

    if id_field not in gdf.columns:
        raise SystemExit(f"id_field '{id_field}' no existe. Columnas: {list(gdf.columns)[:50]}")
    if gdf.empty:
        return

    gdf = gdf[[id_field, "geometry"]].copy()
    gdf[id_field] = gdf[id_field].astype(str)

    # ── CRS → metric (ETRS89 UTM30N) ──────────────────────────────────────
    if gdf.crs is None:
        print("[Step2] AVISO: CRS no definido en el GeoJSON — asumiendo EPSG:25830 (ETRS89 UTM30N).")
        gdf = gdf.set_crs(25830, allow_override=True)
    else:
        try:
            gdf = gdf.to_crs(25830)
        except Exception as e:
            print(f"[Step2] AVISO: No se pudo reproyectar a EPSG:25830: {e}")

    print(f"[Step2] CRS activo: {gdf.crs}  |  filas={len(gdf)}  |  "
          f"primeros IDs: {list(gdf[id_field].head(3))}")

    # ── Simplify first (on original metric geometry) ───────────────────────
    if simplify_m and simplify_m > 0:
        gdf["geometry"] = gdf.geometry.simplify(simplify_m, preserve_topology=True)

    # ── Buffer ────────────────────────────────────────────────────────────
    # KEY FIX: buffer BEFORE building sindex, and switch predicate to
    # 'intersects' because buffered polygons overlap, not merely touch.
    effective_predicate = predicate
    if buffer_m and buffer_m != 0:
        gdf["geometry"] = gdf.geometry.buffer(buffer_m)
        if predicate == "touches":
            effective_predicate = "intersects"
            print(f"[Step2] buffer_m={buffer_m} → predicate forzado a 'intersects' "
                  "(buffered polygons overlap, no longer merely touch).")

    # ── Spatial index on the (possibly buffered) geometry ─────────────────
    gdf = gdf.set_geometry("geometry")
    sindex = gdf.sindex

    seen = set()
    for i, row in gdf.iterrows():
        gi = row["geometry"]
        if gi is None or gi.is_empty:
            continue

        cand_idx = list(sindex.intersection(gi.bounds))

        # Limit candidates to nearest N by centroid distance (avoid O(n²) for dense areas)
        if max_candidates and len(cand_idx) > max_candidates:
            ib = gi.bounds
            icx = (ib[0] + ib[2]) / 2.0
            icy = (ib[1] + ib[3]) / 2.0
            def _d(j):
                jb = gdf.loc[j, "geometry"].bounds
                return (icx - (jb[0]+jb[2])/2)**2 + (icy - (jb[1]+jb[3])/2)**2
            cand_idx = sorted(cand_idx, key=_d)[:max_candidates]

        u = row[id_field]
        for j in cand_idx:
            if j == i:
                continue
            v = gdf.loc[j, id_field]
            a, b = (u, v) if u < v else (v, u)
            key = (a, b)
            if key in seen:
                continue

            gj = gdf.loc[j, "geometry"]
            if gj is None or gj.is_empty:
                continue

            if effective_predicate == "touches":
                ok = gi.touches(gj)
            elif effective_predicate == "intersects":
                ok = gi.intersects(gj)
            else:
                raise SystemExit(f"predicate desconocido: '{effective_predicate}' — usa 'touches' o 'intersects'")

            if not ok:
                continue

            if min_shared_border_m and min_shared_border_m > 0:
                inter = gi.boundary.intersection(gj.boundary)
                if getattr(inter, "length", 0.0) < min_shared_border_m:
                    continue

            seen.add(key)
            if log_every and len(seen) % log_every == 0:
                print(f"[Step2] edges={len(seen)}")
            yield key


def write_edges_jsonl(edges: Iterable[Tuple[str, str]], out_path: str) -> int:
    outp = Path(out_path).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with outp.open("w", encoding="utf-8") as f:
        for u, v in edges:
            f.write(json.dumps({"u": u, "v": v}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s2  = step_cfg(cfg, "step2_export_edges")

    in_geo      = require(s2.get("in_geojson", ""),      "Falta steps.step2_export_edges.in_geojson")
    id_field    = require(s2.get("id_field", ""),        "Falta steps.step2_export_edges.id_field")
    out_edges   = require(s2.get("out_edges_jsonl", ""), "Falta steps.step2_export_edges.out_edges_jsonl")

    predicate      = s2.get("predicate",           "touches")
    min_shared     = float(s2.get("min_shared_border_m", 0.0) or 0.0)
    buffer_m       = float(s2.get("buffer_m",           0.0) or 0.0)
    simplify_m     = float(s2.get("simplify_m",         0.0) or 0.0)
    max_candidates = int(s2.get("max_candidates",        50) or 50)
    log_every      = int(s2.get("log_every",          10000) or 10000)

    print(f"[Step2] buffer_m={buffer_m}  predicate={predicate}  simplify_m={simplify_m}")

    gdf = load_geojson(in_geo)
    edges = iter_edges(gdf, id_field, predicate, min_shared, buffer_m, simplify_m, max_candidates, log_every)
    n = write_edges_jsonl(edges, out_edges)

    if n == 0:
        print("\n[Step2] AVISO: edges=0 — no se encontraron secciones adyacentes.")
        print("  Revisa que:")
        print("  - El GeoJSON de Step1 contiene geometrías válidas y no vacías")
        print("  - buffer_m es suficiente (prueba 10.0 o 20.0 si el seccionado tiene huecos grandes)")
        print("  - El CRS se proyectó correctamente a EPSG:25830 (ver línea CRS activo arriba)")
    else:
        print(f"[Step2] OK edges={n} out={out_edges}")


if __name__ == "__main__":
    main()
