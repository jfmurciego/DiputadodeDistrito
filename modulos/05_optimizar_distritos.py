#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.1.0
NOMBRE DE VERSIÓN: Reparación prioritaria de restricciones poblacionales
FECHA: 2026-09-11
ESTADO: candidato
FUNCIÓN: optimizar la asignación manteniendo contigüidad y priorizando las restricciones duras de población antes de la desviación respecto del target.
ENTRADAS: grafo territorial M03, solución inicial M04, configuración y reglas de validación.
SALIDAS: asignación optimizada M05 y reporte de métricas.
RAZÓN DE EXISTENCIA: resolver el equilibrio territorial sin reconstruir la base M01-M03.
CAMBIOS VS 7.0.1: sustituye la función objetivo basada únicamente en max_rel_dev por una función lexicográfica: número de violaciones de suelo/techo, magnitud total de violación, máximo desvío y error cuadrático. Añade una fase dirigida de reparación de distritos ilegales antes del pulido aleatorio. El movimiento mantiene conectividad del distrito donante y solo entra en un distrito receptor adyacente.
MOTIVO: GitHub Run #3 alcanzó M08 pero falló la puerta de calidad con 29 distritos bajo 0,80×target; la métrica anterior podía considerar óptima una solución todavía ilegal.
VERSIÓN ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.0.1.py
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import random
import sys
import zipfile
from pathlib import Path
from typing import Dict, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd

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
            members = [
                n for n in z.namelist()
                if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")
            ]
            if not members:
                raise RuntimeError(f"ZIP sin GeoJSON/JSON: {p}")
            data = z.read(members[0])
        return _gpd_read_file(io.BytesIO(data))
    return _gpd_read_file(str(p))


def load_graph(path_str):
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


