#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
Módulo 04 — Generar distritos iniciales
VERSIÓN: 7.4.13
NOMBRE DE VERSIÓN: Fallback determinista multistart de crecimiento directo
FECHA: 2026-09-15
FUNCIÓN: conservar íntegramente el motor M04 v7.4.10 y añadir una segunda construcción determinista únicamente cuando el rebalanceo primario deja violaciones duras de suelo/techo.
ENTRADAS: idénticas a v7.4.10.
SALIDAS: idénticas a v7.4.10, añadiendo trazabilidad de los fallbacks activados en el informe M04.
ESTADO: candidato de reparación topológica Aragón tras exigir frontera compartida mínima de 1 metro.
CAMBIOS: si hybrid_partition + rebalance conserva hard>0, reconstruye las mismas unidades conexas mediante grow_partition, vuelve a ejecutar el mismo rebalanceo y acepta la alternativa solo si mejora lexicográficamente la función objetivo. Si la ruta primaria ya cumple hard=0, no cambia nada.
MOTIVO: con el grafo Aragón depurado a 4.063 aristas, v7.4.10 deja un distrito de Teruel en 13.154 habitantes; sobre exactamente el mismo grafo y las mismas unidades, grow_partition + rebalance obtiene hard=0 y fuera_12=0 sin relajar ninguna restricción.
ANTERIOR: ddd_core/m04_seed_engine_v745.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ddd_core import m04_seed_engine_v7410 as previous
from ddd_core.config import load_params_yaml, module_cfg, require

ENGINE_VERSION = "7.4.13"

# API usada por el motor canónico ddd_core/m04_seed_engine.py.
load_geo = previous.load_geo
partition_oversized_municipality = previous.partition_oversized_municipality

_ORIGINAL_REBALANCE = previous.rebalance
_FALLBACK_EVENTS = []


def _grow_partition_from_seed(nodes, k, adj, w, first_seed):
    """Replica grow_partition con semilla inicial explícita y orden determinista."""
    import collections

    nodes = set(nodes)
    if k == 1:
        return [nodes]
    if first_seed not in nodes:
        raise ValueError("first_seed debe pertenecer a nodes")

    seeds = [first_seed]
    dist = {node: 10**9 for node in nodes}

    def update(seed):
        queue = collections.deque([(seed, 0)])
        seen = {seed}
        while queue:
            node, depth = queue.popleft()
            if depth < dist[node]:
                dist[node] = depth
            for neighbor in adj.get(node, set()):
                if neighbor in nodes and neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, depth + 1))

    update(first_seed)
    while len(seeds) < k:
        seed = max(
            nodes - set(seeds),
            key=lambda node: (dist[node], w[node], str(node)),
        )
        seeds.append(seed)
        update(seed)

    owner = {seed: index for index, seed in enumerate(seeds)}
    parts = [{seed} for seed in seeds]
    populations = [w[seed] for seed in seeds]
    unassigned = nodes - set(seeds)
    local_target = sum(w[node] for node in nodes) / k

    while unassigned:
        best = None
        for node in sorted(unassigned, key=str):
            candidate_parts = sorted({
                owner[neighbor]
                for neighbor in adj.get(node, set())
                if neighbor in owner
            })
            for part_index in candidate_parts:
                score = (
                    populations[part_index] / local_target,
                    abs(populations[part_index] + w[node] - local_target),
                    part_index,
                    str(node),
                )
                candidate = (score, node, part_index)
                if best is None or candidate < best:
                    best = candidate
        if best is None:
            raise SystemExit("M04: crecimiento conexo multistart bloqueado")
        _, node, part_index = best
        owner[node] = part_index
        parts[part_index].add(node)
        populations[part_index] += w[node]
        unassigned.remove(node)
    return parts


