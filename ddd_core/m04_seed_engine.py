#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor M04 canónico.

PROYECTO: Diputado de Distrito
Módulo 04 — Motor canónico de semillas
VERSIÓN: 7.6.3
NOMBRE DE VERSIÓN: Preflight atómico y puertas dependientes por defecto
FECHA: 2026-10-05
FUNCIÓN: ejecutar el núcleo 7.4.13 con preflight atómico fail-closed y política declarativa de puertas de componentes.
CAMBIOS: añade condiciones necesarias y exact-cover conexo acotado para incompatibilidades pequeñas; usa preserve_dependent_component_gateways como default común; conserva puertas protegidas en postproceso y restaura el monkey-patch al terminar cada ejecución.
MOTIVO: distinguir incompatibilidad matemática de fallo heurístico y evitar que el cierre de núcleos urbanos aisle componentes provinciales dependientes sin alterar K, provincia, contigüidad ni cuotas.
ANTERIOR: legacy/ddd_core/m04_seed_engine_v7.6.2.py
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from ddd_core import m04_seed_engine_v7412 as core
from ddd_core import m04_seed_engine_v7411 as postprocess_engine
from ddd_core.config import hard_limits, load_params_yaml, module_cfg, require

ENGINE_ID = "ddd_core.m04_seed_engine"
ENGINE_VERSION = "7.6.3"
partition_oversized_municipality = core.partition_oversized_municipality


def _components(nodes, adj):
    unseen = set(nodes)
    result = []
    while unseen:
        seed = next(iter(unseen))
        unseen.remove(seed)
        seen = {seed}
        stack = [seed]
        while stack:
            node = stack.pop()
            for neighbor in adj.get(node, set()):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    seen.add(neighbor)
                    stack.append(neighbor)
        result.append(seen)
    return result


def _protected_component_gateways(
    nodes, province_nodes, adjacency, *, dependent_only=False
):
    """Puertas mínimas para no fabricar componentes provinciales aislados.

    El modo explícito preserve_component_gateways conserva una puerta por cada
    componente exterior. El modo estructural por defecto sólo fuerza esas
    puertas cuando retirar el municipio divide el exterior en más de una
    componente. Si el exterior sigue siendo conexo, el motor base ya obliga a
    que el residuo conserve alguna salida territorial y no se fija una puerta
    concreta innecesariamente.
    """
    nodes = set(nodes)
    outside = set(province_nodes) - nodes
    exterior_components = _components(outside, adjacency)
    if dependent_only and len(exterior_components) <= 1:
        return set()
    keep = set()
    for component in exterior_components:
        candidates = {
            node for node in nodes
            if any(neighbor in component for neighbor in adjacency.get(node, set()))
        }
        if candidates:
            keep.add(min(
                candidates,
                key=lambda node: (
                    -sum(
                        1 for neighbor in adjacency.get(node, set())
                        if neighbor in component
                    ),
                    str(node),
                ),
            ))
    return keep


def _atomic_population_necessary_conditions(
    nodes,
    weights,
    *,
    k,
    floor,
    cap,
):
    """Necessary hard-population conditions under a relaxed atomic model.

    The check deliberately ignores contiguity and municipality discipline. It
    therefore proves incompatibility only when even the more permissive model
    cannot form k non-empty districts from the atomic sections.
    """
    nodes = set(nodes)
    n = len(nodes)
    k = int(k)
    total = sum(weights[node] for node in nodes)
    detail = {
        "nodes": n,
        "k": k,
        "population": int(total),
        "required_singletons": max(0, 2 * k - n),
        "hard_valid_singletons": sum(
            1 for node in nodes if floor <= weights[node] <= cap
        ),
    }
    if k > n:
        return False, "K_EXCEEDS_ATOMIC_UNITS", detail
    if total < k * floor - 1e-9 or total > k * cap + 1e-9:
        return False, "PROVINCE_POPULATION_OUTSIDE_K_HARD_RANGE", detail
    if detail["hard_valid_singletons"] < detail["required_singletons"]:
        return False, "INSUFFICIENT_HARD_VALID_SINGLETONS", detail
    return True, "NECESSARY_CONDITIONS_PASS", detail


