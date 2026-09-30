from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable

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


def _parse_crs(value: object, *, label: str):
    if value is None or str(value).strip() == "":
        raise ValueError(f"CRS_MISSING: {label}")
    try:
        from pyproj import CRS
        return CRS.from_user_input(value)
    except Exception as exc:
        raise ValueError(f"CRS_INVALID: {label}: {value!r}") from exc


def _crs_text(crs: Any) -> str:
    try:
        authority = crs.to_authority()
    except Exception:
        authority = None
    if authority:
        return f"{authority[0]}:{authority[1]}"
    return crs.to_wkt()


def _crs_audit(*, target_original: object, origin_original: object | None, cross_year: bool) -> dict:
    target = _parse_crs(target_original, label="target_sectioning")
    origin = _parse_crs(origin_original, label="population_sectioning_origin") if cross_year else None
    effective = target
    return {
        "target": {
            "original": _crs_text(target),
            "original_wkt": target.to_wkt(),
        },
        "origin": (
            {
                "original": _crs_text(origin),
                "original_wkt": origin.to_wkt(),
            }
            if origin is not None
            else None
        ),
        "effective": {
            "crs": _crs_text(effective),
            "wkt": effective.to_wkt(),
            "policy": "target_sectioning_crs",
            "origin_reprojected": bool(origin is not None and not origin.equals(target)),
        },
    }


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
    crs_audit: dict | None = None,
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
                    "evidence": "geometric_equality_after_crs_normalization",
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
                    "evidence": "geometric_equality_after_crs_normalization",
                })
                mapped_source.add(source_key)
                mapped_target.add(target_key)
                unmatched_target.remove(target_key)

        unmatched_source = [k for k in sorted(origin) if k not in mapped_source]
        unmatched_target = [k for k in sorted(target) if k not in mapped_target]

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
                    "evidence": "geometric_union_after_crs_normalization",
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
                    "evidence": "geometric_union_after_crs_normalization",
                })

        if any(r["kind"] in {"SPLIT", "FUSION"} for r in correspondences):
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
        "crs": crs_audit or {},
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


def _sectioning_crs_from_bytes(payload: bytes, *, label: str):
    with tempfile.TemporaryDirectory(prefix="ddd_compat_crs_") as td:
        path = Path(td) / "sectioning.zip"
        path.write_bytes(payload)
        gdf, _ = _geometry_frame_from_zip(path)
        return _parse_crs(gdf.crs, label=label)


def _geometry_frame_from_zip(path: Path):
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
        with tempfile.TemporaryDirectory(prefix="ddd_compat_sections_") as td:
            archive.extractall(td)
            gdf = gpd.read_file(Path(td) / shp_members[0])
    id_field = next((x for x in ("CUSEC", "CUSEC_KEY", "CUSEC20", "SEC") if x in gdf.columns), None)
    if not id_field:
        raise ValueError(f"Seccionado sin clave de sección reconocible: {list(gdf.columns)}")
    _parse_crs(gdf.crs, label=str(path))
    return gdf, id_field


def _rows_from_frame(gdf: Any, id_field: str) -> list[tuple[str, Any]]:
    return [(normalize_section_key(row[id_field]), row.geometry) for _, row in gdf.iterrows()]


def normalize_geometry_frames(
    *,
    target_gdf: Any,
    target_id_field: str,
    origin_gdf: Any | None,
    origin_id_field: str | None,
    cross_year: bool,
) -> tuple[list[tuple[str, Any]], list[tuple[str, Any]] | None, dict]:
    target_crs = _parse_crs(getattr(target_gdf, "crs", None), label="target_sectioning")
    origin_crs = None
    normalized_origin = origin_gdf
    if cross_year:
        if origin_gdf is None or origin_id_field is None:
            raise ValueError("ORIGIN_SECTIONING_EVIDENCE_MISSING")
        origin_crs = _parse_crs(getattr(origin_gdf, "crs", None), label="population_sectioning_origin")
        if not origin_crs.equals(target_crs):
            normalized_origin = origin_gdf.to_crs(target_crs)
    elif origin_gdf is not None:
        raise ValueError("CRS_UNEXPECTED: seccionado origen presente para la misma edición")

    crs = _crs_audit(
        target_original=target_crs,
        origin_original=origin_crs,
        cross_year=cross_year,
    )
    return (
        _rows_from_frame(target_gdf, target_id_field),
        (
            _rows_from_frame(normalized_origin, origin_id_field)
            if normalized_origin is not None and origin_id_field is not None
            else None
        ),
        crs,
    )


def _expected_roles(population_year: int, section_year: int) -> tuple[str, ...]:
    roles = ["population", "target_sectioning"]
    if int(population_year) != int(section_year):
        roles.append("population_sectioning_origin")
    return tuple(roles)


