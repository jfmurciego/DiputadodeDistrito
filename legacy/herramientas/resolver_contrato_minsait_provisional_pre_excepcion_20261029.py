#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

SCHEMA = "ddd-minsait-provisional-contracts/1.0"
DEFAULT_PATH = Path("configuracion/contratos_minsait_provisionales.yaml")


def resolve(
    *,
    election_id: str,
    territory_id: str,
    election_date: str,
    root_dir: Path = Path("."),
    contract_path: Path = DEFAULT_PATH,
) -> dict:
    path = root_dir / contract_path
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("schema") != SCHEMA:
        raise ValueError(f"Schema de contratos Minsait inválido: {raw.get('schema')!r}")
    row = (raw.get("contracts") or {}).get(election_id)
    if row is None:
        raise KeyError(election_id)

    required = {
        "territory_id", "election_date", "source_status", "production_eligible",
        "promotion_allowed", "publisher", "source_url", "source_sha256",
        "expected", "reconciliation",
    }
    missing = sorted(required - set(row))
    if missing:
        raise ValueError(f"Contrato Minsait incompleto {election_id}: {missing}")
    if str(row["territory_id"]) != territory_id:
        raise ValueError(
            f"Contrato Minsait de otro territorio: {row['territory_id']} != {territory_id}"
        )
    if str(row["election_date"]) != election_date:
        raise ValueError(
            f"Contrato Minsait de otra fecha: {row['election_date']} != {election_date}"
        )
    if bool(row["production_eligible"]) or bool(row["promotion_allowed"]):
        raise ValueError("Un contrato Minsait provisional no puede ser promocionable")

    expected = row["expected"] or {}
    for key in ("ccaa", "provinces", "sections", "polling_stations", "candidate_votes"):
        if expected.get(key) in (None, ""):
            raise ValueError(f"Contrato Minsait sin expected.{key}: {election_id}")

    reconciliation = row["reconciliation"] or {}
    definitive = reconciliation.get("definitive") or {}
    for key in ("publisher", "url", "candidate_votes"):
        if definitive.get(key) in (None, ""):
            raise ValueError(f"Contrato Minsait sin reconciliation.definitive.{key}: {election_id}")
    delta = int(definitive["candidate_votes"]) - int(expected["candidate_votes"])
    declared_delta = int(reconciliation.get("delta_definitive_minus_provisional"))
    if delta != declared_delta:
        raise ValueError(
            f"Delta de reconciliación inválido para {election_id}: {declared_delta} != {delta}"
        )

    return {
        "election_id": election_id,
        **row,
        "expected": {
            "ccaa": str(expected["ccaa"]).zfill(2),
            "provinces": int(expected["provinces"]),
            "sections": int(expected["sections"]),
            "polling_stations": int(expected["polling_stations"]),
            "candidate_votes": int(expected["candidate_votes"]),
        },
        "reconciliation": {
            **reconciliation,
            "definitive": {
                **definitive,
                "candidate_votes": int(definitive["candidate_votes"]),
            },
            "delta_definitive_minus_provisional": declared_delta,
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--election-id", required=True)
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--election-date", required=True)
    ap.add_argument("--root-dir", type=Path, default=Path("."))
    ap.add_argument("--contract-path", type=Path, default=DEFAULT_PATH)
    ap.add_argument("--output", type=Path)
    ns = ap.parse_args()
    try:
        payload = resolve(
            election_id=ns.election_id,
            territory_id=ns.territory_id,
            election_date=ns.election_date,
            root_dir=ns.root_dir,
            contract_path=ns.contract_path,
        )
    except KeyError:
        raise SystemExit(3)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        ns.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
