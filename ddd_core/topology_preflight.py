#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Preflight topológico territorial genérico
VERSIÓN: 1.0.2
FECHA: 2026-09-16
ESTADO: candidato
QUÉ HACE: separa grafo físico, componentes diagnosticadas, pasarelas declaradas y grafo operativo; emite READY, NEEDS_POLICY o BLOCKED sin ejecutar M01-M03.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable, Mapping

DECISIONS = {"READY", "NEEDS_POLICY", "BLOCKED"}
REQUIRED_BRIDGE_KEYS = ("u", "v", "admin_scope", "edge_type", "reason", "source")


def _components(nodes: Iterable[str], edges: Iterable[tuple[str, str]]) -> list[list[str]]:
    nodes = sorted({str(n) for n in nodes})
    adj = {n: set() for n in nodes}
    for u, v in edges:
        u, v = str(u), str(v)
        if u in adj and v in adj and u != v:
            adj[u].add(v)
            adj[v].add(u)
    seen = set()
    out = []
    for start in nodes:
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nxt in sorted(adj[cur]):
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        out.append(sorted(comp))
    return out


def _group_components(units: Mapping[str, Mapping[str, Any]], edges: set[tuple[str, str]], field: str) -> dict[str, list[list[str]]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for uid, meta in units.items():
        groups[str(meta.get(field, ""))].append(str(uid))
    result = {}
    for key, members in groups.items():
        member_set = set(members)
        group_edges = {(u, v) for u, v in edges if u in member_set and v in member_set}
        result[key] = _components(members, group_edges)
    return result


def _edge(u: Any, v: Any) -> tuple[str, str]:
    a, b = str(u), str(v)
    return (a, b) if a < b else (b, a)


def _scope_nodes(units: Mapping[str, Mapping[str, Any]], admin_scope: str) -> tuple[set[str], str | None]:
    if admin_scope.startswith("province:"):
        expected = admin_scope.split(":", 1)[1].zfill(2)
        return {
            str(uid) for uid, meta in units.items()
            if str(meta.get("province", "")).zfill(2) == expected
        }, None
    if admin_scope.startswith("municipality:"):
        expected = admin_scope.split(":", 1)[1]
        return {
            str(uid) for uid, meta in units.items()
            if str(meta.get("municipality", "")) == expected
        }, None
    return set(), f"unsupported admin_scope: {admin_scope}"


def validate_topology_bridges(
    *,
    units: Mapping[str, Mapping[str, Any]],
    bridges: Iterable[Mapping[str, Any]],
    base_edges: Iterable[tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], set[tuple[str, str]]]:
    """Validate bridges once, against the induced graph of each declared scope."""
    ids = {str(x) for x in units}
    operational_edges = {_edge(u, v) for u, v in base_edges if str(u) != str(v)}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for raw in bridges:
        if not isinstance(raw, Mapping):
            rejected.append({"rejection_reason": "bridge must be an object"})
            continue
        b = dict(raw)
        missing = [k for k in REQUIRED_BRIDGE_KEYS if b.get(k) in (None, "")]
        if missing:
            rejected.append({**b, "rejection_reason": f"missing declarative fields: {', '.join(missing)}"})
            continue
        if "district_id" in b:
            rejected.append({**b, "rejection_reason": "district_id-dependent exceptions are forbidden"})
            continue

        u, v = str(b["u"]), str(b["v"])
        if u == v:
            rejected.append({**b, "rejection_reason": "bridge endpoints must be different"})
            continue
        if u not in ids or v not in ids:
            rejected.append({**b, "rejection_reason": "bridge endpoint does not exist"})
            continue

        scope = str(b["admin_scope"])
        scope_nodes, scope_error = _scope_nodes(units, scope)
        if scope_error:
            rejected.append({**b, "rejection_reason": scope_error})
            continue
        if u not in scope_nodes or v not in scope_nodes:
            rejected.append({**b, "rejection_reason": f"bridge endpoints do not belong to declared scope {scope}"})
            continue

        scope_edges = {(a, c) for a, c in operational_edges if a in scope_nodes and c in scope_nodes}
        before_components = _components(scope_nodes, scope_edges)
        component_of = {uid: i for i, comp in enumerate(before_components) for uid in comp}
        if component_of.get(u) == component_of.get(v):
            rejected.append({**b, "rejection_reason": "bridge does not resolve a diagnosed disconnection inside declared scope"})
            continue

        candidate = _edge(u, v)
        after_scope_edges = set(scope_edges)
        after_scope_edges.add(candidate)
        after_components = _components(scope_nodes, after_scope_edges)
        if len(after_components) >= len(before_components):
            rejected.append({**b, "rejection_reason": "bridge does not reduce components inside declared scope"})
            continue

        operational_edges.add(candidate)
        accepted.append({**b, "u": candidate[0], "v": candidate[1]})

    return accepted, rejected, operational_edges


def evaluate_topology_preflight(
    *,
    units: Mapping[str, Mapping[str, Any]],
    contacts: Iterable[Mapping[str, Any]],
    bridges: Iterable[Mapping[str, Any]],
    min_shared_border_m: float,
    productive_continental: bool = True,
) -> dict[str, Any]:
    ids = {str(x) for x in units}
    bridge_list = [dict(x) for x in bridges]
    reasons: list[str] = []
    blocking: list[str] = []
    physical_edges: set[tuple[str, str]] = set()
    point_contacts_removed: list[dict[str, Any]] = []
    edges_below_threshold: list[dict[str, Any]] = []

    if productive_continental and (not isinstance(min_shared_border_m, (int, float)) or min_shared_border_m <= 0):
        blocking.append("productive continental territories require min_shared_border_m > 0")

    for item in contacts:
        u, v = str(item.get("u")), str(item.get("v"))
        if u not in ids or v not in ids or u == v:
            continue
        shared = float(item.get("shared_border_m", 0.0))
        rec = {"u": min(u, v), "v": max(u, v), "shared_border_m": shared}
        if shared <= 0:
            point_contacts_removed.append(rec)
        elif shared < min_shared_border_m:
            edges_below_threshold.append(rec)
        else:
            physical_edges.add(_edge(u, v))

    physical_components = _components(ids, physical_edges)
    accepted, rejected, operational_edges = validate_topology_bridges(
        units=units,
        bridges=bridge_list,
        base_edges=physical_edges,
    )
    if rejected:
        blocking.extend(item["rejection_reason"] for item in rejected)

    operational_components = _components(ids, operational_edges)
    province_components = _group_components(units, operational_edges, "province")
    municipality_components = _group_components(units, operational_edges, "municipality")
    isolated = sorted(uid for uid in ids if not any(uid in e for e in operational_edges))
    multipart = sorted(uid for uid, meta in units.items() if bool(meta.get("multipart")))

    unresolved_provinces = sorted(k for k, comps in province_components.items() if k and len(comps) > 1)
    unresolved_municipalities = sorted(k for k, comps in municipality_components.items() if k and len(comps) > 1)

    if blocking:
        decision = "BLOCKED"
        reasons.extend(sorted(set(blocking)))
    elif unresolved_provinces or unresolved_municipalities:
        decision = "NEEDS_POLICY"
        if unresolved_provinces:
            reasons.append("disconnected provinces: " + ", ".join(unresolved_provinces))
        if unresolved_municipalities:
            reasons.append("disconnected municipalities: " + ", ".join(unresolved_municipalities))
    else:
        decision = "READY"
        reasons.append("each administrative scope is operationally connected under declared policy")

    return {
        "schema_version": "1.0.1",
        "decision": decision,
        "reasons": reasons,
        "min_shared_border_m": min_shared_border_m,
        "physical_edges": len(physical_edges),
        "point_contacts_removed": point_contacts_removed,
        "edges_below_threshold": edges_below_threshold,
        "components": {
            "territorial_physical": physical_components,
            "territorial_operational": operational_components,
            "provincial": province_components,
            "municipal": municipality_components,
        },
        "isolated_sections": isolated,
        "multipart_sections": multipart,
        "bridges": {
            "requested": len(bridge_list),
            "accepted": accepted,
            "rejected": rejected,
        },
        "operational_edges": len(operational_edges),
    }
