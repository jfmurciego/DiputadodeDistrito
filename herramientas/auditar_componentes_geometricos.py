#!/usr/bin/env python3
"""Auditoría causal genérica de continuidad geométrica.

Las discontinuidades se explican por evidencia, nunca por identificadores de
distrito: secciones censales oficiales MultiPolygon y pasarelas topológicas
declaradas en el contrato territorial M02.
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
        with zipfile.ZipFile(path) as z:
            members = [n for n in z.namelist() if n.lower().endswith((".geojson", ".json")) and not n.endswith("/")]
            if len(members) != 1:
                raise ValueError(f"ZIP debe contener exactamente un GeoJSON; contiene {members}")
            return gpd.read_file(io.BytesIO(z.read(members[0])))
    return gpd.read_file(path)


def _key(value: Any) -> str:
    try:
        if not isinstance(value, bool) and pd.notna(value) and float(value).is_integer():
            return str(int(float(value)))
    except (TypeError, ValueError, OverflowError):
        pass
    return str(value)


def _parts(geometry) -> list[Polygon]:
    if geometry is None or geometry.is_empty:
        return []
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        return [p for g in geometry.geoms for p in _parts(g)]
    return []


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _geometry_sha(geometry) -> str:
    return _sha(geometry.wkb)


def _discover_contract(sections_path: Path) -> Path | None:
    """Localiza el contrato por run_name cuando el consumidor no lo pasa aún."""
    name = sections_path.name
    candidates = []
    for path in Path("territorios").glob("*/config/*.yaml"):
        try:
            cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        run_name = str((cfg.get("meta") or {}).get("run_name") or "")
        if run_name and name.startswith(run_name + "_"):
            candidates.append(path)
    if len(candidates) > 1:
        raise ValueError(f"Contrato territorial ambiguo para {name}: {candidates}")
    return candidates[0] if candidates else None


def _load_contract(path: Path | None) -> tuple[list[dict], str | None]:
    if path is None:
        return [], None
    raw = path.read_bytes()
    cfg = yaml.safe_load(raw.decode("utf-8")) or {}
    bridges = (((cfg.get("modulos") or {}).get("modulo_02_construir_adyacencias") or {}).get("topology_bridges") or [])
    if not isinstance(bridges, list):
        raise ValueError("topology_bridges del contrato debe ser una lista")
    result = []
    for i, bridge in enumerate(bridges):
        if not isinstance(bridge, dict) or not str(bridge.get("u", "")).strip() or not str(bridge.get("v", "")).strip():
            raise ValueError(f"topology_bridges[{i}] carece de extremos u/v")
        result.append({**bridge, "u": str(bridge["u"]), "v": str(bridge["v"]), "contract_index": i})
    return result, _sha(raw)


def _touches(geometry, parts: list[Polygon]) -> list[int]:
    return [i for i, part in enumerate(parts) if geometry.intersection(part).area > 1e-6]


def _connected(n: int, edges: list[dict]) -> tuple[bool, list[int]]:
    graph = {i: set() for i in range(n)}
    for edge in edges:
        a, b = edge["components"]
        graph[a].add(b); graph[b].add(a)
    reached, queue = {0}, [0]
    while queue:
        for nxt in graph[queue.pop()]:
            if nxt not in reached:
                reached.add(nxt); queue.append(nxt)
    return len(reached) == n, sorted(set(range(n)) - reached)


def audit(sections_path: Path, *, section_field: str, district_field: str,
          working_crs: str, contract_path: Path | None = None,
          expected_districts: int | None = None, policy_path: Path | None = None) -> dict:
    if policy_path is not None:
        raise ValueError("Las políticas geométricas por distrito están prohibidas; use evidencia causal y contrato territorial")
    if contract_path is None:
        contract_path = _discover_contract(sections_path)
    sections = _read_geojson(sections_path)
    if sections.crs is None:
        raise ValueError("Las secciones deben declarar CRS")
    for field in (section_field, district_field):
        if field not in sections.columns:
            raise ValueError(f"Falta columna {field!r}")
    if sections[section_field].isna().any() or sections[district_field].isna().any():
        raise ValueError("Identificadores de sección o distrito contienen nulos")
    sections = sections.copy(); sections[section_field] = sections[section_field].astype(str)
    if sections[section_field].duplicated().any():
        raise ValueError(f"{section_field} contiene duplicados")
    if sections.geometry.isna().any() or sections.geometry.is_empty.any():
        raise ValueError("Hay secciones sin geometría")
    invalid = sections.loc[~sections.geometry.is_valid, section_field].tolist()
    if invalid:
        raise ValueError("Geometrías inválidas: " + ", ".join(invalid[:20]))
    if set(sections.geometry.geom_type) - {"Polygon", "MultiPolygon"}:
        raise ValueError("Solo se admiten Polygon/MultiPolygon")

    metric = sections.to_crs(working_crs)
    bridges, contract_hash = _load_contract(contract_path)
    by_section = metric.set_index(section_field, drop=False)
    rows = []; pass_count = exception_count = blocked_count = 0

    for raw_label, group in metric.groupby(district_field, sort=True):
        label = _key(raw_label)
        ordered = group.sort_values(section_field)
        dissolved = unary_union(list(ordered.geometry))
        parts = sorted(_parts(dissolved), key=lambda g: (-float(g.area), tuple(float(v) for v in g.bounds)))
        if not parts:
            raise ValueError(f"Distrito {label}: dissolve vacío")
        district_hash = _geometry_sha(dissolved)
        total_area = sum(float(p.area) for p in parts)
        component_rows = [{"component": i + 1, "area_m2": float(p.area),
                           "area_share": float(p.area) / total_area if total_area else None,
                           "geometry_sha256": _geometry_sha(p),
                           "bounds": [float(v) for v in p.bounds]}
                          for i, p in enumerate(parts)]
        edges: list[dict] = []

        for _, row in ordered.iterrows():
            if not isinstance(row.geometry, MultiPolygon):
                continue
            touched = _touches(row.geometry, parts)
            for pos, left in enumerate(touched):
                for right in touched[pos + 1:]:
                    edges.append({"type": "ATOMIC_MULTIPART", "sections": [str(row[section_field])],
                                  "endpoints": None, "components": [left, right],
                                  "source": "official_census_section_geometry"})

        district_sections = set(ordered[section_field].astype(str))
        for bridge in bridges:
            u, v = bridge["u"], bridge["v"]
            # Una pasarela solo es causal si ambos extremos pertenecen al distrito.
            if u not in district_sections or v not in district_sections or u not in by_section.index or v not in by_section.index:
                continue
            for left in _touches(by_section.loc[u].geometry, parts):
                for right in _touches(by_section.loc[v].geometry, parts):
                    if left != right:
                        edges.append({"type": "GOVERNED_BRIDGE", "sections": None,
                                      "endpoints": [u, v], "components": [left, right],
                                      "edge_type": bridge.get("edge_type"), "admin_scope": bridge.get("admin_scope"),
                                      "reason": bridge.get("reason"),
                                      "source": f"{contract_path}:modulos.modulo_02_construir_adyacencias.topology_bridges[{bridge['contract_index']}]"})

        if len(parts) == 1:
            district_decision, unexplained = "PASS", []; pass_count += 1
        else:
            causally_connected, unexplained = _connected(len(parts), edges)
            if causally_connected:
                district_decision = "PASS_WITH_EXCEPTIONS"; exception_count += 1
            else:
                district_decision = "BLOCK"; blocked_count += 1

        evidence = [{**edge, "components": [c + 1 for c in edge["components"]],
                     "geometry_sha256": district_hash, "contract_sha256": contract_hash}
                    for edge in edges]
        rows.append({"district_id": label, "decision": district_decision,
                     "section_count": int(len(group)), "component_count": len(parts),
                     "interior_ring_count": sum(len(p.interiors) for p in parts),
                     "geometry_sha256": district_hash, "contract_sha256": contract_hash,
                     "components": component_rows, "causal_exceptions": evidence,
                     "unexplained_components": [c + 1 for c in unexplained]})

    count = len(rows)
    expected_ok = expected_districts in (None, 0) or count == expected_districts
    blockers = [] if expected_ok else [f"district_count={count}, expected={expected_districts}"]
    decision = "BLOCK" if blocked_count or blockers else ("PASS_WITH_EXCEPTIONS" if exception_count else "PASS")
    return {"schema": REPORT_SCHEMA, "tool_version": VERSION, "decision": decision,
            "gate_statement": f"{count} distritos evaluados / {pass_count} PASS / {exception_count} PASS_WITH_EXCEPTIONS / {blocked_count} BLOCK",
            "source": str(sections_path), "contract_path": str(contract_path) if contract_path else None,
            "contract_sha256": contract_hash, "working_crs": working_crs,
            "section_field": section_field, "district_field": district_field,
            "section_count": int(len(sections)), "district_count": count,
            "expected_districts": expected_districts, "expected_districts_ok": expected_ok,
            "connected_districts": pass_count, "governed_exceptions": exception_count,
            "blocked_districts": blocked_count, "policy_mismatches": 0,
            "contract_blockers": blockers, "districts": rows}


def main() -> None:
    p = argparse.ArgumentParser(description="Audita continuidad geométrica por causas verificables")
    p.add_argument("--sections", type=Path, required=True); p.add_argument("--output", type=Path, required=True)
    p.add_argument("--section-field", default="CUSEC_KEY"); p.add_argument("--district-field", default="district_id")
    p.add_argument("--working-crs", default="EPSG:3035"); p.add_argument("--expected-districts", type=int, default=0)
    p.add_argument("--contract", type=Path, default=None)
    p.add_argument("--policy", type=Path, default=None, help="Obsoleto: las políticas por distrito están prohibidas")
    args = p.parse_args()
    report = audit(args.sections, section_field=args.section_field, district_field=args.district_field,
                   working_crs=args.working_crs, contract_path=args.contract,
                   expected_districts=args.expected_districts, policy_path=args.policy)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["decision"] == "BLOCK": sys.exit(2)


if __name__ == "__main__": main()
