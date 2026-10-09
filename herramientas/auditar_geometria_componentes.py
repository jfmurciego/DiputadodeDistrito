#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
HERRAMIENTA: Auditoría geométrica de componentes desconectadas
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Relaciones geométricas entre componentes
FECHA: 2026-09-11
QUÉ HACE: reconstruye componentes del grafo por provincia y municipio y diagnostica cada componente menor contra las secciones más próximas del mismo ámbito administrativo, midiendo distancia y relaciones geométricas exactas.
POR QUÉ ES SEPARADA: M02 construye adyacencias y M03 certifica conectividad; esta herramienta explica por qué una componente quedó separada sin modificar el grafo ni introducir excepciones.
CAMBIOS: primera versión; informa distance, touches, intersects, overlaps, within, contains, DE-9IM relate, área de intersección y longitud de borde compartido en CRS métrico.
MOTIVO: EXT-02 mostró secciones a distancia 0 m que no cumplen `touches`; necesitamos distinguir solape cartográfico, contención, borde compartido y auténtico exclave antes de cambiar M02.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import geopandas as gpd


def load_geo(path: str) -> gpd.GeoDataFrame:
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            name = next(n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/"))
            return gpd.read_file(io.BytesIO(z.read(name)))
    return gpd.read_file(p)


def components(nodes: set[str], adj: dict[str, set[str]]) -> list[set[str]]:
    remaining = set(nodes)
    out: list[set[str]] = []
    while remaining:
        start = min(remaining)
        seen = {start}
        stack = [start]
        while stack:
            u = stack.pop()
            for v in adj.get(u, set()):
                if v in remaining and v not in seen:
                    seen.add(v)
                    stack.append(v)
        remaining -= seen
        out.append(seen)
    return sorted(out, key=lambda x: (-len(x), sorted(x)[0]))


def relation(a, b) -> dict:
    inter = a.intersection(b)
    return {
        "distance_m": round(float(a.distance(b)), 3),
        "touches": bool(a.touches(b)),
        "intersects": bool(a.intersects(b)),
        "overlaps": bool(a.overlaps(b)),
        "within": bool(a.within(b)),
        "contains": bool(a.contains(b)),
        "equals": bool(a.equals(b)),
        "relate": str(a.relate(b)),
        "intersection_area_m2": round(float(inter.area), 3),
        "shared_boundary_m": round(float(a.boundary.intersection(b.boundary).length), 3),
    }


def audit_scope(g, adj, idf, key_field, name_field, scope_name, nearest_n):
    findings = []
    for key, gx in g.groupby(key_field, dropna=False):
        ids = set(gx[idf].astype(str))
        comps = components(ids, adj)
        if len(comps) <= 1:
            continue
        main = comps[0]
        for rank, comp in enumerate(comps[1:], start=2):
            candidates = []
            for u in sorted(comp):
                a = g.loc[g[idf] == u, "geometry"].iloc[0]
                for v in sorted(main):
                    b = g.loc[g[idf] == v, "geometry"].iloc[0]
                    r = relation(a, b)
                    candidates.append((r["distance_m"], -r["intersection_area_m2"], -r["shared_boundary_m"], u, v, r))
            candidates.sort(key=lambda x: x[:5])
            near = []
            for _, _, _, u, v, r in candidates[:nearest_n]:
                ru = g.loc[g[idf] == u].iloc[0]
                rv = g.loc[g[idf] == v].iloc[0]
                near.append({
                    "from_section": u,
                    "to_section": v,
                    "from_population": int(ru.get("POP_2025", 0)),
                    "to_population": int(rv.get("POP_2025", 0)),
                    "to_municipality": str(rv.get("CUMUN", "")),
                    "to_municipality_name": str(rv.get("NMUN", "")),
                    **r,
                })
            first = gx.iloc[0]
            findings.append({
                "scope": scope_name,
                "key": str(key),
                "name": str(first.get(name_field, "")) if name_field else "",
                "total_nodes": len(ids),
                "component_rank": rank,
                "component_size": len(comp),
                "component_sections": sorted(comp),
                "main_component_size": len(main),
                "nearest_relations": near,
            })
    return findings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geojson", required=True)
    ap.add_argument("--graph", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--id-field", default="CUSEC_KEY")
    ap.add_argument("--province-field", default="CPRO")
    ap.add_argument("--municipality-field", default="CUMUN")
    ap.add_argument("--municipality-name-field", default="NMUN")
    ap.add_argument("--metric-crs", default="EPSG:3035")
    ap.add_argument("--nearest", type=int, default=8)
    args = ap.parse_args()

    g = load_geo(args.geojson)
    if g.crs is None:
        raise SystemExit("Auditoría geométrica: GeoJSON sin CRS")
    for col in (args.id_field, args.province_field, args.municipality_field):
        if col not in g.columns:
            raise SystemExit(f"Auditoría geométrica: falta columna {col}")
    g[args.id_field] = g[args.id_field].astype(str)
    g[args.province_field] = g[args.province_field].astype(str).str.zfill(2)
    g[args.municipality_field] = g[args.municipality_field].astype(str)
    g = g.to_crs(args.metric_crs)

    graph = json.loads(Path(args.graph).read_text(encoding="utf-8"))
    ids = set(g[args.id_field])
    adj = {u: set() for u in ids}
    for e in graph.get("edges", []):
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    province = audit_scope(g, adj, args.id_field, args.province_field, None, "province", args.nearest)
    municipality = audit_scope(
        g,
        adj,
        args.id_field,
        args.municipality_field,
        args.municipality_name_field,
        "municipality",
        args.nearest,
    )
    report = {
        "version": "1.0.0",
        "metric_crs": args.metric_crs,
        "nodes": len(ids),
        "graph_edges": sum(len(v) for v in adj.values()) // 2,
        "province_disconnected_components": province,
        "municipality_disconnected_components": municipality,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"[Auditoría geométrica] OK provincias_componentes={len(province)} "
        f"municipios_componentes={len(municipality)} out={out}"
    )
    for f in municipality:
        print(json.dumps(f, ensure_ascii=False))


if __name__ == "__main__":
    main()
