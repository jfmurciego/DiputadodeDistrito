#!/usr/bin/env python3
"""Registro durable y verificable de publicaciones del visor DDD.

El registro sólo admite activos persistentes. Los artefactos temporales de
GitHub Actions pueden ser fuente de promoción, nunca referencia definitiva.
Toda actualización se valida completa, incluida la referencia candidata,
antes de sustituir atómicamente el registro anterior.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from herramientas.preparar_visor_ejecucion import (
    certification_status,
    first,
    production_metadata,
    read_json,
)

SCHEMA = "ddd.viewer-publication-registry/1.1"
PERSISTENT_SOURCE_TYPES = {"release_asset", "repository_commit"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "products": [], "ensembles": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"Schema de registro no soportado: {data.get('schema')}")
    data.setdefault("products", [])
    data.setdefault("ensembles", [])
    return data


def _sorted_registry(registry: dict) -> dict:
    result = copy.deepcopy(registry)
    result["schema"] = SCHEMA
    result["products"] = sorted(
        result.get("products", []),
        key=lambda item: (
            item.get("territory_id", ""),
            item.get("kind", ""),
            str(item.get("run_id", "")),
            item.get("id", ""),
        ),
    )
    result["ensembles"] = sorted(
        result.get("ensembles", []),
        key=lambda item: (
            item.get("territory_id", ""),
            item.get("ensemble_id", ""),
            item.get("id", ""),
        ),
    )
    return result


def save_registry_atomic(path: Path, registry: dict) -> None:
    payload = json.dumps(_sorted_registry(registry), ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def upsert(collection: list[dict], entry: dict) -> bool:
    for index, current in enumerate(collection):
        if current.get("id") == entry.get("id"):
            if current == entry:
                return False
            collection[index] = entry
            return True
    collection.append(entry)
    return True


def safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value).strip()).strip("-")
    if not normalized:
        raise ValueError("Identificador vacío")
    return normalized


def _immutable_release_location(repository: str, tag: str, asset_name: str) -> str:
    return f"github-release://{repository}/{tag}/{asset_name}"


def _candidate_entry(entry: dict) -> dict:
    result = {key: value for key, value in entry.items() if key != "local_source"}
    return result


def build_production_candidates(production_root: Path, run_id: str, repository: str) -> list[dict]:
    metadata = production_metadata(production_root)
    audit_path = first(production_root, "*_m06_contiguedad_geometrica.json")
    audit = read_json(audit_path)
    geometric_status = audit.get("decision", "NOT_AUDITED")
    status = metadata["production_status"]
    recorded_status = status.get("territorial_certification_status", status.get("decision"))
    candidates: list[dict] = []

    for stage, pattern, kind, label in (
        ("M06", "*_m06_distritos.geojson.zip", "canonical_m06", "M06 territorial"),
        ("M08", "*_m08_distritos_resultados.geojson.zip", "canonical_m08", "M08 electoral"),
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
        digest = sha256_file(source)
        territory = safe_id(metadata["territory_id"])
        run = safe_id(run_id)
        stage_lower = stage.lower()
        tag = f"viewer-product-{territory}-{run}-{stage_lower}-{digest[:16]}"
        asset_name = f"{territory}-{run}-{stage_lower}-{digest}.zip"
        candidates.append({
            "id": f"{stage_lower}-{territory}-{run}",
            "source_type": "release_asset",
            "kind": kind,
            "territory_id": metadata["territory_id"],
            "territory_label": metadata["territory_label"],
            "run_id": str(run_id),
            "release_tag": tag,
            "asset_name": asset_name,
            "immutable_location": _immutable_release_location(repository, tag, asset_name),
            "sha256": digest,
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
    return candidates


def _ensemble_summary(root: Path) -> dict:
    preferred = sorted(root.rglob("site/data/summary.json"))
    summary_path = preferred[0] if preferred else first(root, "summary.json")
    if not summary_path:
        raise ValueError(f"No se encontró summary.json de ensemble bajo {root}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not summary.get("territory_id"):
        raise ValueError("El ensemble no identifica territory_id")
    if not summary.get("complete"):
        raise ValueError("No se registra un ensemble incompleto")
    return summary


def build_ensemble_candidate(
    ensemble_root: Path,
    release_tag: str,
    asset_path: Path,
    repository: str,
) -> dict:
    summary = _ensemble_summary(ensemble_root)
    if not asset_path.is_file():
        raise FileNotFoundError(asset_path)
    territory_id = str(summary["territory_id"])
    ensemble_id = safe_id(release_tag)
    digest = sha256_file(asset_path)
    return {
        "id": f"ensemble-{safe_id(territory_id)}-{ensemble_id}",
        "source_type": "release_asset",
        "kind": "ensemble",
        "territory_id": territory_id,
        "territory_label": summary.get("territory_label") or territory_id,
        "ensemble_id": ensemble_id,
        "release_tag": release_tag,
        "asset_name": asset_path.name,
        "immutable_location": _immutable_release_location(repository, release_tag, asset_path.name),
        "sha256": digest,
        "candidate_count_expected": int(summary.get("candidate_count_expected", 0)),
        "candidate_count_valid": int(summary.get("candidate_count_valid", 0)),
        "publication_status": "PUBLICABLE",
        "local_source": str(asset_path),
    }


def validate_entry(entry: dict, *, ensemble: bool = False) -> None:
    required = {
        "id", "source_type", "kind", "territory_id", "asset_name",
        "immutable_location", "sha256",
    }
    required.add("ensemble_id" if ensemble else "run_id")
    missing = sorted(key for key in required if entry.get(key) in (None, ""))
    if missing:
        raise ValueError(f"{entry.get('id', '<sin id>')}: faltan campos durables {missing}")
    if entry["source_type"] not in PERSISTENT_SOURCE_TYPES:
        raise ValueError(
            f"{entry['id']}: source_type temporal/no durable no permitido: {entry['source_type']}"
        )
    digest = str(entry["sha256"]).lower()
    if not SHA256_RE.fullmatch(digest):
        raise ValueError(f"{entry['id']}: sha256 inválido")
    if entry["source_type"] == "release_asset":
        for key in ("release_tag", "asset_name"):
            if not entry.get(key):
                raise ValueError(f"{entry['id']}: falta {key} para release_asset")
    if entry["source_type"] == "repository_commit":
        for key in ("source_commit", "source_path"):
            if not entry.get(key):
                raise ValueError(f"{entry['id']}: falta {key} para repository_commit")


def materialized_asset(entry: dict, materialized_root: Path) -> Path:
    return materialized_root / str(entry["id"]) / str(entry["asset_name"])


def verify_registry(registry: dict, materialized_root: Path) -> dict:
    checked = 0
    for collection_name, ensemble in (("products", False), ("ensembles", True)):
        for entry in registry.get(collection_name, []):
            validate_entry(entry, ensemble=ensemble)
            path = materialized_asset(entry, materialized_root)
            if not path.is_file():
                raise FileNotFoundError(f"{entry['id']}: activo persistente ausente: {path}")
            actual = sha256_file(path)
            expected = str(entry["sha256"]).lower()
            if actual != expected:
                raise ValueError(
                    f"{entry['id']}: SHA-256 no coincide: esperado={expected} observado={actual}"
                )
            checked += 1
    return {"checked": checked, "schema": registry.get("schema")}


def proposed_registry(registry: dict, candidates: list[dict]) -> dict:
    proposed = copy.deepcopy(registry)
    for raw in candidates:
        entry = _candidate_entry(raw)
        target = proposed.setdefault("ensembles" if entry.get("kind") == "ensemble" else "products", [])
        upsert(target, entry)
    return _sorted_registry(proposed)


def write_preview(path: Path, registry: dict, candidates: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(proposed_registry(registry, candidates), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def apply_candidates_atomic(
    registry_path: Path,
    candidates: list[dict],
    materialized_root: Path,
) -> bool:
    previous_bytes = registry_path.read_bytes() if registry_path.exists() else None
    current = load_registry(registry_path)
    proposed = proposed_registry(current, candidates)
    verify_registry(proposed, materialized_root)
    serialized = (json.dumps(proposed, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if previous_bytes == serialized:
        return False
    save_registry_atomic(registry_path, proposed)
    return True


def load_candidates(path: Path | None) -> list[dict]:
    if path is None:
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("entries", payload if isinstance(payload, list) else [])
    if not isinstance(candidates, list):
        raise ValueError("Manifest de candidatos inválido")
    return candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    plan = sub.add_parser("plan")
    plan.add_argument("--production-root", type=Path)
    plan.add_argument("--run-id")
    plan.add_argument("--ensemble-root", type=Path)
    plan.add_argument("--ensemble-release-tag")
    plan.add_argument("--ensemble-asset", type=Path)
    plan.add_argument("--repository", required=True)
    plan.add_argument("--output", type=Path, required=True)

    preview = sub.add_parser("preview")
    preview.add_argument("--registry", type=Path, required=True)
    preview.add_argument("--candidate-manifest", type=Path, required=True)
    preview.add_argument("--output", type=Path, required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--registry", type=Path, required=True)
    verify.add_argument("--materialized-root", type=Path, required=True)

    apply = sub.add_parser("apply")
    apply.add_argument("--registry", type=Path, required=True)
    apply.add_argument("--candidate-manifest", type=Path, required=True)
    apply.add_argument("--materialized-root", type=Path, required=True)

    args = parser.parse_args()
    if args.command == "plan":
        entries: list[dict] = []
        if args.production_root:
            if not args.run_id:
                raise SystemExit("--run-id es obligatorio con --production-root")
            entries.extend(build_production_candidates(args.production_root, args.run_id, args.repository))
        if args.ensemble_root:
            if not args.ensemble_release_tag or not args.ensemble_asset:
                raise SystemExit("--ensemble-release-tag y --ensemble-asset son obligatorios")
            entries.append(build_ensemble_candidate(
                args.ensemble_root,
                args.ensemble_release_tag,
                args.ensemble_asset,
                args.repository,
            ))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"schema": "ddd.viewer-promotion-plan/1.0", "entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"planned": len(entries), "output": str(args.output)}, ensure_ascii=False))
    elif args.command == "preview":
        registry = load_registry(args.registry)
        candidates = load_candidates(args.candidate_manifest)
        write_preview(args.output, registry, candidates)
        print(json.dumps({"entries": len(candidates), "output": str(args.output)}, ensure_ascii=False))
    elif args.command == "verify":
        result = verify_registry(load_registry(args.registry), args.materialized_root)
        print(json.dumps(result, ensure_ascii=False))
    else:
        changed = apply_candidates_atomic(
            args.registry,
            load_candidates(args.candidate_manifest),
            args.materialized_root,
        )
        print(json.dumps({"changed": changed, "registry": str(args.registry)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
