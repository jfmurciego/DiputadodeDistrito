"""Fail-closed byte receipt for independent CNIG/IGN administrative boundaries.

This is a receipt *candidate*, not historical validity, domain accreditation,
provincial audit, production permission, or a network downloader.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
import zipfile

TARGET_DATE = "2025-01-01"
OFFICIAL_HOSTS = {"centrodedescargas.cnig.es", "www.ign.es", "ign.es", "www.cnig.es", "cnig.es", "api-features.ign.es"}
OFFICIAL_PRODUCTS = {"LILIM", "BDLJE"}
FORMATS = {".shp", ".gml", ".gpkg"}
SINGLE_FILE_FORMATS = {".gpkg", ".gml"}

MAX_MEMBER_COUNT = 100000
MAX_EXPANDED_BYTES = 8 * 1024**3
BLOCKED_STATE = "PENDING_INDEPENDENT_HISTORICAL_ACREDITATION"


def _parse_date(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError("DATE_REQUIRED:" + field)
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as error:
        raise ValueError("DATE_INVALID:" + field) from error


def _official_url(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("OFFICIAL_SOURCE_URL_REQUIRED")
    url = urlparse(value)
    if url.scheme != "https" or (url.hostname or "").lower() not in OFFICIAL_HOSTS:
        raise ValueError("SOURCE_NOT_OFFICIAL_CNIG_OR_IGN_HTTPS")
    if url.username or url.password or url.fragment:
        raise ValueError("SOURCE_URL_HAS_FORBIDDEN_COMPONENT")
    return value


def _safe_zip_members(archive: zipfile.ZipFile) -> list[dict]:
    members = archive.infolist()
    if not members or len(members) > MAX_MEMBER_COUNT:
        raise ValueError("SOURCE_ZIP_MEMBER_COUNT_INVALID")
    expanded = 0
    seen = set()
    rows = []
    for member in members:
        name = member.filename
        path = PurePosixPath(name)
        # No extraction takes place, but reject path-traversal manifests anyway.
        if (not name or "\\" in name or name.startswith("/") or
                any(part in ("", ".", "..") for part in path.parts)):
            raise ValueError("UNSAFE_ZIP_MEMBER_NAME")
        if name in seen:
            raise ValueError("SOURCE_ZIP_MEMBER_DUPLICATE")
        seen.add(name)
        if member.flag_bits & 0x1:
            raise ValueError("SOURCE_ENCRYPTED_MEMBER_UNSUPPORTED")
        if member.is_dir():
            continue
        expanded += member.file_size
        if expanded > MAX_EXPANDED_BYTES:
            raise ValueError("SOURCE_ZIP_EXPANSION_LIMIT")
        rows.append({"name": name, "bytes_uncompressed": member.file_size,
                     "crc32": f"{member.CRC:08x}"})
    if not rows or not any(PurePosixPath(row["name"]).suffix.lower() in FORMATS for row in rows):
        raise ValueError("SOURCE_VECTOR_LAYER_NOT_FOUND")
    if archive.testzip() is not None:
        raise ValueError("SOURCE_ZIP_CRC_MISMATCH")
    return rows


def prepare_candidate_receipt(archive_path: Path, metadata: dict) -> dict:
    """Prove only file bytes and declared provenance; NEVER elevate accreditation."""
    if not isinstance(metadata, dict):
        raise ValueError("SOURCE_METADATA_REQUIRED")
    fields = ("authority", "product", "edition_issued_on", "source_url", "license",
              "acquired_at", "intended_valid_at")
    for field in fields:
        if not isinstance(metadata.get(field), str) or not metadata[field].strip():
            raise ValueError("SOURCE_METADATA_REQUIRED:" + field)
    if metadata["authority"] != "CNIG/IGN" or metadata["product"] not in OFFICIAL_PRODUCTS:
        raise ValueError("INDEPENDENT_BOUNDARY_AUTHORITY_REQUIRED")
    official_url = _official_url(metadata["source_url"])
    edition = _parse_date(metadata["edition_issued_on"], "edition_issued_on")
    if _parse_date(metadata["intended_valid_at"], "intended_valid_at") != TARGET_DATE:
        raise ValueError("CNIG_HISTORICAL_TARGET_MISMATCH")
    try:
        acquired = datetime.fromisoformat(metadata["acquired_at"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("ACQUISITION_TIMESTAMP_INVALID") from error
    if acquired.tzinfo is None:
        raise ValueError("ACQUISITION_TIMEZONE_REQUIRED")
    path = Path(archive_path)
    if not path.is_file() or not path.is_symlink() and not path.stat().st_size:
        raise ValueError("SOURCE_BYTES_ABSENT")
    if path.is_symlink():
        raise ValueError("SOURCE_SYMLINK_NOT_ALLOWED")
    size, digest = 0, hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    extension = path.suffix.lower()
    if extension == ".zip":
        try:
            with zipfile.ZipFile(path, "r") as archive:
                members = _safe_zip_members(archive)
        except zipfile.BadZipFile as error:
            raise ValueError("SOURCE_ZIP_INVALID") from error
        vector_layers = [row["name"] for row in members
                         if PurePosixPath(row["name"]).suffix.lower() in FORMATS]
        container_format = "ZIP"
    elif extension in SINGLE_FILE_FORMATS:
        # A file extension is merely a declared format. Check the minimum
        # byte signature before issuing a *candidate* receipt, without
        # treating the file contents or its claimed provenance as certified.
        with path.open("rb") as stream:
            signature = stream.read(4096)
        if extension == ".gpkg" and not signature.startswith(b"SQLite format 3\\x00"):
            raise ValueError("SOURCE_GPKG_MAGIC_INVALID")
        if extension == ".gml" and not signature.lstrip(b"\\xef\\xbb\\xbf \\t\\r\\n").startswith(b"<"):
            raise ValueError("SOURCE_GML_XML_SIGNATURE_INVALID")
        members = []
        vector_layers = [path.name]
        container_format = extension[1:].upper()
    else:
        raise ValueError("SOURCE_CONTAINER_FORMAT_UNSUPPORTED")
    # User metadata and even a valid 2025 edition cannot demonstrate when all
    # administrative limits were legally effective. Manual official review
    # with dated segment evidence is a separate mandatory admission step.
    return {
        "schema": "ddd.cnig-candidate-source-receipt/1.0",
        "task_id": "NAT-C-056",
        "authority_claim": "CNIG/IGN",
        "product_claim": metadata["product"],
        "catalog_url": official_url,
        "source_filename": path.name,
        "edition_issued_on": edition,
        "acquired_at": acquired.astimezone(timezone.utc).isoformat(),
        "license_claim": metadata["license"],
        "requested_valid_at": TARGET_DATE,
        "file_sha256": digest.hexdigest(),
        "file_size_bytes": size,
        "container_format": container_format,
        "archive_vector_layers": vector_layers,
        "zip_member_count": len(members),
        "zip_members": members,
        "official_temporal_evidence_verified": False,
        "official_2025_01_01_snapshot_accredited": False,
        "administrative_code_mapping_verified": False,
        "crs_and_layer_schema_verified": False,
        "independent_review_completed": False,
        "source_status": BLOCKED_STATE,
        "eligible_for_52_province_audits": False,
        "generation_authorized": False,
        "warning": "File checksum verifies bytes, not an authoritative effective-date record or provincial boundaries.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only CNIG archive intake; no accreditation")
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("RECEIPT_OUTPUT_ALREADY_EXISTS:" + str(args.output))
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    receipt = prepare_candidate_receipt(args.archive, metadata)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    # O_EXCL avoids accidental overwrite of previous receipt evidence.
    with args.output.open("xb") as stream:
        stream.write(data)
    print("CNIG_CANDIDATE_BYTES_VERIFIED_ONLY " + receipt["file_sha256"], flush=True)


if __name__ == "__main__":
    main()
