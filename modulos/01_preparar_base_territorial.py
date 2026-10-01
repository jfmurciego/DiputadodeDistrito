#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo 01 — Preparar base territorial.

Integra seccionado y población sin reparar ni completar silenciosamente datos
territoriales inválidos. El cero poblacional explícito es válido; ausencia,
valor no numérico, negativo, duplicado tras normalización o falta de
correspondencia bloquean cuando el contrato exige población completa.
"""
from __future__ import annotations

import argparse
import atexit
import io
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ddd_core.comarcas import attach_comarcas as attach_comarcas_by_municipality
from ddd_core.config import load_params_yaml, module_cfg, require
from ddd_core.territorial_validation import (
    TerritorialDataError,
    normalized_unique_keys,
    strict_population_series,
    validate_geodataframe,
)


def normalize_section_key(x):
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return None
    s = str(x).strip()
    exact = re.search(r"(?<!\d)(\d{10})(?!\d)", s)
    if exact:
        return exact.group(1)
    digits = re.sub(r"\D+", "", s)
    if len(digits) == 10:
        return digits
    if len(digits) > 10:
        return digits[:10]
    if digits:
        return digits.zfill(10)
    return None


def _first_member_with_ext(z, exts):
    for name in z.namelist():
        if (
            not name.endswith("/")
            and name.lower().endswith(tuple(e.lower() for e in exts))
            and not name.lower().endswith((".sbn", ".sbx"))
        ):
            return name
    return None


def _extract_shapefile_family(zip_path, shp_member):
    tmpdir = Path(tempfile.mkdtemp(prefix="ddd_seccionado_"))
    atexit.register(lambda: shutil.rmtree(tmpdir, ignore_errors=True))
    base = shp_member.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    folder = shp_member.rsplit("/", 1)[0] if "/" in shp_member else ""
    exts = {".shp", ".shx", ".dbf", ".prj", ".cpg", ".sbn", ".sbx"}
    with zipfile.ZipFile(zip_path, "r") as z:
        for m in z.namelist():
            name = m.rsplit("/", 1)[-1]
            if (
                not m.endswith("/")
                and (not folder or m.startswith(folder + "/"))
                and name.startswith(base + ".")
                and ("." + name.rsplit(".", 1)[-1].lower()) in exts
            ):
                z.extract(m, path=tmpdir)
    shp = tmpdir / (folder if folder else "") / (base + ".shp")
    if not shp.exists():
        raise FileNotFoundError(f"No se encontró shapefile extraído: {shp}")
    return shp


def load_seccionado(path_str, layer="", province_codes=None):
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Seccionado no encontrado: {p}")
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p, "r") as z:
            shp_member = _first_member_with_ext(z, (".shp",))
        if not shp_member:
            raise ValueError("ZIP sin .shp")
        shp = _extract_shapefile_family(p, shp_member)
        try:
            import pyogrio

            where = (
                "CPRO IN (" + ",".join(f"'{x}'" for x in province_codes) + ")"
                if province_codes
                else None
            )
            return pyogrio.read_dataframe(str(shp), layer=layer or None, where=where)
        except Exception as exc:
            print(f"[Módulo 1] AVISO filtro temprano no disponible: {exc}")
            return gpd.read_file(str(shp))
    return gpd.read_file(str(p), layer=layer or None)


def _sniff_sep(sample):
    first = sample.splitlines()[0] if sample.splitlines() else sample
    counts = {d: first.count(d) for d in ("\t", ";", ",")}
    sep = max(counts, key=counts.get)
    if counts[sep] == 0:
        raise ValueError("CSV sin delimitador reconocible")
    return sep


def load_cip(paths, section_key_col, pop_col, year, sep, filters, province_codes=None, chunksize=100000):
    partials = []
    year_col = filters.get("year_col", "Periodo")
    sexo_col = filters.get("sexo_col", "Sexo")
    edad_col = filters.get("edad_col", "Edad")
    sexo_vals = [str(x) for x in filters.get("sexo_total_values", ["Total"])]
    edad_vals = [str(x) for x in filters.get("edad_total_values", ["Todas las edades"])]

    def consume(reader):
        for df in reader:
            for required in (section_key_col, pop_col):
                if required not in df.columns:
                    raise TerritorialDataError(f"POPULATION_COLUMN_MISSING: {required}")
            if year_col in df.columns:
                df = df[df[year_col].astype(str).str.strip() == str(filters.get("year_value", year))]
            if sexo_col in df.columns:
                df = df[df[sexo_col].astype(str).str.strip().isin(sexo_vals)]
            if edad_col in df.columns:
                df = df[df[edad_col].astype(str).str.strip().isin(edad_vals)]
            if df.empty:
                continue

            normalized = df[section_key_col].map(normalize_section_key)
            if normalized.isna().any():
                sample = df.loc[normalized.isna(), section_key_col].astype(str).head(5).tolist()
                raise TerritorialDataError(f"SECTION_ID_INVALID: población: {sample}")

            scope = pd.Series(True, index=df.index)
            if province_codes:
                scope &= normalized.str[:2].isin(province_codes)
            if not scope.any():
                continue

            d = df.loc[scope].copy()
            o = pd.DataFrame(index=d.index)
            o["CUSEC_KEY"] = normalized.loc[scope].astype(str)
            o["POP"] = strict_population_series(
                d[pop_col],
                section_ids=o["CUSEC_KEY"],
                label="población CIP",
                require_non_null=True,
            )
            partials.append(o[["CUSEC_KEY", "POP"]])

    for pstr in paths:
        p = Path(pstr).expanduser().resolve()
        if p.suffix.lower() == ".zip":
            with zipfile.ZipFile(p, "r") as z:
                member = _first_member_with_ext(z, (".csv", ".tsv", ".txt"))
                if not member:
                    raise ValueError("ZIP de población sin CSV/TSV/TXT")
                with z.open(member) as fh:
                    sample = fh.read(4096).decode("utf-8", errors="replace")
                sep2 = _sniff_sep(sample) if sep == "auto" else sep
                with z.open(member) as fh:
                    consume(
                        pd.read_csv(
                            fh,
                            sep=sep2,
                            dtype=str,
                            chunksize=chunksize,
                            encoding="utf-8-sig",
                        )
                    )
        else:
            sample = p.open("rb").read(4096).decode("utf-8", errors="replace")
            sep2 = _sniff_sep(sample) if sep == "auto" else sep
            consume(
                pd.read_csv(
                    p,
                    sep=sep2,
                    dtype=str,
                    chunksize=chunksize,
                    encoding="utf-8-sig",
                )
            )

    if not partials:
        raise TerritorialDataError("POPULATION_MISSING: no hay filas de población en el ámbito")
    out = pd.concat(partials, ignore_index=True)
    duplicates = out.loc[out["CUSEC_KEY"].duplicated(keep=False), "CUSEC_KEY"]
    if not duplicates.empty:
        raise TerritorialDataError(
            "SECTION_ID_DUPLICATE_AFTER_NORMALIZATION: población: "
            + str(sorted(set(duplicates.astype(str)))[:10])
        )
    out["POP"] = out["POP"].astype("int64")
    return out


def write_geojson(gdf, out_path):
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    tmp = outp.parent / (outp.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(outp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    cfg = load_params_yaml(args.params)
    meta = cfg.get("meta", {})
    year = int(meta.get("year", 2025))
    val = cfg.get("validation", {}) or {}
    require_non_null_population = bool(val.get("require_non_null_population", True))
    io_in = cfg["io"]["input"]
    secc = io_in["seccionado"]
    cip_cfg = io_in["population_cip"]
    s1 = module_cfg(cfg, "modulo_01_preparar_base_territorial", legacy_step_key="step1_build_sections")
    prov = [str(x).zfill(2) for x in s1.get("province_codes", [])]

    gdf = load_seccionado(secc["path"], secc.get("layer", "") or "", prov)
    validate_geodataframe(gdf, label="M01 seccionado de entrada")
    section_source_col = secc.get("section_key_col", "CUSEC")
    if section_source_col not in gdf.columns:
        raise SystemExit(f"[Módulo 1] Seccionado sin campo {section_source_col!r}")
    gdf["CUSEC_KEY"] = normalized_unique_keys(
        gdf[section_source_col],
        normalize=normalize_section_key,
        label="geometría M01",
    )
    gdf = gdf[gdf["CUSEC_KEY"].str[:2].isin(prov)].copy()
    if gdf.empty:
        raise SystemExit("[Módulo 1] Seccionado vacío para las provincias declaradas")

    filters = {
        "year_col": "Periodo",
        "sexo_col": "Sexo",
        "edad_col": "Edad",
        "sexo_total_values": ["Total"],
        "edad_total_values": ["Todas las edades"],
        "year_value": year,
    }
    filters.update(cip_cfg.get("filters", {}))
    cip = load_cip(
        cip_cfg["paths"],
        cip_cfg.get("section_key_col", "Secciones"),
        cip_cfg.get("pop_col", "Total"),
        year,
        cip_cfg.get("sep", "auto"),
        filters,
        prov,
    )

    geometry_keys = set(gdf["CUSEC_KEY"])
    population_keys = set(cip["CUSEC_KEY"])
    population_without_geometry = sorted(population_keys - geometry_keys)
    if population_without_geometry:
        raise SystemExit(
            "[Módulo 1] POPULATION_WITHOUT_GEOMETRY: "
            + str(population_without_geometry[:10])
        )

    pop_field = f"POP_{year}"
    gdf = gdf.merge(
        cip.rename(columns={"POP": pop_field}),
        on="CUSEC_KEY",
        how="left",
        validate="one_to_one",
    )
    missing = int(gdf[pop_field].isna().sum())
    if require_non_null_population and missing:
        missing_ids = gdf.loc[gdf[pop_field].isna(), "CUSEC_KEY"].astype(str).head(10).tolist()
        raise SystemExit(
            f"[Módulo 1] POPULATION_MISSING: {missing} secciones sin población: {missing_ids}"
        )
    if not require_non_null_population and missing:
        # La ausencia queda explícita; nunca se transforma en cero.
        gdf[pop_field] = strict_population_series(
            gdf[pop_field],
            section_ids=gdf["CUSEC_KEY"],
            label="población M01",
            require_non_null=False,
        )
    else:
        gdf[pop_field] = strict_population_series(
            gdf[pop_field],
            section_ids=gdf["CUSEC_KEY"],
            label="población M01",
            require_non_null=True,
        ).astype("int64")

    gdf, comarcas_report = attach_comarcas_by_municipality(gdf, io_in.get("comarcas", {}))
    validate_geodataframe(gdf, label="M01 salida territorial")

    out_geo = require(s1.get("out_geojson"), "Falta M01 salida")
    write_geojson(gdf, out_geo)
    out_report = s1.get("out_report", "")
    if out_report:
        Path(out_report).write_text(
            json.dumps(
                {
                    "module": "01",
                    "version": "7.2.0",
                    "rows_out": len(gdf),
                    "missing_population_rows": missing,
                    "require_non_null_population": require_non_null_population,
                    "province_codes": prov,
                    "year": year,
                    "comarcas": comarcas_report,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    print(f"[Módulo 1] OK rows={len(gdf)} missing_population={missing} out={out_geo}")


if __name__ == "__main__":
    main()
