#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Preflight topológico territorial genérico
VERSIÓN: 1.0.0
FECHA: 2026-09-16
ESTADO: candidato
QUÉ HACE: inspecciona el producto M01 existente y el contrato, mide contactos físicos, aplica la política declarada de pasarelas y emite un informe READY / NEEDS_POLICY / BLOCKED. No ejecuta M01-M03.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ddd_core.config import load_params_yaml, module_cfg, require
from ddd_core.topology_preflight import evaluate_topology_preflight
from modulos import _compat_import  # noqa: F401

# Reutiliza el lector canónico de M02 sin ejecutar su main.
import importlib.util


def _load_m02_module(root: Path):
    path = root / "modulos" / "02_construir_adyacencias.py"
    spec = importlib.util.spec_from_file_location("ddd_m02_preflight", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"No se puede cargar M02 desde {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _multipart(geom) -> bool:
    return getattr(geom, "geom_type", "") == "MultiPolygon" and len(getattr(geom, "geoms", [])) > 1


def _measure_contacts(gdf, id_field: str, working_crs: str):
    work = gdf.copy().reset_index(drop=True).to_crs(working_crs)
    work[id_field] = work[id_field].astype(str)
    sindex = work.sindex
    seen = set()
    contacts = []
    for i in range(len(work)):
        gi = work.geometry.iloc[i]
        if gi is None or gi.is_empty:
            continue
        u = str(work.iloc[i][id_field])
        for j in sindex.intersection(gi.bounds):
            if j == i:
                continue
            gj = work.geometry.iloc[j]
            if gj is None or gj.is_empty or not gi.intersects(gj):
                continue
            v = str(work.iloc[j][id_field])
            key = tuple(sorted((u, v)))
            if key in seen:
                continue
            seen.add(key)
            shared = float(gi.boundary.intersection(gj.boundary).length)
            contacts.append({"u": key[0], "v": key[1], "shared_border_m": shared})
    return contacts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    root = Path(cfg["_internal"]["root"]).resolve()
    m02 = module_cfg(cfg, "modulo_02_construir_adyacencias", legacy_step_key="step2_export_edges")
    m04 = module_cfg(cfg, "modulo_04_generar_semillas", legacy_step_key="step4_generate_seeds")
    in_geo = require(m02.get("in_geojson"), "Preflight: falta M01/M02 in_geojson")
    id_field = require(m02.get("id_field"), "Preflight: falta id_field")
    if "min_shared_border_m" not in m02:
        raise SystemExit("Preflight: min_shared_border_m debe declararse explícitamente; no existe fallback")
    min_shared = float(m02["min_shared_border_m"])
    working_crs = str(m02.get("working_crs", "EPSG:25830"))
    province_field = str(m04.get("province_field", "CPRO"))
    municipality_field = str(m04.get("municipality_field", "CUMUN"))

    m02_module = _load_m02_module(root)
    gdf = m02_module.load_geojson_any(in_geo)
    for field in (id_field, province_field, municipality_field):
        if field not in gdf.columns:
            raise SystemExit(f"Preflight: campo requerido ausente: {field}")
    gdf[id_field] = gdf[id_field].astype(str)

    units = {}
    for _, row in gdf.iterrows():
        uid = str(row[id_field])
        units[uid] = {
            "province": str(row[province_field]).zfill(2),
            "municipality": str(row[municipality_field]),
            "multipart": _multipart(row.geometry),
        }

    contacts = _measure_contacts(gdf, id_field, working_crs)
    contract = cfg.get("territory_contract") or {}
    productive_continental = (
        (cfg.get("meta") or {}).get("contract_level") == "production_m01_m06"
        and str(contract.get("topology_mode", "land")) == "land"
    )
    report = evaluate_topology_preflight(
        units=units,
        contacts=contacts,
        bridges=m02.get("topology_bridges", []) or [],
        min_shared_border_m=min_shared,
        productive_continental=productive_continental,
    )
    report["territory_id"] = (cfg.get("meta") or {}).get("territory_id")
    report["source"] = {"params": str(Path(args.params)), "m01_geojson": str(in_geo), "working_crs": working_crs}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[preflight topológico] {report['decision']} -> {out}")
    if report["decision"] == "BLOCKED":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
