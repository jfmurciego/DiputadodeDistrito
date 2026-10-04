#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: Preflight topológico territorial genérico
VERSIÓN: 1.1.0
FECHA: 2026-09-16
ESTADO: candidato
QUÉ HACE: separa grafo físico, componentes administrativas acreditadas, pasarelas declaradas y grafo operativo; emite READY, NEEDS_POLICY o BLOCKED sin ejecutar M01-M03.
"""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any, Iterable, Mapping

DECISIONS = {"READY", "NEEDS_POLICY", "BLOCKED"}
REQUIRED_BRIDGE_KEYS = ("u", "v", "admin_scope", "edge_type", "reason", "source")
TOPOLOGY_ACCREDITATION_SCHEMA = "ddd.topology-accreditation/1.0"
REQUIRED_COMPONENT_KEYS = ("admin_scope", "components", "reason", "source")


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


def _canonical_components(groups: Iterable[Iterable[Any]]) -> tuple[tuple[str, ...], ...]:
    rows = [tuple(sorted(str(value) for value in group)) for group in groups]
    return tuple(sorted(rows, key=lambda row: (-len(row), row[0] if row else "")))


def topology_source_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Identity of the prepared source that topology exceptions are accredited against."""
    meta = cfg.get("meta") or {}
    validation = cfg.get("validation") or {}
    baseline = validation.get("source_baseline") or {}
    section_year = meta.get("source_section_year", baseline.get("section_year"))
    try:
        section_year = int(section_year) if section_year not in (None, "") else None
    except (TypeError, ValueError):
        section_year = None
    return {
        "edition": str(meta.get("year") or ""),
        "section_year": section_year,
        "package_sha256": str(baseline.get("package_sha256") or ""),
        "compatibility_identity_sha256": str(baseline.get("compatibility_identity_sha256") or ""),
    }


