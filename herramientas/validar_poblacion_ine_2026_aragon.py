#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

POP_SERVICE = "https://www.ine.es/servergis2/rest/services/ws/censo_numero_de_personas/MapServer"
POP_LAYER = POP_SERVICE + "/2"
POP_QUERY = POP_LAYER + "/query"
SECTION_COLLECTION = (
    "https://www.ine.es/geoserver/ogc/features/v1/collections/"
    "WMS_INE_SECCIONES_G01%3ASU.VectorStatisticalUnit"
)
SECTION_2026 = SECTION_COLLECTION + "/items"
PROVINCES = ("22", "44", "50")
EXPECTED_SECTIONS = 1463
TARGET_CUSEC = "5002501003"
OLD_ONLY_EXPECTED = "2221301003"
BASELINE_2025 = Path(
    "territorios/aragon/resultados/ejecuciones/"
    "gh-34599224954-1/M01/secciones.csv"
)


def fetch_json(
    url: str,
    *,
    timeout: int = 90,
    retries: int = 3,
    form: dict[str, str] | None = None,
) -> dict:
    last = None
    for attempt in range(retries):
        try:
            body = urlencode(form).encode("utf-8") if form is not None else None
            headers = {
                "User-Agent": (
                    "DiputadoDeDistrito/INE-2026-validation "
                    "(+GitHub Actions; official-source research)"
                )
            }
            if body is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            req = Request(url, data=body, headers=headers, method="POST" if body else "GET")
            with urlopen(req, timeout=timeout) as response:
                payload = response.read()
            text = payload.decode("utf-8", errors="replace")
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                prefix = text[:500].replace("\n", " ")
                raise ValueError(
                    f"respuesta no JSON ({len(payload)} bytes): {prefix!r}"
                ) from exc
            if not isinstance(data, dict):
                raise ValueError("respuesta JSON no es objeto")
            return data
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"fallo descargando {url}: {last}")


def normalized_cusec(value: object) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits.zfill(10)[:10] if digits else ""


def field_name(metadata: dict, alias: str) -> str:
    wanted = alias.casefold()
    for field in metadata.get("fields") or []:
        name = str(field.get("name") or "")
        field_alias = str(field.get("alias") or "")
        if name.casefold() == wanted or field_alias.casefold() == wanted:
            return name
    raise RuntimeError(f"campo {alias!r} no encontrado en metadata")


def digest_rows(rows: list[tuple[str, int]]) -> str:
    raw = "\n".join(f"{cusec},{value}" for cusec, value in sorted(rows)) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def digest_ids(ids: set[str]) -> str:
    raw = "\n".join(sorted(ids)) + "\n"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_population() -> tuple[dict, dict[str, int], dict[str, int]]:
    service = fetch_json(POP_SERVICE + "?f=pjson")
    metadata = fetch_json(POP_LAYER + "?f=pjson")
    cusec_field = field_name(metadata, "cusec")
    province_field = field_name(metadata, "cpro")
    population_field = field_name(metadata, "n_personas")
    joined_cusec_field = next(
        (
            str(field.get("name"))
            for field in metadata.get("fields") or []
            if str(field.get("name") or "").casefold() == "cusec_1"
        ),
        None,
    )
    if not joined_cusec_field:
        raise RuntimeError("metadata 2026 no expone el campo tabular cusec_1")
    population: dict[str, int] = {}
    joined_population: dict[str, int] = {}
    duplicates: list[str] = []
    null_population: list[str] = []
    query_evidence: list[dict] = []
    for province in PROVINCES:
        form = {
            "where": f"{province_field}='{province}'",
            "outFields": (
                f"{cusec_field},{joined_cusec_field},"
                f"{province_field},{population_field}"
            ),
            "returnGeometry": "false",
            "orderByFields": cusec_field,
            "resultRecordCount": "2000",
            "f": "json",
        }
        query_url = POP_QUERY + "?" + urlencode(form)
        payload = fetch_json(query_url)
        if payload.get("error"):
            raise RuntimeError(
                f"ArcGIS feature query error para CPRO={province}: {payload['error']}"
            )
        if payload.get("exceededTransferLimit") is True:
            raise RuntimeError(
                f"ArcGIS truncó la respuesta territorial para CPRO={province}"
            )
        features = payload.get("features") or []
        query_evidence.append({"province": province, "features": len(features)})
        for feature in features:
            attrs = feature.get("attributes") or {}
            actual_province = str(attrs.get(province_field) or "").zfill(2)
            if actual_province != province:
                raise RuntimeError(
                    f"población 2026 devolvió CPRO={actual_province} para {province}"
                )
            cusec = normalized_cusec(attrs.get(cusec_field))
            joined_cusec = normalized_cusec(attrs.get(joined_cusec_field))
            if not cusec or cusec[:2] != province:
                raise RuntimeError(
                    f"CUSEC geométrico incoherente en población 2026: {cusec!r} / {province}"
                )
            if not joined_cusec:
                raise RuntimeError(
                    f"cusec_1 tabular ausente para CUSEC geométrico {cusec}"
                )
            if cusec in population or joined_cusec in joined_population:
                duplicates.append(f"{cusec}|{joined_cusec}")
                continue
            raw_value = attrs.get(population_field)
            if raw_value is None:
                null_population.append(f"{cusec}|{joined_cusec}")
                continue
            value = int(raw_value)
            population[cusec] = value
            joined_population[joined_cusec] = value

    if duplicates:
        raise RuntimeError(f"CUSEC duplicados en población 2026: {duplicates[:20]}")
    if null_population:
        raise RuntimeError(
            f"n_personas nulo en población 2026: {null_population[:20]}"
        )

    document_info = service.get("documentInfo") or {}
    metadata_summary = {
        "service_description": service.get("serviceDescription") or service.get("description"),
        "service_map_name": service.get("mapName"),
        "service_document_title": document_info.get("Title"),
        "service_spatial_reference": service.get("spatialReference"),
        "layer_description": metadata.get("description"),
        "layer_name": metadata.get("name"),
        "display_field": metadata.get("displayField"),
        "geometry_type": metadata.get("geometryType"),
        "max_record_count": metadata.get("maxRecordCount"),
        "supported_query_formats": metadata.get("supportedQueryFormats"),
        "spatial_reference": (metadata.get("extent") or {}).get("spatialReference"),
        "cusec_field": cusec_field,
        "province_field": province_field,
        "population_field": population_field,
        "joined_cusec_field": joined_cusec_field,
        "fields": [
            {
                "name": field.get("name"),
                "alias": field.get("alias"),
                "type": field.get("type"),
            }
            for field in metadata.get("fields") or []
        ],
        "query_method": "GET equality by CPRO",
        "query_evidence": query_evidence,
    }
    return metadata_summary, population, joined_population


