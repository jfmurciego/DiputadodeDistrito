#!/usr/bin/env python3
"""Audit candidate physical connectivity on original INE polygon parts.

Version: 1.0.0 (isolated analytical audit; 2026-10-26). No geometry repair,
buffer, simplification, precision rounding, production or publication.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import tempfile
import zipfile
from collections import defaultdict, deque
from pathlib import Path


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _pairs(pairs):
    out = {}
    for key, val in pairs:
        if key in out:
            raise ValueError("JSON_DUPLICATE_KEY:" + key)
        out[key] = val
    return out


def _components(root, expected_zip_sha):
    import geopandas as gpd
    parts_dir = root / "inputs/partes"
    source_manifest = parts_dir / "MANIFEST_PARTES.sha256"
    expected = {}
    for line in source_manifest.read_text(encoding="utf-8").splitlines():
        fields = line.strip().split()
        if len(fields) == 2:
            expected[fields[1].lstrip("*./")] = fields[0]
    source_parts = [parts_dir / f"seccionado_2025.zip.part{i:02d}" for i in range(3)]
    part_hashes = {p.name: sha256_file(p) for p in source_parts}
    if any(expected.get(p.name) != part_hashes[p.name] for p in source_parts):
        raise ValueError("INE_SOURCE_PART_HASH_MISMATCH")
    with tempfile.TemporaryDirectory(prefix="ddd-pilot-geometry-") as tmpdir:
        archive_path = Path(tmpdir) / "seccionado_2025.zip"
        with archive_path.open("wb") as out:
            for src in source_parts:
                with src.open("rb") as inp:
                    for chunk in iter(lambda: inp.read(1024 * 1024), b""):
                        out.write(chunk)
        observed_zip_sha = sha256_file(archive_path)
        if observed_zip_sha != expected_zip_sha:
            raise ValueError("INE_SECTIONING_ARCHIVE_SHA_MISMATCH")
        with zipfile.ZipFile(archive_path) as archive:
            bad = archive.testzip()
            if bad:
                raise ValueError("INE_ZIP_CRC_INVALID:" + bad)
            shps = [n for n in archive.namelist() if n.lower().endswith(".shp")]
            if len(shps) != 1:
                raise ValueError("INE_SHAPEFILE_COUNT_INVALID")
            stem = shps[0].rsplit(".", 1)[0]
            for name in archive.namelist():
                if name.rsplit(".", 1)[0] == stem:
                    suffix = name.rsplit(".", 1)[-1].lower()
                    (Path(tmpdir) / f"sections.{suffix}").write_bytes(archive.read(name))
            shp_path = Path(tmpdir) / "sections.shp"
            frame = gpd.read_file(shp_path)
            sidecar_hashes = {p.name: sha256_file(p) for p in Path(tmpdir).glob("sections.*")}
    if frame.crs is None or frame.crs.to_epsg() != 25830:
        raise ValueError("INE_CRS_MUST_BE_EPSG25830")
    if "CUSEC" not in frame.columns:
        raise ValueError("INE_CUSEC_FIELD_MISSING")
    frame["CUSEC"] = frame["CUSEC"].astype(str)
    return frame, {"archive_sha256": observed_zip_sha, "part_sha256": part_hashes,
                   "extracted_component_sha256": sidecar_hashes, "crs": "EPSG:25830",
                   "source_manifest_sha256": sha256_file(source_manifest)}


def _polygon_parts(geometry):
    from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
    if geometry is None or geometry.is_empty or not geometry.is_valid:
        raise ValueError("INE_GEOMETRY_EMPTY_OR_INVALID")
    if isinstance(geometry, Polygon):
        return [geometry]
    if isinstance(geometry, MultiPolygon):
        return list(geometry.geoms)
    if isinstance(geometry, GeometryCollection):
        polys = [g for g in geometry.geoms if isinstance(g, Polygon)]
        if len(polys) == len(geometry.geoms):
            return polys
    raise ValueError("INE_GEOMETRY_TYPE_UNSUPPORTED:" + geometry.geom_type)


def classify_contact(first, second):
    """Classify original-geometry contact; point/overlap never become edges."""
    intersection_area = first.intersection(second).area
    if intersection_area > 0:
        return {"kind": "OVERLAP", "overlap_area_m2": intersection_area, "shared_border_m": 0.0}
    boundary = first.boundary.intersection(second.boundary)
    if boundary.geom_type in ("LineString", "LinearRing"):
        length = boundary.length
    elif boundary.geom_type in ("MultiLineString", "GeometryCollection"):
        length = sum(g.length for g in boundary.geoms
                     if g.geom_type in ("LineString", "LinearRing"))
    else:
        length = 0.0
    if length > 0:
        return {"kind": "LINEAR", "overlap_area_m2": 0.0, "shared_border_m": length}
    if not boundary.is_empty and boundary.geom_type in ("Point", "MultiPoint"):
        return {"kind": "POINT", "overlap_area_m2": 0.0, "shared_border_m": 0.0}
    return {"kind": "DISJOINT", "overlap_area_m2": 0.0, "shared_border_m": 0.0}


def audit(candidate_path: Path, root: Path, output: Path):
    import geopandas as gpd
    import shapely
    from shapely.strtree import STRtree
    from ddd_core.congreso_constructive_witness import evaluate_unit
    from ddd_core.congreso_pilot_adapter import audit_candidate

    candidate_bytes = candidate_path.read_bytes()
    candidate = json.loads(candidate_bytes, object_pairs_hook=_pairs,
                            parse_constant=lambda x: (_ for _ in ()).throw(ValueError("JSON_NONFINITE:" + x)))
    if (candidate.get("schema") != "ddd.congress-provincial-analytical-candidate/1.0"
            or candidate.get("generation_authorized") is not False
            or candidate.get("product_certification") != "NOT_PERFORMED"):
        raise ValueError("CANDIDATE_CONTRACT_INVALID")
    cpro, k = candidate["cpro"], candidate["k"]
    contract_path = root / "territorios/congreso/contrato_congreso_2026.json"
    contract = json.loads(contract_path.read_text())
    expected_zip_sha = contract["sources"]["geometry"]["sha256"]
    preflight = root / "docs/ESTUDIOS/CAMPANA_NACIONAL_20261013" / f"PREFLIGHT_CPRO{cpro}"
    product_dir = root / "docs/ESTUDIOS/N08_TOPOLOGIA_NACIONAL_20251012/producto"
    unit_path = product_dir / "unidades" / f"{cpro}.json.gz"
    bound = evaluate_unit(preflight_path=preflight / "PREFLIGHT.json",
                          checkpoint_path=preflight / "CHECKPOINT.json",
                          unit_path=unit_path,
                          product_manifest_path=product_dir / "manifest.json",
                          contract_path=contract_path)
    if bound["errors"] or candidate.get("source_binding") != bound["input_sha256"]:
        raise ValueError("CANDIDATE_SOURCE_BINDING_INVALID:" + repr(bound["errors"]))
    with gzip.open(unit_path, "rt", encoding="utf-8") as stream:
        topology = json.load(stream)
    analytical_audit = audit_candidate(candidate, topology, contract,
                                       expected_binding=bound["input_sha256"])
    part_counts = {node["CUSEC"]: len(node["physical_part_components"]) for node in topology["nodes"]}
    frame, source = _components(root, expected_zip_sha)
    frame = frame[frame["CUSEC"].str[:2] == cpro].copy()
    assigned_rows = candidate["districts"]
    assignment = {c: row["id"] for row in assigned_rows for c in row["cusecs"]}
    if len(assignment) != sum(len(row["cusecs"]) for row in assigned_rows):
        raise ValueError("CANDIDATE_DUPLICATE_CUSEC")
    if len(frame) != len(set(frame["CUSEC"])) or set(frame["CUSEC"]) != set(assignment):
        raise ValueError("INE_CUSEC_COVERAGE_MISMATCH")
    frame["district"] = frame["CUSEC"].map(assignment)
    parts, owner, geom_by_id = [], [], {}
    invalid_rows = []
    for _, row in frame.iterrows():
        cusec = row["CUSEC"]
        try:
            geom_parts = _polygon_parts(row.geometry)
        except ValueError as exc:
            invalid_rows.append({"CUSEC": cusec, "reason": str(exc)})
            continue
        for index, geom in enumerate(geom_parts):
            pid = f"{cusec}:p{index:04d}"
            parts.append(geom); owner.append((pid, cusec, assignment[cusec])); geom_by_id[pid] = geom
        if len(geom_parts) != part_counts.get(cusec):
            raise ValueError("INE_POLYGON_PART_COUNT_MISMATCH:" + cusec)
    if invalid_rows:
        raise ValueError("INE_INVALID_GEOMETRIES:" + json.dumps(invalid_rows, ensure_ascii=False))
    tree = STRtree(parts)
    edges_by_district = defaultdict(list)
    point_only, overlap_pairs = [], []
    for i, geom in enumerate(parts):
        pid, cusec, district = owner[i]
        for j in tree.query(geom):
            j = int(j)
            if j <= i:
                continue
            qid, qsec, qdistrict = owner[j]
            if district != qdistrict:
                # Cross-district contacts are informational, not connectivity edges.
                pass
            contact = classify_contact(geom, parts[j])
            if contact["kind"] == "OVERLAP":
                overlap_pairs.append({"part_a": pid, "part_b": qid,
                                      "cusec_a": cusec, "cusec_b": qsec,
                                      "district_a": district, "district_b": qdistrict,
                                      "overlap_area_m2": contact["overlap_area_m2"]})
                continue
            lineal = contact["shared_border_m"]
            if lineal > 0:
                if district == qdistrict:
                    edges_by_district[district].append((pid, qid, lineal))
            elif contact["kind"] == "POINT":
                point_only.append({"part_a": pid, "part_b": qid, "district_a": district,
                                   "district_b": qdistrict})

    districts = {}
    for row in assigned_rows:
        did = row["id"]
        vertices = sorted(pid for pid, sec, d in owner if d == did)
        adj = {v: set() for v in vertices}
        for a, b, length in edges_by_district[did]:
            adj[a].add(b); adj[b].add(a)
        components, seen = [], set()
        for start in vertices:
            if start in seen:
                continue
            seen.add(start); queue = deque([start]); component = []
            while queue:
                u = queue.popleft(); component.append(u)
                for v in sorted(adj[u]):
                    if v not in seen:
                        seen.add(v); queue.append(v)
            components.append(sorted(component))
        districts[did] = {"polygon_parts": len(vertices), "positive_line_edges": len(edges_by_district[did]),
                          "physical_components": len(components), "components": components,
                          "connected": len(components) == 1}
    report = {
        "schema": "ddd.congress-analytical-physical-connectivity/1.0",
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "candidate_canonical_sha256": hashlib.sha256(json.dumps(candidate, sort_keys=True,
                separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest(),
        "source": source, "runtime": {"geopandas": gpd.__version__, "shapely": shapely.__version__,
                   "geos": shapely.geos_version_string},
        "cpro": cpro, "k": k, "sections": len(frame),
        "analytical_audit_sha256": hashlib.sha256(json.dumps(analytical_audit,
                sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest(),
        "polygon_parts": len(parts), "districts": districts,
        "topology_unit_sha256": bound["input_sha256"]["unit_product"],
        "point_only_contacts": point_only, "positive_area_overlap_pairs": overlap_pairs,
        "within_district_part_graph_connected": all(x["connected"] for x in districts.values()),
        "source_geometry_unmodified": True, "buffers_or_repairs": False,
        "generation_authorized": False, "product_certification": "NOT_PERFORMED",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2,
                                 allow_nan=False) + "\n", encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.candidate, args.root, args.output)
    print(json.dumps({"cpro": report["cpro"], "districts": report["districts"],
                      "physical_connected": report["within_district_part_graph_connected"],
                      "point_only": len(report["point_only_contacts"]),
                      "overlaps": len(report["positive_area_overlap_pairs"])}, sort_keys=True))


if __name__ == "__main__":
    main()
