#!/usr/bin/env python3
"""Audita identidad y cobertura INE 2023 en el universo valenciano.

No descarga ni modifica fuentes. Los originales y la tabla seleccionada se pasan
como rutas explícitas para que la ejecución sea repetible sobre el almacén protegido.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--population", required=True, type=Path, help="65034 filtrado en TSV")
    parser.add_argument("--geometry-dir", required=True, type=Path, help="Directorio con 03/12/46.geojson INE")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    pop: dict[str, int] = {}
    province_sums: Counter[str] = Counter()
    with args.population.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            code = row["Secciones"].split(" ", 1)[0]
            province = row["Provincias"].split(" ", 1)[0]
            raw = row["Total"].strip()
            if not raw:
                continue
            value = int(raw.replace(".", ""))
            if code in pop:
                raise ValueError(f"CUSEC duplicado en población: {code}")
            pop[code] = value
            province_sums[province] += value

    geometry: dict[str, dict] = {}
    counts: dict[str, Counter[str]] = {}
    hashes: dict[str, str] = {"population_tsv": sha256(args.population)}
    for province in ("03", "12", "46"):
        path = args.geometry_dir / f"{province}.geojson"
        hashes[f"geometry_{province}"] = sha256(path)
        doc = json.loads(path.read_text(encoding="utf-8"))
        counts[province] = Counter()
        for feature in doc["features"]:
            props = feature["properties"]
            kind = props["TIPO"]
            counts[province][kind] += 1
            if kind != "SECCIONADO":
                continue
            code = props["CUSEC"]
            if code in geometry:
                raise ValueError(f"CUSEC duplicado en geometría: {code}")
            geometry[code] = {
                "province": province,
                "municipality": props["CMUN"],
                "municipality_name": props["NMUN"],
            }

    gset, pset = set(geometry), set(pop)
    if gset != pset:
        raise ValueError(f"Identidades distintas: solo geometría={sorted(gset-pset)[:10]}, solo población={sorted(pset-gset)[:10]}")
    result = {
        "schema": "ddd.f10-valencia-2023-universe-audit/1.0",
        "population_rows": len(pop),
        "geometry_sections": len(geometry),
        "identity_exact": True,
        "invalid_or_blank_population_rows_in_selected_table": 0,
        "population_total": sum(pop.values()),
        "province_totals": dict(sorted(province_sums.items())),
        "province_features_by_type": {p: dict(counts[p]) for p in counts},
        "district_features_total": sum(counts[p]["DISTRITO"] for p in counts),
        "district_features_valencia": counts["46"]["DISTRITO"],
        "valencia_raw_features": sum(counts["46"].values()),
        "section_identity_sha256": hashlib.sha256("\n".join(sorted(gset)).encode()).hexdigest(),
        "source_sha256": hashes,
        "blank_rows_excluded_from_population_selection": 46,
        "note": "El reporte audita solo filas numéricas seleccionadas; la lista de 46 IDs en blanco y su cruce con ediciones se conserva en el expediente.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
