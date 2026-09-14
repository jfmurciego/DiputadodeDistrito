#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 08 — Integrar resultados en el mapa final
VERSIÓN: 7.1.0
NOMBRE DE VERSIÓN: Unión electoral exhaustiva
FECHA: 2026-09-14
QUÉ HACE: une resultados agregados con la geometría y exige cobertura distrital exacta.
POR QUÉ ES SEPARADO: es la unión final de dos productos ya generados y permite cambiar datos electorales sin redistritar.
ESTADO: vigente — R039
CAMBIOS: hace legible M08 y bloquea duplicados, faltantes y distritos electorales ajenos.
MOTIVO: impedir productos parciales creados por una unión silenciosa.
ANTERIOR: legacy/modulo08/08_integrar_resultados_v7.0.2.py
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd
import geopandas as gpd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ddd_core.config import load_params_yaml, module_cfg, require


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


def integrate_results(gdf, results):
    """Une solo si geometría y resumen describen exactamente los mismos distritos."""
    if "district_id" not in gdf.columns or "district_id" not in results.columns:
        raise ValueError("Falta district_id en M08")
    geo = gdf.copy()
    electoral = results.copy()
    geo["district_id"] = geo["district_id"].astype(str)
    electoral["district_id"] = electoral["district_id"].astype(str)
    duplicated = sorted(electoral.loc[electoral["district_id"].duplicated(False), "district_id"].unique())
    if duplicated:
        raise ValueError(f"M08 recibió distritos electorales duplicados: {duplicated}")
    geo_ids = set(geo["district_id"])
    electoral_ids = set(electoral["district_id"])
    missing = sorted(geo_ids - electoral_ids)
    unexpected = sorted(electoral_ids - geo_ids)
    if missing or unexpected:
        raise ValueError(
            "Cobertura distrital electoral incompleta: "
            f"sin_resultados={missing}, ajenos_al_mapa={unexpected}"
        )
    return geo.merge(electoral, on="district_id", how="left", validate="one_to_one")


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
    output = integrate_results(load_geojson_zip(districts_geo), pd.read_csv(Path(results_csv)))
    write_geojson_zip(output, out_geo)
    print(f"[Módulo 8] OK districts={len(output)} out={out_geo}")


if __name__ == "__main__":
    main()