def _materialized_member(row: dict) -> str:
    path = str(row.get("path") or "").strip()
    if not path:
        raise ValueError("INPUT_BINDING_INVALID: inventario sin path")
    return "materialized/" + path.lstrip("/")


def _inventory_by_role(inventory: dict, *, population_year: int, section_year: int) -> dict[str, dict]:
    expected = set(_expected_roles(population_year, section_year))
    rows = inventory.get("sources")
    if not isinstance(rows, list) or not rows:
        raise ValueError("INPUT_ROLE_INVALID: inventario sin fuentes")
    by_role: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("INPUT_ROLE_INVALID: entrada de inventario no es objeto")
        role = str(row.get("role") or "").strip()
        if not role:
            raise ValueError("INPUT_ROLE_MISSING: entrada de inventario sin role")
        if role not in expected:
            raise ValueError(f"INPUT_ROLE_UNEXPECTED: {role}")
        if role in by_role:
            raise ValueError(f"INPUT_ROLE_DUPLICATE: {role}")
        by_role[role] = row
    missing = sorted(expected - set(by_role))
    if missing:
        raise ValueError("INPUT_ROLE_MISSING: " + ", ".join(missing))
    members: dict[str, str] = {}
    for role, row in by_role.items():
        member = _materialized_member(row)
        previous = members.get(member)
        if previous is not None:
            raise ValueError(
                f"INPUT_MEMBER_AMBIGUOUS: {member} usado por {previous} y {role}"
            )
        members[member] = role
    return by_role


def _validate_crs_contract(report: dict, *, population_year: int, section_year: int) -> list[str]:
    reasons: list[str] = []
    crs = report.get("crs")
    if not isinstance(crs, dict):
        return ["CRS_MISSING: informe sin bloque crs"]
    target = crs.get("target") or {}
    origin = crs.get("origin")
    effective = crs.get("effective") or {}
    try:
        target_crs = _parse_crs(target.get("original"), label="report.target.original")
        target_wkt = _parse_crs(target.get("original_wkt"), label="report.target.original_wkt")
        effective_crs = _parse_crs(effective.get("crs"), label="report.effective.crs")
        effective_wkt = _parse_crs(effective.get("wkt"), label="report.effective.wkt")
        if not target_crs.equals(target_wkt):
            reasons.append("CRS_CONTRADICTORY: target original y WKT no equivalen")
        if not effective_crs.equals(effective_wkt):
            reasons.append("CRS_CONTRADICTORY: effective crs y WKT no equivalen")
        if not target_crs.equals(effective_crs):
            reasons.append("CRS_CONTRADICTORY: CRS efectivo no equivale al CRS objetivo")
        if int(population_year) != int(section_year):
            if not isinstance(origin, dict):
                reasons.append("CRS_MISSING: informe sin CRS de seccionado origen")
            else:
                origin_crs = _parse_crs(origin.get("original"), label="report.origin.original")
                origin_wkt = _parse_crs(origin.get("original_wkt"), label="report.origin.original_wkt")
                if not origin_crs.equals(origin_wkt):
                    reasons.append("CRS_CONTRADICTORY: origin original y WKT no equivalen")
        elif origin not in (None, {}):
            reasons.append("CRS_UNEXPECTED: CRS de origen declarado para la misma edición")
    except ValueError as exc:
        reasons.append(str(exc))
    return reasons


