#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 08 — Integrar resultados en el mapa final
VERSIÓN: 7.2.0
NOMBRE DE VERSIÓN: Unión electoral exhaustiva con identificador canónico
FECHA: 2026-09-15
QUÉ HACE: une resultados agregados con la geometría; por defecto exige cobertura exacta y sólo permite distritos sin resultados cuando todas sus secciones están declaradas como map_only en la reconciliación M07.
POR QUÉ ES SEPARADO: es la unión final de dos productos ya generados y permite cambiar datos electorales sin redistritar.
ESTADO: vigente — R039
CAMBIOS: añade excepción auditable para distritos compuestos íntegramente por secciones map_only declaradas en M07.
MOTIVO: pandas puede inferir district_id electoral como float al leer CSV; la representación no puede convertir una cobertura 67/67 en un falso faltante total.
ANTERIOR: legacy/modulo08/08_integrar_resultados_v7.1.0.py
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ddd_core.config import load_params_yaml, module_cfg, require

_INTEGER_FLOAT_ID = re.compile(r"^([+-]?\d+)\.0+$")


def load_geojson_zip(p):
    pp = Path(p).expanduser().resolve()
    if pp.suffix.lower() == ".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp, "r") as archive:
            members = [
                name for name in archive.namelist()
                if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
            ]
            if len(members) != 1:
                raise ValueError(f"M08 esperaba un GeoJSON en {pp}; encontró {len(members)}")
            data = archive.read(members[0])
        return gpd.read_file(io.BytesIO(data))
    return gpd.read_file(str(pp))


def write_geojson_zip(gdf,out_path):
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    tmp = outp.parent / (outp.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(outp, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def canonical_district_id(value):
    """Normaliza solo representaciones numéricas enteras equivalentes; conserva IDs alfanuméricos."""
    if pd.isna(value):
        raise ValueError("M08 recibió district_id nulo")
    text = str(value).strip()
    if not text:
        raise ValueError("M08 recibió district_id vacío")
    match = _INTEGER_FLOAT_ID.fullmatch(text)
    return match.group(1) if match else text


def integrate_results(gdf, results, *, allowed_missing_districts=None):
    """Une resultados; los faltantes sólo se admiten si están explícitamente autorizados."""
    if "district_id" not in gdf.columns or "district_id" not in results.columns:
        raise ValueError("Falta district_id en M08")
    geo = gdf.copy()
    electoral = results.copy()
    geo["district_id"] = geo["district_id"].map(canonical_district_id)
    electoral["district_id"] = electoral["district_id"].map(canonical_district_id)
    duplicated = sorted(electoral.loc[electoral["district_id"].duplicated(False), "district_id"].unique())
    if duplicated:
        raise ValueError(f"M08 recibió distritos electorales duplicados: {duplicated}")
    geo_ids = set(geo["district_id"])
    electoral_ids = set(electoral["district_id"])
    missing = sorted(geo_ids - electoral_ids)
    unexpected = sorted(electoral_ids - geo_ids)
    allowed={canonical_district_id(x) for x in (allowed_missing_districts or [])}
    forbidden_missing=sorted(set(missing)-allowed)
    stale_allowed=sorted(allowed-set(missing))
    if forbidden_missing or unexpected or stale_allowed:
        raise ValueError(
            "Cobertura distrital electoral incompleta: "
            f"sin_resultados={forbidden_missing}, ajenos_al_mapa={unexpected}, "
            f"excepciones_obsoletas={stale_allowed}"
        )
    out=geo.merge(electoral, on="district_id", how="left", validate="one_to_one")
    out["electoral_data_status"]=out["district_id"].map(
        lambda value: "NO_MATCHING_ELECTION_SECTIONS" if value in allowed else "AVAILABLE"
    )
    return out


def derive_declared_missing_districts(section_gdf, reconciliation_report, *, section_field, district_field):
    """Autoriza sólo distritos cuyas secciones están todas en map_only ya validado por M07."""
    if section_field not in section_gdf.columns or district_field not in section_gdf.columns:
        raise ValueError("No se puede auditar cobertura distrital: faltan campos de sección/distrito")
    map_only={str(item.get("section_id")) for item in (reconciliation_report.get("map_only_sections") or [])}
    if not map_only:
        return []
    work=section_gdf[[section_field,district_field]].copy()
    work[section_field]=work[section_field].astype(str)
    work[district_field]=work[district_field].map(canonical_district_id)
    allowed=[]
    for district_id,group in work.groupby(district_field):
        sections=set(group[section_field])
        if sections and sections.issubset(map_only):
            allowed.append(district_id)
    return sorted(allowed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    args = parser.parse_args()
    config = load_params_yaml(args.params)
    m08 = module_cfg(config, "modulo_08_integrar_resultados", "step8_join_results")
    m07 = module_cfg(config, "modulo_07_agregar_resultados_electorales", "step7_elections")
    m06 = module_cfg(config, "modulo_06_consolidar_distritos", "step6_export_final")
    districts_geo = require(
        m08.get("in_district_geojson") or m06.get("out_district_geojson"),
        "Falta M08 geometría",
    )
    results_csv = require(
        m08.get("in_district_summary_csv") or m07.get("out_district_summary_csv"),
        "Falta M08 resultados",
    )
    out_geo = require(m08.get("out_districts_with_results_geojson"), "Falta M08 salida")
    allowed_missing=[]
    if bool(m08.get("allow_declared_map_only_districts", False)):
        section_geo=require(m06.get("out_geojson"), "Falta M06 secciones para auditar excepciones M08")
        reconciliation_path=require(m07.get("out_reconciliation_report"), "Falta informe de reconciliación M07")
        import json
        reconciliation=json.loads(Path(reconciliation_path).read_text(encoding="utf-8"))
        if reconciliation.get("status") not in {"PASS","PASS_WITH_DECLARED_EXCEPTIONS"}:
            raise ValueError("M08 no puede usar excepciones de una reconciliación M07 no aprobada")
        allowed_missing=derive_declared_missing_districts(
            load_geojson_zip(section_geo),
            reconciliation,
            section_field=require(m07.get("section_id_field"), "Falta M07 section_id"),
            district_field=require(m07.get("district_field"), "Falta M07 district_id"),
        )
    output = integrate_results(
        load_geojson_zip(districts_geo),
        pd.read_csv(Path(results_csv)),
        allowed_missing_districts=allowed_missing,
    )
    write_geojson_zip(output, out_geo)
    print(f"[Módulo 8] OK districts={len(output)} allowed_missing={allowed_missing} out={out_geo}")


if __name__ == "__main__":
    main()
