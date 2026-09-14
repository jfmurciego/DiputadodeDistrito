#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DDD Step 5 — Optimise districts via Simulated Annealing (v7.0)

Improvements over v6 baseline:
  1. Simulated Annealing: accepts slightly-worse moves with probability
     exp(-Δ/T), escaping local optima. Temperature decays geometrically.
  2. Multi-objective score:
       score = α·mean_sq_rel_deviation + γ·comarca_violation_fraction
  3. Fast contiguity via Tarjan articulation-point detection.
     A node is only blocked if removing it disconnects its source district.
     Cache invalidated only when district membership changes.
  4. 300k iterations default (feasible with AP check vs full BFS).
  5. District IDs remain 1-based (from Step 4 v7).

YAML: steps.step5_optimize_swaps.*
"""
from __future__ import annotations
import sys, argparse, io, json, zipfile, random, collections, math
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import geopandas as gpd
import pandas as pd

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
    if not pp.exists(): raise FileNotFoundError(f"GeoJSON: {pp}")
    if pp.suffix.lower()==".zip" and pp.name.lower().endswith(".geojson.zip"):
        with zipfile.ZipFile(pp) as z:
            nm = [n for n in z.namelist() if n.lower().endswith((".geojson",".json")) and not n.endswith("/")]
            return _gpd_read(io.BytesIO(z.read(nm[0])))
    return _gpd_read(str(pp))


def load_graph(p: str) -> Dict[str,Any]:
    pp = Path(p).expanduser().resolve()
    if not pp.exists(): raise FileNotFoundError(f"Graph: {pp}")
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
    else: gdf.to_file(p, driver="GeoJSON")


def write_json(obj: Any, p: str):
    pp = Path(p).expanduser().resolve()
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Tarjan articulation points ────────────────────────────────────────────────
def articulation_points(adj: Dict[str,Set[str]], members: Set[str]) -> Set[str]:
    if len(members) <= 2: return set()
    ladj = {m: [nb for nb in adj.get(m,set()) if nb in members] for m in members}
    disc: Dict[str,int] = {}; low: Dict[str,int] = {}
    par:  Dict[str,Optional[str]] = {}; ap: Set[str] = set()
    timer = [0]; root_ch: Dict[str,int] = {}
    for src in members:
        if src in disc: continue
        disc[src] = low[src] = timer[0]; timer[0] += 1
        par[src] = None; root_ch[src] = 0
        stk = [(src, iter(ladj[src]))]
        while stk:
            u, it = stk[-1]
            try:
                v = next(it)
                if v not in disc:
                    disc[v] = low[v] = timer[0]; timer[0] += 1
                    par[v] = u
                    if par[u] is None: root_ch[u] = root_ch.get(u,0)+1
                    stk.append((v, iter(ladj[v])))
                elif v != par[u]:
                    low[u] = min(low[u], disc[v])
            except StopIteration:
                stk.pop()
                if stk:
                    p = par[u]
                    if p:
                        low[p] = min(low[p], low[u])
                        if par[p] is not None and low[u] >= disc[p]: ap.add(p)
    for nd, cnt in root_ch.items():
        if par.get(nd) is None and cnt > 1: ap.add(nd)
    return ap


# ── Score ─────────────────────────────────────────────────────────────────────
def score(pops: List[int], target: float,
          members: List[Set[str]], comarca_map: Dict[str,str],
          alpha: float, gamma: float) -> float:
    K = len(pops)
    pop_term = sum(((p-target)/target)**2 for p in pops)/K if target>0 else 0.0
    com_term = 0.0
    if gamma > 0 and comarca_map:
        total = viol = 0
        for ms in members:
            votes: Dict[str,int] = {}
            for n in ms:
                c = comarca_map.get(n,"")
                if c: votes[c] = votes.get(c,0)+1
            if not votes: continue
            dom = max(votes, key=votes.__getitem__)
            for n in ms:
                c = comarca_map.get(n,"")
                if c:
                    total += 1
                    if c != dom: viol += 1
        com_term = viol/total if total>0 else 0.0
    return alpha * pop_term + gamma * com_term


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    args = ap.parse_args()

    cfg = load_params_yaml(args.params)
    s5  = step_cfg(cfg, "step5_optimize_swaps")

    in_graph  = require(s5.get("in_graph_json",""), "Falta steps.step5_optimize_swaps.in_graph_json")
    in_geo    = require(s5.get("in_geojson",""),    "Falta steps.step5_optimize_swaps.in_geojson")
    id_field  = require(s5.get("id_field",""),      "Falta steps.step5_optimize_swaps.id_field")
    pop_field = require(s5.get("pop_field",""),     "Falta steps.step5_optimize_swaps.pop_field")
    df_field  = s5.get("district_field","district_id") or "district_id"
    out_geo   = require(s5.get("out_geojson",""),   "Falta steps.step5_optimize_swaps.out_geojson")
    out_rep   = s5.get("out_report","") or ""

    iters   = int(s5.get("iters",    300000) or 300000)
    seed    = int(s5.get("seed",      12345) or 12345)
    T0      = float(s5.get("temp_start",0.05) or 0.05)
    T1      = float(s5.get("temp_end",0.0005)or 0.0005)
    alpha   = float(s5.get("alpha_pop",0.70)  or 0.70)
    gamma   = float(s5.get("gamma_comarca",0.10) or 0.10)

    random.seed(seed)

    G  = load_graph(in_graph)
    nodes       = [n["id"] for n in G.get("nodes",[])]
    pop_map     = {n["id"]: int(n.get("pop",0)) for n in G.get("nodes",[])}
    comarca_map = {n["id"]: n.get("comarca_id","") for n in G.get("nodes",[])}
    adj: Dict[str,Set[str]] = {nid: set() for nid in nodes}
    for e in G.get("edges",[]):
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj: adj[u].add(v); adj[v].add(u)

    has_comarca = any(v for v in comarca_map.values())
    if not has_comarca: gamma = 0.0; print("[Step5] Sin comarca → gamma=0")

    gdf = load_geojson(in_geo)
    for col in (id_field, df_field):
        if col not in gdf.columns:
            raise SystemExit(f"GeoJSON sin '{col}'. Columnas: {list(gdf.columns)[:40]}")

    # Update pop_map from GeoJSON (Step4 may have corrected values)
    if pop_field in gdf.columns:
        for _, row in gdf[[id_field, pop_field]].iterrows():
            nid = str(row[id_field])
            if nid in pop_map:
                try: pop_map[nid] = int(float(row[pop_field]))
                except Exception: pass

    dft = gdf[[id_field, df_field]].copy()
    dft[id_field] = dft[id_field].astype(str)
    dft[df_field] = pd.to_numeric(dft[df_field], errors="coerce").fillna(-1).astype("int64")

    assign: Dict[str,int] = {
        str(r[id_field]): int(r[df_field])
        for _, r in dft.iterrows() if int(r[df_field]) > 0
    }

    all_dists = sorted({d for d in assign.values() if d>0})
    K = len(all_dists)
    d2k = {d: i for i,d in enumerate(all_dists)}   # 1-based → 0-based
    k2d = {i: d for d,i in d2k.items()}             # 0-based → 1-based

    members: List[Set[str]] = [set() for _ in range(K)]
    pops:    List[int]      = [0]*K
    cvotes:  List[Dict[str,int]] = [{} for _ in range(K)]

    for n, d in assign.items():
        if d<=0: continue
        k = d2k[d]
        members[k].add(n)
        pops[k] += pop_map.get(n,0)
        c = comarca_map.get(n,"")
        if c: cvotes[k][c] = cvotes[k].get(c,0)+1

    total_pop = sum(pops)
    target    = total_pop/float(K) if K>0 else 0.0

    # AP cache
    ap_cache: Dict[int, Optional[Set[str]]] = {k: None for k in range(K)}
    def get_ap(k: int) -> Set[str]:
        if ap_cache[k] is None: ap_cache[k] = articulation_points(adj, members[k])
        return ap_cache[k]  # type: ignore

    boundary: List[str] = []
    def rebuild():
        nonlocal boundary
        boundary = [
            n for n, d in assign.items()
            if d>0 and any(assign.get(nb,-1)>0 and assign.get(nb,-1)!=d for nb in adj.get(n,set()))
        ]

    rebuild()
    cur = score(pops, target, members, comarca_map, alpha, gamma)
    best_score = cur; best_assign = dict(assign)

    log_r = math.log(T1/T0) if T0>0 else 0.0
    accepted = improved = 0
    rbev = max(2000, iters//150)

    print(f"[Step5] SA iters={iters} T={T0}→{T1} α={alpha} γ={gamma} K={K}")

    for t in range(iters):
        if not boundary: rebuild()
        if not boundary: break

        n = random.choice(boundary)
        d_from = assign.get(n,-1)
        if d_from<=0: continue
        kf = d2k[d_from]
        if len(members[kf])<=1: continue
        if n in get_ap(kf): continue    # contiguity guard

        nk = {d2k[assign[nb]] for nb in adj.get(n,set())
              if assign.get(nb,-1)>0 and assign.get(nb,-1)!=d_from}
        if not nk: continue
        kt = random.choice(tuple(nk))

        popn = pop_map.get(n,0)
        # Pop delta (only two districts change)
        old_sq = ((pops[kf]-target)/target)**2 + ((pops[kt]-target)/target)**2
        new_sq = ((pops[kf]-popn-target)/target)**2 + ((pops[kt]+popn-target)/target)**2
        d_pop  = alpha * (new_sq - old_sq) / K

        # Comarca delta
        d_com = 0.0
        if gamma > 0:
            c = comarca_map.get(n,"")
            if c:
                total_sec = max(sum(len(m) for m in members), 1)
                dom_f = max(cvotes[kf], key=cvotes[kf].__getitem__) if cvotes[kf] else ""
                dom_t = max(cvotes[kt], key=cvotes[kt].__getitem__) if cvotes[kt] else ""
                was_bad  = 1 if (dom_f and c!=dom_f) else 0
                will_bad = 1 if (dom_t and c!=dom_t) else 0
                d_com = gamma * (will_bad - was_bad) / total_sec

        delta = d_pop + d_com
        T = T0 * math.exp(log_r * t / max(iters,1))

        if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-10)):
            d_to = k2d[kt]
            assign[n] = d_to
            members[kf].discard(n); members[kt].add(n)
            pops[kf] -= popn;       pops[kt] += popn
            c = comarca_map.get(n,"")
            if c:
                cvotes[kf][c] = max(0, cvotes[kf].get(c,0)-1)
                cvotes[kt][c] = cvotes[kt].get(c,0)+1
            ap_cache[kf] = None; ap_cache[kt] = None
            cur += delta; accepted += 1
            if delta<0: improved += 1
            if cur < best_score: best_score=cur; best_assign=dict(assign)

        if (t+1)%rbev==0: rebuild()
        if (t+1)%(rbev*5)==0:
            # Recompute full score to correct float drift
            cur = score(pops, target, members, comarca_map, alpha, gamma)
            pct = 100*(t+1)/iters
            print(f"[Step5] {pct:5.1f}%  T={T:.5f}  score={cur:.5f}  best={best_score:.5f}  acc={accepted}")

    assign = best_assign

    # Hard repair: no empty districts
    cnt = collections.Counter(assign.values())
    for k in range(K):
        d = k2d[k]
        if cnt.get(d,0)==0:
            donors = sorted([kk for kk in range(K) if cnt.get(k2d[kk],0)>1],
                            key=lambda kk: cnt.get(k2d[kk],0), reverse=True)
            if not donors: break
            dd = k2d[donors[0]]
            cand = next(
                (n for n in assign if assign[n]==dd and
                 any(assign.get(nb,-1)!=dd for nb in adj.get(n,set()))),
                next((n for n in assign if assign[n]==dd), None)
            )
            if cand: assign[cand]=d; cnt[dd]-=1; cnt[d]=cnt.get(d,0)+1

    gdf["_id"]     = gdf[id_field].astype(str)
    gdf[df_field]  = gdf["_id"].map(lambda x: assign.get(x,-1)).astype("int64")
    write_gz(gdf.drop(columns=["_id"]), out_geo)

    fp: List[int] = [0]*K
    for n, d in assign.items():
        if d>0: fp[d2k[d]] += pop_map.get(n,0)
    mx = max(abs(p-target)/target for p in fp) if fp and target>0 else 0.0
    mn = sum(abs(p-target)/target for p in fp)/K if K>0 and target>0 else 0.0

    if out_rep:
        write_json({"step":"step5_optimize_swaps","version":"7.0",
                    "algorithm":"simulated_annealing","K":K,
                    "total_pop":int(total_pop),"target":float(target),
                    "iters":iters,"accepted":accepted,"improved":improved,
                    "best_score":float(best_score),
                    "final_max_rel_dev":float(mx),"final_mean_rel_dev":float(mn),
                    "T0":T0,"T1":T1,"alpha":alpha,"gamma":gamma,
                    "has_comarca":bool(has_comarca),"seed":seed}, out_rep)

    print(f"[Step5] OK best={best_score:.5f} max_dev={mx:.4f} mean_dev={mn:.4f} "
          f"accepted={accepted}/{iters} out={out_geo}")


if __name__ == "__main__":
    main()