def validate_topology_accreditation_binding(cfg: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed when a source-bound topology accreditation no longer matches the input."""
    validation = cfg.get("validation") or {}
    accreditation = validation.get("topology_accreditation")
    if not accreditation:
        return {"present": False, "valid": True, "declared": None, "current": topology_source_binding(cfg)}

    if not isinstance(accreditation, Mapping):
        return {
            "present": True, "valid": False,
            "reason": "topology_accreditation must be an object",
            "declared": None, "current": topology_source_binding(cfg),
        }
    if accreditation.get("schema") != TOPOLOGY_ACCREDITATION_SCHEMA:
        return {
            "present": True, "valid": False,
            "reason": f"unsupported topology accreditation schema: {accreditation.get('schema')}",
            "declared": accreditation.get("source_binding"),
            "current": topology_source_binding(cfg),
        }

    declared = accreditation.get("source_binding")
    current = topology_source_binding(cfg)
    required = ("edition", "section_year", "package_sha256", "compatibility_identity_sha256")
    if not isinstance(declared, Mapping) or any(declared.get(key) in (None, "") for key in required):
        return {
            "present": True, "valid": False,
            "reason": "topology accreditation source_binding is incomplete",
            "declared": dict(declared) if isinstance(declared, Mapping) else declared,
            "current": current,
        }
    normalized = {
        "edition": str(declared.get("edition") or ""),
        "section_year": int(declared["section_year"]),
        "package_sha256": str(declared.get("package_sha256") or ""),
        "compatibility_identity_sha256": str(declared.get("compatibility_identity_sha256") or ""),
    }
    if normalized != current:
        mismatch = [key for key in required if normalized.get(key) != current.get(key)]
        return {
            "present": True, "valid": False,
            "reason": "stale topology accreditation; source binding changed: " + ", ".join(mismatch),
            "declared": normalized, "current": current,
        }
    return {"present": True, "valid": True, "declared": normalized, "current": current}


def validate_administrative_components(
    *,
    units: Mapping[str, Mapping[str, Any]],
    declarations: Iterable[Mapping[str, Any]],
    operational_edges: Iterable[tuple[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate exact administrative component membership without adding operational edges."""
    edges = {_edge(u, v) for u, v in operational_edges if str(u) != str(v)}
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_scopes: set[str] = set()

    for raw in declarations:
        if not isinstance(raw, Mapping):
            rejected.append({"rejection_reason": "administrative component declaration must be an object"})
            continue
        rec = dict(raw)
        missing = [key for key in REQUIRED_COMPONENT_KEYS if rec.get(key) in (None, "")]
        if missing:
            rejected.append({**rec, "rejection_reason": "missing declarative fields: " + ", ".join(missing)})
            continue
        if "district_id" in rec:
            rejected.append({**rec, "rejection_reason": "district_id-dependent component declarations are forbidden"})
            continue
        scope = str(rec["admin_scope"])
        if scope in seen_scopes:
            rejected.append({**rec, "rejection_reason": f"duplicate administrative component declaration: {scope}"})
            continue
        seen_scopes.add(scope)

        scope_nodes, scope_error = _scope_nodes(units, scope)
        if scope_error:
            rejected.append({**rec, "rejection_reason": scope_error})
            continue
        if not scope_nodes:
            rejected.append({**rec, "rejection_reason": f"declared scope has no units: {scope}"})
            continue

        raw_components = rec.get("components")
        if (
            not isinstance(raw_components, list)
            or len(raw_components) < 2
            or any(not isinstance(group, list) or not group for group in raw_components)
        ):
            rejected.append({**rec, "rejection_reason": "components must contain at least two non-empty unit lists"})
            continue
        declared_components = [[str(value) for value in group] for group in raw_components]
        flattened = [value for group in declared_components for value in group]
        if len(flattened) != len(set(flattened)):
            rejected.append({**rec, "rejection_reason": "administrative components contain duplicate units"})
            continue
        if set(flattened) != scope_nodes:
            missing_nodes = sorted(scope_nodes - set(flattened))
            foreign_nodes = sorted(set(flattened) - scope_nodes)
            rejected.append({
                **rec,
                "rejection_reason": (
                    f"administrative component membership no longer covers {scope}; "
                    f"missing={missing_nodes[:12]} foreign={foreign_nodes[:12]}"
                ),
            })
            continue

        scope_edges = {(u, v) for u, v in edges if u in scope_nodes and v in scope_nodes}
        observed = _components(scope_nodes, scope_edges)
        if _canonical_components(declared_components) != _canonical_components(observed):
            rejected.append({
                **rec,
                "rejection_reason": (
                    f"accredited administrative components no longer match observed topology for {scope}; "
                    f"observed={observed}"
                ),
            })
            continue
        accepted.append({
            **rec,
            "admin_scope": scope,
            "components": [list(group) for group in _canonical_components(declared_components)],
            "component_count": len(observed),
        })

    return accepted, rejected


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
    administrative_components: Iterable[Mapping[str, Any]] = (),
    accreditation_error: str | None = None,
) -> dict[str, Any]:
    ids = {str(x) for x in units}
    bridge_list = [dict(x) for x in bridges]
    component_declarations = [dict(x) for x in administrative_components]
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
    component_accepted, component_rejected = validate_administrative_components(
        units=units,
        declarations=component_declarations,
        operational_edges=operational_edges,
    )
    if accreditation_error:
        blocking.append(accreditation_error)
    if component_rejected:
        blocking.extend(item["rejection_reason"] for item in component_rejected)

    operational_components = _components(ids, operational_edges)
    province_components = _group_components(units, operational_edges, "province")
    municipality_components = _group_components(units, operational_edges, "municipality")
    isolated = sorted(uid for uid in ids if not any(uid in e for e in operational_edges))
    multipart = sorted(uid for uid, meta in units.items() if bool(meta.get("multipart")))

    admitted_scopes = {str(item["admin_scope"]) for item in component_accepted}
    unresolved_provinces = sorted(
        k for k, comps in province_components.items()
        if k and len(comps) > 1 and f"province:{k}" not in admitted_scopes
    )
    unresolved_municipalities = sorted(
        k for k, comps in municipality_components.items()
        if k and len(comps) > 1 and f"municipality:{k}" not in admitted_scopes
    )

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
        if component_accepted:
            reasons.append("disconnected administrative scopes match source-bound accredited components")
        else:
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
        "administrative_components": {
            "requested": len(component_declarations),
            "accepted": component_accepted,
            "rejected": component_rejected,
        },
        "operational_edges": len(operational_edges),
    }
