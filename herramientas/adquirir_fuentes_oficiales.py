#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: adquisición genérica de fuentes oficiales
VERSIÓN: 1.4.0
NOMBRE DE VERSIÓN: Seccionado INE vigente acreditado por evidencia durable
FECHA: 2026-10-03
ESTADO: candidato
FUNCIÓN: materializar fuentes territoriales por declaración, preservando inmutables las copias oficiales nacionales.
CAMBIOS: resuelve SU.VectorStatisticalUnit mediante la última edición acreditada por evidencia INE durable, sin depender del reloj del runner; conserva Secciones_AÑO para históricos.
MOTIVO: mantener determinista la identidad del locator durante cambios de año y fallar cerrado si la colección vigente no queda acreditada.
ANTERIOR: legacy/herramientas/adquirir_fuentes_oficiales_v1.1.0.py
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

from ddd_core.official_geometry import (
    load_geometry_policy,
    normalize_official_features,
    persist_geometry_normalization_evidence,
    persist_raw_ogc_response,
    validate_materialization_roundtrip,
)
from ddd_core.territorial_validation import parse_population_value, validate_geodataframe

FetchBytes = Callable[[str], bytes]
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PREPARATION_MATRIX = Path("configuracion/preparacion_legislatura_vigente.yaml")
CORE_FIELDS = ("source_id", "path", "sha256", "bytes", "urls", "edition")
SNAPSHOT_REQUIRED = ("path", "expected_sha256", "official_origin_url", "edition", "acquired_at")


def load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Documento YAML no válido: {path}")
    return data


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def live_fetch(url: str, retries: int = 4, timeout: int = 120) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": "DiputadoDeDistrito/2.1 (+GitHub Actions; fuente oficial)"})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - depende de red real
            last = exc
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"No se pudo descargar la fuente oficial: {last}")


def _territory(declaration: dict) -> tuple[str, str, int, int, int, list[dict]]:
    territory = declaration.get("territory") or {}
    territory_id = str(territory.get("id") or "").strip()
    name = str(territory.get("business_name") or "").strip()
    edition = territory.get("edition")
    legacy_year = territory.get("source_year", edition)
    population_year = territory.get("population_year", legacy_year)
    section_year = territory.get("section_year", legacy_year)
    codes = territory.get("territorial_codes")
    if not territory_id or not name or edition is None or not isinstance(codes, list) or not codes:
        raise ValueError("Declaración territorial incompleta: id, nombre, edición y códigos son obligatorios")
    normalized = []
    for row in codes:
        if not isinstance(row, dict) or row.get("code") is None or not row.get("business_name"):
            raise ValueError("Cada provincia debe declarar code y business_name")
        normalized.append({"code": str(row["code"]).zfill(2), "business_name": str(row["business_name"])})
    return territory_id, name, int(edition), int(population_year), int(section_year), normalized


def _required_sources(catalog: dict, declaration: dict) -> list[tuple[str, dict, dict]]:
    sources = catalog.get("sources") or {}
    required = declaration.get("required_sources")
    bindings = declaration.get("source_bindings") or {}
    if not isinstance(required, list) or not required:
        raise ValueError("No hay fuentes requeridas declaradas")
    result = []
    for source_id in required:
        source_id = str(source_id)
        source = sources.get(source_id)
        binding = bindings.get(source_id)
        if not isinstance(source, dict):
            raise ValueError(f"Fuente requerida no catalogada: {source_id}")
        if source.get("id") != source_id:
            raise ValueError(f"Identificador estable inconsistente en catálogo: {source_id}")
        if not isinstance(binding, dict) or not binding.get("materialized_path"):
            raise ValueError(f"Falta materialized_path para {source_id}")
        result.append((source_id, source, binding))
    return result


def _select_mode(declaration: dict, environment: str, requested: str | None) -> str:
    mode = requested or str((declaration.get("default_mode") or {}).get(environment) or "")
    if mode not in {"official_live", "verified_snapshot", "simulated"}:
        raise ValueError(f"Modo de adquisición no declarado para {environment}: {mode or 'vacío'}")
    allowed = (declaration.get("environment_policy") or {}).get(environment)
    if not isinstance(allowed, list) or mode not in allowed:
        raise RuntimeError(f"La política territorial no permite {mode} en {environment}")
    if mode == "simulated" and environment != "test":
        raise RuntimeError("La simulación sólo está permitida en el entorno test")
    return mode


def _resolve(root_dir: Path, configured: str) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else root_dir / path


def _territorial_destination(evidence_dir: Path, configured_path: str) -> Path:
    configured = Path(configured_path)
    if configured.is_absolute():
        raise ValueError(f"materialized_path debe ser relativo al producto territorial: {configured_path}")
    destination = (evidence_dir / "materialized" / configured).resolve()
    staging_root = (evidence_dir / "materialized").resolve()
    try:
        destination.relative_to(staging_root)
    except ValueError as exc:
        raise ValueError(f"materialized_path sale del área temporal: {configured_path}") from exc
    return destination


def _section_publication_identity(*, policy_root: Path | None = None) -> dict:
    root = (policy_root or PROJECT_ROOT).resolve()
    matrix_path = (root / PREPARATION_MATRIX).resolve()
    if not matrix_path.is_file():
        raise ValueError(
            f"SECTION_PUBLICATION_IDENTITY_MISSING: no existe {PREPARATION_MATRIX}"
        )
    matrix = load_yaml(matrix_path)
    policy = matrix.get("population_section_policy") or {}
    evidence_rel = str(policy.get("availability_evidence") or "").strip()
    current_collection = str(policy.get("current_section_collection") or "").strip()
    provider = str(policy.get("provider") or "").strip()
    if not evidence_rel or not current_collection or not provider:
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_MISSING: "
            "faltan availability_evidence/current_section_collection/provider"
        )

    evidence_path = (root / evidence_rel).resolve()
    try:
        evidence_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            f"SECTION_PUBLICATION_IDENTITY_INVALID: evidencia fuera del repositorio: {evidence_rel}"
        ) from exc
    if not evidence_path.is_file():
        raise ValueError(
            f"SECTION_PUBLICATION_IDENTITY_MISSING: no existe {evidence_rel}"
        )

    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(
            f"SECTION_PUBLICATION_IDENTITY_INVALID: evidencia ilegible: {evidence_rel}"
        ) from exc
    if not isinstance(evidence, dict):
        raise ValueError("SECTION_PUBLICATION_IDENTITY_INVALID: evidencia no es objeto")
    if evidence.get("schema") != "ddd.official-temporal-availability-evidence/1.0":
        raise ValueError("SECTION_PUBLICATION_IDENTITY_INVALID: schema no reconocido")
    if str(evidence.get("provider") or "").strip() != provider:
        raise ValueError("SECTION_PUBLICATION_IDENTITY_INVALID: proveedor incoherente")

    check = (evidence.get("checks") or {}).get("census_sections")
    if not isinstance(check, dict):
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_INVALID: falta census_sections"
        )
    response = str(check.get("preserved_response") or "")
    declared_digest = str(check.get("response_sha256") or "").strip().lower()
    available = check.get("available_years")
    if not response or not declared_digest or not isinstance(available, list) or not available:
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_INVALID: census_sections incompleto"
        )
    actual_digest = sha256_bytes(response.encode("utf-8"))
    if declared_digest != actual_digest:
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_DIGEST_MISMATCH: "
            f"{declared_digest} != {actual_digest}"
        )
    try:
        years = sorted({int(value) for value in available})
        latest = int(check.get("latest_available_year"))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_INVALID: años no normalizables"
        ) from exc
    if latest != max(years):
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_INVALID: latest_available_year incoherente"
        )
    collection_identifier = current_collection.rsplit(":", 1)[-1]
    if collection_identifier not in response or f"Secciones_{latest}" not in response:
        raise ValueError(
            "SECTION_PUBLICATION_IDENTITY_UNPROVEN: "
            f"{current_collection} no queda vinculada de forma durable a Secciones_{latest}"
        )
    return {
        "latest_available_year": latest,
        "current_collection": current_collection,
        "evidence": evidence_rel,
        "evidence_sha256": sha256_bytes(evidence_path.read_bytes()),
    }


