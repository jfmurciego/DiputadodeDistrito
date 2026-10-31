#!/usr/bin/env python3
"""Fuente oficial Infoelectoral por mesa (Ministerio del Interior) para la 03.

PROYECTO: Diputado de Distrito
VERSIÓN: 1.0.0 · FECHA: 2026-10-30 · ESTADO: candidato
QUÉ HACE: resuelve el contrato gobernado de ``configuracion/contratos_infoelectoral.yaml`` y convierte
  el ZIP oficial ``{tipo}{AAAA}{MM}_MESA.zip`` (ficheros 09 de mesa, 10 de votos por candidatura y 03 de
  candidaturas, ancho fijo ISO-8859-1) en el CSV largo por mesa que consume el adaptador común
  (``adaptador_minsait_csv.py``). Excluye el CERA (municipio 999), que no tiene sección, y exige que
  mesas, secciones, candidaturas, votos, blancos, nulos y votantes cuadren con el contrato.
MOTIVO: piloto Congreso Huesca; resultados oficiales definitivos del Congreso 23-07-2023 por mesa.
ANTERIOR: ninguno (herramienta nueva).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from collections import defaultdict
from pathlib import Path

import yaml

SCHEMA = "ddd-infoelectoral-contracts/1.0"
DEFAULT_PATH = Path("configuracion/contratos_infoelectoral.yaml")
CERA_MUNICIPALITY = "999"
OUTPUT_FIELDS = (
    "codigo_ccaa", "codigo_provincia", "codigo_municipio", "codigo_distrito",
    "codigo_seccion", "codigo_mesa", "partido", "votos",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve(*, election_id: str, territory_id: str, election_date: str,
            root_dir: Path = Path("."), contract_path: Path = DEFAULT_PATH) -> dict:
    raw = yaml.safe_load((root_dir / contract_path).read_text(encoding="utf-8")) or {}
    if raw.get("schema") != SCHEMA:
        raise ValueError(f"Schema de contratos Infoelectoral inválido: {raw.get('schema')!r}")
    row = (raw.get("contracts") or {}).get(election_id)
    if row is None:
        raise KeyError(election_id)
    required = {"territory_id", "election_date", "publisher", "source_url", "source_sha256",
                "election_prefix", "files", "province", "expected"}
    missing = sorted(required - set(row))
    if missing:
        raise ValueError(f"Contrato Infoelectoral incompleto {election_id}: {missing}")
    if str(row["territory_id"]) != territory_id or str(row["election_date"]) != election_date:
        raise ValueError(f"Contrato Infoelectoral de otra identidad: {election_id}")
    expected = row["expected"] or {}
    for key in ("ccaa", "sections", "polling_stations", "candidate_votes", "blank_votes",
                "null_votes", "voters", "parties"):
        if expected.get(key) in (None, ""):
            raise ValueError(f"Contrato Infoelectoral sin expected.{key}: {election_id}")
    if int(expected["candidate_votes"]) + int(expected["blank_votes"]) + int(expected["null_votes"]) != int(expected["voters"]):
        raise ValueError(f"Totales incoherentes en el contrato Infoelectoral: {election_id}")
    official = row.get("official_totals") or {}
    cera = official.get("cera") or {}
    if official and cera:
        pairs = (("candidate_votes_total", "candidate_votes", "candidate_votes"), ("blank_votes_total", "blank_votes", "blank_votes"),
                 ("null_votes_total", "null_votes", "null_votes"), ("voters_total", "voters", "voters"))
        for total_key, cera_key, expected_key in pairs:
            if int(official[total_key]) - int(cera[cera_key]) != int(expected[expected_key]):
                raise ValueError(f"Totales oficiales menos CERA no cuadran con expected.{expected_key}: {election_id}")
    return {"election_id": election_id, **row}


def _records(archive: zipfile.ZipFile, member: str):
    with archive.open(member) as fh:
        for raw in fh:
            line = raw.decode("iso-8859-1").rstrip("\r\n")
            if line:
                yield line


def _int(line: str, start: int, end: int) -> int:
    return int(line[start - 1:end].strip() or "0")


def convert(zip_path: Path, contract: dict, out_csv: Path) -> dict:
    """Convierte el ZIP oficial en CSV largo por mesa y devuelve el resumen verificado."""
    actual_sha = _sha256(zip_path)
    if actual_sha != str(contract["source_sha256"]).lower():
        raise ValueError(f"SHA-256 del ZIP Infoelectoral no coincide: {actual_sha}")
    prefix = str(contract["election_prefix"])
    province = str(contract["province"]).zfill(2)
    files = contract["files"]
    expected = contract["expected"]

    def mesa_key(line: str) -> tuple[str, str, str, str, str]:
        section = line[18:22].strip()
        if not section.isdigit():
            raise ValueError(f"Sección no numérica en registro Infoelectoral: {line[:30]!r}")
        return (line[11:13], line[13:16], line[16:18], f"{int(section):03d}", line[22:23])

    with zipfile.ZipFile(zip_path) as archive:
        names = {}
        for line in _records(archive, files["candidaturas"]):
            if line.startswith(prefix[:8]):
                names[line[8:14]] = line[14:64].strip()

        mesas: dict[tuple, dict[str, int]] = {}
        ccaa_seen: set[str] = set()
        cera = {"records": 0, "blank_votes": 0, "null_votes": 0, "candidate_votes": 0}
        for line in _records(archive, files["mesas"]):
            if not line.startswith(prefix) or line[11:13] != province:
                continue
            blank, null, candidates = _int(line, 66, 72), _int(line, 73, 79), _int(line, 80, 86)
            if line[13:16] == CERA_MUNICIPALITY:
                cera["records"] += 1
                cera["blank_votes"] += blank
                cera["null_votes"] += null
                cera["candidate_votes"] += candidates
                continue
            key = mesa_key(line)
            if key in mesas:
                raise ValueError(f"Mesa duplicada en fichero 09: {key}")
            ccaa_seen.add(line[9:11])
            mesas[key] = {"census": _int(line, 24, 30), "blank_votes": blank,
                          "null_votes": null, "candidate_votes": candidates}

        votes: dict[tuple, dict[str, int]] = defaultdict(dict)
        for line in _records(archive, files["candidaturas_mesa"]):
            if not line.startswith(prefix) or line[11:13] != province or line[13:16] == CERA_MUNICIPALITY:
                continue
            key = mesa_key(line)
            if key not in mesas:
                raise ValueError(f"Votos de una mesa ausente del fichero 09: {key}")
            code = line[23:29]
            if code not in names:
                raise ValueError(f"Candidatura sin siglas en fichero 03: {code}")
            if code in votes[key]:
                raise ValueError(f"Candidatura repetida en la mesa {key}: {code}")
            votes[key][code] = _int(line, 30, 36)

    mismatched = [k for k, row in mesas.items() if sum(votes.get(k, {}).values()) != row["candidate_votes"]]
    if mismatched:
        raise ValueError(f"{len(mismatched)} mesas con votos 10 distintos de candidaturas 09; p. ej. {mismatched[0]}")
    if ccaa_seen != {str(expected["ccaa"]).zfill(2)}:
        raise ValueError(f"CCAA inesperada en el fichero 09: {sorted(ccaa_seen)}")

    summary = {
        "polling_stations": len(mesas),
        "sections": len({k[:4] for k in mesas}),
        "candidate_votes": sum(r["candidate_votes"] for r in mesas.values()),
        "blank_votes": sum(r["blank_votes"] for r in mesas.values()),
        "null_votes": sum(r["null_votes"] for r in mesas.values()),
        "parties": len({code for row in votes.values() for code in row}),
    }
    summary["voters"] = summary["candidate_votes"] + summary["blank_votes"] + summary["null_votes"]
    for key, value in summary.items():
        if int(expected[key]) != value:
            raise ValueError(f"Infoelectoral {key}: {value} != {expected[key]} (contrato)")
    if "cera_records" in expected and int(expected["cera_records"]) != cera["records"]:
        raise ValueError(f"Registros CERA: {cera['records']} != {expected['cera_records']}")

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for key in sorted(votes):
            prov, muni, dist, sec, mesa = key
            for code in sorted(votes[key]):
                writer.writerow({
                    "codigo_ccaa": str(expected["ccaa"]).zfill(2), "codigo_provincia": prov,
                    "codigo_municipio": muni, "codigo_distrito": dist, "codigo_seccion": sec,
                    "codigo_mesa": mesa, "partido": names[code], "votos": votes[key][code],
                })
    return {"schema": "ddd.infoelectoral-conversion/1.0", "election_id": contract["election_id"],
            "source_sha256": actual_sha, "province": province, **summary, "cera_excluded": cera,
            "csv_sha256": _sha256(out_csv)}


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    rs = sub.add_parser("resolve")
    cv = sub.add_parser("convert")
    for p in (rs, cv):
        p.add_argument("--election-id", required=True)
        p.add_argument("--territory-id", required=True)
        p.add_argument("--election-date", required=True)
        p.add_argument("--root-dir", type=Path, default=Path("."))
        p.add_argument("--output", type=Path)
    cv.add_argument("--zip", type=Path, required=True)
    cv.add_argument("--csv", type=Path, required=True)
    ns = ap.parse_args()
    try:
        contract = resolve(election_id=ns.election_id, territory_id=ns.territory_id,
                           election_date=ns.election_date, root_dir=ns.root_dir)
    except KeyError:
        raise SystemExit(3)
    payload = contract if ns.cmd == "resolve" else convert(ns.zip, contract, ns.csv)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if ns.output:
        ns.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
