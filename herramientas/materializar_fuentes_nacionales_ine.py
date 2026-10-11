"""Versión 1.0.0; materializar y validar las fuentes nacionales INE 2025.

Alcance: pareja oficial de población por sección y seccionado de circunscripciones.
Estado: candidato; no decide el contrato institucional ni autoriza generación.
Origen: incremento nacional sobre N07; sin predecesor.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Iterable
import sys

import geopandas as gpd
from shapely.validation import explain_validity

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from herramientas.crosswalk_nacional import FIELDS, validate_rows

POPULATION_URL = "https://www.ine.es/jaxiT3/files/t/csv_bdsc/65034.csv"
EXPECTED_TOTAL = 49_128_297
EXPECTED_SECTIONS = 36_554
EXPECTED_SECTIONING_SHA = (
    "55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4"
)
EXPECTED_POPULATION_SHA = (
    "91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3"
)
PROVINCES = {f"{n:02d}" for n in range(1, 53)}
PARTS = {
    "seccionado_2025.zip": 3,
    "65034.csv.zip": 4,
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _int_total(value: str, *, label: str) -> int:
    raw = str(value or "").strip().replace("\u00a0", "").replace(" ", "")
    if not raw or not re.fullmatch(r"(?:\d+|\d{1,3}(?:\.\d{3})+)", raw):
        raise ValueError(f"POPULATION_VALUE_INVALID:{label}:{value!r}")
    return int(raw.replace(".", ""))


def validate_population_rows(
    rows: Iterable[dict[str, str]],
    crosswalk_rows: list[dict[str, str]],
    *,
    expected_counts: dict[str, int],
) -> tuple[dict[str, int], dict]:
    """Independently reduce INE 65034 and join its rows to the N07 universe."""
    crosswalk_by_id: dict[str, dict[str, str]] = {}
    for row in crosswalk_rows:
        key = row.get("CUSEC")
        if key in crosswalk_by_id:
            raise ValueError(f"CROSSWALK_DUPLICATE:{key}")
        crosswalk_by_id[key] = row
    if len(crosswalk_by_id) != EXPECTED_SECTIONS:
        raise ValueError(f"CROSSWALK_COUNT:{len(crosswalk_by_id)}")

    population: dict[str, int] = {}
    provincial_aggregate: dict[str, int] = {}
    national_aggregate: list[int] = []
    municipality_aggregate_total = 0
    selected_rows = 0
    unobserved_cusec: list[str] = []
    levels: Counter[str] = Counter()
    for row in rows:
        if (
            str(row.get("Periodo", "")).strip() != "2025"
            or str(row.get("Sexo", "")).strip() != "Total"
            or str(row.get("Edad", "")).strip() != "Todas las edades"
        ):
            continue
        selected_rows += 1
        section = str(row.get("Secciones") or "").strip()
        province = str(row.get("Provincias") or "").strip()
        municipality = str(row.get("Municipios") or "").strip()
        if section:
            match = re.match(r"^(\d{10})(?:\s|$)", section)
            if not match:
                raise ValueError(f"CUSEC_FORMAT_INVALID:{section!r}")
            key = match.group(1)
            if key in population:
                raise ValueError(f"POPULATION_DUPLICATE_CUSEC:{key}")
            cpro = str(row.get("Secciones", ""))[:2]
            declared_province = re.match(r"^(\d{2})\b", province)
            declared_municipality = re.match(r"^(\d{5})\b", municipality)
            if not declared_province or declared_province.group(1) != cpro:
                raise ValueError(f"POPULATION_PROVINCE_MISMATCH:{key}")
            if not declared_municipality or declared_municipality.group(1) != key[:5]:
                raise ValueError(f"POPULATION_MUNICIPALITY_MISMATCH:{key}")
            raw_value = row.get("Total", "")
            if raw_value is None or not str(raw_value).strip():
                # INE conserva códigos de secciones históricas sin observación.
                # Ausente no significa cero; la cobertura exacta contra N07
                # determina si alguno pertenece al universo vigente.
                levels["section_unobserved"] += 1
                unobserved_cusec.append(key)
                continue
            if key not in crosswalk_by_id:
                raise ValueError(f"POPULATION_EXTRA_CUSEC_WITH_VALUE:{key}")
            crosswalk = crosswalk_by_id[key]
            if cpro != crosswalk["CPRO"] or key[:5] != crosswalk["CUMUN"]:
                raise ValueError(f"POPULATION_CUSEC_HIERARCHY_MISMATCH:{key}")
            value = _int_total(raw_value, label=f"INE65034-2025:{key}")
            population[key] = value
            levels["section"] += 1
        elif municipality:
            levels["municipality"] += 1
            raw_value = row.get("Total", "")
            if raw_value:
                municipality_aggregate_total += _int_total(raw_value, label="municipality")
        elif province:
            match = re.match(r"^(\d{2})\b", province)
            if not match:
                raise ValueError(f"PROVINCE_CODE_INVALID:{province!r}")
            code = match.group(1)
            if code not in PROVINCES or code in provincial_aggregate:
                raise ValueError(f"PROVINCE_AGGREGATE_INVALID_OR_DUPLICATE:{code}")
            provincial_aggregate[code] = _int_total(row.get("Total", ""), label=f"province:{code}")
            levels["province"] += 1
        else:
            national_aggregate.append(_int_total(row.get("Total", ""), label="national"))
            levels["national"] += 1

    if len(population) != EXPECTED_SECTIONS or set(population) != set(crosswalk_by_id):
        raise ValueError(
            f"SECTION_COVERAGE_MISMATCH:population={len(population)} "
            f"missing={len(set(crosswalk_by_id)-set(population))} "
            f"extra={len(set(population)-set(crosswalk_by_id))}; "
            f"unobserved_in_n07={sorted(set(unobserved_cusec)&set(crosswalk_by_id))[:30]}"
        )
    if set(provincial_aggregate) != PROVINCES:
        raise ValueError("PROVINCIAL_AGGREGATE_COVERAGE_NOT_52_OF_52")
    if len(national_aggregate) != 1:
        raise ValueError(f"NATIONAL_AGGREGATE_NOT_UNIQUE:{len(national_aggregate)}")

    population_by_province: Counter[str] = Counter()
    for key, value in population.items():
        population_by_province[crosswalk_by_id[key]["CPRO"]] += value
    observed_section_counts = Counter(crosswalk_by_id[key]["CPRO"] for key in population)
    if dict(observed_section_counts) != expected_counts:
        raise ValueError(
            "SECTION_PROVINCE_COUNTS_DIFFER_FROM_N07:"
            + json.dumps({"expected": expected_counts, "actual": observed_section_counts}, sort_keys=True)
        )
    for code in sorted(PROVINCES):
        if population_by_province[code] != provincial_aggregate[code]:
            raise ValueError(f"PROVINCIAL_POPULATION_TOTAL_MISMATCH:{code}")

    population_total = sum(population.values())
    if population_total != EXPECTED_TOTAL or population_total != national_aggregate[0]:
        raise ValueError(
            f"NATIONAL_POPULATION_TOTAL_MISMATCH:{population_total}:"
            f"{national_aggregate[0]}"
        )
    if sum(provincial_aggregate.values()) != national_aggregate[0]:
        raise ValueError("PROVINCES_DO_NOT_RECONCILE_TO_NATIONAL_TOTAL")

    report = {
        "selected_ine_rows": selected_rows,
        "row_levels": dict(sorted(levels.items())),
        "section_count": len(population),
        "unique_cusec": len(population),
        "section_population_total": population_total,
        "province_population_total": sum(provincial_aggregate.values()),
        "national_official_total": national_aggregate[0],
        "province_totals_exact": True,
        "national_total_exact": True,
        "province_section_counts": dict(sorted(observed_section_counts.items())),
        "province_population_totals": dict(sorted(population_by_province.items())),
        "population_by_circumscription": {
            code: sum(population[key] for key in population
                      if crosswalk_by_id[key]["CPRO"] == code)
            for code in sorted(PROVINCES)
        },
        "ceuta": {
            "sections": sum(row["CPRO"] == "51" for row in crosswalk_rows),
            "population": sum(population[key] for key in population
                              if crosswalk_by_id[key]["CPRO"] == "51"),
        },
        "melilla": {
            "sections": sum(row["CPRO"] == "52" for row in crosswalk_rows),
            "population": sum(population[key] for key in population
                              if crosswalk_by_id[key]["CPRO"] == "52"),
        },
        "municipality_aggregate_total_diagnostic_only": municipality_aggregate_total,
    }
    return population, report


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _hash_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _protected_zip(parts_dir: Path, name: str, target: Path) -> dict:
    count = PARTS[name]
    part_paths = [parts_dir / f"{name}.part{i:02d}" for i in range(count)]
    if any(not path.is_file() for path in part_paths):
        raise ValueError(f"PROTECTED_SOURCE_PART_MISSING:{name}")
    manifest = parts_dir / "MANIFEST_PARTES.sha256"
    expected_parts = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})\s+\*?(.+)", line.strip())
        if match:
            expected_parts[match.group(2)] = match.group(1)
    actual_parts = {}
    for path in part_paths:
        actual = _hash_path(path)
        if expected_parts.get(path.name) != actual:
            raise ValueError(f"PROTECTED_SOURCE_PART_SHA_MISMATCH:{path.name}")
        actual_parts[path.name] = actual
    with target.open("xb") as output:
        for path in part_paths:
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    output.write(chunk)
    expected = EXPECTED_POPULATION_SHA if name == "65034.csv.zip" else EXPECTED_SECTIONING_SHA
    actual = _hash_path(target)
    if actual != expected:
        raise ValueError(f"PROTECTED_SOURCE_SHA_MISMATCH:{name}:{actual}")
    return {"path": f"inputs/partes/{name}.partXX", "bytes": target.stat().st_size,
            "sha256": actual, "part_sha256": actual_parts,
            "manifest_path": "inputs/partes/MANIFEST_PARTES.sha256"}


def _shapefile_frame(source: Path) -> tuple[gpd.GeoDataFrame, dict]:
    with zipfile.ZipFile(source) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"SECTIONING_ZIP_CRC_INVALID:{bad}")
        shapefiles = [name for name in archive.namelist() if name.lower().endswith(".shp")]
        if len(shapefiles) != 1:
            raise ValueError(f"SECTIONING_LAYER_COUNT:{len(shapefiles)}")
        stem = shapefiles[0].rsplit(".", 1)[0]
        with tempfile.TemporaryDirectory(prefix="ddd-ine-national-") as tmp:
            for name in archive.namelist():
                if name.rsplit(".", 1)[0] != stem:
                    continue
                suffix = name.rsplit(".", 1)[-1].lower()
                Path(tmp, f"sectioning.{suffix}").write_bytes(archive.read(name))
            frame = gpd.read_file(Path(tmp, "sectioning.shp"))
    if frame.crs is None or frame.crs.to_epsg() != 25830:
        raise ValueError("SECTIONING_CRS_NOT_EPSG25830")
    if len(frame) != EXPECTED_SECTIONS:
        raise ValueError(f"SECTIONING_COUNT_MISMATCH:{len(frame)}")
    rows = frame[list(FIELDS)].to_dict("records")
    reference = json.loads(
        (ROOT / "docs/ESTUDIOS/cartografia_nacional_20261008/referencia_seccionado_2025.json")
        .read_text(encoding="utf-8")
    )
    validate_rows(rows, rows, reference["province_counts"])
    invalid = []
    geometry_hashes = {}
    by_key = {}
    for index, row in frame.iterrows():
        key = row["CUSEC"]
        geom = row.geometry
        if geom is None or geom.is_empty or not geom.is_valid:
            invalid.append({"CUSEC": key,
                            "reason": "MISSING_OR_EMPTY" if geom is None or geom.is_empty
                            else explain_validity(geom)})
        geometry_hashes[key] = hashlib.sha256(geom.wkb).hexdigest()
        if key in by_key:
            raise ValueError(f"SECTIONING_DUPLICATE_CUSEC:{key}")
        by_key[key] = index
    if invalid:
        raise ValueError(f"SECTIONING_GEOMETRY_INVALID:{len(invalid)}")
    geometry_identity = hashlib.sha256(
        json.dumps(geometry_hashes, sort_keys=True).encode()
    ).hexdigest()
    return frame, {"crs": "EPSG:25830", "section_count": len(frame),
                   "unique_cusec": len(by_key), "geometry_invalid": 0,
                   "geometry_identity_sha256": geometry_identity}


def materialize(parts_dir: Path, crosswalk_path: Path, output: Path) -> dict:
    if output.exists():
        raise FileExistsError(f"OUTPUT_ALREADY_EXISTS:{output}")
    crosswalk_bytes = crosswalk_path.read_bytes()
    crosswalk = list(csv.DictReader(io.StringIO(crosswalk_bytes.decode("utf-8-sig"))))
    reference = json.loads((crosswalk_path.parent / "evidence.json").read_text(encoding="utf-8"))
    if reference.get("status") != "PASS" or reference.get("unit_count") != EXPECTED_SECTIONS:
        raise ValueError("N07_CROSSWALK_EVIDENCE_NOT_PASS")
    if sha256(crosswalk_bytes) != reference.get("crosswalk_sha256"):
        raise ValueError("N07_CROSSWALK_SHA_MISMATCH")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ddd-ine-source-pair-") as tmp_name:
        tmp = Path(tmp_name)
        geometry_source = _protected_zip(parts_dir, "seccionado_2025.zip", tmp / "seccionado_2025.zip")
        population_source = _protected_zip(parts_dir, "65034.csv.zip", tmp / "65034.csv.zip")
        if sha256(crosswalk_bytes) != reference["crosswalk_sha256"]:
            raise ValueError("N07_CROSSWALK_CHANGED_DURING_READ")
        with zipfile.ZipFile(tmp / "65034.csv.zip") as archive:
            if archive.testzip() is not None:
                raise ValueError("POPULATION_ZIP_CRC_INVALID")
            csv_members = [name for name in archive.namelist()
                           if name.lower().endswith(".csv") and "__macosx/" not in name.lower()]
            if len(csv_members) != 1:
                raise ValueError(f"POPULATION_CSV_MEMBER_COUNT:{len(csv_members)}")
            with archive.open(csv_members[0]) as binary:
                text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
                reader = csv.DictReader(text, delimiter="\t")
                required = {"Provincias", "Municipios", "Secciones", "Sexo", "Edad", "Periodo", "Total"}
                if not required.issubset(set(reader.fieldnames or [])):
                    raise ValueError("POPULATION_CSV_COLUMNS_INVALID")
                population, population_audit = validate_population_rows(
                    reader, crosswalk, expected_counts=reference["province_counts"])
        frame, geometry_audit = _shapefile_frame(tmp / "seccionado_2025.zip")
        geometry_rows = frame[list(FIELDS)].to_dict("records")
        validate_rows(geometry_rows, crosswalk, reference["province_counts"])
        frame = frame.sort_values("CUSEC", kind="mergesort").copy()
        frame["POB_2025"] = frame["CUSEC"].map(population)
        if frame["POB_2025"].isna().any():
            raise ValueError("GEOMETRY_WITHOUT_POPULATION")
        crosswalk_by_id = {row["CUSEC"]: row for row in crosswalk}

        output.mkdir(parents=False, exist_ok=False)
        population_stream = io.StringIO(newline="")
        writer = csv.writer(population_stream, lineterminator="\n")
        writer.writerow([*FIELDS, "POB_2025"])
        for key in sorted(population):
            attributes = crosswalk_by_id[key]
            writer.writerow([*(attributes[field] for field in FIELDS), population[key]])
        population_csv = population_stream.getvalue().encode("utf-8")
        (output / "poblacion_por_seccion_2025.csv").write_bytes(population_csv)
        (output / "crosswalk_n07_2025.csv").write_bytes(crosswalk_bytes)

        if geometry_audit["geometry_identity_sha256"] != reference.get("geometry_identity_sha256"):
            raise ValueError("N07_GEOMETRY_IDENTITY_MISMATCH")
        manifest = {
            "schema": "ddd.official-national-section-population-pair/1.0",
            "version": "1.0.0",
            "date": "2026-10-12",
            "status": "SOURCE_PAIR_ACCREDITED; CONTRACT_WAIT_OWNER; GENERATION_DISABLED",
            "territory_id": "espana_congreso",
            "authority": "Instituto Nacional de Estadística (INE)",
            "edition": 2025,
            "population_year": 2025,
            "section_year": 2025,
            "unit": "sección censal CUSEC",
            "input_contract": {
                "geometry": {
                    "archive": "seccionado_2025.zip",
                    "member_type": "ESRI Shapefile",
                    "required_fields": FIELDS,
                    "key": "CUSEC",
                    "crs": "EPSG:25830",
                    "validity": "one nonempty individually valid geometry per CUSEC",
                },
                "population": {
                    "archive": "65034.csv.zip",
                    "member": "65034.csv",
                    "delimiter": "tab",
                    "encoding": "UTF-8 with optional BOM",
                    "required_columns": ["Provincias", "Municipios", "Secciones", "Sexo",
                                         "Edad", "Periodo", "Total"],
                    "filter": {"Periodo": "2025", "Sexo": "Total",
                               "Edad": "Todas las edades"},
                    "key": "first 10 digits of Secciones; exact string CUSEC join",
                    "hierarchy": {"province": "CPRO", "municipality": "CUMUN"},
                    "empty_total": "absent observation; never coerce to zero",
                },
                "join": "one-to-one exact CUSEC; no padding, reassignment, interpolation, or redistribution",
            },
            "crosswalk": {"path": "crosswalk_n07_2025.csv", "sha256": sha256(crosswalk_bytes),
                          "evidence_path": "docs/ESTUDIOS/N07_20261011/result/evidence.json",
                          "evidence_sha256": _hash_path(crosswalk_path.parent / "evidence.json")},
            "sources": {"geometry": geometry_source, "population": population_source},
            "outputs": {
                "poblacion_por_seccion_2025.csv": {"bytes": len(population_csv),
                                                  "sha256": sha256(population_csv),
                                                  "media_type": "text/csv; charset=utf-8",
                                                  "columns": [*FIELDS, "POB_2025"]},
            },
            "delivery_contract": {
                "format": "CSV joined to N07 attributes by exact CUSEC",
                "geometry_coordinates_duplicated": False,
                "geometry_join_key": "CUSEC",
                "geometry_source": "protected official 2025 sectioning ZIP; reassembled from inputs/partes/",
                "consumer_note": "Join this CSV to the official geometry by CUSEC; the manifest records its protected ZIP hash and EPSG:25830. No geometry reassignment or coordinate transformation is performed.",
            },
            "geometry": geometry_audit,
            "population": population_audit,
            "province_population_totals": population_audit["population_by_circumscription"],
            "identity": {"key": "CUSEC", "join": "exact string equality; no padding or reassignment",
                         "attributes_equal_to_n07": True, "losses": 0, "extras": 0,
                         "duplicates": 0, "invalid_values": 0},
            "reproduction": {
                "command": "python herramientas/materializar_fuentes_nacionales_ine.py --parts-dir inputs/partes --crosswalk docs/ESTUDIOS/N07_20261011/result/crosswalk.csv --output <new-directory>",
                "official_downloads": 0,
                "network": "not used",
                "n07_geometry_replay": "crosswalk protected input; member and identity hashes compared",
                "geometry_validation_scope": "per-feature nonempty and valid; N07 topology limitations remain",
                "software": {"python": __import__("platform").python_version(),
                             "geopandas": gpd.__version__,
                             "shapely": __import__("shapely").__version__,
                             "geos": __import__("shapely").geos_version_string},
            },
            "institutional_contract_status": "CANDIDATO_WAIT_OWNER",
            "k_selected": False,
            "quotas_created": False,
            "generation_authorized": False,
        }
        canonical = json.dumps(manifest, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
        manifest["manifest_identity_sha256"] = sha256(canonical)
        (output / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8")
        return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts-dir", type=Path, required=True)
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = materialize(args.parts_dir, args.crosswalk, args.output)
    print(json.dumps({"status": report["status"], "sections": report["population"]["section_count"],
                      "population": report["population"]["section_population_total"],
                      "circumscriptions": len(report["province_population_totals"]),
                      "ceuta": report["population"]["ceuta"],
                      "melilla": report["population"]["melilla"],
                      "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
