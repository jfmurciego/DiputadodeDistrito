#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 6 — Export final artifacts + district naming (v7.0)

Critical changes vs v6:
  1. District dissolved GeoJSON carries ALL attributes:
       district_id, district_name, district_pop, n_sections,
       dominant_comarca_id, dominant_comarca_name, sections_list
  2. District naming built in here (no separate step needed):
       Urban capitals → cardinal direction  (Zaragoza Norte, Huesca Sur…)
       Rural majority comarca (≥60%) → comarca name
       Two comarcas each ≥25% → "Eje ComarcaA-ComarcaB"
       Duplicates get Roman numeral suffix (I, II…)
  3. Sections GeoJSON also gets district_name so Steps 7/8 inherit it.
  4. Summary CSV contains all district attributes for downstream use.

How to avoid dissolve losing columns
-------------------------------------
geopandas dissolve(aggfunc=…) only keeps columns listed in aggfunc plus
the geometry. We work around this by:
  a) Computing all district-level attributes from the section rows FIRST
     (population, comarca counts, sections list, names).
  b) Dissolving ONLY geometry.
  c) Merging the pre-computed attributes back onto the dissolved geometry.
This is the only reliable pattern — do NOT rely on aggfunc to carry attrs.

Run:
  python scripts/ddd_step6_export_final_v7_params.py --params params/ddd_params.yaml