def _enumerate_connected_hard_groups(
    nodes,
    adjacency,
    weights,
    *,
    floor,
    cap,
    max_seen=100000,
):
    """Enumera subconjuntos conexos poblacionalmente admisibles en grafos pequeños.

    La enumeración sólo se usa como preflight diagnóstico. Si el espacio supera
    el límite, devuelve UNKNOWN en vez de inferir imposibilidad.
    """
    nodes = set(nodes)
    seen = {frozenset((node,)) for node in nodes}
    frontier = list(seen)
    groups = []
    while frontier:
        group = frontier.pop()
        population = sum(weights[node] for node in group)
        if floor <= population <= cap:
            groups.append(group)
        # Si population == cap todavía puede ser necesario absorber nodos
        # de población cero para cubrir el universo sin superar el techo.
        # Sólo una masa ya estrictamente superior al techo es inextendible.
        if population > cap:
            continue
        boundary = sorted(
            {
                neighbor
                for node in group
                for neighbor in adjacency.get(node, set())
                if neighbor in nodes and neighbor not in group
            },
            key=str,
        )
        for neighbor in boundary:
            candidate = frozenset(set(group) | {neighbor})
            if candidate in seen:
                continue
            candidate_population = population + weights[neighbor]
            seen.add(candidate)
            if len(seen) > max_seen:
                return None, len(seen)
            if candidate_population <= cap:
                frontier.append(candidate)
    groups.sort(key=lambda group: (len(group), tuple(sorted(group, key=str))))
    return groups, len(seen)


def _exact_connected_hard_partition(
    nodes,
    groups,
    weights,
    *,
    k,
    floor,
    cap,
    max_states=200000,
):
    """Exact cover acotado: True/False si concluye, None si agota estados."""
    nodes = frozenset(nodes)
    by_node = {node: [] for node in nodes}
    for group in groups:
        for node in group:
            by_node[node].append(group)
    for node in by_node:
        by_node[node].sort(
            key=lambda group: (len(group), tuple(sorted(group, key=str)))
        )

    memo = {}
    states = 0

    class SearchLimit(RuntimeError):
        pass

    def solve(remaining, left):
        nonlocal states
        states += 1
        if states > max_states:
            raise SearchLimit
        if not remaining:
            return left == 0
        if left <= 0:
            return False
        population = sum(weights[node] for node in remaining)
        if population < left * floor - 1e-9 or population > left * cap + 1e-9:
            return False
        key = (remaining, left)
        if key in memo:
            return memo[key]
        pivot = min(
            remaining,
            key=lambda node: (
                sum(1 for group in by_node[node] if group <= remaining),
                str(node),
            ),
        )
        for group in by_node[pivot]:
            if group <= remaining and solve(remaining - group, left - 1):
                memo[key] = True
                return True
        memo[key] = False
        return False

    try:
        return solve(nodes, int(k)), states
    except SearchLimit:
        return None, states

