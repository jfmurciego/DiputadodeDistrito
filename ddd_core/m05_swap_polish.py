#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: M05 — Pulido determinista por swaps 1×1
VERSIÓN: 1.0.1
NOMBRE: Swap-polish canónico — corrección de alias
FECHA: 2026-09-11
FUNCIÓN: aplicar iterativamente el mejor intercambio 1×1 de unidades territoriales frontera después del
optimizador M05, preservando provincia, suelo/techo, distritos urbanos cerrados y contigüidad estricta.
CRITERIO: acepta únicamente swaps que mejoren lexicográficamente la función objetivo canónica de M05:
violaciones duras, magnitud dura, distritos fuera de tolerancia, máximo desvío y error cuadrático.
CAMBIOS: renombra las variables locales de población `pd`/`pe` a `pop_d`/`pop_e` para no eclipsar el alias
`pandas as pd`. No cambia el algoritmo, la función objetivo ni ninguna restricción territorial.
MOTIVO: EXT-06 Run 34641628564 llegó correctamente al swap-polish pero falló antes de evaluarlo con
`UnboundLocalError` por sombreado léxico del alias pandas.
ANTERIOR: legacy/modulo05/m05_swap_polish_v1.0.0.py
"""
from __future__ import annotations

import io
import json
import zipfile
from collections import deque
from pathlib import Path

import geopandas as gpd
import pandas as pd


def load_geo(path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            n = next(
                n for n in z.namelist()
                if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")
            )
            return gpd.read_file(io.BytesIO(z.read(n)))
    return gpd.read_file(p)


def write_geo(gdf, path):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / (out.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def connected(nodes, adj):
    nodes = set(nodes)
    if not nodes:
        return False
    start = next(iter(nodes))
    seen = {start}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in adj.get(u, set()):
            if v in nodes and v not in seen:
                seen.add(v)
                q.append(v)
    return len(seen) == len(nodes)


def objective(values, target, floor, cap, tol):
    vals = list(values.values())
    hard = sum(p < floor or p > cap for p in vals)
    hard_mag = sum(max(0, floor - p, p - cap) for p in vals)
    outside = sum(abs(p - target) > tol for p in vals)
    maxdev = max(abs(p - target) / target for p in vals)
    sq = sum(((p - target) / target) ** 2 for p in vals)
    return (
        hard,
        round(hard_mag / target, 12),
        outside,
        round(maxdev, 12),
        round(sq, 12),
    )


def polish(*, cfg, graph_path, geojson_path, out_geojson_path=None, max_swaps=200):
    """Aplica swaps 1×1 monótonos y devuelve metadatos del pulido."""
    mods = cfg.get("modulos", {}) or {}
    s5 = mods.get("modulo_05_optimizar_distritos") or cfg.get("step5_optimize_swaps") or {}
    val = cfg.get("validation", {}) or {}

    idf = s5.get("id_field", "CUSEC_KEY")
    did = s5.get("district_field", "district_id")
    provf = s5.get("province_field", "CPRO")

    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in graph["nodes"]}
    adj = {n: set() for n in pop}
    for e in graph["edges"]:
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    g = load_geo(geojson_path)
    g[idf] = g[idf].astype(str)
    g[did] = pd.to_numeric(g[did], errors="raise").astype(int)
    g[provf] = g[provf].astype(str).str.zfill(2)
    if "ddd_unit_id" not in g.columns or "ddd_closed_urban" not in g.columns:
        raise SystemExit("M05 swap-polish requiere ddd_unit_id y ddd_closed_urban")
    g["ddd_unit_id"] = g["ddd_unit_id"].astype(str)

    section_to_unit = dict(zip(g[idf], g["ddd_unit_id"]))
    unit_nodes = {u: set(x[idf].astype(str)) for u, x in g.groupby("ddd_unit_id")}
    unit_pop = {u: sum(pop.get(n, 0) for n in ns) for u, ns in unit_nodes.items()}
    unit_dist = {u: int(x[did].iloc[0]) for u, x in g.groupby("ddd_unit_id")}
    unit_prov = {u: str(x[provf].iloc[0]).zfill(2) for u, x in g.groupby("ddd_unit_id")}
    if any(x[did].nunique() != 1 for _, x in g.groupby("ddd_unit_id")):
        raise SystemExit("M05 swap-polish: unidad territorial partida entre distritos")

    d_units = {d: set(x["ddd_unit_id"].astype(str)) for d, x in g.groupby(did)}
    d_nodes = {d: set(x[idf].astype(str)) for d, x in g.groupby(did)}
    d_pop = {d: sum(pop.get(n, 0) for n in ns) for d, ns in d_nodes.items()}
    d_prov = {d: str(g[g[did] == d][provf].iloc[0]).zfill(2) for d in d_nodes}
    d_closed = {int(d): bool(x["ddd_closed_urban"].all()) for d, x in g.groupby(did)}

    total = sum(pop.values())
    K = len(d_pop)
    target, floor, cap, tol = hard_limits(cfg, k=K, total_pop=total)

    uadj = {u: set() for u in unit_nodes}
    for n, u in section_to_unit.items():
        for nb in adj.get(n, set()):
            v = section_to_unit.get(nb)
            if v is not None and v != u:
                uadj[u].add(v)

    start_obj = objective(d_pop, target, floor, cap, tol)
    swaps = []

    for iteration in range(max_swaps):
        cur = objective(d_pop, target, floor, cap, tol)
        outliers = {d for d, p in d_pop.items() if abs(p - target) > tol}
        if not outliers:
            break

        boundary = {d: set() for d in d_pop}
        for u, d in unit_dist.items():
            if d_closed.get(d, False):
                continue
            if any(unit_dist.get(v) != d for v in uadj.get(u, set())):
                boundary[d].add(u)

        pairs = set()
        for d in outliers:
            if d_closed.get(d, False):
                continue
            for u in boundary[d]:
                for v in uadj.get(u, set()):
                    e = unit_dist[v]
                    if (
                        e != d
                        and not d_closed.get(e, False)
                        and d_prov[e] == d_prov[d]
                    ):
                        pairs.add(tuple(sorted((d, e))))

        best = None
        for d, e in sorted(pairs):
            if d_closed.get(d, False) or d_closed.get(e, False):
                continue
            for u in sorted(boundary[d], key=str):
                if not any(unit_dist.get(v) == e for v in uadj.get(u, set())):
                    continue
                for v in sorted(boundary[e], key=str):
                    if not any(unit_dist.get(x) == d for x in uadj.get(v, set())):
                        continue
                    if unit_prov[u] != unit_prov[v] or unit_prov[u] != d_prov[d]:
                        continue
                    if u == v:
                        continue

                    nd = (d_nodes[d] - unit_nodes[u]) | unit_nodes[v]
                    ne = (d_nodes[e] - unit_nodes[v]) | unit_nodes[u]
                    if not nd or not ne:
                        continue
                    if not connected(nd, adj) or not connected(ne, adj):
                        continue

                    pop_d = d_pop[d] - unit_pop[u] + unit_pop[v]
                    pop_e = d_pop[e] - unit_pop[v] + unit_pop[u]
                    if not (floor <= pop_d <= cap and floor <= pop_e <= cap):
                        continue

                    trial = dict(d_pop)
                    trial[d] = pop_d
                    trial[e] = pop_e
                    obj = objective(trial, target, floor, cap, tol)
                    if obj >= cur:
                        continue
                    key = (obj, str(u), str(v), d, e)
                    cand = (key, d, e, u, v, nd, ne, trial)
                    if best is None or key < best[0]:
                        best = cand

        if best is None:
            break

        _, d, e, u, v, nd, ne, trial = best
        before = cur
        d_units[d].remove(u)
        d_units[d].add(v)
        d_units[e].remove(v)
        d_units[e].add(u)
        d_nodes[d] = nd
        d_nodes[e] = ne
        d_pop = trial
        unit_dist[u] = e
        unit_dist[v] = d
        after = objective(d_pop, target, floor, cap, tol)
        swaps.append({
            "iteration": iteration + 1,
            "districts": [d, e],
            "unit_d": u,
            "unit_e": v,
            "unit_d_population": unit_pop[u],
            "unit_e_population": unit_pop[v],
            "new_populations": [d_pop[d], d_pop[e]],
            "objective_before": list(before),
            "objective_after": list(after),
        })

    for u, d in unit_dist.items():
        g.loc[g["ddd_unit_id"] == u, did] = int(d)

    final_obj = objective(d_pop, target, floor, cap, tol)
    out_path = Path(out_geojson_path or geojson_path)
    write_geo(g, out_path)

    return {
        "version": "1.0.1",
        "accepted_swaps": len(swaps),
        "objective_start": list(start_obj),
        "objective_final": list(final_obj),
        "outside_start": int(start_obj[2]),
        "outside_final": int(final_obj[2]),
        "max_rel_dev_start": float(start_obj[3]),
        "max_rel_dev_final": float(final_obj[3]),
        "swaps": swaps,
    }