def load_sectioning_2026() -> tuple[dict, set[str], dict[str, int], list[str]]:
    collection = fetch_json(SECTION_COLLECTION + "?f=json")
    collection_summary = {
        "id": collection.get("id"),
        "title": collection.get("title"),
        "description": collection.get("description"),
        "item_type": collection.get("itemType"),
        "crs": collection.get("crs") or [],
    }
    ids: set[str] = set()
    province_counts: dict[str, int] = {}
    urls: list[str] = []
    for province in PROVINCES:
        url = SECTION_2026 + "?" + urlencode(
            {
                "f": "application/geo+json",
                "filter": f"CPRO='{province}'",
                "filter-lang": "cql2-text",
                "limit": "10000",
            }
        )
        urls.append(url)
        payload = fetch_json(url)
        features = payload.get("features") or []
        local: set[str] = set()
        for feature in features:
            props = feature.get("properties") or {}
            actual = str(props.get("CPRO") or "").zfill(2)
            if actual != province:
                raise RuntimeError(
                    f"SU.VectorStatisticalUnit devolvió CPRO={actual} para {province}"
                )
            tipo = str(props.get("TIPO") or "").strip().upper()
            csec = str(props.get("CSEC") or "").strip()
            # Mismo selector que la adquisición común: la colección vigente
            # contiene también otras unidades estadísticas.
            is_section = ("SECC" in tipo) if tipo else bool(csec and csec != "000")
            if not is_section:
                continue
            cusec = normalized_cusec(props.get("CUSEC") or props.get("cusec"))
            if not cusec:
                raise RuntimeError("sección 2026 sin CUSEC normalizable")
            if cusec[:2] != province:
                raise RuntimeError(
                    f"Seccionado vigente devolvió {cusec} para provincia {province}"
                )
            if cusec in local:
                raise RuntimeError(f"CUSEC duplicado en {province}: {cusec}")
            local.add(cusec)
        if not local:
            raise RuntimeError(f"sin secciones seleccionadas para provincia {province}")
        overlap = ids.intersection(local)
        if overlap:
            raise RuntimeError(f"CUSEC repetidos entre provincias: {sorted(overlap)[:20]}")
        ids.update(local)
        province_counts[province] = len(local)
    return collection_summary, ids, province_counts, urls