def _preflight_atomic_population_connectivity(cfg, step):
    """Preflight poblacional atómico en dos niveles, sin heurística territorial.

    Primero aplica a cada provincia condiciones necesarias sobre secciones
    indivisibles bajo un modelo relajado que ignora contigüidad y disciplina
    municipal; si ese modelo ya es imposible, el contrato es incompatible.
    Después, sólo en provincias monomunicipales pequeñas, intenta además una
    cobertura conexa exacta dentro de suelo/techo. Si el espacio exacto resulta
    demasiado grande, devuelve UNKNOWN y deja actuar al motor normal.
    """
    graph_path = require(step.get("in_graph_json"), "Falta M04 grafo")
    geo_path = require(step.get("in_geojson"), "Falta M04 geojson")
    id_field = require(step.get("id_field"), "Falta id")
    province_field = step.get("province_field", "CPRO")
    municipality_field = step.get("municipality_field", "CUMUN")
    graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
    weights = {str(node["id"]): int(node.get("pop", 0)) for node in graph["nodes"]}
    adjacency = {node: set() for node in weights}
    for edge in graph["edges"]:
        left, right = str(edge["u"]), str(edge["v"])
        if left in adjacency and right in adjacency:
            adjacency[left].add(right)
            adjacency[right].add(left)

    geo = core.load_geo(geo_path)
    geo[id_field] = geo[id_field].astype(str)
    geo[province_field] = geo[province_field].astype(str).str.zfill(2)
    geo[municipality_field] = geo[municipality_field].astype(str)
    graph_nodes = set(weights)
    geo_nodes = set(geo[id_field].astype(str))
    if graph_nodes != geo_nodes:
        missing_geometry = sorted(graph_nodes - geo_nodes, key=str)
        extra_geometry = sorted(geo_nodes - graph_nodes, key=str)
        raise SystemExit(
            "M04: universo M03/geometría incoherente "
            f"missing_geometry={len(missing_geometry)} "
            f"extra_geometry={len(extra_geometry)} "
            f"missing_example={missing_geometry[:5]} "
            f"extra_example={extra_geometry[:5]}"
        )

    validation = cfg.get("validation", {}) or {}
    quota = {
        str(province).zfill(2): int(value)
        for province, value in (validation.get("province_districts") or {}).items()
    }
    k_total = int(
        step.get("k_districts")
        or validation.get("expected_districts")
        or sum(quota.values())
    )
    if not quota and geo[province_field].nunique() == 1:
        quota = {str(geo[province_field].iloc[0]).zfill(2): k_total}
    total_population = sum(weights.values())
    _, floor, cap, _ = hard_limits(cfg, k=k_total, total_pop=total_population)
    floor_exempt = {
        str(value).zfill(2)
        for value in (validation.get("population_floor_exempt_partitions") or [])
    }

    diagnostics = []
    for province, province_k in sorted(quota.items()):
        if province_k <= 0:
            continue
        rows = geo[geo[province_field] == province]
        if rows.empty:
            continue
        nodes = set(rows[id_field].astype(str))
        province_floor = 0.0 if province in floor_exempt else floor
        necessary_ok, necessary_reason, necessary_detail = (
            _atomic_population_necessary_conditions(
                nodes,
                weights,
                k=province_k,
                floor=province_floor,
                cap=cap,
            )
        )
        diagnostics.append({
            "province": province,
            "status": "NECESSARY_PASS" if necessary_ok else "INCOMPATIBLE",
            **necessary_detail,
            "reason": necessary_reason,
        })
        if not necessary_ok:
            raise SystemExit(
                "M04: INCOMPATIBLE_ATOMIC_POPULATION "
                f"provincia {province}: nodes={necessary_detail['nodes']} "
                f"k={province_k} pop={necessary_detail['population']} "
                f"floor={province_floor:.2f} cap={cap:.2f} "
                f"required_singletons={necessary_detail['required_singletons']} "
                f"hard_valid_singletons={necessary_detail['hard_valid_singletons']} "
                f"reason={necessary_reason}"
            )
        if rows[municipality_field].nunique() != 1:
            continue
        if len(nodes) > 64:
            diagnostics.append({
                "province": province,
                "status": "UNKNOWN_EXACT_CONNECTIVITY_TOO_LARGE",
                "nodes": len(nodes),
                "k": province_k,
            })
            continue
        groups, seen = _enumerate_connected_hard_groups(
            nodes,
            adjacency,
            weights,
            floor=province_floor,
            cap=cap,
        )
        if groups is None:
            diagnostics.append({
                "province": province,
                "status": "UNKNOWN_SEARCH_LIMIT",
                "nodes": len(nodes),
                "k": province_k,
                "states_seen": seen,
            })
            continue
        feasible, exact_states = _exact_connected_hard_partition(
            nodes,
            groups,
            weights,
            k=province_k,
            floor=province_floor,
            cap=cap,
        )
        if feasible is None:
            diagnostics.append({
                "province": province,
                "status": "UNKNOWN_EXACT_SEARCH_LIMIT",
                "nodes": len(nodes),
                "k": province_k,
                "hard_valid_connected_groups": len(groups),
                "exact_states": exact_states,
            })
            continue
        diagnostics.append({
            "province": province,
            "status": "FEASIBLE" if feasible else "INCOMPATIBLE",
            "nodes": len(nodes),
            "k": province_k,
            "population": sum(weights[node] for node in nodes),
            "hard_valid_connected_groups": len(groups),
            "exact_states": exact_states,
        })
        if not feasible:
            detail = diagnostics[-1]
            raise SystemExit(
                "M04: INCOMPATIBLE_ATOMIC_POPULATION_CONNECTIVITY "
                f"provincia {province}: nodes={detail['nodes']} "
                f"k={province_k} pop={detail['population']} "
                f"floor={province_floor:.2f} cap={cap:.2f} "
                f"connected_groups={len(groups)} "
                "reason=NO_EXACT_CONNECTED_HARD_PARTITION"
            )
    return diagnostics


