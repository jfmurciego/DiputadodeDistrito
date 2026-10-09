#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

SCHEMA = "ddd-special-electoral-acquisitions/1.0"
KINDS = {"official_api_snapshot"}


def load_registry(root_dir: Path) -> dict:
    path = Path(root_dir) / "configuracion" / "adquisiciones_electorales_especiales.yaml"
    if not path.is_file():
        raise ValueError(f"Registro de adquisiciones electorales especiales ausente: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if data.get("schema") != SCHEMA:
        raise ValueError(f"Schema de adquisiciones electorales especiales inválido: {data.get('schema')!r}")
    acquisitions = data.get("acquisitions")
    if not isinstance(acquisitions, dict):
        raise ValueError("acquisitions debe ser un objeto")
    return data


def resolve(
    *,
    root_dir: Path,
    election_id: str,
    territory_id: str,
    election_date: str,
) -> dict | None:
    data = load_registry(root_dir)
    row = (data.get("acquisitions") or {}).get(election_id)
    if row is None:
        return None
    if not isinstance(row, dict):
        raise ValueError(f"Contrato especial inválido para {election_id}")
    expected = {
        "territory_id": territory_id,
        "election_date": election_date,
    }
    for field, value in expected.items():
        if str(row.get(field) or "") != str(value):
            raise ValueError(
                f"Contrato especial {election_id}: {field}={row.get(field)!r} != {value!r}"
            )
    kind = str(row.get("kind") or "")
    if kind not in KINDS:
        raise ValueError(f"kind de adquisición no soportado: {kind!r}")
    provider = str(row.get("provider") or "").strip()
    if not provider:
        raise ValueError("provider de adquisición ausente")
    provider_config = row.get("provider_config")
    if not isinstance(provider_config, dict):
        raise ValueError("provider_config debe ser un objeto")
    if row.get("promotion_allowed") is not True:
        raise ValueError("Una adquisición oficial especializada debe declarar promotion_allowed: true")
    source_status = str(row.get("source_status") or "")
    if source_status != "VERIFIED_OFFICIAL_FINAL":
        raise ValueError(f"source_status especial no promocionable: {source_status!r}")
    return {
        "schema": SCHEMA,
        "election_id": election_id,
        **row,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--election-id", required=True)
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--election-date", required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    row = resolve(
        root_dir=args.root_dir,
        election_id=args.election_id,
        territory_id=args.territory_id,
        election_date=args.election_date,
    )
    if row is None:
        raise SystemExit(3)
    raw = json.dumps(row, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(raw, encoding="utf-8")
    print(raw, end="")


if __name__ == "__main__":
    main()
