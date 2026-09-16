#!/usr/bin/env python3
"""Auditoría causal genérica de continuidad geométrica distrital.

Una discontinuidad solo queda gobernada cuando el grafo de componentes se
conecta por hechos verificables: una sección oficial MultiPolygon que ocupa
varias componentes o una pasarela declarada en el contrato territorial cuyos
dos extremos pertenecen al mismo distrito y enlazan componentes distintas.
No existe lista de excepciones por identificador de distrito.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd
import yaml
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.ops import unary_union

VERSION = "2.0.0"
REPORT_SCHEMA = "ddd.geometric-components-audit/2.0"


def _read_geojson(path: Path) -> gpd.GeoDataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [n for n in archive.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")]
            if len(members) != 1:
                raise ValueError(f"ZIP debe contener exactamente un GeoJSON; contiene {members}")
            return gpd.read_file(io.BytesIO(archive.read(members[0])))
    return gpd.read_file(path)


def _district_key(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    try:
        if pd.notna(value) and float(value).is_integer():
            return str(int(float(value)))
    except (TypeError, ValueError, OverflowError):
        pass
    return str(value)


def _polygon_parts(geometry) -> list[Polygon]:
    if geometry is None or geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        result: list[Polygon] = []
        for member in geometry.geoms:
            result.extend(_polygon_parts(member))
        return result
    return []


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_geometry(geometry) -> str:
    return _sha256_bytes(geometry.wkb)


def _load_contract(path: Path | None) -> tuple[list[dict], str | None]:
    if path is None:
        return [], None
    raw = path.read_bytes()
    cfg = yaml.safe_load(raw.decode("utf-8")) or {}
    m02 = (cfg.get("modulos") or {}).get("modulo_02_construir_adyacencias") or {}
    bridges = m02.get("topology_bridges") or []
    if not isinstance(bridges, list):
        raise ValueError("topology_bridges del contrato debe ser una lista")
    normalized = []
    for index, item in enumerate(bridges):
        if not isinstance(item, dict) or not str(item.get("u", "")).strip() or not str(item.get("v", "")).strip():
            raise ValueError(f"topology_bridges[{index}] carece de extremos u/v válidos")
        normalized.append({**item, "u": str(item["u"]), "v": str(item["v"]), "contract_index": index})
    return normalized, _sha256_bytes(raw)


def _touched_components(geometry, parts: list[Polygon]) -> list[int]:
    return [i for i, part in enumerate(parts) if geometry.intersection(part).area > 1e-6]


def _component_graph_connected(count: int, edges: list[dict]) -> tuple[bool, list[int]]:
    adjacency = {i: set() for i in range(count)}
    for edge in edges:
        a, b = edge["components"]
        adjacency[a].add(b)
        adjacency[b].add(a)
    reached = {0}
    queue = [0]
    while queue:
        current = queue.pop()
        for neighbor in adjacency[current]:
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return len(reached) == count, sorted(set(range(count)) - reached)


def audit(sections_path: Path, *, section_field: str, district_field: str,
          working_crs: str, contract_path: Path | None = None,
          expected_districts: int | None = None) -> dict:
    sections = _read_geojson(sections_path)
    if sections.crs is None:
        raise ValueError("Las secciones deben declarar CRS")
    for field in (section_field, district_field):
        if field not in sections.columns:
            raise ValueError(f"Falta columna {field!r}")
    if sections[section_field].isna().any() or sections[district_field].isna().any():
        raise ValueError("Identificadores de sección o distrito contienen nulos")
    sections = sections.copy()
    sections[section_field] = sections[section_field].astype(str)
    if sections[section_field].duplicated().any():
        raise ValueError(f"{section_field} contiene duplicados")
    if sections.geometry.isna().any() or sections.geometry.is_empty.any():
        raise ValueError("Hay secciones sin geometría")
    invalid = sections.loc[~sections.geometry.is_valid, section_field].tolist()
    if invalid:
        raise ValueError("Geometrías de sección inválidas: " + ", ".join(invalid[:20]))
    if set(sections.geometry.geom_type) - {"Polygon", "MultiPolygon"}:
        raise ValueError("Solo se admiten geometrías Polygon/MultiPolygon")

    metric = sections.to_crs(working_crs)
    bridges, contract_hash = _load_contract(contract_path)
    by_section = metric.set_index(section_field, drop=False)
    rows = []
    connected_count = exception_count = blocked_count = 0

    for raw_district, group in metric.groupby(district_field, sort=True):
        district_label = _district_key(raw_district)
        ordered = group.sort_values(section_field)
        dissolved = unary_union(list(ordered.geometry))
        parts = sorted(_polygon_parts(dissolved), key=lambda g: (-float(g.area), tuple(float(v) for v in g.bounds)))
        if not parts:
            raise ValueError(f"Distrito {district_label}: dissolve vacío")
        total_area = sum(float(p.area) for p in parts)
        component_rows = [{
            "component": i + 1, "area_m2": float(p.area),
            "area_share": float(p.area) / total_area if total_area else None,
            "geometry_sha256": _sha256_geometry(p),
            "bounds": [float(v) for v in p.bounds],
        } for i, p in enumerate(parts)]

        causal_edges: list[dict] = []
        for _, row in ordered.iterrows():
            geom = row.geometry
            if not isinstance(geom, MultiPolygon):
                continue
            touched = _touched_components(geom, parts)
            for pos, left in enumerate(touched):
                for right in touched[pos + 1:]:
                    causal_edges.append({
                        "type": "ATOMIC_MULTIPART",
                        "sections": [str(row[section_field])],
                        "endpoints": None,
                        "components": [left, right],
                        "contract_source": "official_census_section_geometry",
                    })

        district_sections = set(ordered[section_field].astype(str))
        for bridge in bridges:
            u, v = bridge["u"], bridge["v"]
            if u not in district_sections or v not in district_sections:
                continue
            if u not in by_section.index or v not in by_section.index:
                continue
            gu = by_section.loc[u].geometry
            gv = by_section.loc[v].geometry
            touched_u = _touched_components(gu, parts)
            touched_v = _touched_components(gv, parts)
            for left in touched_u:
                for right in touched_v:
                    if left == right:
                        continue
                    causal_edges.append({
                        "type": "GOVERNED_BRIDGE",
                        "sections": None,
                        "endpoints": [u, v],
                        "components": [left, right],
                        "edge_type": bridge.get("edge_type"),
                        "admin_scope": bridge.get("admin_scope"),
                        "reason": bridge.get("reason"),
                        "contract_source": f"{contract_path}:modulos.modulo_02_construir_adyacencias.topology_bridges[{bridge['contract_index']}]" if contract_path else None,
                    })

        if len(parts) == 1:
            status = "PASS"
            connected_count += 1
            unexplained = []
        else:
            causally_connected, unexplained = _component_graph_connected(len(parts), causal_edges)
            if causally_connected:
                status = "PASS_WITH_EXCEPTIONS"
                exception_count += 1
            else:
                status = "BLOCK"
                blocked_count += 1

        rows.append({
            "district_id": district_label,
            "decision": status,
            "section_count": int(len(group)),
            "component_count": len(parts),
            "interior_ring_count": sum(len(p.interiors) for p in parts),
            "geometry_sha256": _sha256_geometry(dissolved),
            "contract_sha256": contract_hash,
            "components": component_rows,
            "causal_exceptions": [{**e, "components": [c + 1 for c in e["components"]]} for e in causal_edges],
            "unexplained_components": [c + 1 for c in unexplained],
        })

    count = len(rows)
    expected_ok = expected_districts in (None, 0) or count == expected_districts
    contract_blockers = [] if expected_ok else [f"district_count={count}, expected={expected_districts}"]
    decision = "BLOCK" if blocked_count or contract_blockers else ("PASS_WITH_EXCEPTIONS" if exception_count else "PASS")
    gate_statement = f"{count} distritos evaluados / {connected_count} PASS / {exception_count} PASS_WITH_EXCEPTIONS / {blocked_count} BLOCK"
    return {
        "schema": REPORT_SCHEMA, "tool_version": VERSION, "decision": decision,
        "gate_statement": gate_statement, "source": str(sections_path),
        "contract_path": str(contract_path) if contract_path else None,
        "contract_sha256": contract_hash, "working_crs": working_crs,
        "section_field": section_field, "district_field": district_field,
        "section_count": int(len(sections)), "district_count": count,
        "expected_districts": expected_districts, "expected_districts_ok": expected_ok,
        "connected_districts": connected_count, "governed_exceptions": exception_count,
        "blocked_districts": blocked_count, "policy_mismatches": 0,
        "contract_blockers": contract_blockers, "districts": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audita continuidad geométrica por causas verificables")
    parser.add_argument("--sections", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--section-field", default="CUSEC_KEY")
    parser.add_argument("--district-field", default="district_id")
    parser.add_argument("--working-crs", default="EPSG:3035")
    parser.add_argument("--expected-districts", type=int, default=0)
    parser.add_argument("--contract", type=Path, default=None)
    args = parser.parse_args()
    report = audit(args.sections, section_field=args.section_field, district_field=args.district_field,
                   working_crs=args.working_crs, contract_path=args.contract,
                   expected_districts=args.expected_districts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["decision"] == "BLOCK":
        sys.exit(2)


if __name__ == "__main__":
    main()
