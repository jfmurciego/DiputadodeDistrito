#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 02 — Construir adyacencias
VERSIÓN: 7.2.0
NOMBRE DE VERSIÓN: Contacto topológico robusto
FECHA: 2026-09-11
QUÉ HACE: calcula adyacencias geométricas con predicados configurables (`touches`, `intersects`, `contact`) y añade, opcionalmente, pasarelas topológicas explícitas auditables.
POR QUÉ ES SEPARADO: M02 define la relación territorial elemental; M03 solo audita el grafo resultante y los módulos posteriores no deben compensar una adyacencia mal construida.
ESTADO: candidato EXT-02; `touches` mantiene compatibilidad histórica de Aragón y Castilla y León.
CAMBIOS: añade CRS de trabajo configurable, predicado `contact` tolerante a micro-solapes cartográficos, límite configurable de área de solape y uso correcto del índice espacial sobre la geometría de trabajo con índices posicionales normalizados.
MOTIVO: en Monesterio dos secciones comparten más de 1,5 km de borde, pero una reproyección produce un micro-solape de 0,003 m² y hace inestable `touches`. Esa relación es una adyacencia geométrica real y debe modelarse con una regla reusable, no mediante una pasarela territorial falsa.
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
        ok = gi.touches(gj)
        if not ok:
            return False
        if min_shared_border_m > 0:
            return gi.boundary.intersection(gj.boundary).length >= min_shared_border_m
        return True

    if predicate == "intersects":
        ok = gi.intersects(gj)
        if not ok:
            return False
        if min_shared_border_m > 0:
            return gi.boundary.intersection(gj.boundary).length >= min_shared_border_m
        return True

    if predicate == "contact":
        if not gi.intersects(gj):
            return False
        shared = float(gi.boundary.intersection(gj.boundary).length)
        if shared < min_shared_border_m:
            return False
        overlap_area = float(gi.intersection(gj).area)
        # Contacto válido: borde puro o micro-solape atribuible a precisión/cartografía.
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


def _normalize_bridge(raw, valid_ids):
    if not isinstance(raw, dict):
        raise SystemExit("M02 topology_bridges debe contener objetos")
    u = str(require(raw.get("u"), "Puente sin u"))
    v = str(require(raw.get("v"), "Puente sin v"))
    if u == v:
        raise SystemExit(f"Puente inválido con extremos iguales: {u}")
    if u not in valid_ids or v not in valid_ids:
        raise SystemExit(f"Puente con extremo inexistente: {u}-{v}")
    a, b = (u, v) if u < v else (v, u)
    return {
        "u": a,
        "v": b,
        "edge_type": str(raw.get("edge_type", "topology_bridge")),
        "reason": str(raw.get("reason", "")),
        "source": str(raw.get("source", "config")),
    }


def write_edges_jsonl(geometric_edges, bridges, out_path):
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    geom = {tuple(sorted((str(u), str(v)))) for u, v in geometric_edges if str(u) != str(v)}
    bridge_map = {}
    for b in bridges:
        key = (b["u"], b["v"])
        if key not in geom:
            bridge_map[key] = b
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
    in_geo = require(s2.get("in_geojson"), "Falta M02 entrada")
    id_field = require(s2.get("id_field"), "Falta M02 id")
    out_edges = require(s2.get("out_edges_jsonl"), "Falta M02 salida")
    gdf = load_geojson_any(in_geo)
    gdf[id_field] = gdf[id_field].astype(str)
    valid_ids = set(gdf[id_field])

    predicate = str(s2.get("predicate", "touches"))
    min_shared = float(s2.get("min_shared_border_m", 0))
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
    bridges = [_normalize_bridge(x, valid_ids) for x in (s2.get("topology_bridges", []) or [])]
    n, ng, nb = write_edges_jsonl(geometric, bridges, out_edges)
    print(
        f"[Módulo 2] OK v7.2.0 edges={n} geometric={ng} bridges={nb} "
        f"predicate={predicate} crs={working_crs} out={out_edges}"
    )


if __name__ == "__main__":
    main()
