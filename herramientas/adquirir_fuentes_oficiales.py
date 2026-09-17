#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: adquisición genérica de fuentes oficiales
VERSIÓN: 1.2.0
NOMBRE DE VERSIÓN: Copia nacional inmutable y recorte territorial aislado
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: materializar fuentes territoriales por declaración, preservando inmutables las copias oficiales nacionales.
CAMBIOS: escribe recortes sólo en evidence/materialized, separa raíz nacional y raíz territorial y bloquea origen=destino.
MOTIVO: impedir que la preparación de un territorio mutile o sobrescriba una copia oficial compartida por otros territorios.
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

FetchBytes = Callable[[str], bytes]
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


def _territory(declaration: dict) -> tuple[str, str, int, list[dict]]:
    territory = declaration.get("territory") or {}
    territory_id = str(territory.get("id") or "").strip()
    name = str(territory.get("business_name") or "").strip()
    edition = territory.get("edition")
    codes = territory.get("territorial_codes")
    if not territory_id or not name or edition is None or not isinstance(codes, list) or not codes:
        raise ValueError("Declaración territorial incompleta: id, nombre, edición y códigos son obligatorios")
    normalized = []
    for row in codes:
        if not isinstance(row, dict) or row.get("code") is None or not row.get("business_name"):
            raise ValueError("Cada provincia debe declarar code y business_name")
        normalized.append({"code": str(row["code"]).zfill(2), "business_name": str(row["business_name"])})
    return territory_id, name, int(edition), normalized


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


def _source_urls(source: dict, edition: int, provinces: list[dict]) -> list[str]:
    kind = source.get("kind")
    if kind == "static_csv":
        return [str(source["url"])]
    if kind == "ogc_features":
        endpoint = str(source["endpoint_template"]).format(edition=edition)
        filter_field = str(source["territorial_filter_field"])
        feature_filter = str(source.get("feature_filter") or "")
        urls = []
        for province in provinces:
            clauses = [f"{filter_field}='{province['code']}'"]
            if feature_filter:
                clauses.append(feature_filter)
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
        rows_out = 0
        for row in reader:
            if str(row.get(rules["year_col"], "")).strip() != str(edition):
                continue
            if str(row.get(rules["sex_col"], "")).strip() not in rules["sex_total_values"]:
                continue
            if str(row.get(rules["age_col"], "")).strip() not in rules["age_total_values"]:
                continue
            section_id = _normalize_section_id(row.get(rules["section_col"]))
            if not section_id:
                continue
            province = section_id[:2]
            if province not in province_codes:
                continue
            writer.writerow(row)
            seen_provinces.add(province)
            rows_out += 1
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


def _collect_live_sections(source: dict, edition: int, provinces: list[dict], fetcher: FetchBytes) -> tuple[list[dict], list[str], dict]:
    urls = _source_urls(source, edition, provinces)
    filter_field = str(source["territorial_filter_field"])
    section_id_field = str(source["section_id_field"])
    all_features: list[dict] = []
    seen_ids: set[str] = set()
    coverage: dict[str, int] = {}
    for province, url in zip(provinces, urls):
        code = province["code"]
        payload = fetcher(url)
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
                raise ValueError("Sección sin identificador oficial")
            if section_id in seen_ids:
                continue
            seen_ids.add(section_id)
            all_features.append(feature)
            count += 1
        coverage[code] = count
    if set(coverage) != {row["code"] for row in provinces}:
        raise ValueError("Cobertura provincial de secciones incompleta")
    return all_features, urls, {"provinces": sorted(coverage), "sections_by_province": coverage, "sections": len(all_features)}


