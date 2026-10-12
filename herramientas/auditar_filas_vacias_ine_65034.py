#!/usr/bin/env python3
"""Reconstruye filas vacías INE 65034 desde sus partes originales protegidas.

La herramienta es de solo lectura. Requiere los cuatro fragmentos originales
del ZIP y contrasta las identidades con la tabla de auditoría ya conservada.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXPECTED_PART_SHA256 = (
    "5e675666a42207681d62fc4cc412bf6153a6e206de395020f73ad0f56d227cba",
    "bb91e3ba9c02024b845e0448eafb77392006c36a04cf8313200ff091c1a4b7cb",
    "f6efa2619751094b31c2e5346fa4f4a60c37648748d72451048bbe570e19371d",
    "d345be82122d1a461ed725aed2f20300c205c25b72318a08f565d60a4ee5c8ac",
)
EXPECTED_ARCHIVE_SHA256 = "91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3"
EXPECTED_CENSUS_SHA256 = {
    "03": "acbc7a60725e221612c71f9095dd96c0f279919b87b4717b02dadba6eb8eb5d2",
    "12": "25166f2b184e690379eb011798f62e00d19a774974b10804c8f1fbe1b0c91de0",
    "46": "6804ceeecdba53e2c8e2f1bb4fe0bd331cf987ec2c38303c4557a55548120953",
}
EXPECTED_GEOMETRY_2023_SHA256 = {
    "03": "b1ce66fcab1f7b418e1f56bd4ea23d0ab66f460c52707f87efe54854fcaad7cb",
    "12": "886bb1ad78ad7f96d36e6c883eed3a38d43c858b4217c728ad851739a2cd2ff3",
    "46": "4e0597c12ea2be75cf5e630578388c0825fdde97818abe142d155d7d378da58e",
}
EXPECTED_PREPARED_ZIP_SHA256 = "76ffdfc3c11291b7578560cd31b9eeab2e9b8aedc06bdfbd6c763590d6f969d9"
TARGET_PROVINCES = {"03", "12", "46"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def selected_rows(stream: Iterable[str]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return numeric rows and empty rows for the requested INE dimensions."""
    numeric: list[dict[str, str]] = []
    empty: list[dict[str, str]] = []
    reader = csv.DictReader(stream, delimiter="\t")
    required = {"Provincias", "Municipios", "Secciones", "Sexo", "Edad", "Periodo", "Total"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError("El CSV 65034 no contiene las columnas esperadas")
    for row in reader:
        if row["Periodo"].strip() != "2023" or row["Sexo"].strip() != "Total" or row["Edad"].strip() != "Todas las edades":
            continue
        province = row["Provincias"].split(" ", 1)[0].zfill(2)
        if province not in TARGET_PROVINCES:
            continue
        section = row["Secciones"].split(" ", 1)[0]
        municipality = row["Municipios"].split(" ", 1)[0]
        item = {"CUSEC": section, "CUMUN": municipality, "provincia": province,
                "municipio": row["Municipios"].split(" ", 1)[1] if " " in row["Municipios"] else ""}
        (empty if not row["Total"].strip() else numeric).append(item)
    return numeric, empty


def read_reference(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_hash(actual: str, expected: str, label: str) -> None:
    if actual != expected:
        raise ValueError(f"Hash {label} no coincide con el original protegido")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parts-dir", type=Path, required=True, help="inputs/partes con 65034.csv.zip.part00..03")
    parser.add_argument("--reference", type=Path, required=True, help="46_cusec_sin_observacion.csv existente")
    parser.add_argument("--census-dir", type=Path, required=True, help="JSON oficiales Censo 2023 cpro-03/12/46.json")
    parser.add_argument("--geometry-2023-dir", type=Path, required=True, help="GeoJSON oficiales INE 2023 03/12/46.geojson")
    parser.add_argument("--prepared-2025-zip", type=Path, required=True, help="ZIP protegido de geometría 2025")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    payloads = [(args.parts_dir / f"65034.csv.zip.part{i:02d}").read_bytes() for i in range(4)]
    part_hashes = [sha256_bytes(part) for part in payloads]
    if tuple(part_hashes) != EXPECTED_PART_SHA256:
        raise ValueError("Las partes INE 65034 no coinciden con los SHA-256 protegidos")
    archive_bytes = b"".join(payloads)
    archive_hash = sha256_bytes(archive_bytes)
    verify_hash(archive_hash, EXPECTED_ARCHIVE_SHA256, "del ZIP concatenado")
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        with archive.open("65034.csv") as raw:
            import codecs
            stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            numeric, empty = selected_rows(stream)

    reference = read_reference(args.reference)
    expected = {row["CUSEC"]: row for row in reference}
    actual = {row["CUSEC"]: row for row in empty}
    if len(actual) != len(empty) or set(actual) != set(expected):
        raise ValueError(f"Diferencia en filas vacías: original={len(actual)}, referencia={len(expected)}, solo original={sorted(set(actual)-set(expected))}, solo referencia={sorted(set(expected)-set(actual))}")
    for code, row in actual.items():
        ref = expected[code]
        if row["CUMUN"] != ref["CUMUN"] or row["municipio"] != ref["municipio"]:
            raise ValueError(f"Identidad municipio distinta para {code}")

    census_ids: set[str] = set()
    hashes: dict[str, str] = {"prepared_sources_zip": sha256_file(args.prepared_2025_zip)}
    verify_hash(hashes["prepared_sources_zip"], EXPECTED_PREPARED_ZIP_SHA256, "del paquete protegido 2025")
    geometry_2023_ids: set[str] = set()
    geometry_2025_ids: set[str] = set()
    for province in sorted(TARGET_PROVINCES):
        census_path = args.census_dir / f"cpro-{province}.json"
        hashes[f"census_2023_{province}"] = sha256_file(census_path)
        verify_hash(hashes[f"census_2023_{province}"], EXPECTED_CENSUS_SHA256[province], f"Censo 2023 {province}")
        census_doc = json.loads(census_path.read_text(encoding="utf-8"))
        for feature in census_doc["features"]:
            attrs = feature["attributes"]
            census_ids.add(str(attrs.get("cusec_1") or attrs["cusec"]))
        geo23_path = args.geometry_2023_dir / f"{province}.geojson"
        hashes[f"geometry_2023_{province}"] = sha256_file(geo23_path)
        verify_hash(hashes[f"geometry_2023_{province}"], EXPECTED_GEOMETRY_2023_SHA256[province], f"geometría INE 2023 {province}")
        geo23 = json.loads(geo23_path.read_text(encoding="utf-8"))
        geometry_2023_ids.update(str(f["properties"]["CUSEC"]) for f in geo23["features"]
                                 if f["properties"].get("TIPO") == "SECCIONADO")
    with zipfile.ZipFile(args.prepared_2025_zip) as archive:
        for province in sorted(TARGET_PROVINCES):
            path = f"raw/secciones_censales/2025/{province}.geojson"
            doc = json.loads(archive.read(path))
            geometry_2025_ids.update(str(f["properties"]["CUSEC"]) for f in doc["features"]
                                     if f["properties"].get("TIPO") == "SECCIONADO")

    classifications = {}
    for code, row in actual.items():
        classifications[code] = {
            "censo_2023_personas": code in census_ids,
            "geometria_2023_SECCIONADO": code in geometry_2023_ids,
            "geometria_2025_SECCIONADO": code in geometry_2025_ids,
        }
        ref = expected[code]
        observed = classifications[code]
        if (observed["censo_2023_personas"] != (ref["censo_2023_personas"] == "SI")
                or observed["geometria_2023_SECCIONADO"] != (ref["geometria_2023_SECCIONADO"] == "SI")
                or observed["geometria_2025_SECCIONADO"] != (ref["geometria_2025_SECCIONADO"] == "SI")):
            raise ValueError(f"Cruce de ediciones no coincide con evidencia tabular para {code}")

    result = {
        "schema": "ddd.f10-ine-65034-empty-rows-audit/1.0",
        "source": "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv",
        "selection": {"Periodo": "2023", "Sexo": "Total", "Edad": "Todas las edades", "CPRO": sorted(TARGET_PROVINCES)},
        "archive_sha256": archive_hash,
        "cross_reference_sha256": hashes,
        "part_sha256": {f"part{i:02d}": h for i, h in enumerate(part_hashes)},
        "numeric_rows": len(numeric),
        "empty_rows": len(empty),
        "empty_rows_match_reference_exactly": True,
        "classifications_recomputed_from_official_inputs": classifications,
        "counts": {
            "absent_from_census_2023": sum(not value["censo_2023_personas"] for value in classifications.values()),
            "present_in_geometry_2025": sum(value["geometria_2025_SECCIONADO"] for value in classifications.values()),
            "absent_from_geometry_2025": sum(not value["geometria_2025_SECCIONADO"] for value in classifications.values()),
        },
        "rows": sorted(empty, key=lambda row: row["CUSEC"]),
        "note": "Reconstruye vacíos desde el ZIP oficial original y calcula los cruces por identidad con geometría INE 2023, Censo 2023 y seccionado INE 2025. No asigna cero ni infiere causa estadística.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
