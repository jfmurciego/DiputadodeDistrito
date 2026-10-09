#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 1 — Build Sections + Population (v7.0)

Changes vs v6.0:
  - Comarca join uses NORMALISED keys on both sides:
      strips whitespace, removes dots/hyphens, zero-pads to 5 digits.
    This handles the common formats: "22 001", "22.001", "022001", "22001".
  - Prints a clear match-rate diagnostic so you immediately see if
    the join worked (e.g. "comarcas: 731/731 secciones con comarca").
  - If match rate is 0%, prints 5 sample keys from each side so you
    can see the mismatch format directly.
  - comarca_id_col / comarca_name_col YAML params: if set, the comarcas
    CSV columns are renamed to canonical "comarca_id" / "comarca_name"
    on output, so Steps 3/6 always find them regardless of CSV column names.

Run:
  python scripts/ddd_step1_build_sections_v7_params.py --params params/ddd_params.yaml
"""
from __future__ import annotations

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse, atexit, io, json, re, shutil, tempfile, zipfile
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import geopandas as gpd

from ddd_core.config import load_params_yaml, step_cfg, require

SECTION10_RE = re.compile(r"^\d{10}$")
PROV2_RE     = re.compile(r"^\d{2}$")


# ── Section key normalisation (unchanged from v6) ─────────────────────────────
def normalize_section_key(x: object) -> Optional[str]:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    if not s:
        return None
    digits = re.sub(r"\D+", "", s)
    if len(digits) == 10:
        return digits
    if len(digits) > 10:
        tail = digits[-10:]
        if SECTION10_RE.match(tail):
            return tail
    if len(digits) < 10:
        padded = digits.zfill(10)
        if SECTION10_RE.match(padded):
            return padded
    return None


# ── MUN_KEY normalisation (NEW) ───────────────────────────────────────────────
def normalize_mun_key(x: Any) -> Optional[str]:
    """Normalise any municipality-code variant to 5-digit zero-padded string.

    Handles: "22001", "22 001", "22.001", "22-001", "022001",
             22001 (int/float), "22001.0", etc.
    Returns None if fewer than 4 digits are present.
    """
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    # Remove trailing ".0" from float-as-string
    s = re.sub(r"\.0+$", "", s)
    digits = re.sub(r"\D+", "", s)
    if len(digits) < 4:
        return None
    # If 6+ digits, take last 5 (handles "0" prefix on 6-digit codes)
    if len(digits) > 5:
        digits = digits[-5:]
    return digits.zfill(5)


# ── File I/O helpers (unchanged from v6) ─────────────────────────────────────
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


def _first_member_with_ext(z: zipfile.ZipFile, exts: Tuple[str, ...]) -> Optional[str]:
    exts_l = tuple(e.lower() for e in exts)
    for name in z.namelist():
        if name.endswith("/"): continue
        low = name.lower()
        if low.endswith((".sbn", ".sbx")): continue
        if low.endswith(exts_l): return name
    return None


def _extract_shapefile_family(zip_path: Path, shp_member: str) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="ddd_secc_"))
    atexit.register(lambda: shutil.rmtree(tmpdir, ignore_errors=True))
    base_name = shp_member.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    folder    = shp_member.rsplit("/", 1)[0] if "/" in shp_member else ""
    wanted    = {".shp", ".shx", ".dbf", ".prj", ".cpg"}

    def is_wanted(m: str) -> bool:
        if m.endswith("/"): return False
        if folder and not m.startswith(folder + "/"): return False
        nm = m.rsplit("/", 1)[-1]
        if not nm.startswith(base_name + "."): return False
        return ("." + nm.rsplit(".", 1)[-1].lower()) in wanted

    with zipfile.ZipFile(zip_path) as z:
        for m in [m for m in z.namelist() if is_wanted(m)]:
            z.extract(m, path=tmpdir)

    shp_fs = tmpdir / (folder if folder else "") / f"{base_name}.shp"
    if not shp_fs.exists():
        raise FileNotFoundError(f"No se encontró .shp extraído: {shp_fs}")
    return shp_fs


def load_seccionado(path_str: str, layer: str = "") -> gpd.GeoDataFrame:
    p = Path(path_str).expanduser().resolve()
    if not p.exists(): raise FileNotFoundError(f"Seccionado no encontrado: {p}")
    if p.suffix.lower() in {".geojson", ".json"}:
        return _gpd_read_file(str(p), layer=layer or None)
    if p.suffix.lower() == ".zip" and p.name.lower().endswith((".geojson.zip", ".json.zip")):
        with zipfile.ZipFile(p) as z:
            gj = _first_member_with_ext(z, (".geojson", ".json"))
            if not gj: raise ValueError("ZIP GeoJSON sin .geojson/.json.")
            data = z.read(gj)
        return _gpd_read_file(io.BytesIO(data))
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            shp_m = _first_member_with_ext(z, (".shp",))
            if not shp_m:
                raise ValueError("No .shp dentro del ZIP.")
        shp_fs = _extract_shapefile_family(p, shp_m)
        return _gpd_read_file(str(shp_fs), layer=layer or None)
    if p.is_dir():
        shps = sorted(p.rglob("*.shp"))
        if not shps: raise ValueError(f"No .shp en directorio: {p}")
        return _gpd_read_file(str(shps[0]), layer=layer or None)
    raise ValueError(f"Formato no soportado: {p}")


def _sniff_sep(sample: str) -> str:
    return "\t" if "\t" in sample and sample.count("\t") >= sample.count(",") else ","


def _read_table(path: Path, sep: str = "auto") -> pd.DataFrame:
    if sep == "auto":
        with open(path, "rb") as f:
            sep2 = _sniff_sep(f.read(4096).decode("utf-8", errors="replace"))
    else:
        sep2 = sep.encode("utf-8").decode("unicode_escape")
    return pd.read_csv(path, sep=sep2, dtype=str)


def _read_table_from_bytes(data: bytes, sep: str = "auto") -> pd.DataFrame:
    txt = data.decode("utf-8", errors="replace")
    sep2 = _sniff_sep(txt[:4096]) if sep == "auto" else sep.encode().decode("unicode_escape")
    return pd.read_csv(io.StringIO(txt), sep=sep2, dtype=str)


def load_cip(paths, section_key_col, pop_col, year, sep, filters) -> pd.DataFrame:
    dfs = []
    for pstr in paths:
        p = Path(pstr).expanduser().resolve()
        if not p.exists(): raise FileNotFoundError(f"CIP no encontrado: {p}")
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p) as z:
                m = _first_member_with_ext(z, (".csv", ".tsv", ".txt"))
                if not m: raise ValueError(f"ZIP CIP sin CSV: {p}")
                dfs.append(_read_table_from_bytes(z.read(m), sep=sep))
        else:
            dfs.append(_read_table(p, sep=sep))

    df = pd.concat(dfs, ignore_index=True)
    year_col  = filters.get("year_col", "Periodo")
    year_val  = filters.get("year_value", year)
    if year_col in df.columns:
        df = df[df[year_col].astype(str).str.strip() == str(year_val)]
    sexo_col  = filters.get("sexo_col", "Sexo")
    sexo_vals = filters.get("sexo_total_values", ["Total"])
    if sexo_col in df.columns and sexo_vals:
        df = df[df[sexo_col].astype(str).str.strip().isin([str(x) for x in sexo_vals])]
    edad_col  = filters.get("edad_col", "Edad")
    edad_vals = filters.get("edad_total_values", ["Todas las edades"])
    if edad_col in df.columns and edad_vals:
        df = df[df[edad_col].astype(str).str.strip().isin([str(x) for x in edad_vals])]

    if section_key_col not in df.columns:
        raise ValueError(f"Columna sección no encontrada en CIP: {section_key_col}. Columnas: {list(df.columns)}")
    if pop_col not in df.columns:
        raise ValueError(f"Columna población no encontrada en CIP: {pop_col}. Columnas: {list(df.columns)}")

    out = pd.DataFrame()
    out["CUSEC_KEY"] = df[section_key_col].map(normalize_section_key)
    out["POP"] = pd.to_numeric(df[pop_col].astype(str).str.replace(".", "", regex=False), errors="coerce")
    out = out.dropna(subset=["CUSEC_KEY", "POP"]).copy()
    out["POP"] = out["POP"].astype("int64")
    out = out.groupby("CUSEC_KEY", as_index=False)["POP"].sum()
    return out


def write_geojson(gdf: gpd.GeoDataFrame, out_path_str: str) -> None:
    outp = Path(out_path_str).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    if outp.suffix.lower() == ".zip" and outp.name.lower().endswith(".geojson.zip"):
        tmp = outp.parent / (outp.stem.replace(".geojson", "") + ".geojson")
        gdf.to_file(tmp, driver="GeoJSON")
        with zipfile.ZipFile(outp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, arcname=tmp.name)
        try: tmp.unlink()
        except Exception: pass
    else:
        gdf.to_file(outp, driver="GeoJSON")


def write_report(report: dict, out_path_str: str) -> None:
    outp = Path(out_path_str).expanduser().resolve()
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg  = load_params_yaml(args.params)
    meta = cfg.get("meta", {}) or {}
    year = int(meta.get("year", 2025))
    scope = meta.get("scope", "national")

    io_in   = ((cfg.get("io", {}) or {}).get("input", {}) or {})
    secc    = (io_in.get("seccionado", {}) or {})
    cip_cfg = (io_in.get("population_cip", {}) or {})
    com_cfg = (io_in.get("comarcas", {}) or {})
    s1      = step_cfg(cfg, "step1_build_sections")

    seccionado = require(secc.get("path", ""), "Falta io.input.seccionado.path")
    secc_layer = secc.get("layer", "") or ""
    secc_key   = secc.get("section_key_col", "CUSEC") or "CUSEC"

    cip_paths   = require(cip_cfg.get("paths", []), "Falta io.input.population_cip.paths")
    cip_sep     = cip_cfg.get("sep", "auto") or "auto"
    cip_key     = cip_cfg.get("section_key_col", "Secciones") or "Secciones"
    cip_pop     = cip_cfg.get("pop_col", "Total") or "Total"
    cip_filters = dict(cip_cfg.get("filters", {}) or {})
    cip_filters.setdefault("sexo_total_values", ["Total"])
    cip_filters.setdefault("edad_total_values", ["Todas las edades"])
    cip_filters.setdefault("sexo_col", "Sexo")
    cip_filters.setdefault("edad_col", "Edad")
    cip_filters.setdefault("year_col", "Periodo")
    cip_filters.setdefault("year_value", year)

    out_geo    = require(s1.get("out_geojson", ""), "Falta steps.step1_build_sections.out_geojson")
    out_report = s1.get("out_report", "") or ""
    drop_missing = bool(s1.get("drop_missing_population", False))

    prov_codes: List[str] = []
    if scope == "provincial":
        prov_codes = [str(x).zfill(2) for x in (s1.get("province_codes", []) or [])]
        if not prov_codes:
            raise SystemExit("scope=provincial requiere steps.step1_build_sections.province_codes")

    # ── Load seccionado ────────────────────────────────────────────────────
    gdf = load_seccionado(seccionado, layer=secc_layer)
    if secc_key not in gdf.columns:
        raise SystemExit(f"Seccionado sin campo {secc_key}. Columnas: {list(gdf.columns)[:40]}")

    gdf["CUSEC_KEY"] = gdf[secc_key].map(normalize_section_key)
    n_bad = int(gdf["CUSEC_KEY"].isna().sum())
    if n_bad:
        print(f"[Step1] AVISO: {n_bad} filas descartadas por CUSEC_KEY no parseable.")
    gdf = gdf.dropna(subset=["CUSEC_KEY"]).copy()

    if prov_codes:
        gdf["CPRO"] = gdf["CUSEC_KEY"].str[:2]
        gdf = gdf[gdf["CPRO"].isin(prov_codes)].copy()

    # ── Population join ────────────────────────────────────────────────────
    cip = load_cip(list(cip_paths), cip_key, cip_pop, year, cip_sep, cip_filters)
    pop_field = f"POP_{year}"
    gdf = gdf.merge(cip[["CUSEC_KEY", "POP"]].rename(columns={"POP": pop_field}),
                    on="CUSEC_KEY", how="left")
    missing_pop = int(gdf[pop_field].isna().sum())
    if missing_pop:
        print(f"[Step1] AVISO: {missing_pop} secciones sin datos de población en CIP.")
    if drop_missing:
        gdf = gdf.dropna(subset=[pop_field]).copy()

    # ── Comarca join (v7: normalised keys + diagnostics) ───────────────────
    com_joined = False
    if bool(com_cfg.get("enabled", False)):
        com_path = com_cfg.get("path", "") or ""
        if com_path:
            com = pd.read_csv(Path(com_path).expanduser().resolve(), dtype=str)
            com_key = ((com_cfg.get("join", {}) or {}).get("comarcas_key_col", "MUN_KEY") or "MUN_KEY")

            if com_key not in com.columns:
                print(f"[Step1] ERROR: columna de join '{com_key}' no existe en comarcas CSV.")
                print(f"  Columnas disponibles: {list(com.columns)}")
                raise SystemExit("Corrige comarcas.join.comarcas_key_col en el YAML.")

            # Normalise both sides
            gdf["_MUN_KEY_NORM"] = gdf["CUSEC_KEY"].str[:5]   # already 5 digits
            com["_JOIN_KEY_NORM"] = com[com_key].map(normalize_mun_key)

            # Diagnostics before join
            gdf_keys = set(gdf["_MUN_KEY_NORM"].dropna().unique())
            com_keys = set(com["_JOIN_KEY_NORM"].dropna().unique())
            overlap  = gdf_keys & com_keys
            print(f"\n[Step1] Comarca join diagnostics:")
            print(f"  MUN_KEYs en seccionado:  {len(gdf_keys)}  (ej: {sorted(gdf_keys)[:5]})")
            print(f"  Claves en comarcas CSV:  {len(com_keys)}  (ej: {sorted(com_keys)[:5]})")
            print(f"  Coincidencias:           {len(overlap)}")

            if len(overlap) == 0:
                print(f"\n  AVISO: 0 coincidencias — los formatos de clave no coinciden.")
                print(f"  Muestra seccionado MUN_KEY: {sorted(gdf_keys)[:5]}")
                print(f"  Muestra comarcas CSV key '{com_key}' normalizada: {sorted(com_keys)[:5]}")
                print(f"  Muestra comarcas CSV key '{com_key}' original: "
                      f"{list(com[com_key].dropna()[:5])}")
                print(f"  → Comprueba que '{com_key}' es la columna con el código INE del municipio")
                print(f"    (5 dígitos, p.ej. '22001' para Abizanda).\n")
            else:
                unmatched = len(gdf_keys) - len(overlap)
                if unmatched > 0:
                    miss = sorted(gdf_keys - com_keys)[:10]
                    print(f"  AVISO: {unmatched} municipios sin comarca (no en CSV): {miss}")

            # Rename optional canonical columns if configured
            cid_rename = com_cfg.get("comarca_id_col",   "") or ""
            cnm_rename = com_cfg.get("comarca_name_col", "") or ""
            rename_map: Dict[str, str] = {}
            if cid_rename and cid_rename in com.columns:
                rename_map[cid_rename] = "comarca_id"
            if cnm_rename and cnm_rename in com.columns:
                rename_map[cnm_rename] = "comarca_name"
            if rename_map:
                com = com.rename(columns=rename_map)
                print(f"  Renombrado: {rename_map}")

            # Do the join on normalised keys
            gdf = gdf.merge(
                com.drop(columns=[com_key] if com_key not in rename_map else []),
                left_on="_MUN_KEY_NORM",
                right_on="_JOIN_KEY_NORM",
                how="left",
            )
            gdf = gdf.drop(columns=["_MUN_KEY_NORM", "_JOIN_KEY_NORM"], errors="ignore")

            # Report match rate
            # Pick any non-geometry, non-join column from comarcas to check nulls
            com_data_cols = [c for c in com.columns if c not in ("_JOIN_KEY_NORM", com_key)]
            if com_data_cols:
                matched = int(gdf[com_data_cols[0]].notna().sum())
                total   = len(gdf)
                print(f"  Resultado: {matched}/{total} secciones con datos de comarca "
                      f"({100*matched/total:.1f}%)\n")

            com_joined = True

    write_geojson(gdf, out_geo)
    if out_report:
        write_report({
            "step": "step1_build_sections", "version": "7.0",
            "scope": scope, "province_codes": prov_codes, "year": year,
            "rows_out": int(len(gdf)), "missing_population_rows": missing_pop,
            "comarcas_joined": com_joined,
            "columns_out": list(gdf.columns),
            "out": out_geo,
        }, out_report)

    print(f"[Step1] OK rows={len(gdf)} out={out_geo}")
    print(f"[Step1] Columnas en output: {list(gdf.columns)}")


if __name__ == "__main__":
    main()