def validate_report_bindings(
    *,
    report: dict,
    inventory: dict,
    read_member_bytes: Callable[[str], bytes],
    territory_id: str,
    edition: str | int,
    population_year: int,
    section_year: int,
    require_ready: bool,
) -> list[str]:
    reasons: list[str] = []
    if report.get("schema") != SCHEMA:
        reasons.append("informe de compatibilidad población↔seccionado inválido")
        return reasons

    canonical = {
        key: value
        for key, value in report.items()
        if key not in {"schema", "compatibility_identity_sha256", "decision"}
    }
    declared_identity = str(report.get("compatibility_identity_sha256") or "")
    if declared_identity != _canonical_sha256(canonical):
        reasons.append("identidad del informe de compatibilidad población↔seccionado contradictoria")
    expected_decision = "READY" if not (report.get("causes") or []) else "BLOCKED"
    if report.get("decision") != expected_decision:
        reasons.append("decisión del informe de compatibilidad población↔seccionado contradictoria")
    if require_ready and report.get("decision") != "READY":
        reasons.append(
            "informe de compatibilidad población↔seccionado bloqueado: "
            + "; ".join(report.get("causes") or [])
        )

    if str(report.get("territory_id") or "") != str(territory_id):
        reasons.append("informe de compatibilidad pertenece a otro territorio")
    if str(report.get("edition") or "") != str(edition):
        reasons.append("informe de compatibilidad pertenece a otra edición")
    if int(report.get("population_year") or 0) != int(population_year):
        reasons.append("informe de compatibilidad usa otro año de población")
    if int(report.get("section_year") or 0) != int(section_year):
        reasons.append("informe de compatibilidad usa otro año de seccionado")
    reasons.extend(_validate_crs_contract(
        report,
        population_year=population_year,
        section_year=section_year,
    ))

    try:
        by_role = _inventory_by_role(
            inventory,
            population_year=population_year,
            section_year=section_year,
        )
    except ValueError as exc:
        reasons.append(str(exc))
        return reasons

    inputs = report.get("inputs")
    if not isinstance(inputs, dict):
        reasons.append("INPUT_BINDING_INVALID: informe sin inputs")
        return reasons
    expected_roles = set(_expected_roles(population_year, section_year))
    report_roles = set(inputs)
    missing = sorted(expected_roles - report_roles)
    unexpected = sorted(report_roles - expected_roles)
    if missing:
        reasons.append("INPUT_BINDING_MISSING: " + ", ".join(missing))
    if unexpected:
        reasons.append("INPUT_BINDING_UNEXPECTED: " + ", ".join(unexpected))
    report_members: dict[str, str] = {}
    for role in sorted(expected_roles & report_roles):
        binding = inputs.get(role)
        if isinstance(binding, dict):
            member = str(binding.get("member") or "")
            if member:
                previous = report_members.get(member)
                if previous is not None:
                    reasons.append(
                        f"INPUT_BINDING_AMBIGUOUS: {member} usado por {previous} y {role}"
                    )
                report_members[member] = role

    payloads_by_role: dict[str, bytes] = {}
    for role in sorted(expected_roles & report_roles):
        inv = by_role[role]
        binding = inputs.get(role)
        if not isinstance(binding, dict):
            reasons.append(f"INPUT_BINDING_INVALID: {role}")
            continue
        expected_member = _materialized_member(inv)
        if str(binding.get("role") or "") != role:
            reasons.append(f"INPUT_BINDING_ROLE_MISMATCH: {role}")
        if str(binding.get("member") or "") != expected_member:
            reasons.append(f"INPUT_BINDING_MEMBER_MISMATCH: {role}")
        if str(binding.get("path") or "") != str(inv.get("path") or ""):
            reasons.append(f"INPUT_BINDING_PATH_MISMATCH: {role}")
        inv_sha = str(inv.get("sha256") or "").lower()
        report_sha = str(binding.get("sha256") or "").lower()
        inv_bytes = inv.get("bytes")
        report_bytes = binding.get("bytes")
        try:
            payload = read_member_bytes(expected_member)
        except Exception as exc:
            reasons.append(f"INPUT_MEMBER_MISSING: {role}: {expected_member}: {exc}")
            continue
        payloads_by_role[role] = payload
        actual_sha = _sha256_bytes(payload)
        actual_bytes = len(payload)
        if not inv_sha or inv_sha != actual_sha:
            reasons.append(f"INPUT_INVENTORY_SHA_MISMATCH: {role}")
        if report_sha != actual_sha:
            reasons.append(f"INPUT_REPORT_SHA_MISMATCH: {role}")
        try:
            if int(inv_bytes) != actual_bytes:
                reasons.append(f"INPUT_INVENTORY_SIZE_MISMATCH: {role}")
        except Exception:
            reasons.append(f"INPUT_INVENTORY_SIZE_INVALID: {role}")
        try:
            if int(report_bytes) != actual_bytes:
                reasons.append(f"INPUT_REPORT_SIZE_MISMATCH: {role}")
        except Exception:
            reasons.append(f"INPUT_REPORT_SIZE_INVALID: {role}")
        if str(binding.get("source_id") or "") != str(inv.get("source_id") or ""):
            reasons.append(f"INPUT_BINDING_SOURCE_ID_MISMATCH: {role}")

    crs_block = report.get("crs") or {}
    try:
        target_payload = payloads_by_role.get("target_sectioning")
        if target_payload is not None:
            actual_target_crs = _sectioning_crs_from_bytes(
                target_payload,
                label="package.target_sectioning",
            )
            declared_target_crs = _parse_crs(
                (crs_block.get("target") or {}).get("original"),
                label="report.target.original",
            )
            if not actual_target_crs.equals(declared_target_crs):
                reasons.append("CRS_BINDING_MISMATCH: target_sectioning")
        if int(population_year) != int(section_year):
            origin_payload = payloads_by_role.get("population_sectioning_origin")
            if origin_payload is not None:
                actual_origin_crs = _sectioning_crs_from_bytes(
                    origin_payload,
                    label="package.population_sectioning_origin",
                )
                declared_origin_crs = _parse_crs(
                    (crs_block.get("origin") or {}).get("original"),
                    label="report.origin.original",
                )
                if not actual_origin_crs.equals(declared_origin_crs):
                    reasons.append("CRS_BINDING_MISMATCH: population_sectioning_origin")
    except ValueError as exc:
        reasons.append(str(exc))

    population_audit = report.get("population") or {}
    if require_ready and population_audit.get("exact_conservation") is not True:
        reasons.append("informe de compatibilidad no acredita conservación exacta de población")
    return reasons