def _ogc_endpoint(
    source: dict,
    edition: int,
    *,
    policy_root: Path | None = None,
) -> str:
    identity = _section_publication_identity(policy_root=policy_root)
    requested = int(edition)
    latest = int(identity["latest_available_year"])
    if requested > latest:
        raise ValueError(
            f"SECTION_YEAR_NOT_ACCREDITED: {requested} > {latest}"
        )
    if requested == latest:
        source_collection = str(source.get("current_collection") or "").strip()
        if source_collection != identity["current_collection"]:
            raise ValueError(
                "SECTION_PUBLICATION_IDENTITY_MISMATCH: "
                f"catálogo={source_collection or 'vacío'} "
                f"política={identity['current_collection']}"
            )
        endpoint = str(source.get("current_endpoint") or "").strip()
        if not endpoint:
            raise ValueError(
                "Fuente OGC sin current_endpoint para el seccionado vigente acreditado"
            )
        return endpoint
    endpoint = str(source.get("endpoint_template") or "").strip()
    if not endpoint:
        raise ValueError("Fuente OGC sin endpoint_template histórico")
    return endpoint.format(edition=requested)


def _source_urls(
    source: dict,
    edition: int,
    provinces: list[dict],
    *,
    policy_root: Path | None = None,
) -> list[str]:
    kind = source.get("kind")
    if kind == "static_csv":
        return [str(source["url"])]
    if kind == "ogc_features":
        endpoint = _ogc_endpoint(source, edition, policy_root=policy_root)
        filter_field = str(source["territorial_filter_field"])
        feature_filter = str(source.get("feature_filter") or "")
        urls = []
        for province in provinces:
            # Filtrar remotamente sólo por provincia. La API del INE expone TIPO,
            # pero sus valores/semántica no son estables entre colecciones anuales.
            # La selección de secciones se hace después de forma determinista con
            # TIPO/CSEC/CUSEC sobre la respuesta territorial.
            clauses = [f"{filter_field}='{province['code']}'"]
            params = {"f": "application/geo+json", "filter": " AND ".join(clauses), "filter-lang": "cql2-text", "limit": "10000"}
            urls.append(endpoint + "?" + urlencode(params))
        return urls
    raise ValueError(f"Tipo de fuente no soportado: {kind}")


