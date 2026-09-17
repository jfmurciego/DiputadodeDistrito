#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROYECTO: Diputado de Distrito
COMPONENTE: adquisición genérica de fuentes oficiales
VERSIÓN: 1.0.0
NOMBRE DE VERSIÓN: Adquisición declarativa INE
FECHA: 2026-09-17
ESTADO: candidato
FUNCIÓN: materializar fuentes oficiales declaradas por territorio y registrar inventario y procedencia.
CAMBIOS: elimina códigos territoriales, edición y cardinalidades incrustadas de la lógica de adquisición.
MOTIVO: reutilizar una sola implementación para cualquier territorio con fuentes INE compatibles.
ANTERIOR: legacy/herramientas/adquirir_fuentes_ine_v1.0.1.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

FetchBytes = Callable[[str], bytes]


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
            request = Request(url, headers={"User-Agent": "DiputadoDeDistrito/2.0 (+GitHub Actions; fuente oficial INE)"})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"No se pudo descargar la fuente oficial: {last}")


def _territory_names(declaration: dict) -> tuple[str, int, list[dict]]:
    territory = declaration.get("territory") or {}
    name = str(territory.get("business_name") or "").strip()
    edition = int(territory.get("edition"))
    codes = territory.get("territorial_codes")
    if not name or not isinstance(codes, list) or not codes:
        raise ValueError("Declaración territorial incompleta")
    for row in codes:
        if not isinstance(row, dict) or not row.get("code") or not row.get("business_name"):
            raise ValueError("Cada división territorial debe declarar código y nombre de negocio")
    return name, edition, codes


def _policy_allows(declaration: dict, environment: str, acquisition_mode: str) -> bool:
    policy = declaration.get("environment_policy") or {}
    allowed = policy.get(environment)
    return isinstance(allowed, list) and acquisition_mode in allowed


def _write_bytes(path: Path, payload: bytes) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"path": str(path), "sha256": sha256_bytes(payload), "bytes": len(payload)}


def _acquire_static(source: dict, out_dir: Path, fetcher: FetchBytes) -> tuple[dict, dict]:
    url = str(source["url"])
    payload = fetcher(url)
    output = out_dir / str(source["output_name"])
    evidence = _write_bytes(output, payload)
    item = {"business_name": source["business_name"], "provider": source["provider"], "format": source["format"], "availability": "AVAILABLE", **evidence}
    provenance = {**item, "urls": [url], "acquired_at_utc": datetime.now(timezone.utc).isoformat()}
    return item, provenance


def _acquire_sections(source: dict, declaration: dict, out_dir: Path, fetcher: FetchBytes) -> tuple[dict, dict]:
    territory_name, edition, territorial_codes = _territory_names(declaration)
    filter_field = str(source["territorial_filter_field"])
    section_id_field = str(source["section_id_field"])
    endpoint = str(source["endpoint_template"]).format(edition=edition)
    feature_filter = str(source.get("feature_filter") or "")
    features: list[dict] = []
    seen: set[str] = set()
    urls: list[str] = []
    coverage: list[dict] = []

    for territory in territorial_codes:
        code = str(territory["code"])
        business_name = str(territory["business_name"])
        clauses = [f"{filter_field}='{code}'"]
        if feature_filter:
            clauses.append(feature_filter)
        params = {"f": "application/geo+json", "filter": " AND ".join(clauses), "filter-lang": "cql2-text", "limit": "10000"}
        url = endpoint + "?" + urlencode(params)
        urls.append(url)
        data = json.loads(fetcher(url).decode("utf-8-sig"))
        rows = data.get("features") or []
        if not rows:
            raise RuntimeError(f"El INE no devolvió secciones para {business_name}")
        count = 0
        for feature in rows:
            props = feature.get("properties") or {}
            if str(props.get(filter_field, "")).zfill(2) != code.zfill(2):
                raise RuntimeError(f"Cobertura territorial inesperada en {business_name}")
            section_id = str(props.get(section_id_field) or "").strip()
            if not section_id:
                raise RuntimeError(f"Sección sin identificador oficial en {business_name}")
            if section_id in seen:
                continue
            seen.add(section_id)
            features.append(feature)
            count += 1
        coverage.append({"territory": business_name, "sections": count})

    features.sort(key=lambda row: str((row.get("properties") or {}).get(section_id_field, "")))
    expected = int((declaration.get("coverage_checks") or {}).get("expected_sections", 0) or 0)
    if expected and len(features) != expected:
        raise RuntimeError(f"Cobertura de {territory_name}: {len(features)} secciones; esperadas {expected}")
    output_name = str(source["output_name"]).format(edition=edition)
    payload = json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    evidence = _write_bytes(out_dir / output_name, payload)
    item = {"business_name": f"{source['business_name']} {edition}", "provider": source["provider"], "format": source["format"], "availability": "AVAILABLE", "coverage": coverage, "sections": len(features), **evidence}
    provenance = {**item, "collection": str(source["collection_template"]).format(edition=edition), "urls": urls, "acquired_at_utc": datetime.now(timezone.utc).isoformat()}
    return item, provenance


def acquire(*, catalog: dict, declaration: dict, out_dir: Path, environment: str, acquisition_mode: str, fetcher: FetchBytes = live_fetch) -> tuple[dict, dict]:
    territory_name, edition, territorial_codes = _territory_names(declaration)
    if not _policy_allows(declaration, environment, acquisition_mode):
        raise RuntimeError(f"La política de {territory_name} no permite {acquisition_mode} en {environment}")
    sources = catalog.get("sources") or {}
    required = declaration.get("required_sources")
    if not isinstance(required, list) or not required:
        raise ValueError("No hay fuentes requeridas declaradas")
    inventory_items = []
    provenance_items = []
    for source_name in required:
        source = sources.get(source_name)
        if not isinstance(source, dict):
            raise ValueError(f"Fuente requerida no catalogada: {source_name}")
        kind = source.get("kind")
        if kind == "static_csv":
            item, provenance = _acquire_static(source, out_dir, fetcher)
        elif kind == "ogc_features":
            item, provenance = _acquire_sections(source, declaration, out_dir, fetcher)
        else:
            raise ValueError(f"Tipo de fuente no soportado: {kind}")
        inventory_items.append(item)
        provenance_items.append(provenance)

    divisions = [row["business_name"] for row in territorial_codes]
    inventory = {"schema": "ddd-source-inventory/1.0", "territory": territory_name, "edition": edition, "environment": environment, "acquisition_mode": acquisition_mode, "territorial_coverage": divisions, "sources": inventory_items}
    provenance = {"schema": "ddd-source-provenance/1.0", "territory": territory_name, "edition": edition, "provider": "Instituto Nacional de Estadística", "acquisition_mode": acquisition_mode, "sources": provenance_items}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "inventario_fuentes.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "manifiesto_procedencia.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return inventory, provenance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=Path("fuentes/catalogo_oficial.yaml"))
    parser.add_argument("--territory", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--environment", choices=["development", "test", "production"], required=True)
    parser.add_argument("--acquisition-mode", choices=["official_live", "verified_snapshot"], default="official_live")
    args = parser.parse_args()
    catalog = load_yaml(args.catalog)
    declaration = load_yaml(args.territory)
    inventory, _ = acquire(catalog=catalog, declaration=declaration, out_dir=args.out_dir, environment=args.environment, acquisition_mode=args.acquisition_mode)
    print(f"Fuentes oficiales materializadas para {inventory['territory']} ({inventory['edition']}): {len(inventory['sources'])}")


if __name__ == "__main__":
    main()
