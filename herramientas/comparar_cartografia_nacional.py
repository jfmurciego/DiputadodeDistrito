#!/usr/bin/env python3
"""VERSIÓN: 1.0.1; NOMBRE: comparador cartográfico nacional acreditado.
FECHA: 2026-10-10; ALCANCE: diagnóstico local, sin generación ni reparación.
ESTADO: candidato, CI_PENDIENTE; CAMBIOS: inventario y comparación fail-closed.
MOTIVO: separar edición, identidad, geometría y población de materiales históricos.
ANTERIOR: legacy/herramientas/comparar_cartografia_nacional_v1.0.0.py; CAMBIOS: geometría ausente rechazada en inventario.
"""
from __future__ import annotations
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
import math
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET


def metadata():
    return {"version": "1.0.0", "name": "Comparación cartográfica nacional",
            "date": "2026-10-08", "scope": "análisis local sin generación",
            "status": "CI_PENDIENTE", "changes": "diagnóstico y correspondencia acreditada",
            "reason": "no inferir ediciones ni causas por nombres", "origin": "nuevo, sin predecesor"}


def read_bytes(path):
    path = Path(path)
    return gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()


def identity(value):
    if isinstance(value, bool) or value is None or not isinstance(value, (str, int)):
        raise ValueError("IDENTITY_MISSING_OR_INVALID")
    result = str(value).strip()
    if not result:
        raise ValueError("IDENTITY_MISSING_OR_INVALID")
    return result


def province(value):
    result = identity(value).zfill(2)
    if result not in {f"{i:02d}" for i in range(1, 53)}:
        raise ValueError("PROVINCE_INVALID")
    return result


