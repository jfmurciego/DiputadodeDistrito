#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 05 — Optimizar distritos
VERSIÓN: 7.3.0
NOMBRE DE VERSIÓN: Escape determinista de mínimos locales
FECHA: 2026-09-11
ESTADO: candidato
FUNCIÓN: optimizar población sin cruzar provincias ni romper las unidades municipales/urbanas construidas por M04.
ENTRADAS: grafo M03 y solución M04 v7.3.0 con ddd_unit_id y ddd_closed_urban.
SALIDAS: asignación optimizada y reporte.
REGLAS DURAS: provincia única por distrito; movimientos de unidad completa; distritos urbanos cerrados no reciben ni ceden unidades; contigüidad estricta; suelo/techo poblacional.
OBJETIVO CANÓNICO: primero eliminar violaciones duras; después minimizar distritos fuera de ±12%; después máximo desvío y error cuadrático.
CAMBIOS VS 7.2.0: añade una fase greedy determinista de mejor movimiento y, si queda bloqueo, un recocido simulado reproducible limitado a las provincias con desequilibrio. El recocido puede atravesar estados intermedios peores en ±12%, pero nunca viola reglas duras; la salida siempre restaura la mejor solución encontrada según el objetivo canónico. Añade penalización de churn para evitar movimientos territoriales innecesarios.
MOTIVO: Run #7 dejó el distrito 56 en 31.563 habitantes y M05 aceptó 0 movimientos. La auditoría demostró que los únicos movimientos directos territorialmente válidos crean temporalmente un segundo distrito fuera de ±12%, por lo que el greedy lexicográfico queda atrapado en un mínimo local.
ANTERIOR: legacy/modulo05/05_optimizar_distritos_v7.2.0.py
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import random
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ddd_core.config import load_params_yaml, module_cfg, require


