#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 02 — Construir adyacencias
VERSIÓN: 7.3.1
NOMBRE DE VERSIÓN: Política topológica declarativa por ámbito
FECHA: 2026-09-16
ESTADO: candidato
QUÉ HACE: calcula adyacencias geométricas con umbral métrico explícito y aplica, opcionalmente, pasarelas topológicas declarativas auditables.
POR QUÉ ES SEPARADO: M02 define la relación territorial elemental; M03 solo audita el grafo resultante y los módulos posteriores no deben compensar una adyacencia mal construida.
CAMBIOS: reutiliza la validación común de pasarelas y evalúa necesidad/eficacia dentro del subgrafo inducido por admin_scope.
MOTIVO: evitar interpretaciones divergentes entre M02 y el preflight topológico.
ANTERIOR: legacy/modulo02/02_construir_adyacencias_v7.1.0.py
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd

from ddd_core.config import load_params_yaml, module_cfg, require
from ddd_core.topology_preflight import validate_topology_bridges


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


def load_geojson_any(path_str):
    p = Path(path_str).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"GeoJSON no encontrado: {p}")
    if p.suffix.lower() == ".zip" and p.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(p, "r") as z:
            members = [n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")]
            if not members:
                raise ValueError(f"ZIP GeoJSON sin .geojson/.json: {p}")
            return _gpd_read_file(io.BytesIO(z.read(members[0])))
    return _gpd_read_file(str(p))


def _relation_ok(gi, gj, predicate, min_shared_border_m, max_precision_overlap_area_m2):
    if predicate == "touches":
        if not gi.touches(gj):
            return False
        return gi.boundary.intersection(gj.boundary).length >= min_shared_border_m

    if predicate == "intersects":
        if not gi.intersects(gj):
            return False
        return gi.boundary.intersection(gj.boundary).length >= min_shared_border_m

    if predicate == "contact":
        if not gi.intersects(gj):
            return False
        shared = float(gi.boundary.intersection(gj.boundary).length)
        if shared < min_shared_border_m:
            return False
        overlap_area = float(gi.intersection(gj).area)
        return gi.touches(gj) or overlap_area <= max_precision_overlap_area_m2

    raise SystemExit(f"M02: predicate no soportado: {predicate}")


def iter_edges(
    gdf,
    id_field,
    predicate,
    min_shared_border_m,
    max_precision_overlap_area_m2,
    buffer_m,
    simplify_m,
    max_candidates,
    log_every,
    working_crs,
) -> Iterable[Tuple[str, str]]:
    if id_field not in gdf.columns:
        raise SystemExit(f"id_field '{id_field}' no existe")

    gdf = gdf.copy().reset_index(drop=True)
    gdf[id_field] = gdf[id_field].astype(str)
    if gdf.crs is None:
        raise SystemExit("M02: geometría sin CRS; no se puede construir una adyacencia métrica reproducible")
    try:
        gdf = gdf.to_crs(working_crs)
    except Exception as exc:
        raise SystemExit(f"M02: no se puede reproyectar a {working_crs}: {exc}") from exc

    geom = gdf.geometry
    if simplify_m and simplify_m > 0:
        geom = geom.simplify(simplify_m, preserve_topology=True)
    if buffer_m and buffer_m != 0:
        geom = geom.buffer(buffer_m)
    gdf["_geom_work"] = geom

    work = gdf.set_geometry("_geom_work")
    sindex = work.sindex
    seen = set()

    for i in range(len(work)):
        row = work.iloc[i]
        gi = row["_geom_work"]
        if gi is None or gi.is_empty:
            continue
        cand_pos = list(sindex.intersection(gi.bounds))
        if max_candidates and len(cand_pos) > max_candidates:
            ib = gi.bounds
            icx, icy = (ib[0] + ib[2]) / 2, (ib[1] + ib[3]) / 2

            def _dist(j):
                jb = work.iloc[j]["_geom_work"].bounds
                jcx, jcy = (jb[0] + jb[2]) / 2, (jb[1] + jb[3]) / 2
                return (icx - jcx) ** 2 + (icy - jcy) ** 2

            cand_pos = sorted(cand_pos, key=_dist)[:max_candidates]

        u = str(row[id_field])
        for j in cand_pos:
            if j == i:
                continue
            other = work.iloc[j]
            v = str(other[id_field])
            a, b = (u, v) if u < v else (v, u)
            key = (a, b)
            if key in seen:
                continue
            gj = other["_geom_work"]
            if gj is None or gj.is_empty:
                continue
            if not _relation_ok(gi, gj, predicate, min_shared_border_m, max_precision_overlap_area_m2):
                continue
            seen.add(key)
            if log_every and len(seen) % log_every == 0:
                print(f"[Módulo 2] edges={len(seen)}")
            yield key


def write_edges_jsonl(geometric_edges, bridges, out_path):
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    geom = {tuple(sorted((str(u), str(v)))) for u, v in geometric_edges if str(u) != str(v)}
    bridge_map = {(b["u"], b["v"]): b for b in bridges if (b["u"], b["v"]) not in geom}
    with outp.open("w", encoding="utf-8") as f:
        for u, v in sorted(geom):
            f.write(json.dumps({"u": u, "v": v, "edge_type": "geometric"}, ensure_ascii=False) + "\n")
        for key in sorted(bridge_map):
            f.write(json.dumps(bridge_map[key], ensure_ascii=False) + "\n")
    return len(geom) + len(bridge_map), len(geom), len(bridge_map)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()
    cfg = load_params_yaml(args.params)
    s2 = module_cfg(cfg, "modulo_02_construir_adyacencias", legacy_step_key="step2_export_edges")
    s4 = module_cfg(cfg, "modulo_04_generar_semillas", legacy_step_key="step4_generate_seeds")
    in_geo = require(s2.get("in_geojson"), "Falta M02 entrada")
    id_field = require(s2.get("id_field"), "Falta M02 id")
    out_edges = require(s2.get("out_edges_jsonl"), "Falta M02 salida")
    gdf = load_geojson_any(in_geo)
    gdf[id_field] = gdf[id_field].astype(str)

    if "min_shared_border_m" not in s2:
        raise SystemExit("M02: min_shared_border_m debe declararse explícitamente; no existe fallback")
    min_shared = float(s2["min_shared_border_m"])
    contract = cfg.get("territory_contract") or {}
    productive_continental = (
        (cfg.get("meta") or {}).get("contract_level") == "production_m01_m06"
        and str(contract.get("topology_mode", "land")) == "land"
    )
    if productive_continental and min_shared <= 0:
        raise SystemExit("M02: territorio continental productivo exige min_shared_border_m > 0")

    predicate = str(s2.get("predicate", "touches"))
    max_overlap = float(s2.get("max_precision_overlap_area_m2", 1.0))
    working_crs = str(s2.get("working_crs", "EPSG:25830"))
    geometric = list(
        iter_edges(
            gdf,
            id_field,
            predicate,
            min_shared,
            max_overlap,
            float(s2.get("buffer_m", 0)),
            float(s2.get("simplify_m", 0)),
            int(s2.get("max_candidates", 50)),
            int(s2.get("log_every", 10000)),
            working_crs,
        )
    )

    province_field = str(s2.get("bridge_admin_level_1_field", s4.get("province_field", "CPRO")))
    municipality_field = str(s2.get("bridge_admin_level_2_field", s4.get("municipality_field", "CUMUN")))
    for field in (province_field, municipality_field):
        if field not in gdf.columns:
            raise SystemExit(f"M02: campo administrativo para pasarelas ausente: {field}")

    units = {
        str(row[id_field]): {
            "province": str(row[province_field]).zfill(2),
            "municipality": str(row[municipality_field]),
        }
        for _, row in gdf.iterrows()
    }
    bridges, rejected, _ = validate_topology_bridges(
        units=units,
        bridges=s2.get("topology_bridges", []) or [],
        base_edges=geometric,
    )
    if rejected:
        first = rejected[0]
        raise SystemExit(f"M02 pasarela inválida: {first.get('rejection_reason', 'error de política')}")

    n, ng, nb = write_edges_jsonl(geometric, bridges, out_edges)
    print(
        f"[Módulo 2] OK v7.3.1 edges={n} geometric={ng} bridges={nb} "
        f"predicate={predicate} min_shared_border_m={min_shared} crs={working_crs} out={out_edges}"
    )


if __name__ == "__main__":
    main()