def population(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("POPULATION_INVALID")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("POPULATION_INVALID") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("POPULATION_INVALID")
    return result


def workbook_summary(path):
    """Sólo XML/ZIP; no abre Excel, ejecuta macros ni interpreta fórmulas."""
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(Path(path)) as archive:
        strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ["".join(n.itertext()) for n in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("s:si", ns)]
        records = []
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        for row in sheet.findall("s:sheetData/s:row", ns):
            cells = {}
            for cell in row.findall("s:c", ns):
                if cell.find("s:f", ns) is not None:
                    raise ValueError("WORKBOOK_FORMULA_NOT_EVALUATED")
                value = cell.find("s:v", ns); inline = cell.find("s:is", ns)
                text = value.text if value is not None else "".join(inline.itertext()) if inline is not None else None
                if cell.get("t") == "s":
                    text = strings[int(text)]
                key = "".join(c for c in cell.get("r", "") if c.isalpha())
                cells[key] = text
            records.append(cells)
        core = ET.fromstring(archive.read("docProps/core.xml"))
        dates = {n.tag.rsplit("}", 1)[-1]: n.text for n in core if n.tag.rsplit("}", 1)[-1] in {"created", "modified"}}
        return {"sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                "core_dates_not_data_editions": dates, "row_count_excluding_header": len(records)-1,
                "header": records[0] if records else {},
                "sheet_xml_sha256": hashlib.sha256(archive.read("xl/worksheets/sheet1.xml")).hexdigest(),
                "member_sha256": {n: hashlib.sha256(archive.read(n)).hexdigest() for n in sorted(archive.namelist())},
                "macro_members": [n for n in archive.namelist() if "vba" in n.lower()], "rows": records}


def inspect_geojson(path, descriptor):
    """El descriptor elige campos; edición/procedencia desconocidas permanecen desconocidas."""
    import shapely
    from shapely.geometry import shape
    from shapely.validation import explain_validity
    from pyproj import CRS
    raw = read_bytes(path); data = json.loads(raw)
    if data.get("type") != "FeatureCollection" or not isinstance(data.get("features"), list) or not data["features"]:
        raise ValueError("FEATURE_COLLECTION_REQUIRED")
    declared_crs = ((data.get("crs") or {}).get("properties") or {}).get("name")
    crs = descriptor.get("crs") or declared_crs or "OGC:CRS84"
    origin = "descriptor" if descriptor.get("crs") else "legacy_declared" if declared_crs else "RFC7946_default_CRS84"
    parsed_crs = CRS.from_user_input(crs)
    if descriptor.get("crs") and declared_crs and not parsed_crs.equals(CRS.from_user_input(declared_crs), ignore_axis_order=True):
        raise ValueError("CRS_CONTRADICTION")
    records = {}; errors = []; disconnected = []; types = Counter(); counts = Counter(); totals = Counter()
    for index, feature in enumerate(data["features"]):
        props = feature.get("properties") or {}; item_id = None
        try:
            if feature.get("type") != "Feature":
                raise ValueError("FEATURE_REQUIRED")
            item_id = identity(props.get(descriptor["id_field"]))
            if item_id in records:
                raise ValueError("IDENTITY_DUPLICATE")
            code = province(props.get(descriptor["province_field"]))
            pop = population(props.get(descriptor["population_field"]))
            if not isinstance(feature.get("geometry"),dict):
                raise ValueError('GEOMETRY_MISSING_OR_INVALID')
            geom = shape(feature.get("geometry"))
            if geom.geom_type not in {"Polygon", "MultiPolygon"} or geom.is_empty or not all(math.isfinite(x) for x in geom.bounds):
                raise ValueError("GEOMETRY_EMPTY_OR_NON_POLYGONAL")
            types[geom.geom_type] += 1
            components = len(geom.geoms) if geom.geom_type == "MultiPolygon" else 1
            if components > 1:
                disconnected.append({"id": item_id, "components": components})
            if not geom.is_valid:
                raise ValueError("GEOMETRY_INVALID: " + explain_validity(geom))
            if descriptor.get("require_connected") is True and components > 1:
                raise ValueError("DISCONTINUITY_NOT_ADMITTED")
            if parsed_crs.is_geographic and not (-180 <= geom.bounds[0] <= geom.bounds[2] <= 180 and -90 <= geom.bounds[1] <= geom.bounds[3] <= 90):
                raise ValueError("GEOGRAPHIC_COORDINATES_OUT_OF_RANGE")
            records[item_id] = {"geometry": geom, "raw_geometry": feature["geometry"], "province": code, "population": pop}
            counts[code] += 1; totals[code] += pop
        except (ValueError, TypeError, KeyError, shapely.errors.GEOSException) as exc:
            errors.append({"feature_index": index, "id": item_id, "error": str(exc)})
    report = {"metadata": metadata(), "file_sha256": hashlib.sha256(raw).hexdigest(),
              "status": "VALID_GEOMETRY_INVENTORY" if not errors else "BLOCKED_INVALID_INPUT",
              "feature_count": len(data["features"]), "valid_record_count": len(records),
              "geometry_types": dict(sorted(types.items())), "errors": errors,
              "disconnected_features": disconnected, "crs": parsed_crs.to_string(), "crs_origin": origin,
              "geometry_edition": descriptor.get("geometry_edition"), "population_edition": descriptor.get("population_edition"),
              "provenance": descriptor.get("provenance"), "unit_kind": descriptor.get("unit_kind"),
              "valid_records_only_province_counts": dict(sorted(counts.items())),
              "valid_records_only_province_population": {c: str(p) for c, p in sorted(totals.items())}}
    return report, records, parsed_crs


def compare_maps(old_path, old_descriptor, new_path, new_descriptor, expected_editions=(2022, 2025), area_epsilon_m2=0.01):
    """Matrices de solapamiento; no fuerza parejas uno a uno ni atribuye causas."""
    import shapely
    import pyproj
    from shapely.ops import transform, unary_union
    from shapely.strtree import STRtree
    from pyproj import Transformer
    if not math.isfinite(area_epsilon_m2) or area_epsilon_m2 < 0:
        raise ValueError("AREA_EPSILON_INVALID")
    reports = []; sets = []; crs_list = []; blockers = []
    for path, descriptor, expected in zip((old_path, new_path), (old_descriptor, new_descriptor), expected_editions, strict=True):
        report, records, crs = inspect_geojson(path, descriptor)
        reports.append(report); sets.append(records); crs_list.append(crs)
        if descriptor.get("file_sha256") != report["file_sha256"]:
            blockers.append("SOURCE_HASH_MISSING_OR_MISMATCH")
        for role in ("geometry_edition", "population_edition"):
            if type(descriptor.get(role)) is not int or descriptor[role] != expected:
                blockers.append(f"EDITION_NOT_ACCREDITED_OR_INCOMPATIBLE: {role}")
        provenance = descriptor.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("accredited") is not True or not isinstance(provenance.get("evidence"), list) or not provenance["evidence"] or any(not isinstance(e, str) or not e.strip() for e in provenance["evidence"]):
            blockers.append("PROVENANCE_NOT_ACCREDITED")
        if report["errors"]:
            blockers.append("INVALID_GEOMETRY_OR_IDENTITY_OR_DISCONTINUITY")
    if not old_descriptor.get("scope") or old_descriptor.get("scope") != new_descriptor.get("scope"):
        blockers.append("SCOPE_INCOMPATIBLE")
    if not old_descriptor.get("unit_kind") or old_descriptor.get("unit_kind") != new_descriptor.get("unit_kind"):
        blockers.append("GEOGRAPHIC_UNIT_INCOMPATIBLE")
    result = {"metadata": metadata(), "status": "NOT_COMPARABLE" if blockers else "COMPARABLE",
              "blockers": sorted(set(blockers)), "input_reports": reports,
              "expected_editions": list(expected_editions), "pairs": None, "coverage": None,
              "population_differences": None, "cause_attribution": "UNACCREDITED_NO_AUTOMATIC_ATTRIBUTION"}
    if blockers:
        return result
    projected = []
    for records, crs in zip(sets, crs_list, strict=True):
        converter = Transformer.from_crs(crs, "EPSG:3035", always_xy=True, allow_ballpark=False)
        projected.append({key: transform(converter.transform, record["geometry"]) for key, record in records.items()})
    for geometries in projected:
        if any(not g.is_valid or g.area <= 0 or not math.isfinite(g.area) for g in geometries.values()):
            raise ValueError("PROJECTED_GEOMETRY_INVALID")
    unions = [unary_union(list(geoms.values())) for geoms in projected]
    internal_overlap = [sum(g.area for g in geoms.values()) - union.area for geoms, union in zip(projected, unions, strict=True)]
    if any(value > area_epsilon_m2 for value in internal_overlap):
        result.update(status="NOT_COMPARABLE", blockers=["OVERLAPPING_DISTRICTS_INSIDE_INPUT"])
        return result
    new_ids = sorted(projected[1]); tree = STRtree([projected[1][key] for key in new_ids]); pairs = []
    for left in sorted(projected[0]):
        a = projected[0][left]
        for index in sorted(tree.query(a)):
            right = new_ids[int(index)]; b = projected[1][right]; intersection = a.intersection(b).area
            if intersection <= area_epsilon_m2:
                continue
            symmetric = a.symmetric_difference(b).area
            pairs.append({"old_id": left, "new_id": right, "same_identifier": left == right,
                          "intersection_m2": intersection, "old_coverage": intersection/a.area, "new_coverage": intersection/b.area,
                          "jaccard": intersection/(a.area+b.area-intersection), "symmetric_difference_m2": symmetric,
                          "equivalent_geometry_within_epsilon": symmetric <= area_epsilon_m2,
                          "province_codes_equal": sets[0][left]["province"] == sets[1][right]["province"],
                          "boundary_change_cause": "NO_BOUNDARY_DIFFERENCE_WITHIN_EPSILON" if symmetric <= area_epsilon_m2 else "UNACCREDITED"})
    intersection = unions[0].intersection(unions[1]).area
    stable = old_descriptor.get("stable_identity_accredited") is True and new_descriptor.get("stable_identity_accredited") is True and bool(old_descriptor.get("identity_namespace")) and old_descriptor.get("identity_namespace") == new_descriptor.get("identity_namespace")
    common = sorted(set(sets[0]) & set(sets[1]))
    result.update(pairs=pairs, metric_crs="EPSG:3035", area_epsilon_m2=area_epsilon_m2,
                  runtime={"shapely": shapely.__version__, "GEOS": shapely.geos_version_string, "pyproj": pyproj.__version__, "PROJ": pyproj.proj_version_str},
                  identifier_intersection=common, conserved_identities=common if stable else None,
                  only_old_identifiers=sorted(set(sets[0])-set(sets[1])), only_new_identifiers=sorted(set(sets[1])-set(sets[0])),
                  coverage={"intersection_m2": intersection, "old_union_m2": unions[0].area, "new_union_m2": unions[1].area,
                            "old_covered_by_new": intersection/unions[0].area, "new_covered_by_old": intersection/unions[1].area,
                            "symmetric_difference_m2": unions[0].symmetric_difference(unions[1]).area,
                            "national_completeness_accredited": False},
                  population_differences={"old_total": str(sum((r["population"] for r in sets[0].values()), Decimal(0))),
                                          "new_total": str(sum((r["population"] for r in sets[1].values()), Decimal(0))),
                                          "stable_identity_deltas": {key: str(sets[1][key]["population"]-sets[0][key]["population"]) for key in common} if stable else None})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path); parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--old-descriptor", required=True, type=Path); parser.add_argument("--new-descriptor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = compare_maps(args.old, json.loads(args.old_descriptor.read_text()), args.new, json.loads(args.new_descriptor.read_text()))
    with args.output.open("x", encoding="utf-8") as target:
        target.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)+"\n")
    print(result["status"])


if __name__ == "__main__":
    main()