def load_baseline_2025(root: Path) -> set[str]:
    path = root / BASELINE_2025
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    candidates = ("CUSEC", "CUSEC_KEY", "cusec", "section_id")
    field = next((name for name in candidates if name in (reader.fieldnames or [])), None)
    if field is None:
        # El baseline histórico también existe con CUSEC como primera columna.
        rows = list(csv.reader(io.StringIO(text)))
        return {
            normalized_cusec(row[0])
            for row in rows[1:]
            if row and normalized_cusec(row[0])
        }
    return {
        normalized_cusec(row.get(field))
        for row in reader
        if normalized_cusec(row.get(field))
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root_dir).resolve()

    metadata, population, joined_population = load_population()
    section_metadata, sectioning, section_counts, section_urls = load_sectioning_2026()
    population_ids = set(population)
    joined_population_ids = set(joined_population)
    baseline = load_baseline_2025(root)

    population_counts = {
        province: sum(1 for cusec in population if cusec.startswith(province))
        for province in PROVINCES
    }
    population_only = sorted(population_ids - sectioning)
    sectioning_only = sorted(sectioning - population_ids)
    joined_population_only = sorted(joined_population_ids - sectioning)
    joined_sectioning_only = sorted(sectioning - joined_population_ids)
    target_value = population.get(TARGET_CUSEC)
    joined_target_value = joined_population.get(TARGET_CUSEC)

    population_service_identity = "2026" in " ".join(
        str(metadata.get(key) or "")
        for key in (
            "service_description",
            "service_map_name",
            "service_document_title",
        )
    )
    section_collection_identity = (
        section_metadata.get("title") == "Secciones_2026"
        and any(str(value).endswith("/25830") for value in section_metadata.get("crs") or [])
    )
    metadata_pass = (
        population_service_identity
        and section_collection_identity
        and metadata.get("layer_name") == "Nivel: secciones"
        and metadata.get("geometry_type") == "esriGeometryPolygon"
        and int(metadata.get("max_record_count") or 0) >= EXPECTED_SECTIONS
        and int((metadata.get("spatial_reference") or {}).get("wkid") or 0) == 25830
        and metadata.get("cusec_field")
        and metadata.get("population_field")
    )
    extraction_pass = (
        len(population_ids) == EXPECTED_SECTIONS
        and set(population_counts) == set(PROVINCES)
        and all(population_counts[p] > 0 for p in PROVINCES)
    )
    geometry_key_match = (
        len(sectioning) == EXPECTED_SECTIONS
        and population_ids == sectioning
    )
    source_key_match = (
        len(joined_population_ids) == EXPECTED_SECTIONS
        and joined_population_ids == sectioning
    )
    exact_match_pass = source_key_match
    target_pass = (
        TARGET_CUSEC in sectioning
        and isinstance(joined_target_value, int)
    )

    checks = {
        "metadata_layer": bool(metadata_pass),
        "aragon_population_extraction": bool(extraction_pass),
        "exact_1463_cusec_match": bool(exact_match_pass),
        "target_5002501003_has_population": bool(target_pass),
    }
    technical_pass = all(checks.values())

    evidence = {
        "schema": "ddd.ine-2026-population-validation/1.0",
        "provider": "Instituto Nacional de Estadística",
        "scope": "Aragón",
        "population_service": POP_SERVICE,
        "population_layer": POP_LAYER,
        "sectioning_collection": "WMS_INE_SECCIONES_G01:SU.VectorStatisticalUnit",
        "sectioning_identity": (
            "Colección vigente acreditada en el repo como Secciones_2026 mediante "
            "configuracion/evidencia_disponibilidad_fuentes_territoriales_2026-09-30.json"
        ),
        "metadata": metadata,
        "population_2026": {
            "geometry_cusec": {
                "section_count": len(population_ids),
                "province_counts": population_counts,
                "total_population": sum(population.values()),
                "attributes_sha256": digest_rows(list(population.items())),
            },
            "source_cusec_1": {
                "section_count": len(joined_population_ids),
                "total_population": sum(joined_population.values()),
                "attributes_sha256": digest_rows(list(joined_population.items())),
            },
        },
        "sectioning_2026": {
            "collection_metadata": section_metadata,
            "section_count": len(sectioning),
            "province_counts": section_counts,
            "cusec_sha256": digest_ids(sectioning),
            "query_urls": section_urls,
        },
        "comparison": {
            "geometry_cusec_equal": geometry_key_match,
            "geometry_population_only": population_only,
            "geometry_sectioning_only": sectioning_only,
            "source_cusec_1_equal": source_key_match,
            "source_population_only": joined_population_only,
            "source_sectioning_only": joined_sectioning_only,
        },
        "target_section": {
            "cusec": TARGET_CUSEC,
            "present_in_geometry_cusec": TARGET_CUSEC in population_ids,
            "geometry_n_personas": target_value,
            "present_in_source_cusec_1": TARGET_CUSEC in joined_population_ids,
            "source_n_personas": joined_target_value,
            "present_in_sectioning_2026": TARGET_CUSEC in sectioning,
        },
        "baseline_2025_diagnostic": {
            "available": bool(baseline),
            "section_count": len(baseline),
            "added_in_2026": sorted(sectioning - baseline) if baseline else [],
            "removed_in_2026": sorted(baseline - sectioning) if baseline else [],
            "expected_cross_year_swap": (
                bool(baseline)
                and sorted(sectioning - baseline) == [TARGET_CUSEC]
                and sorted(baseline - sectioning) == [OLD_ONLY_EXPECTED]
            ),
        },
        "identity_checks": {
            "population_service_identifies_2026": population_service_identity,
            "section_collection_identifies_2026": section_collection_identity,
        },
        "checks": checks,
        "technical_decision": (
            "PASS_TECHNICAL_GOVERNANCE_PENDING"
            if technical_pass
            else "BLOCK_TECHNICAL"
        ),
        "governance_note": (
            "Esta validación prueba identidad técnica y cobertura del GIS INE 2026; "
            "no acredita por sí sola el carácter definitivo/publicado del Censo Anual 2026."
        ),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
    return 0 if technical_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
