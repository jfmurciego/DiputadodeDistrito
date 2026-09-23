#!/usr/bin/env python3
"""Registro durable de publicaciones del visor DDD.

Registra productos ya certificados y ensembles ya empaquetados. No calcula
geometrías ni distritos y no despliega GitHub Pages.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from herramientas.preparar_visor_ejecucion import (
    certification_status,
    first,
    production_metadata,
    read_json,
)

SCHEMA = "ddd.viewer-publication-registry/1.0"


def load_registry(path: Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "products": [], "ensembles": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"Schema de registro no soportado: {data.get('schema')}")
    data.setdefault("products", [])
    data.setdefault("ensembles", [])
    return data


def save_registry(path: Path, registry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    registry["products"] = sorted(
        registry.get("products", []),
        key=lambda item: (item.get("territory_id", ""), item.get("kind", ""), str(item.get("run_id", "")), item.get("id", "")),
    )
    registry["ensembles"] = sorted(
        registry.get("ensembles", []),
        key=lambda item: (item.get("territory_id", ""), item.get("ensemble_id", ""), item.get("id", "")),
    )
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def promote_production(registry: dict, production_root: Path, run_id: str) -> bool:
    metadata = production_metadata(production_root)
    audit_path = first(production_root, "*_m06_contiguedad_geometrica.json")
    audit = read_json(audit_path)
    geometric_status = audit.get("decision", "NOT_AUDITED")
    status = metadata["production_status"]
    recorded_status = status.get("territorial_certification_status", status.get("decision"))
    changed = False

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
                f"No se registra M06 no certificado: territorio={metadata['territory_id']} "
                f"run={run_id} technical={technical_status} geometric={geometric_status}"
            )
        entry = {
            "id": f"{stage.lower()}-{safe_id(metadata['territory_id'])}-{safe_id(run_id)}",
            "source_type": "workflow_artifact",
            "kind": kind,
            "territory_id": metadata["territory_id"],
            "territory_label": metadata["territory_label"],
            "run_id": str(run_id),
            "artifact_name": f"ddd-state-{run_id}-{stage}",
            "expected_districts": metadata["expected_districts"],
            "technical_status": technical_status,
            "certification_status": certified,
            "territorial_certification_status": certified,
            "publication_status": "PUBLICABLE",
            "geometric_status": geometric_status,
            "geometric_gate": audit.get("gate_statement"),
            "label": f"{label} · run {run_id}",
        }
        changed = upsert(registry.setdefault("products", []), entry) or changed
    return changed


def _ensemble_summary(root: Path) -> tuple[Path, dict]:
    preferred = sorted(root.rglob("site/data/summary.json"))
    summary_path = preferred[0] if preferred else first(root, "summary.json")
    if not summary_path:
        raise ValueError(f"No se encontró summary.json de ensemble bajo {root}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if not summary.get("territory_id"):
        raise ValueError("El ensemble no identifica territory_id")
    if not summary.get("complete"):
        raise ValueError("No se registra un ensemble incompleto")
    return summary_path, summary


def promote_ensemble(registry: dict, ensemble_root: Path, release_tag: str) -> bool:
    _, summary = _ensemble_summary(ensemble_root)
    territory_id = str(summary["territory_id"])
    ensemble_id = safe_id(release_tag)
    entry = {
        "id": f"ensemble-{safe_id(territory_id)}-{ensemble_id}",
        "source_type": "release",
        "kind": "ensemble",
        "territory_id": territory_id,
        "territory_label": summary.get("territory_label") or territory_id,
        "ensemble_id": ensemble_id,
        "release_tag": release_tag,
        "candidate_count_expected": int(summary.get("candidate_count_expected", 0)),
        "candidate_count_valid": int(summary.get("candidate_count_valid", 0)),
        "publication_status": "PUBLICABLE",
    }
    return upsert(registry.setdefault("ensembles", []), entry)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)

    production = sub.add_parser("promote-production")
    production.add_argument("--production-root", type=Path, required=True)
    production.add_argument("--run-id", required=True)

    ensemble = sub.add_parser("promote-ensemble")
    ensemble.add_argument("--ensemble-root", type=Path, required=True)
    ensemble.add_argument("--release-tag", required=True)

    args = parser.parse_args()
    registry = load_registry(args.registry)
    if args.command == "promote-production":
        changed = promote_production(registry, args.production_root, args.run_id)
    else:
        changed = promote_ensemble(registry, args.ensemble_root, args.release_tag)
    if changed:
        save_registry(args.registry, registry)
    print(json.dumps({"changed": changed, "registry": str(args.registry)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