def _ensure_snapshot_metadata(binding: dict, edition: int) -> dict:
    snapshot = binding.get("snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError("verified_snapshot exige bloque snapshot")
    missing = [key for key in SNAPSHOT_REQUIRED if snapshot.get(key) in (None, "")]
    if missing:
        raise ValueError("verified_snapshot incompleto: " + ", ".join(missing))
    if int(snapshot["edition"]) != edition:
        raise ValueError("La edición de la copia verificada no coincide con la solicitada")
    return snapshot


def _read_snapshot(root_dir: Path, evidence_dir: Path, binding: dict, configured_path: str, edition: int) -> tuple[bytes, dict]:
    snapshot = _ensure_snapshot_metadata(binding, edition)
    path = _resolve(root_dir, str(snapshot["path"])).resolve()
    destination = _territorial_destination(evidence_dir, configured_path)
    if path == destination:
        raise ValueError(f"Origen oficial y destino territorial resuelven al mismo fichero: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"No existe la copia oficial declarada: {snapshot['path']}")
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    expected = str(snapshot["expected_sha256"]).lower()
    if actual.lower() != expected:
        raise ValueError(f"Huella de copia incorrecta: {actual} != {expected}")
    return payload, {
        "snapshot_path": str(snapshot["path"]),
        "snapshot_resolved_path": str(path),
        "snapshot_sha256": actual,
        "snapshot_bytes": len(payload),
        "snapshot_official_origin_url": str(snapshot["official_origin_url"]),
        "snapshot_acquired_at": str(snapshot["acquired_at"]),
        "snapshot_edition": int(snapshot["edition"]),
        "territorial_resolved_path": str(destination),
    }


def _looks_like_html(payload: bytes) -> bool:
    prefix = payload[:2048].lstrip().lower()
    return prefix.startswith(b"<html") or prefix.startswith(b"<!doctype html") or b"<body" in prefix


def _detect_delimiter(text: str) -> str:
    first = text.splitlines()[0] if text.splitlines() else ""
    counts = {delim: first.count(delim) for delim in ("\t", ";", ",")}
    delimiter = max(counts, key=counts.get)
    if counts[delimiter] == 0:
        raise ValueError("No se reconoce un CSV delimitado")
    return delimiter


def _normalize_section_id(value: object) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    if len(digits) < 10:
        digits = digits.zfill(10)
    return digits[:10]


def _population_rules(declaration: dict) -> dict:
    rules = declaration.get("population_validation") or {}
    required_columns = rules.get("required_columns") or ["Periodo", "Sexo", "Edad", "Secciones", "Total"]
    return {
        "required_columns": [str(x) for x in required_columns],
        "year_col": str(rules.get("year_col") or "Periodo"),
        "sex_col": str(rules.get("sex_col") or "Sexo"),
        "age_col": str(rules.get("age_col") or "Edad"),
        "section_col": str(rules.get("section_col") or "Secciones"),
        "population_col": str(rules.get("population_col") or "Total"),
        "sex_total_values": [str(x) for x in (rules.get("sex_total_values") or ["Total"])],
        "age_total_values": [str(x) for x in (rules.get("age_total_values") or ["Todas las edades"])],
    }


def _filter_population(payload: bytes, declaration: dict, edition: int, province_codes: list[str]) -> tuple[bytes, dict]:
    if _looks_like_html(payload):
        raise ValueError("La fuente de población contiene HTML, no CSV")
    bio = io.BytesIO(payload)
    zf = None
    raw = None
    text_stream = None
    try:
        if zipfile.is_zipfile(bio):
            zf = zipfile.ZipFile(bio)
            members = [name for name in zf.namelist() if not name.endswith("/") and name.lower().endswith((".csv", ".tsv", ".txt")) and "__macosx/" not in name.lower()]
            if not members:
                raise ValueError("La copia de población no contiene CSV")
            raw = zf.open(members[0], "r")
            prefix = raw.read(2048)
            if _looks_like_html(prefix):
                raise ValueError("La fuente de población contiene HTML, no CSV")
            raw.close()
            raw = zf.open(members[0], "r")
            text_stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            first = text_stream.readline()
            delimiter = _detect_delimiter(first)
            text_stream.detach().close()
            raw = zf.open(members[0], "r")
            text_stream = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        else:
            text = payload.decode("utf-8-sig")
            delimiter = _detect_delimiter(text)
            text_stream = io.StringIO(text)
        reader = csv.DictReader(text_stream, delimiter=delimiter)
        if not reader.fieldnames:
            raise ValueError("CSV de población sin cabecera")
        rules = _population_rules(declaration)
        missing_columns = [col for col in rules["required_columns"] if col not in reader.fieldnames]
        if missing_columns:
            raise ValueError("CSV de población sin columnas obligatorias: " + ", ".join(missing_columns))
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=reader.fieldnames, delimiter=delimiter, lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        seen_provinces: set[str] = set()
        seen_sections: set[str] = set()
        rows_out = 0
        pertinent_rows = 0
        territorial_exclusions = 0
        aggregate_counts = {"national": 0, "provincial": 0, "municipal": 0}
        aggregate_causes = {
            "national": "TOTAL_NACIONAL_WITHOUT_LOWER_LEVELS",
            "provincial": "PROVINCIA_WITHOUT_MUNICIPIO_OR_SECCION",
            "municipal": "MUNICIPIO_WITHOUT_SECCION",
        }
        selected_population_total = 0
        row_issues: list[dict] = []
        unobserved_sections: list[str] = []

        def record_row_issue(reason: str, row: dict) -> None:
            diagnostic_row = {
                key: row.get(key)
                for key in (
                    rules["year_col"],
                    rules["sex_col"],
                    rules["age_col"],
                    "Total Nacional",
                    "Provincias",
                    "Municipios",
                    rules["section_col"],
                    rules["population_col"],
                )
                if key in row
            }
            row_issues.append({"reason": reason, "row": diagnostic_row})

        for row in reader:
            if str(row.get(rules["year_col"], "")).strip() != str(edition):
                continue
            if str(row.get(rules["sex_col"], "")).strip() not in rules["sex_total_values"]:
                continue
            if str(row.get(rules["age_col"], "")).strip() not in rules["age_total_values"]:
                continue
            pertinent_rows += 1
            raw_section = row.get(rules["section_col"])
            section_id = _normalize_section_id(raw_section)
            if not section_id:
                # INE 65034 repite los ancestros de la jerarquía en niveles
                # inferiores: una fila provincial puede conservar Total Nacional y
                # una municipal puede conservar Total Nacional + Provincia. El nivel
                # efectivo lo determina el descendiente más específico presente.
                national = str(row.get("Total Nacional") or "").strip()
                province_value = str(row.get("Provincias") or "").strip()
                municipality = str(row.get("Municipios") or "").strip()
                raw_section_text = str(raw_section or "").strip()
                if raw_section_text:
                    province_digits = "".join(ch for ch in province_value if ch.isdigit())
                    if province_digits and province_digits[:2].zfill(2) not in province_codes:
                        territorial_exclusions += 1
                        continue
                    record_row_issue(f"SECTION_ID_INVALID: población: {raw_section!r}", row)
                    continue
                if municipality:
                    if not province_value:
                        record_row_issue(
                            "SECTION_ID_INVALID: población: sección ausente con jerarquía "
                            "INE 65034 contradictoria: municipio sin provincia: "
                            f"Total Nacional={national!r}, Provincias={province_value!r}, "
                            f"Municipios={municipality!r}",
                            row,
                        )
                        continue
                    aggregate_counts["municipal"] += 1
                    continue
                if province_value:
                    aggregate_counts["provincial"] += 1
                    continue
                if national:
                    aggregate_counts["national"] += 1
                    continue
                record_row_issue(
                    "SECTION_ID_INVALID: población: sección ausente con jerarquía "
                    f"INE 65034 ambigua/incompatible: Total Nacional={national!r}, "
                    f"Provincias={province_value!r}, Municipios={municipality!r}",
                    row,
                )
                continue
            section_province = section_id[:2]
            province_value = str(row.get("Provincias") or "").strip()
            municipality = str(row.get("Municipios") or "").strip()
            province_digits = "".join(ch for ch in province_value if ch.isdigit())
            municipality_digits = "".join(ch for ch in municipality if ch.isdigit())
            declared_province = province_digits[:2].zfill(2) if province_digits else ""
            municipality_province = municipality_digits[:2].zfill(2) if municipality_digits else ""
            points_to_requested = any(
                code in province_codes
                for code in (section_province, declared_province, municipality_province)
                if code
            )

            hierarchy_issue = None
            if municipality and not province_value:
                hierarchy_issue = "SECTION_HIERARCHY_MISMATCH: sección con municipio pero sin provincia"
            elif declared_province and declared_province != section_province:
                hierarchy_issue = "SECTION_HIERARCHY_MISMATCH: código de provincia no coincide con sección"
            elif municipality_digits and municipality_digits[:5].zfill(5) != section_id[:5]:
                hierarchy_issue = "SECTION_HIERARCHY_MISMATCH: código de municipio no coincide con sección"

            if hierarchy_issue:
                if points_to_requested:
                    record_row_issue(hierarchy_issue, row)
                else:
                    territorial_exclusions += 1
                continue

            if section_province not in province_codes:
                territorial_exclusions += 1
                continue
            if section_id in seen_sections:
                record_row_issue(
                    f"SECTION_ID_DUPLICATE_AFTER_NORMALIZATION: población: {section_id}",
                    row,
                )
                continue
            # INE 65034 conserva identidades seccionales históricas sin observación
            # para periodos posteriores. Un Total vacío no equivale a población cero:
            # se omite del conjunto poblacional y la compatibilidad con el seccionado
            # oficial decide después si la ausencia es legítima o bloqueante.
            raw_population = row.get(rules["population_col"])
            if raw_population is None or str(raw_population).strip() == "":
                unobserved_sections.append(section_id)
                continue
            # Valida sin reescribir el valor: cero explícito se conserva tal cual.
            try:
                population_value = parse_population_value(
                    raw_population,
                    section_id=section_id,
                    label="población adquirida",
                )
            except Exception as exc:
                record_row_issue(str(exc), row)
                continue
            selected_population_total += population_value
            seen_sections.add(section_id)
            writer.writerow(row)
            seen_provinces.add(section_province)
            rows_out += 1
        if row_issues:
            raise ValueError(
                "POPULATION_SOURCE_ROWS_INVALID: "
                f"count={len(row_issues)}; issues="
                + json.dumps(row_issues, ensure_ascii=False, sort_keys=True)
            )
        classified_rows = (
            sum(aggregate_counts.values())
            + rows_out
            + territorial_exclusions
            + len(unobserved_sections)
        )
        if pertinent_rows != classified_rows:
            raise ValueError(
                "POPULATION_ROW_RECONCILIATION_FAILED: "
                f"pertinentes={pertinent_rows}, clasificados={classified_rows}"
            )
        if rows_out == 0:
            raise ValueError(f"No hay filas de población total para la edición {edition}")
        if seen_provinces != set(province_codes):
            raise ValueError(f"Cobertura provincial de población incorrecta: {sorted(seen_provinces)} != {sorted(province_codes)}")
        return ("\ufeff" + output.getvalue()).encode("utf-8"), {
            "format": "csv",
            "delimiter": "tab" if delimiter == "\t" else delimiter,
            "columns": list(reader.fieldnames),
            "edition": edition,
            "population_filter": {"sex": rules["sex_total_values"], "age": rules["age_total_values"]},
            "provinces": sorted(seen_provinces),
            "rows": rows_out,
            "pertinent_rows_examined": pertinent_rows,
            "aggregate_exclusions": {
                "total": sum(aggregate_counts.values()),
                "by_level": aggregate_counts,
                "causes": aggregate_causes,
            },
            "territorial_exclusions": {
                "count": territorial_exclusions,
                "cause": "SECTION_PROVINCE_OUTSIDE_REQUESTED_SCOPE",
            },
            "row_reconciliation": {
                "pertinent": pertinent_rows,
                "classified_aggregates": sum(aggregate_counts.values()),
                "accepted_sections": rows_out,
                "unobserved_sections": len(unobserved_sections),
                "territorial_exclusions": territorial_exclusions,
                "balanced": pertinent_rows == classified_rows,
            },
            "unobserved_sections": {
                "count": len(unobserved_sections),
                "section_ids": sorted(unobserved_sections),
                "cause": "INE_65034_SECTION_WITHOUT_POPULATION_OBSERVATION",
                "population_semantics": "ABSENT_NOT_ZERO",
            },
            "selected_section_population_total": selected_population_total,
        }
    finally:
        try:
            if text_stream is not None:
                text_stream.close()
        except Exception:
            pass
        try:
            if zf is not None:
                zf.close()
        except Exception:
            pass


def _zip_single(member: str, payload: bytes) -> bytes:
    out = io.BytesIO()
    info = zipfile.ZipInfo(member, date_time=(2025, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(out, "w") as zf:
        zf.writestr(info, payload)
    return out.getvalue()


def _read_sections_from_snapshot(payload: bytes, filter_field: str, section_id_field: str, province_codes: list[str]) -> tuple[list[dict], str | None]:
    with tempfile.TemporaryDirectory(prefix="ddd_snapshot_") as td:
        archive = Path(td) / "snapshot.zip"
        archive.write_bytes(payload)
        if not zipfile.is_zipfile(archive):
            raise ValueError("La copia de secciones no es un ZIP válido")
        with zipfile.ZipFile(archive) as zf:
            shp_members = [n for n in zf.namelist() if n.lower().endswith(".shp") and "__macosx/" not in n.lower()]
            if not shp_members:
                raise ValueError("La copia de secciones no contiene shapefile")
            zf.extractall(Path(td) / "x")
            shp = Path(td) / "x" / shp_members[0]
        try:
            import geopandas as gpd
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"geopandas es obligatorio para copiar secciones verificadas: {exc}")
        gdf = gpd.read_file(shp)
        if gdf.crs is None or str(gdf.crs).strip() == "":
            raise ValueError("CRS_MISSING: copia verificada de seccionado")
        if bool(gdf.geometry.isna().any()):
            raise ValueError(
                "GEOMETRY_NULL: copia verificada de seccionado: "
                f"count={int(gdf.geometry.isna().sum())}"
            )
        if bool(gdf.geometry.is_empty.any()):
            raise ValueError(
                "GEOMETRY_EMPTY: copia verificada de seccionado: "
                f"count={int(gdf.geometry.is_empty.sum())}"
            )
        if filter_field not in gdf.columns or section_id_field not in gdf.columns:
            raise ValueError("La copia de secciones no contiene campos territoriales obligatorios")
        gdf[filter_field] = gdf[filter_field].astype(str).str.zfill(2)
        if "TIPO" in gdf.columns:
            gdf = gdf[gdf["TIPO"].astype(str) == "SECCION"]
        gdf = gdf[gdf[filter_field].isin(province_codes)].copy()
        if gdf.empty:
            raise ValueError("La copia verificada no contiene secciones de las provincias declaradas")
        features = json.loads(gdf.to_json()).get("features") or []
        crs = gdf.crs.to_string() if gdf.crs else None
        return features, crs


def _collect_live_sections(
    source: dict,
    source_year: int,
    provinces: list[dict],
    fetcher: FetchBytes,
    *,
    evidence_dir: Path | None = None,
    source_id: str = "secciones_censales",
) -> tuple[list[dict], list[str], dict, str]:
    urls = _source_urls(source, source_year, provinces)
    filter_field = str(source["territorial_filter_field"])
    section_id_field = str(source["section_id_field"])
    all_features: list[dict] = []
    seen_ids: set[str] = set()
    coverage: dict[str, int] = {}
    raw_responses: list[dict] = []
    declared_crs = str(source.get("crs") or "").strip()
    if not declared_crs:
        raise ValueError("CRS_MISSING: fuente OGC sin CRS declarado en catálogo")
    for province, url in zip(provinces, urls):
        code = province["code"]
        payload = fetcher(url)
        if evidence_dir is not None:
            raw_responses.append(
                persist_raw_ogc_response(
                    evidence_dir,
                    source_id=source_id,
                    source_year=source_year,
                    province_code=code,
                    url=url,
                    payload=payload,
                )
            )
        if _looks_like_html(payload):
            raise ValueError(f"La fuente de secciones devolvió HTML para CPRO={code}")
        data = json.loads(payload.decode("utf-8-sig"))
        rows = data.get("features") or []
        if not rows:
            raise ValueError(f"No hay secciones para la provincia {code}")
        count = 0
        for feature in rows:
            props = feature.get("properties") or {}
            actual = str(props.get(filter_field, "")).zfill(2)
            if actual != code:
                raise ValueError(f"Provincia inesperada en secciones: {actual}; solicitada {code}")
            section_id = str(props.get(section_id_field) or "").strip()
            if not section_id:
                raise ValueError("Entidad sin identificador oficial")
            tipo = str(props.get("TIPO") or "").strip().upper()
            csec = str(props.get("CSEC") or "").strip()
            # Las colecciones OGC del INE pueden contener también distritos.
            # Preferimos TIPO cuando identifica una sección; como respaldo,
            # CSEC distinto de 000 identifica el nivel sección.
            is_section = ("SECC" in tipo) if tipo else bool(csec and csec != "000")
            if not is_section:
                continue
            normalized_section_id = _normalize_section_id(section_id)
            if not normalized_section_id:
                raise ValueError(f"Clave geométrica no normalizable: {section_id!r}")
            if normalized_section_id in seen_ids:
                raise ValueError(
                    f"Clave geométrica duplicada antes de materializar: {normalized_section_id}"
                )
            seen_ids.add(normalized_section_id)
            all_features.append(feature)
            count += 1
        coverage[code] = count
    if set(coverage) != {row["code"] for row in provinces}:
        raise ValueError("Cobertura provincial de secciones incompleta")
    observed_columns = sorted({
        str(key)
        for feature in all_features
        for key in ((feature.get("properties") or {}).keys())
    })
    return all_features, urls, {
        "provinces": sorted(coverage),
        "sections_by_province": coverage,
        "sections": len(all_features),
        "columns": observed_columns,
        "raw_responses": raw_responses,
    }, declared_crs


def _persist_geometry_evidence(
    *,
    evidence_dir: Path,
    source_id: str,
    source_year: int,
    content_checks: dict,
    snapshot_identity: dict | None = None,
    derived_path: str | None = None,
    derived_payload: bytes | None = None,
    materialization_validation: dict | None = None,
) -> dict:
    report = content_checks.get("geometry_normalization")
    if not isinstance(report, dict):
        raise ValueError("GEOMETRY_NORMALIZATION_EVIDENCE_MISSING_REPORT")
    reference = persist_geometry_normalization_evidence(
        evidence_dir,
        source_id=source_id,
        source_year=source_year,
        report=report,
        raw_records=list(content_checks.get("raw_responses") or []),
        snapshot_identity=snapshot_identity,
        derived_path=derived_path,
        derived_payload=derived_payload,
        materialization_validation=materialization_validation,
    )
    content_checks["geometry_normalization_evidence"] = reference
    return reference


def _geometry_declared_use(
    root_dir: Path,
    *,
    territory_id: str,
    edition: int,
    role: str,
) -> dict:
    """Resuelve el consumidor geométrico sin inventar umbrales nuevos."""
    if role == "population_sectioning_origin":
        return {
            "role": role,
            "consumer": "population_sectioning_compatibility",
            "gate": "assert_materialized_territorial_gate",
            "required_evidence": (
                "compatibilidad_poblacion_seccionado.json "
                "geometry_admissibility decision READY"
            ),
        }

    if role != "target_sectioning":
        return {
            "role": role,
            "consumer": "unsupported",
        }

    contract_path = (
        Path(root_dir)
        / "territorios"
        / territory_id
        / "config"
        / f"{territory_id}_{int(edition)}.yaml"
    )
    if not contract_path.is_file():
        return {
            "role": role,
            "consumer": "modulo_02_construir_adyacencias",
            "contract_path": contract_path.as_posix(),
            "adjacency": {},
        }
    cfg = load_yaml(contract_path)
    m02 = (
        ((cfg.get("modulos") or {}).get(
            "modulo_02_construir_adyacencias"
        ))
        or {}
    )
    adjacency = {
        "predicate": str(m02.get("predicate", "touches")),
        "working_crs": str(m02.get("working_crs", "EPSG:25830")),
        "min_shared_border_m": m02.get("min_shared_border_m"),
        # No se aplica el fallback de M02 para acreditar defectos de fuente:
        # un solape sólo es admisible si el contrato territorial lo declara.
        "max_precision_overlap_area_m2": (
            m02.get("max_precision_overlap_area_m2")
            if "max_precision_overlap_area_m2" in m02
            else None
        ),
    }
    return {
        "role": role,
        "consumer": "modulo_02_construir_adyacencias",
        "contract_path": contract_path.relative_to(root_dir).as_posix(),
        "adjacency": adjacency,
    }


def _normalize_sections_or_block(
    features: list[dict],
    source: dict,
    content_checks: dict,
    *,
    crs: str,
    evidence_dir: Path,
    source_id: str,
    source_year: int,
    snapshot_identity: dict | None = None,
    declared_use: dict | None = None,
) -> list[dict]:
    policy, policy_sha256, policy_path = load_geometry_policy()
    source_stage = (
        "RAW_SNAPSHOT_GEOMETRY_AFTER_VECTOR_READ_BEFORE_NORMALIZATION"
        if snapshot_identity
        else "RAW_SOURCE_FEATURE_AFTER_JSON_DECODE_BEFORE_GEOMETRY_TRANSFORMATION"
    )
    normalized, audit = normalize_official_features(
        features,
        str(source["section_id_field"]),
        crs=crs,
        coverage_field=str(source["territorial_filter_field"]),
        policy=policy,
        policy_sha256=policy_sha256,
        policy_path=policy_path,
        declared_use=declared_use,
        source_stage=source_stage,
    )
    raw_by_partition = {
        str(row.get("province_code") or "").zfill(2): row
        for row in (content_checks.get("raw_responses") or [])
        if isinstance(row, dict)
    }
    snapshot_sha256 = (
        str(snapshot_identity.get("snapshot_sha256") or "")
        if snapshot_identity else ""
    )
    for issue in audit.get("issues") or []:
        before = issue.get("before") or {}
        partition = str(before.get("source_partition") or "")
        raw_record = raw_by_partition.get(partition.zfill(2))
        if raw_record:
            before["raw_source_response_sha256"] = raw_record.get("sha256")
            before["raw_source_response_path"] = raw_record.get("path")
        elif snapshot_sha256:
            before["raw_source_response_sha256"] = snapshot_sha256
            before["raw_source_response_path"] = snapshot_identity.get(
                "snapshot_path"
            )
        else:
            before["raw_source_response_sha256"] = None
            before["raw_source_response_path"] = None

    content_checks["geometry_normalization"] = audit
    _persist_geometry_evidence(
        evidence_dir=evidence_dir,
        source_id=source_id,
        source_year=source_year,
        content_checks=content_checks,
        snapshot_identity=snapshot_identity,
    )
    if audit["decision"] != "READY":
        raise ValueError(
            "GEOMETRY_INVALID_AUDITED: "
            + json.dumps(
                {
                    "decision": audit["decision"],
                    "issues": audit["issues"],
                    "normalization_safety": audit.get(
                        "normalization_safety"
                    ),
                    "source_admissibility": audit.get(
                        "source_admissibility"
                    ),
                    "topology": audit["topology"],
                    "identity_and_attributes": audit[
                        "identity_and_attributes"
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    return normalized


def _write_shapefile_zip(
    features: list[dict],
    crs: str | None,
    *,
    section_id_field: str | None = None,
    source_partition_field: str | None = None,
    materialization_checks: dict | None = None,
) -> bytes:
    try:
        import geopandas as gpd
        from pyproj import CRS
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            f"geopandas es obligatorio para materializar secciones: {exc}"
        )
    if crs is None or not str(crs).strip():
        raise ValueError(
            "CRS_MISSING: no se puede materializar seccionado sin CRS acreditado"
        )
    try:
        CRS.from_user_input(crs)
    except Exception as exc:
        raise ValueError(f"CRS_INVALID: {crs!r}") from exc
    if materialization_checks is not None:
        materialization_checks.update({
            "decision": "PENDING",
            "stage": "PRE_SHAPEFILE_WRITE",
        })
    with tempfile.TemporaryDirectory(prefix="ddd_sections_") as td:
        shp = Path(td) / "seccionado.shp"
        try:
            gdf = gpd.GeoDataFrame.from_features(features, crs=crs)
            validate_geodataframe(
                gdf,
                label="seccionado normalizado antes de materializar",
            )
            if materialization_checks is not None:
                materialization_checks["stage"] = "SHAPEFILE_WRITE"
            gdf.to_file(shp, driver="ESRI Shapefile", index=False)

            if materialization_checks is not None:
                materialization_checks["stage"] = "POST_SHAPEFILE_WRITE_READBACK"
            reloaded = gpd.read_file(shp)
            if section_id_field:
                roundtrip = validate_materialization_roundtrip(
                    features,
                    reloaded,
                    section_id_field=section_id_field,
                    source_crs=str(crs),
                    source_partition_field=source_partition_field,
                )
                if materialization_checks is not None:
                    materialization_checks.update(roundtrip)
                if roundtrip["decision"] != "READY":
                    raise ValueError(
                        "GEOMETRY_POST_MATERIALIZATION_BLOCKED: "
                        + json.dumps(
                            {
                                "defects": roundtrip.get("defects") or [],
                                "attribute_changes": roundtrip.get(
                                    "attribute_changes"
                                ) or [],
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                    )
                validate_geodataframe(
                    reloaded,
                    label="seccionado derivado tras materialización",
                )
            else:
                validate_geodataframe(
                    reloaded,
                    label="seccionado derivado tras materialización",
                )
                if materialization_checks is not None:
                    materialization_checks.update({
                        "decision": "READY",
                        "stage": "POST_SHAPEFILE_WRITE_READBACK",
                        "note": "roundtrip identity not requested",
                    })
        except Exception as exc:
            if materialization_checks is not None:
                materialization_checks.update({
                    "decision": "BLOCKED",
                    "error": str(exc),
                })
                materialization_checks.setdefault(
                    "stage",
                    "MATERIALIZATION_STAGE_UNKNOWN",
                )
            raise

        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as zf:
            for file in sorted(Path(td).glob("seccionado.*")):
                info = zipfile.ZipInfo(
                    file.name,
                    date_time=(2025, 1, 1, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zf.writestr(info, file.read_bytes())
        return out.getvalue()


def _enrich_materialization_defects_with_source_lineage(
    content_checks: dict,
    *,
    snapshot_identity: dict | None = None,
) -> None:
    materialization = content_checks.get("geometry_materialization") or {}
    defects = materialization.get("defects") or []
    if not defects:
        return

    normalization = content_checks.get("geometry_normalization") or {}
    normalization_by_id = {
        str((issue.get("before") or {}).get("section_id") or ""): issue
        for issue in (normalization.get("issues") or [])
        if isinstance(issue, dict)
    }
    raw_by_partition = {
        str(row.get("province_code") or row.get("province") or "").zfill(2): row
        for row in (content_checks.get("raw_responses") or [])
        if isinstance(row, dict)
    }
    snapshot_sha256 = (
        str(snapshot_identity.get("snapshot_sha256") or "")
        if snapshot_identity else ""
    )
    snapshot_path = (
        snapshot_identity.get("snapshot_path")
        if snapshot_identity else None
    )

    for defect in defects:
        section_id = str(defect.get("section_id") or "")
        before = defect.get("before") or {}
        after = defect.get("after") or {}
        partition = str(
            defect.get("source_partition")
            or before.get("source_partition")
            or ""
        )
        source_issue = normalization_by_id.get(section_id) or {}
        source_before = source_issue.get("before") or {}
        raw_record = raw_by_partition.get(partition.zfill(2))
        defect["raw_source"] = {
            "section_id": section_id,
            "crs": source_before.get("crs") or before.get("crs"),
            "geometry_type": (
                source_before.get("geometry_type")
                or before.get("geometry_type")
            ),
            "geometry_sha256": (
                source_before.get("geometry_sha256")
                or before.get("geometry_sha256")
            ),
            "validity_reason": (
                source_before.get("validity_reason")
                or before.get("validity_reason")
            ),
            "response_sha256": (
                raw_record.get("sha256")
                if raw_record else (snapshot_sha256 or None)
            ),
            "response_path": (
                raw_record.get("path")
                if raw_record else snapshot_path
            ),
        }
        defect["pre_materialization"] = {
            "section_id": section_id,
            "crs": before.get("crs"),
            "geometry_type": before.get("geometry_type"),
            "geometry_sha256": before.get("geometry_sha256"),
            "validity_reason": before.get("validity_reason"),
        }
        defect["post_materialization"] = {
            "section_id": section_id,
            "crs": after.get("crs"),
            "geometry_type": after.get("geometry_type"),
            "geometry_sha256": after.get("geometry_sha256"),
            "validity_reason": after.get("validity_reason"),
        }


def _materialize_sections_with_evidence(
    features: list[dict],
    *,
    crs: str,
    section_id_field: str,
    source_partition_field: str | None = None,
    evidence_dir: Path,
    source_id: str,
    source_year: int,
    content_checks: dict,
    derived_path: str,
    snapshot_identity: dict | None = None,
) -> bytes:
    """Materializa y persiste el resultado de roundtrip incluso si éste bloquea."""
    materialization_checks: dict = {}
    content_checks["geometry_materialization"] = materialization_checks
    try:
        payload = _write_shapefile_zip(
            features,
            crs=crs,
            section_id_field=section_id_field,
            source_partition_field=source_partition_field,
            materialization_checks=materialization_checks,
        )
    except Exception:
        _enrich_materialization_defects_with_source_lineage(
            content_checks,
            snapshot_identity=snapshot_identity,
        )
        _persist_geometry_evidence(
            evidence_dir=evidence_dir,
            source_id=source_id,
            source_year=source_year,
            content_checks=content_checks,
            snapshot_identity=snapshot_identity,
            derived_path=derived_path,
            derived_payload=None,
            materialization_validation=materialization_checks,
        )
        raise

    _enrich_materialization_defects_with_source_lineage(
        content_checks,
        snapshot_identity=snapshot_identity,
    )
    _persist_geometry_evidence(
        evidence_dir=evidence_dir,
        source_id=source_id,
        source_year=source_year,
        content_checks=content_checks,
        snapshot_identity=snapshot_identity,
        derived_path=derived_path,
        derived_payload=payload,
        materialization_validation=materialization_checks,
    )
    return payload


def _write_materialized(evidence_dir: Path, configured_path: str, payload: bytes) -> tuple[Path, dict]:
    destination = _territorial_destination(evidence_dir, configured_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination, {"path": configured_path, "sha256": sha256_bytes(payload), "bytes": len(payload), "staged_path": str(destination)}


def _core(source_id: str, configured_path: str, payload: bytes | None, urls: list[str], edition: int) -> dict:
    return {"source_id": source_id, "path": configured_path, "sha256": sha256_bytes(payload) if payload is not None else None, "bytes": len(payload) if payload is not None else None, "urls": list(urls), "edition": edition}


def _resolved_consumer_contract(
    *,
    source_id: str,
    source: dict,
    binding: dict,
    declaration: dict,
    role: str,
    configured_path: str,
    effective_year: int,
    content_checks: dict,
) -> dict:
    """Contrato físico durable que deben consumir las fases posteriores.

    Conserva nombres, rutas y campos observados/declarados; no obliga al
    consumidor a reconstruirlos desde edition, territory o convenciones INE.
    """
    contract = {
        "schema": "ddd.resolved-source-binding/1.0",
        "source_id": source_id,
        "role": role,
        "path": configured_path,
        "effective_year": int(effective_year),
        "source_kind": str(source.get("kind") or ""),
        "source_format": str(source.get("format") or ""),
        "container": "zip" if configured_path.lower().endswith(".zip") else "file",
    }
    if role == "population":
        rules = _population_rules(declaration)
        delimiter = str(content_checks.get("delimiter") or "auto")
        if delimiter == "tab":
            delimiter = "\t"
        contract.update({
            "materialized_format": "csv",
            "archive_member": str(
                binding.get("archive_member")
                or source.get("output_name")
                or ""
            ),
            "encoding": "utf-8-sig",
            "delimiter": delimiter,
            "fields": {
                "section_id": rules["section_col"],
                "population": rules["population_col"],
                "year": rules["year_col"],
                "sex": rules["sex_col"],
                "age": rules["age_col"],
            },
            "filters": {
                "year_value": int(effective_year),
                "sex_total_values": list(rules["sex_total_values"]),
                "age_total_values": list(rules["age_total_values"]),
            },
        })
    elif role in {"target_sectioning", "population_sectioning_origin"}:
        contract.update({
            "materialized_format": "shapefile",
            "layer": "",
            "crs": str(source.get("crs") or ""),
            "fields": {
                "section_id": str(source.get("section_id_field") or ""),
                "territorial_filter": str(source.get("territorial_filter_field") or ""),
            },
        })
    return contract


def _render_runtime_value(value: object, *, edition: int, population_year: int, section_year: int) -> str:
    text = str(value or "")
    try:
        return text.format(
            year=edition,
            project_edition=edition,
            population_year=population_year,
            section_year=section_year,
        )
    except Exception:
        return text


def resolve_runtime_bindings(
    root_dir: Path,
    declaration: dict,
    *,
    territory_id: str,
    edition: int,
    population_year: int,
    section_year: int,
) -> dict:
    """Fija una vez los nombres runtime que producirán/consumirán los módulos.

    Una declaración futura puede sobrescribirlos explícitamente. Para los
    contratos españoles existentes se conservan los nombres operativos actuales,
    pero el valor queda materializado en el contrato durable y deja de requerir
    inferencias aguas abajo.
    """
    explicit = declaration.get("runtime_bindings") or {}
    contract_path = (
        root_dir
        / "territorios"
        / territory_id
        / "config"
        / f"{territory_id}_{edition}.yaml"
    )
    generation = {}
    if contract_path.is_file():
        generation = load_yaml(contract_path)
    modules = generation.get("modulos") or {}
    validation = generation.get("validation") or {}
    m02 = modules.get("modulo_02_construir_adyacencias") or {}
    m03 = modules.get("modulo_03_construir_grafo") or {}
    m04 = modules.get("modulo_04_generar_semillas") or {}

    section_id = str(
        explicit.get("section_id_field")
        or m02.get("id_field")
        or m03.get("id_field")
        or "CUSEC_KEY"
    )
    population_template = (
        explicit.get("population_field")
        or m03.get("pop_field")
        or m04.get("pop_field")
        or "POP_{population_year}"
    )
    # Si el contrato histórico usa el placeholder ambiguo {year}, el compilador
    # de fuentes lo resuelve por semántica poblacional, no por project edition.
    if str(population_template) == "POP_{year}":
        population_template = "POP_{population_year}"
    population_field = _render_runtime_value(
        population_template,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
    )
    province_field = str(
        explicit.get("province_field")
        or validation.get("province_field")
        or "CPRO"
    )
    municipality_field = str(
        explicit.get("municipality_field")
        or validation.get("municipality_field")
        or "CUMUN"
    )
    return {
        "section_id_field": section_id,
        "population_field": population_field,
        "province_field": province_field,
        "municipality_field": municipality_field,
    }


def _resolved_source_contract(
    *,
    root_dir: Path,
    declaration: dict,
    inventory: dict,
    territory_id: str,
    territory_name: str,
    edition: int,
    population_year: int,
    section_year: int,
) -> dict:
    available = [
        row for row in (inventory.get("sources") or [])
        if isinstance(row, dict) and row.get("availability") == "AVAILABLE"
    ]
    by_role: dict[str, dict] = {}
    for row in available:
        role = str(row.get("role") or "")
        binding = row.get("consumer_contract")
        if not role or not isinstance(binding, dict):
            continue
        source = json.loads(json.dumps(binding))
        source["artifact"] = {
            "path": str(row.get("path") or ""),
            "sha256": str(row.get("sha256") or ""),
            "bytes": int(row.get("bytes") or 0),
        }
        # El path del binding debe describir exactamente el artefacto acreditado.
        source["path"] = source["artifact"]["path"]
        by_role[role] = source

    required = {"population", "target_sectioning"}
    if not required.issubset(by_role):
        missing = sorted(required - set(by_role))
        raise ValueError(
            "RESOLVED_SOURCE_CONTRACT_INCOMPLETE: faltan roles " + ", ".join(missing)
        )

    runtime = resolve_runtime_bindings(
        root_dir,
        declaration,
        territory_id=territory_id,
        edition=edition,
        population_year=population_year,
        section_year=section_year,
    )
    contract = {
        "schema": "ddd.resolved-source-contract/1.0",
        "territory": {
            "territory_id": territory_id,
            "territory_name": territory_name,
            "project_edition": str(edition),
        },
        "temporal": {
            "population_year": int(population_year),
            "section_year": int(section_year),
        },
        "sources": {
            "population": by_role["population"],
            "sectioning": by_role["target_sectioning"],
        },
        "runtime": runtime,
        "transformations": [
            {
                "kind": "normalize_section_identifier",
                "from": "sources.sectioning.fields.section_id",
                "to": "runtime.section_id_field",
            },
            {
                "kind": "attach_population",
                "source_field": "sources.population.fields.population",
                "to": "runtime.population_field",
            },
        ],
    }
    if "population_sectioning_origin" in by_role:
        contract["sources"]["population_sectioning_origin"] = by_role[
            "population_sectioning_origin"
        ]
    canonical = json.dumps(
        contract,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    contract["contract_sha256"] = sha256_bytes(canonical)
    return contract


def _persist(evidence_dir: Path, resolved: dict, inventory: dict, provenance: dict, decision: dict) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "declaracion_materializacion.json": resolved,
        "inventario_fuentes.json": inventory,
        "manifiesto_procedencia.json": provenance,
        "decision_adquisicion.json": decision,
    }
    contract = inventory.get("resolved_source_contract")
    if isinstance(contract, dict):
        files["resolved_source_contract.json"] = contract
    for name, data in files.items():
        (evidence_dir / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def acquire(*, catalog: dict, declaration: dict, evidence_dir: Path, environment: str, acquisition_mode: str | None = None, fetcher: FetchBytes | None = None, root_dir: Path | None = None) -> tuple[dict, dict, dict, dict]:
    root_dir = (root_dir or Path.cwd()).resolve()
    evidence_dir = evidence_dir.resolve()
    territory_id, territory_name, edition, population_year, section_year, provinces = _territory(declaration)
    province_codes = [row["code"] for row in provinces]
    mode = _select_mode(declaration, environment, acquisition_mode)
    if mode == "simulated" and fetcher is None:
        raise ValueError("La simulación exige un fetcher inyectado por pruebas")
    fetch = fetcher or live_fetch
    required = _required_sources(catalog, declaration)
    header = {
        "territory_id": territory_id,
        "territory": territory_name,
        "edition": edition,
        "population_year": population_year,
        "section_year": section_year,
        "environment": environment,
        "acquisition_mode": mode,
    }
    if population_year == section_year:
        header["source_year"] = population_year
    resolved = {"schema": "ddd-source-materialization-declaration/1.1", **header, "materialization_root": str((evidence_dir / "materialized").resolve()), "sources": []}
    inventory = {"schema": "ddd-source-inventory/1.2", **header, "territorial_coverage": province_codes, "sources": []}
    provenance = {"schema": "ddd-source-provenance/1.2", **header, "sources": []}
    decision = {"schema": "ddd-source-acquisition-decision/1.1", **header, "decision": "READY", "reasons": []}

    target_geometry_use = _geometry_declared_use(
        root_dir,
        territory_id=territory_id,
        edition=edition,
        role="target_sectioning",
    )
    origin_geometry_use = _geometry_declared_use(
        root_dir,
        territory_id=territory_id,
        edition=edition,
        role="population_sectioning_origin",
    )

    for source_id, source, binding in required:
        configured_path = str(binding["materialized_path"])
        effective_year = population_year if source.get("kind") == "static_csv" else section_year
        official_urls = _source_urls(source, effective_year, provinces)
        payload_out: bytes | None = None
        content_checks: dict = {}
        snapshot_meta: dict = {}
        staged_meta: dict = {}
        try:
            destination = _territorial_destination(evidence_dir, configured_path)
            if mode == "verified_snapshot":
                source_payload, snapshot_meta = _read_snapshot(root_dir, evidence_dir, binding, configured_path, effective_year)
            elif source.get("kind") == "static_csv":
                source_payload = fetch(official_urls[0])
            else:
                source_payload = b""

            if source.get("kind") == "static_csv":
                filtered_csv, content_checks = _filter_population(source_payload, declaration, population_year, province_codes)
                member = str(binding.get("archive_member") or source.get("output_name") or "population.csv")
                payload_out = _zip_single(member, filtered_csv) if configured_path.lower().endswith(".zip") else filtered_csv
            elif source.get("kind") == "ogc_features":
                if mode == "verified_snapshot":
                    features, crs = _read_sections_from_snapshot(source_payload, str(source["territorial_filter_field"]), str(source["section_id_field"]), province_codes)
                    coverage = sorted({str((f.get("properties") or {}).get(source["territorial_filter_field"], "")).zfill(2) for f in features})
                    if coverage != sorted(province_codes):
                        raise ValueError(f"Cobertura provincial de secciones incorrecta: {coverage}")
                    content_checks = {
                        "provinces": coverage,
                        "sections": len(features),
                        "columns": sorted({
                            str(key)
                            for feature in features
                            for key in ((feature.get("properties") or {}).keys())
                        }),
                    }
                    features = _normalize_sections_or_block(
                        features,
                        source,
                        content_checks,
                        crs=str(crs),
                        evidence_dir=evidence_dir,
                        source_id=source_id,
                        source_year=section_year,
                        snapshot_identity=snapshot_meta,
                        declared_use=target_geometry_use,
                    )
                    payload_out = _materialize_sections_with_evidence(
                        features,
                        crs=str(crs),
                        section_id_field=str(source["section_id_field"]),
                        source_partition_field=str(source["territorial_filter_field"]),
                        evidence_dir=evidence_dir,
                        source_id=source_id,
                        source_year=section_year,
                        content_checks=content_checks,
                        derived_path=configured_path,
                        snapshot_identity=snapshot_meta,
                    )
                else:
                    features, official_urls, content_checks, live_crs = _collect_live_sections(
                        source,
                        section_year,
                        provinces,
                        fetch,
                        evidence_dir=evidence_dir,
                        source_id=source_id,
                    )
                    features = _normalize_sections_or_block(
                        features,
                        source,
                        content_checks,
                        crs=str(live_crs),
                        evidence_dir=evidence_dir,
                        source_id=source_id,
                        source_year=section_year,
                        declared_use=target_geometry_use,
                    )
                    payload_out = _materialize_sections_with_evidence(
                        features,
                        crs=str(live_crs),
                        section_id_field=str(source["section_id_field"]),
                        source_partition_field=str(source["territorial_filter_field"]),
                        evidence_dir=evidence_dir,
                        source_id=source_id,
                        source_year=section_year,
                        content_checks=content_checks,
                        derived_path=configured_path,
                    )
            else:
                raise ValueError(f"Tipo de fuente no soportado: {source.get('kind')}")

            _, staged_meta = _write_materialized(evidence_dir, configured_path, payload_out)
            role = "population" if source.get("kind") == "static_csv" else "target_sectioning"
            core = {**_core(source_id, configured_path, payload_out, official_urls, effective_year), "role": role}
            consumer_contract = _resolved_consumer_contract(
                source_id=source_id,
                source=source,
                binding=binding,
                declaration=declaration,
                role=role,
                configured_path=configured_path,
                effective_year=effective_year,
                content_checks=content_checks,
            )
            resolved["sources"].append({
                **core,
                "staged_path": str(destination),
                "consumer_contract": consumer_contract,
            })
            derivation = content_checks.get("geometry_normalization_evidence")
            inventory["sources"].append({
                **core,
                "availability": "AVAILABLE",
                "content_checks": content_checks,
                "consumer_contract": consumer_contract,
                "derivation": derivation,
                **staged_meta,
            })
            provenance["sources"].append({
                **core,
                "provider": source.get("provider"),
                "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
                "mode": mode,
                "consumer_contract": consumer_contract,
                "derivation": derivation,
                **snapshot_meta,
                **staged_meta,
            })

            if source.get("kind") == "ogc_features" and population_year != section_year:
                origin_path = f"inputs/seccionado_origen_poblacion_{population_year}.zip"
                origin_urls = _source_urls(source, population_year, provinces)
                origin_snapshot_meta: dict = {}
                if mode == "verified_snapshot":
                    origin_snapshot = binding.get("population_sectioning_snapshot")
                    if not isinstance(origin_snapshot, dict):
                        raise ValueError(
                            "Años población/seccionado distintos sin seccionado de origen verificable"
                        )
                    origin_binding = dict(binding)
                    origin_binding["snapshot"] = origin_snapshot
                    origin_payload_raw, origin_snapshot_meta = _read_snapshot(
                        root_dir, evidence_dir, origin_binding, origin_path, population_year
                    )
                    origin_features, origin_crs = _read_sections_from_snapshot(
                        origin_payload_raw,
                        str(source["territorial_filter_field"]),
                        str(source["section_id_field"]),
                        province_codes,
                    )
                    origin_checks = {
                        "provinces": sorted({
                            str((f.get("properties") or {}).get(source["territorial_filter_field"], "")).zfill(2)
                            for f in origin_features
                        }),
                        "sections": len(origin_features),
                    }
                    origin_features = _normalize_sections_or_block(
                        origin_features,
                        source,
                        origin_checks,
                        crs=str(origin_crs),
                        evidence_dir=evidence_dir,
                        source_id=source_id + "_origen_poblacion",
                        source_year=population_year,
                        snapshot_identity=origin_snapshot_meta,
                        declared_use=origin_geometry_use,
                    )
                    origin_payload = _materialize_sections_with_evidence(
                        origin_features,
                        crs=str(origin_crs),
                        section_id_field=str(source["section_id_field"]),
                        source_partition_field=str(source["territorial_filter_field"]),
                        evidence_dir=evidence_dir,
                        source_id=source_id + "_origen_poblacion",
                        source_year=population_year,
                        content_checks=origin_checks,
                        derived_path=origin_path,
                        snapshot_identity=origin_snapshot_meta,
                    )
                else:
                    origin_features, origin_urls, origin_checks, origin_crs = _collect_live_sections(
                        source,
                        population_year,
                        provinces,
                        fetch,
                        evidence_dir=evidence_dir,
                        source_id=source_id + "_origen_poblacion",
                    )
                    origin_features = _normalize_sections_or_block(
                        origin_features,
                        source,
                        origin_checks,
                        crs=str(origin_crs),
                        evidence_dir=evidence_dir,
                        source_id=source_id + "_origen_poblacion",
                        source_year=population_year,
                        declared_use=origin_geometry_use,
                    )
                    origin_payload = _materialize_sections_with_evidence(
                        origin_features,
                        crs=str(origin_crs),
                        section_id_field=str(source["section_id_field"]),
                        source_partition_field=str(source["territorial_filter_field"]),
                        evidence_dir=evidence_dir,
                        source_id=source_id + "_origen_poblacion",
                        source_year=population_year,
                        content_checks=origin_checks,
                        derived_path=origin_path,
                    )
                origin_destination, origin_staged = _write_materialized(
                    evidence_dir, origin_path, origin_payload
                )
                origin_core = {
                    **_core(
                        source_id + "_origen_poblacion",
                        origin_path,
                        origin_payload,
                        origin_urls,
                        population_year,
                    ),
                    "role": "population_sectioning_origin",
                }
                origin_consumer_contract = _resolved_consumer_contract(
                    source_id=source_id + "_origen_poblacion",
                    source=source,
                    binding=binding,
                    declaration=declaration,
                    role="population_sectioning_origin",
                    configured_path=origin_path,
                    effective_year=population_year,
                    content_checks=origin_checks,
                )
                resolved["sources"].append({
                    **origin_core,
                    "staged_path": str(origin_destination),
                    "consumer_contract": origin_consumer_contract,
                })
                origin_derivation = origin_checks.get(
                    "geometry_normalization_evidence"
                )
                inventory["sources"].append({
                    **origin_core,
                    "availability": "AVAILABLE",
                    "content_checks": origin_checks,
                    "consumer_contract": origin_consumer_contract,
                    "derivation": origin_derivation,
                    **origin_staged,
                })
                provenance["sources"].append({
                    **origin_core,
                    "provider": source.get("provider"),
                    "acquired_at_utc": datetime.now(timezone.utc).isoformat(),
                    "mode": mode,
                    "consumer_contract": origin_consumer_contract,
                    "derivation": origin_derivation,
                    **origin_snapshot_meta,
                    **origin_staged,
                })
        except Exception as exc:
            core = _core(source_id, configured_path, payload_out, official_urls, effective_year)
            resolved["sources"].append(dict(core))
            derivation = content_checks.get("geometry_normalization_evidence")
            inventory["sources"].append({
                **core,
                "availability": "BLOCKED",
                "error": str(exc),
                "content_checks": content_checks,
                "derivation": derivation,
                **staged_meta,
            })
            provenance["sources"].append({
                **core,
                "provider": source.get("provider"),
                "mode": mode,
                "derivation": derivation,
                **snapshot_meta,
                **staged_meta,
            })
            decision["decision"] = "BLOCKED"
            decision["reasons"].append({"source_id": source_id, "reason": str(exc)})
            _persist(evidence_dir, resolved, inventory, provenance, decision)
            continue
        _persist(evidence_dir, resolved, inventory, provenance, decision)

    if decision["decision"] == "READY":
        contract = _resolved_source_contract(
            root_dir=root_dir,
            declaration=declaration,
            inventory=inventory,
            territory_id=territory_id,
            territory_name=territory_name,
            edition=edition,
            population_year=population_year,
            section_year=section_year,
        )
        inventory["resolved_source_contract"] = contract
        resolved["resolved_source_contract_sha256"] = contract["contract_sha256"]
        provenance["resolved_source_contract_sha256"] = contract["contract_sha256"]
        _persist(evidence_dir, resolved, inventory, provenance, decision)

    return resolved, inventory, provenance, decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("fuentes/catalogo_oficial.yaml"))
    parser.add_argument("--territory", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--environment", choices=["development", "test", "production"], required=True)
    parser.add_argument("--acquisition-mode", choices=["official_live", "verified_snapshot", "simulated"], default=None)
    parser.add_argument("--root-dir", type=Path, default=Path("."))
    args = parser.parse_args()
    catalog = load_yaml(args.catalog)
    declaration = load_yaml(args.territory)
    _, inventory, _, decision = acquire(catalog=catalog, declaration=declaration, evidence_dir=args.evidence_dir, environment=args.environment, acquisition_mode=args.acquisition_mode, root_dir=args.root_dir)
    print(f"{inventory['territory']}: adquisición {decision['decision']} ({inventory['acquisition_mode']})")
    if decision["decision"] != "READY":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