def write_geojson_zip(gdf, out_path):
    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    tmp = outp.parent / (outp.stem.replace(".geojson", "") + ".geojson")
    gdf.to_file(tmp, driver="GeoJSON")
    with zipfile.ZipFile(outp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(tmp, arcname=tmp.name)
    tmp.unlink(missing_ok=True)


def write_json(obj, out_path):
    Path(out_path).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def district_connected(adj: Dict[str, Set[str]], members: Set[str]) -> bool:
    if not members:
        return False
    start = min(members)
    q = collections.deque([start])
    seen = {start}
    while q:
        x = q.popleft()
        for nb in sorted(adj.get(x, set())):
            if nb in members and nb not in seen:
                seen.add(nb)
                q.append(nb)
    return len(seen) == len(members)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s5 = module_cfg(
        cfg,
        "modulo_05_optimizar_distritos",
        legacy_step_key="step5_optimize_swaps",
    )

    in_graph = require(s5.get("in_graph_json"), "Falta M05 grafo")
    in_geo = require(s5.get("in_geojson"), "Falta M05 geojson")
    id_field = require(s5.get("id_field"), "Falta M05 id")
    pop_field = require(s5.get("pop_field"), "Falta M05 población")
    district_field = s5.get("district_field", "district_id")
    out_geo = require(s5.get("out_geojson"), "Falta M05 salida")
    out_report = s5.get("out_report", "")
    iters = int(s5.get("iters", 20000))
    seed = int(s5.get("seed", 12345))
    rng = random.Random(seed)

    validation = cfg.get("validation", {}) or {}
    floor_ratio = float(validation.get("population_floor_ratio", 0.80))
    cap_ratio = float(validation.get("population_cap_ratio", 1.75))

    G = load_graph(in_graph)
    nodes = [str(n["id"]) for n in G.get("nodes", [])]
    pop_map = {str(n["id"]): int(n.get("pop", 0)) for n in G.get("nodes", [])}
    adj = {nid: set() for nid in nodes}
    for e in G.get("edges", []):
        u = str(e["u"])
        v = str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    gdf = load_geojson_any(in_geo)
    if id_field not in gdf.columns or district_field not in gdf.columns:
        raise SystemExit("Entrada M05 sin columnas requeridas")

    if pop_field in gdf.columns:
        df_pop = gdf[[id_field, pop_field]].copy()
        df_pop[id_field] = df_pop[id_field].astype(str)
        df_pop[pop_field] = (
            pd.to_numeric(df_pop[pop_field], errors="coerce")
            .fillna(0)
            .astype("int64")
        )
        for rid, pv in zip(df_pop[id_field], df_pop[pop_field]):
            if rid in pop_map:
                pop_map[rid] = int(pv)

    df = gdf[[id_field, district_field]].copy()
    df[id_field] = df[id_field].astype(str)
    df[district_field] = (
        pd.to_numeric(df[district_field], errors="coerce")
        .fillna(-1)
        .astype("int64")
    )
    assign = {rid: int(did) for rid, did in zip(df[id_field], df[district_field])}

    if not assign or min(assign.values()) < 0:
        raise SystemExit("M05 recibió secciones sin distrito válido")

    K = max(assign.values()) + 1
    total_pop = sum(pop_map.values())
    target = total_pop / float(K)
    floor_pop = floor_ratio * target
    cap_pop = cap_ratio * target

    members = [set() for _ in range(K)]
    pops = [0] * K
    for n, d in assign.items():
        members[d].add(n)
        pops[d] += pop_map.get(n, 0)

    empty = [k for k in range(K) if not members[k]]
    if empty:
        raise SystemExit(f"M05 recibió distritos vacíos: {empty}")

    def objective_for(values) -> Tuple[int, float, float, float]:
        under = sum(1 for p in values if p < floor_pop)
        over = sum(1 for p in values if p > cap_pop)
        violation = 0.0
        max_dev = 0.0
        sq_dev = 0.0
        for p in values:
            if p < floor_pop:
                violation += floor_pop - p
            elif p > cap_pop:
                violation += p - cap_pop
            dev = abs(p - target) / target if target > 0 else 0.0
            max_dev = max(max_dev, dev)
            sq_dev += dev * dev
        # Redondeo únicamente para evitar ruido de coma flotante al comparar tuplas.
        return (
            under + over,
            round(violation / target if target > 0 else violation, 12),
            round(max_dev, 12),
            round(sq_dev, 12),
        )

    def current_objective():
        return objective_for(pops)

    def candidate_objective(d_from: int, d_to: int, popn: int):
        candidate = list(pops)
        candidate[d_from] -= popn
        candidate[d_to] += popn
        return objective_for(candidate)

    def can_move(node: str, d_from: int, d_to: int) -> bool:
        if d_from == d_to or len(members[d_from]) <= 1:
            return False
        if not any(assign.get(nb) == d_to for nb in adj.get(node, set())):
            return False
        remaining = members[d_from] - {node}
        return district_connected(adj, remaining)

    def apply_move(node: str, d_from: int, d_to: int):
        popn = pop_map.get(node, 0)
        members[d_from].remove(node)
        pops[d_from] -= popn
        members[d_to].add(node)
        pops[d_to] += popn
        assign[node] = d_to

    def boundary_nodes():
        result = []
        for node in sorted(assign):
            d = assign[node]
            if any(assign.get(nb, d) != d for nb in adj.get(node, set())):
                result.append(node)
        return result

    start_obj = current_objective()
    accepted_repair = 0
    accepted_polish = 0

    # Fase 1: reparación dirigida. Se atienden primero los distritos que violan
    # suelo/techo. Cada movimiento debe mejorar lexicográficamente la situación
    # global y mantener conectado el distrito donante.
    repair_limit = max(2000, iters // 2)
    for _ in range(repair_limit):
        old_obj = current_objective()
        if old_obj[0] == 0:
            break

        illegal = sorted(
            [d for d, p in enumerate(pops) if p < floor_pop or p > cap_pop],
            key=lambda d: (
                0 if pops[d] < floor_pop else 1,
                -abs(pops[d] - target),
                d,
            ),
        )
        best_move = None
        best_obj = old_obj

        for d_bad in illegal:
            if pops[d_bad] < floor_pop:
                # Recibir desde distritos vecinos.
                candidates = set()
                for m in members[d_bad]:
                    for nb in adj.get(m, set()):
                        if assign.get(nb, d_bad) != d_bad:
                            candidates.add(nb)
                for node in sorted(candidates):
                    d_from = assign[node]
                    popn = pop_map.get(node, 0)
                    if not can_move(node, d_from, d_bad):
                        continue
                    obj = candidate_objective(d_from, d_bad, popn)
                    if obj < best_obj:
                        best_obj = obj
                        best_move = (node, d_from, d_bad)
            else:
                # Ceder desde un distrito sobre techo a cualquiera de sus vecinos.
                for node in sorted(members[d_bad]):
                    neigh_ds = sorted(
                        {
                            assign[nb]
                            for nb in adj.get(node, set())
                            if nb in assign and assign[nb] != d_bad
                        }
                    )
                    for d_to in neigh_ds:
                        popn = pop_map.get(node, 0)
                        if not can_move(node, d_bad, d_to):
                            continue
                        obj = candidate_objective(d_bad, d_to, popn)
                        if obj < best_obj:
                            best_obj = obj
                            best_move = (node, d_bad, d_to)

        if best_move is None:
            break
        apply_move(*best_move)
        accepted_repair += 1

    # Fase 2: pulido local. Una vez reparadas —o hasta donde llegue la reparación—
    # se exploran fronteras de forma reproducible. Nunca se acepta un movimiento
    # que empeore la tupla de restricciones/objetivos.
    boundary = boundary_nodes()
    remaining_iters = max(0, iters - accepted_repair)
    for t in range(remaining_iters):
        if not boundary:
            break
        node = rng.choice(boundary)
        d_from = assign[node]
        neigh_ds = sorted(
            {
                assign[nb]
                for nb in adj.get(node, set())
                if nb in assign and assign[nb] != d_from
            }
        )
        if not neigh_ds:
            continue
        d_to = rng.choice(neigh_ds)
        if not can_move(node, d_from, d_to):
            continue
        popn = pop_map.get(node, 0)
        old_obj = current_objective()
        new_obj = candidate_objective(d_from, d_to, popn)
        if new_obj < old_obj:
            apply_move(node, d_from, d_to)
            accepted_polish += 1
            if accepted_polish % 100 == 0:
                boundary = boundary_nodes()

    final_obj = current_objective()
    under_final = [d for d, p in enumerate(pops) if p < floor_pop]
    over_final = [d for d, p in enumerate(pops) if p > cap_pop]

    # Defensa adicional: M05 no exporta una solución con distritos desconectados.
    disconnected = [d for d in range(K) if not district_connected(adj, members[d])]
    if disconnected:
        raise SystemExit(f"M05 produjo distritos desconectados: {disconnected}")

    gdf["_id"] = gdf[id_field].astype(str)
    gdf[district_field] = gdf["_id"].map(lambda x: assign.get(x, -1)).astype("int64")
    write_geojson_zip(gdf.drop(columns=["_id"]), out_geo)

    report = {
        "module": "05",
        "version": "7.1.0",
        "K": K,
        "total_pop": int(total_pop),
        "target": float(target),
        "population_floor_ratio": floor_ratio,
        "population_cap_ratio": cap_ratio,
        "population_floor": float(floor_pop),
        "population_cap": float(cap_pop),
        "objective_start": list(start_obj),
        "objective_final": list(final_obj),
        "districts_below_floor": len(under_final),
        "districts_above_cap": len(over_final),
        "under_district_ids": under_final,
        "over_district_ids": over_final,
        "best_max_rel_dev": float(final_obj[2]),
        "iters": iters,
        "accepted_repair_moves": accepted_repair,
        "accepted_polish_moves": accepted_polish,
        "seed": seed,
    }
    if out_report:
        write_json(report, out_report)

    print(
        "[Módulo 5] OK "
        f"violaciones={final_obj[0]} bajo_suelo={len(under_final)} "
        f"sobre_techo={len(over_final)} max_rel_dev={final_obj[2]:.4f} "
        f"repair_moves={accepted_repair} polish_moves={accepted_polish} out={out_geo}"
    )


if __name__ == "__main__":
    main()
