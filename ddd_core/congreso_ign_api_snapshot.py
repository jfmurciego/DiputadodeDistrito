# VERSIÓN: 1.0.1; NOMBRE: auditor de páginas OGC API Features IGN.
# FECHA: 2026-10-20; ALCANCE: validar capturas de páginas administrativas.
# ESTADO: experimental; CAMBIOS: rechaza claves JSON duplicadas.
# MOTIVO: evitar interpretaciones ambiguas de páginas capturadas.
# ANTERIOR: legacy/n08_nac_20261019/congreso_ign_api_snapshot_v1.0.0.py.
"""Audita páginas capturadas de la API IGN; no descarga ni acredita fuentes.

El resultado sólo identifica candidatas temporales a partir de date_boundary y
endlifespanversion. No demuestra la semántica jurídica de esos campos, cobertura
administrativa, completitud fuera del conjunto de páginas ni vigencia legal.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import date
from typing import Iterable, Mapping
from urllib.parse import parse_qs, urljoin, urlparse

API_HOST = "api-features.ign.es"
API_PATH = "/collections/administrativeboundary/items"
TARGET_DATE = "2025-01-01"
MAX_PAGES = 1000
MAX_FEATURES = 100_000
MAX_PAGE_BYTES = 32 * 1024 * 1024
PAGINATION_QUERY_KEYS = frozenset({"offset", "startindex", "cursor", "page", "continuationtoken", "nexttoken"})


class _DuplicateJSONKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJSONKey(key)
        result[key] = value
    return result


def _fail(reason: str) -> None:
    raise ValueError(reason)


def _url(value: object) -> str:
    if not isinstance(value, str) or not value:
        _fail("API_PAGE_URL_REQUIRED")
    parsed = urlparse(value)
    if (parsed.scheme != "https" or parsed.hostname != API_HOST or parsed.port is not None
            or parsed.username or parsed.password or parsed.fragment or parsed.path != API_PATH):
        _fail("API_PAGE_URL_OUTSIDE_OFFICIAL_COLLECTION")
    query = parse_qs(parsed.query)
    if query.get("f") not in (["json"], ["geojson"], ["application/geo+json"]):
        _fail("API_PAGE_GEOJSON_FORMAT_REQUIRED")
    return value


def _selection_query(value: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return non-cursor query parameters; they must not drift between pages."""
    query = parse_qs(urlparse(value).query, keep_blank_values=True)
    return tuple(sorted(
        (key, tuple(values))
        for key, values in query.items()
        if key not in PAGINATION_QUERY_KEYS
    ))


def _as_date(value: object, field: str, *, nullable: bool = False) -> date | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        _fail("API_TEMPORAL_FIELD_INVALID:" + field)
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise ValueError("API_TEMPORAL_FIELD_INVALID:" + field) from error


def _valid_line(geometry: object) -> bool:
    if not isinstance(geometry, dict) or geometry.get("type") not in ("LineString", "MultiLineString"):
        return False
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates:
        return False
    lines = [coordinates] if geometry["type"] == "LineString" else coordinates
    def valid_position(point: object) -> bool:
        return (isinstance(point, (list, tuple)) and len(point) in (2, 3)
                and all(isinstance(value, (int, float)) and not isinstance(value, bool)
                        and math.isfinite(value) for value in point))

    return bool(lines) and all(
        isinstance(line, list) and len(line) >= 2 and all(valid_position(point) for point in line)
        for line in lines
    )


