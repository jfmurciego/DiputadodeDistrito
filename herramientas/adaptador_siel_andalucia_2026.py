#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

TERRITORY_ID = "andalucia"
ELECTION_ID = "andalucia_parlamento_2026"
ELECTION_DATE = "2026-05-17"
OFFICIAL_CANDIDATE_VOTES = 4_157_539
EXPECTED_SECTIONS = 6_044
SIEL_ELECTION_KEY = 202605
LOCATOR_SHA256 = "13ffb00bbba4403b9e8d072e766e3979c29ac63cfb5cdcdb7b5e91348484ac21"
VALID_PROVINCES = {"04","11","14","18","21","23","29","41"}
SIEL_BASE = "https://ws040.juntadeandalucia.es/siel-api/v1"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def code(value, width: int) -> str:
    raw = str(value or "").strip()
    if not raw or not raw.isdigit():
        raise ValueError(f"Código electoral no numérico: {value!r}")
    return str(int(raw)).zfill(width)


def _read_manifest(snapshot: Path) -> dict:
    path = snapshot / "manifest.json"
    if not path.is_file():
        raise ValueError("Snapshot SIEL sin manifest.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {
        "territory_id": TERRITORY_ID,
        "election_id": ELECTION_ID,
        "election_date": ELECTION_DATE,
        "siel_election_key": SIEL_ELECTION_KEY,
        "source_base": SIEL_BASE,
        "sections": EXPECTED_SECTIONS,
        "candidate_votes_official": OFFICIAL_CANDIDATE_VOTES,
    }
    for key, value in expected.items():
        if data.get(key) != value:
            raise ValueError(f"Identidad SIEL incorrecta {key}: {data.get(key)!r} != {value!r}")
    locator = data.get("section_locator") or {}
    expected_locator = {
        "role": "SECTION_LOCATOR_ONLY",
        "source_class": "PROVISIONAL",
        "sha256": LOCATOR_SHA256,
        "sections": EXPECTED_SECTIONS,
        "votes_consumed": False,
    }
    for key, value in expected_locator.items():
        if locator.get(key) != value:
            raise ValueError(f"Índice SIEL incorrecto {key}: {locator.get(key)!r} != {value!r}")
    return data


