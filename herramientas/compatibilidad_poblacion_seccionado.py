from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

SCHEMA = "ddd.population-sectioning-compatibility/1.0"
REPORT_NAME = "compatibilidad_poblacion_seccionado.json"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_sha256(data: dict) -> str:
    return _sha256_bytes(
        json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def normalize_section_key(value: object) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    if len(digits) < 10:
        digits = digits.zfill(10)
    return digits[:10]


def _dedupe_population(rows: list[tuple[str, int]]) -> tuple[dict[str, int], list[str]]:
    values: dict[str, int] = {}
    duplicates: set[str] = set()
    for raw_key, population in rows:
        key = normalize_section_key(raw_key)
        if not key:
            duplicates.add("<EMPTY>")
            continue
        if key in values:
            duplicates.add(key)
            continue
        values[key] = int(population)
    return values, sorted(duplicates)


def _dedupe_geometry(rows: list[tuple[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    values: dict[str, Any] = {}
    duplicates: set[str] = set()
    for raw_key, geometry in rows:
        key = normalize_section_key(raw_key)
        if not key:
            duplicates.add("<EMPTY>")
            continue
        if key in values:
            duplicates.add(key)
            continue
        values[key] = geometry
    return values, sorted(duplicates)


def _equals(left: Any, right: Any) -> bool:
    try:
        return bool(left.equals(right))
    except Exception:
        return False


def _intersects(left: Any, right: Any) -> bool:
    try:
        return bool(left.intersects(right))
    except Exception:
        return False


def _union_equals(parts: list[Any], whole: Any) -> bool:
    if len(parts) < 2:
        return False
    try:
        from shapely.ops import unary_union
        return bool(unary_union(parts).equals(whole))
    except Exception:
        return False


def reconcile_population_sectioning(
    *,
    territory_id: str,
    edition: str,
    population_year: int,
    section_year: int,
    population_rows: list[tuple[str, int]],
    target_geometry_rows: list[tuple[str, Any]],
    origin_geometry_rows: list[tuple[str, Any]] | None,
    input_identities: dict | None = None,
) -> dict:
    populations, duplicate_population = _dedupe_population(population_rows)
    target, duplicate_target = _dedupe_geometry(target_geometry_rows)
    origin, duplicate_origin = _dedupe_geometry(origin_geometry_rows or [])

    causes: list[str] = []
    if duplicate_population:
        causes.append("DUPLICATE_POPULATION_KEYS")
    if duplicate_target:
        causes.append("DUPLICATE_TARGET_GEOMETRY_KEYS")
    if population_year != section_year and origin_geometry_rows is None:
        causes.append("ORIGIN_SECTIONING_EVIDENCE_MISSING")
    if population_year != section_year and duplicate_origin:
        causes.append("DUPLICATE_ORIGIN_GEOMETRY_KEYS")

    reference_geometry = target if population_year == section_year else origin
    population_without_geometry = sorted(set(populations) - set(reference_geometry))
    geometry_without_population_at_origin = sorted(set(reference_geometry) - set(populations))
    if population_without_geometry:
        causes.append("POPULATION_WITHOUT_GEOMETRY")
    if geometry_without_population_at_origin:
        causes.append("GEOMETRY_WITHOUT_POPULATION")

    correspondences: list[dict] = []
    geometric_changes: list[dict] = []
    mapped_source: set[str] = set()
    mapped_target: set[str] = set()

    if population_year == section_year:
        for key in sorted(set(reference_geometry) & set(target)):
            correspondences.append({
                "source_keys": [key],
                "target_keys": [key],
                "kind": "IDENTITY_SAME_EDITION",
                "evidence": "same_materialized_sectioning",
            })
            mapped_source.add(key)
            mapped_target.add(key)
    elif origin:
        common = sorted(set(origin) & set(target))
        for key in common:
            if _equals(origin[key], target[key]):
                correspondences.append({
                    "source_keys": [key],
                    "target_keys": [key],
                    "kind": "ONE_TO_ONE",
                    "evidence": "geometric_equality",
                })
                mapped_source.add(key)
                mapped_target.add(key)
            else:
                geometric_changes.append({
                    "source_keys": [key],
                    "target_keys": [key],
                    "kind": "SAME_CODE_BOUNDARY_CHANGED",
                })

        unmatched_source = [k for k in sorted(origin) if k not in mapped_source]
        unmatched_target = [k for k in sorted(target) if k not in mapped_target]

        # A code change is accepted only when the source and target geometries are
        # verifiably equal. Code equality by itself is never evidence across years.
        for source_key in list(unmatched_source):
            equal_targets = [
                target_key for target_key in unmatched_target
                if _equals(origin[source_key], target[target_key])
            ]
            if len(equal_targets) == 1:
                target_key = equal_targets[0]
                correspondences.append({
                    "source_keys": [source_key],
                    "target_keys": [target_key],
                    "kind": "ONE_TO_ONE_CODE_CHANGE",
                    "evidence": "geometric_equality",
                })
                mapped_source.add(source_key)
                mapped_target.add(target_key)
                unmatched_target.remove(target_key)

        unmatched_source = [k for k in sorted(origin) if k not in mapped_source]
        unmatched_target = [k for k in sorted(target) if k not in mapped_target]

        # Splits/fusions are diagnosed only after a geometric union check. They are
        # still blocking: source-section population cannot be redistributed among
        # several target sections without an authoritative population correspondence.
        for source_key in unmatched_source:
            candidates = [
                target_key for target_key in unmatched_target
                if _intersects(origin[source_key], target[target_key])
            ]
            if len(candidates) > 1 and _union_equals([target[k] for k in candidates], origin[source_key]):
                correspondences.append({
                    "source_keys": [source_key],
                    "target_keys": sorted(candidates),
                    "kind": "SPLIT",
                    "evidence": "geometric_union",
                })

        for target_key in unmatched_target:
            candidates = [
                source_key for source_key in unmatched_source
                if _intersects(target[target_key], origin[source_key])
            ]
            if len(candidates) > 1 and _union_equals([origin[k] for k in candidates], target[target_key]):
                correspondences.append({
                    "source_keys": sorted(candidates),
                    "target_keys": [target_key],
                    "kind": "FUSION",
                    "evidence": "geometric_union",
                })

        non_bijective = [r for r in correspondences if r["kind"] in {"SPLIT", "FUSION"}]
        if non_bijective:
            causes.append("NON_BIJECTIVE_GEOMETRIC_CORRESPONDENCE")
        if geometric_changes:
            causes.append("SAME_CODE_BOUNDARY_CHANGED")

    one_to_one = [
        r for r in correspondences
        if len(r["source_keys"]) == 1 and len(r["target_keys"]) == 1
    ]
    assignment: dict[str, int] = {}
    source_to_target: dict[str, str] = {}
    for row in one_to_one:
        source_key = row["source_keys"][0]
        target_key = row["target_keys"][0]
        if source_key in populations:
            if target_key in assignment:
                causes.append("DUPLICATE_TARGET_ASSIGNMENT")
            else:
                assignment[target_key] = populations[source_key]
                source_to_target[source_key] = target_key

    population_without_destination = sorted(set(populations) - set(source_to_target))
    geometry_without_population = sorted(set(target) - set(assignment))
    if population_without_destination:
        causes.append("POPULATION_WITHOUT_DESTINATION")
    if geometry_without_population:
        causes.append("TARGET_GEOMETRY_WITHOUT_POPULATION")

    input_total = sum(populations.values())
    assigned_total = sum(assignment.values())
    exact_conservation = input_total == assigned_total
    if not exact_conservation:
        causes.append("POPULATION_TOTAL_NOT_CONSERVED")

    if population_year != section_year:
        # Any still-unmapped origin/target geometry is an unaccredited edition change.
        mapped_one_source = {r["source_keys"][0] for r in one_to_one}
        mapped_one_target = {r["target_keys"][0] for r in one_to_one}
        if sorted(set(origin) - mapped_one_source) or sorted(set(target) - mapped_one_target):
            causes.append("UNACCREDITED_SECTIONING_CHANGE")

    causes = sorted(set(causes))
    canonical = {
        "territory_id": str(territory_id),
        "edition": str(edition),
        "population_year": int(population_year),
        "section_year": int(section_year),
        "inputs": input_identities or {},
        "correspondences": correspondences,
        "geometric_changes": geometric_changes,
        "duplicates": {
            "population": duplicate_population,
            "target_geometry": duplicate_target,
            "origin_geometry": duplicate_origin,
        },
        "population_without_geometry": population_without_geometry,
        "geometry_without_population": geometry_without_population,
        "population_without_destination": population_without_destination,
        "population": {
            "input_total": input_total,
            "assigned_total": assigned_total,
            "exact_conservation": exact_conservation,
        },
        "causes": causes,
    }
    identity = _canonical_sha256(canonical)
    return {
        "schema": SCHEMA,
        **canonical,
        "compatibility_identity_sha256": identity,
        "decision": "READY" if not causes else "BLOCKED",
    }


def _population_rows_from_zip(path: Path) -> list[tuple[str, int]]:
    if not zipfile.is_zipfile(path):
        raise ValueError(f"Fuente de población no ZIP: {path}")
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.lower().endswith((".csv", ".tsv", ".txt")) and "__macosx/" not in n.lower()]
        if len(names) != 1:
            raise ValueError(f"Fuente de población ambigua: {names}")
        text = archive.read(names[0]).decode("utf-8-sig")
    first = text.splitlines()[0] if text.splitlines() else ""
    delimiter = max(("\t", ";", ","), key=lambda d: first.count(d))
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows: list[tuple[str, int]] = []
    for row in reader:
        key = normalize_section_key(row.get("Secciones"))
        raw = str(row.get("Total") or "").strip()
        if not key:
            rows.append(("", 0))
            continue
        if raw == "":
            raise ValueError(f"Población ausente para sección {key}")
        cleaned = raw.replace(".", "").replace(",", "")
        if not cleaned.lstrip("-").isdigit():
            raise ValueError(f"Población no numérica para sección {key}: {raw!r}")
        rows.append((key, int(cleaned)))
    return rows


def _geometry_rows_from_zip(path: Path) -> list[tuple[str, Any]]:
    try:
        import geopandas as gpd
    except Exception as exc:
        raise RuntimeError(f"geopandas es obligatorio para reconciliar seccionados: {exc}") from exc
    if not path.is_file() or not zipfile.is_zipfile(path):
        raise ValueError(f"Seccionado no ZIP: {path}")
    with zipfile.ZipFile(path) as archive:
        shp_members = [n for n in archive.namelist() if n.lower().endswith(".shp") and "__macosx/" not in n.lower()]
        if len(shp_members) != 1:
            raise ValueError(f"Seccionado ambiguo: shapefiles={shp_members}")
        import tempfile
        with tempfile.TemporaryDirectory(prefix="ddd_compat_sections_") as td:
            archive.extractall(td)
            gdf = gpd.read_file(Path(td) / shp_members[0])
    id_field = next((x for x in ("CUSEC", "CUSEC_KEY", "CUSEC20", "SEC") if x in gdf.columns), None)
    if not id_field:
        raise ValueError(f"Seccionado sin clave de sección reconocible: {list(gdf.columns)}")
    return [(normalize_section_key(row[id_field]), row.geometry) for _, row in gdf.iterrows()]


def build_materialized_report(
    *,
    evidence_dir: Path,
    territory_id: str,
    edition: str,
    population_year: int,
    section_year: int,
    inventory: dict,
) -> dict:
    rows = inventory.get("sources") or []
    by_role = {str(row.get("role") or ""): row for row in rows if isinstance(row, dict)}
    population = by_role.get("population")
    target = by_role.get("target_sectioning")
    origin = by_role.get("population_sectioning_origin")
    if not population or not target:
        raise ValueError("Fuentes materializadas sin roles population/target_sectioning")

    def materialized(row: dict) -> Path:
        return evidence_dir / "materialized" / str(row["path"])

    population_path = materialized(population)
    target_path = materialized(target)
    origin_path = materialized(origin) if origin else None
    identities = {
        "population": {"path": str(population["path"]), "sha256": str(population["sha256"])},
        "target_sectioning": {"path": str(target["path"]), "sha256": str(target["sha256"])},
        "origin_sectioning": (
            {"path": str(origin["path"]), "sha256": str(origin["sha256"])}
            if origin else None
        ),
    }
    report = reconcile_population_sectioning(
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
        population_rows=_population_rows_from_zip(population_path),
        target_geometry_rows=_geometry_rows_from_zip(target_path),
        origin_geometry_rows=_geometry_rows_from_zip(origin_path) if origin_path else None,
        input_identities=identities,
    )
    path = evidence_dir / REPORT_NAME
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def read_report_from_package(package: Path) -> tuple[dict, str]:
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    bundle = package / str(manifest.get("path") or "")
    if not bundle.is_file() or not zipfile.is_zipfile(bundle):
        raise ValueError("Paquete congelado ausente o inválido")
    with zipfile.ZipFile(bundle) as archive:
        try:
            raw = archive.read(REPORT_NAME)
        except KeyError as exc:
            raise ValueError(
                "informe de compatibilidad población↔seccionado ausente; paquete histórico no reutilizable"
            ) from exc
    report = json.loads(raw.decode("utf-8"))
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise ValueError("informe de compatibilidad población↔seccionado inválido")
    declared_identity = str(report.get("compatibility_identity_sha256") or "")
    canonical = {
        key: value
        for key, value in report.items()
        if key not in {"schema", "compatibility_identity_sha256", "decision"}
    }
    actual_identity = _canonical_sha256(canonical)
    if declared_identity != actual_identity:
        raise ValueError(
            "identidad del informe de compatibilidad población↔seccionado contradictoria"
        )
    expected_decision = "READY" if not (report.get("causes") or []) else "BLOCKED"
    if report.get("decision") != expected_decision:
        raise ValueError(
            "decisión del informe de compatibilidad población↔seccionado contradictoria"
        )
    return report, _sha256_bytes(raw)
