#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 4 — Seed contiguous districts (v7.0 — KMeans++ + island-free)

Why the previous version produced islands
-----------------------------------------
The heap contains entries (cost, k, node). When a node is pushed for
district k, it may later lose its adjacency to k because a neighbour got
claimed by another district. The old code skipped such nodes silently.
They then fell to a BFS fallback that attached them to "nearest assigned
node by graph traversal" — which is NOT necessarily geographically
nearest, so sections could be attached to a district on the other side
of the map, creating geographic islands.

Three-phase fix
---------------
Phase 1 — heap-driven growth (fast, balanced, comarca-aware).
Phase 2 — BFS sweep: repeats until no more changes; each still-unassigned
           node is attached to whichever adjacent district it shares the
           most boundary with (ties broken by best pop balance). Guaranteed
           to leave only truly isolated nodes.
Phase 3 — truly isolated (degree-0) nodes → nearest district centroid.

District IDs: 1-based (1..K).

YAML: steps.step4_seed_districts.*
"""
from __future__ import annotations
import sys, argparse, io, json, zipfile, random, heapq, collections, math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd
import numpy as np

from ddd_core.config import load_params_yaml, step_cfg, require


# ── I/O ──────────────────────────────────────────────────────────────────────
def _gpd_read(path_or_buf, layer=None):
    try:
        import pyogrio; return pyogrio.read_dataframe(path_or_buf, layer=layer)
    except Exception: pass
    try:
        return gpd.read_file(path_or_buf, layer=layer, engine="pyogrio")
    except Exception:
        return gpd.read_file(path_or_buf, layer=layer)


def load_geojson(p: str) -> gpd.GeoDataFrame:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"GeoJSON no encontrado: {pp}")
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm = [n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def load_graph(p: str) -> Dict[str,Any]:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"Graph JSON no encontrado: {pp}")
    return json.loads(pp.read_text(encoding="utf-8"))


def write_gz(gdf: gpd.GeoDataFrame, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        tmp = pp.parent / (pp.stem.replace(".geojson","") + ".geojson")
        gdf.to_file(tmp, driver="GeoJSON")
        with zipfile.ZipFile(pp, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.write(tmp, arcname=tmp.name)
        try: tmp.unlink()
        except Exception: pass
    else:
        gdf.to_file(p, driver="GeoJSON")


def write_json(obj: Any, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# ── KMeans++ seeds ────────────────────────────────────────────────────────────
def _kpp_pure(coords: np.ndarray, weights: np.ndarray, K: int, rng: random.Random) -> List[int]:
    N = len(coords)
    chosen = [rng.randrange(N)]
    for _ in range(1, K):
        dists = np.full(N, np.inf)
        for c in chosen:
            d = np.sum((coords - coords[c])**2, axis=1)
            dists = np.minimum(dists, d)
        probs = dists * weights
        total = probs.sum()
        if total <= 0:
            chosen.append(rng.randrange(N)); continue
        probs /= total
        r, cum, idx = rng.random(), 0.0, N-1
        for i, pr in enumerate(probs):
            cum += pr
            if r <= cum: idx = i; break
        chosen.append(idx)
    return chosen


def _kpp_sklearn(coords: np.ndarray, weights: np.ndarray, K: int, seed: int) -> List[int]:
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=K, init="k-means++", n_init=3, random_state=seed, max_iter=300)
    km.fit(coords, sample_weight=weights)
    used: Set[int] = set()
    chosen: List[int] = []
    for c in km.cluster_centers_:
        for idx in np.argsort(np.sum((coords - c)**2, axis=1)):
            if int(idx) not in used:
                chosen.append(int(idx)); used.add(int(idx)); break
    return chosen


# ── Island-free growth ────────────────────────────────────────────────────────
def grow(
    nodes: List[str],
    adj: Dict[str, Set[str]],
    pop_map: Dict[str, int],
    comarca_map: Dict[str, str],
    centroid_map: Dict[str, Tuple[float, float]],
    seeds: List[str],
    target: float,
    cw: float,          # comarca crossing weight (>1 penalises crossing)
) -> Dict[str, int]:
    """Returns {node_id → district_id (1-based)}. Every node is assigned."""
    K = len(seeds)
    assign: Dict[str, Optional[int]] = {n: None for n in nodes}
    dpop:   List[int]             = [0] * K
    dcom:   List[Dict[str,int]]   = [{} for _ in range(K)]
    dcx =   [0.0]*K;  dcy = [0.0]*K;  dn = [0]*K   # running centroid

    heap: List[Tuple[float, int, int, str]] = []
    ctr = 0

    def push(k: int, node: str):
        nonlocal ctr
        popn = pop_map.get(node, 0)
        cost = abs(dpop[k] + popn - target)
        nc = comarca_map.get(node, "")
        if nc and cw > 1.0 and dcom[k]:
            dom = max(dcom[k], key=dcom[k].__getitem__)
            if nc != dom: cost *= cw
        heapq.heappush(heap, (cost, ctr, k, node)); ctr += 1

    def claim(k: int, node: str):
        assign[node] = k + 1
        popn = pop_map.get(node, 0)
        dpop[k] += popn
        nc = comarca_map.get(node, "")
        if nc: dcom[k][nc] = dcom[k].get(nc, 0) + 1
        cx, cy = centroid_map.get(node, (0.0, 0.0))
        dcx[k] = (dcx[k]*dn[k] + cx) / (dn[k]+1)
        dcy[k] = (dcy[k]*dn[k] + cy) / (dn[k]+1)
        dn[k] += 1

    # Seed initialisation
    for k, s in enumerate(seeds):
        claim(k, s)
        for nb in adj.get(s, set()):
            if assign[nb] is None: push(k, nb)

    # Phase 1: heap
    while heap:
        _, _, k, node = heapq.heappop(heap)
        if assign[node] is not None: continue
        if not any(assign.get(nb) == k+1 for nb in adj.get(node, set())):
            continue   # stale — Phase 2 will catch it
        claim(k, node)
        for nb in adj.get(node, set()):
            if assign[nb] is None: push(k, nb)

    # Phase 2: BFS sweep — attach stale-dropped nodes to their graph neighbours.
    # We collect all unassigned nodes first, then iterate.
    # Repeat until no node can be assigned (handles chains of dropped nodes).
    prev_unassigned = -1
    while True:
        unassigned = [n for n in nodes if assign[n] is None]
        if not unassigned or len(unassigned) == prev_unassigned:
            break          # nothing left to attach, or truly isolated
        prev_unassigned = len(unassigned)
        for node in unassigned:
            # count adjacent nodes per district
            adj_d: Dict[int, int] = {}
            for nb in adj.get(node, set()):
                d = assign.get(nb)
                if d and d > 0:
                    adj_d[d] = adj_d.get(d, 0) + 1
            if not adj_d: continue
            # best district: most shared neighbours, then best pop balance
            best_d = max(adj_d, key=lambda d: (
                adj_d[d],
                -abs(dpop[d-1] + pop_map.get(node, 0) - target)
            ))
            claim(best_d - 1, node)

    # Phase 3: isolated nodes (no graph neighbours at all) → nearest centroid
    for node in nodes:
        if assign[node] is not None: continue
        cx, cy = centroid_map.get(node, (0.0, 0.0))
        best_k = min(range(K), key=lambda k: (dcx[k]-cx)**2 + (dcy[k]-cy)**2)
        claim(best_k, node)

    return {n: v for n, v in assign.items() if v is not None}


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s4  = step_cfg(cfg, "step4_seed_districts")

    in_graph  = require(s4.get("in_graph_json",""), "Falta steps.step4_seed_districts.in_graph_json")
    in_geo    = require(s4.get("in_geojson",""),    "Falta steps.step4_seed_districts.in_geojson")
    id_field  = require(s4.get("id_field",""),      "Falta steps.step4_seed_districts.id_field")
    pop_field = require(s4.get("pop_field",""),     "Falta steps.step4_seed_districts.pop_field")
    K         = int(require(s4.get("k_districts"), "Falta steps.step4_seed_districts.k_districts"))
    out_geo   = require(s4.get("out_geojson",""),   "Falta steps.step4_seed_districts.out_geojson")
    out_rep   = s4.get("out_report","") or ""
    seed      = int(s4.get("seed", 12345) or 12345)
    cw        = float(s4.get("comarca_priority_weight", 1.5) or 1.5)

    rng = random.Random(seed)
    np.random.seed(seed)

    G  = load_graph(in_graph)
    nodes       = [n["id"] for n in G.get("nodes",[])]
    pop_map     = {n["id"]: int(n.get("pop",0)) for n in G.get("nodes",[])}
    comarca_map = {n["id"]: n.get("comarca_id","") for n in G.get("nodes",[])}
    adj: Dict[str,Set[str]] = {nid: set() for nid in nodes}
    for e in G.get("edges",[]):
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj: adj[u].add(v); adj[v].add(u)

    has_comarca = any(v for v in comarca_map.values())
    print(f"[Step4] comarca={'YES' if has_comarca else 'NO'} nodes={len(nodes)} K={K}")

    # Centroids from GeoJSON (projected to metric for distance calculations)
    gdf = load_geojson(in_geo)
    if id_field not in gdf.columns:
        raise SystemExit(f"GeoJSON sin id_field '{id_field}'.")
    gdf_m = gdf.copy()
    if gdf_m.crs is None: gdf_m = gdf_m.set_crs(4326)
    try: gdf_m = gdf_m.to_crs(25830)
    except Exception: pass
    gdf_m["_id"] = gdf_m[id_field].astype(str)
    centroid_map: Dict[str,Tuple[float,float]] = dict(zip(
        gdf_m["_id"],
        zip(gdf_m.geometry.centroid.x.tolist(), gdf_m.geometry.centroid.y.tolist())
    ))

    valid   = [n for n in nodes if n in centroid_map]
    coords  = np.array([centroid_map[n] for n in valid])
    weights = np.array([max(pop_map.get(n,0),1) for n in valid], dtype=float)

    try:
        idxs = _kpp_sklearn(coords, weights, K, seed)
        print(f"[Step4] scikit-learn KMeans++ → {K} semillas")
    except ImportError:
        idxs = _kpp_pure(coords, weights, K, rng)
        print(f"[Step4] KMeans++ puro Python → {K} semillas (instala scikit-learn para mejor calidad)")

    seen: Set[str] = set()
    seeds: List[str] = []
    for i in idxs:
        n = valid[i]
        if n not in seen: seeds.append(n); seen.add(n)
    for n in valid:
        if len(seeds) == K: break
        if n not in seen: seeds.append(n); seen.add(n)

    total_pop = sum(pop_map.values())
    target    = total_pop / float(K) if K > 0 else 0.0

    assign = grow(
        nodes=nodes, adj=adj, pop_map=pop_map,
        comarca_map=comarca_map, centroid_map=centroid_map,
        seeds=seeds, target=target,
        cw=cw if has_comarca else 1.0,
    )

    # Safety net
    leftover = [n for n in nodes if assign.get(n,-1) <= 0]
    if leftover:
        print(f"[Step4] AVISO: {len(leftover)} nodos sin asignar → distrito con menor población")
        cnt = collections.Counter(assign.values())
        for n in leftover:
            d = min(range(1, K+1), key=lambda d: cnt.get(d,0))
            assign[n] = d; cnt[d] += 1

    gdf["_id"]          = gdf[id_field].astype(str)
    gdf["district_id"]  = gdf["_id"].map(lambda x: assign.get(x,-1)).astype("int64")
    gdf["district_pop"] = gdf["_id"].map(lambda x: pop_map.get(x,0)).astype("int64")
    write_gz(gdf.drop(columns=["_id"]), out_geo)

    cnt2: Dict[int,int] = collections.Counter()
    for n, d in assign.items(): cnt2[d] += pop_map.get(n,0)
    pops = list(cnt2.values())
    max_dev  = max(abs(p-target)/target for p in pops) if pops and target>0 else 0.0
    mean_dev = sum(abs(p-target)/target for p in pops)/K if K>0 and target>0 else 0.0

    if out_rep:
        write_json({"step":"step4_seed_districts","version":"7.0","K":K,
                    "total_pop":int(total_pop),"target":float(target),
                    "max_rel_dev":float(max_dev),"mean_rel_dev":float(mean_dev),
                    "comarca_weight":cw,"has_comarca":bool(has_comarca),
                    "seed":seed,"out_geojson":out_geo}, out_rep)

    print(f"[Step4] OK K={K} target≈{target:.0f} max_dev={max_dev:.3f} mean_dev={mean_dev:.3f} out={out_geo}")


if __name__ == "__main__":
    main()