def build(
    snapshot: Path,
    out: Path,
    *,
    expected_sections_sha256: str | None = None,
    expected_cera_sha256: str | None = None,
    edition: str = "2025",
) -> dict:
    meta = _read_manifest(snapshot)
    sections_path = snapshot / "andalucia_2026_siel_secciones.csv"
    cera_path = snapshot / "andalucia_2026_siel_cera_provincias.csv"
    if not sections_path.is_file() or not cera_path.is_file():
        raise ValueError("Snapshot SIEL incompleto: faltan secciones o CERA")

    sections_sha = sha256(sections_path)
    cera_sha = sha256(cera_path)
    if sections_sha != str(meta.get("sections_sha256") or ""):
        raise ValueError("Huella de secciones SIEL no coincide con el manifiesto")
    if cera_sha != str(meta.get("cera_sha256") or ""):
        raise ValueError("Huella CERA SIEL no coincide con el manifiesto")
    if expected_sections_sha256 and sections_sha != expected_sections_sha256:
        raise ValueError("Huella gobernada de secciones SIEL modificada")
    if expected_cera_sha256 and cera_sha != expected_cera_sha256:
        raise ValueError("Huella gobernada CERA SIEL modificada")

    aggregates: dict[tuple[str, str], int] = {}
    sections: set[str] = set()
    parties: set[str] = set()
    geographic_votes = 0
    vote_rows = 0
    with sections_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"province","municipality","district","section","party","votes"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV SIEL de secciones sin columnas requeridas: {reader.fieldnames}")
        for row in reader:
            prov = code(row["province"], 2)
            if prov not in VALID_PROVINCES:
                raise ValueError(f"Provincia ajena a Andalucía: {prov}")
            mun = code(row["municipality"], 3)
            dist = code(row["district"], 2)
            sec = code(row["section"], 3)
            cusec = prov + mun + dist + sec
            if len(cusec) != 10:
                raise ValueError(f"CUSEC inválido: {cusec}")
            party = str(row["party"] or "").strip()
            if not party:
                raise ValueError(f"Fila SIEL sin candidatura: {row}")
            votes = int(row["votes"] or 0)
            if votes < 0:
                raise ValueError(f"Votos negativos: {row}")
            key = (cusec, party)
            aggregates[key] = aggregates.get(key, 0) + votes
            sections.add(cusec)
            parties.add(party)
            geographic_votes += votes
            vote_rows += 1

    if not sections or not aggregates or geographic_votes <= 0:
        raise ValueError("Snapshot SIEL no contiene resultados geográficos válidos")
    if len(sections) != int(meta.get("sections") or 0):
        raise ValueError(f"Secciones SIEL: {len(sections)} != manifiesto {meta.get('sections')}")
    if vote_rows != int(meta.get("vote_rows") or 0):
        raise ValueError(f"Filas SIEL: {vote_rows} != manifiesto {meta.get('vote_rows')}")
    if geographic_votes != int(meta.get("candidate_votes_sections") or 0):
        raise ValueError(
            f"Votos geográficos SIEL: {geographic_votes} != manifiesto {meta.get('candidate_votes_sections')}"
        )

    cera_party_totals: dict[str, int] = {}
    cera_total = 0
    with cera_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"province","party","votes"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV SIEL CERA sin columnas requeridas: {reader.fieldnames}")
        for row in reader:
            prov = code(row["province"], 2)
            if prov not in VALID_PROVINCES:
                raise ValueError(f"Provincia CERA ajena a Andalucía: {prov}")
            party = str(row["party"] or "").strip()
            if not party:
                raise ValueError(f"Fila CERA sin candidatura: {row}")
            votes = int(row["votes"] or 0)
            if votes < 0:
                raise ValueError(f"Votos CERA negativos: {row}")
            cera_party_totals[party] = cera_party_totals.get(party, 0) + votes
            parties.add(party)
            cera_total += votes

    if cera_total != int(meta.get("candidate_votes_cera") or 0):
        raise ValueError(f"CERA SIEL: {cera_total} != manifiesto {meta.get('candidate_votes_cera')}")
    if geographic_votes + cera_total != OFFICIAL_CANDIDATE_VOTES:
        raise ValueError(
            f"Reconciliación SIEL/BOJA: geográfico={geographic_votes} + CERA={cera_total} "
            f"!= oficial={OFFICIAL_CANDIDATE_VOTES}"
        )
    controls = meta.get("province_controls") or {}
    if len(controls) != 8 or not all(bool(x.get("reconciles")) for x in controls.values()):
        raise ValueError("Controles provinciales SIEL incompletos o no reconciliados")

    data_dir = out / "data"
    contract_dir = out / "contract"
    data_dir.mkdir(parents=True, exist_ok=True)
    contract_dir.mkdir(parents=True, exist_ok=True)

    normalized = data_dir / "resultados_electorales_normalizados.csv"
    with normalized.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["CUSEC_KEY","party","votes"], delimiter=";")
        writer.writeheader()
        for (cusec, party), votes in sorted(aggregates.items()):
            writer.writerow({"CUSEC_KEY": cusec, "party": party, "votes": votes})

    dictionary = contract_dir / "party_dictionary.json"
    dictionary.write_text(
        json.dumps(
            {
                "schema_family": "ddd-party-dictionary",
                "schema_version": "1.0.0",
                "unknown_party_policy": "reject",
                "parties": [
                    {"canonical_id": p, "display_name": p, "aliases": [], "classification": ""}
                    for p in sorted(parties)
                ],
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    contract = contract_dir / "election_contract.json"
    contract_payload = {
        "schema_family": "ddd-election",
        "schema_version": "1.0.0",
        "election_id": ELECTION_ID,
        "territory_id": TERRITORY_ID,
        "title": "Elecciones al Parlamento de Andalucía 2026",
        "election_date": ELECTION_DATE,
        "input_mode": "verifiable_file",
        "boundary_independence": True,
        "sources": [
            {
                "path": "data/resultados_electorales_normalizados.csv",
                "sha256": sha256(normalized),
                "publisher": "Junta de Andalucía — Sistema de Información Electoral de Andalucía (SIEL)",
                "source_url": SIEL_BASE,
                "adapter": {
                    "kind": "long_csv",
                    "separator": ";",
                    "section_field": "CUSEC_KEY",
                    "party_field": "party",
                    "votes_field": "votes",
                },
                "upstream_snapshot": {
                    "sections_sha256": sections_sha,
                    "cera_sha256": cera_sha,
                },
            }
        ],
        "party_dictionary": {
            "path": "contract/party_dictionary.json",
            "sha256": sha256(dictionary),
        },
        "reconciliation": {
            "policy": "fail_unless_declared",
            "allowed_result_only_sections": [],
            "allowed_map_only_sections": [],
        },
        "source_verification": {
            "status": "VERIFIED_EXACT",
            "official_reference": meta.get("official_reference"),
            "official_candidate_votes": OFFICIAL_CANDIDATE_VOTES,
            "geographic_candidate_votes": geographic_votes,
            "cera_candidate_votes": cera_total,
            "sections": len(sections),
            "province_controls_match": True,
        },
        "non_geocodable_votes": {
            "policy": "exclude_from_geographic_district_allocation",
            "kind": "CERA",
            "candidate_votes": cera_total,
            "official_candidate_votes": OFFICIAL_CANDIDATE_VOTES,
            "percentage_of_candidate_votes": (100.0 * cera_total / OFFICIAL_CANDIDATE_VOTES),
            "party_totals": cera_party_totals,
        },
    }
    contract.write_text(json.dumps(contract_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    normalized_sha = sha256(normalized)
    manifest = {
        "schema": "ddd-electoral-package/1.0",
        "decision": "ACQUIRE",
        "adapter": "siel_andalucia_snapshot/1.0",
        "territory_id": TERRITORY_ID,
        "edition": str(edition),
        "election_id": ELECTION_ID,
        "election_date": ELECTION_DATE,
        "source_status": "VERIFIED_OFFICIAL_FINAL",
        "snapshot": {
            "sections_sha256": sections_sha,
            "cera_sha256": cera_sha,
        },
        "source_sha256": normalized_sha,
        "sections": len(sections),
        "records": len(aggregates),
        "parties": len(parties),
        "geographic_candidate_votes": geographic_votes,
        "cera_candidate_votes": cera_total,
        "official_candidate_votes": OFFICIAL_CANDIDATE_VOTES,
        "selected_source": {
            "path": "data/resultados_electorales_normalizados.csv",
            "publisher": "Junta de Andalucía — Sistema de Información Electoral de Andalucía (SIEL)",
            "url": SIEL_BASE,
            "sha256": normalized_sha,
            "bytes": normalized.stat().st_size,
            "records": len(aggregates),
            "record_count_method": "csv_rows_excluding_header",
            "source_class": "official_primary",
            "source_verification_status": "VERIFIED_EXACT",
        },
        "embedded_contract": {
            "election_contract": "contract/election_contract.json",
            "party_dictionary": "contract/party_dictionary.json",
            "contract_sha256": sha256(contract),
            "party_dictionary_sha256": sha256(dictionary),
        },
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--sections-sha256")
    ap.add_argument("--cera-sha256")
    ap.add_argument("--edition", default="2025")
    args = ap.parse_args()
    print(
        json.dumps(
            build(
                args.snapshot,
                args.out,
                expected_sections_sha256=args.sections_sha256,
                expected_cera_sha256=args.cera_sha256,
                edition=args.edition,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
