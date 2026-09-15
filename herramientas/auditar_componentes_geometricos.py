#!/usr/bin/env python3
"""PROYECTO: Diputado de Distrito
HERRAMIENTA: Auditoría independiente de componentes geométricos distritales
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Dissolve independiente con excepciones territoriales explícitas
FECHA: 2026-09-15

QUÉ HACE:
- agrupa todas las secciones de cada distrito;
- reproyecta a un CRS de trabajo explícito;
- disuelve la geometría sin consultar el grafo M03;
- cuenta componentes poligonales y diferencia Polygon/MultiPolygon;
- informa huecos interiores;
- bloquea toda discontinuidad no gobernada;
- solo admite MultiPolygon mediante una excepción explícita, motivada y con
  número esperado de componentes.

POR QUÉ EXISTE:
la conectividad de un grafo de secciones no demuestra por sí sola que la
geometría disuelta de un distrito forme una pieza territorial defendible.
Esta herramienta constituye una segunda prueba independiente.
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
from shapely.geometry import GeometryCollection, MultiPolygon, Polygon
from shapely.ops import unary_union


VERSION = "1.0.0"
REPORT_SCHEMA = "ddd.geometric-components-audit/1.0"
POLICY_SCHEMA = "ddd.geometric-contiguity-policy/1.0"


def _read_geojson(path: Path) -> gpd.GeoDataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [
                name
                for name in archive.namelist()
                if name.lower().endswith((".geojson", ".json"))
                and not name.endswith("/")
            ]
            if len(members) != 1:
                raise ValueError(
                    f"ZIP debe contener exactamente un GeoJSON; contiene {members}"
                )
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
        parts: list[Polygon] = []
        for member in geometry.geoms:
            parts.extend(_polygon_parts(member))
        return parts
    return []


def _load_policy(path: Path | None) -> dict[str, dict]:
    if path is None:
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != POLICY_SCHEMA:
        raise ValueError(
            f"Política con schema inválido: {payload.get('schema')!r}; "
            f"esperado {POLICY_SCHEMA!r}"
        )
    raw = payload.get("allowed_disconnected_districts", [])
    if not isinstance(raw, list):
        raise ValueError("allowed_disconnected_districts debe ser una lista")

    result: dict[str, dict] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Cada excepción debe ser un objeto")
        if "district_id" not in item:
            raise ValueError("Excepción sin district_id")
        key = _district_key(item["district_id"])
        if key in result:
            raise ValueError(f"Excepción duplicada para distrito {key}")

        expected = item.get("expected_components")
        if not isinstance(expected, int) or expected < 2:
            raise ValueError(
                f"Excepción {key}: expected_components debe ser entero >= 2"
            )
        reason = str(item.get("reason", "")).strip()
        kind = str(item.get("kind", "")).strip()
        if not reason or not kind:
            raise ValueError(f"Excepción {key}: kind y reason son obligatorios")

        result[key] = {
            "district_id": key,
            "expected_components": expected,
            "kind": kind,
            "reason": reason,
        }
    return result


def _sha256_geometry(geometry) -> str:
    return hashlib.sha256(geometry.wkb).hexdigest()


def audit(
    sections_path: Path,
    *,
    section_field: str,
    district_field: str,
    working_crs: str,
    policy_path: Path | None = None,
    expected_districts: int | None = None,
) -> dict:
    sections = _read_geojson(sections_path)
    if sections.crs is None:
        raise ValueError("Las secciones deben declarar CRS")

    for field in (section_field, district_field):
        if field not in sections.columns:
            raise ValueError(f"Falta columna {field!r}")

    if sections[section_field].isna().any():
        raise ValueError(f"{section_field} contiene nulos")
    sections = sections.copy()
    sections[section_field] = sections[section_field].astype(str)
    if sections[section_field].duplicated().any():
        duplicate = sections.loc[
            sections[section_field].duplicated(), section_field
        ].iloc[0]
        raise ValueError(f"{section_field} duplicado: {duplicate}")

    if sections[district_field].isna().any():
        raise ValueError(f"{district_field} contiene nulos")
    if sections.geometry.isna().any() or sections.geometry.is_empty.any():
        raise ValueError("Hay secciones sin geometría o con geometría vacía")

    invalid = sections.loc[~sections.geometry.is_valid, section_field].tolist()
    if invalid:
        raise ValueError(
            "Geometrías de sección inválidas; la auditoría no las repara: "
            + ", ".join(invalid[:20])
        )

    non_polygonal = sorted(
        set(sections.geometry.geom_type) - {"Polygon", "MultiPolygon"}
    )
    if non_polygonal:
        raise ValueError(
            "Geometrías de sección no poligonales: " + ", ".join(non_polygonal)
        )

    metric = sections.to_crs(working_crs)
    policy = _load_policy(policy_path)

    district_rows: list[dict] = []
    connected_count = 0
    exception_count = 0
    blocked_district_count = 0
    policy_mismatch_count = 0
    observed_districts: set[str] = set()

    for raw_district, group in metric.groupby(district_field, sort=True):
        district_id = _district_key(raw_district)
        observed_districts.add(district_id)

        # El orden fijo hace reproducible el dissolve y su huella binaria dentro
        # de una misma pila GEOS/Shapely.
        ordered = group.sort_values(section_field)
        dissolved = unary_union(list(ordered.geometry))
        parts = _polygon_parts(dissolved)
        if not parts:
            raise ValueError(
                f"Distrito {district_id}: dissolve sin componentes poligonales"
            )

        parts = sorted(
            parts,
            key=lambda geom: (
                -float(geom.area),
                tuple(float(v) for v in geom.bounds),
            ),
        )
        component_count = len(parts)
        geometry_type = dissolved.geom_type
        interior_ring_count = sum(len(poly.interiors) for poly in parts)
        total_area = float(sum(float(poly.area) for poly in parts))

        component_rows = []
        for rank, part in enumerate(parts, start=1):
            area = float(part.area)
            component_rows.append(
                {
                    "rank": rank,
                    "area_m2": area,
                    "area_share": (area / total_area) if total_area > 0 else None,
                    "bounds": [float(v) for v in part.bounds],
                    "geometry_sha256": _sha256_geometry(part),
                }
            )

        policy_entry = policy.get(district_id)
        connected = component_count == 1 and geometry_type == "Polygon"
        exact_policy_match = (
            geometry_type == "MultiPolygon"
            and policy_entry is not None
            and policy_entry["expected_components"] == component_count
        )

        if connected:
            status = "CONNECTED"
            connected_count += 1
            policy_applied = False
            if policy_entry is not None:
                policy_mismatch_count += 1
        elif exact_policy_match:
            status = "GOVERNED_EXCEPTION"
            exception_count += 1
            policy_applied = True
        else:
            status = "POTENTIAL_DISCONTINUITY"
            blocked_district_count += 1
            policy_applied = False
            if policy_entry is not None:
                policy_mismatch_count += 1

        district_rows.append(
            {
                "district_id": district_id,
                "section_count": int(len(group)),
                "source_geometry_types": sorted(
                    set(group.geometry.geom_type.astype(str))
                ),
                "dissolved_geometry_type": geometry_type,
                "component_count": component_count,
                "interior_ring_count": interior_ring_count,
                "connected": connected,
                "status": status,
                "policy_applied": policy_applied,
                "policy": policy_entry,
                "area_m2": total_area,
                "components": component_rows,
                "bounds": [float(v) for v in dissolved.bounds],
                "geometry_sha256": _sha256_geometry(dissolved),
            }
        )

    unknown_policy_districts = sorted(set(policy) - observed_districts)
    if unknown_policy_districts:
        raise ValueError(
            "La política contiene distritos inexistentes en la evidencia: "
            + ", ".join(unknown_policy_districts)
        )

    district_count = len(district_rows)
    expected_ok = (
        expected_districts in (None, 0) or district_count == expected_districts
    )
    contract_blockers: list[str] = []
    if not expected_ok:
        contract_blockers.append(
            f"district_count={district_count}, expected={expected_districts}"
        )
    if policy_mismatch_count:
        contract_blockers.append(
            f"policy_mismatches={policy_mismatch_count}"
        )

    if blocked_district_count or contract_blockers:
        decision = "BLOCK"
    elif exception_count:
        decision = "PASS_WITH_EXCEPTIONS"
    else:
        decision = "PASS"

    if decision == "PASS":
        gate_statement = (
            f"{district_count} distritos evaluados / "
            f"{connected_count} geométricamente conexos"
        )
    elif decision == "PASS_WITH_EXCEPTIONS":
        gate_statement = (
            f"{district_count} distritos evaluados / {connected_count} conexos / "
            f"{exception_count} excepciones territoriales explícitas / 0 bloqueados"
        )
    else:
        gate_statement = (
            f"{district_count} distritos evaluados / {connected_count} conexos / "
            f"{exception_count} excepciones explícitas / "
            f"{blocked_district_count} distritos bloqueados / "
            f"{len(contract_blockers)} bloqueos de contrato"
        )

    return {
        "schema": REPORT_SCHEMA,
        "tool_version": VERSION,
        "decision": decision,
        "gate_statement": gate_statement,
        "source": str(sections_path),
        "working_crs": working_crs,
        "section_field": section_field,
        "district_field": district_field,
        "section_count": int(len(sections)),
        "district_count": district_count,
        "expected_districts": expected_districts,
        "expected_districts_ok": expected_ok,
        "connected_districts": connected_count,
        "governed_exceptions": exception_count,
        "blocked_districts": blocked_district_count,
        "policy_mismatches": policy_mismatch_count,
        "contract_blockers": contract_blockers,
        "policy_schema": POLICY_SCHEMA if policy_path is not None else None,
        "policy_path": str(policy_path) if policy_path is not None else None,
        "districts": district_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Audita continuidad distrital reconstruyendo y disolviendo "
            "geometrías de sección, sin usar el grafo."
        )
    )
    parser.add_argument("--sections", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--section-field", default="CUSEC_KEY")
    parser.add_argument("--district-field", default="district_id")
    parser.add_argument("--working-crs", default="EPSG:3035")
    parser.add_argument("--expected-districts", type=int, default=0)
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help=(
            "JSON de excepciones territoriales explícitas. "
            "Sin política, todo MultiPolygon bloquea."
        ),
    )
    args = parser.parse_args()

    report = audit(
        args.sections,
        section_field=args.section_field,
        district_field=args.district_field,
        working_crs=args.working_crs,
        policy_path=args.policy,
        expected_districts=args.expected_districts,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["decision"] == "BLOCK":
        sys.exit(2)


if __name__ == "__main__":
    main()
