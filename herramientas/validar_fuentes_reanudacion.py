#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puerta de reutilización de fuentes para reanudaciones modulares.

Valida exclusivamente el paquete ``sources/`` restaurado desde un checkpoint.
Una reanudación sólo puede continuar con REUSE; una copia ausente, de otra
edición o dañada produce BLOCK. Este adaptador no importa ni invoca ningún
descargador y, por diseño, no puede convertir un fallo en ACQUIRE.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from herramientas.politica_reutilizacion_fuentes import resolve_source_action


def _read_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError(f"YAML inválido: {path}")
    return data


def validate_resume_sources(*, params: Path, package: Path, root_dir: Path = Path(".")) -> dict:
    root_dir = root_dir.resolve()
    params_path = params if params.is_absolute() else root_dir / params
    cfg = _read_yaml(params_path)
    territory_id = str((cfg.get("meta") or {}).get("territory_id") or "").strip()
    if not territory_id:
        raise RuntimeError("Fuentes BLOQUEADAS: el contrato no declara meta.territory_id")

    declaration = root_dir / "territorios" / territory_id / "config" / "fuentes_oficiales.yaml"
    if not declaration.is_file():
        raise RuntimeError(f"Fuentes BLOQUEADAS: no existe declaración de fuentes: {declaration}")
    source_cfg = _read_yaml(declaration)
    edition = (source_cfg.get("territory") or {}).get("edition")
    if edition in (None, ""):
        raise RuntimeError("Fuentes BLOQUEADAS: la declaración no especifica territory.edition")
    expected_records = (source_cfg.get("coverage_checks") or {}).get("expected_sections")
    expected_records = int(expected_records) if expected_records not in (None, "") else None

    package_path = package if package.is_absolute() else root_dir / package
    manifest_path = package_path / "manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError(f"Fuentes BLOQUEADAS: checkpoint sin sources/manifest.json: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Fuentes BLOQUEADAS: manifest.json ilegible: {exc}") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("Fuentes BLOQUEADAS: manifest.json no contiene un objeto")

    decision = resolve_source_action(
        prepared_manifest=manifest,
        root=package_path,
        requested_edition=edition,
        official_available=False,
        expected_records=expected_records,
    )
    if decision.get("decision") != "REUSE":
        raise RuntimeError("Fuentes BLOQUEADAS: " + str(decision.get("reason") or "copia no reutilizable"))

    evidence = {
        "schema": "ddd-source-execution/1.0",
        "decision": "REUSE",
        "restored_from_checkpoint": True,
        "edition": str(edition),
        "sha256": manifest["sha256"],
        "bytes": int(manifest["bytes"]),
        "records": int(manifest["records"]),
        "origin": manifest["origin"],
        "acquired_at": manifest["acquired_at"],
    }
    (package_path / "source_execution.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", required=True, type=Path)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--root-dir", default=".", type=Path)
    args = parser.parse_args()
    evidence = validate_resume_sources(params=args.params, package=args.package, root_dir=args.root_dir)
    print(json.dumps(evidence, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
