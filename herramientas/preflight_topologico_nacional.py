#!/usr/bin/env python3
"""VERSIÓN 1.0.1; NOMBRE preflight nacional N08; FECHA 2026-10-12.
ALCANCE: 52 unidades, fuentes protegidas, diagnóstico sin M04–M06 reales.
ESTADO: candidato; CAMBIOS/MOTIVO: hashes persistidos antes de reutilizar checkpoints.
ANTERIOR: legacy/herramientas/preflight_topologico_nacional_v1.0.0.py.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import platform
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
import geopandas as gpd
import numpy as np
import pyogrio
import shapely
from ddd_core.congreso_contract import validate_congress_identity
from ddd_core.congreso_topology import analyze_unit, digest

BASE = "b583c52128daa85c14de9def0c9a3cb7d5f5e92e"


def bytes_hash(data): return hashlib.sha256(data).hexdigest()


def json_bytes(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(data); os.replace(temporary, path)


def read_checkpoint(output, run_binding):
    """Fail closed on stale, missing or contradictory checkpoint ledgers.

    Old un-hashed checkpoints remain archival evidence, not reusable state.
    An orphan written before a crash requires explicit fresh recomputation or
    independent auditing; it is never silently trusted by its own run_binding.
    """
    path = output / "checkpoint.json"
    if not path.exists():
        if list((output / "unidades").glob("*.json.gz")):
            raise ValueError("CHECKPOINT_LEDGER_MISSING")
        return {"schema": "ddd.congress-topology-checkpoint/1.1", "run_binding": run_binding,
                "completed_codes": [], "artifacts": {}, "generation_authorized": False}
    ledger = json.loads(path.read_bytes())
    if ledger.get("schema") != "ddd.congress-topology-checkpoint/1.1":
        raise ValueError("CHECKPOINT_HASH_LEDGER_REQUIRED")
    if ledger.get("run_binding") != run_binding: raise ValueError("STALE_CHECKPOINT_LEDGER")
    codes = ledger.get("completed_codes")
    records = ledger.get("artifacts")
    if (not isinstance(codes, list) or len(set(codes)) != len(codes)
            or any(code not in {f"{i:02d}" for i in range(1, 53)} for code in codes)
            or not isinstance(records, dict) or set(records) != {f"unidades/{code}.json.gz" for code in codes}
            or ledger.get("generation_authorized") is not False):
        raise ValueError("CHECKPOINT_LEDGER_INVALID")
    for code in codes:
        artifact = output / "unidades" / f"{code}.json.gz"
        if not artifact.is_file(): raise ValueError("CHECKPOINT_ARTIFACT_MISSING:" + code)
        read_unit_checkpoint(artifact, records[f"unidades/{code}.json.gz"], run_binding)
    return ledger


def read_unit_checkpoint(artifact, record, run_binding):
    data = artifact.read_bytes()
    if (not isinstance(record, dict) or record.get("sha256") != bytes_hash(data)
            or record.get("bytes") != len(data)):
        raise ValueError("CHECKPOINT_ARTIFACT_HASH_MISMATCH:" + artifact.name)
    raw = gzip.decompress(data)
    if record.get("canonical_json_sha256") != bytes_hash(raw):
        raise ValueError("CHECKPOINT_CONTENT_HASH_MISMATCH:" + artifact.name)
    product = json.loads(raw)
    if raw != json_bytes(product): raise ValueError("CHECKPOINT_NON_CANONICAL:" + artifact.name)
    if product.get("run_binding") != run_binding: raise ValueError("STALE_CHECKPOINT:" + artifact.name)
    return product


def load_inputs(parts_dir, root=ROOT):
    """Reassemble protected original ZIP in RAM; preserve every member's bytes.

    GDAL fails on the archived accented directory name in this environment.
    Only names are flattened in an ephemeral in-memory reader ZIP; shapefile,
    DBF, SHX and PRJ bytes and all coordinates remain exactly the originals.
    """
    source_dir = root / "territorios/congreso/fuentes/ine_2025_2025"
    source_bytes = (source_dir / "manifest.json").read_bytes()
    manifest = json.loads(source_bytes)
    identity = manifest.pop("manifest_identity_sha256")
    if bytes_hash(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()) != identity:
        raise ValueError("SOURCE_MANIFEST_IDENTITY_MISMATCH")
    manifest["manifest_identity_sha256"] = identity
    contract_bytes = (root / "territorios/congreso/contrato_congreso_2026.json").read_bytes()
    contract = json.loads(contract_bytes); validate_congress_identity(contract)
    if contract["accreditation"]["generation_authorized"] is not False: raise ValueError("GENERATION_MUST_REMAIN_FALSE")
    for role in ("geometry", "population"):
        if contract["sources"][role]["sha256"] != manifest["sources"][role]["sha256"]:
            raise ValueError("CONTRACT_SOURCE_HASH_MISMATCH")
        if contract["sources"][role]["year"] != 2025: raise ValueError("SOURCE_EDITION_MISMATCH")
    for name, record in manifest["outputs"].items():
        data = (source_dir / name).read_bytes()
        if bytes_hash(data) != record["sha256"]: raise ValueError("SOURCE_OUTPUT_HASH_MISMATCH:" + name)
    part_records = manifest["sources"]["geometry"]["part_sha256"]
    payload_parts = []
    for name, expected in sorted(part_records.items()):
        data = (parts_dir / name).read_bytes()
        if bytes_hash(data) != expected: raise ValueError("PROTECTED_PART_HASH_MISMATCH:" + name)
        payload_parts.append(data)
    payload = b"".join(payload_parts)
    source_hash = bytes_hash(payload)
    if source_hash != contract["sources"]["geometry"]["sha256"]: raise ValueError("PROTECTED_ZIP_HASH_MISMATCH")
    reader_zip = io.BytesIO(); member_hashes = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive, zipfile.ZipFile(reader_zip, "w") as reader:
        if archive.testzip() is not None: raise ValueError("PROTECTED_ZIP_CRC_MISMATCH")
        shapes = [name for name in archive.namelist() if name.lower().endswith(".shp")]
        if len(shapes) != 1: raise ValueError("SOURCE_LAYER_COUNT")
        stem = shapes[0].rsplit(".", 1)[0]
        for name in archive.namelist():
            if name.rsplit(".", 1)[0] == stem:
                data = archive.read(name); member_hashes[name] = bytes_hash(data)
                reader.writestr("sectioning." + name.rsplit(".", 1)[1].lower(), data)
    frame = pyogrio.read_dataframe(reader_zip.getvalue())
    if frame.crs is None or frame.crs.to_epsg() != 25830: raise ValueError("CRS_MISMATCH")
    if frame.CUSEC.duplicated().any() or len(frame) != 36554: raise ValueError("CUSEC_COVERAGE_MISMATCH")
    if not frame.geometry.is_valid.all() or frame.geometry.is_empty.any() or frame.geometry.isna().any():
        raise ValueError("ORIGINAL_GEOMETRY_INVALID")
    if not frame.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).all(): raise ValueError("GEOMETRY_TYPE_INVALID")
    geo_hashes = {str(row.CUSEC): bytes_hash(row.geometry.wkb) for row in frame.itertuples()}
    geometry_identity = bytes_hash(json.dumps(geo_hashes, sort_keys=True).encode())
    if geometry_identity != manifest["geometry"]["geometry_identity_sha256"]: raise ValueError("GEOMETRY_IDENTITY_MISMATCH")
    with (source_dir / "poblacion_por_seccion_2025.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 36554 or len({r["CUSEC"] for r in rows}) != 36554: raise ValueError("POPULATION_COVERAGE_MISMATCH")
    population = {r["CUSEC"]: r for r in rows}
    if set(population) != set(frame.CUSEC): raise ValueError("EXACT_CUSEC_JOIN_MISMATCH")
    for row in frame.itertuples():
        ref = population[row.CUSEC]
        for field in ("CUSEC", "CPRO", "CUMUN", "CMUN", "CDIS", "CSEC"):
            if str(getattr(row, field)) != ref[field]: raise ValueError("ADMIN_ATTRIBUTE_MISMATCH:" + field)
        if row.CUSEC[:2] != row.CPRO or row.CUMUN[:2] != row.CPRO: raise ValueError("ADMIN_PREFIX_MISMATCH")
    frame["POB_2025"] = frame.CUSEC.map(lambda uid: int(population[uid]["POB_2025"]))
    if int(frame.POB_2025.sum()) != 49128297: raise ValueError("NATIONAL_POPULATION_MISMATCH")
    quotas = {r["code"]: r["k"] for r in contract["quotas_by_origin_unit"]}
    actual = {str(code): max(1, (int(group.POB_2025.sum()) + 60000) // 120000) for code, group in frame.groupby("CPRO")}
    if actual != quotas or len(quotas) != 52 or sum(quotas.values()) != 407: raise ValueError("APPROVED_QUOTA_MISMATCH")
    binding = {role: {"edition": 2025, "sha256": contract["sources"][role]["sha256"]} for role in ("geometry", "population")}
    return frame.sort_values("CUSEC", kind="mergesort").reset_index(drop=True), contract, {
        "source_binding": binding, "source_manifest_sha256": bytes_hash(source_bytes),
        "contract_sha256": bytes_hash(contract_bytes), "geometry_identity_sha256": geometry_identity,
        "original_member_sha256": member_hashes, "reader_operation": "names_only_flattened_in_memory; bytes_unchanged",
        "geometry_operations": "none; no CRS transform, buffer, simplify, repair or precision rounding in physical graph"}


def cross_province_contacts(frame):
    """Audit partition boundaries without admitting any interprovincial edge."""
    geoms = frame.geometry.to_numpy(); codes = frame.CPRO.to_numpy(); ids = frame.CUSEC.to_numpy()
    pairs = shapely.STRtree(geoms).query(geoms, predicate="intersects")
    pairs = pairs[:, (pairs[0] < pairs[1]) & (codes[pairs[0]] != codes[pairs[1]])]
    pairs = pairs[:, np.lexsort((pairs[1], pairs[0]))]
    result = []
    for start in range(0, pairs.shape[1], 2048):
        i, j = pairs[:, start:start + 2048]
        borders = shapely.intersection(shapely.boundary(geoms[i]), shapely.boundary(geoms[j]))
        lengths = shapely.length(borders); areas = shapely.area(shapely.intersection(geoms[i], geoms[j]))
        for a, b, line, length, area in zip(i, j, borders, lengths, areas):
            result.append({"u": str(ids[a]), "v": str(ids[b]), "CPRO_u": str(codes[a]), "CPRO_v": str(codes[b]),
                           "shared_border_m": float(length), "overlap_m2": float(area),
                           "contact_sha256": bytes_hash(line.wkb), "excluded_from_graph": True})
    return result


def run(parts_dir, output, root=ROOT, *, resume=False):
    frame, contract, evidence = load_inputs(parts_dir, root)
    versions = {"python": platform.python_version(), "shapely": shapely.__version__, "geos": shapely.geos_version_string,
                "geopandas": gpd.__version__, "pyogrio": pyogrio.__version__, "numpy": np.__version__}
    code_hashes = {name: bytes_hash((root / name).read_bytes()) for name in
                   ("ddd_core/congreso_topology.py", "herramientas/preflight_topologico_nacional.py")}
    run_binding = digest({"sources": evidence, "software": versions, "implementation": code_hashes})
    output.mkdir(parents=True, exist_ok=True)
    ledger = read_checkpoint(output, run_binding) if resume else {
        "schema": "ddd.congress-topology-checkpoint/1.1", "run_binding": run_binding,
        "completed_codes": [], "artifacts": {}, "generation_authorized": False}
    cached_records = dict(ledger["artifacts"])
    summaries, artifact_records = [], {}
    for code in sorted(frame.CPRO.unique()):
        artifact = output / "unidades" / f"{code}.json.gz"
        if artifact.exists():
            if not resume: raise FileExistsError("CHECKPOINT_EXISTS_USE_EXPLICIT_RESUME:" + str(artifact))
            if f"unidades/{code}.json.gz" not in cached_records:
                raise ValueError("UNIT_WITHOUT_CHECKPOINT_RECORD:" + code)
            product = read_unit_checkpoint(artifact, cached_records[f"unidades/{code}.json.gz"], run_binding)
        else:
            k = next(r["k"] for r in contract["quotas_by_origin_unit"] if r["code"] == code)
            product = analyze_unit(frame.loc[frame.CPRO == code].copy(), k, evidence["source_binding"]["geometry"]["sha256"])
            product["run_binding"] = run_binding
            atomic(artifact, gzip.compress(json_bytes(product), mtime=0))
        summaries.append(product["summary"])
        data = artifact.read_bytes()
        artifact_records[f"unidades/{code}.json.gz"] = {"sha256": bytes_hash(data), "bytes": len(data),
                                                       "canonical_json_sha256": bytes_hash(json_bytes(product))}
        ledger = {"schema": "ddd.congress-topology-checkpoint/1.1", "run_binding": run_binding,
                  "completed_codes": sorted(set(ledger["completed_codes"]) | {r["CPRO"] for r in summaries}),
                  "artifacts": {**cached_records, **artifact_records}, "generation_authorized": False}
        atomic(output / "checkpoint.json", json_bytes(ledger))
        print(json.dumps(product["summary"], ensure_ascii=False), flush=True)
    cross = cross_province_contacts(frame)
    cross_path = output / "contactos_interprovinciales.json.gz"
    data = gzip.compress(json_bytes(cross), mtime=0); atomic(cross_path, data)
    artifact_records[cross_path.name] = {"sha256": bytes_hash(data), "bytes": len(data), "canonical_json_sha256": bytes_hash(json_bytes(cross))}
    manifest = {"schema": "ddd.congress-topology-diagnostic/1.0", "date": "2026-10-12", "base": BASE,
                "run_binding": run_binding, "evidence": evidence, "software": versions, "implementation": code_hashes,
                "sections": sum(r["sections"] for r in summaries), "population": sum(r["population"] for r in summaries),
                "k": sum(r["k"] for r in summaries), "origin_units": len(summaries), "edges": sum(r["edges"] for r in summaries),
                "section_graph_components": sum(r["section_graph_components"] for r in summaries),
                "physical_part_components": sum(r["physical_part_components"] for r in summaries),
                "interprovincial_edges": 0, "interprovincial_contacts_excluded": len(cross),
                "interprovincial_overlap_pairs": sum(r["overlap_m2"] > 0 for r in cross),
                "artifacts": artifact_records, "inventory": summaries, "generation_authorized": False,
                "operational_graph": "NO_BRIDGES; identical to physical section graph; no approval inferred",
                "gates": {"A_diagnostic_coverage": "PASS", "A_topological_integrity": "BLOCKED" if any(r["overlap_pairs"] for r in summaries) or any(r["overlap_m2"] > 0 for r in cross) else "NOT_EVIDENCED",
                          "B_first_pilot_feasibility": "NOT_EVIDENCED", "C_productive_authorization": "BLOCKED"}}
    manifest["identity_sha256"] = digest(manifest)
    atomic(output / "manifest.json", json_bytes(manifest))
    print("N08_DIAGNOSTIC_COMPLETE " + json.dumps({k: manifest[k] for k in ("sections", "population", "k", "edges", "physical_part_components")}), flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Diagnóstico N08, nunca generación")
    parser.add_argument("--parts-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true", help="Sólo checkpoints ligados a mismos bytes/código/software")
    args = parser.parse_args(); run(args.parts_dir, args.output, resume=args.resume)


if __name__ == "__main__": main()
