"""Preparación del grafo M03 para ReCom: aristas con frontera métrica insuficiente.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-11-02 · ESTADO: candidato
QUÉ HACE: antes de entregar el grafo al motor, descarta las aristas cuya frontera compartida mide menos de
  `min_shared_border_m` (adyacencias por esquina del grafo de contigüidad) y deja un informe con cuáles y cuántas.
  Si al descartarlas el grafo pierde conexidad, se detiene (pregunta de diseño); nunca relaja el contrato del motor.
MOTIVO: T-29, el piloto de Salamanca falló en los 5 perfiles con «Arista sin frontera métrica suficiente»
  ('3700101001','3706801001'), shared_border_m=0,044 < 1,0. Es opt-in (`topology.prune_weak_adjacencies`): Aragón no cambia.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping


class GraphPreparationError(ValueError):
    pass


def _components(nodes: list[str], edges: list[tuple[str, str]]) -> int:
    parent = {n: n for n in nodes}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        ru, rv = find(u), find(v)
        if ru != rv:
            parent[ru] = rv
    return len({find(n) for n in nodes})


def prune_weak_adjacencies(
    graph_data: Mapping[str, Any],
    geojson: Mapping[str, Any],
    min_shared_border_m: float,
    section_field: str = "CUSEC_KEY",
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Devuelve (grafo sin aristas débiles, informe). Falla si el grafo deja de ser conexo igual que el original."""
    from shapely.geometry import shape

    geometries = {}
    for feature in geojson.get("features") or []:
        key = str((feature.get("properties") or {}).get(section_field) or "")
        if key and feature.get("geometry") is not None:
            geometries[key] = shape(feature["geometry"])
    node_ids = [str(n.get("id")) for n in graph_data.get("nodes") or []]
    raw_edges = graph_data.get("edges") or []
    kept, weak, seen = [], [], set()
    for raw in raw_edges:
        u, v = str(raw.get("u")), str(raw.get("v"))
        edge = tuple(sorted((u, v)))
        if edge in seen:
            continue
        seen.add(edge)
        if u not in geometries or v not in geometries:
            raise GraphPreparationError(f"Arista sin geometría en ambos extremos: {edge}")
        shared = float(geometries[u].boundary.intersection(geometries[v].boundary).length)
        (weak if shared + 1e-9 < min_shared_border_m else kept).append((edge, shared))
    before = _components(node_ids, [e for e, _ in kept + weak])
    after = _components(node_ids, [e for e, _ in kept])
    report = {
        "schema": "ddd.ensemble-graph-preparation/1.0",
        "min_shared_border_m": min_shared_border_m,
        "edges_total": len(kept) + len(weak),
        "edges_pruned": len(weak),
        "pruned": [{"edge": list(e), "shared_border_m": round(s, 6)} for e, s in sorted(weak)],
        "components_before": before,
        "components_after": after,
        "connected_preserved": after == before,
    }
    if after != before:
        raise GraphPreparationError(
            f"Al descartar {len(weak)} aristas débiles el grafo pasa de {before} a {after} componentes: {report['pruned'][:5]}"
        )
    prepared = copy.deepcopy(dict(graph_data))
    weak_set = {e for e, _ in weak}
    prepared["edges"] = [
        raw for raw in raw_edges if tuple(sorted((str(raw.get("u")), str(raw.get("v"))))) not in weak_set
    ]
    return prepared, report
