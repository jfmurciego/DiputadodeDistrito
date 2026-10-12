"""VERSIÓN 1.0.0; NOMBRE diagnóstico físico Congreso; FECHA 2026-10-12.
ALCANCE: mediciones sobre geometría original, sin distritación ni decisiones.
ESTADO: candidato; CAMBIOS/MOTIVO: evidencia N08 sin pasarelas ficticias.
ORIGEN: nuevo; reutiliza componentes deterministas del preflight común.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

import numpy as np
import shapely
from shapely import STRtree
from ddd_core.topology_preflight import _components


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def contacts(geometries, ids):
    """All intersecting original pairs; point, linear and overlap distinguished.

    Zero tolerance, no buffer, no repair, no simplify. Positive overlap never
    establishes an accepted edge, even when it also has a common boundary.
    """
    geoms = np.asarray(geometries, dtype=object)
    pairs = STRtree(geoms).query(geoms, predicate="intersects")
    pairs = pairs[:, pairs[0] < pairs[1]]
    order = np.lexsort((pairs[1], pairs[0]))
    pairs = pairs[:, order]
    result = []
    for start in range(0, pairs.shape[1], 2048):
        i, j = pairs[:, start:start + 2048]
        borders = shapely.intersection(shapely.boundary(geoms[i]), shapely.boundary(geoms[j]))
        shared = shapely.length(borders)
        areas = shapely.area(shapely.intersection(geoms[i], geoms[j]))
        for a, b, line, length, area in zip(i, j, borders, shared, areas):
            rec = {"u": ids[a], "v": ids[b], "shared_border_m": float(length),
                   "overlap_m2": float(area), "contact_sha256": hashlib.sha256(line.wkb).hexdigest()}
            if not math.isfinite(rec["shared_border_m"]) or not math.isfinite(rec["overlap_m2"]):
                raise ValueError("NONFINITE_CONTACT")
            rec["kind"] = "overlap" if area > 0 else "linear" if length > 0 else "point"
            result.append(rec)
    return result


def canonical_components(ids, edges):
    return _components(ids, [(r["u"], r["v"]) for r in edges])


def analyze_unit(frame, k, source_hash, *, precision_grids=(0.01, 0.1, 1.0)):
    """Measured section and polygon-part graphs, never population on invented parts."""
    frame = frame.sort_values("CUSEC", kind="mergesort").reset_index(drop=True)
    code = str(frame.iloc[0].CPRO)
    ids = frame.CUSEC.tolist()
    geoms = frame.geometry.to_numpy()
    raw = contacts(geoms, ids)
    edges = [{**r, "edge_type": "geometric"} for r in raw if r["kind"] == "linear"]
    components = canonical_components(ids, edges)
    component_of = {uid: members[0] for members in components for uid in members}
    populations = dict(zip(ids, map(int, frame.POB_2025)))

    # A MultiPolygon node is not evidence of physical passage between its parts.
    part_ids, part_geoms, owners = [], [], {}
    for uid, geom in zip(ids, geoms):
        parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        # Stable across shapefile feature order; WKB identity retains original coordinates.
        parts.sort(key=lambda p: p.wkb)
        for index, part in enumerate(parts):
            pid = f"{uid}:p{index:04d}"
            part_ids.append(pid); part_geoms.append(part); owners[pid] = uid
    part_contacts = contacts(part_geoms, part_ids)
    part_edges = [r for r in part_contacts if r["kind"] == "linear"]
    part_components = canonical_components(part_ids, part_edges)
    part_component_of = {pid: members[0] for members in part_components for pid in members}
    owner_components = defaultdict(set)
    for pid in part_ids:
        owner_components[owners[pid]].add(part_component_of[pid])

    nodes = []
    for record in frame.to_dict("records"):
        geom = record.pop("geometry"); uid = str(record["CUSEC"])
        attrs = {key: (value.item() if hasattr(value, "item") else value) for key, value in record.items()}
        node = {**attrs, "id": uid, "pop": populations[uid],
                "geometry_sha256": hashlib.sha256(geom.wkb).hexdigest(),
                "source_geometry_sha256": source_hash,
                "physical_component": component_of[uid],
                "physical_part_components": sorted(owner_components[uid])}
        nodes.append(node)
    component_records = [{"id": members[0], "sections": members,
                          "population": sum(populations[u] for u in members)} for members in components]
    part_records = []
    for members in part_components:
        section_ids = sorted({owners[p] for p in members})
        unallocated = [uid for uid in section_ids if len(owner_components[uid]) > 1]
        part_records.append({"id": members[0], "parts": members, "sections": section_ids,
                             "population_exact": (sum(populations[u] for u in section_ids) if not unallocated else None),
                             "population_known": sum(populations[u] for u in section_ids if len(owner_components[u]) == 1),
                             "population_unallocatable_sections": unallocated})
    groups = defaultdict(list)
    for node in nodes: groups[node["CUMUN"]].append(node["id"])
    owner_municipality = {node["id"]: node["CUMUN"] for node in nodes}
    municipality_parts = defaultdict(list)
    part_adjacency = defaultdict(set)
    for pid in part_ids: municipality_parts[owner_municipality[owners[pid]]].append(pid)
    for edge in part_edges:
        part_adjacency[edge["u"]].add(edge["v"]); part_adjacency[edge["v"]].add(edge["u"])
    adjacency = defaultdict(set)
    for edge in edges:
        adjacency[edge["u"]].add(edge["v"]); adjacency[edge["v"]].add(edge["u"])
    municipalities = []
    for mun, members in sorted(groups.items()):
        subset = set(members)
        induced = [(u, v) for u in members for v in adjacency[u] if v in subset and u < v]
        comps = _components(members, induced)
        mun_parts = municipality_parts[mun]; part_subset = set(mun_parts)
        induced_parts = [(u, v) for u in mun_parts for v in part_adjacency[u] if v in part_subset and u < v]
        physical = _components(mun_parts, induced_parts)
        municipalities.append({"CUMUN": mun, "sections": len(members),
                               "population": sum(populations[u] for u in members),
                               "section_components": len(comps), "component_members": comps,
                               "physical_part_components": len(physical), "part_component_members": physical,
                               "isolated_from_other_municipalities": not any(v not in subset for u in members for v in adjacency[u])})
    sensitivity = []
    baseline = {(r["u"], r["v"]) for r in edges}
    for threshold in (0.0, 1.0, 10.0, 50.0):
        selected = [r for r in edges if r["shared_border_m"] > 0 and r["shared_border_m"] >= threshold]
        sensitivity.append({"operation": "original_border_threshold", "threshold_m": threshold,
                            "edges": len(selected), "components": len(canonical_components(ids, selected))})
    for grid in precision_grids:
        snapped = shapely.set_precision(geoms, grid_size=grid)
        measured = contacts(snapped, ids)
        selected = [r for r in measured if r["kind"] == "linear"]
        candidate = {(r["u"], r["v"]) for r in selected}
        added, removed = sorted(candidate - baseline), sorted(baseline - candidate)
        sensitivity.append({"operation": "diagnostic_grid_rounding_only", "grid_m": grid,
                            "edges": len(selected), "components": len(canonical_components(ids, selected)),
                            "new_edges_not_accredited": added, "removed_original_edges": removed,
                            "empty_after_rounding": [ids[i] for i, g in enumerate(snapped) if g.is_empty],
                            "new_edges_sha256": digest(added), "removed_edges_sha256": digest(removed)})
    # Enclosed voids measured on the original union, not labelled missing coverage.
    union = shapely.union_all(geoms)
    polygons = list(union.geoms) if union.geom_type == "MultiPolygon" else [union]
    voids = []
    for poly in polygons:
        for ring in poly.interiors:
            hole = shapely.Polygon(ring)
            voids.append({"area_m2": float(hole.area), "boundary_sha256": hashlib.sha256(hole.wkb).hexdigest()})
    voids.sort(key=lambda r: (r["boundary_sha256"], r["area_m2"]))
    # Structural bounds apply only to measured valid-contact graph; necessary, never sufficient.
    impossibilities = []
    if len(components) > k: impossibilities.append("SECTION_GRAPH_COMPONENTS_EXCEED_K_WITHOUT_BRIDGES")
    if len(part_components) > k: impossibilities.append("PHYSICAL_PART_COMPONENTS_EXCEED_K_WITHOUT_GEOGRAPHICAL_EXCEPTIONS")
    multipart_crossing = sorted(uid for uid, comps in owner_components.items() if len(comps) > 1)
    summary = {"CPRO": code, "sections": len(nodes), "population": sum(populations.values()), "k": k,
               "edges": len(edges), "point_contacts": sum(r["kind"] == "point" for r in raw),
               "overlap_pairs": sum(r["kind"] == "overlap" for r in raw),
               "overlap_area_pair_sum_m2": sum(r["overlap_m2"] for r in raw),
               "section_graph_components": len(components), "physical_part_components": len(part_components),
               "union_polygon_components": len(polygons), "polygon_parts": len(part_ids),
               "isolated_sections": sorted(uid for uid in ids if not adjacency[uid]),
               "discontinuous_municipalities": [r["CUMUN"] for r in municipalities if r["section_components"] > 1 or r["physical_part_components"] > 1],
               "multipart_sections_spanning_physical_components": multipart_crossing,
               "municipalities": len(municipalities), "enclosed_voids": len(voids),
               "enclosed_void_area_m2": sum(r["area_m2"] for r in voids),
               "external_gap_accreditation": "NOT_EVIDENCED_NO_INDEPENDENT_BOUNDARY",
               "structural_impossibilities_under_strict_physical_contiguity": impossibilities,
               "feasibility": "BLOCKED" if impossibilities or multipart_crossing or any(r["kind"] == "overlap" for r in raw) else "NOT_EVIDENCED",
               "generation_authorized": False}
    return {"schema": "ddd.congress-topology-unit/1.0", "summary": summary,
            "nodes": nodes, "edges": edges, "physical_components": component_records,
            "polygon_part_components": part_records, "municipalities": municipalities,
            "point_contacts": [r for r in raw if r["kind"] == "point"],
            "overlaps": [r for r in raw if r["kind"] == "overlap"], "enclosed_voids": voids,
            "sensitivity": sensitivity, "operational_graph": "IDENTICAL_TO_PHYSICAL_SECTION_GRAPH_NO_BRIDGES"}