def audit_captured_pages(
    pages: Iterable[Mapping[str, object]], *, target_date: str = TARGET_DATE,
) -> dict:
    """Validate complete, ordered API page captures without changing their bytes.

    Each item is ``{"url": request_url, "raw": response_bytes}``. A next link
    must be represented by the immediately following page. Errors fail closed.
    """
    if target_date != TARGET_DATE:
        _fail("ONLY_APPROVED_HISTORICAL_REFERENCE_2025_01_01")
    target = _as_date(target_date, "target_date")
    iterator = iter(pages)
    try:
        page = next(iterator)
    except StopIteration:
        _fail("API_PAGE_COUNT_OUT_OF_RANGE")

    expected_matched: int | None = None
    seen_urls: set[str] = set()
    seen_ids: set[str] = set()
    hashes: list[dict[str, object]] = []
    selection_query: tuple[tuple[str, tuple[str, ...]], ...] | None = None
    candidate_count = 0
    noncandidate_count = 0
    codes: set[str] = set()
    expected_next: str | None = None
    feature_total = 0
    page_count = 0

    while True:
        page_count += 1
        if page_count > MAX_PAGES:
            _fail("API_PAGE_COUNT_OUT_OF_RANGE")
        if not isinstance(page, Mapping):
            _fail("API_PAGE_RECORD_INVALID")
        request_url = _url(page.get("url"))
        if page_count > 1 and request_url != expected_next:
            _fail("API_NEXT_PAGE_SEQUENCE_MISMATCH")
        page_selection_query = _selection_query(request_url)
        if selection_query is None:
            selection_query = page_selection_query
        elif page_selection_query != selection_query:
            _fail("API_QUERY_SELECTION_CHANGED")
        if request_url in seen_urls:
            _fail("API_PAGE_URL_CYCLE_OR_DUPLICATE")
        seen_urls.add(request_url)
        raw = page.get("raw")
        if not isinstance(raw, bytes) or not raw or len(raw) > MAX_PAGE_BYTES:
            _fail("API_PAGE_BYTES_INVALID")
        try:
            document = json.loads(raw, object_pairs_hook=_unique_object)
        except _DuplicateJSONKey as error:
            raise ValueError("API_PAGE_JSON_DUPLICATE_KEY") from error
        except (UnicodeError, ValueError) as error:
            raise ValueError("API_PAGE_JSON_INVALID") from error
        if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
            _fail("API_PAGE_NOT_FEATURE_COLLECTION")
        matched = document.get("numberMatched")
        returned = document.get("numberReturned")
        features = document.get("features")
        if (not isinstance(matched, int) or isinstance(matched, bool) or matched < 0
                or not isinstance(returned, int) or isinstance(returned, bool) or returned < 0
                or not isinstance(features, list) or returned != len(features)):
            _fail("API_PAGE_COUNT_METADATA_INVALID")
        if matched > MAX_FEATURES:
            _fail("API_FEATURE_COUNT_LIMIT")
        if expected_matched is None:
            expected_matched = matched
        elif matched != expected_matched:
            _fail("API_NUMBER_MATCHED_CHANGED_BETWEEN_PAGES")
        feature_total += returned
        if feature_total > MAX_FEATURES:
            _fail("API_FEATURE_COUNT_LIMIT")

        for feature in features:
            if not isinstance(feature, dict):
                _fail("API_FEATURE_INVALID")
            ident = feature.get("id")
            if (not isinstance(ident, (str, int)) or isinstance(ident, bool)
                    or not str(ident)):
                _fail("API_FEATURE_ID_INVALID")
            ident_text = str(ident)
            if ident_text in seen_ids:
                _fail("API_FEATURE_ID_DUPLICATE")
            seen_ids.add(ident_text)
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                _fail("API_FEATURE_PROPERTIES_REQUIRED")
            code = properties.get("nationalcode")
            if not isinstance(code, str) or not code:
                _fail("API_NATIONALCODE_REQUIRED")
            if "date_boundary" not in properties or "endlifespanversion" not in properties:
                _fail("API_TEMPORAL_FIELDS_REQUIRED")
            start = _as_date(properties.get("date_boundary"), "date_boundary")
            end = _as_date(properties.get("endlifespanversion"), "endlifespanversion", nullable=True)
            if end is not None and start is not None and end < start:
                _fail("API_TEMPORAL_INTERVAL_REVERSED")
            if not _valid_line(feature.get("geometry")):
                _fail("API_ADMINISTRATIVE_BOUNDARY_LINE_REQUIRED")
            if start is not None and start <= target and (end is None or target < end):
                candidate_count += 1
                codes.add(code)
            else:
                noncandidate_count += 1

        hashes.append({"url": request_url, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                       "number_returned": returned})

        links = document.get("links", [])
        if not isinstance(links, list):
            _fail("API_PAGE_LINKS_INVALID")
        next_links = [link for link in links if isinstance(link, dict) and link.get("rel") == "next"]
        if len(next_links) > 1:
            _fail("API_NEXT_LINK_AMBIGUOUS")
        if next_links:
            href = next_links[0].get("href")
            if not isinstance(href, str) or not href:
                _fail("API_NEXT_LINK_HREF_REQUIRED")
            expected_next = _url(urljoin(request_url, href))
            if expected_next in seen_urls:
                _fail("API_PAGE_URL_CYCLE_OR_DUPLICATE")
            if page_count >= MAX_PAGES:
                _fail("API_PAGE_COUNT_OUT_OF_RANGE")
            try:
                page = next(iterator)
            except StopIteration:
                _fail("API_PAGINATION_CAPTURE_INCOMPLETE")
        else:
            try:
                next(iterator)
            except StopIteration:
                break
            else:
                _fail("API_NEXT_PAGE_LINK_MISSING")

    if expected_matched is None or feature_total != expected_matched:
        _fail("API_PAGINATION_COVERAGE_INCOMPLETE")
    return {
        "schema": "ddd.ign-api-historical-page-audit/1.0",
        "source": "IGN OGC API Features administrativeboundary",
        "target_date": target_date,
        "page_count": page_count,
        "number_matched": expected_matched,
        "number_returned_total": feature_total,
        "unique_feature_ids": len(seen_ids),
        "time_window_candidates": candidate_count,
        "time_window_non_candidates": noncandidate_count,
        "distinct_nationalcodes_in_candidates": len(codes),
        "page_receipts": hashes,
        "pagination_complete_for_reported_collection": True,
        "temporal_field_semantics_independently_verified": False,
        "historical_2025_source_accredited": False,
        "eligible_for_52_province_audits": False,
        "generation_authorized": False,
        "status": "CAPTURE_COMPLETE_TEMPORAL_CANDIDATE_ONLY_NOT_ACCREDITATION",
    }
