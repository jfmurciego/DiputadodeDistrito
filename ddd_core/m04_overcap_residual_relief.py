#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Alivio de residuos municipales sobre el techo
VERSIÓN: 1.1.0
FECHA: 2026-11-07
FUNCIÓN: cuando un distrito supera el techo porque el residuo R de un municipio
dividido absorbe municipios dependientes (enclaves que solo lindan con él), ceder secciones
fronterizas de R a los núcleos U del mismo municipio que tienen margen bajo el límite.
REGLAS DURAS: solo movimientos R→U del mismo municipio; núcleo receptor dentro de
[target−tol, target+tol]; R, distrito origen y distrito destino siguen conexos; R conserva
una pasarela fuera del municipio; no se mueven nodos protegidos (puentes y pasarelas).
MOTIVO: M05 opera sobre unidades enteras; si M04 dimensiona R sin contar los enclaves que
deben ir con él (Murcia: Alcantarilla y Beniel), el distrito queda sobre el techo y ningún
movimiento de M05 puede repararlo (T-22).
ANTERIOR: legacy/ddd_core/m04_overcap_residual_relief_v1.0.0.py
CAMBIO 1.1.0: fase 2 en dos saltos; si ningún municipio del distrito linda con un residual, pasa uno a un
distrito vecino sin residual y desde allí traslada otro al residual (T-44, Málaga: Benalmádena y Torremolinos).
"""
from __future__ import annotations


def _connected(nodes, adj):
    nodes = set(nodes)
    if not nodes:
        return False
    seen = {next(iter(nodes))}
    stack = list(seen)
    while stack:
        u = stack.pop()
        for v in adj.get(u, ()):
            if v in nodes and v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == len(nodes)


def relieve_overcap_residuals(
    g,
    *,
    pop,
    adj,
    cap,
    core_low,
    core_high,
    id_field,
    municipality_field,
    district_field="district_id",
    unit_field="ddd_unit_id",
    closed_field="ddd_closed_urban",
    protected=(),
    max_moves=5000,
    max_room_steps=20,
):
    """Modifica ``g`` in situ y devuelve la lista de movimientos aplicados.

    Fase 1: el distrito sobre el techo contiene un residuo R; cede secciones de R a núcleos U.
    Fase 2: el distrito no tiene R que ceder; traslada una unidad municipal completa al distrito
    de un residuo R vecino de otro municipio dividido (su único distrito mixto) y cede el
    exceso de ese R a sus núcleos U. Se deshace si el receptor no queda bajo el techo.
    """
    protected = {str(x) for x in protected}
    ids = g[id_field].astype(str)
    node_unit = dict(zip(ids, g[unit_field].astype(str)))
    node_dist = dict(zip(ids, g[district_field].astype(int)))
    node_mun = dict(zip(ids, g[municipality_field].astype(str)))
    mun_nodes = {}
    unit_nodes, dist_nodes = {}, {}
    for n in node_unit:
        mun_nodes.setdefault(node_mun[n], set()).add(n)
        unit_nodes.setdefault(node_unit[n], set()).add(n)
        dist_nodes.setdefault(node_dist[n], set()).add(n)
    moved_to_core = set()

    def upop(nodes):
        return sum(pop[n] for n in nodes)

    def snapshot():
        return ({k: set(v) for k, v in unit_nodes.items()}, {k: set(v) for k, v in dist_nodes.items()},
                dict(node_unit), dict(node_dist), set(moved_to_core))

    def restore(state):
        for target, saved in zip((unit_nodes, dist_nodes, node_unit, node_dist, moved_to_core), state):
            target.clear()
            target.update(saved)

    def cede_step(d):
        excess = upop(dist_nodes[d]) - cap
        best = None
        for rid in sorted({node_unit[n] for n in dist_nodes[d] if node_unit[n].endswith(":R")}):
            rnodes = unit_nodes[rid]
            mun = node_mun[next(iter(rnodes))]
            for n in sorted(rnodes - protected):
                targets = {
                    node_unit[v] for v in adj.get(n, ())
                    if v in node_unit and ":U" in node_unit[v] and node_mun[v] == mun and node_dist[v] != d
                }
                for cid in sorted(targets):
                    cd = node_dist[next(iter(unit_nodes[cid]))]
                    if not (core_low <= upop(unit_nodes[cid]) + pop[n] <= core_high):
                        continue
                    new_r = rnodes - {n}
                    if not new_r or not _connected(new_r, adj):
                        continue
                    if not any(v not in mun_nodes[mun] for m in new_r for v in adj.get(m, ())):
                        continue
                    if not _connected(dist_nodes[d] - {n}, adj) or not _connected(dist_nodes[cd] | {n}, adj):
                        continue
                    fits = pop[n] <= excess
                    score = (0 if fits else 1, -pop[n] if fits else pop[n], n, cid)
                    if best is None or score < best[0]:
                        best = (score, n, rid, cid, d, cd)
        if best is None:
            return None
        _, n, rid, cid, d, cd = best
        unit_nodes[rid].discard(n)
        unit_nodes[cid].add(n)
        dist_nodes[d].discard(n)
        dist_nodes[cd].add(n)
        node_unit[n], node_dist[n] = cid, cd
        moved_to_core.add(n)
        return {"kind": "residual_to_core", "section": n, "population": int(pop[n]), "from_unit": rid,
                "to_unit": cid, "from_district": int(d), "to_district": int(cd)}

    def make_room(d):
        """Traspasa una sección de un núcleo lleno vecino de R a otro núcleo con margen."""
        best = None
        residual_nodes = {n for n in dist_nodes[d] if node_unit[n].endswith(":R")}
        full = sorted({node_unit[v] for n in residual_nodes for v in adj.get(n, ())
                       if v in node_unit and ":U" in node_unit[v] and node_dist[v] != d
                       and node_mun[v] == node_mun[n]})
        for cid in full:
            cnodes = unit_nodes[cid]
            cd = node_dist[next(iter(cnodes))]
            room_needed = upop(cnodes) - core_low
            for n in sorted(cnodes - protected):
                if pop[n] > room_needed:
                    continue
                for cid2 in sorted({node_unit[v] for v in adj.get(n, ())
                                    if v in node_unit and ":U" in node_unit[v] and node_unit[v] != cid
                                    and node_mun[v] == node_mun[n] and node_dist[v] not in (d, cd)}):
                    c2nodes = unit_nodes[cid2]
                    cd2 = node_dist[next(iter(c2nodes))]
                    slack = core_high - upop(c2nodes) - pop[n]
                    if slack < 0:
                        continue
                    if not _connected(cnodes - {n}, adj) or not _connected(c2nodes | {n}, adj):
                        continue
                    if not _connected(dist_nodes[cd] - {n}, adj) or not _connected(dist_nodes[cd2] | {n}, adj):
                        continue
                    score = (-pop[n], n, cid2)
                    if best is None or score < best[0]:
                        best = (score, n, cid, cid2, cd, cd2)
        if best is None:
            return None
        _, n, cid, cid2, cd, cd2 = best
        unit_nodes[cid].discard(n)
        unit_nodes[cid2].add(n)
        dist_nodes[cd].discard(n)
        dist_nodes[cd2].add(n)
        node_unit[n], node_dist[n] = cid2, cd2
        moved_to_core.add(n)
        return {"kind": "core_to_core", "section": n, "population": int(pop[n]), "from_unit": cid,
                "to_unit": cid2, "from_district": int(cd), "to_district": int(cd2)}

    def cede_until_cap(d, budget):
        steps, idle = [], 0
        while upop(dist_nodes[d]) > cap and len(steps) < budget and idle <= max_room_steps:
            step = cede_step(d)
            if step is None:
                step = make_room(d)
                if step is None:
                    break
                idle += 1
            else:
                idle = 0
            steps.append(step)
        return steps

    def movable_units(d):
        """Unidades municipales completas que pueden salir de ``d`` dejándolo conexo."""
        for uid in sorted({node_unit[n] for n in dist_nodes[d]}):
            unodes = unit_nodes[uid]
            if uid.endswith(":R") or ":U" in uid or unodes & protected:
                continue
            if unodes != mun_nodes[node_mun[next(iter(unodes))]]:
                continue
            rest = dist_nodes[d] - unodes
            if rest and _connected(rest, adj):
                yield uid, unodes

    def relocation_candidates(d):
        result = []
        dpop = upop(dist_nodes[d])
        for uid, unodes in movable_units(d):
            if dpop - upop(unodes) > cap:
                continue
            receivers = {node_dist[v] for m in unodes for v in adj.get(m, ())
                         if v in node_unit and node_unit[v].endswith(":R") and node_dist[v] != d}
            for rd in sorted(receivers):
                if not _connected(dist_nodes[rd] | unodes, adj):
                    continue
                need = upop(dist_nodes[rd]) + upop(unodes) - cap
                result.append((need, abs(dpop - upop(unodes) - (core_low + core_high) / 2), uid, rd))
        return sorted(result)

    def move_unit(uid, src, dst):
        unodes = set(unit_nodes[uid])
        dist_nodes[src] -= unodes
        dist_nodes[dst] |= unodes
        for n in unodes:
            node_dist[n] = dst
        return {"kind": "unit_to_residual_district", "unit": uid, "population": int(upop(unodes)),
                "from_district": int(src), "to_district": int(dst)}

    def relocate(d, budget):
        """Fase 2: unidad completa de ``d`` al distrito de un residual vecino."""
        for _need, _dev, uid, rd in relocation_candidates(d):
            state = snapshot()
            move = move_unit(uid, d, rd)
            steps = cede_until_cap(rd, budget - 1)
            if upop(dist_nodes[rd]) <= cap:
                return [move] + steps
            restore(state)
        return []

    def relocate_chain(d, budget):
        """Fase 2 en dos saltos: X de ``d`` a un distrito vecino d2 sin residual, e Y de d2 a un residual."""
        dpop = upop(dist_nodes[d])
        for uid, unodes in list(movable_units(d)):
            if dpop - upop(unodes) > cap:
                continue
            neighbours = sorted({node_dist[v] for m in unodes for v in adj.get(m, ())
                                 if v in node_dist and node_dist[v] != d})
            for d2 in neighbours:
                if any(node_unit[n].endswith(":R") for n in dist_nodes[d2]):
                    continue
                state = snapshot()
                first = move_unit(uid, d, d2)
                first["kind"] = "unit_to_neighbour_district"
                for _need, _dev, uid2, rd in relocation_candidates(d2):
                    if uid2 == uid:
                        continue
                    inner = snapshot()
                    second = move_unit(uid2, d2, rd)
                    steps = cede_until_cap(rd, budget - 2)
                    if upop(dist_nodes[rd]) <= cap and upop(dist_nodes[d2]) <= cap:
                        return [first, second] + steps
                    restore(inner)
                restore(state)
        return []

    moves = []
    while len(moves) < max_moves:
        over = sorted((d for d in dist_nodes if upop(dist_nodes[d]) > cap),
                      key=lambda d: upop(dist_nodes[d]), reverse=True)
        progressed = False
        for d in over:
            budget = max_moves - len(moves)
            steps = (cede_until_cap(d, budget) or relocate(d, budget) or relocate_chain(d, budget))
            if steps:
                moves.extend(steps)
                progressed = True
                break
        if not progressed:
            break

    if moves:
        g[unit_field] = ids.map(node_unit)
        g[district_field] = ids.map(node_dist).astype(int)
        moved = ids.isin(moved_to_core)
        g.loc[moved, closed_field] = True
    return moves
