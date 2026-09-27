#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _code(value: object, width: int) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Código territorial vacío")
    try:
        text = str(int(float(text)))
    except ValueError:
        pass
    if not text.isdigit():
        raise ValueError(f"Código territorial no numérico: {value!r}")
    return text.zfill(width)


def build(
    source: Path,
    out: Path,
    *,
    territory_id: str,
    election_id: str,
    election_date: str,
    edition: str,
    expected_sha256: str,
    expected_ccaa: str,
    expected_sections: int,
    expected_polling_stations: int,
    expected_candidate_votes: int,
    source_url: str,
    publisher: str,
    source_status: str = "PROVISIONAL",
) -> dict:
    actual_sha = sha256(source)
    if actual_sha.lower() != expected_sha256.lower():
        raise ValueError(f"SHA-256 Minsait no coincide: {actual_sha}")

    aggregated: dict[tuple[str, str], int] = defaultdict(int)
    sections: set[str] = set()
    polling_stations: set[tuple[str, str]] = set()
    parties: set[str] = set()
    candidate_votes = 0
    raw_rows = 0
    provinces: set[str] = set()

    with source.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {
            "codigo_ccaa", "codigo_provincia", "codigo_municipio",
            "codigo_distrito", "codigo_seccion", "codigo_mesa",
            "partido", "votos",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV Minsait sin columnas requeridas: {sorted(missing)}")

        for row in reader:
            raw_rows += 1
            ccaa = _code(row["codigo_ccaa"], 2)
            if ccaa != expected_ccaa:
                raise ValueError(f"CCAA inesperada: {ccaa} != {expected_ccaa}")
            prov = _code(row["codigo_provincia"], 2)
            muni = _code(row["codigo_municipio"], 3)
            dist = _code(row["codigo_distrito"], 2)
            sec = _code(row["codigo_seccion"], 3)
            mesa = str(row["codigo_mesa"] or "").strip()
            if not mesa:
                raise ValueError("Mesa vacía")
            cusec = prov + muni + dist + sec
            if len(cusec) != 10:
                raise ValueError(f"CUSEC inválido: {cusec}")
            party = str(row["partido"] or row.get("siglas") or row.get("denominacion") or "").strip()
            if not party:
                raise ValueError("Fila sin candidatura")
            votes = int(str(row["votos"] or "0").strip())
            if votes < 0:
                raise ValueError("Votos negativos")

            provinces.add(prov)
            sections.add(cusec)
            polling_stations.add((cusec, mesa))
            parties.add(party)
            aggregated[(cusec, party)] += votes
            candidate_votes += votes

    if len(sections) != expected_sections:
        raise ValueError(f"Secciones Minsait: {len(sections)} != {expected_sections}")
    if len(polling_stations) != expected_polling_stations:
        raise ValueError(
            f"Mesas Minsait: {len(polling_stations)} != {expected_polling_stations}"
        )
    if candidate_votes != expected_candidate_votes:
        raise ValueError(
            f"Votos a candidaturas Minsait: {candidate_votes} != {expected_candidate_votes}"
        )
    if len(provinces) != 8:
        raise ValueError(f"Provincias Minsait: {len(provinces)} != 8")

    out.mkdir(parents=True, exist_ok=True)
    data_dir = out / "data"
    contract_dir = out / "contract"
    data_dir.mkdir(exist_ok=True)
    contract_dir.mkdir(exist_ok=True)

    normalized = data_dir / "resultados_electorales_normalizados.csv"
    with normalized.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["CUSEC_KEY", "party", "votes"], delimiter=";"
        )
        writer.writeheader()
        for (cusec, party), votes in sorted(aggregated.items()):
            writer.writerow({"CUSEC_KEY": cusec, "party": party, "votes": votes})

    dictionary = contract_dir / "party_dictionary.json"
    dictionary.write_text(
        json.dumps(
            {
                "schema_family": "ddd-party-dictionary",
                "schema_version": "1.0.0",
                "unknown_party_policy": "reject",
                "parties": [
                    {
                        "canonical_id": party,
                        "display_name": party,
                        "aliases": [],
                        "classification": "",
                    }
                    for party in sorted(parties)
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    normalized_sha = sha256(normalized)
    contract = contract_dir / "election_contract.json"
    contract_payload = {
        "schema_family": "ddd-election",
        "schema_version": "1.0.0",
        "election_id": election_id,
        "territory_id": territory_id,
        "title": election_id,
        "election_date": election_date,
        "input_mode": "verifiable_file",
        "boundary_independence": True,
        "sources": [
            {
                "path": "data/resultados_electorales_normalizados.csv",
                "sha256": normalized_sha,
                "publisher": publisher,
                "source_url": source_url,
                "source_class": "provisional_mirror",
                "source_status": source_status,
                "production_eligible": False,
                "adapter": {
                    "kind": "long_csv",
                    "separator": ";",
                    "section_field": "CUSEC_KEY",
                    "party_field": "party",
                    "votes_field": "votes",
                },
                "upstream_snapshot": {
                    "adapter": "minsait_csv/1.0",
                    "source_sha256": actual_sha,
                    "codigo_ccaa": expected_ccaa,
                },
            }
        ],
        "party_dictionary": {
            "path": "contract/party_dictionary.json",
            "sha256": sha256(dictionary),
        },
        "reconciliation": {
            "policy": "provisional_source_only",
            "allowed_result_only_sections": [],
            "allowed_map_only_sections": [],
        },
        "source_verification": {
            "status": source_status,
            "production_eligible": False,
            "sections": len(sections),
            "polling_stations": len(polling_stations),
            "raw_rows": raw_rows,
            "records": len(aggregated),
            "candidate_votes": candidate_votes,
            "source_sha256": actual_sha,
        },
    }
    contract.write_text(
        json.dumps(contract_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "schema": "ddd-electoral-package/1.0",
        "decision": "ACQUIRE",
        "adapter": "minsait_csv/1.0",
        "territory_id": territory_id,
        "edition": str(edition),
        "election_id": election_id,
        "election_date": election_date,
        "source_status": source_status,
        "production_eligible": False,
        "selected_source": {
            "path": "data/resultados_electorales_normalizados.csv",
            "sha256": normalized_sha,
            "bytes": normalized.stat().st_size,
            "source_class": "provisional_mirror",
            "source_status": source_status,
            "production_eligible": False,
        },
        "embedded_contract": {
            "election_contract": "contract/election_contract.json",
            "party_dictionary": "contract/party_dictionary.json",
            "contract_sha256": sha256(contract),
            "party_dictionary_sha256": sha256(dictionary),
        },
        "source_sha256": actual_sha,
        "sections": len(sections),
        "polling_stations": len(polling_stations),
        "raw_rows": raw_rows,
        "records": len(aggregated),
        "parties": len(parties),
        "candidate_votes": candidate_votes,
        "provenance": {
            "publisher": publisher,
            "source_url": source_url,
            "source_status": source_status,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--territory-id", required=True)
    ap.add_argument("--election-id", required=True)
    ap.add_argument("--election-date", required=True)
    ap.add_argument("--edition", default="2025")
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--expected-ccaa", required=True)
    ap.add_argument("--expected-sections", type=int, required=True)
    ap.add_argument("--expected-polling-stations", type=int, required=True)
    ap.add_argument("--expected-candidate-votes", type=int, required=True)
    ap.add_argument("--source-url", required=True)
    ap.add_argument("--publisher", required=True)
    ap.add_argument("--source-status", default="PROVISIONAL")
    args = ap.parse_args()
    print(
        json.dumps(
            build(
                args.source,
                args.out,
                territory_id=args.territory_id,
                election_id=args.election_id,
                election_date=args.election_date,
                edition=args.edition,
                expected_sha256=args.expected_sha256,
                expected_ccaa=args.expected_ccaa,
                expected_sections=args.expected_sections,
                expected_polling_stations=args.expected_polling_stations,
                expected_candidate_votes=args.expected_candidate_votes,
                source_url=args.source_url,
                publisher=args.publisher,
                source_status=args.source_status,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