"""
from __future__ import annotations
import sys, argparse, io, json, zipfile, math, collections
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd

from ddd_core.config import load_params_yaml, step_cfg, require

# ── I/O ──────────────────────────────────────────────────────────────────────
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
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def save_gz(gdf: gpd.GeoDataFrame, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    if not (pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip")):
        raise SystemExit(f"out_geojson debe terminar en .geojson.zip — recibido: {p}")
    tmp = pp.parent / (pp.stem.replace(".geojson","") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(pp,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    try: tmp.unlink()
    except Exception: pass


# ── District naming ───────────────────────────────────────────────────────────
_ROMAN = ["","I","II","III","IV","V","VI","VII","VIII","IX","X"]

def _cardinal(dx: float, dy: float) -> str:
    """Cardinal direction of district centroid relative to city centre."""
    ang = math.degrees(math.atan2(dx, dy))   # N=0°, E=90°
    if   -45 <= ang <  45: return "Norte"
    if    45 <= ang < 135: return "Este"
    if   ang >= 135 or ang < -135: return "Sur"
    return "Oeste"


def _to_metric(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None: gdf = gdf.set_crs(4326)
    try: return gdf.to_crs(25830)
    except Exception: return gdf


def build_names(
    dist_centroids: Dict[str, Tuple[float,float]],
    dist_comarca_counts: Dict[str, Dict[str,int]],
    dist_comarca_names:  Dict[str, Dict[str,str]],
    urban_capitals: List[Dict[str,Any]],
    urban_radius_m: float,
    centro_radius_m: float,
    comarca_majority_pct: float,
    eje_min_pct: float,
    eje_prefix: str,
) -> Dict[str,str]:
    raw: Dict[str,str] = {}

    for did, (cx, cy) in dist_centroids.items():
        # 1. Urban check — cardinal from city centre
        urban_label: Optional[str] = None
        for cap in urban_capitals:
            dist = math.hypot(cx - float(cap["x_m"]), cy - float(cap["y_m"]))
            if dist <= urban_radius_m:
                if dist <= centro_radius_m:
                    urban_label = f"{cap['name']} Centro"
                else:
                    dx = cx - float(cap["x_m"]); dy = cy - float(cap["y_m"])
                    urban_label = f"{cap['name']} {_cardinal(dx, dy)}"
                break
        if urban_label:
            raw[did] = urban_label; continue

        # 2. Comarca-based naming
        votes  = dist_comarca_counts.get(did, {})
        id2nm  = dist_comarca_names.get(did, {})
        total  = sum(votes.values())
        if not total:
            raw[did] = f"Distrito {did}"; continue

        sorted_v = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        top_id, top_n = sorted_v[0]
        top_pct = top_n / total

        def cname(cid: str) -> str:
            return id2nm.get(cid, cid) or cid

        if top_pct >= comarca_majority_pct:
            raw[did] = cname(top_id); continue

        if len(sorted_v) >= 2:
            c2_id, c2_n = sorted_v[1]
            if top_n/total >= eje_min_pct and c2_n/total >= eje_min_pct:
                raw[did] = f"{eje_prefix} {cname(top_id)}-{cname(c2_id)}"; continue

        raw[did] = cname(top_id)

    # 3. Ordinal suffixes for duplicate names
    counts = collections.Counter(raw.values())
    usage:  Dict[str,int] = {}
    final:  Dict[str,str] = {}
    for did in sorted(raw, key=lambda x: (int(x) if str(x).lstrip("-").isdigit() else 0)):
        name = raw[did]
        if counts[name] > 1:
            n = usage.get(name, 0) + 1; usage[name] = n
            suffix = f" {_ROMAN[n]}" if n < len(_ROMAN) else f" {n}"
            final[did] = name + suffix
        else:
            final[did] = name
    return final


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s6  = step_cfg(cfg, "step6_export_final")

    in_geo     = require(s6.get("in_geojson",""),     "Falta steps.step6_export_final.in_geojson")
    id_field   = require(s6.get("id_field",""),       "Falta steps.step6_export_final.id_field")
    dist_field = require(s6.get("district_field",""), "Falta steps.step6_export_final.district_field")
    pop_field  = require(s6.get("pop_field",""),      "Falta steps.step6_export_final.pop_field")
    out_csv    = require(s6.get("out_summary_csv",""),"Falta steps.step6_export_final.out_summary_csv")
    out_sec_gz = s6.get("out_geojson","")          or ""   # sections GeoJSON
    out_dst_gz = s6.get("out_district_geojson","") or ""   # dissolved district GeoJSON

    cid_col = s6.get("comarca_id_field",   "comarca_id")   or "comarca_id"
    cnm_col = s6.get("comarca_name_field", "comarca_name") or "comarca_name"

    urban_caps_raw   = s6.get("urban_capitals", [])       or []
    urban_radius_m   = float(s6.get("urban_radius_m",  15000) or 15000)
    centro_radius_m  = float(s6.get("centro_radius_m",  3000) or 3000)
    com_majority_pct = float(s6.get("comarca_majority_pct", 0.60) or 0.60)
    eje_min_pct      = float(s6.get("eje_min_pct",          0.25) or 0.25)
    eje_prefix       = s6.get("eje_prefix", "Eje") or "Eje"

    # ── Load sections GeoJSON ──────────────────────────────────────────────
    gdf = load_geojson(in_geo)
    for col in (id_field, dist_field, pop_field):
        if col not in gdf.columns:
            raise SystemExit(f"Falta columna '{col}'. Columnas: {list(gdf.columns)[:40]}")

    has_cid = cid_col in gdf.columns
    has_cnm = cnm_col in gdf.columns
    has_comarca = has_cid and has_cnm
    if not has_comarca:
        print(f"[Step6] AVISO: comarca columns '{cid_col}'/'{cnm_col}' no encontradas. "
              "Nombres serán 'Distrito N'. Activa comarcas.enabled=true en YAML.")

    gdf = gdf.copy()
    gdf[id_field]   = gdf[id_field].astype(str)
    gdf[dist_field] = gdf[dist_field].astype(str)
    gdf[pop_field]  = pd.to_numeric(gdf[pop_field], errors="coerce").fillna(0).astype("int64")

    # ── Expected K check ──────────────────────────────────────────────────
    exp_k = int(s6.get("expected_districts") or
                (step_cfg(cfg,"step4_seed_districts") or {}).get("k_districts",0) or 0)
    strict = bool(s6.get("strict_expected_k", True))
    n_dists = gdf[dist_field].nunique()
    if exp_k and strict and n_dists != exp_k:
        raise SystemExit(f"[Step6] ERROR: distritos={n_dists} expected={exp_k}. "
                         "Revisa Step5 (district_id cardinalidad incorrecta).")

    # ── Compute all district attributes from section rows ─────────────────
    # (Do this BEFORE dissolve — dissolve only touches geometry)
    dist_pop:  Dict[str,int]            = {}
    dist_nsec: Dict[str,int]            = {}
    dist_secs: Dict[str,List[str]]      = {}
    dist_cid_votes: Dict[str,Dict[str,int]] = {}
    dist_cid_names: Dict[str,Dict[str,str]] = {}

    def _s(v: Any) -> str:
        return "" if (v is None or (isinstance(v,float) and pd.isna(v))) else str(v).strip()

    for _, row in gdf.iterrows():
        did = str(row[dist_field])
        dist_pop[did]  = dist_pop.get(did, 0) + int(row[pop_field])
        dist_nsec[did] = dist_nsec.get(did, 0) + 1
        dist_secs.setdefault(did, []).append(str(row[id_field]))
        if has_comarca:
            cid = _s(row[cid_col]); cnm = _s(row[cnm_col])
            if cid:
                dist_cid_votes.setdefault(did, {})
                dist_cid_names.setdefault(did, {})
                dist_cid_votes[did][cid] = dist_cid_votes[did].get(cid, 0) + 1
                if cnm: dist_cid_names[did][cid] = cnm

    def dominant_comarca(did: str) -> Tuple[str,str]:
        votes = dist_cid_votes.get(did, {})
        if not votes: return "", ""
        top = max(votes, key=votes.__getitem__)
        return top, dist_cid_names.get(did,{}).get(top,"")

    # ── Convert urban capital lon/lat → metric (ETRS89 UTM30N) ───────────
    urban_capitals: List[Dict[str,Any]] = []
    if urban_caps_raw:
        try:
            import pyproj
            tr = pyproj.Transformer.from_crs("EPSG:4326","EPSG:25830",always_xy=True)
            for cap in urban_caps_raw:
                c = dict(cap)
                if "x_m" not in c and "lon" in c and "lat" in c:
                    c["x_m"], c["y_m"] = tr.transform(float(c["lon"]), float(c["lat"]))
                urban_capitals.append(c)
        except Exception as e:
            print(f"[Step6] AVISO: coord transform fallida ({e}) — nombres urbanos desactivados.")

    # ── Centroids of dissolved districts (metric) for naming ─────────────
    gdf_m = _to_metric(gdf[[dist_field,"geometry"]].copy())
    dissolved_geom = gdf_m.dissolve(by=dist_field, as_index=False)[["district_id" if "district_id"==dist_field else dist_field, "geometry"]]
    # rename to district_id for clarity
    dissolved_geom = dissolved_geom.rename(columns={dist_field: "district_id"})

    dist_centroids: Dict[str,Tuple[float,float]] = {}
    for _, row in dissolved_geom.iterrows():
        ctr = row.geometry.centroid
        dist_centroids[str(row["district_id"])] = (float(ctr.x), float(ctr.y))

    # ── Naming ────────────────────────────────────────────────────────────
    names = build_names(
        dist_centroids       = dist_centroids,
        dist_comarca_counts  = dist_cid_votes,
        dist_comarca_names   = dist_cid_names,
        urban_capitals       = urban_capitals,
        urban_radius_m       = urban_radius_m,
        centro_radius_m      = centro_radius_m,
        comarca_majority_pct = com_majority_pct,
        eje_min_pct          = eje_min_pct,
        eje_prefix           = eje_prefix,
    )

    # ── Build district attributes DataFrame ───────────────────────────────
    all_dids = sorted(dist_pop.keys(), key=lambda x: (int(x) if x.lstrip("-").isdigit() else 0))
    district_attrs = pd.DataFrame({
        "district_id":           all_dids,
        "district_name":         [names.get(d, f"Distrito {d}") for d in all_dids],
        "district_pop":          [dist_pop.get(d, 0) for d in all_dids],
        "n_sections":            [dist_nsec.get(d, 0) for d in all_dids],
        "dominant_comarca_id":   [dominant_comarca(d)[0] for d in all_dids],
        "dominant_comarca_name": [dominant_comarca(d)[1] for d in all_dids],
        "sections_list":         ["|".join(sorted(dist_secs.get(d,[]))) for d in all_dids],
    })

    # ── Summary CSV (all district attributes) ─────────────────────────────
    out_p = Path(out_csv).expanduser().resolve()
    out_p.parent.mkdir(parents=True, exist_ok=True)
    district_attrs.to_csv(out_p, index=False)
    print(f"[Step6] Resumen CSV: {out_csv}")

    # ── Dissolved district GeoJSON ────────────────────────────────────────
    # Dissolve geometry only (no aggfunc for attributes — we merge separately)
    gdf_for_dissolve = gdf[[dist_field, "geometry"]].copy()
    gdf_for_dissolve[dist_field] = gdf_for_dissolve[dist_field].astype(str)
    dist_gdf = gdf_for_dissolve.dissolve(by=dist_field, as_index=False)
    dist_gdf = dist_gdf.rename(columns={dist_field: "district_id"})

    # Reproject to WGS84 for GeoJSON output
    try: dist_gdf = dist_gdf.to_crs(4326)
    except Exception: pass

    # Merge ALL pre-computed attributes — this is how columns survive dissolve
    dist_gdf = dist_gdf.merge(district_attrs, on="district_id", how="left")

    if out_dst_gz:
        save_gz(dist_gdf, out_dst_gz)
        print(f"[Step6] Districts GeoJSON: {out_dst_gz}")

    # ── Sections GeoJSON — add district_name + comarca attrs so Step7 inherits
    if out_sec_gz:
        sec_out = gdf.copy()
        sec_out["district_name"] = sec_out[dist_field].map(names).fillna("Sin nombre")
        if has_comarca:
            sec_out["dominant_comarca_id"]   = sec_out[dist_field].map(lambda d: dominant_comarca(d)[0])
            sec_out["dominant_comarca_name"] = sec_out[dist_field].map(lambda d: dominant_comarca(d)[1])
        save_gz(sec_out, out_sec_gz)
        print(f"[Step6] Sections GeoJSON: {out_sec_gz}")

    # ── Console summary ───────────────────────────────────────────────────
    print(f"\n[Step6] OK — {len(all_dids)} distritos")
    for _, row in district_attrs.iterrows():
        print(f"  {str(row['district_id']):>3} → {row['district_name']:<35} "
              f"pop={row['district_pop']:>8,}  n={row['n_sections']:>3}  "
              f"comarca={row['dominant_comarca_name']}")


if __name__ == "__main__":
    main()
