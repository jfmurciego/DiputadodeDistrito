#!/usr/bin/env python3
"""Genera nombres técnicos reproducibles desde composiciones M06 existentes.

VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Cabecera dominante auditable
FECHA: 2026-09-13
ESTADO: activo C-12
CAMBIOS: implementación inicial sin datos electorales ni modificación de M06.
MOTIVO: recuperar nombres estables, explicables y verificables para cada distrito.
ANTERIOR: ninguno — herramienta nueva.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


FORBIDDEN = {"party", "partido", "vote", "voto", "candidatura", "escanos", "seats"}


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def roman(number):
    values = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    result = []
    for value, symbol in values:
        while number >= value:
            result.append(symbol)
            number -= value
    return "".join(result)


def build_names(territory, composition_path, threshold=0.5):
    totals = defaultdict(int)
    municipalities = defaultdict(lambda: defaultdict(int))
    metadata = {}
    with Path(composition_path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fields = {field.lower() for field in (reader.fieldnames or [])}
        forbidden = sorted(fields & FORBIDDEN)
        if forbidden:
            raise ValueError(f"campos partidistas prohibidos: {forbidden}")
        for row in reader:
            district = int(row["district_id"])
            population_text = row.get("section_pop") or row.get("POP_2025")
            if population_text is None:
                raise ValueError("falta población de sección")
            population = int(float(population_text))
            municipality_code = str(row["CUMUN"])
            municipality_name = str(row["NMUN"]).strip()
            province_code = str(row["CPRO"]).zfill(2)
            province_name = str(row["NPRO"]).strip()
            totals[district] += population
            municipalities[district][(municipality_code, municipality_name)] += population
            metadata.setdefault(district, (province_code, province_name))

    preliminary = []
    for district in sorted(totals):
        ranked = sorted(
            municipalities[district].items(),
            key=lambda item: (-item[1], item[0][0], item[0][1].casefold()),
        )
        (municipality_code, municipality_name), dominant_population = ranked[0]
        share = dominant_population / totals[district]
        province_code, province_name = metadata[district]
        if share >= threshold:
            base = f"{province_name} — {municipality_name}"
            rule = "DOMINANT_MUNICIPALITY"
        else:
            base = f"{province_name} — Entorno de {municipality_name}"
            rule = "RURAL_REFERENCE_MUNICIPALITY"
        preliminary.append({
            "territory": territory,
            "district_id": district,
            "province_code": province_code,
            "province_name": province_name,
            "dominant_municipality_code": municipality_code,
            "dominant_municipality_name": municipality_name,
            "dominant_population": dominant_population,
            "district_population": totals[district],
            "dominant_population_share": round(share, 12),
            "naming_rule": rule,
            "base_name": base,
        })

    groups = defaultdict(list)
    for row in preliminary:
        groups[row["base_name"]].append(row)
    for rows in groups.values():
        rows.sort(key=lambda row: row["district_id"])
        for index, row in enumerate(rows, 1):
            row["district_name"] = (
                row["base_name"] if len(rows) == 1
                else f"{row['base_name']} {roman(index)}"
            )
    return preliminary


def generate(config_path):
    root = Path(__file__).resolve().parents[1]
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    if config.get("partisan_fields_allowed") is not False:
        raise ValueError("el contrato debe prohibir campos partidistas")
    rows = []
    inputs = {}
    for territory, relative in sorted(config["territories"].items()):
        path = root / relative
        rows.extend(build_names(territory, path, config["dominant_municipality_threshold"]))
        inputs[territory] = {"path": relative, "sha256": file_hash(path)}
    rows.sort(key=lambda row: (row["territory"], row["district_id"]))
    out_csv = root / config["output_csv"]
    out_report = root / config["output_report"]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with out_csv.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    report = {
        "schema_version": "1.0.0",
        "algorithm_version": config["algorithm_version"],
        "config": str(Path(config_path)),
        "inputs": inputs,
        "districts": len(rows),
        "unique_names": len({row["district_name"] for row in rows}),
        "partisan_fields_used": [],
        "output_csv": config["output_csv"],
    }
    out_report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rows, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    rows, report = generate(args.config)
    if report["districts"] != report["unique_names"]:
        raise SystemExit("los nombres no son únicos")
    print(f"C-12 nombres={len(rows)} únicos={report['unique_names']}")


if __name__ == "__main__":
    main()