def build_materialized_report(
    *,
    evidence_dir: Path,
    territory_id: str,
    edition: str,
    population_year: int,
    section_year: int,
    inventory: dict,
) -> dict:
    by_role = _inventory_by_role(
        inventory,
        population_year=population_year,
        section_year=section_year,
    )

    def path_for(role: str) -> Path:
        return evidence_dir / "materialized" / str(by_role[role]["path"])

    population_path = path_for("population")
    target_path = path_for("target_sectioning")
    origin_path = (
        path_for("population_sectioning_origin")
        if population_year != section_year
        else None
    )

    target_gdf, target_id = _geometry_frame_from_zip(target_path)
    origin_gdf = None
    origin_id = None
    if origin_path is not None:
        origin_gdf, origin_id = _geometry_frame_from_zip(origin_path)

    target_rows, origin_rows, crs = normalize_geometry_frames(
        target_gdf=target_gdf,
        target_id_field=target_id,
        origin_gdf=origin_gdf,
        origin_id_field=origin_id,
        cross_year=population_year != section_year,
    )

    identities: dict[str, dict] = {}
    for role, row in by_role.items():
        path = evidence_dir / "materialized" / str(row["path"])
        payload = path.read_bytes()
        identities[role] = {
            "role": role,
            "source_id": str(row.get("source_id") or ""),
            "path": str(row["path"]),
            "member": _materialized_member(row),
            "bytes": len(payload),
            "sha256": _sha256_bytes(payload),
        }

    report = reconcile_population_sectioning(
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
        population_rows=_population_rows_from_zip(population_path),
        target_geometry_rows=target_rows,
        origin_geometry_rows=origin_rows,
        input_identities=identities,
        crs_audit=crs,
    )
    reasons = validate_report_bindings(
        report=report,
        inventory=inventory,
        read_member_bytes=lambda member: (
            evidence_dir / member
        ).read_bytes(),
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
        require_ready=False,
    )
    if reasons:
        raise ValueError("COMPATIBILITY_REPORT_INVALID: " + "; ".join(reasons))
    path = evidence_dir / REPORT_NAME
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def validate_compatibility_package(
    package: Path,
    *,
    territory_id: str,
    edition: str | int,
    population_year: int,
    section_year: int,
    require_ready: bool = True,
) -> tuple[dict, str, list[str]]:
    manifest_path = package / "manifest.json"
    if not manifest_path.is_file():
        return {}, "", ["manifest.json ausente"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle = package / str(manifest.get("path") or "")
    if not bundle.is_file() or not zipfile.is_zipfile(bundle):
        return {}, "", ["paquete congelado ausente o inválido"]
    with zipfile.ZipFile(bundle) as archive:
        try:
            raw = archive.read(REPORT_NAME)
        except KeyError:
            return {}, "", [
                "informe de compatibilidad población↔seccionado ausente; paquete histórico no reutilizable"
            ]
        try:
            inventory = json.loads(archive.read("inventario_fuentes.json").decode("utf-8"))
        except Exception as exc:
            return {}, _sha256_bytes(raw), [f"inventario de fuentes ilegible: {exc}"]
        try:
            report = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            return {}, _sha256_bytes(raw), [f"informe de compatibilidad ilegible: {exc}"]
        if not isinstance(report, dict) or not isinstance(inventory, dict):
            return {}, _sha256_bytes(raw), ["informe/inventario de compatibilidad inválido"]
        reasons = validate_report_bindings(
            report=report,
            inventory=inventory,
            read_member_bytes=archive.read,
            territory_id=territory_id,
            edition=edition,
            population_year=population_year,
            section_year=section_year,
            require_ready=require_ready,
        )
        return report, _sha256_bytes(raw), reasons


def read_report_from_package(package: Path) -> tuple[dict, str]:
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    population_year = int(manifest.get("population_year", manifest.get("source_year", manifest.get("edition"))))
    section_year = int(manifest.get("section_year", manifest.get("source_year", manifest.get("edition"))))
    report, digest, reasons = validate_compatibility_package(
        package,
        territory_id=str(manifest.get("territory_id") or ""),
        edition=str(manifest.get("edition") or ""),
        population_year=population_year,
        section_year=section_year,
        require_ready=True,
    )
    if reasons:
        raise ValueError("; ".join(reasons))
    return report, digest
