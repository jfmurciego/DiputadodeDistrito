#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 7 — Aggregate election results to districts (v7.0)

Changes vs v6.1:
  - Reads district_name, dominant_comarca_name from the input GeoJSON
    (written by Step 6 v7) and carries them through to ALL output files.
  - Summary CSV now has columns:
      district_id, district_name, dominant_comarca_name,
      total_votes, winner_party, winner_votes, winner_share, winner_bloc,
      <party>_votes, <party>_share   (one column pair per party)
  - Party long CSV unchanged.
  - Sections enriched GeoJSON also carries district_name.
  - RTVE JSON parsing identical to v6.1.

Run:
  python scripts/ddd_step7_aggregate_elections_v7_params.py --params params/ddd_params.yaml
"""
from __future__ import annotations
import sys, argparse, io, json, zipfile, re
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd

from ddd_core.config import load_params_yaml, step_cfg, require


# ── I/O ──────────────────────────────────────────────────────────────────────
def _gpd_read(path_or_buf):
    try:
        import pyogrio; return pyogrio.read_dataframe(path_or_buf)
    except Exception:
        return gpd.read_file(path_or_buf)


def load_geojson(p: str) -> gpd.GeoDataFrame:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"GeoJSON: {pp}")
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm=[n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def save_gz(gdf: gpd.GeoDataFrame, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        tmp = pp.parent / (pp.stem.replace(".geojson","") + ".geojson")
        gdf.to_file(tmp, driver="GeoJSON")
        with zipfile.ZipFile(pp,"w",compression=zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, arcname=tmp.name)
        try: tmp.unlink()
        except Exception: pass
    else:
        gdf.to_file(p, driver="GeoJSON")


def read_text(p: str) -> str:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"Fichero: {pp}")
    if pp.suffix.lower()==".zip":
        with zipfile.ZipFile(pp) as z:
            nm=[n for n in z.namelist() if not n.endswith("/")]
            return z.read(nm[0]).decode("utf-8","replace")
    return pp.read_text(encoding="utf-8", errors="replace")


def normalize_party(x: Any) -> str:
    if x is None: return ""
    return re.sub(r"\s+", " ", str(x).strip())


def _get_path(obj: Any, dotted: str) -> Any:
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict): cur = cur.get(part)
        else: return None
    return cur


# ── Results loader (identical logic to v6.1) ─────────────────────────────────
def load_results(
    path: str, section_key: str, party_col: str, votes_col: str, sep: str,
    rtve_enabled: bool, rtve_zonas_path: str, rtve_sec_field: str,
    rtve_party_list: str, rtve_party_field: str, rtve_votes_field: str,
) -> pd.DataFrame:
    txt = read_text(path).lstrip()
    rows: List[Dict[str,Any]] = []

    def emit(sec: Any, party: Any, votes: Any):
        if sec is None: return
        p = normalize_party(party)
        if not p: return
        try: v = int(float(votes))
        except Exception: return
        rows.append({section_key: str(sec), "party": p, "votes": v})

    if txt.startswith("{") or txt.startswith("["):
        obj = json.loads(txt)
        # RTVE format
        if rtve_enabled and isinstance(obj, dict):
            zonas = _get_path(obj, rtve_zonas_path)
            if isinstance(zonas, list) and zonas and isinstance(zonas[0], dict) \
               and rtve_sec_field in zonas[0]:
                for z in zonas:
                    sec = z.get(rtve_sec_field)
                    for it in (z.get(rtve_party_list) or []):
                        if isinstance(it, dict):
                            emit(sec, it.get(rtve_party_field), it.get(rtve_votes_field))
                df = pd.DataFrame(rows)
                if not df.empty:
                    df["party"]  = df["party"].map(normalize_party)
                    df["votes"]  = pd.to_numeric(df["votes"], errors="coerce").fillna(0).astype("int64")
                    df[section_key] = df[section_key].astype(str)
                    return df[[section_key,"party","votes"]]

        # Generic JSON (unchanged from v6.1)
        if isinstance(obj, dict):
            for sec, payload in obj.items():
                if isinstance(payload, dict):
                    for key in ["results","parties","votos","votes"]:
                        if key in payload and isinstance(payload[key],(list,dict)):
                            part = payload[key]
                            if isinstance(part, dict):
                                for p,v in part.items(): emit(sec, p, v)
                            else:
                                for it in part:
                                    if isinstance(it, dict):
                                        emit(sec, it.get("party") or it.get("siglas") or it.get("name"),
                                             it.get("votes") or it.get("votos"))
                            break
                    else:
                        for p,v in payload.items():
                            if isinstance(v,(int,float)) and len(str(p))<=25: emit(sec,p,v)
                elif isinstance(payload, list):
                    for it in payload:
                        if isinstance(it, dict):
                            emit(sec, it.get("party") or it.get("siglas"), it.get("votes") or it.get("votos"))
        elif isinstance(obj, list):
            for it in obj:
                if not isinstance(it, dict): continue
                sec = (it.get(section_key) or it.get("section") or it.get("seccion") or
                       it.get("CUSEC") or it.get("CESUC") or it.get("CUSEC_KEY") or it.get("id"))
                for key in ["results","parties","votos","votes"]:
                    if key in it and isinstance(it[key],(list,dict)):
                        part = it[key]
                        if isinstance(part, dict):
                            for p,v in part.items(): emit(sec, p, v)
                        else:
                            for r in part:
                                if isinstance(r, dict):
                                    emit(sec, r.get("party") or r.get("siglas"), r.get("votes") or r.get("votos"))
                        break
                else:
                    if ("party" in it or party_col in it) and ("votes" in it or votes_col in it or "votos" in it):
                        emit(sec, it.get("party") or it.get(party_col), it.get("votes") or it.get("votos") or it.get(votes_col))
                    else:
                        for p,v in it.items():
                            if p in [section_key,"section","seccion","CUSEC","CESUC","CUSEC_KEY","id"]: continue
                            if isinstance(v,(int,float)) and len(str(p))<=25: emit(sec, p, v)

        df = pd.DataFrame(rows)
        if df.empty:
            if isinstance(obj,dict) and _get_path(obj,"mapa.zonas") is not None:
                raise ValueError("JSON RTVE detectado pero sin votos extraídos. Revisa json_rtve_* en YAML.")
            raise ValueError("JSON leído pero sin votos por partido. Revisa formato/claves.")
        df["party"] = df["party"].map(normalize_party)
        df["votes"] = pd.to_numeric(df["votes"],errors="coerce").fillna(0).astype("int64")
        df[section_key] = df[section_key].astype(str)
        return df[[section_key,"party","votes"]]

    # CSV
    from io import StringIO
    first = txt.splitlines()[0] if txt else ""
    sep_use = sep if sep != "auto" else (";" if first.count(";") > first.count(",") else ",")
    df = pd.read_csv(StringIO(txt), sep=sep_use)
    cols = list(df.columns)
    # detect section col
    if section_key in cols:
        sec_col = section_key
    else:
        for c in ["CUSEC_KEY","CUSEC","CESUC","SECCION","section_id","seccion"]:
            if c in cols: sec_col=c; break
        else:
            for c in cols:
                if "CUSEC" in c.upper() or "SECC" in c.upper(): sec_col=c; break
            else:
                raise ValueError(f"No encuentro columna sección en CSV. Columnas: {cols[:40]}")
    df = df.rename(columns={sec_col: section_key})
    if party_col in df.columns and votes_col in df.columns:
        out = df[[section_key, party_col, votes_col]].rename(columns={party_col:"party", votes_col:"votes"})
        out["party"] = out["party"].map(normalize_party)
        out["votes"] = pd.to_numeric(out["votes"],errors="coerce").fillna(0).astype("int64")
        out[section_key] = out[section_key].astype(str)
        return out[out["party"]!=""][[section_key,"party","votes"]]
    # Wide CSV — pivot to long
    id_like = {section_key}
    good = [c for c in df.columns if c not in id_like and (
        pd.api.types.is_numeric_dtype(df[c]) or
        pd.to_numeric(df[c], errors="coerce").notna().mean() > 0.6
    )]
    if not good: raise ValueError(f"CSV no usable. Columnas: {cols[:60]}")
    long = df[[section_key]+good].melt(id_vars=[section_key], var_name="party", value_name="votes")
    long["party"] = long["party"].map(normalize_party)
    long["votes"] = pd.to_numeric(long["votes"],errors="coerce").fillna(0).astype("int64")
    long[section_key] = long[section_key].astype(str)
    return long[long["party"]!=""][[section_key,"party","votes"]]


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s7  = step_cfg(cfg, "step7_aggregate_elections")

    in_geo         = require(s7.get("in_geojson",""),          "Falta steps.step7_aggregate_elections.in_geojson")
    sec_id_field   = require(s7.get("section_id_field",""),    "Falta steps.step7_aggregate_elections.section_id_field")
    dist_field     = require(s7.get("district_field",""),      "Falta steps.step7_aggregate_elections.district_field")
    results_files  = require(s7.get("results_files",[]),       "Falta steps.step7_aggregate_elections.results_files")
    out_party_csv  = require(s7.get("out_district_party_csv",""),   "Falta steps.step7_aggregate_elections.out_district_party_csv")
    out_summary    = require(s7.get("out_district_summary_csv",""), "Falta steps.step7_aggregate_elections.out_district_summary_csv")
    out_sec_geo    = s7.get("out_sections_enriched_geojson","") or ""

    sep        = s7.get("csv_sep","auto") or "auto"
    party_col  = s7.get("party_col","PARTIDO") or "PARTIDO"
    votes_col  = s7.get("votes_col","VOTOS")   or "VOTOS"
    blocs      = s7.get("blocs",{}) or {}

    rtve_en   = bool(s7.get("json_rtve_enabled",True))
    rtve_zp   = s7.get("json_rtve_zonas_path","mapa.zonas")       or "mapa.zonas"
    rtve_sf   = s7.get("json_rtve_section_field","cod")            or "cod"
    rtve_pl   = s7.get("json_rtve_party_list_field","lp")          or "lp"
    rtve_pf   = s7.get("json_rtve_party_field","s")                or "s"
    rtve_vf   = s7.get("json_rtve_votes_field","v")                or "v"

    # Load sections GeoJSON (has district_id, district_name, comarca attrs from Step6)
    gdf = load_geojson(in_geo)
    for col in (sec_id_field, dist_field):
        if col not in gdf.columns:
            raise SystemExit(f"GeoJSON sin '{col}'. Columnas: {list(gdf.columns)[:40]}")

    # Collect district-level metadata columns present in GeoJSON
    meta_cols = ["district_name", "dominant_comarca_id", "dominant_comarca_name",
                 "n_sections", "sections_list"]
    meta_cols = [c for c in meta_cols if c in gdf.columns]

    sec_to_dist = gdf[[sec_id_field, dist_field] + meta_cols].copy()
    sec_to_dist[sec_id_field] = sec_to_dist[sec_id_field].astype(str)
    sec_to_dist[dist_field]   = pd.to_numeric(sec_to_dist[dist_field], errors="coerce").fillna(-1).astype("int64")

    # District metadata (one row per district — take first occurrence of meta cols)
    dist_meta = (sec_to_dist[sec_to_dist[dist_field]>=0]
                 .groupby(dist_field, as_index=False)
                 [meta_cols].first() if meta_cols else None)

    # Load results
    frames = []
    for f in results_files:
        frames.append(load_results(
            f, section_key=sec_id_field, party_col=party_col, votes_col=votes_col,
            sep=sep, rtve_enabled=rtve_en, rtve_zonas_path=rtve_zp,
            rtve_sec_field=rtve_sf, rtve_party_list=rtve_pl,
            rtve_party_field=rtve_pf, rtve_votes_field=rtve_vf,
        ))
    res = pd.concat(frames, ignore_index=True)
    res[sec_id_field] = res[sec_id_field].astype(str)
    res["party"]  = res["party"].map(normalize_party)
    res["votes"]  = pd.to_numeric(res["votes"],errors="coerce").fillna(0).astype("int64")

    # Aggregate: section → district
    sec_party = res.groupby([sec_id_field,"party"],as_index=False)["votes"].sum()
    merged = sec_party.merge(sec_to_dist[[sec_id_field,dist_field]], on=sec_id_field, how="inner")
    merged = merged[merged[dist_field]>=0]

    dist_party = merged.groupby([dist_field,"party"],as_index=False)["votes"].sum()
    dist_party = dist_party.rename(columns={dist_field:"district_id"})
    dist_party["bloc"] = dist_party["party"].map(lambda p: blocs.get(p,"")) if blocs else ""

    totals  = dist_party.groupby("district_id",as_index=False)["votes"].sum().rename(columns={"votes":"total_votes"})
    dp      = dist_party.merge(totals, on="district_id", how="left")
    dp["vote_share"] = dp["votes"] / dp["total_votes"].replace({0:pd.NA})

    idx     = dp.groupby("district_id")["votes"].idxmax()
    winners = dp.loc[idx, ["district_id","party","votes","vote_share","bloc"]].copy()
    winners = winners.rename(columns={"party":"winner_party","votes":"winner_votes",
                                      "vote_share":"winner_share","bloc":"winner_bloc"})

    summary = totals.merge(winners, on="district_id", how="left")

    # Attach district metadata (district_name, comarca, etc.)
    if dist_meta is not None:
        dist_meta_r = dist_meta.rename(columns={dist_field:"district_id"})
        dist_meta_r["district_id"] = dist_meta_r["district_id"].astype("int64")
        summary["district_id"] = summary["district_id"].astype("int64")
        summary = summary.merge(dist_meta_r, on="district_id", how="left")

    # Also add per-party vote columns (wide) for Flourish — every party gets its own column
    parties = sorted(dist_party["party"].unique())
    party_wide = dist_party.pivot_table(index="district_id", columns="party",
                                        values="votes", aggfunc="sum", fill_value=0).reset_index()
    party_share = dist_party.pivot_table(index="district_id", columns="party",
                                         values="vote_share", aggfunc="sum", fill_value=0).reset_index()
    # Rename columns to safe names
    party_wide.columns   = ["district_id"] + [f"{p}_votes"  for p in parties]
    party_share.columns  = ["district_id"] + [f"{p}_share"  for p in parties]
    summary = summary.merge(party_wide,  on="district_id", how="left")
    summary = summary.merge(party_share, on="district_id", how="left")

    summary = summary.sort_values("district_id").reset_index(drop=True)

    # Save long party CSV
    out1 = Path(out_party_csv).expanduser().resolve()
    out1.parent.mkdir(parents=True, exist_ok=True)
    dist_party.sort_values(["district_id","votes"],ascending=[True,False]).to_csv(out1, index=False)

    # Save summary CSV
    out2 = Path(out_summary).expanduser().resolve()
    out2.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out2, index=False)

    # Enriched sections GeoJSON (optional)
    if out_sec_geo:
        sec_tot = sec_party.groupby(sec_id_field,as_index=False)["votes"].sum().rename(columns={"votes":"section_total_votes"})
        sidx = sec_party.groupby(sec_id_field)["votes"].idxmax()
        sec_win = sec_party.loc[sidx, [sec_id_field,"party","votes"]].rename(
            columns={"party":"section_winner_party","votes":"section_winner_votes"})
        gg = gdf.copy()
        gg[sec_id_field] = gg[sec_id_field].astype(str)
        gg = gg.merge(sec_tot, on=sec_id_field, how="left")
        gg = gg.merge(sec_win, on=sec_id_field, how="left")
        save_gz(gg, out_sec_geo)

    print(f"[Step7] OK districts={summary.shape[0]} parties={len(parties)} "
          f"meta_cols={meta_cols} out_summary={out_summary}")


if __name__ == "__main__":
    main()
