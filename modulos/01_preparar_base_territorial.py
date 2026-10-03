#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 01 — Preparar base territorial
VERSIÓN: 7.2.0
NOMBRE DE VERSIÓN: Fronteras territoriales fail-closed
FECHA: 2026-10-01
QUÉ HACE: integra cartografía y población oficial bloqueando ausencias, duplicados normalizados, valores inválidos y geometría/CRS no acreditados.
POR QUÉ ES SEPARADO: es la base estable, costosa y cacheable de todos los módulos posteriores.
ESTADO: candidato multi-territorio — frontera territorial estricta.
CAMBIOS: hace efectivo require_non_null_population, conserva cero explícito y elimina pérdidas silenciosas de población y geometría.
MOTIVO: impedir que datos territoriales incompletos o inválidos avancen a grafo, consolidación o validación.
ANTERIOR: legacy/modulo01/01_preparar_base_territorial_v7.0.4.py
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


def load_seccionado(
    path_str,
    layer="",
    province_codes=None,
    *,
    container="auto",
    materialized_format="",
    archive_member="",
):
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Seccionado no encontrado: {p}")

    container = str(container or "auto").strip().lower()
    materialized_format = str(materialized_format or "").strip().lower()
    use_zip = container == "zip" or (container == "auto" and p.suffix.lower() == ".zip")

    if materialized_format and materialized_format not in {
        "shapefile",
        "geojson",
        "geopackage",
        "gpkg",
    }:
        raise ValueError(
            f"Formato de seccionado no soportado por M01: {materialized_format}"
        )

    if use_zip:
        with zipfile.ZipFile(p, "r") as z:
            shp_member = str(archive_member or "").strip()
            if shp_member:
                if shp_member not in z.namelist():
                    raise ValueError(
                        f"archive_member de seccionado no existe: {shp_member}"
                    )
                if not shp_member.lower().endswith(".shp"):
                    raise ValueError(
                        "archive_member de seccionado debe apuntar al .shp materializado"
                    )
            else:
                shp_member = _first_member_with_ext(z, (".shp",))
        if not shp_member:
            raise ValueError("Contenedor ZIP de seccionado sin .shp")
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

    if container not in {"auto", "file"}:
        raise ValueError(f"Container de seccionado no soportado por M01: {container}")
    return gpd.read_file(str(p), layer=layer or None)

def _sniff_sep(sample):
    first = sample.splitlines()[0] if sample.splitlines() else sample
    counts = {d: first.count(d) for d in ("\t", ";", ",")}
    sep = max(counts, key=counts.get)
    if counts[sep] == 0:
        raise ValueError("CSV sin delimitador reconocible")
    return sep


def load_cip(
    paths,
    section_key_col,
    pop_col,
    year,
    sep,
    filters,
    province_codes=None,
    chunksize=100000,
    *,
    container="auto",
    materialized_format="",
    archive_member="",
    encoding="utf-8-sig",
):
    partials = []
    year_col = filters.get("year_col", "Periodo")
    sexo_col = filters.get("sexo_col", "Sexo")
    edad_col = filters.get("edad_col", "Edad")
    sexo_vals = [str(x) for x in filters.get("sexo_total_values", ["Total"])]
    edad_vals = [str(x) for x in filters.get("edad_total_values", ["Todas las edades"])]

    container = str(container or "auto").strip().lower()
    materialized_format = str(materialized_format or "").strip().lower()
    archive_member = str(archive_member or "").strip()
    encoding = str(encoding or "utf-8-sig").strip()

    if materialized_format and materialized_format not in {"csv", "tsv", "txt"}:
        raise ValueError(
            f"Formato poblacional no soportado por M01: {materialized_format}"
        )

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

    def reader_from_binary(binary, *, effective_sep):
        return pd.read_csv(
            binary,
            sep=effective_sep,
            dtype=str,
            chunksize=chunksize,
            encoding=encoding,
        )

    for pstr in paths:
        p = Path(pstr).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Fuente poblacional no encontrada: {p}")
        use_zip = container == "zip" or (container == "auto" and p.suffix.lower() == ".zip")
        if use_zip:
            with zipfile.ZipFile(p, "r") as z:
                member = archive_member
                if member:
                    if member not in z.namelist():
                        raise ValueError(
                            f"archive_member poblacional no existe: {member}"
                        )
                else:
                    member = _first_member_with_ext(z, (".csv", ".tsv", ".txt"))
                    if not member:
                        raise ValueError("ZIP de población sin CSV/TSV/TXT")
                with z.open(member) as fh:
                    sample = fh.read(4096).decode(encoding, errors="strict")
                sep2 = _sniff_sep(sample) if sep == "auto" else sep
                with z.open(member) as fh:
                    consume(reader_from_binary(fh, effective_sep=sep2))
        else:
            if container not in {"auto", "file"}:
                raise ValueError(
                    f"Container poblacional no soportado por M01: {container}"
                )
            sample = p.open("rb").read(4096).decode(encoding, errors="strict")
            sep2 = _sniff_sep(sample) if sep == "auto" else sep
            consume(reader_from_binary(p, effective_sep=sep2))

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


