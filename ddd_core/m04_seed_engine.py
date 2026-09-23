#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor M04 canónico.

PROYECTO: Diputado de Distrito
Módulo 04 — Motor canónico de semillas
VERSIÓN: 7.6.1
NOMBRE DE VERSIÓN: Reparación dura determinista tras topología métrica
FECHA: 2026-09-15
FUNCIÓN: componer estáticamente el núcleo 7.4.6, el postproceso 7.4.9 y la política de puertas 7.5.4.
CAMBIOS: sustituye el núcleo 7.4.5 por 7.4.6. El nuevo núcleo solo activa un crecimiento directo alternativo cuando la ruta primaria deja alguna violación dura de suelo/techo, y solo lo acepta si mejora la función objetivo.
MOTIVO: el grafo de Aragón con frontera compartida mínima de un metro deja a v7.4.5 un distrito de Teruel en 13.154 habitantes; la misma unidad territorial admite una partición conexa y dura válida mediante el fallback determinista.
ANTERIOR: legacy/ddd_core/m04_seed_engine_v7.6.0.py
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from ddd_core import m04_seed_engine_v746 as core
from ddd_core import m04_seed_engine_v749 as postprocess_engine
from ddd_core.config import load_params_yaml, module_cfg, require

ENGINE_ID = "ddd_core.m04_seed_engine"
ENGINE_VERSION = "7.6.1"
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
    policy = str(step.get("gateway_policy", "legacy"))
    original = core.partition_oversized_municipality

    if policy in {"preserve_all_external_gateways", "preserve_component_gateways"}:
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
                return {
                    node for node in nodes
                    if any(
                        neighbor in province_nodes[province] - nodes
                        for neighbor in adjacency.get(node, set())
                    )
                }
            outside = province_nodes[province] - nodes
            keep = set()
            for component in _components(outside, adjacency):
                candidates = {
                    node for node in nodes
                    if any(neighbor in component for neighbor in adjacency.get(node, set()))
                }
                if candidates:
                    keep.add(min(
                        candidates,
                        key=lambda node: (
                            -sum(1 for neighbor in adjacency.get(node, set()) if neighbor in component),
                            str(node),
                        ),
                    ))
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

    core.main()
    output = require(step.get("out_geojson"), "Falta salida M04")
    changed = _normalize_unit_property_for_ogr(output)
    if changed:
        print(f"[Módulo 4] normalizados ddd_unit_id OGR-safe={changed}")
    postprocess_engine.postprocess(args.params)
    print(f"[Módulo 4] motor canónico {ENGINE_VERSION} gateway_policy={policy}")


if __name__ == "__main__":
    main()
