#!/usr/bin/env python3
"""Registro durable y verificable de publicaciones del visor DDD.

Los artefactos de Actions sólo pueden actuar como fuente transitoria de una
promoción. El registro definitivo acepta únicamente activos persistentes con
ubicación inmutable e integridad SHA-256 verificable.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import zipfile
from pathlib import Path

from herramientas.preparar_visor_ejecucion import (
    certification_status,
    first,
    production_metadata,
    read_json,
)

SCHEMA = "ddd.viewer-publication-registry/2.0"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_SOURCES = {"release_asset", "repository_blob"}
PRODUCT_KINDS = {"static", "canonical_m06", "canonical_m08"}


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip()).strip("-")
    if not normalized:
        raise ValueError("Identificador vacío")
    return normalized


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "products": [], "ensembles": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    validate_registry(data)
    return data


def _entries(registry: dict) -> list[dict]:
    return list(registry.get("products", [])) + list(registry.get("ensembles", []))


def identity_key(entry: dict) -> tuple[str, str, str]:
    territory = str(entry.get("territory_id") or "")
    kind = str(entry.get("kind") or "")
    if kind == "ensemble":
        identity = str(entry.get("ensemble_id") or "")
    else:
        identity = str(entry.get("run_id") or entry.get("execution_id") or "")
    return territory, kind, identity


def _validate_entry(entry: dict) -> None:
    required = (
        "id",
        "asset_type",
        "source_type",
        "immutable_location",
        "territory_id",
        "sha256",
        "kind",
    )
    missing = [key for key in required if not entry.get(key)]
    if missing:
        raise ValueError(f"{entry.get('id', '<sin id>')}: campos obligatorios ausentes: {missing}")
    if entry["source_type"] not in ALLOWED_SOURCES:
        raise ValueError(
            f"{entry['id']}: source_type definitivo no permitido: {entry['source_type']}; "
            "workflow_artifact sólo puede ser transitorio"
        )
    if not SHA256_RE.fullmatch(str(entry["sha256"])):
        raise ValueError(f"{entry['id']}: SHA-256 inválido")

    kind = entry["kind"]
    if kind == "ensemble":
        if not entry.get("ensemble_id"):
            raise ValueError(f"{entry['id']}: ensemble_id obligatorio")
    elif kind in PRODUCT_KINDS:
        if not (entry.get("run_id") or entry.get("execution_id")):
            raise ValueError(f"{entry['id']}: ejecución obligatoria")
    else:
        raise ValueError(f"{entry['id']}: kind no soportado: {kind}")

    if entry["source_type"] == "release_asset":
        for key in ("asset_id", "asset_name", "release_tag"):
            if entry.get(key) in (None, ""):
                raise ValueError(f"{entry['id']}: {key} obligatorio para release_asset")
        expected = f"github-release-asset://{entry.get('repository')}/{entry['asset_id']}"
        if entry["immutable_location"] != expected:
            raise ValueError(
                f"{entry['id']}: ubicación release no inmutable o inconsistente: "
                f"{entry['immutable_location']} != {expected}"
            )
    elif entry["source_type"] == "repository_blob":
        if not entry.get("blob_sha"):
            raise ValueError(f"{entry['id']}: blob_sha obligatorio para repository_blob")
        expected = f"github-git-blob://{entry.get('repository')}/{entry['blob_sha']}"
        if entry["immutable_location"] != expected:
            raise ValueError(
                f"{entry['id']}: ubicación blob inconsistente: "
                f"{entry['immutable_location']} != {expected}"
            )


def validate_registry(registry: dict) -> None:
    if registry.get("schema") != SCHEMA:
        raise ValueError(f"Schema de registro no soportado: {registry.get('schema')}")
    if not isinstance(registry.get("products", []), list) or not isinstance(registry.get("ensembles", []), list):
        raise ValueError("products y ensembles deben ser listas")

    ids: set[str] = set()
    identities: set[tuple[str, str, str]] = set()
    locations: set[str] = set()
    for entry in _entries(registry):
        _validate_entry(entry)
        entry_id = str(entry["id"])
        if entry_id in ids:
            raise ValueError(f"ID duplicado en registro: {entry_id}")
        ids.add(entry_id)

        identity = identity_key(entry)
        if identity in identities:
            raise ValueError(f"Identidad de publicación duplicada: {identity}")
        identities.add(identity)

        location = str(entry["immutable_location"])
        if location in locations:
            raise ValueError(f"Activo inmutable duplicado en varias entradas: {location}")
        locations.add(location)


def _sorted_registry(registry: dict) -> dict:
    registry = copy.deepcopy(registry)
    registry["products"] = sorted(
        registry.get("products", []),
        key=lambda item: (
            item.get("territory_id", ""),
            item.get("kind", ""),
            str(item.get("run_id") or item.get("execution_id") or ""),
            item.get("id", ""),
        ),
    )
    registry["ensembles"] = sorted(
        registry.get("ensembles", []),
        key=lambda item: (item.get("territory_id", ""), item.get("ensemble_id", ""), item.get("id", "")),
    )
    return registry


def save_registry(path: Path, registry: dict) -> None:
    validate_registry(registry)
    payload = _sorted_registry(registry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upsert_entry(registry: dict, entry: dict) -> None:
    _validate_entry(entry)
    collection_name = "ensembles" if entry["kind"] == "ensemble" else "products"
    collection = registry.setdefault(collection_name, [])
    identity = identity_key(entry)
    matches = [index for index, current in enumerate(collection) if identity_key(current) == identity]
    if len(matches) > 1:
        raise ValueError(f"Registro base ya contiene identidad duplicada: {identity}")
    if matches:
        collection[matches[0]] = copy.deepcopy(entry)
    else:
        collection.append(copy.deepcopy(entry))
    validate_registry(registry)


def make_candidate(registry: dict, entries: list[dict]) -> dict:
    validate_registry(registry)
    candidate = copy.deepcopy(registry)
    for entry in entries:
        upsert_entry(candidate, entry)
    validate_registry(candidate)
    return _sorted_registry(candidate)


def materialized_asset_path(materialized_root: Path, entry: dict) -> Path:
    return materialized_root / safe_id(entry["id"]) / "asset"


def verify_materialized_registry(registry: dict, materialized_root: Path) -> list[dict]:
    validate_registry(registry)
    verified: list[dict] = []
    for entry in _entries(registry):
        asset = materialized_asset_path(materialized_root, entry)
        if not asset.is_file():
            raise FileNotFoundError(f"{entry['id']}: activo ausente en preflight: {asset}")
        observed = sha256_file(asset)
        expected = str(entry["sha256"])
        if observed != expected:
            raise ValueError(
                f"{entry['id']}: SHA-256 no coincide; esperado={expected} observado={observed}"
            )
        asset_type = entry["asset_type"]
        if asset_type in {"territorial_product", "electoral_product"}:
            if not zipfile.is_zipfile(asset):
                raise ValueError(f"{entry['id']}: producto persistente no es ZIP")
            with zipfile.ZipFile(asset) as archive:
                geodata = [
                    name for name in archive.namelist()
                    if name.lower().endswith((".geojson", ".json")) and not name.endswith("/")
                ]
                if len(geodata) != 1:
                    raise ValueError(f"{entry['id']}: ZIP no contiene un único GeoJSON: {geodata}")
        elif asset_type == "ensemble_archive":
            if not zipfile.is_zipfile(asset):
                raise ValueError(f"{entry['id']}: ensemble persistente no es ZIP")
        elif asset_type == "territorial_geojson":
            payload = json.loads(asset.read_text(encoding="utf-8"))
            if payload.get("type") != "FeatureCollection":
                raise ValueError(f"{entry['id']}: GeoJSON histórico inválido")
        else:
            raise ValueError(f"{entry['id']}: asset_type no soportado: {asset_type}")
        verified.append({
            "id": entry["id"],
            "immutable_location": entry["immutable_location"],
            "sha256": observed,
        })
    return verified


def production_descriptors(production_root: Path, run_id: str) -> list[dict]:
    metadata = production_metadata(production_root)
    audit_path = first(production_root, "*_m06_contiguedad_geometrica.json")
    audit = read_json(audit_path)
    geometric_status = audit.get("decision", "NOT_AUDITED")
    status = metadata["production_status"]
    recorded_status = status.get("territorial_certification_status", status.get("decision"))

    descriptors: list[dict] = []
    for stage, pattern, kind, asset_type, label in (
        ("M06", "*_m06_distritos.geojson.zip", "canonical_m06", "territorial_product", "M06 territorial"),
        ("M08", "*_m08_distritos_resultados.geojson.zip", "canonical_m08", "electoral_product", "M08 electoral"),
    ):
        source = first(production_root, pattern)
        if not source:
            continue
        technical_status = recorded_status or ("BLOCK" if geometric_status == "BLOCK" else "UNKNOWN")
        certified = certification_status(technical_status, audit)
        if stage == "M06" and certified not in {"CERTIFIED", "CERTIFIED_WITH_GOVERNED_EXCEPTIONS"}:
            raise ValueError(
                f"No se promueve M06 no certificado: territorio={metadata['territory_id']} "
                f"run={run_id} technical={technical_status} geometric={geometric_status}"
            )
        descriptors.append({
            "id": f"{stage.lower()}-{safe_id(metadata['territory_id'])}-{safe_id(run_id)}",
            "asset_type": asset_type,
            "kind": kind,
            "stage": stage,
            "territory_id": metadata["territory_id"],
            "territory_label": metadata["territory_label"],
            "run_id": str(run_id),
            "expected_districts": metadata["expected_districts"],
            "technical_status": technical_status,
            "certification_status": certified,
            "territorial_certification_status": certified,
            "publication_status": "PUBLICABLE",
            "geometric_status": geometric_status,
            "geometric_gate": audit.get("gate_statement"),
            "label": f"{label} · run {run_id}",
            "local_source": str(source),
        })
    if not descriptors:
        raise ValueError(f"La ejecución {run_id} no contiene M06 ni M08 publicable")
    return descriptors


def _ensemble_summary(root: Path) -> tuple[Path, dict]:
    preferred = sorted(root.rglob("site/data/summary.json"))
    summary_path = preferred[0] if preferred else first(root, "summary.json")
    if not summary_path:
        raise ValueError(f"No se encontró summary.json de ensemble bajo {root}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not summary.get("territory_id"):
        raise ValueError("El ensemble no identifica territory_id")
    if not summary.get("complete"):
        raise ValueError("No se promueve un ensemble incompleto")
    return summary_path, summary


def ensemble_descriptor(ensemble_root: Path, release_tag: str) -> dict:
    _, summary = _ensemble_summary(ensemble_root)
    territory_id = str(summary["territory_id"])
    ensemble_id = safe_id(release_tag)
    return {
        "id": f"ensemble-{safe_id(territory_id)}-{ensemble_id}",
        "asset_type": "ensemble_archive",
        "kind": "ensemble",
        "territory_id": territory_id,
        "territory_label": summary.get("territory_label") or territory_id,
        "ensemble_id": ensemble_id,
        "candidate_count_expected": int(summary.get("candidate_count_expected", 0)),
        "candidate_count_valid": int(summary.get("candidate_count_valid", 0)),
        "publication_status": "PUBLICABLE",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--registry", type=Path, required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--registry", type=Path, required=True)
    verify.add_argument("--materialized-root", type=Path, required=True)
    verify.add_argument("--output", type=Path)

    describe_product = sub.add_parser("describe-production")
    describe_product.add_argument("--production-root", type=Path, required=True)
    describe_product.add_argument("--run-id", required=True)
    describe_product.add_argument("--output", type=Path, required=True)

    describe_ens = sub.add_parser("describe-ensemble")
    describe_ens.add_argument("--ensemble-root", type=Path, required=True)
    describe_ens.add_argument("--release-tag", required=True)
    describe_ens.add_argument("--output", type=Path, required=True)

    candidate = sub.add_parser("candidate")
    candidate.add_argument("--registry", type=Path, required=True)
    candidate.add_argument("--entries", type=Path, required=True)
    candidate.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()

    if args.command == "validate":
        registry = load_registry(args.registry)
        print(json.dumps({"status": "PASS", "entries": len(_entries(registry))}, ensure_ascii=False))
        return

    if args.command == "verify":
        registry = load_registry(args.registry)
        verified = verify_materialized_registry(registry, args.materialized_root)
        payload = {"status": "PASS", "verified": verified}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, ensure_ascii=False))
        return

    if args.command == "describe-production":
        payload = production_descriptors(args.production_root, args.run_id)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return

    if args.command == "describe-ensemble":
        payload = ensemble_descriptor(args.ensemble_root, args.release_tag)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return

    registry = load_registry(args.registry)
    entries = json.loads(args.entries.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("--entries debe contener una lista JSON")
    result = make_candidate(registry, entries)
    save_registry(args.output, result)
    print(json.dumps({"status": "PASS", "entries": len(_entries(result)), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