def _normalize_unit_property_for_ogr(path):
    archive = Path(path)
    if archive.suffix.lower() != ".zip":
        return 0
    with zipfile.ZipFile(archive) as source:
        name = next(
            item for item in source.namelist()
            if item.lower().endswith((".geojson", ".json")) and not item.endswith("/")
        )
        data = json.loads(source.read(name).decode("utf-8"))
    changed = 0
    for feature in data.get("features", []):
        properties = feature.setdefault("properties", {})
        value = properties.get("ddd_unit_id")
        if isinstance(value, list):
            if len(value) != 1:
                raise SystemExit(
                    f"M04 {ENGINE_VERSION}: ddd_unit_id multivaluado no normalizable: {value!r}"
                )
            properties["ddd_unit_id"] = str(value[0])
            changed += 1
    if changed:
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as target:
            target.writestr(name, json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    return changed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True)
    args = parser.parse_args()
    cfg = load_params_yaml(args.params)
    step = module_cfg(cfg, "modulo_04_generar_semillas", "step4_seed_districts")
    policy = str(step.get("gateway_policy", "preserve_dependent_component_gateways"))
    _preflight_atomic_population_connectivity(cfg, step)
    original = core.partition_oversized_municipality
    protected_component_nodes = set()

    if policy in {
        "preserve_all_external_gateways",
        "preserve_component_gateways",
        "preserve_dependent_component_gateways",
    }:
        graph_path = require(step.get("in_graph_json"), "Falta M04 grafo")
        geo_path = require(step.get("in_geojson"), "Falta M04 geojson")
        id_field = require(step.get("id_field"), "Falta id")
        province_field = step.get("province_field", "CPRO")
        graph = json.loads(Path(graph_path).read_text(encoding="utf-8"))
        adjacency = {str(node["id"]): set() for node in graph["nodes"]}
        for edge in graph["edges"]:
            left, right = str(edge["u"]), str(edge["v"])
            if left in adjacency and right in adjacency:
                adjacency[left].add(right)
                adjacency[right].add(left)
        geo = core.load_geo(geo_path)
        geo[id_field] = geo[id_field].astype(str)
        geo[province_field] = geo[province_field].astype(str).str.zfill(2)
        province_by_node = {
            str(row[id_field]): str(row[province_field]).zfill(2)
            for _, row in geo.iterrows()
        }
        province_nodes = {
            province: set(group[id_field].astype(str))
            for province, group in geo.groupby(province_field)
        }

        def protected_gateways(nodes):
            nodes = set(nodes)
            province = province_by_node[next(iter(nodes))]
            if policy == "preserve_all_external_gateways":
                keep = {
                    node for node in nodes
                    if any(
                        neighbor in province_nodes[province] - nodes
                        for neighbor in adjacency.get(node, set())
                    )
                }
            else:
                keep = _protected_component_gateways(
                    nodes,
                    province_nodes[province],
                    adjacency,
                    dependent_only=(policy == "preserve_dependent_component_gateways"),
                )
            protected_component_nodes.update(keep)
            return keep

        def patched(nodes, target, floor, cap, tolerance, adjacency_arg, weights, label="", protected=None):
            expanded = set(protected or ()) | protected_gateways(nodes)
            return original(
                nodes,
                target,
                floor,
                cap,
                tolerance,
                adjacency_arg,
                weights,
                label=label,
                protected=expanded,
            )

        core.partition_oversized_municipality = patched
    elif policy != "legacy":
        raise SystemExit(f"M04 {ENGINE_VERSION}: gateway_policy desconocida: {policy}")

    try:
        core.main()
    finally:
        core.partition_oversized_municipality = original

    output = require(step.get("out_geojson"), "Falta salida M04")
    changed = _normalize_unit_property_for_ogr(output)
    if changed:
        print(f"[Módulo 4] normalizados ddd_unit_id OGR-safe={changed}")
    postprocess_engine.postprocess(
        args.params,
        additional_protected_nodes=protected_component_nodes,
    )
    print(f"[Módulo 4] motor canónico {ENGINE_VERSION} gateway_policy={policy}")


if __name__ == "__main__":
    main()
