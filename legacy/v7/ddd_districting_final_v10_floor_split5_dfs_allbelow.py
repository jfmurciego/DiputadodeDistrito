#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDD — Motor final v7 (cierre below=0 con max_split relajado SOLO para repair de suelo)

- Contigüidad estricta.
- Suelo duro (>= floor_ratio*target) y techo duro (<= cap_ratio*target).
- Operador global para suelo: merge + repartición local con m<=max_split_floor (p.ej. 5).
- Salidas forzadas a ./output/

Inputs:
  --in_geojson, --edges_jsonl, --k, --floor_ratio, --cap_ratio
  --id_field, --pop_field
  --comarca_field (opcional, preferencia suave solo en grow inicial)

Output:
  output/<out_geojson>, output/<out_report>
"""

import argparse, json, os, re, time
from collections import defaultdict, deque

def parse_edges(path: str):
    adj = defaultdict(set)
    bad = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            if s[0] == "{":
                try:
                    o = json.loads(s)
                    u = o.get("u") or o.get("src") or o.get("a") or o.get("from")
                    v = o.get("v") or o.get("dst") or o.get("b") or o.get("to")
                    if u is None or v is None:
                        bad += 1
                        continue
                    u = str(u); v = str(v)
                except Exception:
                    bad += 1
                    continue
            else:
                parts = re.split(r"[,\t\s]+", s)
                parts = [x for x in parts if x]
                if len(parts) < 2:
                    bad += 1
                    continue
                u, v = str(parts[0]), str(parts[1])
            if u == v:
                continue
            adj[u].add(v); adj[v].add(u)
    return adj, bad

def is_connected_subset(adj, subset):
    if not subset:
        return True
    start = next(iter(subset))
    dq = deque([start])
    seen = {start}
    while dq:
        x = dq.popleft()
        for nb in adj.get(x, ()):
            if nb in subset and nb not in seen:
                seen.add(nb)
                dq.append(nb)
    return len(seen) == len(subset)

def induced_adj(adj, subset):
    return {n: set(nb for nb in adj.get(n, ()) if nb in subset) for n in subset}

def bfs_tree(adj_sub, root):
    parent = {root: None}
    order = [root]
    dq = deque([root])
    while dq:
        x = dq.popleft()
        for nb in sorted(adj_sub.get(x, ())):
            if nb not in parent:
                parent[nb] = x
                dq.append(nb)
                order.append(nb)
    return parent, order

def partition_by_tree_recursive(adj_sub, pops, nodes, m, floor, cap, target):
    """
    Partición determinista contigua en m partes usando cortes en árbol BFS.
    Garantiza conectividad (subcomponentes del árbol).
    Condición de factibilidad por parte: [floor, cap] (por distrito).
    Para m>1 aplica bisección recursiva (m_left + m_right = m).
    """
    if m == 1:
        return [set(nodes)]

    # escoger root: nodo más poblado
    root = max(nodes, key=lambda n: (pops[n], n))
    parent, order = bfs_tree(adj_sub, root)

    # si árbol no cubre todo, no es conexo (debería no ocurrir)
    if len(parent) != len(nodes):
        return None

    # children list
    children = defaultdict(list)
    for n, p in parent.items():
        if p is not None:
            children[p].append(n)

    # postorder para subtree pops
    post = list(reversed(order))
    sub_pop = {n: pops[n] for n in nodes}
    sub_nodes = {n: {n} for n in nodes}
    for n in post:
        for c in children.get(n, ()):
            sub_pop[n] += sub_pop[c]
            sub_nodes[n] |= sub_nodes[c]

    total_pop = sum(pops[n] for n in nodes)

    m_left = m // 2
    m_right = m - m_left

    need_left_lo = m_left * floor
    need_left_hi = m_left * cap
    need_right_lo = m_right * floor
    need_right_hi = m_right * cap

    target_left = m_left * target

    # buscar mejor corte: subtree de algún child-rooted
    best = None
    best_score = 1e30

    for n in nodes:
        if n == root:
            continue
        left_nodes = sub_nodes[n]
        left_pop = sub_pop[n]
        right_pop = total_pop - left_pop

        if left_pop < need_left_lo - 1e-9 or left_pop > need_left_hi + 1e-9:
            continue
        if right_pop < need_right_lo - 1e-9 or right_pop > need_right_hi + 1e-9:
            continue

        score = abs(left_pop - target_left)
        if score < best_score:
            best_score = score
            best = (left_nodes, set(nodes) - set(left_nodes))

    if best is None:
        return None

    left_nodes, right_nodes = best

    # recursión
    left_adj = induced_adj(adj_sub, left_nodes)
    right_adj = induced_adj(adj_sub, right_nodes)

    left_parts = partition_by_tree_recursive(left_adj, pops, left_nodes, m_left, floor, cap, target)
    if left_parts is None:
        return None
    right_parts = partition_by_tree_recursive(right_adj, pops, right_nodes, m_right, floor, cap, target)
    if right_parts is None:
        return None

    return left_parts + right_parts


def choose_seeds(ids_sorted, adj_sub, k, top_m=120, min_sep_hops=1):
    candidates = ids_sorted[:max(k, top_m)]
    seeds = []
    blocked = set()
    def mark(seed):
        dq = deque([(seed, 0)])
        seen = {seed}
        while dq:
            x, d = dq.popleft()
            if d >= min_sep_hops:
                continue
            for nb in adj_sub.get(x, ()):
                if nb not in seen:
                    seen.add(nb)
                    blocked.add(nb)
                    dq.append((nb, d+1))
    for cid in candidates:
        if cid in blocked:
            continue
        seeds.append(cid)
        mark(cid)
        if len(seeds) >= k:
            break
    if len(seeds) < k:
        for cid in ids_sorted:
            if cid not in seeds:
                seeds.append(cid)
                if len(seeds) >= k:
                    break
    return seeds[:k]

def grow_full_coverage(adj, pops, seeds, k, cap, comarca=None, prefer_same=True,
                       grow_overcap_ratio=0.02, timebox_s=60):
    t0 = time.time()
    eff_cap = cap * (1.0 + max(0.0, float(grow_overcap_ratio)))
    assigned = {}
    dn = [set() for _ in range(k)]
    dp = [0.0 for _ in range(k)]

    for did, s in enumerate(seeds):
        assigned[s] = did
        dn[did].add(s)
        dp[did] += pops[s]

    frontier = [set() for _ in range(k)]
    for did in range(k):
        for n in dn[did]:
            for nb in adj.get(n, ()):
                if nb not in assigned:
                    frontier[did].add(nb)

    all_nodes = set(pops.keys())
    unassigned = all_nodes - set(assigned.keys())

    def district_priority(did):
        return (dp[did], did)

    while unassigned and (time.time() - t0) <= timebox_s:
        dids = sorted(range(k), key=district_priority)
        progressed = False
        for did in dids:
            if not frontier[did]:
                continue
            cands = list(frontier[did])
            if prefer_same and comarca is not None:
                anchor = comarca.get(seeds[did], "")
                if anchor:
                    same = [x for x in cands if comarca.get(x, "") == anchor]
                    if same:
                        cands = same
            cands = sorted(set(cands), key=lambda x: (pops[x], x))
            chosen = None
            for x in cands:
                if dp[did] + pops[x] <= eff_cap + 1e-9:
                    chosen = x
                    break
            if chosen is None:
                continue
            assigned[chosen] = did
            dn[did].add(chosen)
            dp[did] += pops[chosen]
            unassigned.remove(chosen)
            frontier[did].discard(chosen)
            for nb in adj.get(chosen, ()):
                if nb not in assigned:
                    frontier[did].add(nb)
            for od in range(k):
                if od != did and chosen in frontier[od]:
                    frontier[od].discard(chosen)
            progressed = True
            break
        if not progressed:
            break
    return assigned, dn, dp, (all_nodes - set(assigned.keys()))

def fill_coverage_first(adj, pops, assigned, dn, dp, cap, fill_overcap_ratio=0.05, timebox_s=240):
    t0 = time.time()
    eff_cap = cap * (1.0 + max(0.0, float(fill_overcap_ratio)))
    all_nodes = set(pops.keys())
    unassigned = all_nodes - set(assigned.keys())
    moves = 0
    while unassigned and (time.time() - t0) <= timebox_s:
        progressed = False
        for u in sorted(list(unassigned)):
            neigh = set()
            for nb in adj.get(u, ()):
                if nb in assigned:
                    neigh.add(assigned[nb])
            if not neigh:
                continue
            u_pop = pops[u]
            # elegir con más slack si cabe, si no el menos malo
            best = None
            best_slack = -1e18
            for did in neigh:
                slack = eff_cap - (dp[did] + u_pop)
                if slack >= -1e-9 and slack > best_slack:
                    best_slack = slack; best = did
            if best is None:
                best = max(neigh, key=lambda did: (eff_cap - (dp[did] + u_pop), -did))
            assigned[u] = best
            dn[best].add(u)
            dp[best] += u_pop
            unassigned.remove(u)
            moves += 1
            progressed = True
            break
        if not progressed:
            break
    return moves, (all_nodes - set(assigned.keys()))

def district_neighbors(adj, assigned, dn, did):
    neigh = set()
    for n in dn[did]:
        for nb in adj.get(n, ()):
            if nb in assigned and assigned[nb] != did:
                neigh.add(assigned[nb])
    return neigh

def multisource_partition(adj_sub, pops, m, target, floor, cap, timebox_s=15):
    """
    Partición determinista contigua en m partes usando cortes en árbol BFS.
    Devuelve (dn, dp) o None.
    """
    nodes = set(adj_sub.keys())
    if not nodes:
        return None
    parts = partition_by_tree_recursive(adj_sub, pops, nodes, m, floor, cap, target)
    if parts is None or len(parts) != m:
        return None
    dn = [set(p) for p in parts]
    dp = [float(sum(pops[n] for n in p)) for p in dn]
    # validación final
    for p in dp:
        if p < floor - 1e-9 or p > cap + 1e-9:
            return None
    return dn, dp

def recom_fix_floor_relaxed(adj, pops, assigned, dn, dp, floor, cap, target,
                           max_split_floor=5, timebox_s=420):
    """
    Cierra below buscando conjuntos conectados de distritos (tamaño ≤ max_split_floor)
    y re-particionando el subgrafo unido en el mismo número de distritos (m).
    Recorre TODOS los distritos below (de menor a mayor) hasta encontrar un movimiento.
    """
    t0 = time.time()
    k = len(dn)
    moves = 0

    def below_ids():
        return [i for i,p in enumerate(dp) if p < floor - 1e-9]

    def below_count(vec):
        return sum(1 for p in vec if p < floor - 1e-9)

    def build_district_adj():
        d_adj = [set() for _ in range(k)]
        for did in range(k):
            for n in dn[did]:
                for nb in adj.get(n, ()):
                    if nb in assigned:
                        od = assigned[nb]
                        if od != did:
                            d_adj[did].add(od)
        return d_adj

    def union_nodes_of(Slist):
        nodes = set()
        up = 0.0
        for d in Slist:
            nodes |= dn[d]
            up += dp[d]
        return nodes, up

    def feasible(m, upop):
        return (upop >= m*floor - 1e-9) and (upop <= m*cap + 1e-9)

    while (time.time() - t0) <= timebox_s:
        bl = below_ids()
        if not bl:
            break

        d_adj = build_district_adj()
        applied = False

        # probar cada below, empezando por el más bajo
        for did0 in sorted(bl, key=lambda i: (dp[i], i)):
            if (time.time() - t0) > timebox_s:
                break

            def gen_sets(size, max_states=2200):
                results = []
                stack = [(frozenset([did0]), set(d_adj[did0]))]
                seen = set([frozenset([did0])])
                while stack and len(results) < max_states:
                    S, boundary = stack.pop()
                    if len(S) == size:
                        results.append(S)
                        continue
                    if len(S) > size:
                        continue
                    cand = sorted(list(boundary), key=lambda x: (-dp[x], x))[:18]
                    for j in cand:
                        if j in S:
                            continue
                        S2 = frozenset(set(S) | {j})
                        if S2 in seen:
                            continue
                        seen.add(S2)
                        b2 = set(boundary)
                        b2 |= d_adj[j]
                        b2 -= set(S2)
                        stack.append((S2, b2))
                return results

            b0 = below_count(dp)

            # tamaños crecientes; en práctica m=5 es el que suele destrabar
            for m in range(2, max_split_floor + 1):
                if (time.time() - t0) > timebox_s:
                    break
                for S in gen_sets(m):
                    S_list = sorted(list(S))
                    nodes, up = union_nodes_of(S_list)
                    if not feasible(m, up):
                        continue

                    adj_sub = induced_adj(adj, nodes)
                    part = multisource_partition(adj_sub, pops, m, target, floor, cap, timebox_s=35)
                    if part is None:
                        continue
                    dn_new, dp_new = part

                    new_dp = list(dp)
                    for idx in range(m):
                        did = S_list[idx]
                        new_dp[did] = float(dp_new[idx])
                    b1 = below_count(new_dp)
                    if b1 >= b0:
                        continue

                    for idx in range(m):
                        did = S_list[idx]
                        dn[did] = set(dn_new[idx])
                        dp[did] = float(dp_new[idx])
                        for n in dn_new[idx]:
                            assigned[n] = did

                    moves += 1
                    applied = True
                    break
                if applied:
                    break
            if applied:
                break

        if not applied:
            break

    return moves, time.time() - t0

def repair_above_simple(adj, pops, assigned, dn, dp, cap, timebox_s=240):
    t0 = time.time()
    moves = 0

    def boundary(did):
        b = set()
        for n in dn[did]:
            for nb in adj.get(n, ()):
                if nb in assigned and assigned[nb] != did:
                    b.add(n); break
        return b

    while (time.time() - t0) <= timebox_s:
        above = [i for i,p in enumerate(dp) if p > cap + 1e-9]
        if not above:
            break
        src = max(above, key=lambda i: dp[i] - cap)
        bnd = sorted(boundary(src), key=lambda x: (pops[x], x))
        moved = False
        for n in bnd:
            n_pop = pops[n]
            neigh = set(assigned[nb] for nb in adj.get(n, ()) if nb in assigned and assigned[nb] != src)
            if not neigh:
                continue
            dsts = sorted(neigh, key=lambda d: (cap - dp[d]), reverse=True)
            for dst in dsts:
                if dp[dst] + n_pop > cap + 1e-9:
                    continue
                if len(dn[src]) <= 1:
                    continue
                new_src = set(dn[src]); new_src.remove(n)
                if not is_connected_subset(adj, new_src):
                    continue
                dn[src].remove(n); dp[src] -= n_pop
                dn[dst].add(n); dp[dst] += n_pop
                assigned[n] = dst
                moves += 1
                moved = True
                break
            if moved:
                break
        if not moved:
            break
    return moves, time.time() - t0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in_geojson", required=True)
    ap.add_argument("--edges_jsonl", required=True)
    ap.add_argument("--out_geojson", required=True)
    ap.add_argument("--out_report", required=True)

    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--floor_ratio", type=float, default=0.80)
    ap.add_argument("--cap_ratio", type=float, default=1.75)
    ap.add_argument("--max_split", type=int, default=3)  # se mantiene para resto del motor
    ap.add_argument("--max_split_floor", type=int, default=5)  # SOLO para cierre de suelo

    ap.add_argument("--id_field", required=True)
    ap.add_argument("--pop_field", required=True)
    ap.add_argument("--comarca_field", default=None)
    ap.add_argument("--prefer_same_comarca", type=int, default=1)

    ap.add_argument("--seed_top_m", type=int, default=120)
    ap.add_argument("--min_seed_sep_hops", type=int, default=2)

    ap.add_argument("--timebox_grow_s", type=int, default=60)
    ap.add_argument("--timebox_fill_s", type=int, default=240)
    ap.add_argument("--timebox_floor_s", type=int, default=420)
    ap.add_argument("--timebox_repair_s", type=int, default=240)

    ap.add_argument("--grow_overcap_ratio", type=float, default=0.02)
    ap.add_argument("--fill_overcap_ratio", type=float, default=0.05)

    args = ap.parse_args()
    t_all = time.time()

    with open(args.in_geojson, "r", encoding="utf-8") as f:
        gj = json.load(f)
    feats = gj.get("features", [])
    if not feats:
        raise ValueError("GeoJSON sin features.")

    pops = {}
    comarca = None
    if args.comarca_field:
        comarca = {}
    ids = []
    for ft in feats:
        props = ft.get("properties", {})
        uid = str(props[args.id_field])
        popv = props.get(args.pop_field)
        if popv is None:
            raise ValueError("Hay POP nula; corrige input.")
        popf = float(popv)
        if popf <= 0:
            raise ValueError("Hay POP <= 0; corrige input.")
        pops[uid] = popf
        ids.append(uid)
        if comarca is not None:
            comarca[uid] = str(props.get(args.comarca_field) or "")

    if len(set(ids)) != len(ids):
        raise ValueError("IDs duplicados en id_field.")

    adj, bad = parse_edges(args.edges_jsonl)
    if bad:
        print(f"[WARN] líneas edges no parseables: {bad}")

    missing = set(pops.keys()) - set(adj.keys())
    if missing:
        raise ValueError(f"Hay {len(missing)} nodos aislados en edges.")

    total_pop = float(sum(pops.values()))
    target = total_pop / float(args.k)
    floor = target * float(args.floor_ratio)
    cap = target * float(args.cap_ratio)

    print(f"[INFO] total_pop={total_pop:.1f} k={args.k} target={target:.2f} floor={floor:.2f} cap={cap:.2f}")

    ids_sorted = sorted(pops.keys(), key=lambda x: (pops[x], x), reverse=True)
    seeds = choose_seeds(ids_sorted, adj, args.k, top_m=args.seed_top_m, min_sep_hops=args.min_seed_sep_hops)

    t_grow0 = time.time()
    assigned, dn, dp, unassigned = grow_full_coverage(
        adj=adj, pops=pops, seeds=seeds, k=args.k, cap=cap,
        comarca=comarca,
        prefer_same=bool(args.prefer_same_comarca) if comarca is not None else False,
        grow_overcap_ratio=args.grow_overcap_ratio,
        timebox_s=args.timebox_grow_s
    )
    grow_time = time.time() - t_grow0

    t_fill0 = time.time()
    fill_moves, un2 = fill_coverage_first(
        adj=adj, pops=pops, assigned=assigned, dn=dn, dp=dp,
        cap=cap, fill_overcap_ratio=args.fill_overcap_ratio,
        timebox_s=args.timebox_fill_s
    )
    fill_time = time.time() - t_fill0

    t_floor0 = time.time()
    floor_moves, floor_time = recom_fix_floor_relaxed(
        adj=adj, pops=pops, assigned=assigned, dn=dn, dp=dp,
        floor=floor, cap=cap, target=target,
        max_split_floor=args.max_split_floor,
        timebox_s=args.timebox_floor_s
    )
    floor_time = time.time() - t_floor0

    t_rep0 = time.time()
    repair_moves, repair_time = repair_above_simple(
        adj=adj, pops=pops, assigned=assigned, dn=dn, dp=dp,
        cap=cap, timebox_s=args.timebox_repair_s
    )
    repair_time = time.time() - t_rep0

    below = sum(1 for p in dp if p < floor - 1e-9)
    above = sum(1 for p in dp if p > cap + 1e-9)
    minp = min(dp)
    maxp = max(dp)
    un_final = len(set(pops.keys()) - set(assigned.keys()))
    H = int(below + above)

    print(f"[INFO] H={H} below={below} above={above} disc=0 unassigned={un_final} min_pop={minp:.0f} max_pop={maxp:.0f}")

    os.makedirs("output", exist_ok=True)
    out_geo = os.path.join("output", os.path.basename(args.out_geojson))
    out_rep = os.path.join("output", os.path.basename(args.out_report))

    for ft in feats:
        uid = str(ft["properties"][args.id_field])
        ft["properties"]["district_id"] = int(assigned.get(uid, -1))

    with open(out_geo, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)

    report = {
        "k": args.k,
        "total_pop": total_pop,
        "target": target,
        "floor_ratio": args.floor_ratio,
        "cap_ratio": args.cap_ratio,
        "floor": floor,
        "cap": cap,
        "max_split": args.max_split,
        "max_split_floor": args.max_split_floor,
        "stats": {
            "min_pop": float(minp),
            "max_pop": float(maxp),
            "below_floor": int(below),
            "above_cap": int(above),
            "disconnected": 0,
            "H": int(H),
            "unassigned_remaining": int(un_final),
            "fill_moves": int(fill_moves),
            "floor_moves": int(floor_moves),
            "repair_moves": int(repair_moves),
        },
        "timing_s": {
            "total": float(time.time() - t_all),
            "grow": float(grow_time),
            "fill": float(fill_time),
            "floor": float(floor_time),
            "repair": float(repair_time),
        }
    }
    with open(out_rep, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[INFO] wrote: {out_geo}")
    print(f"[INFO] report: {out_rep}")

if __name__ == "__main__":
    main()
