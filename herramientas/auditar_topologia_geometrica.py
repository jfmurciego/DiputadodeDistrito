#!/usr/bin/env python3
"""Puerta independiente de contigüidad basada en frontera geométrica métrica.

No acepta que dos secciones sean adyacentes por compartir únicamente un punto.
Mide de nuevo las aristas de M03 sobre el GeoJSON y valida tanto el territorio
como cada distrito antes de abrir trabajos de cálculo paralelos.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from collections import defaultdict, deque
from pathlib import Path

import geopandas as gpd


VERSION = "1.0.0"


def _read_geojson(path: Path):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [
                name for name in archive.namelist()
                if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
            ]
            if len(members) != 1:
                raise ValueError(f"ZIP debe contener un GeoJSON; contiene {members}")
            return gpd.read_file(io.BytesIO(archive.read(members[0])))
    return gpd.read_file(path)


def _components(nodes: set[str], adjacency: dict[str, set[str]]) -> list[list[str]]:
    remaining = set(nodes)
    groups: list[list[str]] = []
    while remaining:
        start = remaining.pop()
        reached = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for neighbour in adjacency[current] & remaining:
                remaining.remove(neighbour)
                reached.add(neighbour)
                queue.append(neighbour)
        groups.append(sorted(reached))
    return sorted(groups, key=lambda group: (-len(group), group[0]))


def audit(
    sections_path: Path,
    graph_path: Path,
    assignment_path: Path,
    *,
    section_field: str,
    district_field: str,
    min_shared_border_m: float,
    working_crs: str,
) -> dict:
    if min_shared_border_m <= 0:
        raise ValueError("min_shared_border_m debe ser positivo")
    sections = _read_geojson(sections_path)
    assignment = _read_geojson(assignment_path)
    if sections.crs is None or assignment.crs is None:
        raise ValueError("Las geometrías deben declarar CRS")
    sections = sections.to_crs(working_crs)
    assignment = assignment.to_crs(working_crs)
    for frame, label in ((sections, "secciones"), (assignment, "asignación")):
        if section_field not in frame.columns:
            raise ValueError(f"Falta {section_field} en {label}")
        frame[section_field] = frame[section_field].astype(str)
        if frame[section_field].duplicated().any():
            raise ValueError(f"{section_field} duplicado en {label}")
    if district_field not in assignment.columns:
        raise ValueError(f"Falta {district_field} en asignación")
    sections = sections.set_index(section_field, drop=False)
    assignment = assignment.set_index(section_field, drop=False)
    if set(sections.index) != set(assignment.index):
        raise ValueError("Los universos de secciones y asignación no coinciden")

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph_nodes = {str(node["id"]) for node in graph.get("nodes", [])}
    if graph_nodes != set(sections.index):
        raise ValueError("El universo de M03 no coincide con el GeoJSON")
    adjacency = {node: set() for node in graph_nodes}
    point_only: list[list[str]] = []
    below_threshold: list[dict] = []
    accepted = 0
    seen: set[tuple[str, str]] = set()
    for edge in graph.get("edges", []):
        left, right = sorted((str(edge["u"]), str(edge["v"])))
        if left == right or left not in graph_nodes or right not in graph_nodes:
            raise ValueError(f"Arista M03 inválida: {left}-{right}")
        if (left, right) in seen:
            continue
        seen.add((left, right))
        shared = float(
            sections.at[left, "geometry"].boundary.intersection(
                sections.at[right, "geometry"].boundary
            ).length
        )
        if shared <= 1e-9:
            point_only.append([left, right])
        if shared + 1e-9 < min_shared_border_m:
            below_threshold.append({"u": left, "v": right, "shared_border_m": shared})
            continue
        adjacency[left].add(right)
        adjacency[right].add(left)
        accepted += 1

    territory_components = _components(graph_nodes, adjacency)
    disconnected: dict[str, list[int]] = {}
    for district, rows in assignment.groupby(district_field):
        groups = _components(set(rows.index), adjacency)
        if len(groups) > 1:
            disconnected[str(district)] = [len(group) for group in groups]
    decision = "PASS" if len(territory_components) == 1 and not disconnected else "BLOCK"
    return {
        "schema": "ddd.geometric-topology-audit/1.0",
        "tool_version": VERSION,
        "decision": decision,
        "working_crs": working_crs,
        "min_shared_border_m": min_shared_border_m,
        "sections": len(sections),
        "districts": int(assignment[district_field].nunique()),
        "graph_edges": len(seen),
        "accepted_edges": accepted,
        "point_only_edges": len(point_only),
        "below_threshold_edges": len(below_threshold),
        "point_only_examples": point_only[:20],
        "below_threshold_examples": below_threshold[:20],
        "territory_component_sizes": [len(group) for group in territory_components],
        "disconnected_districts": disconnected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sections", type=Path, required=True)
    parser.add_argument("--graph", type=Path, required=True)
    parser.add_argument("--assignment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--section-field", default="CUSEC_KEY")
    parser.add_argument("--district-field", default="district_id")
    parser.add_argument("--min-shared-border-m", type=float, default=1.0)
    parser.add_argument("--working-crs", default="EPSG:25830")
    args = parser.parse_args()
    report = audit(
        args.sections,
        args.graph,
        args.assignment,
        section_field=args.section_field,
        district_field=args.district_field,
        min_shared_border_m=args.min_shared_border_m,
        working_crs=args.working_crs,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["decision"] != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