def resolve_runtime_fields(cfg: dict, population_year: int) -> tuple[str, str]:
    runtime = ((cfg.get("resolved_source_contract") or {}).get("runtime") or {})
    return (
        str(runtime.get("section_id_field") or "CUSEC_KEY"),
        str(runtime.get("population_field") or f"POP_{population_year}"),
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    cfg = load_params_yaml(args.params)
    meta = cfg.get("meta", {})
    edition = int(require(meta.get("year"), "Falta meta.year (edición DDD)"))
    population_year = int(require(meta.get("source_population_year"), "Falta meta.source_population_year acreditado"))
    section_year = int(require(meta.get("source_section_year"), "Falta meta.source_section_year acreditado"))
    runtime_section_field, runtime_population_field = resolve_runtime_fields(
        cfg,
        population_year,
    )
    internal_section_field = "__DDD_SECTION_ID"
    val = cfg.get("validation", {}) or {}
    require_non_null_population = bool(val.get("require_non_null_population", True))
    io_in = cfg["io"]["input"]
    secc = io_in["seccionado"]
    cip_cfg = io_in["population_cip"]
    s1 = module_cfg(cfg, "modulo_01_preparar_base_territorial", legacy_step_key="step1_build_sections")
    prov = [str(x).zfill(2) for x in s1.get("province_codes", [])]

    gdf = load_seccionado(
        secc["path"],
        secc.get("layer", "") or "",
        prov,
        container=secc.get("container", "auto"),
        materialized_format=secc.get("materialized_format", ""),
        archive_member=secc.get("archive_member", ""),
    )
    validate_geodataframe(gdf, label="M01 seccionado de entrada")
    section_source_col = secc.get("section_key_col", "CUSEC")
    if section_source_col not in gdf.columns:
        raise SystemExit(f"[Módulo 1] Seccionado sin campo {section_source_col!r}")
    gdf[internal_section_field] = normalized_unique_keys(
        gdf[section_source_col],
        normalize=normalize_section_key,
        label="geometría M01",
    )
    gdf = gdf[gdf[internal_section_field].str[:2].isin(prov)].copy()
    if gdf.empty:
        raise SystemExit("[Módulo 1] Seccionado vacío para las provincias declaradas")

    filters = {
        "year_col": "Periodo",
        "sexo_col": "Sexo",
        "edad_col": "Edad",
        "sexo_total_values": ["Total"],
        "edad_total_values": ["Todas las edades"],
        "year_value": population_year,
    }
    filters.update(cip_cfg.get("filters", {}))
    configured_year = filters.get("year_value")
    if int(configured_year) != population_year:
        raise ValueError(
            f"population_cip.filters.year_value={configured_year} contradice "
            f"source_population_year={population_year}"
        )
    cip = load_cip(
        cip_cfg["paths"],
        cip_cfg.get("section_key_col", "Secciones"),
        cip_cfg.get("pop_col", "Total"),
        population_year,
        cip_cfg.get("sep", "auto"),
        filters,
        prov,
        container=cip_cfg.get("container", "auto"),
        materialized_format=cip_cfg.get("materialized_format", ""),
        archive_member=cip_cfg.get("archive_member", ""),
        encoding=cip_cfg.get("encoding", "utf-8-sig"),
    )

    cip = cip.rename(columns={"CUSEC_KEY": internal_section_field})
    geometry_keys = set(gdf[internal_section_field])
    population_keys = set(cip[internal_section_field])
    population_without_geometry = sorted(population_keys - geometry_keys)
    if population_without_geometry:
        raise SystemExit(
            "[Módulo 1] POPULATION_WITHOUT_GEOMETRY: "
            + str(population_without_geometry[:10])
        )

    pop_field = runtime_population_field
    gdf = gdf.merge(
        cip.rename(columns={"POP": pop_field}),
        on=internal_section_field,
        how="left",
        validate="one_to_one",
    )
    missing = int(gdf[pop_field].isna().sum())
    if require_non_null_population and missing:
        missing_ids = gdf.loc[gdf[pop_field].isna(), internal_section_field].astype(str).head(10).tolist()
        raise SystemExit(
            f"[Módulo 1] POPULATION_MISSING: {missing} secciones sin población: {missing_ids}"
        )
    if not require_non_null_population and missing:
        # La ausencia queda explícita; nunca se transforma en cero.
        gdf[pop_field] = strict_population_series(
            gdf[pop_field],
            section_ids=gdf[internal_section_field],
            label="población M01",
            require_non_null=False,
        )
    else:
        gdf[pop_field] = strict_population_series(
            gdf[pop_field],
            section_ids=gdf[internal_section_field],
            label="población M01",
            require_non_null=True,
        ).astype("int64")

    # Compatibilidad interna: comarcas todavía consume CUSEC_KEY. Ese alias
    # no es contractual y se elimina si runtime declara otro nombre público.
    gdf["CUSEC_KEY"] = gdf[internal_section_field]
    gdf, comarcas_report = attach_comarcas_by_municipality(
        gdf,
        io_in.get("comarcas", {}),
    )
    gdf[runtime_section_field] = gdf[internal_section_field]
    drop_cols = [internal_section_field]
    if runtime_section_field != "CUSEC_KEY":
        drop_cols.append("CUSEC_KEY")
    gdf = gdf.drop(columns=[col for col in drop_cols if col in gdf.columns])

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
                    "edition": edition,
                    "population_year": population_year,
                    "section_year": section_year,
                    "section_id_field": runtime_section_field,
                    "population_field": pop_field,
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