def _multistart_candidates(nodes, adj, w, limit=32):
    nodes = set(nodes)
    rankings = (
        sorted(nodes, key=lambda node: (w[node], str(node))),
        sorted(nodes, key=lambda node: (-w[node], str(node))),
        sorted(nodes, key=lambda node: (len(adj.get(node, set())), w[node], str(node))),
        sorted(nodes, key=lambda node: (-len(adj.get(node, set())), -w[node], str(node))),
        sorted(nodes, key=str),
    )
    candidates = []
    per_ranking = max(1, limit // len(rankings))
    for ranking in rankings:
        for node in ranking[:per_ranking]:
            if node not in candidates:
                candidates.append(node)
                if len(candidates) >= limit:
                    return candidates
    return candidates


def rebalance_with_direct_growth_fallback(parts, adj, w, target, floor, cap, tol, iters=30000):
    """Mantiene v7.4.10 y reintenta solo cuando queda una violación dura.

    El fallback no abre unidades, no cruza provincias y no modifica las reglas de
    contigüidad. Trabaja exactamente sobre el mismo conjunto de nodos/unidades y
    el mismo número de partes. La alternativa solo sustituye a la primaria si su
    tupla objetivo es estrictamente mejor.
    """
    primary_parts, primary_pops, primary_obj = _ORIGINAL_REBALANCE(
        parts, adj, w, target, floor, cap, tol, iters
    )
    if not primary_parts or not primary_obj or primary_obj[0] == 0:
        return primary_parts, primary_pops, primary_obj

    nodes = set().union(*primary_parts)
    best_parts = primary_parts
    best_pops = primary_pops
    best_obj = primary_obj
    attempts = []

    # Conserva primero exactamente el fallback histórico.
    seeds = [max(nodes, key=lambda node: (w[node], str(node)))]
    seeds.extend(
        node for node in _multistart_candidates(nodes, adj, w)
        if node not in seeds
    )

    for seed in seeds:
        alternate_seed = _grow_partition_from_seed(
            nodes, len(primary_parts), adj, w, seed
        )
        alternate_parts, alternate_pops, alternate_obj = _ORIGINAL_REBALANCE(
            alternate_seed, adj, w, target, floor, cap, tol, iters
        )
        attempts.append({
            "seed": str(seed),
            "objective": list(alternate_obj),
            "populations": [int(x) for x in alternate_pops],
        })
        if alternate_obj < best_obj:
            best_parts, best_pops, best_obj = (
                alternate_parts,
                alternate_pops,
                alternate_obj,
            )
        if best_obj[0] == 0:
            break

    event = {
        "nodes": len(nodes),
        "k": len(primary_parts),
        "primary_objective": list(primary_obj),
        "alternate_objective": list(best_obj),
        "accepted": bool(best_obj < primary_obj),
        "primary_populations": [int(x) for x in primary_pops],
        "alternate_populations": [int(x) for x in best_pops],
        "multistart_attempts": attempts,
    }
    _FALLBACK_EVENTS.append(event)

    if best_obj < primary_obj:
        return best_parts, best_pops, best_obj
    return primary_parts, primary_pops, primary_obj


def _annotate_report(params_path: str) -> None:
    cfg = load_params_yaml(params_path)
    step = module_cfg(cfg, "modulo_04_generar_semillas", "step4_seed_districts")
    report_path = step.get("out_report", "")
    if not report_path:
        return
    path = Path(require(report_path, "Falta informe M04"))
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    report["version"] = ENGINE_VERSION
    report["hard_repair_strategy"] = "deterministic_multistart_direct_growth_only_after_primary_hard_violation"
    report["hard_repair_fallbacks"] = list(_FALLBACK_EVENTS)
    report.setdefault("rules", {})["direct_growth_fallback_preserves_same_units_and_k"] = True
    report["rules"]["direct_growth_multistart_is_bounded_and_deterministic"] = True
    report["rules"]["direct_growth_fallback_is_used_only_if_objective_improves"] = True
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--params", required=True)
    args, _ = parser.parse_known_args()

    _FALLBACK_EVENTS.clear()
    original_rebalance = previous.rebalance
    original_partition = previous.partition_oversized_municipality
    previous.rebalance = rebalance_with_direct_growth_fallback
    # Permite que la política de puertas del wrapper canónico siga parcheando
    # partition_oversized_municipality sobre esta versión sin perder el cambio.
    previous.partition_oversized_municipality = partition_oversized_municipality
    try:
        previous.main()
    finally:
        previous.rebalance = original_rebalance
        previous.partition_oversized_municipality = original_partition

    _annotate_report(args.params)
    accepted = sum(1 for item in _FALLBACK_EVENTS if item["accepted"])
    print(
        f"[Módulo 4] motor base {ENGINE_VERSION} "
        f"fallbacks={len(_FALLBACK_EVENTS)} accepted={accepted}"
    )


if __name__ == "__main__":
    main()