def load_geo(path):
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            m = next(
                n
                for n in z.namelist()
                if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")
            )
            return gpd.read_file(io.BytesIO(z.read(m)))
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
    seen = {next(iter(nodes))}
    q = collections.deque(seen)
    while q:
        u = q.popleft()
        for v in adj.get(u, set()):
            if v in nodes and v not in seen:
                seen.add(v)
                q.append(v)
    return len(seen) == len(nodes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--params", required=True)
    a = ap.parse_args()

    cfg = load_params_yaml(a.params)
    s5 = module_cfg(cfg, "modulo_05_optimizar_distritos", "step5_optimize_swaps")
    val = cfg.get("validation", {}) or {}

    ing = require(s5.get("in_graph_json"), "Falta M05 grafo")
    ingeo = require(s5.get("in_geojson"), "Falta M05 geojson")
    idf = require(s5.get("id_field"), "Falta id")
    popf = require(s5.get("pop_field"), "Falta población")
    did = s5.get("district_field", "district_id")
    provf = s5.get("province_field", "CPRO")
    out = require(s5.get("out_geojson"), "Falta salida")
    report_path = s5.get("out_report", "")

    greedy_moves_limit = int(s5.get("greedy_moves_limit", 1000))
    anneal_iters = int(s5.get("anneal_iters", s5.get("iters", 20000)))
    seed = int(s5.get("seed", 12345))
    anneal_seed_offset = int(s5.get("anneal_seed_offset", 0))
    outside_penalty = float(s5.get("anneal_outside_penalty", 0.01))
    maxdev_weight = float(s5.get("anneal_maxdev_weight", 0.05))
    churn_weight = float(s5.get("anneal_churn_weight", 0.0016))
    temp_start = float(s5.get("anneal_temp_start", 0.02))
    temp_end = float(s5.get("anneal_temp_end", 0.0005))
    if anneal_iters < 0 or greedy_moves_limit < 0:
        raise SystemExit("M05: iteraciones/límite de movimientos no pueden ser negativos")
    if temp_start <= 0 or temp_end <= 0:
        raise SystemExit("M05: temperaturas de recocido deben ser positivas")

    G = json.loads(Path(ing).read_text(encoding="utf-8"))
    pop = {str(n["id"]): int(n.get("pop", 0)) for n in G["nodes"]}
    adj = {n: set() for n in pop}
    for e in G["edges"]:
        u, v = str(e["u"]), str(e["v"])
        if u in adj and v in adj:
            adj[u].add(v)
            adj[v].add(u)

    g = load_geo(ingeo)
    g[idf] = g[idf].astype(str)
    for c in (did, provf, "ddd_unit_id", "ddd_closed_urban"):
        if c not in g.columns:
            raise SystemExit(f"M05 requiere {c}; ejecutar M04 v7.3.0")
    g[provf] = g[provf].astype(str).str.zfill(2)
    g[did] = pd.to_numeric(g[did], errors="raise").astype(int)
    g["ddd_unit_id"] = g["ddd_unit_id"].astype(str)

    section_to_unit = dict(zip(g[idf], g["ddd_unit_id"]))
    unit_nodes = {u: set(x[idf].astype(str)) for u, x in g.groupby("ddd_unit_id")}
    unit_pop = {u: sum(pop.get(n, 0) for n in ns) for u, ns in unit_nodes.items()}
    unit_prov = {
        u: str(x[provf].iloc[0]).zfill(2) for u, x in g.groupby("ddd_unit_id")
    }
    unit_dist = {u: int(x[did].iloc[0]) for u, x in g.groupby("ddd_unit_id")}
    if any(x[did].nunique() != 1 for _, x in g.groupby("ddd_unit_id")):
        raise SystemExit("M05: una unidad territorial llega partida entre distritos")

    K = int(g[did].nunique())
    total = sum(pop.values())
    target = total / K
    floor = target * float(val.get("population_floor_ratio", 0.8))
    cap = target * float(val.get("population_cap_ratio", 1.75))
    tol = target * float(val.get("target_tolerance_ratio", 0.12))

    d_units = {d: set() for d in sorted(g[did].unique())}
    d_nodes = {d: set() for d in d_units}
    d_pop = {d: 0 for d in d_units}
    d_prov = {}
    d_closed = {}
    for u, d in unit_dist.items():
        d_units[d].add(u)
        d_nodes[d] |= unit_nodes[u]
        d_pop[d] += unit_pop[u]
        d_prov.setdefault(d, unit_prov[u])
    for d, x in g.groupby(did):
        ps = set(x[provf].astype(str).str.zfill(2))
        if len(ps) != 1:
            raise SystemExit(f"M05 entrada inválida: distrito {d} cruza provincias {sorted(ps)}")
        d_closed[int(d)] = bool(x["ddd_closed_urban"].all())

    # Adyacencia entre unidades, derivada exclusivamente del grafo M03.
    uadj = {u: set() for u in unit_nodes}
    for n in pop:
        u = section_to_unit.get(n)
        if u is None:
            continue
        for nb in adj.get(n, set()):
            v = section_to_unit.get(nb)
            if v is not None and v != u:
                uadj[u].add(v)
    uadj_list = {u: sorted(vs) for u, vs in uadj.items()}

    def obj(values):
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

    def unique_candidates():
        result = set()
        for u, d0 in unit_dist.items():
            if d_closed[d0]:
                continue
            for v in uadj[u]:
                d1 = unit_dist[v]
                if d1 == d0 or d_closed[d1] or d_prov[d1] != unit_prov[u]:
                    continue
                result.add((u, d0, d1))
        return sorted(result, key=lambda x: (str(x[0]), x[1], x[2]))

    baseline_unit_dist = dict(unit_dist)
    start = obj(d_pop)
    initial_candidate_relations = len(unique_candidates())

    # Fase A: mejor movimiento individual, determinista y estrictamente monótono.
    greedy_accepted = 0
    for _ in range(greedy_moves_limit):
        cur = obj(d_pop)
        best = None
        for u, d0, d1 in unique_candidates():
            if len(d_units[d0]) <= 1:
                continue
            new0 = d_pop[d0] - unit_pop[u]
            new1 = d_pop[d1] + unit_pop[u]
            if new0 < floor or new0 > cap or new1 < floor or new1 > cap:
                continue
            remaining = d_nodes[d0] - unit_nodes[u]
            newrecv = d_nodes[d1] | unit_nodes[u]
            if not connected(remaining, adj) or not connected(newrecv, adj):
                continue
            trial = dict(d_pop)
            trial[d0] = new0
            trial[d1] = new1
            trial_obj = obj(trial)
            if trial_obj >= cur:
                continue
            candidate = (trial_obj, str(u), d0, d1, u, remaining, newrecv, trial)
            if best is None or candidate[:4] < best[:4]:
                best = candidate
        if best is None:
            break
        _, _, d0, d1, u, remaining, newrecv, trial = best
        d_units[d0].remove(u)
        d_units[d1].add(u)
        d_nodes[d0] = remaining
        d_nodes[d1] = newrecv
        d_pop = trial
        unit_dist[u] = d1
        greedy_accepted += 1
        if obj(d_pop)[0] == 0 and obj(d_pop)[2] == 0:
            break

    greedy_final = obj(d_pop)

    # Fase B: escape determinista del mínimo local.
    # Se limita a las provincias que todavía contienen distritos fuera de ±12%.
    active_provinces = sorted(
        {d_prov[d] for d, p in d_pop.items() if abs(p - target) > tol}
    )
    active_province_set = set(active_provinces)
    active_districts = sorted(d for d in d_pop if d_prov[d] in active_province_set)
    active_units = sorted(u for u in unit_nodes if unit_prov[u] in active_province_set)

    best_obj = obj(d_pop)
    best_unit_dist = dict(unit_dist)
    best_d_units = {d: set(us) for d, us in d_units.items()}
    best_d_nodes = {d: set(ns) for d, ns in d_nodes.items()}
    best_d_pop = dict(d_pop)

    def changed_active_count(assignments):
        return sum(assignments[u] != baseline_unit_dist[u] for u in active_units)

    def search_energy(values, changed_count):
        if not active_districts:
            return 0.0
        vals = [values[d] for d in active_districts]
        outside = sum(abs(p - target) > tol for p in vals)
        maxdev = max(abs(p - target) / target for p in vals)
        sq = sum(((p - target) / target) ** 2 for p in vals)
        return (
            sq
            + outside_penalty * outside
            + maxdev_weight * maxdev
            + churn_weight * changed_count
        )

    anneal_accepted = 0
    anneal_iterations_executed = 0
    anneal_start_obj = obj(d_pop)
    anneal_start_energy = None
    anneal_best_energy = None

    if active_units and anneal_iters > 0 and best_obj[2] > 0:
        rng = random.Random(seed + anneal_seed_offset)
        changed_count = changed_active_count(unit_dist)
        energy = search_energy(d_pop, changed_count)
        anneal_start_energy = energy
        anneal_best_energy = energy

        for i in range(anneal_iters):
            anneal_iterations_executed = i + 1
            u = rng.choice(active_units)
            d0 = unit_dist[u]
            if d_closed[d0] or len(d_units[d0]) <= 1:
                continue
            neigh_units = uadj_list.get(u, [])
            if not neigh_units:
                continue
            v = rng.choice(neigh_units)
            d1 = unit_dist[v]
            if (
                d1 == d0
                or d_closed[d1]
                or d_prov[d1] != unit_prov[u]
                or d_prov[d0] not in active_province_set
            ):
                continue

            new0 = d_pop[d0] - unit_pop[u]
            new1 = d_pop[d1] + unit_pop[u]
            if new0 < floor or new0 > cap or new1 < floor or new1 > cap:
                continue

            remaining = d_nodes[d0] - unit_nodes[u]
            newrecv = d_nodes[d1] | unit_nodes[u]
            if not connected(remaining, adj) or not connected(newrecv, adj):
                continue

            trial = dict(d_pop)
            trial[d0] = new0
            trial[d1] = new1
            was_changed = unit_dist[u] != baseline_unit_dist[u]
            will_be_changed = d1 != baseline_unit_dist[u]
            trial_changed_count = changed_count - int(was_changed) + int(will_be_changed)
            trial_energy = search_energy(trial, trial_changed_count)
            delta = trial_energy - energy
            frac = i / max(1, anneal_iters - 1)
            temp = temp_start * ((temp_end / temp_start) ** frac)
            accept = delta <= 0 or rng.random() < math.exp(-delta / max(temp, 1e-12))
            if not accept:
                continue

            d_units[d0].remove(u)
            d_units[d1].add(u)
            d_nodes[d0] = remaining
            d_nodes[d1] = newrecv
            d_pop = trial
            unit_dist[u] = d1
            changed_count = trial_changed_count
            energy = trial_energy
            anneal_accepted += 1
            anneal_best_energy = min(anneal_best_energy, energy)

            current_obj = obj(d_pop)
            if current_obj < best_obj:
                best_obj = current_obj
                best_unit_dist = dict(unit_dist)
                best_d_units = {d: set(us) for d, us in d_units.items()}
                best_d_nodes = {d: set(ns) for d, ns in d_nodes.items()}
                best_d_pop = dict(d_pop)
                if best_obj[0] == 0 and best_obj[2] == 0:
                    break

        # La exploración puede terminar en un estado peor. Se restaura siempre
        # la mejor solución según la función canónica, no el último estado SA.
        unit_dist = best_unit_dist
        d_units = best_d_units
        d_nodes = best_d_nodes
        d_pop = best_d_pop

    # Reconstrucción sección->distrito y guardas duras finales.
    sec_assign = {n: unit_dist[u] for u, ns in unit_nodes.items() for n in ns}
    g[did] = g[idf].map(sec_assign).astype(int)
    province_viol = []
    for d, x in g.groupby(did):
        ps = sorted(set(x[provf].astype(str).str.zfill(2)))
        if len(ps) != 1:
            province_viol.append({"district_id": int(d), "provinces": ps})
        if not connected(set(x[idf].astype(str)), adj):
            raise SystemExit(f"M05 produjo distrito desconectado {d}")
    if province_viol:
        raise SystemExit(f"M05 produjo cruces provinciales: {province_viol}")

    final = obj(d_pop)
    if final[0] != 0:
        raise SystemExit(f"M05 terminó con violaciones duras de población: {final}")

    write_geo(g, out)
    final_changed_units = sum(unit_dist[u] != baseline_unit_dist[u] for u in unit_dist)
    rep = {
        "module": "05",
        "version": "7.3.0",
        "K": K,
        "total_pop": int(total),
        "target": target,
        "population_floor": floor,
        "population_cap": cap,
        "tolerance_absolute": tol,
        "objective_start": list(start),
        "objective_after_greedy": list(greedy_final),
        "objective_final": list(final),
        "districts_below_floor": sum(p < floor for p in d_pop.values()),
        "districts_above_cap": sum(p > cap for p in d_pop.values()),
        "districts_outside_tolerance": sum(abs(p - target) > tol for p in d_pop.values()),
        "best_max_rel_dev": final[3],
        "accepted_unit_moves": greedy_accepted + anneal_accepted,
        "accepted_greedy_moves": greedy_accepted,
        "accepted_annealing_moves": anneal_accepted,
        "final_changed_units": final_changed_units,
        "atomic_units": len(unit_nodes),
        "initial_candidate_relations": initial_candidate_relations,
        "active_provinces": active_provinces,
        "anneal_iterations_executed": anneal_iterations_executed,
        "anneal_start_objective": list(anneal_start_obj),
        "anneal_start_energy": anneal_start_energy,
        "anneal_best_energy": anneal_best_energy,
        "anneal_parameters": {
            "outside_penalty": outside_penalty,
            "maxdev_weight": maxdev_weight,
            "churn_weight": churn_weight,
            "temp_start": temp_start,
            "temp_end": temp_end,
            "seed": seed + anneal_seed_offset,
            "iters": anneal_iters,
        },
        "province_violations": province_viol,
        "seed": seed,
    }
    if report_path:
        Path(report_path).write_text(
            json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(
        f"[Módulo 5] OK v7.3.0 hard={final[0]} fuera_12={final[2]} "
        f"max_rel_dev={final[3]:.4f} greedy={greedy_accepted} "
        f"anneal={anneal_accepted} changed_units={final_changed_units} out={out}"
    )


if __name__ == "__main__":
    main()