def _write_shapefile_zip(features: list[dict], crs: str | None = "EPSG:4326") -> bytes:
    try:
        import geopandas as gpd
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"geopandas es obligatorio para materializar secciones: {exc}")
    with tempfile.TemporaryDirectory(prefix="ddd_sections_") as td:
        shp = Path(td) / "seccionado.shp"
        gdf = gpd.GeoDataFrame.from_features(features, crs=crs or "EPSG:4326")
        gdf.to_file(shp, driver="ESRI Shapefile", index=False)
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as zf:
            for file in sorted(Path(td).glob("seccionado.*")):
                info = zipfile.ZipInfo(file.name, date_time=(2025, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                zf.writestr(info, file.read_bytes())
        return out.getvalue()


def _write_materialized(evidence_dir: Path, configured_path: str, payload: bytes) -> tuple[Path, dict]:
    destination = _territorial_destination(evidence_dir, configured_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination, {"path": configured_path, "sha256": sha256_bytes(payload), "bytes": len(payload), "staged_path": str(destination)}


def _core(source_id: str, configured_path: str, payload: bytes | None, urls: list[str], edition: int) -> dict:
    return {"source_id": source_id, "path": configured_path, "sha256": sha256_bytes(payload) if payload is not None else None, "bytes": len(payload) if payload is not None else None, "urls": list(urls), "edition": edition}


def _persist(evidence_dir: Path, resolved: dict, inventory: dict, provenance: dict, decision: dict) -> None:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    files = {"declaracion_materializacion.json": resolved, "inventario_fuentes.json": inventory, "manifiesto_procedencia.json": provenance, "decision_adquisicion.json": decision}
    for name, data in files.items():
        (evidence_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def acquire(*, catalog: dict, declaration: dict, evidence_dir: Path, environment: str, acquisition_mode: str | None = None, fetcher: FetchBytes | None = None, root_dir: Path | None = None) -> tuple[dict, dict, dict, dict]:
    root_dir = (root_dir or Path.cwd()).resolve()
    evidence_dir = evidence_dir.resolve()
    territory_id, territory_name, edition, provinces = _territory(declaration)
    province_codes = [row["code"] for row in provinces]
    mode = _select_mode(declaration, environment, acquisition_mode)
    if mode == "simulated" and fetcher is None:
        raise ValueError("La simulación exige un fetcher inyectado por pruebas")
    fetch = fetcher or live_fetch
    required = _required_sources(catalog, declaration)
    header = {"territory_id": territory_id, "territory": territory_name, "edition": edition, "environment": environment, "acquisition_mode": mode}
    resolved = {"schema": "ddd-source-materialization-declaration/1.1", **header, "materialization_root": str((evidence_dir / "materialized").resolve()), "sources": []}
    inventory = {"schema": "ddd-source-inventory/1.2", **header, "territorial_coverage": province_codes, "sources": []}
    provenance = {"schema": "ddd-source-provenance/1.2", **header, "sources": []}
    decision = {"schema": "ddd-source-acquisition-decision/1.1", **header, "decision": "READY", "reasons": []}

    for source_id, source, binding in required:
        configured_path = str(binding["materialized_path"])
        official_urls = _source_urls(source, edition, provinces)
        payload_out: bytes | None = None
        content_checks: dict = {}
        snapshot_meta: dict = {}
        staged_meta: dict = {}
        try:
            destination = _territorial_destination(evidence_dir, configured_path)
            if mode == "verified_snapshot":
                source_payload, snapshot_meta = _read_snapshot(root_dir, evidence_dir, binding, configured_path, edition)
            elif source.get("kind") == "static_csv":
                source_payload = fetch(official_urls[0])
            else:
                source_payload = b""

            if source.get("kind") == "static_csv":
                filtered_csv, content_checks = _filter_population(source_payload, declaration, edition, province_codes)
                member = str(binding.get("archive_member") or source.get("output_name") or "population.csv")
                payload_out = _zip_single(member, filtered_csv) if configured_path.lower().endswith(".zip") else filtered_csv
            elif source.get("kind") == "ogc_features":
                if mode == "verified_snapshot":
                    features, crs = _read_sections_from_snapshot(source_payload, str(source["territorial_filter_field"]), str(source["section_id_field"]), province_codes)
                    coverage = sorted({str((f.get("properties") or {}).get(source["territorial_filter_field"], "")).zfill(2) for f in features})
                    if coverage != sorted(province_codes):
                        raise ValueError(f"Cobertura provincial de secciones incorrecta: {coverage}")
                    content_checks = {"provinces": coverage, "sections": len(features)}
                    payload_out = _write_shapefile_zip(features, crs=crs)
                else:
                    features, official_urls, content_checks = _collect_live_sections(source, edition, provinces, fetch)
                    payload_out = _write_shapefile_zip(features, crs="EPSG:4326")
            else:
                raise ValueError(f"Tipo de fuente no soportado: {source.get('kind')}")

            _, staged_meta = _write_materialized(evidence_dir, configured_path, payload_out)
            core = _core(source_id, configured_path, payload_out, official_urls, edition)
            resolved["sources"].append({**core, "staged_path": str(destination)})
            inventory["sources"].append({**core, "availability": "AVAILABLE", "content_checks": content_checks, **staged_meta})
            provenance["sources"].append({**core, "provider": source.get("provider"), "acquired_at_utc": datetime.now(timezone.utc).isoformat(), "mode": mode, **snapshot_meta, **staged_meta})
        except Exception as exc:
            core = _core(source_id, configured_path, payload_out, official_urls, edition)
            resolved["sources"].append(dict(core))
            inventory["sources"].append({**core, "availability": "BLOCKED", "error": str(exc), "content_checks": content_checks, **staged_meta})
            provenance["sources"].append({**core, "provider": source.get("provider"), "mode": mode, **snapshot_meta, **staged_meta})
            decision["decision"] = "BLOCKED"
            decision["reasons"].append({"source_id": source_id, "reason": str(exc)})
            _persist(evidence_dir, resolved, inventory, provenance, decision)
            continue
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
